# AEM-001 v1.0 — Authority Evaluation Model Contract

## Contract identity and status

**Contract:** AEM-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 147B — Authority Evaluation Model Contract Freeze
**Architecture basis:** Phase 147A — Next Strategic Capability Architecture
Reassessment
(`docs/PHASE_147A_NEXT_STRATEGIC_CAPABILITY_ARCHITECTURE_REASSESSMENT.md`),
GLP-001 §6.1 Stage 2 (Contract Freeze), applied here exactly as Phase 143B
converted Phase 143A into CHGR-001, Phase 144B converted Phase 144A into
PEC-001, and Phase 145B converted Phase 145A into IWPC-001.
**Governed subject:** The **authority-evaluation layer** referenced,
reserved for, and explicitly deferred by three independent chapters —
IWC-001 (`§6`, `§11 Human Responsibility Contract`), IWPC-001 (`§4.1
Authority Neutrality`, `§18 Authorization Input Contract`, `§29 C-1`, `§31`),
and CHGR-001 (`§11 Authority Contract`, `§20 Governance Responsibility
Contract`, `CHGR-REQ-096/097/199`, `PEC-REQ-115`) — under the informal name
**C-1, the authority-evaluation gap**. AEM-001 is a new companion contract,
sitting alongside IWC-001/IWPC-001/CHGR-001/PEC-001 exactly as IWPC-001 was
introduced alongside IWC-001 rather than amending it (Phase 145A §6,
ratified by 145B). AEM-001 defines: the `eligible_authority` declaration
model for Decision Templates; the deterministic evaluation function that
consumes a claimed identity and an `eligible_authority` declaration and
produces a disclosed, non-fabricated `AuthorityEvaluationOutcome`; and how
that outcome populates CHGR-001's already-reserved `authority_basis_claimed`
field, per PEC-REQ-115's existing "MAY construct... never from an
independent judgment of whether the claim is actually valid" discipline.

AEM-001 is the sole normative authority governing **authority evaluation**
as newly defined here. It does not govern Interactive Decision Session
semantics (IWC-001, unmodified), does not govern the CLI/transport
invocation layer (IWPC-001, unmodified), does not govern Publication
Execution (PEC-001, unmodified), does not govern the Canonical Human
Governance Record artifact class or schema (CHGR-001, unmodified), does not
redefine the Typed Authority Model Consumption or Production Consumption
Contracts (TAMC-001, TAMPC-001 — a distinct, unrelated authority concept,
§9 below), does not redefine GAC-001 or GLP-001 (a distinct,
governance-process-level authority question, §10 below), and does not
modify Runtime, Permission Broker, or any execution-capability contract.
Where this contract cites IWC-001, IWPC-001, PEC-001, or CHGR-001, the
citation illustrates an obligation this contract imposes on the
authority-evaluation layer specifically; it does not redefine the
underlying provision — mirrors IWPC-001 §1's and PEC-001 §1's identical
illustrative-citation discipline.

Phase 147A's Architecture stage is the approved design basis for every
section below. This contract independently re-derives every requirement
directly from Phase 147A's own text (treated as evidence of architectural
intent, never as contractual authority), from IWC-001's own frozen text
(cited `IWC-REQ-###`), from IWPC-001's own frozen text (cited
`IWPC-REQ-###`), from PEC-001's own frozen text (cited `PEC-REQ-###`), from
CHGR-001's own frozen text (cited `CHGR-REQ-###`), and from direct
re-reading of `src/pcae/interactive_workflow/models/session.py`,
`src/pcae/interactive_workflow/publication_handoff/handoff.py`, and
`src/pcae/governance/publication/**` — confirming, by direct source
inspection, that no `eligible_authority`, `DecisionTemplate`, or authority
evaluation mechanism of any kind exists anywhere in this repository today;
`template_ref` is the only Decision-Template-adjacent artifact that exists
in code, and it is a bare, unresolved, opaque `str` field
(`Session.template_ref`, `session.py:87`).

**Compatibility policy:** AEM-001 fills exactly the invocation-surface gap
IWPC-001 §29/§31 and CHGR-001 §11/§20.5 both named and declined to fill.
It narrows nothing in IWC-001, IWPC-001, CHGR-001, or PEC-001; it defines a
new, additive layer those contracts already reserve room for
(`authority_basis_claimed`, PEC-REQ-115's citation rule, CHGR-001 §11's
"eligible-authority rule the record's own Decision Template names"). Any
future implementation phase MUST conform to AEM-001 as written; AEM-001
itself MAY be revised only through a governed superseding contract revision
(§13 below), never through an implementing phase's own discretion.

**Requirement numbering convention:** Requirements are identified
`AEM-REQ-001` through the final requirement in this document, sequential,
with no gaps and no reuse, grouped by the section that introduces them.
Once frozen, no requirement identifier is renumbered, reassigned, or
reused, mirroring IWC-001's, PEC-001's, and IWPC-001's own amendment
discipline (§13 below).

**Runtime:** State: Observed / Maximum Capability: observe / Execution
Availability: unavailable — unaffected by this contract; nothing this
contract defines is implemented by this phase, and nothing it defines
touches `src/pcae/runtime/**`.

---

## 1. Purpose

AEM-001 freezes the stable, closed-form definition of authority evaluation
for Decision Templates: what an `eligible_authority` declaration is, how a
claimed identity is evaluated against one, what outcome that evaluation
produces, how that outcome may (and may not) be used downstream, and what
remains permanently outside this contract's scope. It exists so that a
later, separately-authorized implementation phase can build against an
unambiguous, falsifiable contract rather than reinterpreting Phase 147A's
architectural prose or CHGR-001/IWPC-001's own disclosed deferrals.

