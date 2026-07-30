# Phase 147F — Authority Evaluation Model Implementation Contract Independent Verification

## Contract identity and status

**Phase:** 147F
**Mode:** Independent Implementation Contract Verification (documentation-only;
no production code, contract, schema, or test file modified; no
implementation authorized)
**Predecessor:** 147E — Authority Evaluation Model Implementation Contract
Freeze (IMPLEMENTATION CONTRACT FROZEN WITH OBSERVATIONS)
**Subject:** AEMIC-001 v1.0 — Authority Evaluation Model Implementation
Contract (`docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`)
**Runtime baseline:** Observed / observe / unavailable — unchanged by this
phase; confirmed at §26 below.

---

## 1. Executive Summary

This phase independently reconstructed the implementation-level
requirements for `pcae.authority_evaluation` directly from AEM-001 v1.0,
Phase 147C's independent verification, IWC-001, IWPC-001, PEC-001,
CHGR-001, TAMC-001/TAMPC-001, GAC-001, the Decision Template and Human
Governance Record schemas, and direct re-inspection of current source —
treating Phase 147D's implementation architecture strictly as
non-authoritative design evidence — before opening AEMIC-001 itself.

**Result: the independent reconstruction agrees with AEMIC-001 on every
architectural question except one.** Package boundary, forbidden-import
direction, disclosure-only semantics, Registry read-only/duplicate/
availability semantics, identity/versioning rules, serialization rules,
persistence deferral, and the deferred-integration boundary are all
correctly, concretely, and testably frozen, and each of Phase 147D's
carried-forward findings (FA-147D-1, FA-147D-2, FA-147D-3) is disposed of
consistently with an independent re-reading of the same primary sources.

**One Blocking defect was found and confirmed by direct textual
attack.** AEMIC-001 freezes `evaluate()` with a closed, exactly-four
parameter signature (`claimed_identity`, `declaration`, `evaluated_at`,
`evaluator_version` — AEMIC-REQ-019/020) and simultaneously requires,
"checked at construction time, not left to caller discipline"
(AEMIC-REQ-022), that every `AuthorityEvaluationOutcome` with
`evaluation_result == eligible` carry a non-`None` `citation_text`. No
parameter of `evaluate()`, and no field of `EligibleAuthorityDeclaration`
(closed to exactly six fields, none of them `citation_text` —
AEMIC-REQ-015/016), carries citation text into the function. AEMIC-REQ-031
even asserts, in the same sentence that discloses this gap, that
"Declarations SHALL copy the citation text verbatim into the constructed
`AuthorityEvaluationOutcome.citation_text` at evaluation time" — a claim
the same requirement's own next clause contradicts by confirming the
Declaration carries no such field and `evaluate()` accepts no such
parameter. As specified, `evaluate()` cannot construct a valid `eligible`
outcome under any well-formed input: every attempt either violates
AEMIC-REQ-020's closed-parameter rule (by requiring an undeclared fifth
input) or AEMIC-REQ-022's if-and-only-if invariant (by returning
`eligible` with `citation_text = None`). This is not the disclosed,
already-accepted "how does the caller obtain the citation text" gap
(AEMIC-REQ-032, itself sound) — it is a distinct, one-level-deeper defect:
even a caller that already possesses the correct citation text in hand has
no contractually sanctioned way to hand it to `evaluate()`. The only
practical resolution available to a real implementer is to construct
`AuthorityEvaluationOutcome` directly, bypassing `evaluate()` entirely for
the `eligible` case — which reopens exactly the caller-controlled
citation-injection risk AEMIC-REQ-022's own "not left to caller
discipline" framing exists to foreclose, and which no requirement in this
contract authorizes, prohibits, or tests.

Four findings are reassessed and reaffirmed **Non-Blocking**, consistent
with independent re-derivation from primary sources (§21). One new finding
is **Blocking** (§22, BF-147F-1).

**Overall Verdict: NOT VERIFIED.**

Recommended next phase: **147E.1 — Authority Evaluation Model
Implementation Contract Repair** (a recommendation, not an authorization;
§28).

---

## 2. Authorization and Independence Method

Per the governing prompt's explicit independence discipline (§2), AEMIC-001
was not opened until the reconstruction below (§3) and the existing-state
reinspection (§4) were both complete. Reading order actually followed:

1. AEM-001 v1.0 (`docs/contracts/AUTHORITY_EVALUATION_MODEL_CONTRACT.md`) —
   read in full, as the sole governing predecessor contract.
2. Phase 147C's independent verification report — read in full, as the
   most recent independent check on AEM-001 (not itself authoritative over
   AEMIC-001, but relevant prior-verification context).
3. Phase 147D's implementation architecture — read in full, explicitly
   treated throughout as **non-authoritative design evidence only**,
   exactly as the governing prompt requires (§2). Where this report cites
   Phase 147D, it is to compare AEMIC-001's own choice against 147D's
   recommendation, never to treat 147D's prose as binding.
