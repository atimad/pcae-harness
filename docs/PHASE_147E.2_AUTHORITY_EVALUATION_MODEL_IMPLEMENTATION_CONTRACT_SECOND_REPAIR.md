# Phase 147E.2 — Authority Evaluation Model Implementation Contract Second Repair

**Phase ID:** 147E.2
**Mode:** Narrow Contract Repair
**Predecessor:** Phase 147F.1 — Authority Evaluation Model Implementation
Contract Independent Re-Verification (verdict: REPAIR NOT VERIFIED —
BF-147F-1 confirmed fully repaired; one new, distinct Blocking finding
independently discovered, BF-147F.1-1)
**Governed artifact:** `docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`
(AEMIC-001), repaired from v1.1 to v1.2 in place by this phase
**Human authorization:** This phase is authorized to repair BF-147F.1-1
only. No production implementation is authorized. No implementation of
`pcae.authority_evaluation` may begin until AEMIC-001 v1.2 is
independently verified (147F.2, not authorized by this phase).

---

## 1. Executive Summary

Phase 147F.1's independent re-verification of AEMIC-001 v1.1 confirmed
Finding BF-147F-1 (the `citation_text` plumbing gap Phase 147E.1 repaired)
is fully and correctly repaired, but independently discovered a second,
distinct Blocking defect: **BF-147F.1-1**.
`AuthorityEvaluationOutcome.template_ref` and `.template_version` (§6,
AEMIC-REQ-021) are mandatory, unconditional output fields for all three
`EvaluationResult` branches, described as "verbatim copy of the
evaluation's own input" — but `evaluate()`'s own frozen five-parameter
signature (§14, AEMIC-REQ-072, unchanged by the 147E.1 repair) never
accepted `template_ref`/`template_version` as parameters at all. For the
`ELIGIBLE`/`INELIGIBLE` branches a value could be undocumentedly derived
from `declaration.template_ref`/`.template_version`; for the
`INDETERMINATE` branch, `declaration is None` by definition, and no other
input carried either value — making a mandatory field's construction
impossible for one of exactly three closed branches `evaluate()` is
required to support.

This phase independently reproduced the defect from AEMIC-001 v1.1's own
text (§3 below) — including re-deriving the specific asymmetry between
`declaration_ref`'s own correctly-conditional table entry and
`template_ref`/`template_version`'s incorrectly-unconditional one, the
same textual signal Phase 147F.1's own report identified — evaluated all
seven candidate repair families the governing prompt named (§5), and
selected the minimum correct one: adding `template_ref: str` and
`template_version: str` as `evaluate()`'s own first two parameters
(widening the signature from five to seven), with a new, deterministic
verification rule (AEMIC-REQ-103) requiring `evaluate()` to check
`declaration.template_ref`/`.template_version` against these two new
parameters whenever a Declaration resolved, failing closed via a new
typed exception, `TemplateIdentityMismatchError`, on any disagreement.

AEMIC-001 is now v1.2. §5, §6 (note-only), §10.2 (note-only), §13.1, §14
(including a new §14.2 subsection), §15 (note-only plus one new row), §16
(note-only), §18 (note-only), §20, §22, and §23 were amended; every other
section is byte-for-byte unchanged from v1.1. No `AEMIC-REQ-###`
identifier was renumbered, reassigned, retired, or reused; five new
identifiers were appended (AEMIC-REQ-103 through AEMIC-REQ-107). No
production code, test, schema, or other contract was modified.

**Overall Verdict: IMPLEMENTATION CONTRACT SECOND REPAIR COMPLETE.**

Recommended next phase: **147F.2 — Authority Evaluation Model
Implementation Contract Second Repair Independent Verification** (a
recommendation, not an authorization; §24).

---

## 2. Authorization and Scope

This phase is authorized, per the governing prompt, to repair BF-147F.1-1
only. It shall not: modify `src/pcae/**` or `tests/**`; implement
`pcae.authority_evaluation` or any concrete Registry; modify any schema
file; modify AEM-001, IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001,
TAMPC-001, or GAC-001; modify `Session`, `PublicationReadinessPackage`, or
`PublicationCoordinator`; add publication gating; change runtime, policy,
or strategic lineage; or repair F-147F.1-2, F-147F.1-3, F-147F.1-4, or the
direct-construction Informational observation (unless a wording correction
proved inseparable from BF-147F.1-1's own repair — none was). §22 (No-Go
Confirmation) below restates this as an audited fact of this phase's own
execution.

The repair must, at minimum: establish a lawful, deterministic source for
`AuthorityEvaluationOutcome.template_ref`/`.template_version` for every
required evaluation result including `INDETERMINATE`; preserve all
unaffected AEMIC-001 v1.1 requirements; and not redesign the Authority
Evaluation Model.

---

## 3. BF-147F.1-1 Independent Reproduction

Before editing AEMIC-001, this phase independently reproduced the defect,
restating and re-performing (not merely re-reading) Phase 147F.1's own
§20 analysis:

**Step 1 — locate the two requirements in tension.**
`AuthorityEvaluationOutcome`'s own eight-field table (§6, AEMIC-REQ-021)
names `template_ref` and `template_version` both "Yes" (mandatory), with
no branch exception, described as "Verbatim copy of the evaluation's own
input." `evaluate()`'s own frozen signature (§14, AEMIC-REQ-072, prior to
this repair) accepted exactly five parameters — `claimed_identity`,
`declaration`, `evaluated_at`, `evaluator_version`, `citation_text` — none
named `template_ref` or `template_version`.

**Step 2 — enumerate every value reachable inside `evaluate()`'s own
body for each of the three branches.** `ELIGIBLE`/`INELIGIBLE`: `declaration`
is non-`None`; `declaration.template_ref`/`.template_version` exist
(`EligibleAuthorityDeclaration`'s own six-field shape, AEMIC-REQ-015,
includes both) and are the only plausible source — but no requirement
anywhere in v1.1's text actually states this derivation; it is an
undocumented coincidence of the two types happening to share field names,
not a specified contract path. `INDETERMINATE`: `declaration is None`
(AEMIC-REQ-024's own third-branch condition); `declaration` carries no
fields to draw from because it does not exist; none of `evaluate()`'s
other four inputs (`claimed_identity`, `evaluated_at`, `evaluator_version`,
`citation_text`) carries either value. **No well-formed call to
`evaluate()` yielding `INDETERMINATE` can construct a valid
`AuthorityEvaluationOutcome` under v1.1's own text as written.**

**Step 3 — is this a genuine gap, or a reading artifact?** Checked
`AEMIC-REQ-019`'s own table (§5) for an implicit "source:
`declaration.template_ref` if present, otherwise [undefined]" note — none
exists; the table omits `template_ref`/`template_version` as parameters
entirely. Checked §10.1 (AEMIC-REQ-036/037) for an implicit resolution —
these sections govern identifier *syntax* and the *canonical identity
tuple* as a concept, not `evaluate()`'s own parameter sourcing; no
resolution found. Checked `declaration_ref`'s own derivation rule
(AEMIC-REQ-038: "deterministically derived from the evaluated
Declaration's own `(template_ref, template_version)` pair") for whether it
implies availability — true only for `ELIGIBLE`/`INELIGIBLE`, where
`declaration_ref` is itself required non-`None`; for `INDETERMINATE`,
`declaration_ref` is correctly permitted `None` (AEMIC-REQ-021's own
conditional: "`None` iff `indeterminate`"), but `template_ref`/
`template_version` are given no matching conditional in the same table row
group — an asymmetry within the very same requirement, independent
evidence the omission is a genuine specification gap: whoever authored
AEMIC-REQ-021's table correctly reasoned about `declaration_ref`'s
conditional availability but did not apply the identical reasoning to
`template_ref`/`template_version`. This independently confirms Phase
147F.1's own finding (its report's §20), reached before that report's own
text was consulted a second time for comparison purposes only.

**Step 4 — confirm the defect predates this contract's own repair
history.** Checked Phase 147D's own illustrative sequences (§6.7-6.8 of
that report) — `evaluate(claimed_identity, declaration)`, even narrower
than AEMIC-001's own four-/five-/now-seven-parameter closure, likewise
never names `template_ref`/`template_version`, confirming the gap predates
AEMIC-001 v1.0 (Phase 147E) entirely, tracing to Phase 147D's own
architecture never resolving it. Checked Phase 147F's own independent
verification report (its §3, line 323) — its own reconstructed
`evaluate()` call also omits both parameters, independently confirming
neither phase's own reconstruction noticed the gap before Phase 147F.1
did.