This is a Contract Freeze phase. **No implementation is authorized by this
document.** No `eligible_authority` declaration, evaluation function, or
registry exists in `src/pcae/**` after this phase; none is created by it.

## 2. Scope and No-Go Boundary

### 2.1 In scope

**AEM-REQ-001.** This contract MAY define behavior for: the
`eligible_authority` declaration's data shape; the identity/authority-basis
inputs an evaluation function consumes; the evaluation function's
determinism, purity, and output contract; the closed set of evaluation
outcomes, including "no declaration exists"; the failure model for
malformed or missing inputs; how an evaluation outcome populates
CHGR-001's `authority_basis_claimed` field; the auditability and
provenance obligations of a performed evaluation; and the boundary between
this contract and IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001/
TAMPC-001, and GAC-001.

### 2.2 Out of scope

**AEM-REQ-002.** This contract SHALL NOT govern: Decision Template
authoring, storage, or versioning workflow beyond the minimal shape needed
to reference an `eligible_authority` declaration deterministically (§4);
CLI/transport surface for any new command (IWPC-001's exclusive territory,
untouched — see §11.2); Interactive Decision Session semantics, state
transitions, evidence, clarification, preview, or confirmation (IWC-001's
exclusive territory, untouched); Publication authorization, execution, or
CHGR construction (PEC-001's/CHGR-001's exclusive territory — this
contract supplies an input value, never a new writer); Runtime, Permission
Broker, or any execution-capability behavior; the CLTR authority-epoch/
authority-state model governed by TAMC-001/TAMPC-001 (a distinct concept,
§9); or GAC-001 §9's Stage 6 governance-adoption decision (a distinct
concept, §10).

**AEM-REQ-003.** This contract SHALL NOT introduce, and no declaration,
function, or outcome it defines MAY constitute, an **enforcement**
mechanism. Authority evaluation under this contract is evaluate-and-disclose
only: it MAY NOT block, gate, suppress, delay, or otherwise condition
Confirmation, Readiness construction, Authorization, or Publication on its
outcome. This restates and extends IWPC-REQ-002/003's prohibition on this
contract family inventing an authority-evaluation *policy*, one layer
later, and is the single most important boundary this contract draws (see
§6.2's judgment call for the reasoning).

**AEM-REQ-004.** This contract SHALL NOT define an open-ended authority
*policy language*. The `eligible_authority` declaration shape frozen at §4
is a closed-form, non-Turing-complete, set-membership construct only; no
expression language, external policy engine, or conditional/boolean
rule-composition syntax is authorized by this contract (§4.4's judgment
call).

## 3. Normative Terminology

Terms below are normative wherever they appear in this contract in Title
Case or fixed-width form. Where a term is already defined by IWC-001,
IWPC-001, PEC-001, or CHGR-001, this contract adopts that definition
unchanged and does not restate a synonym.

**AEM-REQ-005.** The following terms SHALL carry exactly the meaning given
here:

- **Eligible authority.** CHGR-001 §11's own phrase, "the eligible-authority
  rule the record's own Decision Template names" — adopted unchanged as the
  concept this contract gives a concrete, frozen shape to for the first
  time (§4).
- **Eligible Authority Declaration.** A new, immutable record this contract
  defines (§4), binding a `(template_ref, template_version)` pair to a
  closed set of eligible claimed-identity values for the decision-maker
  role.
- **Claimed identity.** An already-collected, already-existing value: the
  decision maker's `--owner-id` (IWC-001's session-owner concept, IWPC-001
  §3), transported unchanged. This contract introduces no new identity
  input, collection mechanism, or CLI flag (§5).
- **Authority evaluation.** The deterministic, pure function this contract
  defines (§5): given a claimed identity and an Eligible Authority
  Declaration (or its absence), produces exactly one
  `AuthorityEvaluationOutcome`.
- **AuthorityEvaluationOutcome.** The immutable, closed-shape record this
  contract defines (§5.3) as authority evaluation's sole output.
- **Evaluation result.** The closed three-value enumeration this contract
  defines (§5.4): `eligible`, `ineligible`, `indeterminate`.
- **Authority-basis citation.** The verbatim text an `eligible` evaluation
  outcome contributes toward CHGR-001's `authority_basis_claimed` field,
  per PEC-REQ-115's existing "MAY construct... solely from that
  already-verbatim citation" rule (§7).
- **Decision Template Authority Registry.** The as-yet-unbuilt lookup
  surface a future implementation phase would use to resolve
  `(template_ref, template_version)` to an Eligible Authority Declaration,
  if one exists. This contract freezes the Registry's **lookup contract**
  (§4.5) only; it does not freeze storage location, file format, or
  authoring workflow (§4.6's judgment call — distinguished explicitly from
  IWPC-001 §13's `SessionRepository`, which had a pre-existing ABC to
  extend; no such pre-existing artifact exists here).
- **Runtime/Permission Broker authority.** Not a concept this contract
  defines, touches, or overlaps; see §2.2, §8.
- **CLTR authority (authority_epoch / authority_state).** TAMC-001's own,
  entirely distinct concept — lifecycle-transition authority for the
  canonical lifecycle transition record cutover, unrelated to a human
  decision-maker's eligibility to select a Decision Template option; see
  §9.
- **Governance-adoption authority (GAC-001 §9).** GAC-001's own, entirely
  distinct concept — a Stage-6 decision about whether GLP-001 itself is
  more broadly adopted, unrelated to a per-decision authority evaluation;
  see §10.

