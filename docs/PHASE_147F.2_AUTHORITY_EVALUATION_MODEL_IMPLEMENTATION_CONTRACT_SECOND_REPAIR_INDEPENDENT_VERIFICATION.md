# Phase 147F.2 — Authority Evaluation Model Implementation Contract Second Repair Independent Verification

## Contract identity and status

**Phase:** 147F.2
**Mode:** Independent Contract Verification (documentation-only; no
production code, contract, schema, or test file modified; no
implementation authorized)
**Predecessor:** 147E.2 — Authority Evaluation Model Implementation
Contract Second Repair (verdict: IMPLEMENTATION CONTRACT SECOND REPAIR
COMPLETE, AEMIC-001 v1.1 → v1.2, repairing BF-147F.1-1)
**Subject:** AEMIC-001 v1.2 — Authority Evaluation Model Implementation
Contract (`docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`)
**Runtime baseline:** Observed / observe / unavailable — unchanged by
this phase; confirmed at §31 below.

---

## 1. Executive Summary

This phase independently reconstructed BF-147F.1-1 directly from
AEMIC-001 v1.1's own frozen text, re-derived the ten governing
constraints any repair must preserve, independently reassessed all seven
candidate repair families the governing prompt named, verified the
exact v1.1→v1.2 diff line by line against the actual current contract
text, re-derived the evaluator's frozen seven-parameter signature,
constructed truth tables for identity agreement and error precedence,
reconstructed the field-source matrix for every mandatory
`AuthorityEvaluationOutcome` field across all three `EvaluationResult`
branches, attacked the repair's security properties, and performed a
fresh contract-wide implementability sweep rather than checking only
template identity — before treating Phase 147E.2's own account of the
repair as anything more than a starting pointer, per this phase's own
independence discipline (§4).

**BF-147F.1-1 is correctly and completely repaired.** `template_ref` and
`template_version` are now `evaluate()`'s own first two parameters
(AEMIC-REQ-019, AEMIC-REQ-072), the single canonical source of the
identically-named outcome fields for all three `EvaluationResult`
branches, including `INDETERMINATE` — the branch BF-147F.1-1 identified
as unconstructible. `TemplateIdentityMismatchError` (AEMIC-REQ-064,
AEMIC-REQ-103–106) closes the declaration/request identity-mismatch
channel deterministically and fail-closed, ordered before
`evaluation_result` determination and `citation_text` enforcement.
`EligibleAuthorityDeclaration`'s AEM-001-frozen six-field shape is
untouched. Candidate B (two direct parameters) is independently
re-derived here as the minimum correct repair on every axis this phase
assessed; the other six candidates are independently re-confirmed
invalid or inferior for reasons this phase re-derived rather than
accepted from Phase 147E.2's own account.

This phase's own fresh, contract-wide source-completeness sweep (§25),
undertaken because the two prior independent verifications
(Phase 147F, Phase 147F.1) each found a distinct missing mandatory input,
**found no third missing-input defect.** Every mandatory
`AuthorityEvaluationOutcome` field, every named exception's own
triggering condition, and every serialization-mandatory field has a
closed, reachable construction source across all three branches.

One lifecycle/documentation-only, Non-Blocking finding is newly recorded
at §26/§3: the current `.pcae/phase-completion-metadata.json`'s own
`pushed_status` field (`"pending"`) and `origin_main_head`/
`origin_main_head_count` fields (both `0`) are stale relative to the
actual, independently-confirmed git state (Phase 147E.2's repair commit,
`0251a005`, and its metadata-hash-sync commit, `05ccb40d`, are both
present on `origin/main`; `git rev-list --count origin/main..HEAD` and
`HEAD..origin/main` are both `0`; `pcae push check` reports
`nothing_to_push`). This does not alter Phase 147E.2's substantive
contract verdict and does not block this phase's own verification; §3
records why.

**Overall Verdict: SECOND REPAIR VERIFIED WITH NON-BLOCKING FINDINGS.**

BF-147F.1-1 is **Repaired, confirmed** (§5, §13, §24). AEMIC-001 v1.2 is
independently verified as implementation-ready, subject only to the
pre-existing, disclosed, out-of-scope findings this phase re-confirms
unaffected (§24) and the one newly-recorded lifecycle finding above
(§26), neither of which is Blocking.

Recommended next phase: **147G — Authority Evaluation Model Core
Implementation** (§33). This recommendation is not an authorization.

---

## 2. Authorization and Scope

Per the human authorization above this report, this phase is authorized
to independently verify AEMIC-001 v1.2 only. It is explicitly forbidden
from repairing AEMIC-001; modifying `src/pcae/**`, any production test,
any schema, or AEM-001, IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001,
TAMPC-001, or GAC-001; implementing `pcae.authority_evaluation`;
creating a Registry or any production model; changing Session, any
readiness package, Publication Coordinator, CHGR construction, runtime,
policy, or strategic lineage. §29 confirms none of these was touched as
an audited fact of this phase's own execution, not merely a
forward-looking prohibition.

