# Phase 147E.1 — Authority Evaluation Model Implementation Contract Repair

**Phase ID:** 147E.1
**Mode:** Contract Repair
**Predecessor:** Phase 147F — Authority Evaluation Model Implementation
Contract Independent Verification (verdict: NOT VERIFIED, one Blocking
finding, BF-147F-1)
**Governed artifact:** `docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`
(AEMIC-001), repaired from v1.0 to v1.1 in place by this phase
**Human authorization:** This phase is authorized to repair AEMIC-001
only. No production code changes are authorized. No implementation of
`pcae.authority_evaluation` may begin until the repaired contract is
independently re-verified (147F.1, not authorized by this phase).

---

## 1. Executive Summary

Phase 147F's independent verification of AEMIC-001 v1.0 identified one
Blocking finding, BF-147F-1: `evaluate()`'s closed, four-parameter
signature (v1.0 AEMIC-REQ-019/020/072) provided no channel for
`citation_text`, and `EligibleAuthorityDeclaration`'s closed six-field
shape (AEMIC-REQ-015/016) carried none either, while v1.0 AEMIC-REQ-022
required every `eligible`-result `AuthorityEvaluationOutcome` to carry a
non-`None` `citation_text`. No well-formed call to `evaluate()` as
originally specified could satisfy both requirements simultaneously for
the `eligible` case, and v1.0 AEMIC-REQ-031's own text was internally
self-contradictory on exactly this point.

This phase independently reconstructed the defect from AEMIC-001 v1.0's
own text (§3 below), confirmed the contradiction is genuine and not an
artifact of Phase 147F's own reading (§4), evaluated three candidate
repairs (§5), and selected the minimum correct one: adding
`citation_text: str | None = None` as `evaluate()`'s own fifth parameter,
enforced at construction time by a new requirement (AEMIC-REQ-101) that
raises a new typed exception, `MissingCitationTextError`, when the
internally-determined result is `eligible` and no citation was supplied.
Adding `citation_text` to `EligibleAuthorityDeclaration` instead — the
repair Phase 147F's own report suggested as one of two options — was
evaluated and rejected: `EligibleAuthorityDeclaration`'s six-field shape
is frozen one layer up, at AEM-001's own AEM-REQ-007 ("SHALL carry
exactly... No other field is defined for v1.0"), and widening it would
require narrowing or amending AEM-001, which this contract's own text and
this phase's own No-Go Boundary both forbid.

AEMIC-001 is now v1.1. §5, §9, §13.1, §14, §15, §20, §22, and §23 were
amended; every other section is byte-for-byte unchanged from v1.0. No
`AEMIC-REQ-###` identifier was renumbered, reassigned, retired, or reused;
two new identifiers were appended (AEMIC-REQ-101, AEMIC-REQ-102). No
production code, test, schema, or other contract was modified.

**Overall Verdict: IMPLEMENTATION CONTRACT REPAIRED.**

Recommended next phase: **147F.1 — Authority Evaluation Model
Implementation Contract Independent Re-Verification** (a recommendation,
not an authorization; §12).

---

## 2. Independent Reconstruction

Per the governing prompt's own instruction ("Do not simply implement
Phase 147F's suggested repair... reconstruct BF-147F-1 independently"),
this phase re-derived the contradiction directly from AEMIC-001 v1.0's own
frozen text before treating Phase 147F's own report as anything beyond a
starting pointer to which section pair to examine.

**Step 1 — locate every requirement governing `citation_text`.** A
targeted re-read of AEMIC-001 v1.0 (not Phase 147F's characterization of
it) located exactly four requirements bearing on `citation_text`:

- **AEMIC-REQ-015/016** (§4): `EligibleAuthorityDeclaration`'s shape is
  closed to exactly six fields — `template_ref`, `template_version`,
  `eligible_identities`, `declared_at`, `declared_by`, `schema_version`.
  No `citation_text` field exists, and AEMIC-REQ-016 explicitly forbids
  "any field beyond the six above."