## 4. The Eligible Authority Declaration

### 4.1 Answering Required Architectural Question 1 (What constitutes an eligible authority?)

**AEM-REQ-006.** An eligible authority, for the purposes of this contract,
is a **closed, enumerated set of claimed-identity values** that a Decision
Template's author has declared, for a specific `(template_ref,
template_version)` pair, as permitted to perform decision selection
(IWC-REQ-018) for sessions bound to that template and version. It is
**not** a role, a permission grant, a capability, or a policy predicate —
it is the narrowest possible construct that satisfies CHGR-001 §11's
existing text ("the eligible-authority rule the record's own Decision
Template names") without inventing anything beyond a named set membership
check.

**AEM-REQ-007.** An Eligible Authority Declaration SHALL carry exactly:

```
EligibleAuthorityDeclaration:
  template_ref: str            # matches Session.template_ref verbatim
  template_version: str        # matches IWPC-REQ-192's --template-version
  eligible_identities: frozenset[str]   # closed, non-empty set of
                                         # claimed-identity values
                                         # (matches --owner-id's shape)
  declared_at: str (ISO-8601 UTC)
  declared_by: str             # the Decision Template author's own
                                # claimed identity; not itself evaluated
                                # by this contract (§4.7)
  schema_version: "aem-declaration/1.0"