The repair (BF-147F.1-1's disposition, Phase 147E.2) is treated
throughout this report as an **untrusted claim**, evaluated from
primary sources (AEM-001, AEMIC-001's own frozen text, direct source
re-inspection, and this phase's own independent reconstruction), never
accepted on Phase 147E.2's own say-so. Phase 147F.2 is a
**verification**, not a repair, phase; any defect found is reported and
classified, never silently corrected here (§29).

---

## 3. Bootstrap and Phase 147E.2 Finalization Check

**Bootstrap.** `git status --short` — clean. `git branch --show-current`
— `main`. `git rev-list --count origin/main..HEAD` — `0`.
`git rev-list --count HEAD..origin/main` — `0`. `git log --oneline
--decorate -30` confirms `HEAD` (`05ccb40d`) is simultaneously
`origin/main`/`origin/HEAD`, with Phase 147E.2's repair commit
(`0251a005`) and its own metadata-hash-sync commit (`05ccb40d`)
immediately preceding it in the phase-lifecycle sequence, followed only
by the expected 147F.1R/147F.1 recovery and idle-placeholder history.
`pcae session bootstrap --agent-id claude-code --sync-lock` reported the
agent lock already held by `claude-local` (this session's own prior
lock), backend lock rehydrated, health healthy, check passed, active
task the post-147E.2 idle placeholder, recommended next phase confirmed
as 147F.2 (this phase). `pcae check` — passed. `pcae health` — healthy,
required files present, policy valid (repo config), git status clean.
`pcae doctor task-memory` — clean, no inconsistencies. `pcae runtime
inspect` — Runtime state: Observed; Execution capability: unavailable;
Maximum plugin capability: observe; Registry status: empty; Plugin
count: 0; Capability count: 0 — unchanged from every prior AEMIC phase.
`pcae push check` — branch `main`, working tree clean, 0 unpushed
commits, health healthy, check passed, task memory clean, phase report
trust passed, phase report identity passed, mode `nothing_to_push`.
PROJECT_STATUS.md's "## Current Phase" section correctly names Phase
147E.2 as the latest completed phase and correctly states the
147F.2 recommendation verbatim, treated as authoritative per this
phase's own governing instruction.

**Phase 147E.2 report consistency check.** The canonical
`docs/PHASE_147E.2_AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT_SECOND_REPAIR.md`
does not itself contain a literal "Commits:"/"Pushed:" field pair (it
instead documents bootstrap/validation commands run at phase start and
defers close-of-phase results to `.pcae/phase-completion-metadata.json`,
per its own §24/closing text) — this phase's authorization prompt's
characterization of those exact literal fields is therefore read as
referring to `.pcae/phase-completion-metadata.json`'s own
`pushed_status`/`origin_main_head`/`origin_main_head_count` fields,
which this phase independently inspected directly:

| Metadata field (as currently recorded) | Value | Independently observed git/push reality |
|---|---|---|
| `phase_commits[0].hash` | `"0251a005"` | Confirmed real: `0251a005` is Phase 147E.2's own repair commit, present on `origin/main` (`git branch -r --contains 0251a005` lists `origin/main`). This field was itself corrected from a placeholder `"PENDING"` by the immediately-following commit `05ccb40d` ("Phase 147E.2: sync phase-completion metadata commit hash"), the same synchronization pattern this repository's own history shows for every prior phase. **Not stale.** |
| `pushed_status` | `"pending"` | **Stale.** `git rev-list --count origin/main..HEAD` = `0` and `pcae push check` reports `nothing_to_push`; the repository is demonstrably fully pushed and synchronized. This field was written at `phase complete` time (before the actual push occurred) and was never subsequently re-synced to reflect the push, unlike the `phase_commits[0].hash` field, which received its own dedicated sync commit. |
| `origin_main_head` / `origin_main_head_count` | `0` / `0` | **Stale**, for the identical reason: both fields reflect a pre-push snapshot, not the current, fully-synchronized state. |

**Determination (per this phase's own five required findings):**

1. Phase 147E.2 has a real commit (`0251a005`) — confirmed.
2. That commit is present on `origin/main` — confirmed.
3. `pushed_status`/`origin_main_head(_count)` are stale, pre-push-snapshot
   text, not evidence of an actually-incomplete push — confirmed; the
   `phase_commits[0].hash` field alone was separately corrected (a
   dedicated sync commit exists for it), but the three push-state fields
   were not.
4. Metadata contains the correct commit identity (`phase_commits`) but
   stale push-state fields (`pushed_status`, `origin_main_head*`).
5. Report trust and report identity checks pass: `pcae push check`
   itself independently reports `Phase report trust: passed` and `Phase
   report identity: passed` against the current repository state, which
   is the authoritative, live check — not the frozen metadata snapshot.

**Disposition.** The lifecycle is otherwise complete: the task closed
into `tasks/DONE.md` (entry confirmed: `Phase 147E.2: Authority
Evaluation Model Implementation Contract Second Repair
(20260730-1947-phase-147e-2-...)`), PROJECT_STATUS.md was updated, the
canonical report was written, and the repository is clean and fully
synchronized with origin. Per this phase's own governing instruction,
this is recorded as a **lifecycle/documentation Non-Blocking finding**
(§26, "Lifecycle-2") — the `pushed_status`/`origin_main_head*` fields in
`.pcae/phase-completion-metadata.json` were not re-synced after the
actual push, unlike the commit-hash field, which was. This does **not**
alter Phase 147E.2's own substantive contract verdict (the repair itself
is unaffected by a stale bookkeeping field), and this phase does **not**
edit the canonical report or metadata to correct it, since no separate
lifecycle-repair authorization exists for this phase. Finalization is
**not incomplete** in the sense that would require stopping before
substantive work: the repository is demonstrably pushed, healthy, and
task-closed; only a subset of metadata's own descriptive fields lag the
final push step.

---

## 4. Independence Method

This phase reconstructed the following directly from primary sources
(AEM-001's frozen text, AEMIC-001 v1.1's frozen text as it stood before
Phase 147E.2's repair — reconstructed from AEMIC-001 v1.2's own §26
account of what v1.1 said, cross-checked against v1.2's still-present
unchanged sections, and direct source re-inspection) **before**
re-reading Phase 147E.2's own conclusions a second time for comparison:

1. BF-147F.1-1 itself (§5) — re-derived from AEMIC-REQ-021's field
   table's own mandatory/conditional asymmetry, independent of Phase
   147E.2's narrative account of the same asymmetry.
2. Every mandatory `AuthorityEvaluationOutcome` field's lawful source for
   all three `EvaluationResult` branches (§5, §14, §25) — enumerated
   against §5's seven-parameter list directly, not copied from §26's own
   field-source claims.
3. Declaration/request identity agreement semantics and the required
   failure mode (§11) — a truth table independently constructed from
   AEMIC-REQ-103/104's own normative text, then compared against
   AEMIC-001's own truth table framing.
4. The security consequences of caller-supplied template identity (§19)
   — independently attacked against the candidate list at §20 (Security
   Review) before reading AEMIC-REQ-107's own disposition a second time.

Where this phase's own independent conclusion agrees with Phase 147E.2's
account, that agreement is stated as independently confirmed, not
assumed. No section below treats the repaired interface's two new
parameters as correct merely because Phase 147E.2 selected them;
§6 (Candidate Repair Reassessment) re-derives the selection from the
governing criteria rather than citing Phase 147E.2's own conclusion.

---

## 5. BF-147F.1-1 Reproduction

**Independent reconstruction of AEMIC-001 v1.1's evaluator input set**
(reconstructed from AEMIC-001 v1.2 §26's own verbatim quotation of the
v1.1 signature, cross-checked against the unchanged portions of the
current contract text that still describe pre-repair architecture,
e.g. §1.1's classification table): `evaluate(claimed_identity,
declaration, evaluated_at, evaluator_version, citation_text=None)` —
five parameters, none named `template_ref` or `template_version`.

**Reachable sources for `template_ref`/`template_version` under v1.1, by
`EvaluationResult` branch:**

| Branch | Declaration present? | Reachable source for `template_ref`/`template_version` |
|---|---|---|
| `ELIGIBLE` | Yes (by definition, AEM-REQ-020) | `declaration.template_ref`/`.template_version` — present because `EligibleAuthorityDeclaration` (AEMIC-REQ-015) itself carries both, but **never named as the outcome's own source anywhere in v1.1's own §5/§14 text** — an undocumented, coincidental derivation only. |
| `INELIGIBLE` | Yes (by definition, AEM-REQ-020) | Same as above: coincidentally available via `declaration`, never contractually sourced. |
| `INDETERMINATE` | No (`declaration is None`, by definition, AEM-REQ-020/AEMIC-REQ-024) | **None.** No other v1.1 parameter (`claimed_identity`, `evaluated_at`, `evaluator_version`, `citation_text`) carries either value. There is no lawful construction path for a mandatory, unconditional field. |

This independently reproduces the exact asymmetry Phase 147F.1
identified: `AuthorityEvaluationOutcome`'s own field table (AEMIC-REQ-021
in the current, v1.2 text; the equivalent table in v1.1 carried the
identical entries for these two fields) marks `declaration_ref` and
`citation_text` each with an explicit conditional ("Non-`None` iff...",
"iff `evaluation_result == eligible`"), but marks `template_ref`/
`template_version` "Yes" (mandatory) with **no branch exception** —
internally inconsistent with a construction path that can only produce
a value for two of the three branches its own enum (AEM-REQ-020) closes.

**Determination:**

- **Genuine.** The gap is real, not a misreading: no v1.1 parameter,
  declaration field, or derivation rule supplies `template_ref`/
  `template_version` for `INDETERMINATE`.
- **Blocking.** `INDETERMINATE` is one of exactly three closed branches
  `evaluate()` is required to support (AEM-REQ-020, AEMIC-REQ-024); a
  branch with no lawful construction path for a mandatory field makes
  that branch implementation-impossible as specified — the same
  severity class as BF-147F-1.
- **Implementation-impossible**, not merely inconvenient: no code
  written strictly to v1.1's own text could produce a well-formed
  `evaluate()`-constructed `INDETERMINATE` outcome without either
  fabricating a value from nothing or bypassing `evaluate()` entirely
  (the latter already a disclosed, unrelated Informational finding,
  §24).
- **Distinct from BF-147F-1.** BF-147F-1 was a missing channel for
  `citation_text`, affecting only the `ELIGIBLE` branch's
  citation-population invariant; BF-147F.1-1 is a missing channel for
  `template_ref`/`template_version`, affecting the `INDETERMINATE`
  branch's own core construction. The two share only their general
  shape (a mandatory output field with no reachable construction-time
  source), not their specific field, branch, or fix.
- **Pre-existing, not introduced by the v1.1 repair.** `citation_text`'s
  repair (147E.1) touched §5, §9, §13.1, §14, §15, §20, §22, §23 only;
  none of those edits added, removed, or altered `template_ref`/
  `template_version`'s own field table entry, which is unchanged text
  traceable to AEMIC-001 v1.0 (Phase 147E) itself. This defect predates
  both the v1.0 freeze and the v1.1 repair.

This independently confirms Phase 147F.1's own finding and Phase
147E.2's own restatement of it, reached by direct reconstruction from
the frozen contract text rather than by deference to either phase's
prose.

---

## 6. Candidate Repair Reassessment

Each candidate is independently reassessed against ten criteria this
phase derives from AEM-001/AEMIC-001's own governing constraints: (1)
lawful source for every branch including `INDETERMINATE`; (2) source
exists before outcome construction; (3) caller-explicit and testable
(4) declaration identity cannot silently override caller-supplied
identity; (5) deterministic mismatch handling; (6) no global/ambient
lookup; (7) evaluator purity preserved (AEM-REQ-016, AEMIC-REQ-074/075);
(8) disclosure-only semantics preserved (§8); (9) unchanged Registry
responsibility (§11); (10) minimal change relative to the defect's own
size.

1. **Direct `evaluate()` identity parameters (two new positional
   parameters).** Satisfies all ten criteria: a value is reachable on
   every branch because the parameters are mandatory and
   caller-supplied regardless of `declaration`'s own presence;
   comparison against a present `declaration`'s own identity is a
   straightforward equality check with an obvious fail-closed failure
   mode; no new public type; two-field growth proportional to a
   two-field gap. **Independently assessed as satisfying every
   criterion with no residual defect.**
2. **Widening `AuthorityEvaluationRequest`.** No such type exists in
   v1.1/v1.2 (AEMIC-REQ-019 already declined to introduce one); creating
   one now to carry two fields adds a sixth public type for no benefit
   over (1) — it does not make the source "more canonical," only more
   indirect, and every caller must still separately construct it before
   calling `evaluate`. Independently assessed as strictly dominated by
   (1): equal correctness, worse API cohesion, worse minimality (a new
   type where none is needed).
3. **A dedicated immutable template-identity object
   (`DecisionTemplateIdentity`-shaped).** Bundles exactly two `str`
   fields with no validation or behavior beyond non-emptiness
   (AEMIC-REQ-036) that two plain parameters do not already provide
   identically; requires its own equality/hashing/serialization
   contract for no cohesion gain. Independently assessed as
   over-engineered relative to (1) for equal benefit — same objection
   as (2), narrower in scope.
4. **Conditional outcome identity** (absent for `INDETERMINATE`).
   Independently re-derived as invalid, not merely inferior: this would
   narrow AEMIC-REQ-081's existing "minimum auditable evidence...MUST
   expose" guarantee, removing the one piece of evidence identifying
   *which* Decision Template a disclosed `indeterminate` result concerns
   — a genuine auditability regression, and incompatible with
   AEM-REQ-017/AEM-REQ-020's own framing of `indeterminate` as a
   substantive, auditable result rather than a degraded one. **Rejected
   independently on auditability grounds**, matching Phase 147E.2's own
   conclusion but derived here from AEMIC-REQ-081's own text directly.
5. **Declaration-only derivation.** Independently re-derived as
   categorically invalid for `INDETERMINATE`: `declaration is None` for
   that branch by the enum's own definition (AEM-REQ-020); there is
   nothing to derive from. This is exactly the "undocumented derivation"
   that already coincidentally exists for `ELIGIBLE`/`INELIGIBLE` under
   v1.1 and demonstrably fails the third branch — the same failure mode
   BF-147F.1-1 itself identifies.
6. **Registry-derived identity** (Registry answers identity for
   declaration-absent cases). Independently re-derived as invalid on
   causality grounds alone, without needing to invoke API-surface
   objections: `resolve(template_ref, template_version)`'s own signature
   (AEMIC-REQ-042) requires both values as *input*; the Registry cannot
   simultaneously be the *source* of a value it requires to be called at
   all. This is a logical impossibility, not merely an undesirable
   design, independent of any stylistic preference.
7. **Hidden or ambient lookup** (global/Session/runtime state). Directly
   forecloses on two independently-checkable, mechanical grounds: it
   would require an import from `pcae.interactive_workflow`,
   `pcae.core`, or similar — forbidden outright by AEMIC-REQ-010's
   closed import list (§3.4, independently re-confirmed unchanged at
   §21 below) — and it would make `evaluate` no longer a pure function
   of its own explicit arguments, contradicting AEMIC-REQ-075's
   determinism requirement and AEM-REQ-016's totality/purity guarantee
   directly. No further comparison against the other six candidates is
   needed; this candidate is disqualified by two independent, frozen
   constraints regardless of any comparative merit.

**Determination:** the two direct parameters (candidate 1 above,
AEMIC-001's own "Candidate B") were **uniquely required** among the
seven, not merely acceptable or preferable — every alternative either
fails `INDETERMINATE` outright (candidates 4, 5), is logically
impossible (candidate 6), is forbidden by an already-frozen constraint
(candidate 7), or is strictly dominated on every axis with no
compensating benefit (candidates 2, 3). This phase's own independent
re-derivation reaches the identical selection Phase 147E.2 reports, but
by direct application of AEM-001/AEMIC-001's own frozen constraints, not
by re-reading Phase 147E.2's own comparison table first.

---

## 7. Exact Contract Diff Verification

Direct inspection of AEMIC-001 v1.2's current text confirms every
provision the governing prompt names as reportedly modified:

- **Contract version** — `1.2` (top-of-document identity block, line 6);
  `Second-repaired by: Phase 147E.2` recorded (line 12-14).
- **AEMIC-REQ-019** (§5) — now names seven parameters including
  `template_ref`/`template_version` as the first two, with an explicit
  note that §26 independently reassessed and re-confirmed the
  no-request-wrapper rejection.
- **AEMIC-REQ-020** (§5) — extended to state neither new parameter is
  evidentiary; `evaluation_result` remains a pure function of exactly
  `claimed_identity`/`declaration`.
- **AEMIC-REQ-021** (§6) — `template_ref`/`template_version` rows now
  cross-reference §14.2/AEMIC-REQ-103 explicitly ("repairs
  BF-147F.1-1").
- **AEMIC-REQ-038** (§10.2) — note-only addition observing that
  AEMIC-REQ-103's mismatch check makes `declaration_ref`'s derivation
  source and the outcome's own `template_ref`/`.template_version` fields
  structurally, not coincidentally, identical whenever `declaration_ref`
  is non-`None`.
- **AEMIC-REQ-064** (§13.1) — new row: `TemplateIdentityMismatchError`,
  with condition, retryability, and domain/infrastructure
  classification.
- **AEMIC-REQ-072** (§14) — signature widened to seven parameters,
  ordering rationale (`template_ref`/`template_version` first) stated.
- **AEMIC-REQ-074** (§14) — extended to classify a mismatched
  `declaration` as malformed input, alongside the pre-existing
  empty/non-`str` template identifiers.
- **AEMIC-REQ-075** (§14) — determinism tuple extended to include
  `template_ref`/`template_version`.
- **AEMIC-REQ-077** (§14) — exception boundary restated as "§13.1's six
  named exceptions" (was five under v1.1).
- **AEMIC-REQ-081** (§16) — note added: `indeterminate` outcomes can now
  disclose *which* Decision Template no Declaration existed for, closing
  BF-147F.1-1's own auditability consequence.
- **AEMIC-REQ-095** (§20, Contract Quality Review) — "Complete enough to
  implement" and "Testable" bullets both explicitly record their own
  prior (v1.1) text as falsified by Phase 147F.1, then repaired at §14.2
  and §22 respectively.
- **New §14.2 subsection** — AEMIC-REQ-103 through AEMIC-REQ-107 (five
  new identifiers): canonical identity source, mismatch verification,
  error precedence, non-collapse rule, and the "matching identity does
  not prove authority" security clarification.
- **§15 Security Contract** — new table row: "Request/declaration
  identity mismatch," citing AEMIC-REQ-103-106 and BF-147F.1-1.
- **§22 Requirement/Test Matrix** — new row for AEMIC-REQ-019/021/103-106
  enumerating fifteen positive/negative/adversarial test cases,
  including the two precedence-adversarial cases (12, 13).
- **§23 Finding Disposition** — BF-147F.1-1 row added, marked
  **Repaired**, with F-147F.1-2/-3/-4 and the direct-construction
  Informational observation each re-affirmed unaffected and open.
- **§26 Phase 147E.2 Second Repair Confirmation** — the full
  repair-confirmation narrative (reason, independent reproduction,
  governing constraints, seven-candidate comparison), directly
  inspected in full at §5-6 above.

**Requirement identifier hygiene, independently confirmed by direct
enumeration:** AEMIC-REQ-001 through AEMIC-REQ-107 form a contiguous
sequence with no gap and no reuse (this phase independently walked the
document's own requirement identifiers section by section while reading
§1-26 above; no duplicate or skipped number was observed).
`AEMIC-REQ-096`-`102` were introduced by the 147E.1 repair (§25); the
five new 147E.2 identifiers, `AEMIC-REQ-103`-`107`, are appended after
them with no renumbering of any prior identifier.

**Unrelated-provision check:** direct comparison of every section listed
above against sections *not* listed (§4, §7, §9, §11, §12, §17, §21,
§24) confirms none of the unlisted sections contains a reference to
`template_ref`/`template_version` sourcing, `TemplateIdentityMismatchError`,
or any other artifact of this repair — consistent with Phase 147E.2's
own disclosed touched-section list. No stale five-parameter reference to
`evaluate()` remains anywhere in the current text (a direct grep-style
re-read of every `evaluate(` invocation and every table naming
`evaluate`'s parameters shows all instances consistent with the current
seven-parameter signature). No example in the document depicts the
pre-repair signature as current. Exception counts are coherent
throughout: §13.1 is described as "six" named exceptions everywhere it
is counted (was "five" pre-repair); §22's matrix and §23's disposition
table both independently corroborate this count.

---

## 8. Evaluator Signature

The frozen signature, directly quoted from AEMIC-REQ-072 (§14):

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

Per-parameter verification:

| Parameter | Type | Required | Nullable | Validation | Normalization | Semantic ownership | Affects `evaluation_result`? | Affects outcome identity? | Permitted in every branch? |
|---|---|---|---|---|---|---|---|---|---|
| `template_ref` | `str` | Yes | No | Non-empty `str` (`InvalidTemplateReferenceError` otherwise, AEMIC-REQ-064) | None — exact `str` equality, no case-folding/Unicode normalization (AEMIC-REQ-036) | Canonical identity source for the outcome (AEMIC-REQ-103) | No (AEMIC-REQ-020/104 step 4) | Yes — copied verbatim | Yes, all three |
| `template_version` | `str` | Yes | No | Same as above | Same as above | Same as above | No | Yes — copied verbatim | Yes, all three |
| `claimed_identity` | `str` | Yes | No | Non-empty `str` (`InvalidClaimedIdentityError`) | None (AEMIC-REQ-036) | Evidentiary input to `evaluation_result` | Yes | Yes — copied verbatim | Yes, all three |
| `declaration` | `EligibleAuthorityDeclaration \| None` | Yes (may be `None`) | Yes | Structural validity enforced at `EligibleAuthorityDeclaration`'s own construction (AEMIC-REQ-017), not re-validated by `evaluate` beyond the identity-agreement check | N/A | Evidentiary input to `evaluation_result`; identity-agreement check subject (AEMIC-REQ-103) | Yes | Indirectly — `declaration_ref` derives from it when non-`None` | Yes, all three (`None` for `INDETERMINATE` by definition) |
| `evaluated_at` | `str` (ISO-8601 UTC) | Yes | No | Structural only, caller-supplied clock value (§14, AEMIC-REQ-076 — no internal clock dependency) | None | Observational, not part of determinism tuple (AEMIC-REQ-080) | No | Yes — copied verbatim | Yes, all three |
| `evaluator_version` | `str` | Yes | No | None beyond being a `str`; not verified against a "correct" value (AEMIC-REQ-040) | None | Descriptive metadata only | No | Yes — copied verbatim | Yes, all three |
| `citation_text` | `str \| None` | No (defaults `None`) | Yes | Enforced conditionally: non-`None` required iff `evaluation_result == ELIGIBLE` (`MissingCitationTextError` otherwise, AEMIC-REQ-101) | None — byte-for-byte verbatim copy (AEMIC-REQ-033) | Disclosure content only, never evidentiary (AEMIC-REQ-020) | No | Yes, conditionally (`None` unless `ELIGIBLE`) | Yes, all three (disregarded, not raised, when non-`None` on a non-`ELIGIBLE` branch, AEMIC-REQ-065/101.4) |

**Interface closure and completeness, independently confirmed:** all
seven parameters are consumed by at least one construction path or
validation rule; none is redundant (each has a distinct semantic role —
two identity components, one evidentiary identity claim, one evidentiary
declaration, two audit/provenance markers, one conditional disclosure
payload); no eighth parameter is implied as missing by any requirement
this phase could locate in AEM-001 or AEMIC-001 (confirmed independently
at §25's fresh sweep, not merely asserted here).

---

## 9. Canonical Identity Ownership

**AEMIC-REQ-103 independently verified.** `evaluate()`'s own
`template_ref`/`template_version` parameters are unambiguously the
**sole** canonical source of the outcome's identically-named fields, for
all three branches — confirmed by direct textual attack against each
alternative interpretation the governing prompt names:

- *"Declaration identity is canonical when present."* **Refuted by
  text.** AEMIC-REQ-103's own words state Declaration identity is "used
  **only for this validation**; it never overrides, supplements, or is
  preferred over `evaluate`'s own `template_ref`/`template_version`
  parameters as the outcome's own identity source." AEMIC-REQ-104 step 6
  independently confirms this at the construction step: "template_ref/
  template_version copied verbatim from `evaluate`'s own parameters
  (never from `declaration`...)".
- *"Caller identity is only a fallback."* **Refuted.** There is no
  fallback relationship at all — the caller-supplied parameters are the
  *only* source in every branch, including the two branches where a
  Declaration happens to exist; there is nothing to "fall back" from.
- *"Registry result identity overrides caller identity."* **Refuted and
  structurally impossible.** `evaluate` never calls the Registry
  (AEMIC-REQ-073, unchanged) and receives only the already-resolved
  `declaration` object, not a live Registry result to compare against
  independently of the equality check already specified.
- *"Evaluator may choose either source."* **Refuted.** AEMIC-REQ-104's
  ordering is stated as a deterministic, mandatory sequence
  ("SHALL be exactly"), not a discretionary choice; AEMIC-REQ-105
  explicitly forbids implementation-level variance in this ordering.
- *"Normalized values differ from copied values."* **Refuted.**
  AEMIC-REQ-036 requires exact `str` equality with no normalization
  anywhere in this package; AEMIC-REQ-103's own comparison
  (`declaration.template_ref == template_ref`) and AEMIC-REQ-104 step 6's
  copy operation are both unnormalized, so there is no divergence
  possible between "the value compared" and "the value copied" — they
  are the identical `str` object/value in both operations.

**Determination:** the contract defines exactly **one** canonical
source, not a preference hierarchy — independently confirmed, not
merely restated from AEMIC-REQ-103's own self-description.

---

## 10. Identity Validation

**`template_ref`/`template_version`, independently assessed against each
listed condition:**

| Condition | Behavior | Classification |
|---|---|---|
| Missing (absent argument) | Not applicable in Python (both are non-default positional parameters); a caller omitting them produces a `TypeError` at the language level, outside this contract's own exception taxonomy — consistent with every other non-optional parameter (`claimed_identity`, `evaluated_at`, `evaluator_version`) receiving identical treatment. | Language-level, not a contract-defined condition |
| Empty string | Raises `InvalidTemplateReferenceError` (AEMIC-REQ-064, AEMIC-REQ-104 step 1) | Explicitly classified — Domain/caller error |
| Whitespace-only | **Not distinctly classified.** AEMIC-REQ-036 requires only non-emptiness; a whitespace-only string is non-empty by Python's own `len()` semantics and therefore passes structural validation, is compared byte-for-byte against `declaration.template_ref` (case/whitespace-sensitive, AEMIC-REQ-036), and is copied verbatim into the outcome. This is a **disclosed non-restriction**, not an oversight: AEMIC-REQ-036 explicitly states "No further syntax restriction... beyond non-emptiness." | Explicitly disclosed as out of scope — not a gap this contract leaves ambiguous by omission |
| Non-`str` | Raises `InvalidTemplateReferenceError` (AEMIC-REQ-064's own condition text: "empty or not a `str`") | Explicitly classified |
| Unicode normalization | Not performed (AEMIC-REQ-036: "No canonical-form transformation... is performed"); two Unicode-equivalent-but-not-identical strings are treated as unequal | Explicitly disclosed non-behavior |
| Case sensitivity | Case-sensitive exact match (AEMIC-REQ-036) | Explicitly specified |
| Path-like strings (e.g. containing `/`) | No restriction imposed at this layer; path-safety rejection is a §12 filesystem-persistence-layer concern for a future concrete Registry's own storage keys, not an `evaluate()`-level validation | Explicitly scoped elsewhere (§12), not silently absent |
| Reserved separators | Same disposition as path-like strings — a storage-layer concern (§12, AEMIC-REQ-053), not this parameter's own validation | Explicitly scoped elsewhere |
| Excessive length | No length ceiling imposed anywhere in AEMIC-001 for this field | Explicitly unbounded, disclosed by omission-with-reasoning (mirrors `claimed_identity`'s own AEM-REQ-023 precedent) |

**`template_version`, independently assessed:**

| Condition | Behavior | Classification |
|---|---|---|
| Missing/empty/whitespace-only/non-`str` | Identical disposition to `template_ref` above (both governed by the same `InvalidTemplateReferenceError` condition and the same AEMIC-REQ-036 rule) | Explicitly classified/disclosed, mirroring `template_ref` |
| Unsupported syntax (e.g. not semver-shaped) | No syntax restriction beyond non-emptiness (AEMIC-REQ-036) — this contract does not define a version-string grammar at all | Explicitly unconstrained |
| Leading zeros, case variants, semver aliases, Unicode digits | All treated identically: two distinct `str` values compare unequal under exact-`str`-equality (AEMIC-REQ-036); there is no numeric or semver-aware comparison anywhere in this contract | Explicitly disclosed — exact-string semantics apply uniformly |
| Unsupported *version* in the sense of `schema_version` mismatch | This is a **distinct** concept from `template_version` (a Decision Template's own version component) and is governed separately by AEMIC-REQ-039/041/093 (`EligibleAuthorityDeclaration.schema_version`/`AuthorityEvaluationOutcome.schema_version` fixed literals, `UnsupportedSchemaVersionError` at deserialization) | Explicitly distinguished by this contract; not conflated |

**Malformed identity vs. unsupported version — independently confirmed
distinct:** "malformed" `template_ref`/`template_version` (empty or
non-`str`) raises `InvalidTemplateReferenceError`, a §13.1 domain
failure at `evaluate()` call time; "unsupported version" in this
contract's own vocabulary refers exclusively to `schema_version`, a
different field on a different object, raising a different exception
(`UnsupportedSchemaVersionError`) at a different layer (deserialization,
§18). No behavior classified here is left to undocumented implementation
discretion: every condition above is either an explicit requirement, an
explicit "no restriction beyond X" disclosure, or an explicit
"governed elsewhere" scoping statement — none is a silent gap.

---

## 11. Declaration Identity Agreement

**AEMIC-REQ-104 independently verified.** When `declaration` is
non-`None`, `evaluate` performs, per AEMIC-REQ-103's own quoted text:

```
declaration.template_ref == template_ref
and declaration.template_version == template_version
```

**Truth table, independently constructed:**

| Ref match | Version match | Required result |
|---|---|---|
| Yes | Yes | Continue (proceed to `evaluation_result` determination, AEMIC-REQ-104 step 4) |
| No | Yes | `TemplateIdentityMismatchError` |
| Yes | No | `TemplateIdentityMismatchError` |
| No | No | `TemplateIdentityMismatchError` |

This matches the table the governing prompt supplies exactly. Verified
against AEMIC-REQ-103's own text ("If **either** comparison is false,
`evaluate` SHALL raise `TemplateIdentityMismatchError`") — a single
combined AND condition on the "continue" path, with any single
falsification of either sub-condition sufficient to trigger the
exception; there is no partial-match, majority-match, or ref-only/
version-only override path.

**Further verification, per the governing prompt's own checklist:**

- **Comparison happens before outcome construction.** Confirmed:
  AEMIC-REQ-104 step 3 (identity check) precedes step 4
  (`evaluation_result` determination) and step 6 (construction).
- **Normalization occurs before or after comparison according to one
  frozen rule.** Confirmed, trivially: no normalization occurs at any
  point (AEMIC-REQ-036), so there is no "before vs. after" ambiguity to
  resolve — the comparison is exact-`str`-equality on the raw,
  unmodified values throughout.
- **Both fields are compared.** Confirmed: the `and` conjunction
  requires both `template_ref` and `template_version` agreement.
- **Partial mismatch fails.** Confirmed by the truth table (rows 2, 3).
- **Mismatch cannot produce `INDETERMINATE`.** Confirmed: the mismatch
  check (step 3) is ordered strictly before `evaluation_result`
  determination (step 4); a raised exception at step 3 never reaches
  step 4 at all, so no `EvaluationResult` value — including
  `INDETERMINATE` — is ever produced on the mismatch path.
- **Mismatch cannot be treated as declaration absence.** Confirmed:
  AEMIC-REQ-106 explicitly enumerates this exact non-collapse rule
  ("distinct from... `INDETERMINATE` (a mismatch means a Declaration
  *did* resolve... the opposite situation from no Declaration existing
  at all)").
- **Mismatch cannot be silently resolved by preferring one identity.**
  Confirmed at §9 above — there is no preference rule of any kind.
- **Mismatch cannot be masked by citation handling.** Confirmed:
  AEMIC-REQ-104's ordering places the identity check (step 3) strictly
  before the `MissingCitationTextError` check (step 5); a mismatch
  always raises before citation-related logic is ever reached (also
  independently verified via the adversarial case at §16, item 12
  below).

No defect found in this section.

---

## 12. TemplateIdentityMismatchError

| Property | Verified value |
|---|---|
| Exact class name | `TemplateIdentityMismatchError` (AEMIC-REQ-064, AEMIC-REQ-103-106) |
| Stable code | This contract does not itself define a wire-level error-code string beyond the class name; AEMIC-REQ-071 (unchanged by this repair) restates that error-code mapping is a future CLI/transport surface's own concern (IWPC-001 §19), not this package's |
| Inheritance | Direct subclass of `AuthorityEvaluationError` (AEMIC-REQ-064's own table structure, §13.1) |
| Trigger | `evaluate()`'s own `declaration` parameter is non-`None` and `(declaration.template_ref, declaration.template_version) != (template_ref, template_version)` (AEMIC-REQ-064's own condition column, verified verbatim) |
| Domain vs. infrastructure | Domain (caller/workflow error) — explicitly classified in AEMIC-REQ-064's own table, not infrastructure |
| Retryable | No (AEMIC-REQ-064's own table) — correct, since the condition is deterministic given the same inputs (AEMIC-REQ-105); retrying with identical inputs reproduces the identical exception |
| Public fields | Not explicitly enumerated by this contract (no field list given for any §13.1 exception beyond the base `AuthorityEvaluationError`'s implied message-carrying capability); this is consistent treatment with the other five §13.1 exceptions, none of which has an enumerated field list either — not a gap unique to this exception |
| Message requirements | Not explicitly specified beyond the general "raise a typed error" discipline common to all §13.1 exceptions |
| Serialization/reporting | Not this package's own concern (§18's serialization contract governs `EligibleAuthorityDeclaration`/`AuthorityEvaluationOutcome` payloads, not exception payloads) |
| Safe disclosure of both conflicting identities | Not explicitly mandated by a requirement text, but nothing in the security contract (§15) restricts an implementation from including both identities in the exception's own message/attributes — no security property (§19, §20 below) treats template identity as sensitive |
| Raised when declaration absent | **No** — the trigger condition explicitly requires `declaration` to be non-`None` (AEMIC-REQ-064's condition text: "`evaluate`'s own `declaration` parameter is non-`None` and..."); when `declaration is None` (`INDETERMINATE`), this exception cannot be raised by definition |
| Confusable with unsupported version | Independently verified not confusable: `UnsupportedSchemaVersionError` governs `schema_version` mismatches at deserialization (§18); `TemplateIdentityMismatchError` governs a `template_ref`/`template_version` disagreement between two evaluation-time inputs — distinct fields, distinct layers, distinct triggering objects |
| Confusable with Registry corruption | Independently verified not confusable: `AuthorityRegistryCorruptError` is raised exclusively by a concrete Registry's own `resolve()` method (§13.2, AEMIC-REQ-067), never by `evaluate()` (AEMIC-REQ-073/077, `evaluate` never touches the Registry); `TemplateIdentityMismatchError` is raised exclusively by `evaluate()`. AEMIC-REQ-106 states this non-collapse rule explicitly. |

**Updated exception taxonomy count, independently verified:** six §13.1
exceptions (`InvalidClaimedIdentityError`, `InvalidTemplateReferenceError`,
`MalformedDeclarationError`, `UnsupportedSchemaVersionError`,
`MissingCitationTextError`, `TemplateIdentityMismatchError`) plus two
§13.2 Registry exceptions
(`AuthorityRegistryUnavailableError`, `AuthorityRegistryCorruptError`) —
eight named exceptions total, plus the base-class direct-use fallback
(AEMIC-REQ-069). This count is stated consistently at AEMIC-REQ-067
("§13.1's four exceptions" — corrected to "six" is the current text at
line 945 confirmed directly), AEMIC-REQ-077 ("§13.1's six named
exceptions"), and §22's matrix row ("Each of the eight named
exceptions... independently triggerable"). No inconsistency found.

---

## 13. INDETERMINATE Construction

**Full branch reconstruction, given the exact inputs the governing
prompt specifies:**

```
template_ref = valid (non-empty str)
template_version = valid (non-empty str)
claimed_identity = valid (non-empty str)
declaration = None
evaluated_at = valid ISO-8601 str
evaluator_version = valid str
citation_text = absent (None, default)
```

**Field-by-field lawful source, independently verified:**

| Field | Source | Reachable? |
|---|---|---|
| `template_ref` | `evaluate`'s own `template_ref` parameter, copied verbatim (AEMIC-REQ-103, AEMIC-REQ-104 step 6) | **Yes** — the exact repair |
| `template_version` | `evaluate`'s own `template_version` parameter, copied verbatim | **Yes** — the exact repair |
| `evaluation_result` | Computed: `declaration is None` → `INDETERMINATE` (AEM-REQ-020/AEMIC-REQ-024) | Yes (unaffected by this repair) |
| `declaration_ref` | `None` when `declaration is None` (AEMIC-REQ-021's own conditional: "`None` iff `indeterminate`") | Yes — correctly `None`, not a missing value |
| `citation_text` | `None`, per AEMIC-REQ-101 step 4 (non-`ELIGIBLE` branches always construct with `citation_text=None` regardless of caller input) | Yes |
| `claimed_identity` | Copied verbatim from `evaluate`'s own parameter (AEMIC-REQ-021) | Yes (unaffected) |
| `evaluated_at` | Copied verbatim | Yes (unaffected) |
| `evaluator_version` | Copied verbatim | Yes (unaffected) |
| `schema_version` | Fixed literal `"aem-outcome/1.0"` (AEMIC-REQ-039) | Yes (constant, not caller-sourced) |

**Confirmed:**

- No declaration-derived field remains mandatory without a source: the
  only declaration-derived field, `declaration_ref`, is correctly
  conditional (`None` here), not mandatory-and-unreachable.
- No fabricated declaration identity is required: `template_ref`/
  `template_version` come from `evaluate`'s own parameters, never from a
  nonexistent `declaration`.
- No Registry identity oracle is required: `evaluate` never calls the
  Registry (AEMIC-REQ-073); the two identity parameters are supplied
  directly by the caller who already possessed them (e.g. to have
  called `resolve(template_ref, template_version)` in the first place,
  per §9's own reasoning restated at AEMIC-REQ-084's integration
  sequence — outside this contract's own scope, but consistent with it).
- No hidden lookup is required: both identity parameters are explicit,
  caller-supplied arguments.
- Serialization is valid: `to_payload`/`from_payload` (§18) treat every
  field, including `template_ref`/`template_version`, as mandatory and
  always-emitted (AEMIC-REQ-091) — a fully-populated `INDETERMINATE`
  instance serializes with no `null`/omitted mandatory field.
- Equality/determinism is deterministic: identical inputs (including
  identical `template_ref`/`template_version`) yield a field-identical
  outcome (AEMIC-REQ-075, extended to the two new parameters).

No defect found; BF-147F.1-1's own target branch is fully constructible
under v1.2.

---

## 14. ELIGIBLE and INELIGIBLE Construction

Independently verified for both branches (declaration present): (1)
`evaluate`'s own direct identity parameters are validated first
(AEMIC-REQ-104 step 1); (2) the declaration's own identity is checked
for agreement against those already-validated parameters
(AEMIC-REQ-104 step 3) — this is validation only, not a value source;
(3) the outcome's own `template_ref`/`template_version` fields are
copied from the **direct evaluator parameters**, never from
`declaration` (AEMIC-REQ-104 step 6's explicit parenthetical: "never
from `declaration`"); (4) `declaration`'s own identity fields are used
exclusively for the step-3 comparison and never read again during
construction.

This is exactly what the contract states, confirmed by direct
quotation of AEMIC-REQ-104 step 6 above, not inferred.

**Attack: could an implementation instead copy `declaration`'s own
identity values after the equality check passes, and still claim
compliance?** Independently assessed: **functionally indistinguishable
in observable behavior, but not textually compliant.** Because
AEMIC-REQ-103 requires the equality check to hold as a precondition for
reaching construction at all, `declaration.template_ref == template_ref`
and `declaration.template_version == template_version` are guaranteed
true by the time construction occurs (for `ELIGIBLE`/`INELIGIBLE`
specifically) — so copying from either source produces an identical
resulting value. However, this distinction **is** materially relevant
for two independent reasons this phase identifies:

1. **Textual conformance.** AEMIC-REQ-104 step 6 states "never from
   `declaration`" as a normative SHALL-equivalent instruction, not a
   stylistic preference; an implementation that copies from
   `declaration` instead would fail a hypothetical white-box code-review
   conformance check even though its black-box behavior is
   indistinguishable, for identical reasons that would apply to a future
   revision widening the equality check's own tolerance (e.g. a
   normalization exception) — under a "copy from declaration" design,
   such a future revision would silently change the outcome's own
   identity source; under the frozen "always from the direct
   parameters" design, it cannot.
2. **Robustness under a defective implementation.** If a conforming
   implementation's own equality check (AEMIC-REQ-103) were itself
   buggy — e.g. comparing only `template_ref` and forgetting
   `template_version` — a "copy from evaluate's own parameters" design
   still produces an outcome whose own identity fields exactly match
   what the *caller* asked to evaluate against, whereas a "copy from
   declaration" design under the identical bug could silently substitute
   the Declaration's own (possibly-mismatched-on-the-forgotten-field)
   identity into the outcome without the caller's awareness. The frozen
   design is therefore more defense-in-depth than the two are made to
   appear by their converging happy-path behavior alone.

**Determination:** the "never from `declaration`" rule is real, textual,
material, and correctly the more robust of the two equivalent-looking
designs — independently confirmed, not merely accepted as stated.

---

## 15. Field-Source Matrix Verification

Independently reconstructed, complete field set (nine fields — the
eight AEMIC-REQ-021 enumerates, `schema_version` included as the ninth
fixed-literal field):

| Outcome field | `ELIGIBLE` source | `INELIGIBLE` source | `INDETERMINATE` source |
|---|---|---|---|
| `template_ref` | `evaluate`'s own parameter (verified equal to `declaration`'s own field, never copied from it) | Same as `ELIGIBLE` | `evaluate`'s own parameter (sole source; no `declaration` exists) |
| `template_version` | Same pattern | Same pattern | Same pattern |
| `claimed_identity` | `evaluate`'s own parameter, verbatim | Same | Same |
| `evaluation_result` | Evaluation logic: `declaration` non-`None` and `claimed_identity` in `declaration.eligible_identities` | Evaluation logic: `declaration` non-`None` and `claimed_identity` **not** in the set | Evaluation logic: `declaration is None` |
| `declaration_ref` | Deterministically derived from `declaration`'s own `(template_ref, template_version)` (AEMIC-REQ-038) | Same derivation | `None` (no declaration to derive from) |
| `citation_text` | `evaluate`'s own `citation_text` parameter, verbatim, mandatory (raises `MissingCitationTextError` if `None`) | `None`, forced (caller-supplied value, if any, disregarded — AEMIC-REQ-101 step 4) | `None`, forced (same rule) |
| `evaluated_at` | `evaluate`'s own parameter, verbatim | Same | Same |
| `evaluator_version` | `evaluate`'s own parameter, verbatim | Same | Same |
| `schema_version` | Fixed literal `"aem-outcome/1.0"` | Same | Same |

No field relies on undocumented inference, global state, future
lifecycle integration, or nonexistent declaration data — independently
confirmed field-by-field above, not merely asserted. This matrix is
identical in substance to AEMIC-001's own §22 matrix row for
AEMIC-REQ-019/021/103-106, cross-checked and found consistent.

---

## 16. Error Precedence

**AEMIC-REQ-104/105 jointly verified to freeze a deterministic total
order:**

1. `template_ref`/`template_version` well-formedness
   (`InvalidTemplateReferenceError`)
2. `claimed_identity` well-formedness (`InvalidClaimedIdentityError`)
3. Declaration identity agreement, if `declaration` non-`None`
   (`TemplateIdentityMismatchError`)
4. `evaluation_result` determination (no exception; pure computation)
5. `citation_text` presence, if `ELIGIBLE` (`MissingCitationTextError`)
6. Construction

**Adversarial combinations, independently attacked:**

1. **Malformed `template_ref` + Registry unavailable.** Not reachable as
   a joint condition through `evaluate` itself: Registry-unavailability
   is raised by a concrete Registry's own `resolve()`, upstream of
   `evaluate` (AEMIC-REQ-073/077); by the time `evaluate` is called,
   `declaration` is already resolved (or the caller never reached
   `evaluate` at all because `resolve` itself raised). Within
   `evaluate`'s own boundary, a malformed `template_ref` alone raises
   `InvalidTemplateReferenceError` at step 1, before any other check.
2. **Unsupported `template_version` + duplicate declarations.** Same
   architectural separation: duplicate-declaration detection
   (`AuthorityRegistryCorruptError`) is a Registry-`resolve()`-time
   condition (AEMIC-REQ-045/048), never reachable inside `evaluate`
   itself; an unsupported (in the sense of malformed) `template_version`
   raises `InvalidTemplateReferenceError` at step 1 regardless.
3. **Declaration mismatch + missing citation.** Reachable and
   adversarially significant: a call with a mismatched `declaration`
   *and* an otherwise-`ELIGIBLE`-shaped, `citation_text=None` input
   raises `TemplateIdentityMismatchError` at step 3, never reaching step
   4 (`evaluation_result` determination) or step 5
   (`MissingCitationTextError`) at all — independently confirmed by
   AEMIC-REQ-105's own explicit worked example ("MUST raise
   `TemplateIdentityMismatchError`... never `MissingCitationTextError`").
4. **Declaration mismatch + Registry corruption.** Not jointly reachable
   inside `evaluate` for the identical architectural-separation reason
   as (1)/(2): Registry corruption is a `resolve()`-time condition,
   external to and prior to any call to `evaluate`.
5. **Missing citation + eligible result.** Reachable, ordinary case:
   raises `MissingCitationTextError` at step 5, after `evaluation_result`
   is determined `ELIGIBLE` at step 4 — the originally-repaired
   BF-147F-1 path, unaffected by this repair.
6. **Supplied citation + indeterminate result.** Reachable, ordinary
   case: `evaluation_result` is `INDETERMINATE` at step 4; step 5 is
   skipped (only applies when `ELIGIBLE`); construction proceeds with
   `citation_text=None` regardless of the caller-supplied value
   (AEMIC-REQ-101 step 4, AEMIC-REQ-065) — no exception.
7. **Duplicate declaration + mismatch.** Not jointly reachable inside
   `evaluate`: a duplicate condition prevents `resolve()` from ever
   returning a `declaration` value to pass to `evaluate` in the first
   place (it raises `AuthorityRegistryCorruptError` instead, upstream).
8. **Invalid request + malformed declaration.** `MalformedDeclarationError`
   is raised, if at all, by `EligibleAuthorityDeclaration`'s own
   constructor (AEMIC-REQ-017), strictly before a well-formed instance
   could exist to pass to `evaluate` at all (AEMIC-REQ-104's own closing
   paragraph, directly quoted: "`MalformedDeclarationError` is not part
   of this ordering... raised... strictly before any well-formed
   `EligibleAuthorityDeclaration` instance could exist"). An "invalid
   request" (malformed `template_ref`/`template_version`/
   `claimed_identity`) is independently checked at steps 1-2 regardless
   of whether `declaration` itself is well-formed or not yet
   constructed.

**Determination:** the exact order among input validation, Registry
resolution classification, declaration validation, identity agreement,
evaluation-result determination, citation enforcement, and outcome
construction is unambiguous and independently reconstructible from
AEMIC-REQ-104's own six numbered steps, with AEMIC-REQ-105 explicitly
foreclosing implementation-level variance. Every adversarial pair listed
by the governing prompt either resolves to a single, unambiguous
required exception (cases 3, 5, 6) or is architecturally unreachable as
a joint in-`evaluate` condition because the two named failures occur at
different layers separated by `evaluate`'s own zero-Registry-dependency
boundary (cases 1, 2, 4, 7, 8) — no ambiguous pair was found.

---

## 17. Determinism

**AEMIC-REQ-075 independently verified.** The determinism tuple now
comprises: `template_ref`, `template_version`, `claimed_identity`,
`declaration`, `evaluated_at`, `evaluator_version`, `citation_text` — all
seven of `evaluate`'s own parameters, confirmed by direct reading of
AEMIC-REQ-075's own text ("identical `(template_ref, template_version,
claimed_identity, declaration, evaluated_at, evaluator_version,
citation_text)` inputs SHALL always produce a field-identical... outcome
(or... an identical raised exception type)").

- **Registry resolution** is not itself part of `evaluate`'s own
  determinism tuple (correctly so — `evaluate` receives `declaration`
  as an already-resolved value; Registry-level determinism is governed
  separately by AEMIC-REQ-043, restated unaffected by this repair).
- **All existing evaluation inputs** — confirmed present in the tuple
  above (`claimed_identity`, `declaration`).
- **`citation_text`** — confirmed present, extending the pre-147E.1
  tuple by exactly the same field that repair added.
- **Evaluation context / contract-schema versions** — `evaluator_version`
  is present in the tuple (a descriptive marker, but included in the
  determinism guarantee's own input list per AEMIC-REQ-075's literal
  text); `schema_version` is a fixed literal, not a variable input, so
  it is correctly excluded from the tuple rather than included as a
  redundant constant.

**Confirmed:**

- Identical semantic tuple yields identical outcome or exception — the
  literal text of AEMIC-REQ-075 states exactly this.
- Differing identity (`template_ref`/`template_version`) is materially
  reflected: a different `template_ref` produces a different value in
  the outcome's own `template_ref` field (direct copy), a genuine,
  material difference, not a cosmetic one.
- Mismatch error is deterministic: `TemplateIdentityMismatchError`'s own
  trigger condition (§12) is a pure equality comparison over already-
  deterministic inputs, so identical inputs always either both raise or
  both do not raise it.
- Normalization cannot produce platform-dependent results: none is
  performed (AEMIC-REQ-036), eliminating an entire class of
  platform-dependent (locale-sensitive case-folding, Unicode
  normalization form) nondeterminism risk by construction.
- Registry ordering cannot alter equivalent results: `evaluate` never
  touches the Registry at all (AEMIC-REQ-073), so no Registry-internal
  ordering concern can propagate into `evaluate`'s own determinism.
- Timestamps (`evaluated_at`) do not affect semantic identity: correctly
  excluded from the "stable" field classification at AEMIC-REQ-080,
  which explicitly marks `evaluated_at` as the sole "observational"
  field, not part of the outcome's own deterministic-identity guarantee
  — independently confirmed as the one deliberate, disclosed carve-out
  from an otherwise fully deterministic field set.

No defect found.

---

## 18. Serialization

**Independently verified: the two new parameters are represented as
outcome fields (via `AuthorityEvaluationOutcome.to_payload`/
`from_payload`), not as a separate serialized "request" type** — there
is no `AuthorityEvaluationRequest` type in v1.2 (confirmed rejected at
§6/§7 above), so `template_ref`/`template_version` have no independent
request-serialization surface; they exist in serialized form only as
two of `AuthorityEvaluationOutcome`'s own nine (eight-plus-schema_version)
fields.

- **Field names** — `template_ref`, `template_version`, matching the
  outcome's own dataclass field names exactly (no renaming at the
  serialization boundary is specified or implied).
- **Requiredness/nullability** — both mandatory, non-nullable in every
  branch, per AEMIC-REQ-021/091 — confirmed at §13 above for
  `INDETERMINATE` specifically, the branch where this was previously
  impossible.
- **Omitted vs. `null`** — AEMIC-REQ-091 requires `to_payload` to always
  emit every field and `from_payload` to raise if any required field is
  missing or `null`; `template_ref`/`template_version` are covered by
  this blanket rule identically to every other mandatory field, with no
  field-specific carve-out.
- **Canonical ordering** — `json.dumps(..., sort_keys=True)`
  (AEMIC-REQ-088), applying uniformly; no field-specific ordering
  exception for the two identity fields.
- **Unicode handling** — no ASCII-only restriction (AEMIC-REQ-090);
  `template_ref`/`template_version` are not explicitly named in
  AEMIC-REQ-090's own list (which names `eligible_identities`,
  `declared_by`, `citation_text`), but the general "no ASCII-only
  restriction is imposed" framing is stated as a package-wide rule, not
  a field-enumerated allowlist — independently read as applying to
  every `str` field this package defines, including `template_ref`/
  `template_version`, consistent with AEMIC-REQ-036's own "no format
  beyond non-emptiness" discipline for these two fields specifically.
- **Round-trip behavior** — a fully-populated `INDETERMINATE` instance
  (now constructible per §13) round-trips through `to_payload`/
  `from_payload` with `template_ref`/`template_version` preserved
  byte-for-byte, `declaration_ref`/`citation_text` both `null`/`None`.
- **Invalid identity rejection** — `from_payload` is not independently
  specified to re-validate `template_ref`/`template_version`
  non-emptiness beyond the blanket missing/`null` check
  (AEMIC-REQ-091); this mirrors the treatment of every other mandatory
  `str` field in this contract's own serialization section (no field
  receives bespoke deserialization-time content validation beyond
  presence) — not a defect unique to this repair.
- **Mismatch detection after deserialization** — **not defined**: §18
  does not require `from_payload` to re-run
  `TemplateIdentityMismatchError`-style cross-field validation, because
  `AuthorityEvaluationOutcome`'s own deserialization reconstructs an
  *already-produced* outcome (post-`evaluate`, post-mismatch-check) —
  there is no `declaration` field on `AuthorityEvaluationOutcome` itself
  to re-compare against (only `declaration_ref`, a derived `str`), so a
  mismatch-style re-check is not merely unspecified but has no data
  available to perform it against, consistent with the outcome's own
  closed field set.
- **Preservation of `INDETERMINATE` identity** — confirmed at §13's
  round-trip discussion: `template_ref`/`template_version` survive
  serialization for `INDETERMINATE` specifically, the property that did
  not previously exist to preserve (no `evaluate`-produced
  `INDETERMINATE` instance could exist under v1.1 to serialize in the
  first place — AEMIC-001's own §18 closing paragraph, directly quoted,
  independently confirmed accurate: "what this repair changes is only
  that `evaluate` (§14.2) can now actually *construct* a lawful
  `indeterminate` outcome carrying both fields").

**F-147F.1-4 reassessment (deserialization cross-field ambiguity —
whether `from_payload`'s blanket mandatory-field rule cross-validates
conditionally-mandatory fields, e.g. a hand-crafted payload asserting
`evaluation_result: "eligible"` with `citation_text: null`).**
Independently reassessed in light of v1.2: this finding concerns the
`citation_text`/`evaluation_result` cross-field relationship
exclusively; `template_ref`/`template_version` are **unconditionally**
mandatory in every branch (unlike `citation_text`/`declaration_ref`,
which are conditionally mandatory), so the identity-widening repair
introduces no new instance of this same ambiguity for the two new
fields — there is no branch in which `template_ref`/`template_version`
are permitted to be absent, so no analogous "does deserialization
cross-validate this field's own conditional requirement" question
arises for them. **Determination: the repair neither worsens nor
improves F-147F.1-4** — it is orthogonal to the two new fields' own
unconditional-mandatory status, exactly as Phase 147E.2's own account
states, independently confirmed here rather than merely restated.

---

## 19. Security Review

Each listed attack independently assessed against AEMIC-001 v1.2:

- **Caller-supplied template substitution.** Closed by
  `TemplateIdentityMismatchError`: a caller cannot silently substitute a
  different Declaration's identity for the one it also names directly
  to `evaluate` — any disagreement fails closed (§9, §11).
- **Declaration/request cross-pairing.** This is the exact condition
  `TemplateIdentityMismatchError` exists to catch — independently
  confirmed at §11's truth table (rows 2-4).
- **Version substitution.** Covered identically to ref substitution —
  the AND-conjunction in AEMIC-REQ-103's check requires *both* to agree;
  a version-only substitution (matching `template_ref`, mismatched
  `template_version`) is caught by row 2 of the truth table.
- **Stale declaration replay.** `EligibleAuthorityDeclaration`'s own
  language-level immutability (AEMIC-REQ-018) and the authoring-time
  discipline at AEM-REQ-008 are unaffected by this repair; this repair
  does not introduce a new replay vector, since `evaluate` remains pure
  and stateless (AEMIC-REQ-076).
- **Registry poisoning.** The Registry ABC still exposes no write path
  (AEMIC-REQ-042, unaffected by this repair, independently confirmed
  unchanged at §21 below).
- **Arbitrary template identity fabrication.** A caller can supply any
  `template_ref`/`template_version` string to `evaluate` directly
  (subject only to non-emptiness) — this is unavoidable given the
  repair's own design (the caller must supply these values somewhere;
  §5's own "Source" column states `template_ref` is "the same value the
  caller already used to obtain `declaration`"). This is not a new
  vulnerability the repair introduces: the caller already fully
  controlled which `(template_ref, template_version)` pair it called
  `resolve()` with, upstream, before this repair existed. The repair's
  own mismatch check (`TemplateIdentityMismatchError`) is strictly
  additive protection against a caller supplying *inconsistent* values
  between the two calls — it does not, and could not, protect against a
  caller consistently lying about both calls with the identical
  fabricated identity, a limitation independently confirmed inherent to
  any design in which the caller is the sole identity source (candidate
  6, Registry-derived identity, was independently rejected at §6
  precisely because it cannot exist as an alternative — the Registry
  cannot answer identity for a call it has not yet received).
- **Citation/identity mismatch.** Independently confirmed unrelated
  channels: `citation_text` is validated (presence only) independently
  of `template_ref`/`template_version` (AEMIC-REQ-104's ordering keeps
  the two checks at separate steps, 3 and 5); no cross-validation
  between the identity pair and the citation content exists or is
  claimed to exist.
- **Identity collision.** Not applicable at this package's own layer:
  `evaluate` performs no Registry lookup and has no visibility into
  whether two different Declarations might otherwise collide on a
  reused identity tuple — that is a §11.2 Registry-uniqueness concern,
  unaffected by this repair and independently confirmed unchanged.
- **Direct outcome construction (bypassing `evaluate` entirely).**
  Unaffected: `AuthorityEvaluationOutcome`'s own constructor-level
  invariant (AEMIC-REQ-022) is unchanged and remains the identical,
  sole enforcement point regardless of whether construction is reached
  through `evaluate()` or directly — a direct construction can supply
  any `template_ref`/`template_version` of its own choosing, exactly as
  before this repair for every other field (the Informational finding
  at §24, unaffected).
- **Downstream consumer treating identity match as authority.**
  Directly foreclosed by the new AEMIC-REQ-107, verified at §19 below
  (Disclosure-Only Boundary) — a matching identity proves only identity
  agreement, never authority.
- **Hidden policy escalation.** No new policy-language, role, or
  scope/time-bounding mechanism is introduced (§24, Non-Goals,
  unaffected); the two new parameters are identity strings with no
  evaluative weight on `evaluation_result` (AEMIC-REQ-020, extended and
  reconfirmed unweakened at AEMIC-REQ-104 step 4).

**AEMIC-REQ-107 independently verified correct.** Its own text states
plainly that a matching template identity "proves only that the
Declaration `evaluate`'s caller supplied is the one for the Decision
Template `evaluate`'s caller also named directly" — not authority.
Independently cross-checked against §7/§14's own set-membership
semantics: `evaluation_result` (the actual authority-adjacent
determination) is computed exclusively from `claimed_identity`/
`declaration.eligible_identities` (AEMIC-REQ-020/104 step 4), entirely
independent of whether the identity-agreement check passed — the two
new parameters have zero causal influence on `evaluation_result` itself,
confirmed structurally, not merely by the requirement's own
self-description.

**Confirmed:** the new parameters do not become authorization inputs —
independently verified by the same structural argument (they influence
only `template_ref`/`.template_version`/`declaration_ref` derivation and
the mismatch-exception path, never `evaluation_result`).

---

## 20. Disclosure-Only Boundary

Independently reconfirmed, per §8 (unchanged by this repair) and the
new AEMIC-REQ-107: evaluator identity inputs cannot authorize
publication, execution, or Confirmation (AEMIC-REQ-005/027/028,
unaffected — no requirement below §14.2 alters any disclosure-only
naming/semantics rule); cannot grant or deny human or legal authority
(AEMIC-REQ-107 explicitly forecloses reading a matching identity as
proof of authority); cannot alter runtime capability (§3.4's forbidden
imports, unaffected, independently re-confirmed at §21 below); cannot
mutate Registry state (the ABC still exposes no write method,
AEMIC-REQ-042); cannot gate CHGR construction (§17's deferred
integration boundary, unaffected, independently re-confirmed at §21
below); cannot substitute for governance approval (no requirement
anywhere in this repair references Confirmation, Readiness,
Authorization, or Publication).

**Terminology/naming/examples audit.** `TemplateIdentityMismatchError`
is named and described throughout §13.1/§14.2/§15 as a **fail-closed
structural rejection** ("a fail-closed check," "structural rejection,"
never "denied authorization" or any grant/deny/permit/authorize-shaped
verb) — independently confirmed by direct re-reading of every instance
of the term in the document; no instance describes it as an
authorization decision.

---

## 21. Registry Boundary

Independently verified unchanged: `AuthorityRegistry` still exposes
exactly one abstract method, `resolve(template_ref, template_version) ->
EligibleAuthorityDeclaration | None` (AEMIC-REQ-042 — direct textual
comparison confirms this signature is byte-for-byte identical to the
pre-147E.2 text); Registry absence (`None`) remains distinct from
unavailability (`AuthorityRegistryUnavailableError`) and corruption
(`AuthorityRegistryCorruptError`), all three §11.3/§13.2 provisions
unmodified by this repair's own disclosed touched-section list (§7
above); the Registry does not supply canonical template identity —
independently confirmed at §9 (Candidate F was rejected outright, on
causality grounds, precisely because this would expand Registry
responsibility); Registry results (`declaration`) are checked against
`evaluate`'s own caller-supplied identity parameters, never the reverse
(§9); duplicate handling remains fail-closed (AEMIC-REQ-045,
unmodified); no mutation is added (no write method exists on the ABC,
unmodified); no concrete filesystem Registry is required (§3.3's
deferral, unmodified — independently confirmed no concrete
implementation exists anywhere under `src/pcae/` by direct filesystem
search, §3/§31).

No silent expansion of Registry responsibility found.

---

## 22. Deferred Integration Boundary

Independently confirmed AEMIC-001 v1.2 remains implementable without
changes to Session, `PublicationReadinessPackage`, Interactive Workflow,
Publication Coordinator, `record.py`, CHGR schemas, IWC-001, or PEC-001
— §17's requirements (AEMIC-REQ-083-086) are unmodified by this repair's
own disclosed touched-section list, and this phase's own direct
filesystem search (§3, §31) confirms no file under
`src/pcae/interactive_workflow/**` or `src/pcae/governance/publication/**`
references `template_ref`/`template_version` in any evaluation-adjacent
context introduced by this contract.

A future caller's own mechanism for obtaining `template_ref`/
`template_version` at the moment it calls `evaluate` (e.g. from
`Session.template_ref` plus whatever supplies `--template-version`,
per §10.1's own AEMIC-REQ-037 discussion, or from the identical values
it already used to call `resolve()`) is **explicitly not defined here**
— consistent with AEMIC-REQ-032's own already-disclosed, analogous,
unclosed limitation for `citation_text`'s own sourcing. This is
independently confirmed to be the correct scope boundary: the core
contract requires explicit caller inputs (the two new parameters) but
defers the future lifecycle plumbing that would supply them in a real
Interactive Workflow call site, exactly as it already deferred the
analogous `citation_text`-sourcing question at §9. This distinction —
"the contract requires an explicit input exists" vs. "the contract
does not yet say who supplies it in production" — is stated clearly and
is not conflated anywhere in the document.

---

## 23. Compatibility with AEM-001

Independently verified by direct comparison against AEM-001's own
frozen text (`docs/contracts/AUTHORITY_EVALUATION_MODEL_CONTRACT.md`):

- **Declaration shape unchanged.** AEM-REQ-007's six-field
  `EligibleAuthorityDeclaration` shape, directly re-read, matches
  AEMIC-REQ-015/016 exactly; this repair adds no seventh field
  (independently confirmed — §6's Candidate rejection list does not
  include declaration-widening as even a considered option, correctly,
  since the defect concerns `evaluate()`'s own inputs, not the
  Declaration's own shape).
- **`evaluation_result` purity unchanged.** AEM-REQ-016's "total
  function over its two inputs (claimed identity, Declaration-or-`None`)"
  is directly re-read and independently confirmed unweakened:
  AEMIC-REQ-104 step 4 restates `evaluation_result` is determined "from
  exactly the two evidentiary inputs AEM-REQ-016 names," explicitly
  "unaffected by `template_ref`, `template_version`, or `citation_text`."
- **No new authority source.** `template_ref`/`template_version` carry
  no evaluative weight (§19 above, independently structurally
  confirmed, not merely asserted).
- **No new enforcement surface.** `TemplateIdentityMismatchError` is a
  structural-input-rejection mechanism, not a new authorization gate
  (§20).
- **No AEM-001 requirement weakened.** Direct re-read of AEM-REQ-018
  ("An `AuthorityEvaluationOutcome` SHALL carry exactly: `template_ref:
  str` / `template_version: str`...", both listed with no conditional
  annotation in AEM-001's own text) confirms AEM-001 **itself**
  already required these two fields unconditionally, for every branch
  — independently establishing that AEMIC-001 v1.1's own gap
  (BF-147F.1-1) was an implementation-layer failure to supply a
  reachable input for an obligation AEM-001 had already imposed, not a
  new obligation this repair invents. This repair therefore *restores*
  compatibility with AEM-REQ-018 rather than merely preserving it —
  under v1.1, AEMIC-001 could not have been said to fully honor
  AEM-REQ-018's own unconditional mandate for the `INDETERMINATE`
  branch; under v1.2, it now can.

No contradiction with AEM-001 found.

---

## 24. Prior Finding Reassessment

| Finding | Reassessment |
|---|---|
| **BF-147F-1** | Independently reconfirmed fully repaired: `citation_text` remains `evaluate`'s own fifth parameter (unmoved by this repair's parameter-count growth from five to seven — `citation_text` retains its default-value position last), `MissingCitationTextError` enforcement (AEMIC-REQ-101) is untouched in substance, only re-numbered in ordering terms to accommodate the new steps 1/3 ahead of it (AEMIC-REQ-104). No regression found. |
| **BF-147F.1-1** | Independently determined **fully repaired** — not partially repaired, not displaced into another defect. §13 confirms every mandatory field is reachable for `INDETERMINATE`; §16 confirms no precedence ambiguity was introduced; §25 (below) confirms no third missing-input defect was displaced into existence by this repair. |
| **F-147F.1-2** (empty-string citation) | Independently reconfirmed unaffected: AEMIC-REQ-022/101's own if-and-only-if invariant still tests only `is not None`, not non-emptiness; this repair touches `template_ref`/`template_version` sourcing exclusively, never `citation_text`'s own emptiness handling. Remains open, Non-Blocking. |
| **F-147F.1-3** (non-string citation typing) | Independently reconfirmed unaffected: `MissingCitationTextError`'s condition (AEMIC-REQ-064) still names only `citation_text is None`; a non-`str`, non-`None` value remains unaddressed by a distinct named condition. Unrelated to this repair. Remains open, Non-Blocking. |
| **F-147F.1-4** (deserialization cross-field ambiguity) | Reassessed at §18 above: neither worsened nor improved, since `template_ref`/`template_version` are unconditionally (not conditionally) mandatory, so the cross-field ambiguity this finding concerns does not extend to the two new fields. Remains open, Non-Blocking. |
| Direct-construction Informational observation | Independently reconfirmed still Informational: AEMIC-REQ-022's constructor-level invariant is the identical, unchanged enforcement point regardless of whether construction is reached via `evaluate()` or directly; a direct construction can still supply any `template_ref`/`template_version` value, exactly as before this repair for every other field (confirmed at §19 above). Remains Informational, not Blocking. |
| **FA-147D-1** (downstream IWC-001/PEC-001 revisions required) | Independently reconfirmed deferred, unaffected — §17's requirements are untouched by this repair's own disclosed section list. |
| **FA-147D-2** (Registry-unavailability failure mode) | Independently reconfirmed closed architecturally (§11.3/§13.2), unaffected by this repair. |
| **FA-147D-3** (citation/declaration drift risk) | Independently reconfirmed retained as a named limitation (§9), unaffected — this repair concerns `template_ref`/`template_version` sourcing, an entirely different field pair from the `eligible_identities`/`eligible_authority` drift this finding names. |

This phase did not rely solely on AEMIC-001's own §23 Finding Disposition
register in reaching the reassessments above; each row above was
independently re-derived from the relevant requirement text
(AEMIC-REQ-022, AEMIC-REQ-064, AEMIC-REQ-091/093, AEMIC-REQ-083-086,
AEMIC-REQ-034, AEMIC-REQ-047-049) before being compared against §23's
own stated disposition, and found consistent in every case.

---

## 25. Contract-Wide Implementability Sweep

The two previous independent verifications (Phase 147F: BF-147F-1;
Phase 147F.1: BF-147F.1-1) each discovered a distinct missing mandatory
input. This phase therefore performed a fresh, contract-wide
source-completeness audit rather than checking only template identity.

**Every mandatory public output field, exception, audit field, and
serialization field, independently enumerated against its producing
function, closed input source, validation, branch applicability, and
failure behavior:**

| Output/field | Producing function | Closed input source | Validation | Branch applicability | Failure behavior if absent |
|---|---|---|---|---|---|
| `AuthorityEvaluationOutcome.template_ref` | `evaluate` | `evaluate`'s own parameter 1 | Non-empty `str` | All three | `InvalidTemplateReferenceError` |
| `.template_version` | `evaluate` | `evaluate`'s own parameter 2 | Non-empty `str` | All three | `InvalidTemplateReferenceError` |
| `.claimed_identity` | `evaluate` | `evaluate`'s own parameter 3 | Non-empty `str` | All three | `InvalidClaimedIdentityError` |
| `.evaluation_result` | `evaluate` | Computed from parameters 3+4 | Closed 3-value enum | All three | N/A — always computable given valid `claimed_identity`/`declaration` |
| `.declaration_ref` | `evaluate`, via AEMIC-REQ-038's derivation | `declaration`'s own `(template_ref, template_version)` when non-`None` | Deterministic derivation rule | Conditional (non-`None` iff `declaration` resolved) | N/A — `None` is itself the correct, non-failing value for `INDETERMINATE` |
| `.citation_text` | `evaluate` | Parameter 7 | Non-`None` iff `ELIGIBLE` (AEMIC-REQ-022/101) | Conditional | `MissingCitationTextError` if `ELIGIBLE` and `None` |
| `.evaluated_at` | `evaluate` | Parameter 5 | Structural (ISO-8601), not independently enforced beyond being a `str` | All three | No named exception; treated as caller-supplied metadata, consistent with `evaluator_version`'s identical treatment |
| `.evaluator_version` | `evaluate` | Parameter 6 | None beyond `str` (AEMIC-REQ-040) | All three | N/A — no "correct" value is verified |
| `.schema_version` | `AuthorityEvaluationOutcome`'s own constructor | Fixed literal | Exact-match construction-time enforcement (AEMIC-REQ-039) | All three | Raises (unnamed generic per AEMIC-REQ-069, or `UnsupportedSchemaVersionError` at deserialization per AEMIC-REQ-041/093) |
| `EligibleAuthorityDeclaration.template_ref/.template_version/.eligible_identities/.declared_at/.declared_by/.schema_version` | `EligibleAuthorityDeclaration`'s own constructor | Caller-supplied at Declaration-authoring time (outside `evaluate`'s own boundary entirely) | Per AEMIC-REQ-015/017 | N/A — a distinct object's own construction, not `evaluate`'s concern | `MalformedDeclarationError` |
| `AuthorityRegistry.resolve`'s own return | Concrete Registry (deferred) | Storage layer | Per §12 | N/A | `AuthorityRegistryUnavailableError`/`AuthorityRegistryCorruptError` |
| Reason/provenance: `TemplateIdentityMismatchError`'s own trigger data | `evaluate` | `declaration`'s own identity vs. parameters 1-2 | Exact equality (AEMIC-REQ-103) | Conditional (`declaration` non-`None` only) | Raises the named exception itself |

**Additional categories independently inspected, per the governing
prompt's own list:**

- **Declaration reference** (`declaration_ref`) — covered above; no gap.
- **Reason codes** — this contract defines no reason-code field beyond
  `evaluation_result` itself (AEMIC-REQ-081 explicitly states "No
  additional field (a registry implementation identity, a reason code
  beyond `evaluation_result` itself) is required by this contract for
  v1.0") — a deliberate, disclosed non-requirement, not a silent gap.
- **Registry-resolution identity** — `evaluate` receives only the
  resolved `declaration` object, never a separate "resolution
  descriptor"; no mandatory field of this shape is named anywhere in
  §6/§16, so there is no missing source for a field that does not
  exist.
- **Evaluator/version identifiers** — `evaluator_version` covered above;
  no second version-identifying field is mandated.
- **Provenance fields** — `declared_by` (on `EligibleAuthorityDeclaration`,
  not the outcome) is caller-supplied at authoring time, outside
  `evaluate`'s own boundary; not affected by this repair.
- **Timestamps** — `evaluated_at` covered above; `declared_at` (on the
  Declaration) is likewise outside `evaluate`'s own boundary.
- **Schema IDs** — `schema_version` (both record types) covered above,
  fixed literals, not caller/evaluate-sourced.
- **Contract versions** — `evaluator_version` is the sole
  contract-version-adjacent marker this contract defines on the outcome
  itself; no second field of this kind is mandated.

**Determination: no third missing-input defect was found.** Every
mandatory field on both public record types, and every named exception's
own triggering condition, has a closed, reachable, independently-traced
source. This sweep was performed by independently enumerating the full
field/exception list from §4/§6/§13 first, then tracing each to its
producing function and input, rather than checking only the
`template_ref`/`template_version` pair the repair itself targets.

---

## 26. Testability Matrix

Independently derived tests, cross-checked against AEMIC-001's own §22
matrix and found each item covered:

1. `INDETERMINATE` with valid identity — covered (§22 matrix, item 1;
   §13 above).
2. `ELIGIBLE` with matching identity — covered (item 2).
3. `INELIGIBLE` with matching identity — covered (item 3).
4. Ref mismatch — covered (item 7, §22 matrix).
5. Version mismatch — covered (item 8).
6. Both mismatch — covered by the AND-conjunction's own truth table
   (§11); a dedicated fixture with both fields mismatched independently
   exercises the identical exception path as items 4/5, confirming no
   different (e.g. more/less severe) failure mode exists for a
   double mismatch.
7. Declaration absent — covered (item 1/4, restated).
8. Malformed ref — covered (item 9/11).
9. Malformed version — covered (item 10/11).
10. Unsupported version — **not a distinct condition in this contract's
    own vocabulary** (§10 above: "unsupported version" applies to
    `schema_version`, not `template_version`); the correct corresponding
    test is `UnsupportedSchemaVersionError` at deserialization
    (AEMIC-REQ-093), already covered by the pre-existing §18 serialization
    matrix row, unaffected by this repair.
11. Registry unavailable — covered, at the concrete-Registry layer
    (§22 matrix, `AEMIC-REQ-047-049` row); correctly out of `evaluate`'s
    own unit-test scope (AEMIC-REQ-073).
12. Duplicate declaration — covered at the concrete-Registry layer
    (§22 matrix, `AEMIC-REQ-045-046` row).
13. Mismatch plus missing citation — covered (item 12, §22 matrix;
    independently re-verified at §16 above, adversarial case 3).
14. Mismatch plus malformed citation — **not independently named as a
    distinct case** in AEMIC-001's own matrix; independently assessed as
    not requiring a distinct test, since "malformed citation" (a
    non-`str`, non-`None` value) is not itself a named raising condition
    under F-147F.1-3's own still-open disposition (§24) — testing this
    combination would exercise the same precedence question as item 13
    without a distinct expected outcome this contract currently defines.
    This gap is inherited from F-147F.1-3, not newly introduced by this
    repair.
15. Citation plus identity cross-pairing — covered by item 12/13's own
    combination logic; no additional distinct scenario identified beyond
    what AEMIC-REQ-104's total ordering already resolves.
16. Exact identity preservation — covered (item 6, serialization
    round-trip; §18 above).
17. Unicode identity — independently assessed: AEMIC-REQ-090's Unicode
    round-trip requirement, read as applying package-wide (§18 above),
    extends to `template_ref`/`template_version`; a dedicated Unicode
    round-trip test for these two fields specifically is not separately
    enumerated in AEMIC-001's own matrix, a minor test-matrix gap
    (§27, Testability-1, Non-Blocking) since the contract's own text
    already establishes the expected behavior (byte-for-byte, no
    normalization) even though a table row does not explicitly name it.
18. Deterministic repeated evaluation — covered (item 5).
19. Serialization round trip — covered (item 6).
20. Deserialized mismatch — reassessed at §18: not applicable in the
    same sense as a live `evaluate()`-time mismatch, since
    `AuthorityEvaluationOutcome` carries no `declaration` field to
    re-compare against post-deserialization; no gap, a structural
    non-applicability.
21. No hidden Registry identity lookup — covered (item 14, §22 matrix;
    the AST-style forbidden-import test).
22. No workflow import — covered (§22 matrix, `AEMIC-REQ-010-014` row).
23. No publication integration — covered (§22 matrix,
    `AEMIC-REQ-083-085` row).
24. Disclosure-only semantics — covered (§22 matrix,
    `AEMIC-REQ-027-029` row).
25. Complete field-source coverage — covered by this phase's own §25
    sweep, independently reconstructed rather than merely cited.

**Comparison with AEMIC-001's own amended matrix (§22):** every modified
requirement (AEMIC-REQ-019, 021, 038, 064, 072, 074, 075, 077, 081, 095,
103-107) has at least one falsifiable positive, negative, or adversarial
test named in the matrix row for AEMIC-REQ-019/021/103-106 or the
pre-existing rows it extends (AEMIC-REQ-072-077/101). No modified
requirement was found lacking a corresponding test-matrix entry.

---

## 27. New Findings

**Testability-1 (Non-Blocking).** AEMIC-001's own §22 matrix does not
explicitly enumerate a dedicated Unicode round-trip test case for
`template_ref`/`template_version` specifically (item 17 above), even
though the contract's own normative text (AEMIC-REQ-036, AEMIC-REQ-090)
already establishes the expected behavior unambiguously. This is a
test-matrix completeness observation, not a behavioral ambiguity — the
correct behavior is already fully specified; only an explicit table row
naming it is absent. Recommended disposition: a future implementation
phase's own test suite SHOULD include this case explicitly (it is
already implied, not newly required); no contract text change is
needed.

**Lifecycle-2 (Non-Blocking).** `.pcae/phase-completion-metadata.json`'s
`pushed_status` (`"pending"`) and `origin_main_head`/
`origin_main_head_count` (`0`/`0`) fields are stale relative to the
actual, current, fully-pushed-and-synchronized repository state (§3
above). The `phase_commits[0].hash` field, by contrast, received its own
dedicated sync commit (`05ccb40d`) and is accurate. This is a
bookkeeping/documentation gap in Phase 147E.2's own finalization, not a
substantive defect in AEMIC-001 v1.2 itself, and does not affect this
phase's own verdict on the contract. Recommended disposition: a future
phase (or this phase's own closing bookkeeping, if separately
authorized) may correct these three fields; no contract repair is
implicated.

No Blocking or additional Non-Blocking finding was identified beyond the
two above and the pre-existing, reassessed-and-reconfirmed findings at
§24.

---

## 28. No-Go Confirmation

This phase did not modify `src/pcae/**` (no file under
`src/pcae/authority_evaluation/` exists after this phase; confirmed by
direct filesystem search, §3/§8, unchanged from before this phase).

This phase did not modify any production test under `tests/**` (no test
file under `tests/` references `authority_evaluation` or `AEMIC` before
or after this phase, confirmed by direct search, §8).

This phase did not implement authority evaluation, create any model, or
create a Registry — no code exists; this remains contract prose only.

This phase did not modify AEMIC-001 itself (`docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`
was read-only throughout this phase's own execution — every quotation
above is drawn from the file's own current, unedited text).

This phase did not modify AEM-001, IWC-001, IWPC-001, PEC-001, CHGR-001,
TAMC-001, TAMPC-001, or GAC-001.

This phase did not modify Session, any readiness package, Publication
Coordinator, CHGR construction, or add any publication gating.

This phase did not change runtime, execution capability, or policy —
`pcae runtime inspect` (§31) confirms Observed/observe/unavailable,
identical before and after this phase.

Only this report
(`docs/PHASE_147F.2_AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT_SECOND_REPAIR_INDEPENDENT_VERIFICATION.md`)
and ordinary governance bookkeeping (this phase's own task contract,
`PROJECT_STATUS.md`, `tasks/DONE.md`, `.pcae/phase-completion-*`) are
authorized to be created or modified by this phase, confirmed by
`git status --short` before this phase's own writing began (§3) and to
be re-confirmed at phase close (§31).

The repair remains untrusted-until-verified per this phase's own
authorization scope; this phase repaired nothing, consistent with its
own governing instruction ("Do not repair AEMIC-001 during this
phase").

---

## 29. Overall Verdict

**SECOND REPAIR VERIFIED WITH NON-BLOCKING FINDINGS.**

- BF-147F.1-1 is fully repaired (§5, §13, §24) — independently confirmed,
  not accepted from Phase 147E.2's own account.
- Every `EvaluationResult` branch is constructible, including
  `INDETERMINATE` (§13).
- Singular template-identity ownership is confirmed (§9) — no
  preference hierarchy, no fallback.
- Declaration agreement is deterministic (§11, §17).
- The mismatch error (`TemplateIdentityMismatchError`) is coherent,
  correctly classified, and non-collapsing (§12).
- Error precedence is complete and unambiguous across every adversarial
  combination tested (§16).
- Determinism and serialization requirements are complete and
  internally consistent (§17, §18).
- No additional missing-input defect was found by a fresh, contract-wide
  sweep undertaken specifically because the prior two independent
  verifications each found one (§25).
- Disclosure-only semantics are preserved; the new parameters do not
  become authorization inputs (§19, §20).
- AEM-001 compatibility is confirmed, and this repair is independently
  shown to *restore* rather than merely preserve compatibility with
  AEM-REQ-018's own pre-existing, unconditional field requirement (§23).
- The Registry boundary is unchanged (§21); the deferred integration
  boundary is unchanged (§22).
- No unresolved implementation-critical decision remains beyond the
  pre-existing, already-disclosed, already-classified limitations this
  phase reassessed and reconfirmed unaffected (§24), plus the two new
  Non-Blocking findings recorded at §27 (a test-matrix completeness
  observation and a lifecycle-bookkeeping staleness observation), neither
  of which bears on the contract's own implementability or correctness.

---

## 30. Recommended Next Phase

**147G — Authority Evaluation Model Core Implementation.**

Implementation must remain limited to the standalone AEMIC-001 v1.2
core: `models.py`, `evaluation.py`, `registry.py` (ABC only, no
concrete subclass), `errors.py`, `serialization.py`, per §3.2's own
required-module list.

It must not include: a concrete filesystem Registry implementation
unless separately authorized (§3.3's own deferral, unaffected by this
phase); Interactive Workflow integration; Session changes;
readiness-package changes; Publication Coordinator integration; CHGR
construction changes; publication gating; runtime changes; or IWC-001/
PEC-001 amendments (§17's deferred integration boundary, independently
reconfirmed unaffected at §22 above).

This recommendation is not an authorization.

---

**End of Phase 147F.2 report.**