- **AEMIC-REQ-021/022** (§6/§6.1): `AuthorityEvaluationOutcome.citation_text`
  is `str | None`, and AEMIC-REQ-022 requires, as a construction-time
  invariant, "`citation_text is not None` if and only if
  `evaluation_result == EvaluationResult.ELIGIBLE`" — enforced "not left
  to caller discipline."
- **AEMIC-REQ-019/020** (§5): `evaluate`'s only accepted inputs are
  `claimed_identity`, `declaration`, `evaluated_at`, `evaluator_version` —
  exactly four, closed, with AEMIC-REQ-020 stating explicitly "No
  caller-supplied metadata beyond the four parameters above is accepted."
- **AEMIC-REQ-031** (§9): asserts "Declarations SHALL copy the citation
  text verbatim into the constructed `AuthorityEvaluationOutcome.citation_text`
  at evaluation time," then in the same paragraph confirms
  `EligibleAuthorityDeclaration` "does not carry a `citation_text` field
  at all in v1.0."

**Step 2 — attempt a well-formed construction.** This phase attempted, on
paper, to enumerate every value reachable inside `evaluate()`'s body under
the v1.0 four-parameter signature that could become
`AuthorityEvaluationOutcome.citation_text` for an `eligible` result:
`claimed_identity` (the evaluated identity string, not authority text —
wrong content and, per AEMIC-REQ-021, a distinct field in its own right);
`declaration`'s own six fields (none is `citation_text`, per AEMIC-REQ-016,
confirmed independently by re-reading the table at §4, not merely trusting
AEMIC-REQ-015's own prose summary); `evaluated_at` (a timestamp);
`evaluator_version` (a version marker). None can lawfully become
`citation_text`. There is no fifth source. This independently reproduces
Phase 147F's own Step 3 (§7 of the 147F report) without having read that
section's conclusion first — this phase performed the same enumeration
from AEMIC-001's own text directly.

**Step 3 — is the contradiction genuine, or is there a reading under
which it dissolves?** Considered and rejected: (a) that AEMIC-REQ-022's
invariant might be satisfiable via direct `AuthorityEvaluationOutcome`
construction, bypassing `evaluate()` — true, but AEMIC-REQ-072 names
`evaluate()` as the function `pcae.authority_evaluation.evaluation`
provides, and no other construction path is specified anywhere in
AEMIC-001 v1.0; a "bypass `evaluate()` entirely" reading is not a
specified contract path, it is the absence of one, and directly
reintroduces the caller-controlled-citation-fabrication risk
AEMIC-REQ-022's own enforcement-at-construction-time language exists to
foreclose. (b) that AEMIC-REQ-031's language ("Declarations SHALL copy...")
might be read figuratively, meaning "the authoring workflow, not the
Declaration object itself" — rejected, because the requirement's own
grammatical subject is "Declarations," a defined term (§4) referring to
`EligibleAuthorityDeclaration` instances, not workflows; and even under
the most charitable figurative reading, no channel into `evaluate()`
still exists for whatever performs the copying to use. The contradiction
is genuine, not a reading artifact.

**Step 4 — every requirement affected.** Directly affected (contain or
depend on the broken language): AEMIC-REQ-019, AEMIC-REQ-020, AEMIC-REQ-031
(§9's surrounding prose at AEMIC-REQ-032/033 references AEMIC-REQ-031's
own broken framing and needed a compatible edit, though neither asserts
anything false in isolation), AEMIC-REQ-072 (the signature block),
AEMIC-REQ-074/075/077 (each references the parameter list or exception
boundary by count). Not affected, confirmed by direct re-reading: §4
(AEMIC-REQ-015-018, the Declaration shape itself — sound, closed,
correctly described); §6 (AEMIC-REQ-021/023, the outcome shape and
immutability — sound); §6.1 (AEMIC-REQ-022, the invariant itself — sound
as an invariant, the defect is entirely in the absence of a construction
path that can satisfy it, not in the invariant's own text); §7 (the
closed enum); §11 (the Registry ABC); §12 (persistence); most of §13
(the existing four exceptions, unaffected by adding a fifth); §16–§19,
§21, §24 (auditability, deferred integration, no-go boundary, amendment
discipline, non-goals — none references the parameter count or the
citation channel).