```

No other field is defined for v1.0. In particular, no `role`, `scope`,
`expires_at`, `conditions`, or `exceptions` field is defined (§4.4's
non-policy-language judgment call).

### 4.2 Answering Required Architectural Question 2 (Can eligibility change over time?)

**AEM-REQ-008.** Yes, but only by declaring a **new**
`(template_ref, template_version)` pair with a new Eligible Authority
Declaration. An existing Declaration, once it has been evaluated against
by at least one `AuthorityEvaluationOutcome` (§5), is immutable — it SHALL
NOT be edited, appended to, or have identities added/removed in place.
This mirrors IWC-001's own template-version-pinning discipline
(IWPC-REQ-192's `--template-version` already exists specifically to freeze
"the Decision Template version the presented options were drawn from" at
the moment of a decision) and CHGR-001 §13.3's substantive-field
immutability discipline, applied here one layer earlier. A Decision
Template's authority eligibility at version N is fixed forever once version
N has been evaluated against; changing eligibility requires authoring
version N+1.

### 4.3 Answering Required Architectural Question 3 (Must eligibility be deterministic?)

**AEM-REQ-009.** Yes, unconditionally. Given an identical
`(template_ref, template_version, claimed_identity)` triple, evaluation
(§5) SHALL always produce the identical `AuthorityEvaluationOutcome`. This
restates PEC-REQ-057's and PEC-REQ-115's existing "no discretionary step"
discipline, applied to a new function this contract defines, and is
required for the Registry lookup (§4.5) and evaluation function (§5) to
qualify as pure functions — a precondition for §5's audit/replay
guarantees.

### 4.4 Judgment call: closed set-membership only, no policy language

Phase 147A §8 named "scope creep from evaluation into enforcement" as the
highest-discipline risk in this chapter, and IWPC-REQ-002/003 forbid this
contract family from inventing an authority-evaluation *policy*. This
contract resolves the resulting design question — how expressive should
`eligible_authority` be? — in favor of the narrowest possible shape: a
closed set of literal claimed-identity strings, with no boolean
combinators, no role indirection, no time-bounding, and no exception
mechanism. A richer shape (roles, scopes, time-bounded grants) would
begin to resemble a policy engine, which is exactly what IWPC-REQ-003
prohibits this contract family from inventing, and which GAC-001/GLP-001
already reserve as a separate, higher-ceremony governance-process question
(§10). This is a disclosed, deliberate narrowing: a future, separately
governed contract revision MAY widen `eligible_authority`'s shape (§13's
additive-evolution allowance), but v1.0 does not, because doing so
prematurely would risk resolving, by implication, exactly the kind of
authority-*policy* question every predecessor contract has correctly
declined to resolve.

### 4.5 The Registry lookup contract

**AEM-REQ-010.** A Decision Template Authority Registry, wherever and
however it is eventually implemented, SHALL expose exactly one pure lookup
operation: `resolve(template_ref: str, template_version: str) ->
EligibleAuthorityDeclaration | None`. `None` SHALL be returned, never an
exception, for a `(template_ref, template_version)` pair with no
Declaration — "no declaration exists" is an ordinary, expected outcome
(§4.6's judgment call), not an error condition (§6).

**AEM-REQ-011.** The Registry lookup SHALL be read-only from the
perspective of every consumer this contract or any contract citing it
defines (evaluation function §5, Publication Coordinator per PEC-REQ-115,
CHGR construction per CHGR-REQ-199/200). No consumer MAY create, mutate,
or delete a Declaration through the lookup path.

**AEM-REQ-012.** The Registry lookup SHALL be a pure function of its two
inputs at any fixed point in time: repeated calls with identical inputs,
absent an intervening new-declaration authoring act, SHALL return
identical results (byte-identical `EligibleAuthorityDeclaration`, or
identical `None`).

### 4.6 Judgment call: Registry storage/authoring mechanics deferred to Implementation Planning

Phase 147A §6.3 explicitly left open "whether this lives on the existing
template model or a new companion structure," noting no new storage is
necessarily required. Direct source inspection (this contract's own
research, mirroring IWPC-001 §0's discipline) confirms IWPC-001 §13 was
able to freeze `SessionRepository`'s concrete filesystem contract in the
same phase that named it because a pre-existing `SessionRepository` ABC
(`interactive_workflow/persistence/repository.py`) already existed for it
to extend. No analogous artifact exists for Decision Templates: there is
no `DecisionTemplate` class, no template store, and no template-authoring
command anywhere in this repository today — `Session.template_ref` is a
bare, unvalidated `str` (confirmed at `session.py:87`; `PublicationHandoff`
consumes it only as an opaque pass-through identifier,
`handoff.py:168`). Freezing a concrete file layout, atomicity pattern, or
authoring command surface for the Registry in this same phase would
therefore not be "extending an existing contract" the way IWPC-001 §13 was
— it would be inventing an entire new persistence subsystem's mechanics
under a Contract Freeze phase whose own governing prompt confines it to
"contract, not implementation." This contract accordingly freezes only the
Registry's **lookup contract** (§4.5) — its observable behavior from a
consumer's point of view — and explicitly defers file format, storage
location, atomic-write discipline, and the Decision Template authoring
workflow itself to a future Implementation Planning phase (147D), which
MUST conform to §4.5's lookup contract however it chooses to satisfy it.
This is a narrower freeze than IWPC-001 §13 achieved, disclosed here as a
reasoned consequence of a real difference in starting conditions, not an
oversight.

### 4.7 Answering Required Architectural Question 15 in part (Decision Template authorship authority)

**AEM-REQ-013.** `EligibleAuthorityDeclaration.declared_by` (§4.1) is
recorded for provenance/audit purposes only (§8). This contract does not
evaluate, gate, or restrict who may author a Declaration — Decision
Template authorship and approval already have an existing, disclosed
responsibility mapping (CHGR-001 §20: "Implementer-class role" /
"Independent Contract Verifier"), unmodified and unnarrowed by this
contract. Whether a future implementation additionally applies AEM-001's
own evaluation mechanism recursively to Declaration authorship itself is
explicitly out of scope for v1.0 (§12).

## 5. The Evaluation Function

### 5.1 Answering Required Architectural Question 4 (What evidence establishes authority?) and Question 5 (What authority evidence is mandatory?)

**AEM-REQ-014.** The sole evidentiary input to evaluation is the claimed
decision-maker identity already collected by IWC-001/IWPC-001 at
`decision-session create` (`--owner-id`, IWPC-REQ-015; IWC-001's
session-owner concept). This contract introduces **no new evidence
collection** of any kind: no credential, no signature, no external
identity-provider assertion, and no assurance-level upgrade. This mirrors
IWPC-REQ-007/008's existing "MAY collect... MAY transport... SHALL NOT
establish" discipline exactly, applied to evaluation rather than
transport.

**AEM-REQ-015.** No authority evidence is *mandatory* to attempt
Confirmation, Readiness construction, or Publication (AEM-REQ-003 forbids
gating on evaluation entirely). The claimed decision-maker identity itself
remains mandatory only because IWC-001 already requires `--owner-id` at
session creation, independent of this contract.

### 5.2 Answering Required Architectural Question 6 (Can authority evaluation fail?) and Question 7 (Can evaluation be deferred?)

**AEM-REQ-016.** Evaluation, as this contract defines it, is a total
function over its two inputs (claimed identity, Declaration-or-`None`) —
it always returns exactly one `AuthorityEvaluationOutcome` (§5.3) and never
raises for well-formed inputs. "Failure" in the ordinary sense (an
exception, a crash) is reserved for malformed inputs only (§6); a
substantively unfavorable result (the claimed identity is not in the
eligible set) is not a failure — it is the `ineligible` result (§5.4), a
first-class, valid, disclosed outcome.

**AEM-REQ-017.** Evaluation MAY be deferred in exactly one sense: a
consumer (e.g., `PublicationCoordinator`, per PEC-REQ-115) is never
*required* to invoke evaluation. Where no `EligibleAuthorityDeclaration`
resolves for a session's `(template_ref, template_version)` (§4.5's `None`
return), evaluation, if invoked, deterministically yields `indeterminate`
(§5.4) rather than `ineligible` — "no declaration exists" is not evidence
of ineligibility, and this contract SHALL NOT permit conflating the two.

### 5.3 The `AuthorityEvaluationOutcome` shape

**AEM-REQ-018.** An `AuthorityEvaluationOutcome` SHALL carry exactly:

```
AuthorityEvaluationOutcome:
  template_ref: str
  template_version: str
  claimed_identity: str
  evaluation_result: EvaluationResult   # closed enum, §5.4
  declaration_ref: str | None    # the evaluated Declaration's own
                                  # identity, or None if indeterminate
  citation_text: str | None      # populated only when evaluation_result
                                  # == "eligible" (§7); the verbatim text
                                  # a Publication Coordinator MAY cite
                                  # per PEC-REQ-115
  evaluated_at: str (ISO-8601 UTC)
  evaluator_version: str          # a fixed marker identifying which
                                   # version of this contract's evaluation
                                   # function produced the outcome, for
                                   # future-revision auditability (§13)
  schema_version: "aem-outcome/1.0"