**Step 5 — every requirement affected.** Directly affected: AEMIC-REQ-019,
AEMIC-REQ-020 (§5's own parameter table and closure statement),
AEMIC-REQ-021 (§6's "Notes" column for the two fields), AEMIC-REQ-038
(§10.2, one clarifying note), the §13.1 exception table (one new row),
AEMIC-REQ-072, AEMIC-REQ-074, AEMIC-REQ-075, AEMIC-REQ-077 (§14's
signature, malformed-input classification, determinism tuple, and
exception-count statements). Not affected, confirmed by direct
re-reading: §4 (`EligibleAuthorityDeclaration`'s own shape — sound, not
independently required to change, restating the governing prompt's own
instruction not to modify it absent independent necessity); §7 (the
closed enum — sound); §8 (disclosure-only semantics — sound, and
independently confirmed unweakened at §15 below); §9 (citation
reconciliation — entirely orthogonal to template identity, confirmed
untouched); §11 (the Registry ABC — sound, `resolve()`'s own signature is
unaffected, confirmed at §17 below); §12 (persistence — unaffected); §17
(deferred integration boundary — unaffected, confirmed at §16 below); §19
(Phase 147E's own historical No-Go text — unaffected); §21, §24
(Amendment discipline, Non-Goals — unaffected).

---

## 4. Governing Constraints

Reconstructed from AEM-001, AEMIC-001 v1.1, Phase 147D, Phase 147F, Phase
147F.1, the Decision Template schema, the current Session model, and
current publication/workflow boundaries, restating the ten properties the
governing prompt requires be preserved at minimum:

1. **The frozen six-field declaration shape** (AEM-REQ-007, AEMIC-REQ-015/016)
   — unchanged; not independently required to change, and this repair does
   not touch it.
2. **Disclosure-only semantics** (§8, AEMIC-REQ-027-029) — unaffected;
   `TemplateIdentityMismatchError` is a fail-closed structural rejection,
   never a grant/deny/authorize-shaped decision.
3. **Pure deterministic evaluation** (§14, AEMIC-REQ-074/075) — extended,
   not weakened, to cover the two new parameters (§14.2 below,
   AEMIC-REQ-105).
4. **Read-only Registry behavior** (§11, AEMIC-REQ-042-044) — unaffected;
   `evaluate` still never calls `resolve` (AEMIC-REQ-073, confirmed
   unchanged, §17 below).
5. **No hidden runtime lookup** — unaffected; `template_ref`/
   `template_version` are caller-explicit parameters, never ambient or
   Session-derived (Candidate G, §5 below, rejected outright).
6. **No workflow or publication dependency** (§17, AEMIC-REQ-083-086) —
   unaffected, confirmed unchanged at §16 below.
7. **No schema modification** — none made; confirmed at §22 below.
8. **No downstream integration** — unaffected; this repair is internal to
   `pcae.authority_evaluation`'s own package boundary.
9. **No fabricated template identity** — the central purpose of this
   repair: `TemplateIdentityMismatchError` forecloses exactly this risk
   where a Declaration and a caller's own stated identity disagree.
10. **Exact result identity and serialization rules** (§18,
    AEMIC-REQ-087-093) — unaffected in shape; newly satisfiable in practice
    for `INDETERMINATE` (§14 below).

---

## 5. Candidate Repair Evaluation

Seven candidate families were independently assessed, per the governing
prompt's own required minimum, against the selection criteria at §6 of the
governing prompt (lawful source for every branch; source exists before
outcome construction; caller-explicit and testable; declaration identity
cannot silently override request identity; deterministic mismatch
handling; no global/ambient lookup; evaluator purity preserved;
disclosure-only semantics preserved; unchanged Registry responsibility; no
downstream integration; minimal, straightforward, and test-improving).

### Candidate A — Add template identity to a new `AuthorityEvaluationRequest` wrapper object

**Rejected.** This is precisely the request-wrapper design v1.1's own
AEMIC-REQ-019 already considered and declined: "no request wrapper object
required for v1.0... introducing one would add a sixth public type AEM-001
never requires." Re-assessed independently rather than merely deferred to
that prior text: introducing `AuthorityEvaluationRequest` now would
require either bundling all seven of `evaluate()`'s own parameters into
the new type (a substantially larger surface-area change than Candidate B,
for no functional gain) or a partial wrapper carrying only
`template_ref`/`template_version` (adding one indirection layer a caller
must construct, with no clearer canonical-source guarantee than two plain
parameters already provide). Rejected as disproportionate: BF-147F.1-1 is
a two-field sourcing gap, not evidence the flat-parameter design has
failed.

### Candidate B — Add two parameters, `template_ref` and `template_version`, directly to `evaluate()`

**Selected.** No API fragmentation (one function, unchanged call shape);
no duplicated request data; parameter count grows from five to seven,
proportionate to the two-field gap, mirroring the 147E.1 repair's own
four-to-five growth for the analogous `citation_text` gap; the only
mismatch risk this introduces is the one it itself closes via
`TemplateIdentityMismatchError`.

### Candidate C — Derive template identity from `EligibleAuthorityDeclaration` alone

**Rejected**, restating the governing prompt's own instruction: "A
candidate that cannot satisfy INDETERMINATE is invalid." `declaration is
None` for `INDETERMINATE` by definition; there is nothing to derive from.
This is the same undocumented derivation BF-147F.1-1 itself identified as
insufficient for two of three branches and outright absent for the third.

### Candidate D — Make outcome template identity conditional (absent for `INDETERMINATE`)

**Rejected.** Would narrow an existing guarantee: AEMIC-REQ-081 (§16)
names `template_ref`/`template_version` among the "minimum auditable
evidence" every outcome "MUST expose," with no branch exception — making
them conditional would be a genuine auditability regression (an
`indeterminate` outcome could no longer disclose *which* Decision Template
no Declaration existed for). Also incompatible with AEM-001's own framing
of `indeterminate` as a substantive, auditable result, not a degraded one.

### Candidate E — A separate immutable `DecisionTemplateIdentity` value object

**Rejected as over-engineered** relative to Candidate B for equal benefit:
adds a sixth public type (the same objection foreclosing Candidate A) to
bundle exactly two `str` fields with no validation or behavior beyond
non-emptiness (AEMIC-REQ-036) — no cohesion argument justifies a dedicated
type here that two plain parameters do not already satisfy.

### Candidate F — Registry-derived template identity for declaration-absent cases

**Rejected outright.** Would expand the Registry from a pure
`resolve(template_ref, template_version) -> Declaration | None` lookup
(AEMIC-REQ-042) into an identity oracle answering a question orthogonal to
what it was ever asked to resolve — and inverts causality: a caller must
already possess `template_ref`/`template_version` *before* calling
`resolve` at all, so the Registry cannot be the source of a value its own
signature requires as input.

### Candidate G — Hidden lookup or ambient context

**Rejected outright**, restating the governing prompt's own presumptive
invalidity. Any such source violates AEMIC-REQ-010's forbidden-import
rules and AEMIC-REQ-073's "no I/O of any kind" purity guarantee
simultaneously; `evaluate` would no longer be a pure function of its own
explicit arguments.

### Comparison table

| Axis | A (wrapper) | B (selected) | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| Satisfies `INDETERMINATE` | Yes | Yes | **No — foreclosed** | Yes (by weakening) | Yes | Yes (by scope creep) | Yes (by purity violation) |
| New public type | Yes | **No** | N/A | No | Yes | No | N/A |
| Minimal / proportionate | No | **Yes** | N/A | No (narrows a guarantee) | No | No (expands Registry) | No (violates purity) |
| Deterministic mismatch handling | Achievable, more surface | **Yes, minimal surface** | N/A | N/A (no comparison possible) | Achievable, more surface | Undermines Registry read-only boundary | N/A |
| Compatible with AEM-001 / no narrowing | Yes | **Yes** | N/A | **No** | Yes | Yes | No |
| Forbidden-import / purity preserved | Yes | **Yes** | N/A | Yes | Yes | Yes | **No** |

---

## 6. Selected Repair

Candidate B. `template_ref: str` and `template_version: str` are added as
`evaluate`'s first two parameters (§5, AEMIC-REQ-019; §14, AEMIC-REQ-072),
ahead of `claimed_identity` — widening the signature from five to seven
parameters, with only `citation_text` retaining a default value.
`evaluate` enforces the canonical-identity and mismatch rules itself,
before determining `evaluation_result` or constructing any outcome (new
§14.2, AEMIC-REQ-103-106):

1. Validate `template_ref`/`template_version` are each non-empty `str`
   (`InvalidTemplateReferenceError`).
2. Validate `claimed_identity` is a non-empty `str`
   (`InvalidClaimedIdentityError`).
3. If `declaration` is non-`None`, verify
   `declaration.template_ref == template_ref` and
   `declaration.template_version == template_version` by exact `str`
   equality; raise `TemplateIdentityMismatchError` (new, §13.1) on any
   disagreement.
4. Determine `evaluation_result` exactly as §7 already specifies, from
   exactly the two evidentiary inputs AEM-REQ-016 names — unaffected by
   the two new parameters.
5. If `evaluation_result == ELIGIBLE` and `citation_text is None`, raise
   `MissingCitationTextError` (unchanged, AEMIC-REQ-101).
6. Construct the outcome with `template_ref`/`template_version` copied
   verbatim from `evaluate`'s own parameters — never from `declaration` —
   for every branch, including `INDETERMINATE`.

---

## 7. Canonical Identity Source

`evaluate`'s own `template_ref`/`template_version` parameters are the
**single canonical source** of `AuthorityEvaluationOutcome.template_ref`/
`.template_version` for every branch (AEMIC-REQ-103). Declaration identity
is used **only for validation** against this source — it never overrides,
supplements, or is silently preferred; there is no implicit "prefer one,
fall back to the other" rule anywhere in the repaired contract. When both
sources exist (`ELIGIBLE`/`INELIGIBLE`), agreement is required and
enforced deterministically (`TemplateIdentityMismatchError` on mismatch);
when only the request-level source exists (`INDETERMINATE`), it alone
governs, exactly as it always could have if it had been reachable.

---

## 8. Public Type Changes

No new public type is introduced (Candidates A and E, both rejected, §5
above). `AuthorityEvaluationOutcome`'s own eight-field shape (§6) is
unchanged — every field name, type, and mandatory/optional disposition is
identical to v1.1; only the "Notes" column's own sourcing description is
corrected for `template_ref`/`template_version` to name the new canonical
source. `EligibleAuthorityDeclaration` is unchanged — not independently
required, and this repair does not touch it, restating the governing
prompt's own instruction. The only widened public surface is `evaluate`'s
own function signature (§14), not a "type" in this contract's own §11
sense.

---

## 9. Evaluator Signature

```
evaluate(
    template_ref: str,
    template_version: str,
    claimed_identity: str,
    declaration: EligibleAuthorityDeclaration | None,
    evaluated_at: str,
    evaluator_version: str,
    citation_text: str | None = None,
) -> AuthorityEvaluationOutcome
```

Seven parameters; only `citation_text` retains a default. `template_ref`/
`template_version` are placed first because they identify *which* Decision
Template this evaluation is against, logically prior to and independent of
whichever identity is being claimed against it.

**Source matrix** (every mandatory `AuthorityEvaluationOutcome` field,
proving construction is possible for every result state):

| Outcome field | Canonical source | Validation |
|---|---|---|
| `template_ref` | `evaluate`'s own `template_ref` parameter | Non-empty `str` (`InvalidTemplateReferenceError`); if `declaration` non-`None`, must equal `declaration.template_ref` (`TemplateIdentityMismatchError`) |
| `template_version` | `evaluate`'s own `template_version` parameter | Non-empty `str` (`InvalidTemplateReferenceError`); if `declaration` non-`None`, must equal `declaration.template_version` (`TemplateIdentityMismatchError`) |
| `claimed_identity` | `evaluate`'s own `claimed_identity` parameter | Non-empty `str` (`InvalidClaimedIdentityError`) |
| `evaluation_result` | Evaluator logic (set-membership test, or `INDETERMINATE` if `declaration is None`) | Closed three-value enum |
| `declaration_ref` | Derived from `declaration`'s `(template_ref, template_version)` when non-`None`; else `None` | Branch-dependent |
| `citation_text` | `evaluate`'s own `citation_text` parameter, copied iff `evaluation_result == ELIGIBLE` | `MissingCitationTextError` |
| `evaluated_at` | `evaluate`'s own `evaluated_at` parameter | Non-empty `str`, ISO-8601 (structural only) |
| `evaluator_version` | `evaluate`'s own `evaluator_version` parameter | None beyond `str` |
| `schema_version` | Fixed literal `"aem-outcome/1.0"` | Construction-time literal check |

Every mandatory field now has a reachable, closed-input source for every
one of the three branches — the property BF-147F.1-1 identified as absent
for `template_ref`/`template_version` in the `INDETERMINATE` row
specifically.

---

## 10. Branch-by-Branch Construction Analysis

- **`ELIGIBLE`:** `declaration` non-`None`, `claimed_identity ∈
  declaration.eligible_identities`. `template_ref`/`template_version`
  sourced from `evaluate`'s own parameters, verified equal to
  `declaration`'s own values (else `TemplateIdentityMismatchError`).
  `citation_text` required non-`None` (else `MissingCitationTextError`,
  unaffected).
- **`INELIGIBLE`:** `declaration` non-`None`, `claimed_identity ∉
  declaration.eligible_identities`. Identical sourcing/mismatch discipline
  to `ELIGIBLE`. `citation_text` forced `None` regardless of caller input.
- **`INDETERMINATE`:** `declaration is None`. `template_ref`/
  `template_version` sourced from `evaluate`'s own parameters — the only
  source that exists, now lawful; no mismatch check performed (nothing to
  compare against). `declaration_ref` is `None` (unaffected).
  `citation_text` forced `None`. **This is the branch BF-147F.1-1 found
  unconstructible under v1.1; it is now fully constructible.**

---

## 11. Failure Taxonomy

Six §13.1 exceptions (five existing, unchanged, plus
`TemplateIdentityMismatchError`); two §13.2 exceptions (unaffected,
Registry-layer only). `TemplateIdentityMismatchError`: trigger —
`declaration` non-`None` and its own `(template_ref, template_version)`
disagrees with `evaluate`'s own two identity parameters; inheritance —
direct subclass of `AuthorityEvaluationError`, sibling to the other five;
classification — Domain (caller/workflow error); retryable — No; message
requirements — restates §13's existing narrative (state the condition,
never fabricate a fallback outcome); serialization/reporting — restates
AEMIC-REQ-071 unchanged (maps to a future CLI/transport surface's own
closed error taxonomy). Missing or malformed request identity is
`InvalidTemplateReferenceError` (unchanged, scope widened, never
conflated with `TemplateIdentityMismatchError`).

---

## 12. Error Precedence

Frozen ordering within `evaluate()` (AEMIC-REQ-104-105): (1)
`template_ref`/`template_version` structural validity; (2)
`claimed_identity` structural validity; (3) template identity mismatch
(only when `declaration` non-`None`); (4) `evaluation_result`
determination; (5) `citation_text` enforcement for `ELIGIBLE`. A more
authoritative, earlier-ordered failure is never masked by a later-ordered
one — verified independently: a call with both a malformed `template_ref`
and a mismatched `declaration` raises `InvalidTemplateReferenceError`,
never `TemplateIdentityMismatchError`; a call with both a mismatched
`declaration` and a missing `citation_text` on an otherwise-`ELIGIBLE`-shaped
input raises `TemplateIdentityMismatchError`, never
`MissingCitationTextError`. Registry-layer conditions (unavailable,
corrupt, duplicate) occur strictly upstream of any `evaluate()` call
(AEMIC-REQ-073) and are never reachable from within it — the two
precedence domains are not merged, since different components enforce
them at different times.

---

## 13. Determinism

AEMIC-REQ-075 now reads the full tuple `(template_ref, template_version,
claimed_identity, declaration, evaluated_at, evaluator_version,
citation_text)`; identical values produce a field-identical outcome or an
identical raised exception (AEMIC-REQ-105). `evaluated_at` remains
observational, unchanged, not part of the determinism tuple's own
content-equality requirement.

---

## 14. Serialization

Unaffected in requirement text beyond one clarifying paragraph appended
after AEMIC-REQ-093 (§18) confirming this repair changes no serialization
requirement — `AuthorityEvaluationOutcome`'s shape always required
`template_ref`/`template_version` as mandatory, always-emitted fields;
this repair supplies `evaluate` with a lawful way to *construct* an
`INDETERMINATE` instance in the first place, so `to_payload`/`from_payload`
can now round-trip an `INDETERMINATE` outcome carrying complete template
identity, where none could previously have existed to serialize.

---

## 15. Security Review

Attacked, per the governing prompt's own list: **caller-supplied template
substitution** and **declaration/request identity mismatch** are the two
attacks this repair directly closes via `TemplateIdentityMismatchError`'s
own fail-closed check. **Version substitution** is the identical attack at
the `template_version` component, covered by the same exact-equality
check over the full tuple. **Stale declaration replay** is unaffected
(AEMIC-REQ-051's own named limitation, unchanged). **Arbitrary identity
fabrication:** a caller can still supply any `template_ref`/
`template_version` when `declaration is None` (`INDETERMINATE`, nothing to
check against) — not a new risk, since no mechanism anywhere in AEMIC-001
authenticates any caller-supplied `str`, only cross-checks agreement
between two independently-obtained values when both exist. **Registry
poisoning** unaffected (ABC still exposes no write path). **Citation/identity
cross-pairing:** independently checked and confirmed non-interacting —
the mismatch check (step 3) is strictly ordered before citation
enforcement (step 5); a call with both defects always raises
`TemplateIdentityMismatchError`, never masking it behind a citation-shaped
error. **Direct outcome construction** bypassing `evaluate()`: unaffected,
restating the Informational finding's own disposition — this repair does
not add constructor-level enforcement, since the mismatch check requires
comparing against a second, independent parameter (`declaration`) only
`evaluate()`'s own signature carries. **Hidden authority escalation** and
**downstream consumer confusion:** unaffected — a matching template
identity does not, by itself, prove authority (new AEMIC-REQ-107 states
this explicitly); no new import-path reach into Runtime, Permission
Broker, or execution capability is introduced. No security property
AEM-001 or AEMIC-001 v1.1 already established is weakened.

---

## 16. Compatibility Review

Confirmed this repair requires no change to `Session`,
`PublicationReadinessPackage`, `PublicationCoordinator`, `record.py`, any
CHGR schema, the Decision Template schema, IWC-001, or PEC-001 (§17,
AEMIC-REQ-083-086, unchanged text — no lifecycle caller of
`pcae.authority_evaluation` exists to be affected, AEMIC-REQ-013). A
standalone future implementation would require callers to pass two
additional arguments to `evaluate()` — no current caller exists, and none
is authorized here (§2.2, AEMIC-REQ-004). Compatible with AEM-001's own
frozen declaration shape (untouched); existing schema records (none
touched); an absent concrete Registry implementation (§3.3, still zero
concrete subclass — `AuthorityRegistry`'s own ABC signature, AEMIC-REQ-042,
is unchanged: this repair widens `evaluate()`'s own inputs, never
`resolve()`'s); old sessions/readiness packages/CHGR bundles (none
reference this package); and package isolation (§3.4/§3.5, forbidden-import
rules and zero-dependency-direction unaffected).

---

## 17. Registry Boundary

Confirmed unaffected and unexpanded. The Registry continues to answer
`resolve(template_ref, template_version) -> Declaration | None` only
(unchanged) — never asked, and this repair never asks it, to supply
identity for a declaration-absent case (Candidate F, rejected, §5).
Registry results, when present, are checked against `evaluate()`'s own
request-level identity, never the reverse. Registry absence
(`INDETERMINATE`) does not erase request identity — `template_ref`/
`template_version` remain fully present regardless (this repair's own
central purpose). Registry unavailability remains an entirely distinct,
upstream-of-`evaluate()` condition, never reclassified as
`TemplateIdentityMismatchError` or any other §13.1 exception. Duplicate
handling is unaffected. No Registry mutation is introduced.

---

## 18. Requirement Changes

Amended in place (existing identifiers, text corrected; none retired,
none renumbered): AEMIC-REQ-019 (seven-parameter table, was five — two new
rows), AEMIC-REQ-020 (seven-parameter closure, reworded), AEMIC-REQ-021
(§6 table's "Notes" column for `template_ref`/`template_version`
rewritten), AEMIC-REQ-038 (§10.2, one clarifying sentence),
the §13.1 table (new `TemplateIdentityMismatchError` row;
`InvalidTemplateReferenceError`'s own condition widened to name `evaluate`
as well as `resolve`), AEMIC-REQ-072 (seven-parameter signature block,
with ordering rationale), AEMIC-REQ-074 (new sentence classifying
malformed identity and mismatch as malformed input), AEMIC-REQ-075
(determinism tuple extended), AEMIC-REQ-077 ("five" → "six" named §13.1
exceptions), AEMIC-REQ-081 (§16, one clarifying parenthetical),
a new paragraph following AEMIC-REQ-093 (§18), §20's Contract Quality
Review (two bullets — "Complete enough to implement" and "Testable" —
corrected to record and resolve the BF-147F.1-1 falsification, mirroring
how the 147E.1 repair corrected "Internally coherent" for BF-147F-1), §22's
Requirement/Test Matrix (one new row covering all eighteen scenarios the
governing prompt named; the failure-taxonomy row's exception count updated),
§23's Finding Disposition (BF-147F.1-1 marked Repaired; F-147F.1-2,
F-147F.1-3, F-147F.1-4, and the Informational observation each explicitly
re-affirmed open and out of scope).

New requirements appended, no existing identifier reused:
**AEMIC-REQ-103** (canonical identity source and mismatch verification
rule, §14.2), **AEMIC-REQ-104** (error precedence), **AEMIC-REQ-105**
(determinism of that precedence), **AEMIC-REQ-106** (non-collapse rule for
`TemplateIdentityMismatchError`), **AEMIC-REQ-107** (§15, the
"matching identity does not prove authority" security disposition,
mirroring AEMIC-REQ-102's own precedent).

Unchanged, confirmed byte-for-byte: AEMIC-REQ-001-018
(`EligibleAuthorityDeclaration`'s own shape), AEMIC-REQ-024-037 (closed
enum, disclosure-only semantics, citation reconciliation §9, identifier
syntax §10.1), AEMIC-REQ-039-071 (schema-version literals,
`evaluator_version`, the Registry ABC §11, filesystem persistence §12, the
pre-existing five §13.1 exceptions and both §13.2 exceptions), AEMIC-REQ-073
/076/078-080/082-092/094/096-102 (no-Registry-dependency, no-side-effects,
the security table's pre-existing rows, auditability reconstructibility,
deferred integration boundary, digest non-requirement, No-Go Boundary
Confirmation §19, unresolved-decisions statement, Amendment Contract,
AEMIC-REQ-102's own citation-fabrication disposition).

---

## 19. Requirement/Test Matrix

One new matrix row (§22 of the contract) covers all eighteen test
scenarios the governing prompt named: (1) `INDETERMINATE` with valid
request identity; (2) `ELIGIBLE` with matching request/declaration
identity; (3) `INELIGIBLE` with matching identity; (4) no declaration plus
complete outcome identity (restates 1); (5) request/declaration
`template_ref` mismatch → `TemplateIdentityMismatchError`; (6)
request/declaration `template_version` mismatch → same; (7) missing
request `template_ref` → `InvalidTemplateReferenceError`; (8) missing
request `template_version` → same; (9) malformed (non-`str`) request
identity → same; (10) unsupported version — not applicable within
`evaluate()`'s own scope (`template_version` carries no
supported/unsupported semantics beyond non-emptiness, AEMIC-REQ-036;
`UnsupportedSchemaVersionError` governs payload `schema_version` only,
§18, an orthogonal concept); (11) Registry absence preserving request
identity; (12) Registry unavailability preserving error classification
(never reclassified as `TemplateIdentityMismatchError`); (13) duplicate
declaration — unaffected, a Registry-layer concern (§13.2) orthogonal to
`evaluate()`'s own scope; (14) citation plus identity mismatch → precedence
verified (`TemplateIdentityMismatchError`, never `MissingCitationTextError`);
(15) deterministic repeated evaluation; (16) serialization round trip; (17)
no hidden Session or workflow lookup (AST-style import-boundary test,
restating the existing forbidden-import matrix row); (18) forbidden
imports (restates the existing row, AEMIC-REQ-010-014, unaffected). Every
modified normative requirement maps to a positive, negative, or
adversarial test per this matrix.

---

## 20. Finding Disposition

| Finding | Origin | Disposition |
|---|---|---|
| **BF-147F-1** | Phase 147F | **Remains Repaired, unaffected and unreopened by this phase.** Phase 147F.1's own §22.1 already confirmed BF-147F-1's repair is complete on its own narrow terms; this phase's own independent re-derivation of governing constraints (§4 above) reaches the identical conclusion and does not re-litigate it. |
| **BF-147F.1-1** | Phase 147F.1 | **Repaired.** `template_ref`/`template_version` are now two of `evaluate`'s own seven parameters (§9 above), the single canonical source of the outcome's own identically-named fields for every branch including `INDETERMINATE` (§7 above). Mismatch fails closed via `TemplateIdentityMismatchError`. `EligibleAuthorityDeclaration`'s closed shape is unchanged. |
| F-147F.1-2 (empty-string citation) | Phase 147F.1 | **Unaffected; remains open, Non-Blocking.** Unrelated to BF-147F.1-1; explicitly out of this repair's own scope. |
| F-147F.1-3 (non-string citation typing) | Phase 147F.1 | **Unaffected; remains open, Non-Blocking.** Unrelated to BF-147F.1-1; explicitly out of scope. |
| F-147F.1-4 (deserialization cross-field ambiguity) | Phase 147F.1 | **Unaffected; remains open, Non-Blocking.** Unrelated to BF-147F.1-1 (a `citation_text` cross-field question, not a `template_ref`/`template_version` sourcing question); out of scope. |
| Informational: direct construction bypassing `evaluate()` | Phase 147F.1 | **Unaffected; remains open, Informational.** This repair does not alter construction authority — `AuthorityEvaluationOutcome`'s own constructor-level invariant (AEMIC-REQ-022) is the identical, unchanged enforcement point. |

No finding is marked resolved without the disposition stated above. No
Blocking finding remains open against AEMIC-001: both BF-147F-1 and
BF-147F.1-1 are Repaired.

---

## 21. Contract Quality Review

After this repair, independently re-verified: every mandatory
`AuthorityEvaluationOutcome` field has a reachable source for every branch
(§9's source matrix above); every branch is implementable (§10); identity
ownership is singular — `evaluate`'s own two parameters, never
`declaration`'s (§7); mismatch behavior is deterministic (§12-13);
`evaluate`'s own signature is complete — seven parameters, all consumed,
none redundant (§9); the failure taxonomy is complete and non-collapsing
— six §13.1 exceptions, each independently triggerable and distinguishable
(§11); serialization is coherent (§14); disclosure-only semantics remain
intact (§15); Registry responsibility is unchanged (§17); no downstream
integration is required (§16); no unresolved implementation-critical
choice remains — the contract's own §20 (Contract Quality Review) records
and resolves the BF-147F.1-1 falsification exactly as it already recorded
and resolved BF-147F-1's. No output field remains dependent on
undocumented inference: the undocumented `declaration.template_ref`
derivation this defect's own root cause traced to is now replaced by an
explicit, normative rule (AEMIC-REQ-103).

---

## 22. No-Go Confirmation

This phase did not modify `src/pcae/**` (no file under
`src/pcae/authority_evaluation/` exists after this phase); `tests/**`; any
schema file under `src/pcae/schema_resources/**`; AEM-001, IWC-001,
IWPC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001, or GAC-001 (confirmed
byte-for-byte unmodified); `Session`, `PublicationReadinessPackage`, or
`PublicationCoordinator`; CHGR construction, verification, or inspection;
Publication gating; runtime state, policy, or strategic lineage. Did not
implement `pcae.authority_evaluation` or any concrete Registry; did not
create a Registry; did not migrate any Decision Template; did not repair
F-147F.1-2, F-147F.1-3, F-147F.1-4, or the Informational observation.

`git status --short` immediately before this report was written showed a
clean tree with exactly one modified file
(`docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`).
The only files this phase creates or modifies are: the repaired contract
itself, this report, and ordinary governance bookkeeping (task/phase
lifecycle files, `PROJECT_STATUS.md`, `.pcae/phase-completion-*`) at phase
close.

Bootstrap and validation commands run before this report was finalized:

- `git status --short` / `git branch --show-current` / `git log
  --oneline --decorate -100` / `git rev-list --count origin/main..HEAD` /
  `git rev-list --count HEAD..origin/main` — repository clean, on `main`,
  0 ahead / 0 behind at phase start.
- `pcae session bootstrap --agent-id claude-local --sync-lock` — lock
  rehydrated, health healthy, recommended next phase confirmed as this one.
- `pcae check` — passed.
- `pcae health` — healthy; required files present; policy valid; git
  status clean.
- `pcae doctor task-memory` — clean, no inconsistencies.
- `pcae runtime inspect` — Runtime state: Observed; Execution capability:
  unavailable; Maximum plugin capability: observe; Registry status: empty;
  Plugin count: 0 — unchanged.
- `pcae push check` — clean, nothing to push, at phase start.

Results at phase close, including
`python -m pytest -m fast_green -n auto -q`, are recorded in
`.pcae/phase-completion-metadata.json`'s own `validation_results` array.
Runtime remains: State: Observed / Maximum Capability: observe / Execution
Availability: unavailable — unaffected by this phase, consistent with
every prior AEMIC phase (147B/147C/147D/147E/147E.1/147F/147F.1).

---

## 23. Overall Verdict

**IMPLEMENTATION CONTRACT SECOND REPAIR COMPLETE.**

BF-147F.1-1 is resolved: every mandatory `AuthorityEvaluationOutcome`
field now has a reachable, closed-input construction source for every one
of the three `EvaluationResult` branches, including `INDETERMINATE`;
identity mismatch behavior is deterministic and fail-closed via the new
`TemplateIdentityMismatchError`; the evaluator signature is complete
(seven parameters, all consumed, none redundant); the failure taxonomy is
coherent and non-collapsing; determinism and serialization requirements
are updated and internally consistent; AEM-001 compatibility,
disclosure-only semantics, and Registry responsibility are all preserved
unweakened; no downstream integration is introduced; no unresolved
implementation-critical decision remains. No other defect was introduced;
every AEMIC-001 v1.1 guarantee outside §5, §6 (note-only), §10.2
(note-only), §13.1, §14, §15 (note-only + one new row), §16 (note-only),
§18 (note-only), §20, §22, §23 is preserved byte-for-byte. F-147F-2,
F-147F-3, F-147F.1-2, F-147F.1-3, F-147F.1-4, and the direct-construction
Informational observation all remain open and explicitly out of this
repair's own scope.

---

## 24. Recommended Next Phase

**147F.2 — Authority Evaluation Model Implementation Contract Second
Repair Independent Verification.**

This phase must independently reconstruct and attempt to falsify: canonical
template-identity ownership (AEMIC-REQ-103); request/declaration identity
agreement and its own mismatch error (AEMIC-REQ-104,
`TemplateIdentityMismatchError`); complete `INDETERMINATE` construction;
error precedence (AEMIC-REQ-104-105); determinism (AEMIC-REQ-075, as
extended); serialization (§18); disclosure-only security (§15, including
the new AEMIC-REQ-107 disposition); and the unchanged Registry and
integration boundaries (§11, §17). No implementation of
`pcae.authority_evaluation` may begin until AEMIC-001 v1.2 is
independently verified. This recommendation is not an authorization.

---

**End of Phase 147E.2 report.**