**Step 5 — minimum contract change.** The minimum change is exactly one
new data channel into the one specified construction path (`evaluate()`),
plus the construction-time enforcement AEMIC-REQ-022 already promised but
that no requirement previously described how `evaluate()` itself would
carry out. This determines the shape of §5 below before any candidate
repair language was drafted.

---

## 3. Root Cause Analysis

The defect originates from AEMIC-001 v1.0 having correctly frozen two
independent requirements from two different angles of the same feature —
"the outcome must carry the citation when eligible" (§6.1, derived
directly from AEM-REQ-018's own field description) and "no fifth data
channel is needed because a request `object` is these four parameters
taken together" (§5, a 147D-influenced design simplification, per Phase
147D §6.2's own architecture, which itself never named a `citation_text`
parameter at all) — without independently verifying, at freeze time, that
both requirements could be jointly satisfied. AEMIC-REQ-032 disclosed a
closely adjacent limitation (no `DecisionTemplate` artifact exists for a
caller to fetch citation text from) but framed the entire citation-supply
problem as "external to this package's own domain model," which
correctly describes *where the caller obtains the text* but incorrectly
implied the package itself needed no channel to receive it — a scope
boundary that was drawn one requirement too narrowly. AEMIC-REQ-031 is the
single point where this was written down explicitly and is where the
contradiction became textually visible, but the root cause is upstream of
that one requirement: §5's four-parameter closure was frozen without a
cross-check against §6.1's own invariant.

This defect affects documentation only. No implementation of
`pcae.authority_evaluation` exists under `src/pcae/**` (confirmed at §4
below), so no in-flight behavior required correction.

---

## 4. Existing-State Reinspection

Direct re-inspection, performed independently of Phase 147F's own
Existing-State Reinspection (§4 of the 147F report) though reaching the
same conclusion:

```
$ find src/pcae -iname "*authority_evaluation*" -o -iname "*authority-evaluation*"
(no output)
$ grep -rn "authority_evaluation" src/pcae/ 2>/dev/null
(no output)
```