```

**AEM-REQ-019.** `AuthorityEvaluationOutcome` is immutable once produced,
mirroring `PublicationReadinessPackage`'s and every other IWC-001/PEC-001
artifact's own immutability discipline. It is never recomputed in place;
a session re-evaluated after a Declaration changes (impossible per
AEM-REQ-008's immutability rule, but relevant if the *claimed identity*
input were ever to change, which it cannot post-Confirmation) would
produce a new, distinct outcome record, never an edit to the prior one.

### 5.4 Answering Required Architectural Question 8 (What does unknown authority mean?)

**AEM-REQ-020.** `EvaluationResult` is a closed, three-value enumeration:

- **`eligible`** — a Declaration resolved for `(template_ref,
  template_version)`, and `claimed_identity` is a member of its
  `eligible_identities` set.
- **`ineligible`** — a Declaration resolved for `(template_ref,
  template_version)`, and `claimed_identity` is **not** a member of its
  `eligible_identities` set.
- **`indeterminate`** — no Declaration resolved for `(template_ref,
  template_version)` (§4.5's `None` case). This is "unknown authority":
  not a claim that the identity is ineligible, and not a claim that it is
  eligible — a disclosed absence of an applicable rule, exactly mirroring
  CHGR-REQ-199's existing "correctly and permanently absent — never
  fabricated" discipline for `authority_basis_claimed` itself, one layer
  earlier.

**AEM-REQ-021.** No fourth value (e.g., a numeric confidence score, a
partial-match result) is defined for v1.0. This restates IWPC-REQ-046's
own closed-status-vocabulary discipline (`"success"`/`"error"`, no
`"partial"`), applied here to evaluation results specifically.

### 5.5 Answering Required Architectural Question 9 (How is authority represented in Decision Templates?)

**AEM-REQ-022.** Authority is represented on a Decision Template
exclusively through the `(template_ref, template_version)`-keyed
Eligible Authority Declaration (§4), resolved through the Registry lookup
(§4.5). No other representation (an inline field on `Session`, a CLI flag
at `decision-session create`, an environment variable) is authorized by
this contract. `Session.template_ref` itself is unmodified in shape by
this contract (out of IWC-001's territory; §2.2).

## 6. Failure Model

**AEM-REQ-023.** Evaluation SHALL raise (never silently substitute a
default result) for exactly the following malformed-input conditions:

- `claimed_identity` is empty or not well-formed per the same structural
  validation IWPC-REQ-118 already applies to `--owner-id`/`--operator-id`
  (non-empty; no format beyond non-emptiness enforced for v1.0);
- `template_ref` or `template_version` is empty;
- a resolved `EligibleAuthorityDeclaration`'s `eligible_identities` set is
  empty (a structurally invalid Declaration — §4.1 requires non-empty;
  such a Declaration SHALL have been rejected at authoring time by a
  future implementation, but evaluation MUST still fail closed if one is
  ever encountered, per the fail-closed discipline restated at §8).

**AEM-REQ-024.** No other condition SHALL raise. In particular: "no
Declaration exists" (§5.4's `indeterminate`) and "claimed identity is not
a member" (§5.4's `ineligible`) are both successful evaluations producing
a valid `AuthorityEvaluationOutcome`, never exceptions.

**AEM-REQ-025.** A raised evaluation failure SHALL map, at whatever future
CLI/transport surface eventually invokes evaluation, to that surface's own
existing closed error taxonomy (IWPC-001 §19) rather than a new one
invented by this contract — this contract defines the failure *condition*,
not a new error-rendering vocabulary, mirroring IWPC-001's own layering
discipline (§11.2 below).

## 7. Population of `authority_basis_claimed`

**AEM-REQ-026.** An `AuthorityEvaluationOutcome` with `evaluation_result ==
"eligible"` MAY be used, by `PublicationCoordinator` alone, to construct
CHGR-001's `authority_basis_claimed` field, using exactly the outcome's own
`citation_text` verbatim — restating PEC-REQ-115's existing "MAY construct
`authority_basis_claimed` solely from that already-verbatim citation, never
from an independent judgment of whether the claim is actually valid"
unchanged, one layer later, now with a concrete source for the citation
text PEC-REQ-115 already anticipated but could not yet name.

**AEM-REQ-027.** An `AuthorityEvaluationOutcome` with `evaluation_result ==
"ineligible"` or `"indeterminate"` SHALL NOT populate
`authority_basis_claimed`; the field SHALL remain correctly and
permanently absent for that record, per CHGR-REQ-199, and its absence
SHALL continue to be named in the record's own `limitations` array
unchanged.

**AEM-REQ-028.** `PublicationCoordinator` SHALL NOT itself invoke
evaluation, re-derive an outcome, or perform any part of the evaluation
function — restating PEC-REQ-113's existing forbidden-import boundary
discipline: the Coordinator depends only on the Publication Readiness
Package boundary and the CHGR-001 write surface. Where a future
implementation makes evaluation output available to Publication, it SHALL
arrive as a verbatim, already-computed field carried through the widened
Package (mirroring how IWC-001 v1.2's widened Package already carries
`decision_maker_identity_evidence` for `assurance_level`'s own
CHGR-REQ-200 derivation), never through a new Coordinator-side import of
this contract's own evaluation function or Registry.

**AEM-REQ-029.** `evaluation_result` itself (the three-valued outcome, as
distinct from `authority_basis_claimed`'s derived citation text) MAY be
disclosed in a CHGR's `limitations` or `extensions` array (CHGR-001 §12's
open-extension-point precedent), for `ineligible` and `indeterminate`
outcomes especially, so that "an evaluation was attempted and found
unfavorable" remains distinguishable from "no evaluation was attempted at
all" — this restates CHGR-REQ-097's "any gap... SHALL be surfaced, never
silently resolved in the record's favor" one layer later. The exact
schema field this occupies is Implementation Planning's (147D) decision,
not frozen by this contract beyond the disclosure obligation itself.

## 8. Auditability and Provenance

**AEM-REQ-030.** Every `AuthorityEvaluationOutcome` that is actually
constructed and consumed by a Publication (i.e., contributes a
`citation_text` per §7) SHALL be independently reconstructible from
already-persisted, already-frozen data: the CHGR's own
`authority_basis_claimed` citation text, the session's `template_ref`/
`template_version` (already persisted, IWPC-001 §12/§13), and the
Declaration the citation was drawn from (Registry-resolvable per §4.5,
assuming the Declaration itself remains available — an availability
guarantee this contract does not itself make, since Registry persistence
mechanics are deferred per §4.6). A future verifier SHALL always be able
to determine, from a CHGR's own `authority_basis_claimed` field plus its
governing Decision Template's identity and version (already required by
CHGR-001 §21's Audit Contract: "using which Decision Template — template
identifier and version"), what the evaluation claims to have been based
on — restating CHGR-001 §21 unchanged, one layer deeper.

**AEM-REQ-031.** This contract does not itself define a persistence
mechanism for `AuthorityEvaluationOutcome` records beyond what is implied
by §7's population rule (the outcome's `citation_text` becomes part of an
already-persisted CHGR when `eligible`). Whether `ineligible`/
`indeterminate` outcomes are persisted anywhere durable, and in what form,
is deferred to Implementation Planning (147D), consistent with §4.6's
Registry-mechanics deferral.

**AEM-REQ-032.** Fail-closed discipline: a malformed or ambiguous
evaluation input (§6) SHALL never be resolved in a way that produces
`eligible`, `authority_basis_claimed` population, or any assertion of
authority — restating `docs/ROADMAP.md`'s "Fail closed" principle and
CHGR-REQ-204's identical discipline, one layer earlier.

## 9. Interaction with the Typed Authority Model (TAMC-001 / TAMPC-001)

**AEM-REQ-033.** TAMC-001/TAMPC-001 govern a **different, unrelated**
authority concept: `authority_epoch`/`authority_state` and related record
families (`src/pcae/cltr/authority/*.py`) express **lifecycle-transition
authority** for the Canonical Lifecycle Transition Record cutover system
— i.e., which epoch/state a CLTR migration artifact is authoritatively in
— not a human decision-maker's eligibility to select a Decision Template
option. This contract SHALL NOT be read as extending, consuming, narrowing,
or in any way interacting with TAMC-001/TAMPC-001's own authority model.
The shared English word "authority" names two structurally unrelated
concepts across these two contract families; this requirement exists
specifically to foreclose the perceived-overlap risk Phase 147A §8 flagged
generically and this contract now resolves concretely by direct comparison
of both contracts' primary text (confirmed: TAMC-001 §6/§7's "Authority
SHALL ALWAYS originate from governed lifecycle progression" concerns CLTR
state ownership, not Decision Template eligibility).

**AEM-REQ-034.** No requirement of TAMC-001 or TAMPC-001 is narrowed,
widened, or reinterpreted by this contract. No requirement of this
contract MAY be satisfied by, or is satisfied by, any TAMC-001/TAMPC-001
mechanism.

## 10. Interaction with GAC-001 / GLP-001 (Governance-Adoption Authority)

**AEM-REQ-035.** GAC-001 §9's Stage 6 "governance decision" (GAC-REQ-040
through GAC-REQ-044) concerns a **different, unrelated** authority
question: whether GLP-001 (the governed-pilot lifecycle pattern itself)
is more broadly adopted across future PCAE initiatives — a one-time-per-
pilot, human, governance-*process* decision. This is not a per-decision
eligibility evaluation of the kind this contract defines. This contract
SHALL NOT be read as discharging, informing the outcome of, or in any way
substituting for GAC-001 §9's own Stage 6 decision; the still-undischarged
GAC-001 §9 question (per `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md`)
remains entirely outside this contract's scope and this contract's
existence does not change its status.

**AEM-REQ-036.** No requirement of GAC-001 or GLP-001 is narrowed,
widened, or reinterpreted by this contract.

## 11. Interaction with Publication, Verification, and Inspection

### 11.1 Interaction with Publication (Question 11: Can publication occur without authority evaluation?)

**AEM-REQ-037.** Yes, unconditionally. Publication (PEC-001, IWPC-001 §6)
SHALL remain fully operable for a session whose `(template_ref,
template_version)` resolves no Eligible Authority Declaration
(`indeterminate`, or evaluation never invoked at all) exactly as it does
today, before this contract exists. This restates AEM-REQ-003/AEM-REQ-015:
evaluation is never a precondition of Confirmation, Readiness, or
Publication.

### 11.2 Interaction with the CLI/transport layer

**AEM-REQ-038.** This contract defines no new CLI command, flag, or
transport shape. IWPC-001 remains the sole normative authority over the
`decision-session`/`governance-record` command surfaces. A future
implementation phase that exposes evaluation results at the CLI/transport
layer (e.g., surfacing `evaluation_result` in `decision-session status`'s
output, or a future `decision-session evaluate-authority` command) MUST do
so through a separately governed IWPC-001 contract revision (IWPC-001 §30),
not by this contract's own authority.

### 11.3 Interaction with Verification (Question 12: Can verification determine authority?)

**AEM-REQ-039.** No. An Independent Contract Verifier or Independent
Implementation Verifier reviewing an `AuthorityEvaluationOutcome` or a
published `authority_basis_claimed` citation MAY verify **conformance** —
that the outcome's `evaluation_result` is correctly and deterministically
derivable from its own recorded `(template_ref, template_version,
claimed_identity)` and the Declaration it cites (§4.5, §5), and that
`authority_basis_claimed` was populated only from an `eligible` outcome
per §7 — but SHALL NOT itself determine, adjudicate, or override whether a
claimed identity *should* have been eligible. That determination is
exhaustively defined by §4/§5's deterministic function; there is no
separate, discretionary "verification of eligibility" role, mirroring
CHGR-001's own existing distinction between verifying a record's
structural/procedural conformance and verifying the substantive rightness
of a human decision (which this repository never claims to adjudicate).

### 11.4 Interaction with Inspection (Question 13: Can inspection determine authority?)

**AEM-REQ-040.** No. `decision-session status`/`readiness`,
`governance-record inspect`, or any other read-only inspection surface
MAY report an already-computed `AuthorityEvaluationOutcome` verbatim
(mirroring IWPC-REQ-022's read-only discipline) but SHALL NOT compute,
re-derive, or infer one. Inspection is reporting, never evaluation —
restating IWPC-REQ-065's "persisting... or reporting... confers no
authority" discipline, applied here to evaluation outcomes specifically.

## 12. Question 14 (What remains outside Chapter 147?) and Future Extension Points

**AEM-REQ-041.** The following are explicitly named as remaining outside
Chapter 147's scope, not resolved, narrowed, or foreclosed by this
contract:

- Any enforcement/blocking behavior conditioning Confirmation, Readiness,
  or Publication on an evaluation outcome (§2.2, AEM-REQ-003) — a future,
  separately governed contract revision MAY adopt this, with its own
  explicit reasoning, but v1.0 does not (§6.2 below).
- Registry storage mechanics, file format, and Decision Template
  authoring workflow (§4.6) — Implementation Planning's (147D) decision
  within this contract's bounds.
- A richer `eligible_authority` shape (roles, scopes, time-bounding,
  exceptions) (§4.4) — a future additive-or-major revision's decision,
  not this one's.
- Evaluation of the *authorizing principal* (`--operator-id` at
  `governance-record publish`) against any eligibility model — this
  contract scopes evaluation to the decision-maker role only (§5.1); a
  distinct, future evaluation model for the authorizing principal is not
  precluded but is not defined here.
- GAC-001 §9's Stage 6 governance-adoption decision (§10) — unrelated and
  undischarged by this contract's existence.
- TAMC-001/TAMPC-001's CLTR authority model (§9) — unrelated.
- Runtime, Permission Broker, or any execution-capability behavior (§2.2)
  — this contract's evaluation outcome has no relationship to Runtime
  execution, consistent with Phase 147A §3.1's own risk disclosure that
  this chapter "does not gate Runtime execution, which has no relationship
  to Decision Templates today."
- Recursive application of authority evaluation to Eligible Authority
  Declaration authorship itself (§4.7).

### 12.1 Future extension points

**AEM-REQ-042.** The following are named, explicitly, as the extension
points a future revision MAY use without requiring this contract's own
retraction (mirroring CHGR-001 §12's and IWPC-001 §11's identical
extensibility discipline):

- `EvaluationResult` MAY gain additional values in a future major revision
  (never a minor one — AEM-REQ-021's closed-set guarantee is a v1.0
  compatibility promise, not a permanent ceiling).
- `EligibleAuthorityDeclaration` MAY gain optional fields (e.g.
  `expires_at`) in a future additive revision without breaking v1.0
  consumers that read only the required fields (§4.1).
- The Registry lookup contract (§4.5) MAY be satisfied by any concrete
  storage mechanism a future Implementation Planning phase selects,
  provided its observable behavior conforms to AEM-REQ-010–012.
- A future, separately governed contract revision MAY adopt an
  enforcement/gating policy over evaluation outcomes, with its own
  explicit reasoning distinguishing it from the policy-invention this
  v1.0 contract deliberately declines (§6.2).

## 13. Amendment Contract

**AEM-REQ-043.** AEM-001 MAY evolve only through a governed superseding
contract revision (a future phase producing a revised
`AUTHORITY_EVALUATION_MODEL_CONTRACT.md` with an incremented version and an
explicit revision-history section), never through an implementing phase's
own discretion, mirroring CHGR-001's, PEC-001's, and IWPC-001's own
amendment discipline exactly.

**AEM-REQ-044.** A revision MAY be additive (new optional field, new
`EvaluationResult` value under a major bump, new extension point) without
renumbering any existing `AEM-REQ-###`; a revision narrowing or removing
an existing guarantee MUST be a major version and MUST retain retired
requirement identifiers in place, marked "Retired," never reused.

## 14. Conflict and Findings Register

Checked against IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001,
GAC-001, GLP-001, and direct source inspection. No conflict weakens an
existing contract.

| # | Item | Classification | Disposition |
|---|---|---|---|
| D-1 | No Eligible Authority Declaration, Registry, or evaluation function exists anywhere in this repository today | Non-Blocking, Observation | Expected and disclosed: this is a Contract Freeze phase; §4.6 explicitly defers storage/authoring mechanics to Implementation Planning (147D). |
| D-2 | `Session.template_ref` is a bare, unvalidated `str` with no resolvable Decision Template object behind it | Non-Blocking, Observation | Confirmed by direct source inspection (`session.py:87`); §4.5's Registry lookup contract is defined to be satisfiable regardless, keyed on the same opaque string plus `--template-version`. |
| D-3 | The gating-vs-disclosure-only judgment IWPC-REQ-002/003 and Phase 147A §6.2 left open for this phase | Resolved | §6.2 below adopts disclosure-only for v1.0, with reasoning; a future contract revision may reopen this only as its own explicit, separately governed decision. |
| D-4 | Perceived overlap between this contract's "authority" and TAMC-001's CLTR `authority_epoch`/`authority_state` | Non-Blocking, Observation | Resolved explicitly at §9 by direct textual comparison: the two concepts are structurally unrelated despite the shared English word. |
| D-5 | Perceived overlap between this contract and GAC-001 §9's Stage 6 governance-adoption decision | Non-Blocking, Observation | Resolved explicitly at §10: distinct layers (per-decision eligibility vs. one-time governance-process adoption); neither discharges the other. |
| D-6 | Evaluation of the authorizing principal (`--operator-id`) is not covered by this contract's evaluation scope | Non-Blocking, Observation | Disclosed at §12 as a named, deferred future extension; this contract scopes evaluation to the decision-maker role only, a disclosed narrowing of the broader "authority evaluation" ambition named by Phase 147A §6.2. |
| D-7 | `EligibleAuthorityDeclaration.declared_by` is recorded but not itself evaluated for authority to author a Declaration | Non-Blocking, Observation | Disclosed at §4.7; recursive application to authorship is explicitly out of v1.0 scope. |

**AEM-REQ-045.** No item in this register is Blocking as of this
contract's initial version. A future implementation phase MAY proceed
against this contract without first resolving any disclosed item above,
since each is either an explicitly out-of-scope deferred question (D-1,
D-6, D-7) or an explicitly resolved design decision with recorded
reasoning (D-2, D-3, D-4, D-5).

## 15. Non-Goals

This contract does not, and no future phase MAY treat it as if it did:

- implement any evaluation function, Registry, Declaration store, CLI
  command, transport adapter, or Publication Coordinator change;
- modify `src/pcae/interactive_workflow/**`, `src/pcae/governance/
  publication/**`, `src/pcae/cltr/**`, IWC-001, IWPC-001, PEC-001,
  CHGR-001, TAMC-001, TAMPC-001, GAC-001, or GLP-001;
- create engineering execution capability, change Permission Broker
  behavior, change lifecycle authority, change Publication authority, or
  change CHGR ownership;
- gate, block, or otherwise condition Confirmation, Readiness,
  Authorization, or Publication on an evaluation outcome (AEM-REQ-003);
- introduce a policy language, role model, or scope/time-bounding
  mechanism beyond §4's closed set-membership shape (AEM-REQ-004);
  resolve GAC-001 §9's Stage 6 decision or TAMC-001/TAMPC-001's own
  authority model (§9, §10);
- change runtime state or capability.

## 16. Judgment Call §6.2 — Disclosure-Only, Not Gating

Phase 147A §6.2's final bullet explicitly left this as "a Contract Freeze
phase-level judgment call": whether an unfavorable evaluation outcome ever
blocks Confirmation or Publication, or whether evaluation remains
disclosure-only for this chapter's initial scope. This contract adopts
**disclosure-only** (AEM-REQ-003, AEM-REQ-037), for the following reasons,
independently re-derived from primary contract text rather than assumed:

1. **IWPC-REQ-002/003 are unconditional, not scoped to "evaluation" as
   opposed to "policy."** IWPC-REQ-003 forbids "an authority-evaluation
   policy" from being introduced by "this contract" — and, per IWPC-001
   §29 C-1's own disposition, by any successor addressing the same named
   gap without its own fresh, explicit reasoning. A gating rule is
   definitionally a policy (a rule determining what MAY or MAY NOT
   proceed based on a condition), while a disclosure rule is not (it only
   changes what is recorded, never what is permitted). Adopting gating
   here, without an even higher-ceremony governance act than a single
   Contract Freeze phase, would risk exactly the boundary violation
   IWPC-001 was frozen to prevent.
2. **Every downstream consumer this contract touches already has a
   "MAY, never must, never infer validity" discipline.** PEC-REQ-115
   already frames `authority_basis_claimed` construction as something the
   Coordinator "MAY" do, "never from an independent judgment of whether
   the claim is actually valid." A gating rule would require the
   Coordinator (or some new component) to make exactly the "independent
   judgment of validity" PEC-REQ-115 already forbids it from making with
   the citation text alone — gating would need new authority PEC-001 does
   not currently grant anything in this repository.
3. **Principle 10 ("Pluggable first. Connected second. Automated third.
   Executable last.")** places blocking/enforcing behavior at a later
   maturity stage than simple evaluation-and-disclosure. This chapter (per
   Phase 147A §5) was selected in part because it "evaluates and
   discloses an authority claim for governance-record purposes, a
   strictly narrower act than 'enforcing' anything." Adopting gating in
   this same phase would silently expand the chapter's own selection
   rationale.
4. **A disclosure-only v1.0 is strictly reversible in the direction of
   more enforcement, never the reverse.** A future, separately governed
   contract revision MAY adopt gating later, with its own explicit
   Contract Freeze-level reasoning and its own independent verification
   pass (mirroring how IWPC-001 itself was frozen before any of its
   commands were implemented) — but a v1.0 that gated first and tried to
   loosen to disclosure-only later would have to explain away a period of
   real, already-occurred blocking, a materially harder amendment to
   make honestly.

This is a **reasoned choice**, not a default: the alternative (gating) was
seriously considered and rejected because it fails IWPC-REQ-002/003's
unconditional prohibition, would exceed PEC-001's current authority grant,
and would violate Principle 10's ordering — not because gating is
inherently invalid as a future capability.

---

**End of AEM-001 v1.0.**