4. IWC-001 §6/§11 (cited directly, to independently confirm/falsify
   F-147C-2's continued unresolved status), IWPC-001, PEC-001, CHGR-001,
   TAMC-001/TAMPC-001, and GAC-001 §9 — consulted via AEM-001's own
   citations, direct grep, and section-header confirmation (§4, §21).
5. Direct source re-inspection: `src/pcae/interactive_workflow/models/session.py`,
   `src/pcae/governance/publication/coordinator.py`,
   `src/pcae/governance/publication/record.py`,
   `tests/test_phase_144c_publication_coordinator.py`,
   `src/pcae/schema_resources/chgr/records/decision_template.schema.json`,
   `src/pcae/schema_resources/chgr/records/human_governance_record.schema.json` —
   performed before opening AEMIC-001 (§4).
6. Only after 1–5 above was `docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`
   opened, read in full, and compared section-by-section against the
   reconstruction (§5 onward).

`pcae session bootstrap --agent-id claude-local --sync-lock`, `pcae check`,
`pcae health`, `pcae doctor task-memory`, `pcae runtime inspect`, and
`pcae push check` were run at phase start: repository clean, branch
`main`, 0 commits ahead/behind `origin/main`, health `healthy`, runtime
`Observed`/`observe`/`unavailable`, Registry `empty`, plugin count `0`, no
active governed phase beyond the idle placeholder task. `PROJECT_STATUS.md`
was treated as authoritative throughout, consistent with the governing
prompt's instruction.

---

## 3. Independent Requirement Reconstruction

Reconstructed from AEM-001, IWC-001, IWPC-001, PEC-001, CHGR-001,
TAMC-001/TAMPC-001, GAC-001, and current source — before opening AEMIC-001.

| # | Requirement area | Independent reconstruction | Classification |
|---|---|---|---|
| 1 | Package ownership | A new, self-contained, sibling package (`pcae.authority_evaluation`) is the only architecture consistent with AEM-001 §0's declared non-amendment of IWC-001/IWPC-001/PEC-001/CHGR-001 — no existing package owns this concept | Contractually required |
| 2 | Dependency direction | Zero dependency on `interactive_workflow`, `governance.publication`, `cltr`, or any CLI/command/core/lifecycle layer; standard library plus own sibling modules only (AEM-REQ-028, PEC-REQ-113) | Contractually required |
| 3 | Public domain types | `EligibleAuthorityDeclaration` (AEM-REQ-007), `AuthorityEvaluationOutcome` (AEM-REQ-018), `EvaluationResult` (AEM-REQ-020) — closed, immutable, exactly as AEM-001 names them; a fourth "request" type is not required, since AEM-001 §5 never names one beyond the evaluation function's own inputs | Contractually required (first three); permitted design choice (no separate request type) |
| 4 | Eligible-authority declaration semantics | Closed set-membership only; no role/scope/time-bounding (AEM-REQ-004/006); immutable once evaluated against, at the authoring-workflow level (AEM-REQ-008) | Contractually required |
| 5 | Evaluation request semantics | Four already-collected/caller-supplied values: claimed identity, a Registry-resolved Declaration-or-`None`, a caller-supplied timestamp, a caller-supplied evaluator-version marker (AEM-REQ-014/018) | Contractually required |
| 6 | Evaluation outcome semantics | Total, deterministic, pure function; exactly one outcome per call, never partial/streaming (AEM-REQ-016/018/019) | Contractually required |
| 7 | Disclosure-only behavior | No gating of Confirmation/Readiness/Authorization/Publication; naming and semantics must foreclose any authorization-shaped reading (AEM-REQ-003/037) | Contractually required |
| 8 | Identity and version rules | `(template_ref, template_version)` is the canonical Decision Template identity tuple for every purpose this package defines (AEM-001 §5.5); no normalization performed, non-empty-only validation (implied by AEM-REQ-023's minimal validation discipline) | Contractually required |
| 9 | Registry abstraction | A read-only ABC, `resolve(template_ref, template_version) -> Declaration \| None`, no write path (AEM-REQ-010/011) | Contractually required |
| 10 | Lookup behavior | Pure, `None` for absence, never raising for "no Declaration" (AEM-REQ-010/012) | Contractually required |
| 11 | Duplicate/ambiguity handling | AEM-001's text does not name this explicitly, but AEM-REQ-009's determinism guarantee and AEM-REQ-012's purity guarantee jointly forbid a `resolve` that could non-deterministically pick among multiple candidates for one identity tuple — an implementation-level gap AEM-001 leaves for a later phase to close | Architecturally necessary (AEM-001 requires the *outcome*, i.e., no ambiguity, without naming the *mechanism*) |
| 12 | Unavailable-registry behavior | Not named anywhere in AEM-001's own text (confirmed by direct re-reading of AEM-001 §4.5/§6) — a new failure mode any concrete implementation must name, distinct from "no Declaration" | Architecturally necessary, not contractually named by AEM-001 itself |
| 13 | Malformed-record behavior | Same reasoning as #12 — AEM-001 assumes the Registry always answers cleanly; a concrete backend's own malformed-storage case is an implementation-level gap | Architecturally necessary |
| 14 | Serialization requirements | Not named by AEM-001 at all; a wire format is an ordinary implementation necessity for any persisted record, not something AEM-001 itself constrains beyond `schema_version` literals (AEM-REQ-007/018) | Permitted design choice, contractually anchored only at the `schema_version` literal |
| 15 | Deterministic evaluation requirements | AEM-REQ-009/012/016 jointly require determinism at every layer | Contractually required |
| 16 | Auditability | Every outcome that contributes a citation must be reconstructible from already-persisted data (AEM-REQ-030); no persistence mechanism for `ineligible`/`indeterminate` is itself required (AEM-REQ-031) | Contractually required (reconstructibility); deferred integration concern (persistence of non-eligible outcomes) |
| 17 | Compatibility boundaries | Zero modification to any existing file; total backward compatibility for any Decision Template lacking a Declaration (AEM-001 §0's compatibility policy, restated at §15 Non-Goals) | Contractually required |
| 18 | Downstream integration exclusions | Wiring the mechanism into `Session`/`PublicationReadinessPackage`/`PublicationCoordinator`/CHGR construction requires separately-governed IWC-001/PEC-001 revisions this contract cannot itself authorize (AEM-001 §0, §2.2, §11.2) | Contractually required (as an exclusion) |
| 19 | Security properties | No new identity/credential collection; no gating; Registry read-only; no circular trust closure beyond disclosure (AEM-REQ-011/013/014/028/032) | Contractually required |
| 20 | Testability requirements | Pure-function shape must be independently unit-testable without Session/Package/Registry-implementation fixtures (implied directly by AEM-REQ-009/012/016's purity/determinism guarantees, which are meaningless if not independently testable) | Architecturally necessary |

**Critical independent observation carried into §7/§19 below, derived
before AEMIC-001 was opened:** AEM-001 §5.3 (AEM-REQ-018) states
`citation_text` is "populated only when `evaluation_result == 'eligible'`"
as a field-level description of the `AuthorityEvaluationOutcome` shape, but
AEM-001's own §5 (the Evaluation Function) names only `claimed_identity`
and a Declaration-or-`None` as evaluation's inputs (AEM-REQ-014, "the sole
evidentiary input to evaluation is the claimed decision-maker identity").
**AEM-001 itself never explains, at the contract-freeze level, how the
evaluation function obtains citation text to populate this field** — this
is a genuine open question in AEM-001 that an implementation contract must
resolve, independently identified before AEMIC-001 was opened. This is the
exact question §7/§19 below find AEMIC-001 to have *named* (via AEMIC-REQ-032)
but not actually *resolved* at the function-signature level.

---

## 4. Existing-State Reinspection

Performed via direct source inspection, independent of AEMIC-001's own
claims (which were not yet read).

| Claim | Result | Evidence |
|---|---|---|
| `pcae.authority_evaluation` does not yet exist | **Confirmed** | `find src -iname "*authority_evaluation*"` — no results |
| No authority evaluator exists | **Confirmed** | `grep -rn "EligibleAuthorityDeclaration\|AuthorityEvaluationRequest\|AuthorityEvaluationOutcome" src/ tests/` — no results |
| No `EligibleAuthorityDeclaration` exists | **Confirmed** | same grep, no results |
| No `AuthorityEvaluationRequest` exists | **Confirmed** | same grep, no results |
| No `AuthorityEvaluationOutcome` exists | **Confirmed** | same grep, no results |
| No authority Registry exists | **Confirmed** | no results for `AuthorityRegistry` anywhere in `src/`/`tests/` |
| No authority declaration persistence exists | **Confirmed** | no `.pcae/authority-declarations/` directory or reference anywhere |
| `Session.template_ref` remains opaque | **Confirmed** | `session.py:87` — bare `str`, validated only for non-emptiness (line 108); no resolution against any registry |
| Decision Template schema still contains `eligible_authority` | **Confirmed** | `decision_template.schema.json:27,63` — required, `{"type": "string", "minLength": 1, "maxLength": 500}`, unchanged since Phase 143E/147C/147D |
| CHGR schema still contains `authority_basis_claimed` | **Confirmed** | `human_governance_record.schema.json:67-71` — optional string field, description unchanged since Phase 146D, still describing itself as citing "the template's own `eligible_authority` field" |
| Publication construction still discloses authority absence | **Confirmed** | `record.py:249` — `"authority_basis_claimed is not populated: no Decision Template eligible_authority ..."`, `_authority_basis_disclosure_present` fail-closed check (`record.py:116-137`) unchanged |
| No current publication path consumes authority evaluation | **Confirmed** | `coordinator.py` imports only `pcae.interactive_workflow.errors` and `pcae.interactive_workflow.publication_handoff.{handoff,models}` — no reference to any authority-evaluation concept |
| No hidden runtime or policy integration exists | **Confirmed** | `pcae runtime inspect` — Runtime `not_implemented`, Registry `empty`, plugin count `0`, identical to 147C/147D's own confirmed baseline |

**One additional, independently significant confirmation:** the
forbidden-import boundary test (`tests/test_phase_144c_publication_coordinator.py`,
`_FORBIDDEN_IMPORT_ROOTS`, lines 362–371) does **not** yet list
`pcae.authority_evaluation` — expected, since the package does not exist,
and consistent with AEMIC-001's own disposition (§15 below) that a future
implementation phase, not this contract's own freeze, is responsible for
adding an equivalent "not yet wired in" regression guard.

No claim in AEMIC-001's own §1/§4 (read subsequently) was found to be
factually incorrect against this independent reinspection.

---

## 5. AEMIC-001 Requirement Inventory

AEMIC-001 defines `AEMIC-REQ-001` through `AEMIC-REQ-100`, grouped across
24 narrative sections plus a Requirement/Test Matrix (§22) and Finding
Disposition register (§23). Full per-requirement disposition is provided
in the Requirement-Verification Matrix at §27. Section-level summary:

| AEMIC-001 §§ | Subject | Independent verification result |
|---|---|---|
| 1 | Purpose, independent reconstruction, 147D-choice classification | **Supported** — the classification table (§1.1) correctly distinguishes Required/Permitted/Deferred choices; independently re-derivable from AEM-001 alone |
| 2 | Scope and no-go boundary | **Supported** |
| 3 | Package boundary | **Supported** |
| 4 | `EligibleAuthorityDeclaration` | **Supported** |
| 5 | Evaluation inputs | **Contradicted** — see §6/§7 below (BF-147F-1) |
| 6 | `AuthorityEvaluationOutcome` | **Contradicted** in part — the closed-shape table (§6) and the schema_version/field descriptions are sound; the if-and-only-if invariant (§6.1, AEMIC-REQ-022) is sound as an invariant but **unsatisfiable** given §5/§14's signature (BF-147F-1) |
| 7 | `EvaluationResult` enum | **Supported** |
| 8 | Disclosure-only semantics | **Supported** |
| 9 | Citation-source reconciliation | **Contradicted** — AEMIC-REQ-031 is internally self-contradictory (BF-147F-1) |
| 10 | Identity and versioning | **Supported** |
| 11 | Registry abstraction | **Supported** |
| 12 | Filesystem persistence contract (deferred) | **Supported** as a deferred-phase specification |
| 13 | Failure taxonomy | **Supported**, with one downstream consequence noted at §11 below (the base-exception fallback path, AEMIC-REQ-069, is the only exit available to a real `evaluate()` attempting an eligible construction under the current signature) |
| 14 | Evaluation function contract | **Contradicted** — see §5 above (BF-147F-1) |
| 15 | Security contract | **Supported**, with one new adversarial finding (§18 below) directly caused by BF-147F-1 |
| 16 | Auditability | **Supported**, contingent on BF-147F-1's resolution (an unconstructable `eligible` outcome cannot be audited either) |
| 17 | Deferred integration boundary | **Supported** |
| 18 | Serialization and digest contract | **Supported** |
| 19 | No-Go boundary confirmation | **Supported** — independently confirmed at §23 below |
| 20 | Contract quality review | **Contradicted** — AEMIC-REQ-095's own self-certification ("internally coherent... no requirement above contradicts another") is itself falsified by BF-147F-1 |
| 21 | Amendment contract | **Supported** |
| 22 | Requirement/Test Matrix | **Supported** in form; one row (AEMIC-REQ-021-023) is testable only via direct model construction bypassing `evaluate()`, which is itself evidence for BF-147F-1 (§20 below) |
| 23 | Finding disposition | **Supported** for F-147C-1/F-147C-2/FA-147D-1/FA-147D-2/FA-147D-3's own dispositions (§21 below); silent on the new defect this phase discloses |
| 24 | Non-goals | **Supported** |

---

## 6. Public Type Verification

### 6.1 `EligibleAuthorityDeclaration` (§4, AEMIC-REQ-015–018)

Six required fields (`template_ref`, `template_version`,
`eligible_identities`, `declared_at`, `declared_by`, `schema_version`),
each with a stated structural validation rule, immutability, and no
optional fields. This is complete, closed, deterministic, and directly
testable. **No defect found.** One observation: `declared_at`'s
"parseable as ISO-8601 (structural only)" validation rule is looser than
`schema_version`'s exact-literal rule but this asymmetry is disclosed and
consistent with `Session`'s own precedent (AEMIC-REQ-015's own table
cites this explicitly) — not a defect.

### 6.2 `AuthorityEvaluationRequest` (§5, AEMIC-REQ-019–020)

No distinct request type is defined; `evaluate`'s four parameters
collectively serve this role, a design choice this contract explicitly
justifies (§1's independent reconstruction agrees this is a permitted
design choice, not an omission). **However**: this exact set of four
parameters is where BF-147F-1 originates (§7 below) — the closed
parameter list, closing off "no caller-supplied metadata beyond the four
parameters above" (AEMIC-REQ-020), is precisely what makes `citation_text`
unreachable inside `evaluate()`. Whether contextual fields could create
hidden policy inputs: **no** — the four parameters named are exactly the
ones AEM-001 authorizes (identity, Declaration-or-`None`, timestamp,
version marker); no hidden policy input is smuggled in. The defect is an
omission (missing a required data channel), not a hidden-input problem.

### 6.3 `AuthorityEvaluationOutcome` (§6, AEMIC-REQ-021–023)

Eight fields, correctly typed, correctly described as verbatim copies of
evaluation inputs (`template_ref`, `template_version`, `claimed_identity`,
`evaluated_at`, `evaluator_version`) plus three "computed" fields
(`evaluation_result`, `declaration_ref`, `citation_text`) plus
`schema_version`. The `citation_text` if-and-only-if invariant
(AEMIC-REQ-022) is a sound *invariant* in isolation — it correctly
specifies what must be true of any valid instance. **The defect is not in
the invariant itself; it is in the absence of any specified mechanism by
which the one and only documented construction path (`evaluate()`, §14)
can satisfy it for the `eligible` case.** See §7 for the full analysis.

### 6.4 `EvaluationResult` — enumerations and closed sets (§7, AEMIC-REQ-024–026)

Three-member closed `Enum`, wire values `"eligible"`/`"ineligible"`/
`"indeterminate"`, no fourth value, bound as a real `Enum` type rather than
a bare string. State completeness: **confirmed** — every one of AEM-001's
own three cases (Declaration resolves and identity is a member; Declaration
resolves and identity is not a member; no Declaration resolves) maps to
exactly one enum member, with no overlap and no gap. Absence-vs-error
distinction: **confirmed** — `indeterminate` is a successful evaluation
result, never conflated with a raised exception (AEMIC-REQ-065).
Forward-compatibility: a fourth value requires a major revision
(AEMIC-REQ-025), consistent with AEM-001's own extension-point discipline.
**No defect found in the enum itself.**

---

## 7. Citation-Source Reconciliation (F-147C-1 / FA-147D-3 continued attack)

This section is where BF-147F-1 is fully substantiated, following the
governing prompt's own instruction to "attempt to construct contradictory
but contract-valid records" and to attack whether AEMIC-001 "assumes access
to a Decision Template object that the standalone implementation will not
possess."

**Step 1 — is there exactly one semantic source of truth for the citation?**
AEMIC-REQ-030 names `decision_template.schema.json`'s `eligible_authority`
field as the sole citation-text source. This part is sound, and correctly
closes F-147C-1/Phase 147D's own reconciliation at the *textual-source*
level: there is no second, independently-authored citation text field
anywhere in this contract's own model (`EligibleAuthorityDeclaration` has
no `citation_text` field, per AEMIC-REQ-015/016 — confirmed at §6.1
above). So far, no duplication of the citation *text itself* exists.

**Step 2 — does the contract assume access to a Decision Template object the
standalone implementation will not possess?** Yes, and AEMIC-REQ-032
names this honestly: "there is no `DecisionTemplate` Python artifact
today... a future, separately-governed Decision Template authoring/lookup
mechanism... is a precondition for any real caller to supply a
`citation_text` in practice." This framing treats the problem as entirely
external to the package — a future caller's problem, not this package's
problem — and that framing is where the contradiction is introduced.

**Step 3 — attempt to construct a contradictory but contract-valid
record.** Attempt: construct a valid `EligibleAuthorityDeclaration` (six
fields, all present, structurally valid per AEMIC-REQ-015). Attempt to call
`evaluate(claimed_identity, declaration, evaluated_at, evaluator_version)`
where `claimed_identity` is a member of `declaration.eligible_identities`.
Per AEMIC-REQ-024, the correct `evaluation_result` is `ELIGIBLE`. Per
AEMIC-REQ-022, the constructed outcome **must** carry a non-`None`
`citation_text`. But `evaluate`'s own four parameters (AEMIC-REQ-019),
closed by AEMIC-REQ-020 ("No caller-supplied metadata beyond the four
parameters above is accepted"), contain no value that could become
`citation_text` — not `claimed_identity` (the evaluated identity, not the
template's authority text), not `declaration` (whose six fields, per
AEMIC-REQ-015/016, do not include one), not `evaluated_at` or
`evaluator_version` (both are metadata, not citation content). **There is
no well-formed call to `evaluate()`, as specified, that can produce a
non-`None` `citation_text` for an `ELIGIBLE` result.** Every attempt to
satisfy AEMIC-REQ-022 for the `ELIGIBLE` case requires an input this
contract's own §5 explicitly forbids (AEMIC-REQ-020); every attempt that
respects the closed signature produces `citation_text = None`, which
directly violates AEMIC-REQ-022's own if-and-only-if invariant. This is a
genuine, textually demonstrable contradiction between §5/§14 and §6.1,
not a hypothetical edge case.

**Step 4 — is the drift/contradiction explicit and safely contained, or
does it create two independent (and here, zero available) authority
claims?** AEMIC-REQ-031's own text is the clearest evidence this is not
safely contained — it is not merely under-specified, it is
**self-contradictory within a single requirement**:

> "AEMIC-REQ-031. Declarations SHALL copy the citation text verbatim into
> the constructed `AuthorityEvaluationOutcome.citation_text` at evaluation
> time (not merely hold a reference to be dereferenced later)... 
> `EligibleAuthorityDeclaration` itself, per AEMIC-REQ-015, does not carry
> a `citation_text` field at all in v1.0 — the citation text is sourced
> from the Decision Template's own `eligible_authority` field by whichever
> future authoring/evaluation-caller workflow constructs the `evaluate()`
> call, external to this package's own domain model (§5's four parameters
> do not include a `citation_text` parameter; this is a disclosed
> consequence, not an oversight...)."

The requirement asserts, in its own opening clause, that something
("Declarations") copies citation text into the outcome "at evaluation
time" — language that presupposes a data channel into `evaluate()` exists
— and then, in the same paragraph, confirms that channel does not exist
(`EligibleAuthorityDeclaration` has no such field; `evaluate()`'s four
parameters do not include one). §9's later text compounds this: line
537 of the contract (§9, discussing exact-text-equality) states "this
package **receives** `citation_text` indirectly through `evaluate`'s
caller, per AEMIC-REQ-031/032" — asserting reception of a value that
§5/§14's own closed signature has no parameter to carry. **This is not a
disclosed limitation with a stated, safe reason it is acceptable to defer
(the pattern AEMIC-REQ-032/034 correctly follow elsewhere) — it is an
internal contradiction between two normative requirements, each written
as if the other's constraint did not exist.**

**Step 5 — classification.** Per the governing prompt's own instruction
("Classify any successful contradiction as Blocking unless the contract
explicitly and safely contains it"): this contradiction is **not**
explicitly and safely contained — no requirement anywhere in AEMIC-001
proposes a fifth parameter, an amended six-field-plus-`citation_text`
Declaration shape, or a separate "outcome construction, bypassing
`evaluate()`" path with its own governing rules. It is classified
**Blocking** (BF-147F-1, §22 below).

---

## 8. Disclosure-Only Boundary Verification

Independently attacked: can AEMIC-001 be implemented as an authorization
engine? Every method/type name AEMIC-001 requires
(`evaluate`, `resolve`, `EligibleAuthorityDeclaration`,
`AuthorityEvaluationOutcome`, `EvaluationResult`) is disclosure-shaped, not
authorization-shaped; AEMIC-REQ-027 explicitly forbids `authorize`/`grant`/
`permit`/`allow`/`deny`-named public API surface, and AEMIC-REQ-028
consolidates AEM-REQ-003/037/038/039/040 into one binding
"MAY only... SHALL NOT..." list covering: determining legal authority;
granting/denying/authorizing; policy beyond closed set-membership; human
eligibility beyond the closed check; and Runtime/Permission Broker/
execution capability. No terminology anywhere in AEMIC-001 (audit fields,
outcome names, reason codes, examples, integration language) was found
that could reasonably be read as implying authorization rather than
disclosure. **Holds. No defect found**, independent of BF-147F-1 (the
citation-plumbing defect is an implementability defect, not a
disclosure-boundary defect — nothing about it grants authority; it simply
makes the `eligible` outcome unconstructible via the sanctioned path).

---

## 9. Registry Contract Verification

Exact method set: `resolve(template_ref, template_version) ->
Declaration | None`, no `create`/`persist`/`delete`/`list`/`enumerate`
(AEMIC-REQ-042). Lookup keys: the exact `(template_ref, template_version)`
tuple, no partial/fuzzy match (AEMIC-REQ-037/AEMIC-REQ-042, §15's security
table). Missing-declaration behavior: `None`, never raise
(AEMIC-REQ-044). Duplicate behavior: exactly one Declaration resolvable
per identity tuple by construction of the ABC's own return-value shape;
a concrete implementation encountering more than one candidate MUST raise
`AuthorityRegistryCorruptError`, never first-match-select
(AEMIC-REQ-045 — explicitly, textually, forbids first-match ambiguity).
Historical-version coexistence: explicitly permitted, no "active version"
selection logic exists since the tuple itself is the exact selector
(AEMIC-REQ-046). Deterministic ordering: not applicable — no enumeration
method exists on the ABC at all (AEMIC-REQ-050). Case-normalization
collisions: none possible, since AEMIC-REQ-036 mandates exact
case-sensitive string equality with no normalization anywhere in this
package. Identity aliasing / version shadowing: not reachable under the
ABC's own exact-tuple-match contract. Inconsistent retrieval by
declaration ID vs. template identity: not applicable — `declaration_ref`
(AEMIC-REQ-038) is derived *from* the same `(template_ref,
template_version)` tuple, never an independent identifier a caller could
use for a different, inconsistent lookup path. Silent fallback: forbidden
throughout (§11 below).

**A Registry contract that allows materially different outcomes for
equivalent repository contents should be treated as Blocking** (governing
prompt's own instruction) — independently verified: it does not. Given
identical on-disk state, `resolve` is required to be pure and
deterministic (AEMIC-REQ-043), and any ambiguity in that state itself
(duplicates) is required to raise, never silently resolve one way or
another (AEMIC-REQ-045). **Holds. No defect found.**

---

## 10. Registry-Unavailability Verification

FA-147D-2's claimed closure is re-evaluated, not merely accepted.
Independently confirmed distinct handling for: declaration absent (`None`,
AEMIC-REQ-044); registry unavailable (`AuthorityRegistryUnavailableError`,
AEMIC-REQ-047); registry unreadable / permission denied / path invalid
(folded into the same `AuthorityRegistryUnavailableError` category,
AEMIC-REQ-068 — classified consistently as an infrastructure-layer
refusal); registry corrupt (`AuthorityRegistryCorruptError`,
AEMIC-REQ-048, explicitly including the duplicate-record case,
AEMIC-REQ-045); unsupported implementation (not a distinct failure mode —
no plugin/adapter selection mechanism exists for `AuthorityRegistry`, so
there is no "unsupported implementation" condition to fail on); internal
inconsistency (folded into `AuthorityRegistryCorruptError`, AEMIC-REQ-048).

Verified: infrastructure failure cannot be translated into `not_declared`
(`None`/`indeterminate`) — AEMIC-REQ-047's own text explicitly forbids
this conflation ("Conflating the two would misreport an operational fault
as a substantive `indeterminate` evaluation result"). Cannot be translated
into successful disclosure, fallback declaration, inferred authority, or
empty citation — no code path in AEMIC-001's own specification permits an
infrastructure failure to reach `evaluate()` at all (`evaluate()` itself
never touches the Registry, AEMIC-REQ-073 — the Registry failure and the
evaluation function are structurally separated, so a Registry failure can
only ever surface as a raised exception from `resolve()`, before
`evaluate()` is ever called).

The outcome-versus-exception split is complete (three raise conditions:
absent-but-answered `None`; unavailable; corrupt — jointly exhaustive of
"the Registry was consulted" outcomes) and testable
(AEMIC-REQ-049 explicitly requires all three be independently reproducible
from distinct, controlled fixtures). **FA-147D-2 is fully closed. No
defect found.**

---

## 11. Failure Taxonomy Verification

Six named exception types across two categories (§13.1 domain: 
`InvalidClaimedIdentityError`, `InvalidTemplateReferenceError`,
`MalformedDeclarationError`, `UnsupportedSchemaVersionError`; §13.2
infrastructure: `AuthorityRegistryUnavailableError`,
`AuthorityRegistryCorruptError`), plus one base-class fallback
(AEMIC-REQ-069, reserved for conditions the enumeration does not
anticipate).

For each: stable code (class name — stable); semantic uniqueness (each
condition maps to exactly one class, confirmed distinct at AEMIC-REQ-067);
domain-vs-infrastructure classification (explicit in AEMIC-REQ-064/066's
own tables); retryability (stated per-exception); disclosure safety (none
of the six exceptions carry any field that could leak into a fabricated
`eligible` outcome); serialization (not applicable — exceptions are not
serialized record types); testability (each independently triggerable per
§22's matrix); mapping from concrete failure to public result (one-to-one,
confirmed); mapping from one failure to multiple public results (none
found — no failure condition maps ambiguously to more than one exception
type).

**One consequence of BF-147F-1 surfaces here, not previously disclosed by
AEMIC-001 itself:** AEMIC-REQ-069's base-class fallback
(`AuthorityEvaluationError`, "reserved for conditions this contract's own
§13.1/§13.2 enumeration did not anticipate") is, as specified, the *only*
exception path available to an `evaluate()` implementation that
faithfully attempts to enforce AEMIC-REQ-022's invariant and discovers it
cannot be satisfied for a well-formed `ELIGIBLE` case (since none of
§13.1's four named exceptions describes "the input was well-formed but
this function structurally cannot produce a valid outcome"). A
specification whose only "well-formed input, but cannot succeed" escape
hatch is an unnamed base-class exception is itself evidence the failure
taxonomy was not designed with BF-147F-1's condition in view — this is not
a new, separate defect, but a corroborating symptom of the same one
(§22).

**Two materially different failures collapsing into the same public
result:** none found — attempted directly (empty `declaration_ref`
production, ambiguous corrupt-vs-unavailable construction) and none
succeeded. **One failure mapping to multiple public results:** none found.
Apart from the BF-147F-1 consequence noted above, **the taxonomy itself is
sound.**

---

## 12. Identity and Versioning Verification

Canonical identity for Decision Template: `(template_ref,
template_version)` (AEMIC-REQ-037); for a Declaration: the same tuple
(AEMIC-REQ-015 — Declaration is keyed by, not merely associated with,
this pair); for a Registry entry: identical, by construction of `resolve`'s
own signature; for a request: the four `evaluate()` parameters
collectively (no separate identity beyond the tuple plus claimed
identity); for an outcome: `template_ref`/`template_version`/
`claimed_identity` verbatim-copied plus `declaration_ref` derived from the
same tuple (AEMIC-REQ-038).

Syntax: non-empty `str` only, no further restriction (AEMIC-REQ-036).
Normalization: **none performed** — exact, case-sensitive `str` equality
required for Registry lookup and set-membership evaluation
(AEMIC-REQ-036, explicit). Adversarial identities attempted against this
rule:

| Adversarial input | AEMIC-001's own disposition | Independent assessment |
|---|---|---|
| Whitespace variants (`"alice"` vs `" alice"`) | Treated as distinct strings; no trimming | **Sound** — matches AEM-REQ-023's own "no format beyond non-emptiness" discipline; a whitespace-padded claimed identity simply fails to match, producing `ineligible`, never a false match |
| Case variants (`"Alice"` vs `"alice"`) | Treated as distinct strings; case-sensitive | **Sound**, with a disclosed operational consequence (not a defect): an authoring workflow must be consistent about case when declaring `eligible_identities`, or genuine identities will spuriously fail to match — this is an authoring-discipline concern outside this package's own boundary (§2.2), not a contract defect |
| Unicode normalization variants (NFC vs NFD of the same visual string) | Not discussed anywhere in AEMIC-001 | **Gap, but Non-Blocking** — exact `str` equality in Python compares code points, not normalized forms; two Unicode-equivalent-but-differently-encoded strings would not match. This is a real, disclosed-nowhere gap, but its failure mode is fail-*closed* (a legitimate identity spuriously reads as `ineligible`, never spuriously `eligible`) — consistent with AEM-REQ-032's fail-closed discipline, so it does not rise to Blocking; recommended as a future amendment (§28) |
| Empty segments | Rejected at construction (`InvalidClaimedIdentityError`/`InvalidTemplateReferenceError`) | **Sound** |
| Path-like values (`"../etc/passwd"` as a `template_ref`) | Not rejected by `evaluate`/`resolve`'s own ABC (only a concrete filesystem Registry's own path-safety layer, AEMIC-REQ-053/057, defends against this) | **Sound, by design** — the ABC layer is storage-agnostic and correctly delegates path safety to the concrete implementation layer that actually touches a filesystem; this is not a gap, it is correct separation of concerns |
| Version aliases (`"1.0"` vs `"1.0.0"`) | No version-parsing/comparison logic exists anywhere — versions are opaque strings, compared only for exact equality | **Sound** — consistent with `template_version`'s own bare-`str` nature in `Session` (confirmed at §4) |
| Leading zeros (`"01"` vs `"1"`) | Same as above — opaque string comparison | **Sound** |
| Unsupported version formats | Not applicable — `template_version` is never parsed as a version number, only compared as a string | **Sound** |

`template_ref + template_version` sufficiency and consistent application:
**confirmed** — every place this contract defines identity (Declaration,
Registry lookup, `declaration_ref`, outcome) uses exactly this pair,
consistently, with no alternate identity path introduced anywhere.

**No Blocking defect found in this section.** One Non-Blocking
observation (Unicode normalization) is newly disclosed at §22.

---

## 13. Serialization and Determinism

Canonical serialization: `to_payload` producing a `dict` suitable for
`json.dumps(..., sort_keys=True)` (AEMIC-REQ-088), mirroring
`FilesystemSessionRepository`'s own proven call pattern exactly. Field
ordering: alphabetical at the `json.dumps` boundary, not insertion order —
a sound, already-precedented approach. Omitted vs. null: none of the ten
total fields across both record types are optional in v1.0
(AEMIC-REQ-091), so "omitted" and "null" carry no distinguishing meaning —
sound, and correctly disclosed as such rather than left ambiguous. Unicode
handling: unrestricted, round-tripped byte-for-byte (AEMIC-REQ-090).
Timestamp handling: `declared_at`/`evaluated_at` are structural-only
ISO-8601 strings, no clock-skew rejection — consistent, disclosed, and
matches `Session`'s own precedent. Stable enum representation:
`EvaluationResult`'s three wire values are fixed literals
(`"eligible"`/`"ineligible"`/`"indeterminate"`), never re-derived.

Digest rules: **explicitly none required** (AEMIC-REQ-092), with reasoning
independently checked and found sound — `AuthorityEvaluationOutcome`'s own
reconstructibility already depends on Registry storage-layer integrity
(a separate concern, §12/§16), and the only currently-authorized downstream
path (a future CHGR integration) would inherit CHGR-001's own digest
discipline, making a second digest here non-additive. **Confirmed:
introducing a digest requirement here would not resolve BF-147F-1** (a
digest over an unconstructable field does not make it constructable), so
this omission is independent of, and unaffected by, the Blocking finding.

Result determinism: can two equivalent declarations or requests serialize
differently? **No** — `to_payload`'s `sort_keys=True` discipline and the
closed field set jointly foreclose this. Can the same Registry state and
request produce different outcomes? **No**, for the `ineligible`/
`indeterminate` cases (fully specified, fully deterministic); **the
question is moot for the `eligible` case**, since no well-formed call
produces a valid `eligible` outcome at all under this contract's own
signature (BF-147F-1) — determinism cannot be assessed for a case the
contract does not actually allow to be constructed via its own sanctioned
path. Undeclared side effects: none found; `evaluate` is required to
perform no I/O, no mutation, no logging of its own (AEMIC-REQ-076).

**No new Blocking defect found in this section beyond BF-147F-1's own
consequence, restated for completeness.**

---

## 14. Persistence Deferral Verification

Can the first implementation be meaningfully implemented and tested with
only an abstract Registry? **Yes for the `indeterminate` and `ineligible`
paths** (an in-memory test double suffices, exactly as AEMIC-REQ-009
requires and as Phase 147D's own test architecture (§11) anticipated).
**No, not fully, for the `eligible` path** — but the reason is BF-147F-1
(the signature cannot produce a valid `eligible` outcome regardless of
which Registry implementation, abstract or concrete, is used), not a
persistence-deferral problem per se. This is an important distinction:
§3.3's deferral of the *concrete Registry* is sound and independently
verified sound in isolation (mirrors `SessionRepository` →
`FilesystemSessionRepository`'s own two-phase precedent, correctly);
**the persistence-deferral architecture itself is not defective — it
merely cannot rescue the `eligible` path, because that path's defect
lives one layer up, in `evaluate()`'s own signature, not in the Registry.**

Is a reference in-memory/test Registry required? Yes, and AEMIC-REQ-009
correctly requires one, defined in `tests/`, never in
`src/pcae/authority_evaluation/` itself. Does the contract accidentally
depend on filesystem behavior before the concrete implementation exists?
**No** — `evaluate()` has zero Registry dependency of any kind
(AEMIC-REQ-073), and the ABC itself is storage-agnostic. Is the deferred
persistence contract (§12) sufficiently precise for a later phase?
**Yes** — AEMIC-REQ-052–063 are concrete, falsifiable, and directly mirror
an already-audited pattern in this codebase (`FilesystemSessionRepository`).
Can implementation and verification proceed without hidden storage
assumptions? **Yes**, for everything except the `eligible` case, which
cannot proceed regardless of storage assumptions (BF-147F-1).

**If the first implementation cannot satisfy its own contract without a
concrete Registry, classify as Blocking** (governing prompt's own
instruction) — independently verified: **the first implementation's
inability to satisfy AEMIC-REQ-022 for the `eligible` case is not caused
by the concrete-Registry deferral** (a concrete Registry would not help;
`evaluate()`'s own signature is the blocker, and `evaluate()` never
touches the Registry at all). This section's own deferral decision is
therefore **not** independently Blocking; BF-147F-1 remains classified
under §7/§19, not duplicated here.

---

## 15. Forbidden Dependency Verification

Confirmed prohibition of imports from `pcae.interactive_workflow`,
`pcae.governance` (including `pcae.governance.publication`),
`pcae.cltr`/`pcae.cltr_prototype`, `pcae.commands`, `pcae.cli`,
`pcae.core`, `pcae.lifecycle`, `pcae.repository_intelligence`
(AEMIC-REQ-010) — this list is **broader** than AEM-001's own
minimum-named set (`interactive_workflow`/`governance.publication`/`cltr`),
correctly extending it to cover every higher-level or governance-machinery
layer AEM-001's own text did not individually enumerate but whose
inclusion is clearly implied by AEM-001 §2.2's "does not modify Runtime,
Permission Broker, or any execution-capability contract" and by this
package's own zero-authority design (§9 above). Allowed low-level
dependencies: standard library plus own sibling modules only
(AEMIC-REQ-011) — confirmed no dependency on `pcae.schema_resources` or
`pcae.schema_runtime` either, correctly reasoned (§9, this package never
loads or validates against the JSON Schema itself). Schema-resource
access: correctly **not** authorized. Runtime access: correctly
prohibited, confirmed by the forbidden-root list's own inclusion of
`pcae.core`/`pcae.lifecycle` (the governance-harness engine itself, a
distinct and more thorough prohibition than any predecessor contract's own
forbidden-import test defines). Policy access: prohibited by the same
mechanism. Command-layer imports: explicitly prohibited (`pcae.commands`,
`pcae.cli`). Circular dependencies: not possible — the dependency
direction is stated as strictly one-way and, at this contract's own
freeze point, zero-way in practice (AEMIC-REQ-013; nothing yet depends on
a package that does not yet exist).

Suitable for AST-enforced testing: **yes** — AEMIC-001's own §22 matrix
(row for AEMIC-REQ-010-014) explicitly requires "AST-style test (mirroring
`_FORBIDDEN_IMPORT_ROOTS`)", and the independent re-inspection at §4
confirms this mirrors an already-working, already-audited test pattern in
this exact codebase (`tests/test_phase_144c_publication_coordinator.py`).
One Non-Blocking observation, already implicitly acknowledged by AEMIC-001
itself (§1.1, "extending that test's root list... is this phase's own
recommended test-architecture addition" — carried from 147D, not
independently re-verified as *mandatory* by AEMIC-001's own requirement
text): the *existing* `_FORBIDDEN_IMPORT_ROOTS` list in
`tests/test_phase_144c_publication_coordinator.py` still does not name
`pcae.authority_evaluation` (confirmed at §4). AEMIC-001's own §22 matrix
requires a *new*, package-scoped test achieving an equivalent guard
("no file outside this package imports from it yet"), which is a
sufficient, if structurally distinct, mitigation — **not a defect**, but
worth flagging precisely so a future implementation phase does not treat
extending the *existing* coordinator test as optional simply because
AEMIC-001 itself does not word it as mandatory.

**No Blocking defect found in this section.**

---

## 16. Compatibility Verification

Confirmed zero required modification to: `Session`,
`PublicationReadinessPackage`, `PublicationCoordinator`, `record.py`,
CHGR schemas, IWC-001, PEC-001 (AEMIC-REQ-083, restating FA-147D-1 as a
binding boundary). Existing Decision Template records: unaffected — no
schema change is authorized (AEMIC-REQ-035), and no existing
`decision_template` document (there are none carrying real content, per
147C/147D's own confirmed absence) requires any change. Existing sessions:
unaffected — `Session.template_ref`/`.template_version` are read, never
written or reshaped, by this package's design (§10 above). Existing
readiness packages: unaffected, same reasoning. Existing CHGR bundles:
unaffected — no writer to CHGR is created (§9 above). Current Publication
Coordinator: unaffected, confirmed by direct re-inspection at §4 (imports
unchanged). Current verification/inspection commands: unaffected — no CLI
surface is defined (AEMIC-REQ-003). Absence of declaration-Registry data:
handled identically to today's absence of any authority mechanism at all
— `indeterminate`, disclosed, never fabricated. Old repositories / packaged
installations: unaffected, since the package does not yet exist and
nothing currently depends on it (AEMIC-REQ-013).

AEMIC-REQ-086 explicitly requires the full existing
`interactive_workflow`/`governance.publication`/CHGR-construction test
suite to continue passing unchanged — independently confirmed via this
phase's own fast_green run (§26: 4391/4391 passed, no regression, since no
source file was touched by this phase in the first place).

**Holds fully. No defect found.**

---

## 17. Deferred Integration Boundary Verification

FA-147D-1 is carried forward as AEMIC-REQ-083–085, an explicit,
enumerated, binding list of what the *first implementation phase this
contract authorizes* does **not** do (widen `Session`/Package; add any
authority field to any IWC-001-owned type; modify PEC-001/coordinator.py/
record.py; populate `authority_basis_claimed`; modify any schema; modify
verification/inspection; gate anything; change Interactive Workflow
behavior or any CLI/transport surface). This is independently confirmed to
match FA-147D-1's own scope exactly, with no silent widening or narrowing.
The proposed 8-step future integration sequence (AEMIC-REQ-084) is
logically viable in outline: it correctly sequences "build the package" →
"verify it" → "govern an IWC-001 amendment" → "verify that" → "build the
wiring" → "govern a PEC-001 amendment" → "build that consumption" →
"end-to-end verify" — no step depends on a later step, and no missing
intermediate contract phase was found (this phase — 147F — is itself
exactly the "verify" step in position 2 of that sequence, applied to the
Implementation Contract rather than a built implementation, appropriately
one layer earlier than AEMIC-REQ-084 step 2 literally describes, since no
implementation yet exists to verify).

**One consequence of BF-147F-1 belongs here as well:** step 1 of
AEMIC-REQ-084's sequence ("Implementation of `pcae.authority_evaluation`
per this contract") cannot itself be completed faithfully as specified,
because the contract it would be implemented "per" cannot be satisfied for
the `eligible` case (§7). This does not invalidate the sequence's own
*ordering logic* (steps 3–8 would still need to follow steps 1–2 in this
order once BF-147F-1 is repaired) — it means step 1, as things stand
today, has no way to succeed without either violating this contract or
silently repairing it during implementation (exactly the outcome a
Contract Freeze phase and this Independent Verification phase both exist
to prevent).

**No further Blocking defect found in this section beyond BF-147F-1's own
consequence, restated for completeness. No downstream amendment was
performed by this phase.**

---

## 18. Security and Adversarial Review

| Attack | Precondition | Contract defense | Normative? | Testable? | Residual limitation |
|---|---|---|---|---|---|
| Declaration spoofing | Attacker controls `claimed_identity` input | Exact closed-set membership only, no wildcard/regex (§4, AEMIC-REQ-006 restated) | Yes | Yes | None beyond disclosed non-goals |
| Decision Template substitution | Attacker supplies a different `template_ref`/`template_version` than the session's own | `resolve`'s exact two-argument match (AEMIC-REQ-042); no partial match | Yes | Yes | None found |
| Declaration substitution | Attacker attempts to have `evaluate` cite a different Declaration than the one actually resolved | `declaration_ref` names exactly the Declaration argument passed in (AEMIC-REQ-038); no second, implicit lookup occurs inside `evaluate` (AEMIC-REQ-073) | Yes | Yes | None found |
| Version substitution | Attacker supplies a stale `template_version` hoping to reach a superseded, more permissive Declaration | Per-version immutability (AEM-REQ-008) plus exact-tuple `resolve` (AEMIC-REQ-046) — a stale version simply resolves its own, distinct, still-immutable Declaration, never a "latest" fallback | Yes | Yes | Authoring-time discipline (retiring a stale version) is outside this package's own boundary — disclosed, not hidden |
| Stale declarations | Same as above | Language-level immutability (AEMIC-REQ-018) | Yes | Yes | AEMIC-REQ-051's own named limitation (authoring-time enforcement, not `resolve`-time) — disclosed |
| Duplicate ambiguity | Storage-layer duplicate for one identity tuple | Fail-closed `AuthorityRegistryCorruptError`, never first-match (AEMIC-REQ-045) | Yes | Yes | None found |
| Replay | Attacker re-submits an already-consumed outcome | `evaluate` is pure/stateless; no session concept exists at this layer to replay against (§15's own table, confirmed) | Yes | Yes | Replay in the Publication-layer sense is PEC-001's own unaffected boundary |
| Registry poisoning | Attacker writes an unauthorized Declaration directly to storage | ABC exposes no write path at all (AEMIC-REQ-042); a concrete implementation's own authoring-time access control is the disclosed, correct enforcement point | Partially — this contract requires the *absence* of a write path on the ABC, but does not itself specify authoring-time access control (correctly deferred, since no authoring workflow exists yet) | Testable for the ABC's own read-only shape; not yet testable for authoring-time access control (deferred) | Disclosed, not hidden |
| Malformed serialization | Attacker (or corruption) produces an unparseable/wrong-schema-version payload | `UnsupportedSchemaVersionError`/`MalformedDeclarationError`, checked before other fields (AEMIC-REQ-093) | Yes | Yes | None found |
| **Authority escalation via fabricated citation** | **An implementer, faced with BF-147F-1, bypasses `evaluate()` and constructs `AuthorityEvaluationOutcome` directly with an arbitrary `citation_text` for the `eligible` case** | **None** — no requirement anywhere forbids direct construction of `AuthorityEvaluationOutcome` outside `evaluate()`, and none binds a directly-constructed instance's `citation_text` to any verified source | **No — this is exactly the gap** | **Not testable as specified, since the contract neither authorizes nor forbids this construction path** | **This is BF-147F-1's own security-layer manifestation — see below** |
| Circular trust | `declared_by` trusted recursively | Recorded for provenance only, never evaluated (AEM-REQ-013) — disclosed, unclosed gap, restating AEM-001 §14 D-7 | Yes (as a disclosed non-closure) | N/A (nothing to test; the gap is the absence of a mechanism) | Disclosed, not hidden |
| Outcome misuse as authorization | Downstream consumer treats `evaluation_result` as dispositive | Naming/documentation requirements (AEMIC-REQ-027) are the mitigation; no enforcement mechanism exists to prevent misuse by a future, out-of-scope caller | Yes, at the naming level | Partially (auditable via docstring/naming review, not runtime-enforceable) | Disclosed, matches AEM-001's own §16 judgment-call reasoning |
| Hidden runtime coupling | Any import path reaching Runtime/Permission Broker | Zero — `pcae.core`/`pcae.lifecycle` explicitly forbidden (§15 above) | Yes | Yes | None found |
| Provenance fabrication | Attacker fabricates `declared_by`/`evaluator_version` | Recorded, not verified — same disclosed gap as circular trust (`declared_by`); `evaluator_version` is descriptive metadata, not itself evaluated (AEMIC-REQ-040, explicit) | Yes, as a disclosed non-closure | N/A | Disclosed, not hidden |

**The "authority escalation via fabricated citation" row is the direct
security-layer consequence of BF-147F-1**, and is the strongest single
piece of evidence that BF-147F-1 must be classified Blocking rather than
merely a documentation gap: AEMIC-REQ-022's own stated purpose for
enforcing the citation invariant "at construction time" is explicitly "not
left to caller discipline" — i.e., the whole point of the invariant is to
prevent an arbitrary caller from fabricating a citation. But because
`evaluate()` cannot legitimately produce an `eligible` outcome at all, any
real implementation attempting to make the `eligible` path reachable must
either (a) violate the closed-parameter contract by adding an undocumented
fifth parameter (itself a contract violation a future verifier would need
to catch), or (b) construct `AuthorityEvaluationOutcome` directly,
bypassing `evaluate()`'s "not left to caller discretion" guarantee
entirely and reintroducing caller-controlled citation content with **no**
contractual constraint on where that content came from. Option (b) is the
practically inevitable outcome, and it defeats the exact security property
AEMIC-REQ-022 was written to establish.

---

## 19. Implementability Assessment

Public API completeness: **not complete** — `evaluate()`'s public
signature cannot produce a valid `eligible`-result instance (§7).
Module ownership: complete and correctly bounded (§3 above). Dependency
clarity: complete (§15 above). Model completeness: complete for
`EligibleAuthorityDeclaration`; **incomplete** for
`AuthorityEvaluationOutcome` in the sense that its own construction-time
invariant (§6.1) has no satisfying construction path via the function
that is supposed to be its sole producer. Evaluator determinism: sound
for `ineligible`/`indeterminate`; **not assessable** for `eligible`, since
no well-formed call produces it. Registry semantics: complete (§9/§10
above). Error mapping: complete (§11 above), modulo the corroborating
symptom noted there. Serialization: complete (§13 above). Security:
one Blocking gap identified (§18). Test strategy: complete for every
requirement except the `eligible`-outcome construction path, which §22's
own matrix (row for AEMIC-REQ-021-023) can only test by direct model
construction — itself indirect evidence the intended production path
(`evaluate()`) does not, and cannot, produce this case. Packaging:
complete (§3 above). Independent verification feasibility: this very
phase demonstrates it — falsification of a specific, load-bearing claim
was possible using only this contract's own text plus direct primary-source
comparison, exactly as the contract's own §20 (Contract Quality Review)
claims should be possible for a well-formed contract.

**Identify all choices still left to an implementer, classified per the
governing prompt's own taxonomy:**

| Choice | Classification |
|---|---|
| Exact internal structure of `models.py` submodules (single file vs. split) | Harmless local implementation freedom (AEMIC-REQ-007 explicitly permits this) |
| Exact three-vs-one exception subclass shape beyond the four/two named | Harmless local implementation freedom, within the named minimum |
| Whether to add a store-level `STORE_SCHEMA_VERSION` for a future concrete Registry | Permitted extension point (AEMIC-REQ-063, explicit) |
| Whether a future revision adds an `expires_at` field | Permitted extension point (AEM-REQ-042, restated) |
| **How `evaluate()` obtains `citation_text` for the `eligible` case** | **Implementation-critical ambiguity — in fact, an impossibility under the frozen signature, not merely an ambiguity (§7)** |
| Whether an implementer adds an undocumented fifth parameter, or bypasses `evaluate()` entirely, to work around the above | Implementation-critical ambiguity (a direct consequence of the item above — this is the same defect, not a second one) |
| Which concrete filesystem layout detail (e.g. exact filename-derivation function) a future Registry implementation uses | Deferred integration choice (§12, explicitly named as such and pre-frozen in outline) |

**Any implementation-critical ambiguity is Blocking** (governing prompt's
own instruction). **Confirmed: one such ambiguity exists (BF-147F-1), and
it is Blocking.**

---

## 20. Testability Assessment

Independent test inventory, derived before comparing against AEMIC-001's
own §22 matrix: model construction (both types, all structural
invariants); the citation invariant specifically (§6.1); identity
normalization (exact-equality, no normalization, adversarial inputs per
§12 above); unsupported versions (`schema_version` mismatch); declaration
absence (`indeterminate`); duplicate declarations
(`AuthorityRegistryCorruptError`); conflicting declarations (same);
Registry unavailable; Registry corruption; malformed declaration
(structural, at construction); deterministic evaluation (repeated calls,
identical results); stable serialization (round-trip, non-ASCII); forbidden
imports (AST-style); no side effects (mutation/I/O assertions); disclosure-
only semantics (naming/docstring audit); no publication integration ("not
wired in yet" regression guard); no runtime change (`pcae runtime inspect`
before/after a future implementation phase).

Comparing against AEMIC-001's own §22 matrix: **every item in this
independent inventory has a corresponding row.** No uncovered requirement
was found. One test that **cannot be implemented as specified**: a
positive test constructing a valid `eligible` `AuthorityEvaluationOutcome`
*via a call to `evaluate()`* — because no such well-formed call exists
(§7). AEMIC-001's own matrix row for `AEMIC-REQ-072-077` (`evaluate`
purity/totality/determinism) requires "Table test over
`(claimed_identity, declaration)` → expected outcome for all three
results" — **this table test cannot be completed for the `eligible`
row**, since there is no set of well-formed inputs producing a valid
`eligible` outcome via `evaluate()` itself. This is the same defect
surfacing a third time, at the test-matrix level, precisely where the
governing prompt's own §20 instructs looking for "tests that cannot be
implemented."

Requirements without negative tests: none found beyond the above.
Security requirements without adversarial tests: the "authority escalation
via fabricated citation" row (§18) has **no** adversarial test defined
anywhere in AEMIC-001's own matrix, because the contract does not
recognize this as a live risk (it believes AEMIC-REQ-022's invariant fully
forecloses caller-supplied citation fabrication) — this is itself a test-
coverage gap directly caused by BF-147F-1, not a separate one. Deferred
requirements presented as implemented behavior: none found — every
deferred item (concrete Registry, integration boundary) is explicitly and
correctly labeled deferred, not silently presented as done.

---

## 21. Finding Reassessment

Each inherited finding is independently re-derived from primary sources,
not accepted merely because AEMIC-001 claims a disposition.

**F-147C-1** (dormant `eligible_authority` schema field, overbroad
absence claim in AEM-001). Independently re-confirmed present and
unconsumed by any code (§4 above). AEMIC-001's own disposition (§9,
"Reconciled at the implementation level") is **independently verified
correct as far as it goes** — the field is correctly assigned the
sole-citation-source role, with no schema modification and no
duplication of citation *text*. **However**, this phase's own finding
(BF-147F-1) reveals that "reconciled" was premature: the reconciliation
correctly identifies *where* citation text comes from (the schema field)
but does not correctly specify *how* it reaches the outcome object
(§7). F-147C-1 is therefore **not fully closed** — it is closed at the
textual-source level and reopened at the plumbing level by BF-147F-1.

**F-147C-2** (IWC-001 §6/§11 citation-precision cosmetic defect).
Independently re-confirmed via direct section-header inspection of
`INTERACTIVE_WORKFLOW_CONTRACT.md`: §6 is "Human Responsibility Contract",
§11 is "State Contract" (§2 above) — unchanged since 147C/147D. AEMIC-001's
own disposition ("unaffected by this contract; remains open... outside
this contract's own No-Go Boundary") is **independently confirmed
correct** — this is genuinely an AEM-001-identity-block defect, not an
AEMIC-001 concern, and this phase does not attempt to repair it (§23).

**FA-147D-1** (downstream IWC-001/PEC-001 revisions required to reach a
published CHGR). Independently re-confirmed as a real, disclosed,
unclosed dependency (§17 above) — AEMIC-001's disposition ("carried
forward as an explicit, binding deferred-integration boundary, not
resolved") is **independently confirmed correct**.

**FA-147D-2** (Registry-unavailability failure mode). Independently
re-verified fully closed via direct textual attack (§10 above) —
AEMIC-001's disposition ("Closed architecturally through a typed,
fail-closed contract") is **independently confirmed correct**.

**FA-147D-3** (citation/declaration drift risk between free-text
`eligible_authority` and `eligible_identities`). Independently
re-confirmed as a real, disclosed, non-mechanically-closed limitation
(§7/§12 above, AEMIC-REQ-034) — AEMIC-001's disposition ("Retained as a
named limitation with explicit, testable behavior") is **independently
confirmed correct as a characterization of what AEMIC-001 chose not to
build**, though this phase notes FA-147D-3 and BF-147F-1 are adjacent but
distinct: FA-147D-3 concerns whether the *text* and the *set* agree with
each other; BF-147F-1 concerns whether the *text* can reach the outcome
object at all. Repairing BF-147F-1 does not automatically repair
FA-147D-3, and vice versa.

**No finding above is marked resolved without an independently-verified
reason**, restating the governing prompt's own instruction and confirming
AEMIC-001's own §23 disposition register is accurate for four of its five
entries, with F-147C-1's "reconciled" characterization now qualified by
BF-147F-1 (§22).

---

## 22. New Findings

| # | Finding | Classification |
|---|---|---|
| **BF-147F-1** | `evaluate()`'s closed, four-parameter signature (AEMIC-REQ-019/020/072) provides no channel for `citation_text`, and no field of `EligibleAuthorityDeclaration` (closed to six fields, AEMIC-REQ-015/016) carries it either — yet AEMIC-REQ-022 requires every `eligible`-result `AuthorityEvaluationOutcome` to carry a non-`None` `citation_text`, enforced "at construction time, not left to caller discipline," and `evaluate()` (§14) is the contract's sole specified construction path for outcomes produced "at evaluation time" (AEMIC-REQ-031). No well-formed call to `evaluate()` can satisfy both AEMIC-REQ-020 (closed parameter list) and AEMIC-REQ-022 (the citation invariant) simultaneously for the `eligible` case. AEMIC-REQ-031's own text is internally self-contradictory, asserting in one clause that "Declarations SHALL copy the citation text... into the constructed `AuthorityEvaluationOutcome.citation_text` at evaluation time" while confirming, in the next clause, that no field or parameter exists to carry it. The practical consequence (§18) is that any real implementation must either violate the closed-signature rule or construct `AuthorityEvaluationOutcome` directly, bypassing `evaluate()`'s citation-invariant enforcement entirely and reopening exactly the caller-controlled-citation-fabrication risk that enforcement exists to prevent. | **Blocking** — contract contradiction; impossible implementation (for the `eligible` path); untested security requirement (§18); unresolved implementation-critical decision (§19) |
| F-147F-2 | Exact `str`-equality identity/version matching (AEMIC-REQ-036) performs no Unicode normalization, so NFC/NFD-equivalent identity strings would not match. Fails closed (a legitimate identity spuriously reads `ineligible`, never spuriously `eligible`), so this does not rise to Blocking, but is newly disclosed here (§12) since AEMIC-001's own text does not name it. | Non-Blocking, newly disclosed Observation |
| F-147F-3 | `tests/test_phase_144c_publication_coordinator.py`'s existing `_FORBIDDEN_IMPORT_ROOTS` list does not yet name `pcae.authority_evaluation`; AEMIC-001's own §22 matrix requires an equivalent, package-scoped guard rather than mandating an update to this specific existing test. Sufficient in effect, but worth naming explicitly (§15) so a future implementation phase does not treat extending the coordinator's own test as merely optional. | Non-Blocking, Observation |

No finding above collapses two materially different concerns into one, and
BF-147F-1 is not a restatement of any of F-147C-1/F-147C-2/FA-147D-1/
FA-147D-2/FA-147D-3 — it is a distinct defect discovered by this phase's
own independent attack on the citation-source reconciliation (§7),
adjacent to but not identical with FA-147D-3 (§21).

---

## 23. No-Go Confirmation

This phase did not modify production code, tests, schemas, or any existing
contract. `git status --short` immediately before this report was written
showed a clean tree; the only file this phase creates is this report,
plus ordinary governance bookkeeping (task/phase lifecycle files,
`PROJECT_STATUS.md`, `.pcae/phase-completion-*`) at phase close. No
`pcae.authority_evaluation` package, no `EligibleAuthorityDeclaration`,
`AuthorityEvaluationOutcome`, or Registry implementation was created. No
schema file was modified. AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001,
CHGR-001, TAMC-001, TAMPC-001, and GAC-001 all remain byte-for-byte
unmodified. No verification-only test was added — direct source and
contract textual analysis was sufficient to falsify the load-bearing claim
this phase identifies (BF-147F-1), consistent with the governing prompt's
own §23 allowance ("Documentation-only verification is acceptable when
direct source and contract analysis is sufficient").

---

## 24. Overall Verdict

**NOT VERIFIED.**

One Blocking finding (BF-147F-1) was identified and confirmed by direct
textual attack: AEMIC-001's own `evaluate()` signature (§5, §14) cannot
satisfy its own `citation_text` if-and-only-if invariant (§6.1) for the
`eligible` case, and AEMIC-REQ-031's own text is internally
self-contradictory on this exact point. This is not a disclosed,
reasoned, safely-contained limitation of the kind AEMIC-REQ-032/034
correctly model elsewhere — it is a genuine contract contradiction that
makes the `eligible` outcome unconstructable via the contract's own sole
sanctioned path, and whose most likely practical resolution (direct,
caller-side construction of `AuthorityEvaluationOutcome`, bypassing
`evaluate()`) reopens a caller-controlled-citation-fabrication risk the
contract's own invariant exists to foreclose.

Every other independently-checked property holds: the independent
reconstruction materially agrees with AEMIC-001 outside this one defect;
Registry semantics are unambiguous and fail-closed; Registry-unavailability
behavior is fully closed (FA-147D-2); the disclosure-only boundary is
enforceable by naming and semantics; persistence deferral is coherent and
does not itself cause BF-147F-1; compatibility is fully preserved; the
downstream-integration deferral is explicit and complete; and the test
strategy is otherwise complete and falsifiable. Per the governing prompt's
own verification criteria, Verification requires "no Blocking
contradiction" and "complete and deterministic public types" — both fail
specifically and only because of BF-147F-1. Repairing BF-147F-1 (most
directly, by adding a `citation_text: str` parameter to `evaluate()`, or
by adding an optional `citation_text` field to `EligibleAuthorityDeclaration`
that `evaluate()` may read, together with a corresponding correction to
AEMIC-REQ-019/020/031) would very likely restore VERIFIED WITH
NON-BLOCKING FINDINGS status on a subsequent verification pass, since no
other structural defect was found — but that repair is this contract's
own affair, not this phase's (§25, no-go boundary; repair is explicitly
not authorized here).

---

## 25. Recommended Next Phase

Per the governing prompt's own instruction ("If Blocking findings are
found, recommend instead: 147E.1"):

**147E.1 — Authority Evaluation Model Implementation Contract Repair.**

Scope recommendation (non-binding, for that future phase's own
consideration): resolve BF-147F-1 by giving `evaluate()` (or an
equivalent construction path) an actual, contractually-sanctioned channel
for `citation_text` — either as a fifth parameter to `evaluate()` (with a
corresponding correction to AEMIC-REQ-019/020's closed-parameter rule), or
as a new, additive, optional field on `EligibleAuthorityDeclaration` that
`evaluate()` reads (with a corresponding correction to AEMIC-REQ-015/016's
closed six-field shape) — either resolution should also directly address
AEMIC-REQ-031's own self-contradictory text and add the missing
adversarial test named at §18/§20 (caller-controlled citation fabrication
via direct `AuthorityEvaluationOutcome` construction bypassing
`evaluate()`). This recommendation is scoping guidance only, not a
pre-authorization of any specific repair approach — that choice belongs to
the repair phase itself.

This recommendation is **not an authorization.**

Separately and not folded into Chapter 147: a standalone Phase 107A
execution-capability gap re-derivation, roadmap-tracking reconciliation,
and GLP-PILOT-C6 Stage 3 resumption all remain open, disclosed, and
unscheduled — unaffected by this phase.

---

## 26. Governance Verification

Commands run at phase start and reconfirmed at phase close:

- `git status --short` / `git branch --show-current` / `git rev-list
  --count origin/main..HEAD` / `git rev-list --count HEAD..origin/main` —
  clean, `main`, `0`/`0`.
- `pcae session bootstrap --agent-id claude-local --sync-lock` — lock
  rehydrated, health healthy, check passed, active task the idle
  placeholder, no recommended-phase mismatch beyond the expected
  "awaiting next governed phase" state.
- `pcae check` — passed.
- `pcae health` — healthy; required PCAE files all present; policy
  validation valid; agent lock held by `claude-local`; session continuity
  verified; git status clean.
- `pcae doctor task-memory` — clean, no inconsistencies detected.
- `pcae runtime inspect` — Runtime status `not_implemented`, Runtime state
  `Observed`, Execution capability `unavailable`, Maximum plugin
  capability `observe`, Registry status `empty`, Plugin count `0` —
  identical before and after this phase.
- `pcae push check` — clean (`nothing_to_push`) at phase start; branch
  `main`, working tree clean, health healthy, check passed, task memory
  clean.
- `python -m pytest -m fast_green -n auto -q` — **4391 passed**, 0 failed,
  105 warnings (pre-existing, unrelated dataclass-collection warnings), in
  103.37s. No regression, consistent with this phase touching no source
  file.

No policy file (`.pcae/policy.toml`) was touched. No strategic-lineage
file (`.pcae/strategic-lineage.json`) was touched. Runtime remained
`Observed`/`observe`/`unavailable` throughout. Plugin Registry remained
empty; plugin count remained zero.

---

## 27. Requirement-Verification Matrix

| AEMIC-001 area | Primary-source basis | Verification result | Finding | Future test method |
|---|---|---|---|---|
| §1 Purpose / 147D-choice classification | AEM-001 §0/§4.6/§12.1; Phase 147D §1.1 (evidence only) | Supported | — | N/A (scoping) |
| §3.1–3.2 Package boundary, required modules | AEM-001 §0; Phase 147D §6 (evidence only) | Supported | — | AST-style package-location test |
| §3.3 Concrete Registry deferral | AEM-001 §4.6; `SessionRepository`/`FilesystemSessionRepository` precedent (143K/145D) | Supported | — | N/A (deferred-scope confirmation) |
| §3.4–3.6 Forbidden imports, dependency direction, re-export stability | AEM-REQ-028; PEC-REQ-113; direct re-inspection of `coordinator.py`/`_FORBIDDEN_IMPORT_ROOTS` | Supported | F-147F-3 (Non-Blocking) | AST-style forbidden-import test, package-scoped |
| §4 `EligibleAuthorityDeclaration` | AEM-REQ-006/007/008 | Supported | — | Construction/validation unit tests |
| §5 Evaluation inputs | AEM-REQ-014/015/017/018 | **Contradicted** | **BF-147F-1 (Blocking)** | Cannot be positively tested for the `eligible` case as specified |
| §6 `AuthorityEvaluationOutcome` / §6.1 invariant | AEM-REQ-018 | **Contradicted** (invariant unsatisfiable via sole construction path) | **BF-147F-1 (Blocking)** | Same as above |
| §7 `EvaluationResult` enum | AEM-REQ-020/021 | Supported | — | Enum construction/comparison tests |
| §8 Disclosure-only semantics | AEM-REQ-003/037/038/039/040 | Supported | — | Docstring/naming audit |
| §9 Citation reconciliation | AEM-REQ-026/027; Phase 147D §4 (evidence only); F-147C-1 | **Contradicted** (self-contradictory requirement text) | **BF-147F-1 (Blocking)** | N/A until repaired |
| §10 Identity/versioning | AEM-001 §5.5; AEM-REQ-023 | Supported | F-147F-2 (Non-Blocking) | Adversarial-identity unit tests, incl. Unicode-normalization case |
| §11 Registry abstraction | AEM-REQ-010/011/012 | Supported | — | In-memory test-double unit tests |
| §12 Filesystem persistence (deferred) | Phase 147D §6.4 (evidence only); `FilesystemSessionRepository` precedent | Supported | — | Atomic-write/path-safety/restart-equivalence tests (future phase) |
| §13 Failure taxonomy | AEM-REQ-023/024/025 | Supported, with corroborating symptom | BF-147F-1 (corroborating, not separate) | Per-exception fixture tests |
| §14 Evaluation function contract | AEM-REQ-009/012/016 | **Contradicted** | **BF-147F-1 (Blocking)** | Table test incomplete for `eligible` row |
| §15 Security contract | AEM-001 §9 | Supported, with one new adversarial gap | BF-147F-1 (security manifestation, §18) | Adversarial direct-construction test (new, not yet defined) |
| §16 Auditability | AEM-REQ-030/031 | Supported, contingent | BF-147F-1 (contingent) | Reconstructibility test (post-repair) |
| §17 Deferred integration boundary | Phase 147D §7 (evidence only), FA-147D-1 | Supported | — | `git diff` scope-check (future phase) |
| §18 Serialization/digest | Phase 147D §6.6 (evidence only) | Supported | — | Round-trip serialization tests |
| §19 No-go boundary | AEM-001 §15 | Supported | — | `git status --short` before/after |
| §20 Contract quality self-review | N/A (self-referential) | **Contradicted** (self-certification falsified by BF-147F-1) | **BF-147F-1 (Blocking)** | N/A |
| §21 Amendment contract | AEM-001 §13 | Supported | — | N/A |
| §22 Requirement/Test Matrix | N/A (self-referential) | Supported in form; one row incomplete | BF-147F-1 | See §20 above |
| §23 Finding disposition | Phase 147C, Phase 147D | Supported for 4/5 entries; F-147C-1 qualified | BF-147F-1 (qualifies F-147C-1) | N/A |
| §24 Non-goals | AEM-001 §15 | Supported | — | N/A |

---

**End of Phase 147F independent verification report.**