No `pcae.authority_evaluation` package, module, class, or function exists
anywhere under `src/pcae/**`. `src/pcae/interactive_workflow/models/session.py`'s
`template_ref` field remains a bare, non-empty-validated `str` (unchanged
since Phase 147D/147F's own confirmed re-inspections).
`src/pcae/governance/publication/coordinator.py` and `record.py` are
unmodified. No schema file references `authority_evaluation`, `AEMIC`, or
`citation_text`. This confirms the repair below touches documentation
only and cannot regress any existing behavior, since none exists to
regress.

---

## 5. Candidate Repair Evaluation

Three candidates were assessed, per the governing prompt's own required
minimum, against nine axes: architectural consistency, API clarity,
immutability, security, caller-controlled citation fabrication risk,
compatibility with AEM-001, compatibility with Phase 147D, future Registry
implementation, and future CHGR integration.

### Candidate 1 — Add `citation_text` to `EligibleAuthorityDeclaration`

**Rejected — foreclosed, not merely inferior.** `EligibleAuthorityDeclaration`'s
six-field shape is frozen one layer up the contract stack, at AEM-001's
own AEM-REQ-007: "An Eligible Authority Declaration SHALL carry exactly
[six fields]... No other field is defined for v1.0." AEMIC-001's own
Contract identity and status section states, unconditionally: "AEMIC-001
MUST NOT be read as amending, narrowing, or superseding AEM-001... where
this contract cites [AEM-001], the citation demonstrates compatibility
with an already-frozen provision, never a redefinition of it." Adding a
seventh field to `EligibleAuthorityDeclaration` would be exactly such a
redefinition — it would require either AEM-001's own text to change (this
phase's No-Go Boundary forbids modifying AEM-001) or AEMIC-001 to
knowingly define a Declaration shape wider than AEM-001's own frozen one
(which AEMIC-001's own text forbids of itself). This is a decisive,
structural rejection independent of the remaining eight axes, though those
axes independently confirm it would also be the architecturally worse
choice: `EligibleAuthorityDeclaration` is authored once per
`(template_ref, template_version)` and reused, unchanged, across every
future evaluation against it, `eligible` or not (AEM-REQ-008's
per-version-immutability rule), whereas `citation_text` is meaningful only
to one particular `eligible`-yielding evaluation call — carrying it on the
Declaration would leave it present-but-semantically-irrelevant on every
`ineligible` evaluation, the opposite of AEMIC-REQ-022's own goal of
making "is this citation trustworthy here" mechanically obvious from the
outcome's own shape alone.

### Candidate 2 — Add a `citation_text` channel to `evaluate()`

**Selected.** `evaluate(claimed_identity, declaration, evaluated_at,
evaluator_version, citation_text: str | None = None)`. Preserves
`EligibleAuthorityDeclaration`'s AEM-001-frozen shape untouched (closes
Candidate 1's foreclosure cleanly). Keeps `evaluation_result`'s own
determination a pure function of exactly the two evidentiary inputs
AEM-REQ-016 names (`claimed_identity`, `declaration`) — `citation_text`
carries no evaluative weight and cannot influence which of the three
`EvaluationResult` values is produced, so AEM-REQ-016's own "total
function over its two inputs" language is not violated by a fifth,
non-evidentiary parameter (mirroring the precedent AEMIC-001 v1.0 itself
already set by adding `evaluated_at`/`evaluator_version` as non-evidentiary
pass-through parameters beyond AEM-REQ-016's own two, without objection at
Phase 147F's own verification pass). Introduces no sixth public type.
Directly testable via the existing §13.1 typed-error discipline: a fifth
named exception (`MissingCitationTextError`) slots into the existing
table exactly as the prior four do, with no restructuring of the failure
taxonomy's own shape. Requires zero change to `AuthorityEvaluationOutcome`
(§6, AEMIC-REQ-021/022 both untouched — the invariant they define is now
simply *reachable*, not redefined).

### Candidate 3 — Alternative reconstruction: a distinct outcome-construction path for the `eligible` case

**Rejected as strictly worse than Candidate 2 for equal or greater cost.**
A dedicated function (e.g. `construct_eligible_outcome(...)`) taking
`citation_text` directly, separate from `evaluate()`, would preserve
disclosure-only semantics equally well and would also close the parameter
gap. But it fragments "the sole specified construction path" — a property
Phase 147F's own analysis (§7, Step 5 of the 147F report) treated as
load-bearing precisely because a single enforcement point is what makes
AEMIC-REQ-022's invariant "not left to caller discipline" credible. Two
public construction paths for `AuthorityEvaluationOutcome` (one for
`eligible`, implicitly one for the other two results) is a larger surface
area than one function with one optional parameter, achieves nothing
Candidate 2 does not already achieve, and would require introducing a
second public function name into §3.6's re-export list (AEMIC-REQ-014) —
a strictly larger contract-text footprint for an equivalent outcome.

### Comparison table

| Axis | Candidate 1 | Candidate 2 (selected) | Candidate 3 |
|---|---|---|---|
| Architectural consistency | Foreclosed by AEM-001 | Consistent — extends the existing non-evidentiary-parameter pattern | Consistent but fragments the single-construction-path property |
| API clarity | Confusing (field unused outside `eligible` path) | Clear — one optional parameter, meaningful exactly when needed | Clear per-function, but two entry points to track |
| Immutability | Unaffected either way | Unaffected — no type shape changes | Unaffected — no type shape changes |
| Security / citation fabrication risk | Unaffected relative to pre-repair (caller still supplies the value) | Unaffected relative to pre-repair; enforcement centralized in one place | Unaffected relative to pre-repair; enforcement split across two entry points |
| Compatibility with AEM-001 | **Violates AEM-REQ-007** | Fully compatible | Fully compatible |
| Compatibility with Phase 147D | Contradicts 147D §6.2's own Declaration shape | Fills a gap 147D §6.2 left, doesn't reverse a 147D choice | Fills the same gap via an unnamed-by-147D second function |
| Future Registry implementation | N/A (Registry never sees citation) | Unaffected — Registry never sees `citation_text` | Unaffected — same |
| Future CHGR integration | Unaffected | Unaffected — §17's deferred boundary is untouched | Unaffected — same |

---

## 6. Selected Repair

`citation_text: str | None = None` is added as `evaluate`'s fifth
parameter (AEMIC-001 §5, AEMIC-REQ-019; §14, AEMIC-REQ-072).

`evaluate` enforces the if-and-only-if invariant itself, before
constructing any outcome (new §14.1, AEMIC-REQ-101):

1. `evaluation_result` is determined exactly as before, from exactly the
   two evidentiary inputs (`claimed_identity`, `declaration`) —
   `citation_text` plays no role in this determination.
2. If the result is `ELIGIBLE` and `citation_text` is `None`, `evaluate`
   raises the new `MissingCitationTextError` (§13.1) before attempting any
   construction.
3. If the result is `ELIGIBLE` and `citation_text` is non-`None`,
   `evaluate` constructs the outcome carrying it verbatim.
4. If the result is `INELIGIBLE` or `INDETERMINATE`, `evaluate` constructs
   the outcome with `citation_text=None` regardless of what the caller
   supplied — disregarded, never raised on, never fabricated into the
   outcome. Enforcing a raise on this direction was considered and
   rejected as unnecessary to repair BF-147F-1 and as scope creep beyond
   "the minimum correct repair" (it would newly place a raising condition
   on the two result paths AEM-REQ-024 requires to always succeed, a
   guarantee this repair does not touch).

`AuthorityEvaluationOutcome`'s own construction-time invariant
(AEMIC-REQ-022) remains the final, independent enforcement point — this
repair does not weaken it, it makes it reachable via the one path the
contract specifies.

---

## 7. Requirement Changes

Amended in place (existing `AEMIC-REQ-###` identifiers, text corrected;
none retired, none renumbered): AEMIC-REQ-019 (parameter table widened to
five rows), AEMIC-REQ-020 (reworded for five parameters and the
non-evidentiary-input distinction), AEMIC-REQ-031 (rewritten — the
self-contradictory "Declarations SHALL copy..." framing replaced with
"`evaluate` SHALL copy..."), AEMIC-REQ-032 (one-clause edit: "indirectly
through evaluate's caller" → "directly as evaluate's own fifth parameter";
the named limitation itself is unchanged), AEMIC-REQ-033 (same one-clause
edit), AEMIC-REQ-064 (new `MissingCitationTextError` table row),
AEMIC-REQ-065 (one new sentence disposing of the non-eligible-path
non-raising question), AEMIC-REQ-072 (signature block widened to five
parameters), AEMIC-REQ-074 (one new sentence classifying the
missing-citation condition as malformed input, citing AEM-REQ-023's own
precedent for classifying a structurally-incomplete-but-superficially-valid
input as malformed rather than a substantive result), AEMIC-REQ-075
(determinism tuple extended to name `citation_text`), AEMIC-REQ-077
("four" → "five" named exceptions), AEMIC-REQ-095 (first quality-review
bullet corrected to record the v1.0 falsification and its repair), the §22
Requirement/Test Matrix (three rows updated: AEMIC-REQ-021-023,
AEMIC-REQ-072-077/AEMIC-REQ-101, AEMIC-REQ-064-071/AEMIC-REQ-101), and §23
Finding Disposition (three rows added).

New requirements appended, no existing identifier reused: **AEMIC-REQ-101**
(§14.1 — the construction-time enforcement rule) and **AEMIC-REQ-102**
(§15 — the security-disposition statement confirming citation-fabrication
risk is unchanged by this repair).

Unchanged, confirmed byte-for-byte: AEMIC-REQ-001-018 (purpose, scope,
package boundary, `EligibleAuthorityDeclaration`'s own shape),
AEMIC-REQ-021-030 (`AuthorityEvaluationOutcome`'s shape and immutability,
`EvaluationResult`'s closed enum, disclosure-only semantics, AEMIC-REQ-030's
citation-source-of-truth rule), AEMIC-REQ-034-063 (drift-limitation
disclosure, identity/versioning, the Registry ABC, filesystem persistence
contract), AEMIC-REQ-066-071 (Registry-layer exceptions and the
no-generic-collapse discipline), AEMIC-REQ-073/076 (no-Registry-dependency,
no-side-effects), AEMIC-REQ-078-081 (the security table itself, minus the
new AEMIC-REQ-102 addendum; auditability), AEMIC-REQ-082-094 (auditability
reconstructibility, deferred integration boundary, serialization/digest
contract, No-Go Boundary Confirmation §19), AEMIC-REQ-096-099 (unresolved
implementation-critical decisions, Amendment Contract).

---

## 8. Security Analysis

Verified the repaired contract prevents:

- **Caller-controlled citation fabrication.** Not newly introduced or
  worsened (§15, AEMIC-REQ-102). Before this repair, no channel existed
  for `evaluate()` to receive `citation_text` at all — the only way to
  produce an `eligible` outcome carrying one was to bypass `evaluate()`
  entirely and construct `AuthorityEvaluationOutcome` directly, which
  reaches `AuthorityEvaluationOutcome`'s own construction-time invariant
  (AEMIC-REQ-022) but bypasses `evaluate()`'s own determination of
  `evaluation_result` (now AEMIC-REQ-101) altogether — the exact risk
  Phase 147F's own §18 named as BF-147F-1's practical consequence. After
  this repair, a caller still supplies the raw text value (this package
  still cannot verify it against a `DecisionTemplate` artifact, since none
  exists — AEMIC-REQ-032's disclosed, unclosed limitation, unchanged), but
  can no longer produce a well-formed `eligible` outcome through the one
  specified path without supplying *some* citation, and `evaluation_result`
  itself remains entirely uninfluenced by whatever value is supplied.
- **Fabricated eligible outcomes.** `MissingCitationTextError` (new,
  AEMIC-REQ-101) closes the specific path BF-147F-1 showed was
  previously either unsatisfiable through `evaluate()` or achievable only
  by bypassing it.
- **Inconsistent declaration/outcome pairs.** `declaration_ref`
  (AEMIC-REQ-038) and its derivation from `(template_ref,
  template_version)` are untouched by this repair.
- **Bypass of disclosure-only semantics.** §8 (AEMIC-REQ-027-029) is
  byte-for-byte unchanged. `citation_text` remains disclosure content
  only — never itself evaluated, verified, or treated as evidence of
  authority (AEMIC-REQ-020's own restated text makes this explicit for the
  new parameter specifically).

---

## 9. Compatibility Analysis

Confirmed the repair:

- **Does not require schema changes.** `decision_template.schema.json`'s
  `eligible_authority` field (AEMIC-REQ-030's citation source) is
  unmodified; no schema file references `citation_text`,
  `authority_evaluation`, or AEMIC-001 at all.
- **Does not require runtime changes.** No `pcae.authority_evaluation`
  package exists (§4 above); `src/pcae/runtime/**` is untouched.
- **Does not require IWC-001 changes.** §17's deferred-integration
  boundary (AEMIC-REQ-083-086) is byte-for-byte unchanged; `Session` and
  `PublicationReadinessPackage` are not referenced by this repair.
- **Does not require PEC-001 changes.** `governance/publication/coordinator.py`
  and `record.py` are unreferenced by this repair, exactly as in v1.0.
- **Does not invalidate AEM-001.** Confirmed the decisive point of this
  entire repair: AEM-REQ-007's closed six-field Declaration shape is
  untouched (Candidate 1 was rejected specifically to preserve this);
  AEM-REQ-016's two-evidentiary-input purity guarantee for
  `evaluation_result` is untouched (`citation_text` carries no evaluative
  weight); AEM-REQ-018's `AuthorityEvaluationOutcome` shape is untouched;
  AEM-REQ-023's malformed-input carve-out precedent is extended, not
  contradicted (AEMIC-REQ-074's new sentence cites it directly).
- **Does not invalidate Phase 147D architecture except where explicitly
  repaired.** Phase 147D §6.2 never named a `citation_text` parameter at
  all — this repair fills a gap Phase 147D's own architecture left open,
  it does not reverse a Phase 147D design choice Phase 147D affirmatively
  made. No other Phase 147D architectural choice (the Registry ABC shape,
  the exception hierarchy, the persistence deferral, the module layout) is
  referenced by this repair.

---

## 10. Finding Disposition

| Finding | Origin | Disposition |
|---|---|---|
| **BF-147F-1** | Phase 147F | **Repaired.** `citation_text` is now `evaluate`'s own fifth parameter (§5, AEMIC-REQ-019), enforced at construction time by AEMIC-REQ-101 (§14.1). `EligibleAuthorityDeclaration`'s closed shape is unchanged; widening it was considered and rejected as foreclosed by AEM-REQ-007 (§5 above). |
| F-147F-2 (Unicode normalization, AEMIC-REQ-036) | Phase 147F | **Unaffected; remains open, Non-Blocking.** Unrelated to `citation_text` or BF-147F-1 in any way; explicitly out of this repair's own scope, per the governing prompt's own instruction to repair BF-147F-1 only. |
| F-147F-3 (forbidden-import test not yet extended) | Phase 147F | **Unaffected; remains open, Non-Blocking.** A future implementation phase's own concern; no AEMIC-001 text required correction on its account. |

No finding is marked resolved without the disposition stated above,
restating AEMIC-REQ-100's own discipline. No Blocking finding remains open
against AEMIC-001.

---

## 11. No-Go Confirmation

This phase did not modify production code, tests, schemas, AEM-001,
IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001, GAC-001,
runtime, or any authority boundary. `git status --short` immediately
before this report was written showed a clean tree with exactly one
modified file (`docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`).
The only files this phase creates or modifies are: the repaired contract
itself, this report, and ordinary governance bookkeeping (task/phase
lifecycle files, `PROJECT_STATUS.md`, `.pcae/phase-completion-*`) at phase
close. No `pcae.authority_evaluation` package, no
`EligibleAuthorityDeclaration`, `AuthorityEvaluationOutcome`, or Registry
implementation was created.

Validation commands (run before this report was finalized):

- `pcae check`
- `pcae health`
- `pcae doctor task-memory`
- `pcae runtime inspect`
- `pcae push --check`
- `python -m pytest -m fast_green -n auto -q`

Results are recorded in `.pcae/phase-completion-metadata.json`'s own
`validation_results` array for this phase. Runtime remains: State:
Observed / Maximum Capability: observe / Execution Availability:
unavailable — unaffected by this phase, consistent with every prior AEMIC
phase (147B/147C/147D/147E/147F).

---

## 12. Overall Verdict

**IMPLEMENTATION CONTRACT REPAIRED.**

BF-147F-1 is resolved: `citation_text` is now reachable through
`evaluate()`'s own fifth parameter, enforced at construction time by a new
requirement (AEMIC-REQ-101) and a new typed exception
(`MissingCitationTextError`), with `AuthorityEvaluationOutcome`'s own
if-and-only-if invariant (AEMIC-REQ-022) now satisfiable for every one of
the three `EvaluationResult` values via the contract's own sole specified
construction path. Candidate repair 1 (widening `EligibleAuthorityDeclaration`)
was evaluated and rejected as foreclosed by AEM-001's own closed-shape
freeze, not merely as architecturally inferior. No other defect was
introduced: every requirement outside §5, §9, §13.1, §14, §15, §20, §22,
and §23 is preserved byte-for-byte from v1.0. F-147F-2 and F-147F-3 remain
open, Non-Blocking, and explicitly out of this repair's own scope.

---

## 13. Recommended Next Phase

**147F.1 — Authority Evaluation Model Implementation Contract Independent
Re-Verification.**

This phase must independently reconstruct the repaired contract again —
not merely re-read this report's own account of the repair — and
specifically attempt to falsify: the repaired citation flow (§5, §9, §14.1
above); the `evaluate()` API's own new five-parameter shape and its
interaction with AEM-REQ-016's two-evidentiary-input purity guarantee; the
construction invariants (AEMIC-REQ-022 and the new AEMIC-REQ-101 together);
and the disclosure-only security properties (§8, unchanged, but worth
re-attacking given the new parameter). No implementation of
`pcae.authority_evaluation` may begin until the repaired contract is
independently verified. This recommendation is not an authorization.

---

**End of Phase 147E.1 report.**
