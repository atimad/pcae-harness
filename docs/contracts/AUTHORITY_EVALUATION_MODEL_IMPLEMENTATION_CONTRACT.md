# AEMIC-001 v1.1 — Authority Evaluation Model Implementation Contract

## Contract identity and status

**Contract:** AEMIC-001
**Version:** 1.1
**Status:** FROZEN
**Frozen by:** Phase 147E — Authority Evaluation Model Implementation
Contract Freeze
**Repaired by:** Phase 147E.1 — Authority Evaluation Model Implementation
Contract Repair (in-place minor revision correcting BF-147F-1; see §25)
**Architecture basis:** Phase 147D — Authority Evaluation Model
Implementation Architecture
(`docs/PHASE_147D_AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_ARCHITECTURE.md`)
**Governing predecessor:** AEM-001 v1.0 — Authority Evaluation Model
Contract (`docs/contracts/AUTHORITY_EVALUATION_MODEL_CONTRACT.md`), FROZEN,
independently verified by Phase 147C with two Non-Blocking findings
(F-147C-1, F-147C-2)
**Governed subject:** The **implementation-level design** of the
standalone `pcae.authority_evaluation` package: its package boundary,
public domain model, evaluation-function contract, registry-lookup
contract, failure taxonomy, serialization rules, security properties, and
auditability obligations — precise and falsifiable enough for a future,
separately-authorized implementation phase to build against without
re-deriving Phase 147D's own architectural prose, and for a future,
separately-authorized verification phase to attempt to falsify.

**No-narrowing relationship to AEM-001.** AEMIC-001 narrows nothing AEM-001
already guarantees; it converts Phase 147D's implementation architecture
into binding, requirement-numbered obligations one layer more concrete than
AEM-001 itself, exactly as Phase 144B converted Phase 144A into PEC-001,
Phase 145B converted Phase 145A into IWPC-001, and Phase 147B converted
Phase 147A into AEM-001. Every AEMIC-001 requirement is either a direct,
one-step-more-concrete restatement of an existing AEM-REQ, or an
implementation-level decision AEM-001 itself explicitly deferred (AEM-001
§4.6, §12.1) that this contract now resolves unambiguously. AEMIC-001
MUST NOT be read as amending, narrowing, or superseding AEM-001, IWC-001,
IWPC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001, or GAC-001; where this
contract cites any of them, the citation demonstrates compatibility with an
already-frozen provision, never a redefinition of it (mirrors AEM-001 §0's
own illustrative-citation discipline).

**Supersession rules.** AEMIC-001 v1.0 governs the first implementation of
`pcae.authority_evaluation` only. A future revision of AEM-001 (via its own
§13 Amendment Contract) that widens or narrows the evaluation model MAY
require a corresponding AEMIC-001 revision; until such a revision is
frozen, AEMIC-001 v1.0 remains the sole normative authority over this
package's implementation-level shape. AEMIC-001 itself MAY be revised only
through a governed superseding contract revision (§21 below), never
through an implementing phase's own discretion.

**Requirement numbering convention:** Requirements are identified
`AEMIC-REQ-001` through the final requirement in this document, sequential,
grouped by the section that introduces them, with no gaps and no reuse.
Once frozen, no requirement identifier is renumbered, reassigned, or
reused — mirroring AEM-001's, PEC-001's, IWPC-001's, and CHGR-001's own
amendment discipline (§21 below).

**Runtime:** State: Observed / Maximum Capability: observe / Execution
Availability: unavailable — unaffected by this contract. Nothing this
contract defines is implemented by this phase; nothing it defines touches
`src/pcae/runtime/**`.

**This is contract text only.** It does not implement `pcae.authority_evaluation`
or any module, class, or function within it; does not create
`src/pcae/authority_evaluation/`; does not modify `src/pcae/**`,
`tests/**`, any schema file, or any existing contract; and does not
authorize a future implementation phase to begin merely by this contract's
own freeze (§2, §16, §19 below state this explicitly).

---

## 0. Normative Language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, **SHOULD**,
**SHOULD NOT**, and **MAY** are normative, with the meanings given in
GLP-001 §0, adopted unchanged here (mirrors AEM-001, PEC-001, IWPC-001).

Sections 1–20 state the normative rules in narrative form; §22 (the
Requirement/Test Matrix) is the authoritative, falsifiable enumeration
cross-referencing every `AEMIC-REQ-###`. Where narrative prose and a
requirement differ in force, the requirement's own text in the section
that introduces it is normative.

---

## 1. Purpose and Independent Reconstruction

**AEMIC-REQ-001.** This contract's purpose is to freeze, in falsifiable
terms, every design decision a future implementation of
`pcae.authority_evaluation` requires: package boundaries, public types,
evaluation inputs/outputs, declaration representation, registry
abstraction, evaluator semantics, serialization rules, identity rules,
version rules, determinism requirements, failure taxonomy, persistence
requirements, security properties, compatibility requirements, prohibited
dependencies, and deferred integration boundaries — sufficient for
implementation planning, implementation, adversarial testing, independent
verification, and later operational-readiness assessment.

This contract independently reconstructs every obligation below directly
from AEM-001 v1.0's own frozen text (`AEM-REQ-###`, cited throughout),
Phase 147C's independent verification (its two Non-Blocking findings,
reassessed at §19), Phase 147D's implementation architecture (treated as
evidence of design intent, never as contractual authority in its own
right — restating AEM-001 §0's identical discipline toward Phase 147A),
IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001, TAMPC-001, GAC-001, the
Decision Template and Human Governance Record schemas, and direct
re-inspection of `src/pcae/interactive_workflow/**`,
`src/pcae/governance/publication/**`, `src/pcae/interactive_workflow/persistence/**`,
and `tests/test_phase_144c_publication_coordinator.py`'s
`_FORBIDDEN_IMPORT_ROOTS` mechanism — never transcribed uncritically from
Phase 147D. Where Phase 147D contains a design choice not strictly
required by AEM-001, §1.1 below classifies it explicitly.

### 1.1 Classification of Phase 147D's design choices

| 147D choice | Classification | Disposition in this contract |
|---|---|---|
| `pcae.authority_evaluation` as a new, sibling, self-contained package | **Required** — AEM-001 §0 declines to be an amendment to any existing contract-owned package, and no existing package owns this concept | Frozen at §3 |
| Two free functions (`evaluate`, `resolve`) plus one ABC, no stateful service class | **Required** — AEM-REQ-009/011/012/016 mandate purity/totality, which a stateless free-function shape satisfies most directly | Frozen at §5, §11 |
| Registry ABC has no write method at all | **Required** — AEM-REQ-011 restricts every consumer to read-only access | Frozen at §11 |
| Concrete filesystem Registry implementation deferred past this contract's first implementation scope | **Permitted, and this contract elects it** — AEM-001 §4.6 leaves storage mechanics open; 147D §6.4 fully architected but explicitly did not build it. This contract resolves the question 147D left as a recommendation only: see §3.3 | Frozen at §3.3 |
| Storage root `.pcae/authority-declarations/` | **Recommended by 147D; this contract adopts it as binding** for whichever future phase builds the concrete Registry, since it is a disclosed, reasoned, non-overlapping choice (§12) | Frozen at §12 |
| Three distinct exception subclasses over one generic exception | **Recommended by 147D; this contract adopts it as binding** — a small number of named types maps more legibly onto AEM-REQ-025's future closed error taxonomy | Frozen at §13 |
| `extensions.authority_evaluation` as the schema home for `ineligible`/`indeterminate` disclosure | **Recommended by 147D; this contract does NOT bind it** — populating any CHGR field is PEC-001/CHGR-001 territory, outside this contract's own package boundary (§2.2); binding a specific `extensions` shape here would exceed AEMIC-001's own scope | **Deferred** — named at §17, not frozen |
| No caching | **Required** — AEM-REQ-012's purity guarantee makes caching a pure optimization with a disclosed staleness footgun and zero present justification | Restated at §11.6 as a non-goal |
| Registry-unavailability as a distinct exception, never `None` | **Required** — conflating it with "no Declaration" would violate AEM-REQ-024's closed condition list | Frozen at §13.2 |

No 147D choice is adopted as **Prohibited**; none of Phase 147D's design
choices contradicts AEM-001. The single "Deferred, not bound" item above
(the `extensions` schema shape) is deferred because it is genuinely outside
this contract's own package-boundary scope (§2.2), not because it is
unresolved by oversight.

---

## 2. Scope and No-Go Boundary

### 2.1 In scope

**AEMIC-REQ-002.** This contract MAY define, and does define: the
`pcae.authority_evaluation` package's module boundary and forbidden-import
rules (§3); the public domain model — `EligibleAuthorityDeclaration`,
`AuthorityEvaluationRequest`-shaped inputs, `AuthorityEvaluationOutcome`,
`EvaluationResult` (§4–§7); disclosure-only implementation obligations
(§8); the Decision Template citation-reconciliation rule (§9); identity and
versioning rules (§10); the Registry ABC's ordering, duplicate, and
availability semantics (§11); the first-implementation persistence
decision and, if a concrete filesystem Registry is later built, its
persistence contract (§12); the failure taxonomy (§13); the evaluation
function's purity/mutation contract (§14); security properties (§15);
auditability requirements (§16); compatibility guarantees (§17);
serialization rules (§18); and the deferred integration boundary (§17,
§19).

### 2.2 Out of scope

**AEMIC-REQ-003.** This contract SHALL NOT govern, define, or authorize:
any change to `src/pcae/interactive_workflow/**`, `src/pcae/governance/publication/**`,
or `src/pcae/cltr/**`; any CLI/transport command or flag (IWPC-001's
exclusive territory); Interactive Decision Session semantics
(IWC-001's exclusive territory); Publication authorization, execution, or
CHGR construction (PEC-001's/CHGR-001's exclusive territory); any schema
file under `src/pcae/schema_resources/**`; the CLTR authority-epoch/
authority-state model (TAMC-001/TAMPC-001); or GAC-001 §9's Stage 6
governance-adoption decision. This restates AEM-001 §2.2 one layer more
concretely, scoped to this contract's own implementation-boundary subject
matter.

**AEMIC-REQ-004.** This contract SHALL NOT authorize implementation. No
production code, module, class, or function under `src/pcae/**` is created,
modified, or implied to already exist by this contract's own freeze. §19
(No-Go Boundary Confirmation) restates this as an audited fact of this
phase's own execution, not merely a forward-looking prohibition.

**AEMIC-REQ-005.** This contract SHALL NOT introduce, and no type,
function, or outcome it defines MAY constitute, an enforcement mechanism —
restating AEM-REQ-003 unchanged, one layer more concrete: no
`pcae.authority_evaluation` type or function signature defined below may be
named, shaped, or documented in a way that implies it grants, blocks, or
conditions Confirmation, Readiness, Authorization, or Publication (§8).

---

## 3. Package Boundary Contract

### 3.1 Package root

**AEMIC-REQ-006.** The package root SHALL be `src/pcae/authority_evaluation/`,
a new top-level sibling of `pcae.interactive_workflow`, `pcae.governance`,
`pcae.cltr`, `pcae.cltr_prototype`, `pcae.commands`, `pcae.core`,
`pcae.lifecycle`, `pcae.repository_intelligence`, `pcae.schema_resources`,
and `pcae.schema_runtime` — never nested inside any of them, restating
Phase 147D §6's sibling-package architecture unchanged. This placement
ensures no existing forbidden-import test (e.g.
`tests/test_phase_144c_publication_coordinator.py`'s
`_FORBIDDEN_IMPORT_ROOTS`) needs modification merely to accommodate this
package's own internal structure.

### 3.2 Required modules (first implementation scope)

**AEMIC-REQ-007.** The package's first implementation SHALL include, at
minimum, exactly these modules:

```
src/pcae/authority_evaluation/
  __init__.py       # public re-exports only; no logic
  models.py         # EligibleAuthorityDeclaration, AuthorityEvaluationOutcome,
                     # EvaluationResult (§4-7)
  evaluation.py      # the pure evaluate() function (§14)
  registry.py         # AuthorityRegistry ABC only (§11) -- no concrete
                     # implementation in this module (§3.3)
  errors.py           # the exception hierarchy (§13)
  serialization.py    # to_payload/from_payload for both record types (§18)
```

No other module is required for the first implementation. A future
implementation MAY split any of the above into private submodules
(e.g. `models/declaration.py`, `models/outcome.py`) provided the public
re-export surface at `pcae.authority_evaluation.__init__` remains stable
per §3.4.

### 3.3 Concrete Registry implementation: explicitly deferred

**AEMIC-REQ-008.** A concrete, storage-backed `AuthorityRegistry`
implementation (e.g. a filesystem-backed `FilesystemAuthorityRegistry`) is
**explicitly deferred** from this package's first implementation scope.
The first implementation SHALL define the `AuthorityRegistry` ABC (§11)
only, with zero concrete subclass.

This is a **decision, not an omission**, resolved as follows: Phase 147D
§6.4 fully architected a concrete filesystem Registry design (storage
layout, atomicity, path safety, immutability enforcement) but explicitly
titled that section "architected, not built," and Phase 147D §10 (Migration
Architecture) itself lists building the evaluation package (step 1) and
building a concrete Registry implementation (step 2) as two **separate**
rollout steps. This mirrors the repository's own strongest precedent for
exactly this situation: `SessionRepository` (the ABC) was frozen and built
in Phase 143K with zero concrete implementation, and
`FilesystemSessionRepository` (the concrete filesystem backend) was built
in a **later, separately-governed phase** (145D) — not the same phase, and
not merely "the same package, a later module." This contract adopts the
identical two-phase discipline: the first implementation phase authorized
under this contract builds `pcae.authority_evaluation.registry.AuthorityRegistry`
(ABC) and nothing else in `registry.py`; a subsequent, separately-governed
implementation phase builds the concrete filesystem backend, which SHALL
conform to §11's ABC contract and SHOULD conform to §12's persistence
contract (frozen now, for that future phase's benefit, exactly as
`SessionRepository`'s own ABC-freezing phase did not need to also freeze
`FilesystemSessionRepository`'s file layout in the same phase, yet
IWPC-001 §13 later did so productively ahead of 145D's own build).

**AEMIC-REQ-009.** Without a concrete Registry implementation, the first
implementation's own test suite (§22) SHALL exercise `AuthorityRegistry`
exclusively through a minimal, in-memory test double defined within
`tests/` (never inside `src/pcae/authority_evaluation/` itself, which
SHALL NOT contain any concrete Registry implementation per AEMIC-REQ-008)
— mirroring how `pcae.authority_evaluation.evaluation`'s own unit tests
require no Registry fixture at all (§14).

### 3.4 Forbidden imports

**AEMIC-REQ-010.** No module under `src/pcae/authority_evaluation/**`
SHALL import, directly or transitively through another first-party module,
from:

- `pcae.interactive_workflow` (any submodule);
- `pcae.governance` (any submodule, including `pcae.governance.publication`);
- `pcae.cltr` or `pcae.cltr_prototype`;
- `pcae.commands` (the CLI command layer);
- `pcae.cli` (the CLI entry point);
- `pcae.core` (the governance-harness engine itself — phase/task/session
  machinery — an entirely different layer from the governed subject
  matter this package evaluates);
- `pcae.lifecycle` (phase-lifecycle governance machinery);
- `pcae.repository_intelligence` (analytics layer).

**AEMIC-REQ-011.** `pcae.authority_evaluation` MAY depend only on: the
Python standard library, and, within its own package boundary, its own
sibling modules (`models`, `errors`, `serialization`, `evaluation`,
`registry`). No dependency on `pcae.schema_resources` or
`pcae.schema_runtime` is required or authorized for v1.0 — the Decision
Template schema's `eligible_authority` field remains a citation-source
concept this package's own `EligibleAuthorityDeclaration` is
authored/keyed alongside, never a JSON schema this package loads,
validates against, or imports code from (§9). A future revision MAY
reconsider this restriction only through this contract's own Amendment
process (§21).

**AEMIC-REQ-012.** This restates and extends AEM-REQ-028's "the Coordinator
never imports this contract's evaluation function or Registry" discipline
from the opposite direction: `pcae.authority_evaluation` itself never
imports anything that would let it discover, infer, or construct
Publication, Runtime, or execution authority. The package obtains no
authority of any kind through its own import graph — restating AEM-001
§2.2's Runtime/Permission Broker exclusion at the dependency-direction
level.

### 3.5 Allowed dependency direction

**AEMIC-REQ-013.** The dependency direction is strictly one-way and,
for v1.0, **zero-way** in practice: nothing outside
`pcae.authority_evaluation` may be assumed to already depend on it (no such
dependent exists after this contract's own freeze, per AEMIC-REQ-004), and
`pcae.authority_evaluation` depends on nothing outside the standard library
and its own sibling modules. A future, separately-governed integration
phase (§17) is the only mechanism by which any other package may come to
depend on `pcae.authority_evaluation` (e.g. a future widened
`PublicationReadinessPackage` carrying a verbatim, already-computed
outcome — never a live import of this package's own functions from
`governance/publication/**`, restating AEM-REQ-028/Phase 147D §5.6
unchanged).

### 3.6 Public re-export stability

**AEMIC-REQ-014.** `pcae.authority_evaluation.__init__` SHALL re-export
exactly: `EligibleAuthorityDeclaration`, `AuthorityEvaluationOutcome`,
`EvaluationResult`, `evaluate`, `AuthorityRegistry`, and the exception
hierarchy's public names (§13). No private helper, and no concrete Registry
implementation (per AEMIC-REQ-008, none exists in v1.0), is re-exported
from `__init__`.

---

## 4. Public Domain Model — `EligibleAuthorityDeclaration`

**AEMIC-REQ-015.** `EligibleAuthorityDeclaration` SHALL be an immutable
(frozen dataclass or equivalent) record carrying exactly the fields
AEM-REQ-007 already freezes, with the following field-by-field
mandatory/optional and validation disposition (none of which AEM-001 left
ambiguous, but which this contract makes falsifiable at the
implementation level):

| Field | Type | Mandatory | Structural validation at construction |
|---|---|---|---|
| `template_ref` | `str` | Yes | Non-empty (§10.1) |
| `template_version` | `str` | Yes | Non-empty (§10.1) |
| `eligible_identities` | `frozenset[str]` | Yes | Non-empty; every member a non-empty `str` (§10.1) |
| `declared_at` | `str` (ISO-8601 UTC) | Yes | Non-empty; parseable as ISO-8601 (structural only — no clock-skew or future-dated rejection, mirroring `Session`'s own timestamp discipline) |
| `declared_by` | `str` | Yes | Non-empty (recorded for provenance only, never evaluated — AEM-REQ-013) |
| `schema_version` | `str` | Yes | SHALL equal exactly `"aem-declaration/1.0"` (§10.3) |

**AEMIC-REQ-016.** No field beyond the six above SHALL exist on
`EligibleAuthorityDeclaration` in v1.0 — restating AEM-REQ-007's closed
shape. In particular, no `role`, `expires_at`, `conditions`, or
`exceptions` field is defined (AEM-REQ-004's non-policy-language judgment
call, restated).

**AEMIC-REQ-017.** `EligibleAuthorityDeclaration` construction SHALL
raise a typed error (§13.1) for any structural violation in the table
above; it SHALL NOT silently coerce, truncate, or default an invalid field.

**AEMIC-REQ-018.** Once constructed, `EligibleAuthorityDeclaration` SHALL
be immutable at the language level (a frozen dataclass or equivalent — no
setter, no mutable field). AEM-REQ-008's higher-level "immutable once
evaluated against" rule is an **authoring-workflow** discipline this
contract does not itself enforce at the object level (there is no
`resolve`-time visibility into "has this been evaluated against before,"
per Phase 147D §6.4's own disclosed reasoning) — restated as a named
limitation at §11.5, not silently assumed solved by language-level
immutability alone.

## 5. Public Domain Model — Evaluation Inputs

**AEMIC-REQ-019.** The `evaluate` function (§14) SHALL accept exactly five
positional-or-keyword arguments, with no request wrapper object required
for v1.0 (a request "object" in the governing prompt's sense is these five
parameters taken together, not a distinct dataclass — introducing one would
add a sixth public type AEM-001 never requires and Phase 147D's own
§6.2 architecture does not name):

| Parameter | Type | Source |
|---|---|---|
| `claimed_identity` | `str` | Already-collected `Session.owner_identity` (or an equivalent already-collected value a future caller supplies) — AEM-REQ-014; this package collects nothing |
| `declaration` | `EligibleAuthorityDeclaration \| None` | The Registry's own `resolve()` return value — AEM-REQ-010 |
| `evaluated_at` | `str` (ISO-8601 UTC) | Supplied by the caller (this package has no clock dependency of its own — keeps `evaluate` a pure function of its arguments, §14.4) |
| `evaluator_version` | `str` | A fixed constant this package itself defines and exports (§10.4) — never caller-supplied in the sense of being arbitrary; callers pass through the package's own published constant |
| `citation_text` | `str \| None`, default `None` | Sourced by the caller, verbatim, from the Decision Template's own `eligible_authority` field (§9, AEMIC-REQ-030) — never evaluated, interpreted, or verified by this package; carried through into the constructed outcome only when `evaluation_result == eligible` (§14, AEMIC-REQ-101) |

**AEMIC-REQ-020.** No caller-supplied metadata beyond the five parameters
above is accepted by `evaluate`. No "evaluation context" object, no
free-form `dict` of caller metadata, is defined for v1.0 — restating
AEM-REQ-014's "no new evidence collection of any kind" one layer more
concretely: `citation_text` is not evidence bearing on the authority
determination itself (`evaluation_result` remains a pure function of
exactly the two evidentiary inputs AEM-REQ-016 names — `claimed_identity`
and `declaration` — unchanged by this parameter's addition); it is
disclosure content the outcome's own shape already required
(AEM-REQ-018, AEMIC-REQ-021) and that a caller must supply through some
channel regardless of which channel this contract chooses (§9). There is
nothing else, beyond the five parameters named above, that AEM-001
authorizes evaluation to consider or that this package's own outcome
shape (§6) requires as construction input.

## 6. Public Domain Model — `AuthorityEvaluationOutcome`

**AEMIC-REQ-021.** `AuthorityEvaluationOutcome` SHALL be an immutable
record carrying exactly the eight fields AEM-REQ-018 already freezes, with
the following disposition:

| Field | Type | Mandatory | Notes |
|---|---|---|---|
| `template_ref` | `str` | Yes | Verbatim copy of the evaluation's own input |
| `template_version` | `str` | Yes | Verbatim copy of the evaluation's own input |
| `claimed_identity` | `str` | Yes | Verbatim copy of the evaluation's own input |
| `evaluation_result` | `EvaluationResult` | Yes | Closed three-value enum (§7) |
| `declaration_ref` | `str \| None` | Conditionally | Non-`None` iff a Declaration resolved (`eligible` or `ineligible`); `None` iff `indeterminate` (§10.2 defines the reference's own shape) |
| `citation_text` | `str \| None` | Conditionally | Non-`None` if and only if `evaluation_result == eligible` (AEM-REQ-018's own field description, restated as a construction-time invariant, §6.1) |
| `evaluated_at` | `str` (ISO-8601 UTC) | Yes | Verbatim copy of the caller-supplied input |
| `evaluator_version` | `str` | Yes | Verbatim copy of the caller-supplied input |
| `schema_version` | `str` | Yes | SHALL equal exactly `"aem-outcome/1.0"` |

### 6.1 The `citation_text` if-and-only-if invariant

**AEMIC-REQ-022.** Construction of `AuthorityEvaluationOutcome` SHALL
enforce, as a structural invariant checked at construction time (not left
to caller discipline): `citation_text is not None` **if and only if**
`evaluation_result == EvaluationResult.ELIGIBLE`. A construction attempt
violating either direction of this invariant (a non-`None` citation on a
non-`eligible` result, or a `None` citation on an `eligible` result) SHALL
raise a typed error (§13.1). This is the single most important field-level
invariant this contract adds beyond AEM-001's own prose description,
because it is the mechanical device that makes AEM-REQ-026/027's
population rule (§8) falsifiable by construction rather than merely by
convention.

**AEMIC-REQ-023.** `AuthorityEvaluationOutcome` SHALL be immutable at the
language level once constructed (restating AEM-REQ-019). It is never
recomputed in place; a distinct evaluation event, however triggered,
produces a new, distinct `AuthorityEvaluationOutcome` instance.

## 7. `EvaluationResult` — the closed enumeration

**AEMIC-REQ-024.** `EvaluationResult` SHALL be a closed Python `Enum` with
exactly three members, matching AEM-REQ-020 exactly:

- `ELIGIBLE` (wire value `"eligible"`) — a Declaration resolved, and
  `claimed_identity` is a member of its `eligible_identities`.
- `INELIGIBLE` (wire value `"ineligible"`) — a Declaration resolved, and
  `claimed_identity` is **not** a member.
- `INDETERMINATE` (wire value `"indeterminate"`) — no Declaration resolved.

**AEMIC-REQ-025.** No fourth value is defined for v1.0. A future major
revision MAY add one only through this contract's own Amendment process
(§21), never through an implementing phase's own discretion — restating
AEM-REQ-021/AEM-REQ-042.

**AEMIC-REQ-026.** This enumeration SHALL NOT be represented as a bare
`str` anywhere in the public API — restating the closed-vocabulary
discipline IWPC-REQ-046 already applies elsewhere in this repository, at
the implementation-type level: a Python `Enum`, not a string constant, is
the type this contract binds, so that an invalid fourth value is a
type-checking or construction-time error, not a silently-accepted typo.

---

## 8. Disclosure-Only Semantics

**AEMIC-REQ-027.** No type, function, method, or module-level name in
`pcae.authority_evaluation` SHALL be named, documented, or shaped in a way
a reasonable downstream consumer could mistake for an authorization
decision. In particular: the package SHALL NOT define any function or
method named or described as `authorize`, `grant`, `permit`, `allow`, or
`deny`; `evaluate`'s own docstring, and every public type's own docstring,
SHALL state explicitly that the result is a disclosed evaluation, never an
authorization — restating AEM-REQ-003 as a naming/documentation
requirement, not merely a behavioral one.

**AEMIC-REQ-028.** The evaluator MAY only: resolve a registered Declaration
(via a caller-supplied Registry lookup result, §5); validate the
structural shape of its own inputs (§13.1); return the Decision Template's
declared eligible-authority citation text, verbatim, when and only when
`evaluation_result == eligible` (§6.1); and disclose, via `evaluation_result`
itself, why a Declaration could not establish eligibility (`ineligible`) or
did not exist at all (`indeterminate`). The evaluator SHALL NOT: determine
legal authority; grant, deny, or authorize anything; infer policy beyond
the closed set-membership check (§4); resolve human eligibility beyond
that check; or elevate runtime, execution, or Permission Broker capability
in any way — restating AEM-REQ-003/037/038/039/040, AEM-001 §2.2, as a
single consolidated implementation-level obligation.

**AEMIC-REQ-029.** Every `AuthorityEvaluationOutcome` MUST be
machine-distinguishable, by its own `evaluation_result` field alone,
between (a) a claimed identity found ineligible against a real,
resolved Declaration, and (b) no Declaration existing at all — restating
AEM-REQ-017/020 as the specific implementation-level property a consumer
(e.g. a future CHGR-consuming phase) needs to avoid conflating "an
evaluation was attempted and found unfavorable" with "no evaluation was
attempted" (AEM-REQ-029's own downstream disclosure obligation, carried
forward as a precondition this package's own outcome shape must satisfy).

---

## 9. Decision Template and Citation Contract — Reconciling F-147C-1 and FA-147D-3

**AEMIC-REQ-030.** `decision_template.schema.json`'s existing
`eligible_authority` field (required, free-text, 1–500 characters) SHALL
remain, unmodified, the **sole citation-text source** for
`AuthorityEvaluationOutcome.citation_text` when `evaluation_result ==
eligible`. This restates Phase 147D §4.1's reconciliation as a binding
implementation rule: `EligibleAuthorityDeclaration` does not duplicate,
paraphrase, or independently generate citation text; whatever future
authoring workflow constructs an `EligibleAuthorityDeclaration` alongside a
Decision Template MUST source `citation_text` from that same template's
own `eligible_authority` field, verbatim.

**AEMIC-REQ-031.** `evaluate` SHALL copy `citation_text` verbatim into the
constructed `AuthorityEvaluationOutcome.citation_text` at evaluation time
(not merely hold a reference to be dereferenced later) — the simpler of the
two options the governing prompt raises ("whether declarations copy the
citation text... or reference a digest"), chosen because
`AuthorityEvaluationOutcome` is itself immutable and independently
reconstructible (AEM-REQ-030) only if it carries the text it claims,
verbatim, at the moment of construction; a reference requiring a later
dereference against a possibly-since-modified Decision Template would
violate AEM-REQ-019's immutability guarantee and AEM-REQ-030's
reconstructibility guarantee simultaneously. `EligibleAuthorityDeclaration`
itself, per AEMIC-REQ-015/016, does NOT carry a `citation_text` field in
v1.0, and this repair does not add one: `EligibleAuthorityDeclaration`'s
closed six-field shape is frozen one layer up, at AEM-REQ-007 ("SHALL
carry exactly... No other field is defined for v1.0"), and AEMIC-001
itself MUST NOT be read as narrowing or amending AEM-001 (Contract
identity and status, above) — adding a seventh field here would do exactly
that, and is accordingly foreclosed as a candidate repair (§25 records
this rejection explicitly). Instead, `citation_text` is `evaluate`'s own
fifth parameter (§5, AEMIC-REQ-019): the caller — the same
future authoring/evaluation-caller workflow that already must source
`eligible_identities` and every other Declaration field from outside this
package's own domain model — passes the Decision Template's own
`eligible_authority` text directly into the `evaluate()` call that
produces the outcome citing it, closing the channel BF-147F-1 (Phase 147F)
identified as missing without widening `EligibleAuthorityDeclaration`'s
own closed shape.

**AEMIC-REQ-032.** This contract does NOT resolve, in this version, exactly
how `evaluate`'s caller obtains the Decision Template's `eligible_authority`
citation text at the moment it constructs the `evaluate()` call (there is
no `DecisionTemplate` Python artifact today — Phase 147D §2.4, confirmed
unchanged by this phase's own re-inspection at §1, and reconfirmed
unchanged by Phase 147F's own re-inspection). This is a **named
limitation**, not a mechanically closed gap: a future, separately-governed
Decision Template authoring/lookup mechanism (outside this package's own
boundary, §2.2) is a precondition for any real caller to supply a
`citation_text` argument in practice, exactly as it was already a
precondition for supplying one indirectly before this repair — this
repair changes only *which parameter* carries the value into `evaluate`,
not whether a caller must somehow already possess it. This limitation is
safe for the first implementation because `pcae.authority_evaluation` is
fully unit-testable without one (hand-constructed `citation_text` values
suffice for every test in this contract's own Requirement/Test Matrix,
§22); it must be surfaced explicitly in the first implementation's own
module-level documentation and in any future implementation-planning
phase's own disclosure register; a future contract (an amendment to this
one, or a new companion contract governing Decision Template authoring) is
the correct place to close it.

**AEMIC-REQ-033.** Exact text equality, not normalization, SHALL be
required between a `citation_text` value and the Decision Template's own
`eligible_authority` field at the moment a Declaration/citation pairing is
authored — no whitespace trimming, case-folding, or Unicode normalization
is performed by this package (this package receives `citation_text`
directly as `evaluate`'s own fifth parameter, per AEMIC-REQ-019/031, and
performs no transformation of it whatsoever; it is carried into
`AuthorityEvaluationOutcome.citation_text` byte-for-byte).

**AEMIC-REQ-034.** This package SHALL NOT itself validate consistency
between an `EligibleAuthorityDeclaration.eligible_identities` set and its
sibling Decision Template's free-text `eligible_authority` field
(restating Phase 147D §4.4/FA-147D-3's own judgment call: a consistency-
validation rule would begin to resemble the policy-language expansion
AEM-REQ-004 forbids this contract family from introducing). This is a
**retained, disclosed limitation**, not resolved by this contract: the
resulting drift risk (a template's free text names one authority while its
`eligible_identities` set names a different one, with nothing in this
package detecting the mismatch) is real, is not mechanically closed here,
and is surfaced at §19 (Finding Disposition) and §22 (as an explicitly
untested condition, not a false-negative test gap) — a future, separately
governed Decision Template *authoring* workflow SHOULD, as an operational
discipline outside this package's own code, prompt consistency between the
two; this package itself enforces none.

**AEMIC-REQ-035.** No schema modification of any kind
(`decision_template.schema.json`, `human_governance_record.schema.json`,
or any other schema file) is authorized by this contract, restating
AEM-001's own No-Go Boundary and AEMIC-REQ-003/004.

---

## 10. Identity and Versioning

### 10.1 Identifier syntax and normalization

**AEMIC-REQ-036.** `template_ref`, `template_version`, and every member of
`eligible_identities` SHALL be non-empty `str` values. No further syntax
restriction (character set, length ceiling, casing) is imposed by this
contract beyond non-emptiness — mirroring AEM-REQ-023's own minimal
"non-empty; no format beyond non-emptiness enforced for v1.0" discipline
for `claimed_identity`, extended here to every identifier this package
handles. No canonical-form transformation (case-folding, whitespace
trimming, Unicode normalization) is performed by this package on any
identifier; equality for Registry lookup (§11) and set-membership
evaluation (§14) is **exact `str` equality**, case-sensitive, no implicit
normalization.

**AEMIC-REQ-037.** Decision Template identity, for every purpose this
package defines, SHALL be the tuple `(template_ref, template_version)` —
restating AEM-001 §5.5's own representation rule as this package's own
canonical identity tuple, never `Session.template_ref` alone (which,
per Phase 147D §2.4's own confirmed re-inspection, is unvalidated beyond
non-emptiness and carries no independent proof that a Registry entry with
a matching `template_version` actually exists — this package's own
`resolve(template_ref, template_version)` signature, requiring both,
is the only proof of Registry resolution this contract recognizes;
`Session.template_ref` by itself is never treated as evidence that a
Declaration exists).

### 10.2 `declaration_ref` shape

**AEMIC-REQ-038.** `AuthorityEvaluationOutcome.declaration_ref`, when
non-`None`, SHALL be a `str` deterministically derived from the evaluated
Declaration's own `(template_ref, template_version)` pair (e.g. their
concatenation with a fixed separator) — never an opaque, storage-specific
identifier (a filesystem path, a database row ID) that would leak
Registry-implementation details into this package's own storage-agnostic
public type. This preserves AEMIC-REQ-008's deferred-concrete-Registry
decision: `declaration_ref`'s shape does not depend on which concrete
Registry implementation (if any) eventually resolves the Declaration.

### 10.3 `schema_version` fields

**AEMIC-REQ-039.** `EligibleAuthorityDeclaration.schema_version` SHALL
equal exactly the literal string `"aem-declaration/1.0"`;
`AuthorityEvaluationOutcome.schema_version` SHALL equal exactly the literal
string `"aem-outcome/1.0"` — both restating AEM-REQ-007/018 as fixed,
construction-time-enforced literals (a construction attempt supplying any
other value SHALL raise, §13.1), never a caller-suppliable parameter.

### 10.4 `evaluator_version`

**AEMIC-REQ-040.** This package SHALL export exactly one module-level
constant, `EVALUATOR_VERSION` (a fixed `str`, e.g. `"aem-evaluator/1.0"`),
identifying which version of this contract's evaluation function produced
a given outcome — restating AEM-REQ-018's own field description
("a fixed marker... for future-revision auditability"). Callers SHALL pass
this package's own published constant unchanged; this package does not
itself validate that a caller passed the "correct" value (there is no
authority-escalation risk in a caller supplying an arbitrary string here,
since `evaluator_version` is descriptive metadata, never itself evaluated).

### 10.5 Version-compatibility and unsupported-version behavior

**AEMIC-REQ-041.** A future major revision of this contract (§21) MAY
introduce a new `schema_version` literal for either record type. This
package's `serialization.from_payload` (§18) SHALL raise a typed
deserialization error (§13.1) for any `schema_version` value it does not
recognize — never silently accept, coerce, or best-effort-parse an
unrecognized version, restating IWPC-001's own schema-version-checked
deserialization discipline (Phase 147D §6.6).

---

## 11. Registry Abstraction

**AEMIC-REQ-042.** `AuthorityRegistry` SHALL be an `ABC` exposing exactly
one abstract method:

```
resolve(template_ref: str, template_version: str) -> EligibleAuthorityDeclaration | None
```

No `create`, `persist`, `delete`, `list`, or `enumerate` method exists on
this ABC — restating AEM-REQ-011's read-only-consumer discipline as a
stronger boundary than `SessionRepository`'s own five-method ABC: every
consumer this contract or any contract citing it defines has read-only
access, full stop; Declaration authoring is an entirely separate, deferred
concern (§3.3) that MAY be exposed on a concrete subclass's own additional
methods without those methods being part of this ABC.

### 11.1 Lookup semantics

**AEMIC-REQ-043.** `resolve` SHALL be a pure function of its two inputs at
any fixed point in time (AEM-REQ-012, restated): repeated calls with
identical `(template_ref, template_version)`, absent an intervening
new-Declaration authoring act external to this package, SHALL return
identical results — an identical `EligibleAuthorityDeclaration` instance's
field values (not necessarily object identity), or identical `None`.

**AEMIC-REQ-044.** `resolve` SHALL return `None`, never raise, for a
`(template_ref, template_version)` pair with no matching Declaration —
restating AEM-REQ-010 unchanged: "no Declaration exists" is an ordinary,
expected outcome, not an error condition.

### 11.2 Duplicate and conflict handling

**AEMIC-REQ-045.** Exactly one `EligibleAuthorityDeclaration` SHALL ever be
resolvable for a given `(template_ref, template_version)` pair at any fixed
point in time — the Registry's own key space is one Declaration per
identity tuple, by construction of the abstraction itself (`resolve`
returns a single value, not a collection). A concrete Registry
implementation (§3.3, deferred) MUST enforce this uniqueness at its own
authoring-time write path (out of this package's own `resolve`-time
concern, since `resolve` has no visibility into how many candidate records
its own backing store might otherwise contain) — this contract requires
that whatever authoring mechanism a future concrete Registry exposes
reject an attempt to author a second Declaration for an already-Declared
`(template_ref, template_version)` pair, never silently overwrite or
first-match-select among candidates. **A `resolve`-time
first-match-among-multiple-candidates lookup is explicitly prohibited**:
if a concrete implementation's own storage layer is ever found to contain
more than one candidate record for the same identity tuple (a storage-layer
invariant violation, e.g. from an out-of-band file write), `resolve` MUST
raise a distinct, new typed error (§13.2's `AuthorityRegistryCorruptError`
family) rather than silently selecting one — restating this package's own
fail-closed discipline (§15) at the Registry layer specifically.

**AEMIC-REQ-046.** Historical (superseded) Declarations for an earlier
`template_version` of the same `template_ref` MAY coexist in a concrete
Registry's own storage indefinitely (AEM-REQ-008's per-version
immutability rule already establishes that a new version requires a new,
distinct Declaration, never an edit) — `resolve` selects the exact
Declaration matching the caller's own `(template_ref, template_version)`
argument pair; there is no "latest version" or "active version" selection
logic in this ABC, since the tuple itself is the exact selector, never an
ambiguous partial key.

### 11.3 Registry-unavailability behavior

**AEMIC-REQ-047.** A concrete Registry implementation MUST distinguish, by
raising `AuthorityRegistryUnavailableError` (§13.2), any condition where its
own storage layer could not be consulted at all (a read failure,
permission failure, an inaccessible path) from `resolve`'s ordinary `None`
return (AEM-REQ-010's "no Declaration exists"). Conflating the two would
misreport an operational fault as a substantive `indeterminate` evaluation
result, violating AEM-REQ-024's closed condition list — restating Phase
147D §8.2 (FA-147D-2) as a binding requirement rather than a named
observation.

**AEMIC-REQ-048.** A concrete Registry implementation MUST raise
`AuthorityRegistryCorruptError` (§13.2), distinct from
`AuthorityRegistryUnavailableError`, for a condition where its storage
layer answered but the answer is structurally malformed (unparseable JSON,
a record missing a required field, a `schema_version` mismatch, or the
duplicate/conflict condition named at AEMIC-REQ-045) — a third, distinct
failure category from "unavailable" (the store could not be reached at
all) and "no Declaration" (the store was reached and correctly reports
absence).

**AEMIC-REQ-049.** The distinction among `None` (no Declaration),
`AuthorityRegistryUnavailableError` (store unreachable), and
`AuthorityRegistryCorruptError` (store reachable but malformed) SHALL be
deterministic and testable: a concrete implementation's own test suite
MUST demonstrate all three conditions independently reproducible from
distinct, controlled fixture setups (§22).

### 11.4 Ordering

**AEMIC-REQ-050.** `AuthorityRegistry` defines no enumeration or listing
operation (AEMIC-REQ-042); no ordering requirement therefore applies to
this ABC beyond `resolve`'s own single-value determinism (AEMIC-REQ-043).
If a future concrete implementation exposes an enumeration method on its
own additional (non-ABC) surface for operational/debugging purposes, this
contract does not constrain its ordering — restating that such a method is
outside this ABC's own frozen shape (§3.3).

### 11.5 Named limitation: authoring-time immutability is not `resolve`-time enforceable

**AEMIC-REQ-051.** This contract confirms, as a named limitation (not a
defect): `resolve` itself has no mechanism to detect or prevent a
concrete Registry's own backing store from having been mutated in place
by an out-of-band process bypassing this package's own (non-existent, in
v1.0) authoring API — AEM-REQ-008's immutability guarantee is a discipline
this contract requires of a future authoring workflow (§3.3's deferred
concern), not a property `resolve` can mechanically verify at lookup time.
A future Implementation Contract revision governing the authoring
workflow itself (§17, §21) is the correct place to close this fully; this
contract discloses it rather than mechanically closing it, per Phase
147D §6.4's own identical disclosure.

---

## 12. Filesystem Persistence Contract (for the deferred concrete Registry)

This section freezes the persistence contract a future, separately
governed implementation phase MUST follow if and when it builds a
concrete filesystem-backed `AuthorityRegistry` (§3.3). None of this
section is built by this contract's own freeze.

**AEMIC-REQ-052.** Storage root: `.pcae/authority-declarations/` — a new,
dedicated root, distinct from `CHGR_STORAGE_PREFIX`
(`.pcae/governance-records/`) and `SessionRepository`'s own root
(`.pcae/decision-sessions/`). A concrete implementation's own constructor
MUST reject, at construction time, a supplied root that overlaps either
existing prefix — mirroring `FilesystemSessionRepository.__init__`'s own
`_paths_overlap` guard against `CHGR_STORAGE_PREFIX` exactly (same pattern,
new prefix pair).

**AEMIC-REQ-053.** Record layout: one JSON document per
`(template_ref, template_version)` pair, filename deterministically derived
from both values through a validated-identifier discipline mirroring
`SessionRepository`'s own `_validated_path`/`validate_session_id` pattern:
reject any component containing `/`, `\`, or `..`; confirm the resolved
path's parent directory equals the storage root exactly; reject symlinks on
every read and write. This is a **reuse of the pattern**, never an import
of `interactive_workflow.persistence`'s own private helpers (which would
create the exact unwanted cross-package dependency AEMIC-REQ-010 forbids) —
a future implementation phase MUST reimplement the pattern independently
within `pcae.authority_evaluation`'s own module boundary.

**AEMIC-REQ-054.** Atomic-write method: `tempfile.mkstemp` in the same
directory as the target file, write + flush + `os.fsync`, then
`os.replace` onto the final path, with a `finally`-block temp-file cleanup
— mirroring `FilesystemSessionRepository._write_atomic` and
`governance/publication/storage.py`'s `_write_atomic_json` exactly, an
already-proven pattern in this codebase.

**AEMIC-REQ-055.** Temporary-file handling: the temp file MUST be created
in the same directory as its eventual final path (never a system temp
directory), so `os.replace` is guaranteed atomic on a POSIX filesystem;
the temp file MUST be removed in a `finally` block regardless of success or
failure of the write.

**AEMIC-REQ-056.** Replacement semantics: `resolve` (a read-only operation)
never triggers a write; whatever future authoring path a concrete
implementation exposes on its own additional surface MUST refuse to
overwrite an already-existing file for the same `(template_ref,
template_version)` pair (restating AEMIC-REQ-045's uniqueness requirement
at the storage layer) — an authoring-time refusal-to-overwrite check, not a
`resolve`-time one.

**AEMIC-REQ-057.** Path traversal and symlink rejection: restating
AEMIC-REQ-053; both the storage root itself and every individual record
path MUST be checked for symlink status before any read or write, raising
`AuthorityRegistryUnavailableError` on a positive symlink check — mirroring
`FilesystemSessionRepository._reject_symlink`/`_ensure_root` exactly.

**AEMIC-REQ-058.** Malformed-record isolation: a single malformed record
file (unparseable JSON, wrong `schema_version`, missing required field)
encountered during a `resolve` call for that specific
`(template_ref, template_version)` pair MUST raise
`AuthorityRegistryCorruptError` scoped to that lookup; it MUST NOT corrupt,
invalidate, or affect the readability of any other record file in the same
storage root.

**AEMIC-REQ-059.** Restart equivalence: a concrete implementation MUST
produce identical `resolve` results across process restarts for the same
on-disk state — no in-memory-only state exists that would make a fresh
process see different results than the process that most recently wrote a
record (restating AEM-REQ-012's purity guarantee at the process-lifecycle
level).

**AEMIC-REQ-060.** Concurrent-write expectations: restating
`SessionRepository`'s own disclosed "no locking primitive... last-write-wins
as a disclosed, non-authority-relevant race" discipline — a future concrete
implementation is not required to implement file locking; a race between
two concurrent authoring attempts for the same identity tuple is an
accepted, disclosed limitation (and, per AEMIC-REQ-056, the *second*
concurrent writer's attempt SHOULD be rejected by the refuse-to-overwrite
check on a best-effort basis, not guaranteed atomic across the check-then-
write gap without an explicit locking primitive this contract does not
require).

**AEMIC-REQ-061.** Crash recovery: an interrupted write (process killed
mid-write) MUST leave either the prior valid record file or no file at all
— never a partially-written file at the final path — guaranteed by the
`mkstemp`-then-`os.replace` pattern (AEMIC-REQ-054) exactly as it already
guarantees this for `FilesystemSessionRepository`.

**AEMIC-REQ-062.** Read-after-write: a `resolve` call immediately following
a successful authoring write for the same identity tuple, within the same
process or a fresh one, MUST return the just-written Declaration (no
write-behind caching, restating AEMIC-REQ-042's no-caching architecture).

**AEMIC-REQ-063.** `schema_version` at the storage layer: a concrete
implementation MAY define its own store-level schema version (e.g.
`STORE_SCHEMA_VERSION = "authority-declaration-store/1.0"`), independent of
and in addition to `EligibleAuthorityDeclaration.schema_version` itself —
mirroring `FilesystemSessionRepository`'s own `STORE_SCHEMA_VERSION` vs.
`Session.schema_version` distinction exactly.

---

## 13. Failure Taxonomy

### 13.1 Structural (malformed-input) failures

**AEMIC-REQ-064.** `pcae.authority_evaluation.errors` SHALL define a base
`AuthorityEvaluationError` and, as its own direct subclasses, at minimum:

| Exception | Condition | Retryable | Domain or infrastructure |
|---|---|---|---|
| `InvalidClaimedIdentityError` | `claimed_identity` empty or not a `str` | No | Domain (caller error) |
| `InvalidTemplateReferenceError` | `template_ref` or `template_version` empty or not a `str` | No | Domain (caller error) |
| `MalformedDeclarationError` | A resolved `EligibleAuthorityDeclaration`'s own `eligible_identities` is empty, or another construction-time invariant is violated (AEMIC-REQ-017, AEMIC-REQ-022, AEMIC-REQ-039) | No | Domain (caller/authoring error) |
| `UnsupportedSchemaVersionError` | A payload's `schema_version` does not match a known value at deserialization (§18, AEMIC-REQ-041) | No | Domain (stale/incompatible payload) |
| `MissingCitationTextError` | `evaluate`'s own internally-computed `evaluation_result` is `ELIGIBLE` but the caller-supplied `citation_text` parameter (§5, AEMIC-REQ-019) is `None` (§14, AEMIC-REQ-101) | No | Domain (caller error) |

None of these SHALL be silently substituted with a default result — every
condition above MUST raise, never return a fabricated `AuthorityEvaluationOutcome`
or a fabricated `EligibleAuthorityDeclaration` (restating AEM-REQ-023,
AEM-REQ-032's fail-closed discipline).

**AEMIC-REQ-065.** No condition beyond those named at AEMIC-REQ-064 (§13.1)
and §13.2 (below) SHALL raise. In particular: `INDETERMINATE` (no
Declaration) and `INELIGIBLE` (not a member) are both successful
evaluations producing a valid `AuthorityEvaluationOutcome`, never
exceptions — restating AEM-REQ-024 unchanged. A non-`None` `citation_text`
supplied alongside an `INELIGIBLE` or `INDETERMINATE` result is not a
raising condition either (AEMIC-REQ-101): `evaluate` disregards it rather
than raising, since raising on that direction is not necessary to repair
BF-147F-1 and would newly place a raising condition on the two result
paths AEM-REQ-024 requires to always succeed.

### 13.2 Registry (infrastructure) failures

**AEMIC-REQ-066.** `pcae.authority_evaluation.errors` SHALL additionally
define, as its own direct subclasses of `AuthorityEvaluationError`:

| Exception | Condition | Retryable | Domain or infrastructure |
|---|---|---|---|
| `AuthorityRegistryUnavailableError` | The Registry's own storage layer could not be consulted at all (§11.3, AEMIC-REQ-047) | Caller-dependent (this package expresses no retry policy of its own) | Infrastructure |
| `AuthorityRegistryCorruptError` | The Registry's own storage layer answered but the record is structurally malformed or a duplicate/conflict was detected (§11.3, §11.2, AEMIC-REQ-048, AEMIC-REQ-045) | No | Infrastructure (or authoring-time defect) |

**AEMIC-REQ-067.** These two exceptions are architecturally distinct from
§13.1's four exceptions along exactly one axis this contract requires be
testable: §13.1 exceptions are raised by `pcae.authority_evaluation.models`/`evaluation`
against caller-supplied, well-formed-or-not inputs; §13.2 exceptions are
raised exclusively by a concrete `AuthorityRegistry` implementation's own
`resolve` method, never by `evaluate` itself (which never touches storage,
§14).

### 13.3 Path-safety and invariant-violation failures

**AEMIC-REQ-068.** A concrete Registry implementation MUST raise
`AuthorityRegistryUnavailableError` for a detected path-traversal or
symlink-escape attempt (§12, AEMIC-REQ-057) — classified as an
infrastructure-layer refusal, not a domain error, since the caller supplied
well-formed `template_ref`/`template_version` values and the failure
originates in the storage layer's own safety check.

**AEMIC-REQ-069.** An internal invariant violation not otherwise named
above (e.g. a constructed `AuthorityEvaluationOutcome` somehow failing its
own `citation_text` if-and-only-if invariant, AEMIC-REQ-022, despite
passing every named precondition) SHALL raise a generic
`AuthorityEvaluationError` directly (the base class itself, never silently
ignored) — this is the sole permitted use of the base exception class
directly, reserved for conditions this contract's own §13.1/§13.2
enumeration did not anticipate; a future revision naming a recurring such
condition SHOULD promote it to a named subclass via this contract's own
Amendment process (§21).

### 13.4 No generic collapse

**AEMIC-REQ-070.** No condition named at §13.1–§13.3 above SHALL be
collapsed into a single generic `ValueError`, `RuntimeError`, or bare
`Exception` where a more specific type above already exists — restating
Phase 147D §6.5's own reasoning: a small number of named, distinguishable
exception types maps more legibly onto a future CLI/transport layer's own
closed error taxonomy (AEM-REQ-025) than one generic type would.

**AEMIC-REQ-071.** A raised failure from this package SHALL map, at
whatever future CLI/transport surface eventually invokes evaluation, to
that surface's own existing closed error taxonomy (IWPC-001 §19) — this
package defines the failure *condition* and its own exception hierarchy,
never a new error-rendering vocabulary for a CLI it does not itself expose
(restating AEM-REQ-025 unchanged).

---

## 14. Evaluation Function Contract

**AEMIC-REQ-072.** `pcae.authority_evaluation.evaluation.evaluate` SHALL be
a module-level function (not a method on a stateful class) with the
signature implied by §5:

```
evaluate(
    claimed_identity: str,
    declaration: EligibleAuthorityDeclaration | None,
    evaluated_at: str,
    evaluator_version: str,
    citation_text: str | None = None,
) -> AuthorityEvaluationOutcome
```

**AEMIC-REQ-073.** `evaluate` has **no Registry dependency**: it never
calls `AuthorityRegistry.resolve` itself, never imports
`pcae.authority_evaluation.registry`, and never performs any I/O of any
kind. The Registry lookup is always performed by `evaluate`'s own caller,
upstream, exactly once, with the result passed in as the `declaration`
parameter — restating Phase 147D §5.2's "the evaluation function itself
never calls the Registry" architecture as a binding requirement, and the
mechanism that makes `evaluate`'s own unit tests require no Registry
fixture, filesystem, or mock of any kind (§22).

**AEMIC-REQ-074.** `evaluate` SHALL be total and non-raising for every
well-formed input (§13.1's exceptions are reserved for malformed input
only) — restating AEM-REQ-016 unchanged: `INDETERMINATE` and `INELIGIBLE`
are successful returns, never exceptions. Per AEM-REQ-023's own precedent
(a structurally invalid Declaration, e.g. an empty `eligible_identities`
set, is itself classified as malformed input despite superficially
resembling a substantive result), a `citation_text` that is `None` when
`evaluate`'s own internal determination of `evaluation_result` is
`ELIGIBLE` is classified as malformed input, not a substantive result:
the caller has supplied an incomplete construction request for the
specific outcome shape AEM-REQ-018/AEMIC-REQ-021-022 require, exactly as
an empty `eligible_identities` set is an incomplete Declaration rather
than a valid `ineligible`-implying one. AEMIC-REQ-101 states this
condition and its own exception precisely.

**AEMIC-REQ-075.** `evaluate` SHALL be deterministic: identical
`(claimed_identity, declaration, evaluated_at, evaluator_version,
citation_text)` inputs SHALL always produce a field-identical
`AuthorityEvaluationOutcome` — restating AEM-REQ-009 unchanged, at the
function-signature level.

**AEMIC-REQ-076.** `evaluate` SHALL have no side effects: it SHALL NOT
mutate its own `declaration` argument (already guaranteed by
`EligibleAuthorityDeclaration`'s own immutability, AEMIC-REQ-018), SHALL
NOT write to any file, log, or external system, and SHALL NOT persist
anything. This package defines no logging requirement of its own beyond
what a caller chooses to do with the returned outcome — restating Phase
147D §5.10.2's own "this phase does not architect a durable outcome log as
a requirement" disposition as this function's own binding non-mutation
contract.

**AEMIC-REQ-077.** `evaluate`'s exception boundary is exactly §13.1's five
named exceptions, plus the base-class fallback at AEMIC-REQ-069 — never
§13.2's Registry-layer exceptions, which `evaluate` cannot raise since it
never touches a Registry (AEMIC-REQ-073).

### 14.1 The `citation_text` construction-time enforcement — repairing BF-147F-1

**AEMIC-REQ-101.** `evaluate` SHALL enforce, as the sole binding mechanism
that makes AEMIC-REQ-022's if-and-only-if invariant satisfiable for the
`eligible` case — repairing Finding BF-147F-1 (Phase 147F):

1. `evaluate` first determines `evaluation_result` exactly as §7
   (AEMIC-REQ-024) already specifies, from exactly the two evidentiary
   inputs AEM-REQ-016 names (`claimed_identity`, `declaration`) — the
   `citation_text` parameter plays no role in this determination, so
   `evaluation_result`'s own purity/determinism (AEMIC-REQ-075) is
   unaffected by whatever `citation_text` value is supplied.
2. If the resulting `evaluation_result` is `ELIGIBLE` and `citation_text`
   is `None`, `evaluate` SHALL raise `MissingCitationTextError` (§13.1)
   before constructing any `AuthorityEvaluationOutcome` — this is the
   specific, previously-missing enforcement point BF-147F-1 identified as
   absent; no well-formed call can now produce an `ELIGIBLE` outcome
   lacking a citation.
3. If the resulting `evaluation_result` is `ELIGIBLE` and `citation_text`
   is non-`None`, `evaluate` SHALL construct the outcome with
   `citation_text` copied verbatim (AEMIC-REQ-031).
4. If the resulting `evaluation_result` is `INELIGIBLE` or
   `INDETERMINATE`, `evaluate` SHALL construct the outcome with
   `citation_text=None` regardless of what value (if any) the caller
   supplied for the `citation_text` parameter — restating AEMIC-REQ-065's
   own "not a raising condition" disposition: a non-`None` value supplied
   here is disregarded, not fabricated into the outcome and not treated
   as caller error, since raising on this direction is not necessary to
   repair BF-147F-1 (§25 records this as the deliberately minimal scope
   of this repair).

`AuthorityEvaluationOutcome`'s own construction-time invariant
(AEMIC-REQ-022) remains the final, independent enforcement point
regardless of `evaluate`'s own behavior above — `evaluate` can no longer
attempt a construction that invariant would reject, but the invariant
itself is unchanged and unweakened by this repair.

---

## 15. Security Contract

**AEMIC-REQ-078.** This package SHALL preserve, without weakening, every
security property AEM-001 §9 (of the Contract Freeze) already establishes,
restated at the implementation level:

| Property | Implementation-level requirement |
|---|---|
| Declaration spoofing | `eligible_identities` is a closed, literal-`str` set (§4); no wildcard, regex, or role-indirection membership test is implemented (§14's `evaluate` performs exact set-membership only) |
| Template substitution | `resolve`'s own two-argument signature requires an exact `(template_ref, template_version)` match (§11.1); no partial or fuzzy match is implemented |
| Declaration substitution | `AuthorityEvaluationOutcome` carries `declaration_ref` (§10.2) referencing exactly the Declaration actually evaluated against — a future verifier can confirm no substitution occurred (§16) |
| Stale declarations | `EligibleAuthorityDeclaration`'s language-level immutability (AEMIC-REQ-018) combined with AEM-REQ-008's authoring-time discipline (AEMIC-REQ-051's named limitation notwithstanding) |
| Replay | `AuthorityEvaluationOutcome` is immutable once produced (AEMIC-REQ-023); `evaluate` is a pure function, so there is no stateful "replay" concept at this package's own layer to exploit |
| Duplicate ambiguity | `resolve` MUST raise `AuthorityRegistryCorruptError`, never silently first-match, on a detected duplicate (AEMIC-REQ-045) |
| Path traversal / symlink escape | §12's persistence contract requires rejection of both, for whichever future concrete Registry implementation exists (AEMIC-REQ-053, AEMIC-REQ-057) |
| Registry poisoning | The ABC exposes no write path at all (AEMIC-REQ-042); a future concrete implementation's own authoring-time access control is the correct enforcement point, outside this package's own `resolve`-path scope (§11.5) |
| Unauthorized mutation | No mutation method exists on any public type in this package (§4, §6, §11) |
| Authority escalation | Disclosure-only naming/semantics (§8) forecloses any type or function implying grant/deny; this package has zero import-path reach into Runtime, Permission Broker, or any execution-capability code (§3.4) |
| Circular trust | `EligibleAuthorityDeclaration.declared_by` is recorded for provenance only, never itself evaluated (AEM-REQ-013) — a disclosed, unclosed gap this contract does not attempt to close (restating AEM-001 §14 D-7 and Phase 147D §9's identical disclosure) |
| Outcome misuse as authorization | §8's naming/documentation requirements (AEMIC-REQ-027) are the mitigation; this package's own public API surface contains no function whose name or return type could be reasonably mistaken for an authorization primitive |

**AEMIC-REQ-079.** No security property is weakened relative to AEM-001 or
Phase 147D's own architecture by any requirement in this contract. The one
disclosed, unclosed gap (Declaration-authorship circular trust) is named,
not hidden, restating AEM-001 §14 D-7 unchanged.

**AEMIC-REQ-102.** Caller-controlled citation fabrication (the risk Phase
147F's §18 named as the practical consequence of BF-147F-1) is **not**
newly introduced or worsened by this repair. Before this repair, no
channel existed for a caller to supply `citation_text` to `evaluate` at
all — the only way to produce an `ELIGIBLE` outcome carrying one was to
bypass `evaluate` entirely and construct `AuthorityEvaluationOutcome`
directly, which defeats every enforcement point this package defines
(AEMIC-REQ-022's invariant is `AuthorityEvaluationOutcome`'s own
constructor-level check and remains reachable that way regardless, but
`evaluate`'s own determination of `evaluation_result`, AEMIC-REQ-101, is
not). After this repair, a caller still supplies `citation_text` — now
through `evaluate`'s own fifth parameter — and this package still cannot
verify that value against the Decision Template's own `eligible_authority`
field, because no `DecisionTemplate` artifact exists for it to check
against (AEMIC-REQ-032's disclosed, unclosed limitation, unchanged by this
repair). The improvement this repair makes is narrower and real: a caller
can no longer produce a well-formed `ELIGIBLE` outcome through `evaluate`
*without* supplying some `citation_text` value (AEMIC-REQ-101 raises
`MissingCitationTextError` otherwise), and `evaluation_result` itself
remains entirely uninfluenced by whatever `citation_text` value is
supplied (§14.1). Whether the supplied text is the *correct* citation
remains, exactly as before, a caller-workflow discipline this package does
not itself verify — the same disclosed gap AEMIC-REQ-032/033 already name,
not a new one this repair creates.

---

## 16. Auditability

**AEMIC-REQ-080.** Every field on `AuthorityEvaluationOutcome` (§6) is
**stable** (part of the outcome's own deterministic identity, per
AEMIC-REQ-075) except `evaluated_at`, which is **observational** (records
when evaluation occurred; two evaluations with otherwise-identical inputs
but different `evaluated_at` timestamps are both valid, independently
correct outcomes — `evaluated_at` is not itself part of the
determinism guarantee AEMIC-REQ-075 requires, since a caller supplies it
per-call, not derived from the other inputs).

**AEMIC-REQ-081.** The minimum auditable evidence an
`AuthorityEvaluationOutcome` MUST expose is exactly its own eight fields
(§6) — restating AEM-REQ-030: `template_ref`/`template_version` (Decision
Template identity), `claimed_identity` (the evaluated identity),
`evaluation_result` (the outcome), `declaration_ref` (which Declaration, if
any, was evaluated against), `citation_text` (the disclosed citation, if
`eligible`), `evaluated_at` (when), `evaluator_version` (which contract
version), and `schema_version`. No additional field (a registry
implementation identity, a reason code beyond `evaluation_result` itself)
is required by this contract for v1.0 — a future revision MAY add one
additively (§21) if a future implementation phase demonstrates a concrete
audit need beyond what these eight fields already support.

**AEMIC-REQ-082.** This restates AEM-REQ-030's own reconstructibility
guarantee, unchanged, at this package's own level: given a persisted
`AuthorityEvaluationOutcome` (or, downstream, a CHGR's own
`authority_basis_claimed` citation plus the session's `template_ref`/
`template_version`), a future verifier SHALL always be able to determine
what the evaluation claims to have been based on — contingent on the
Declaration itself remaining Registry-resolvable, an availability guarantee
this contract does not itself make (restating AEM-REQ-030's own disclosed
caveat unchanged; §3.3's deferred concrete Registry mechanics govern actual
availability).

---

## 17. Deferred Integration Boundary

**AEMIC-REQ-083.** Restating Finding FA-147D-1 as a binding boundary: the
first implementation authorized under this contract does **not**:

- widen `IWC-001`'s `Session` or `PublicationReadinessPackage`;
- add any authority-evaluation field to
  `PublicationReadinessPackage`, `Session`, or any other IWC-001-owned
  type;
- modify PEC-001, `governance/publication/coordinator.py`, or
  `governance/publication/record.py`;
- populate `authority_basis_claimed` on any CHGR record;
- modify `human_governance_record.schema.json`, `decision_template.schema.json`,
  or any other schema file;
- modify Publication verification, inspection, or the CHGR construction
  path in any way;
- gate, block, or otherwise condition Confirmation, Readiness,
  Authorization, or Publication on anything this package computes;
- change Interactive Workflow behavior, Session state transitions, or any
  CLI/transport surface.

**AEMIC-REQ-084.** The likely future integration sequence (planning only,
not authorized by this contract) is, restating the governing prompt's own
sequence and Phase 147D §10's rollout order:

1. Implementation of `pcae.authority_evaluation` per this contract (the
   phase this contract makes possible, not itself authorized here).
2. Standalone independent verification of that implementation against
   this contract (mirroring 147C's own role relative to AEM-001).
3. A separately-governed IWC-001 minor-revision contract amendment
   widening `Session`/`PublicationReadinessPackage` (mirroring Phase 144F's
   own IWC-REQ-185 precedent).
4. Independent verification of that IWC-001 amendment.
5. Implementation of the Interactive Workflow transport wiring the
   evaluation call into a Session-state-transition command.
6. A separately-governed PEC-001/`record.py` consumption-contract
   amendment reading the widened Package's new field(s).
7. Implementation of that consumption change.
8. End-to-end independent verification of the full "Decision Template
   declares eligible authority → published CHGR discloses
   `authority_basis_claimed`" path.

**AEMIC-REQ-085.** Nothing in AEMIC-REQ-084's sequence is authorized by
this contract; it is disclosed planning context only, restating the
governing prompt's own explicit instruction that this section is
"planning, not authorization."

**AEMIC-REQ-086.** Existing workflows (every currently-passing
`interactive_workflow`, `governance/publication`, and CHGR-construction
test) SHALL continue to operate unchanged, with unchanged output, until a
separately-authorized integration phase (AEMIC-REQ-084 steps 3+) actually
modifies them — restating AEM-REQ-037's "Publication SHALL remain fully
operable... exactly as it does today" one layer more concretely, as a
regression-test-level requirement (§22).

---

## 18. Serialization and Digest Contract

**AEMIC-REQ-087.** `pcae.authority_evaluation.serialization` SHALL define
`to_payload`/`from_payload` pairs for both `EligibleAuthorityDeclaration`
and `AuthorityEvaluationOutcome`, mirroring
`interactive_workflow.serialization`'s own per-schema submodule pattern.

**AEMIC-REQ-088.** Canonical JSON encoding: `to_payload` SHALL produce a
`dict` suitable for `json.dumps(..., sort_keys=True)` — keys in a
stable, alphabetically-sortable order at the `json.dumps` call site (not
necessarily insertion order in the `dict` itself, since `sort_keys=True` at
the serialization boundary is the actual determinism guarantee, mirroring
`FilesystemSessionRepository._write_atomic`'s own `json.dumps(payload,
indent=2, sort_keys=True, default=str)` call exactly).

**AEMIC-REQ-089.** Whitespace/formatting is a storage-layer concern (§12),
not this module's own concern: `to_payload` returns a plain `dict`;
whichever concrete Registry implementation eventually serializes it to
bytes decides indentation, mirroring the existing repository-wide
separation between "serialize to payload" (per-schema modules) and
"serialize payload to bytes" (storage modules) exactly.

**AEMIC-REQ-090.** Unicode handling: no ASCII-only restriction is imposed;
`eligible_identities` members, `declared_by`, and `citation_text` (carried
via `AuthorityEvaluationOutcome`, not stored on `EligibleAuthorityDeclaration`
itself per AEMIC-REQ-031) MAY contain arbitrary Unicode, round-tripped
byte-for-byte through `to_payload`/`from_payload`.

**AEMIC-REQ-091.** Omitted versus `null` fields: every field defined at §4
and §6 is mandatory (no optional field exists in v1.0's closed shape,
AEMIC-REQ-016); `to_payload` SHALL always emit every field, and
`from_payload` SHALL raise (a typed error, §13.1) if any required field is
missing or `null` in the input payload — there is no field for which
"omitted" and "`null`" carry different meaning in v1.0, since none is
optional.

**AEMIC-REQ-092.** No digest (cryptographic hash) is required over either
record type in the first implementation. This is a deliberate, disclosed
non-requirement, not an oversight: neither AEM-001 nor Phase 147D's own
architecture names a digest requirement for either record type (contrast
with CHGR-001's own digest-binding discipline, a distinct artifact class
this package does not produce); introducing one here would add a
cryptographic requirement with no architectural justification this
contract can independently derive. The resulting limitation — a
Declaration or Outcome payload could be tampered with in transit or at
rest without this package itself detecting it — is accepted for v1.0
because: (a) `AuthorityEvaluationOutcome`'s reconstructibility (§16)
already relies on the Registry's own storage-layer integrity (§12), a
separate concern; (b) the outcome's only currently-authorized downstream
consumer path (a future, separately-governed CHGR integration, §17) would
inherit whatever digest-binding discipline CHGR-001 itself already applies
to the record it eventually becomes part of, making a second, redundant
digest at this package's own layer non-additive. A future revision MAY
introduce a digest requirement (§21) if a future implementation or
integration phase demonstrates a concrete need this reasoning does not
anticipate.

**AEMIC-REQ-093.** `from_payload` SHALL verify `schema_version` before
attempting to construct any other field (restating AEMIC-REQ-041), so a
version mismatch is reported precisely (`UnsupportedSchemaVersionError`)
rather than manifesting as a confusing downstream field-validation error.

---

## 19. No-Go Boundary Confirmation

**AEMIC-REQ-094.** This phase (147E) SHALL NOT, and did not:

- modify `src/pcae/**` (no file under `src/pcae/authority_evaluation/`
  exists after this phase; it is not created by this phase);
- modify `tests/**`;
- modify any schema file under `src/pcae/schema_resources/**`;
- modify AEM-001, IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001,
  TAMPC-001, or GAC-001 — all confirmed byte-for-byte unmodified (§20.4);
- implement `pcae.authority_evaluation` or any concrete Registry;
- create a Registry;
- migrate any Decision Template;
- change `Session`, `PublicationReadinessPackage`, or
  `PublicationCoordinator`;
- change CHGR construction, verification, or inspection;
- gate Publication;
- enable execution capability of any kind;
- change runtime state, policy, or strategic lineage.

Only this contract (`docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`),
the Phase 147E report, and ordinary governance bookkeeping (task/phase
lifecycle files, `PROJECT_STATUS.md`, `.pcae/phase-completion-*`) are
authorized to be created or modified by this phase — confirmed by
`git status --short` before and after this phase's own writing (Phase
147E report §25).

---

## 20. Contract Quality Review

**AEMIC-REQ-095.** Before freezing, this contract confirms itself:

- **Internally coherent** — no requirement above contradicts another. This
  bullet's v1.0 text was itself falsified by Phase 147F's independent
  verification (BF-147F-1: §5/§14's closed evaluate() signature provided
  no channel for `citation_text`, making §6.1's own invariant
  unsatisfiable for the `eligible` case) — repaired at §14.1
  (AEMIC-REQ-101, Phase 147E.1, §25). With `citation_text` now `evaluate`'s
  own fifth parameter, the `citation_text` if-and-only-if invariant (§6.1)
  and the three-value closed enum (§7) together make every
  `AuthorityEvaluationOutcome` shape fully determined by its own
  `evaluation_result`, and that shape is now reachable via `evaluate`
  itself for every one of the three results, not merely constructible
  in the abstract.
- **Complete enough to implement** — every module named at §3.2 has a
  fully specified public shape (§4–§7, §11, §13, §14, §18); the one
  deferred module (a concrete Registry, §3.3) is deferred by an explicit,
  reasoned decision, not left unspecified by omission — its own eventual
  contract is pre-frozen at §12 for whichever future phase builds it.
- **Deterministic** — `evaluate` (§14) and `resolve` (§11.1) are both
  required to be pure functions of their own inputs.
- **Testable** — every requirement above is either directly restated in
  §22's Requirement/Test Matrix or is itself a scoping/no-go statement
  (§2, §19) not requiring its own positive test.
- **Security-preserving** — §15 confirms no AEM-001 security property is
  weakened; the one disclosed gap (circular trust, declaration authorship)
  was already disclosed at AEM-001 §14 D-7, not newly introduced.
- **Compatible** — §17/§19 confirm zero required modification to any
  existing file; §17.086 (AEMIC-REQ-086) requires existing behavior to
  remain unchanged until a separately-governed integration phase.
- **Independent of downstream integration** — §3.4/§3.5's forbidden-import
  and zero-dependency-direction rules make this package buildable, testable,
  and mergeable with zero coupling to any future IWC-001/PEC-001 revision.
- **Free of hidden runtime or authority expansion** — §3.4 (AEMIC-REQ-010/012)
  and §8 (AEMIC-REQ-027/028) jointly foreclose any import-path or
  naming-level route to Runtime, Permission Broker, or authorization
  capability.

**AEMIC-REQ-096.** Unresolved implementation-critical decisions: **none**.
Every decision the governing prompt's own §2–§18 sections ask this
contract to resolve unambiguously has been resolved at §1.1 (147D-choice
classification), §3.3 (concrete Registry deferral), §9 (citation-source
reconciliation and its own named, non-mechanically-closed drift
limitation), §11.2–§11.3 (duplicate/conflict/availability semantics), and
§18 (digest non-requirement, with reasoning). The two items explicitly
left open — how a future caller obtains citation text absent a
`DecisionTemplate` artifact (AEMIC-REQ-032), and consistency validation
between free text and `eligible_identities` (AEMIC-REQ-034) — are each a
**named, disclosed limitation with a stated reason it is safe to defer**,
not an unresolved implementation-critical choice this contract failed to
make; both are, in any case, outside `pcae.authority_evaluation`'s own
package boundary (§2.2), belonging respectively to a future Decision
Template authoring workflow and this contract's own explicit
non-mechanism at AEMIC-REQ-034.

---

## 21. Amendment Contract

**AEMIC-REQ-097.** AEMIC-001 MAY evolve only through a governed superseding
contract revision (a future phase producing a revised
`AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md` with an incremented
version and an explicit revision-history section), never through an
implementing phase's own discretion — mirroring AEM-001 §13, PEC-001,
IWPC-001, and CHGR-001's own amendment discipline exactly.

**AEMIC-REQ-098.** A revision MAY be additive (a new optional field, a new
extension point, a newly-authorized concrete Registry module) without
renumbering any existing `AEMIC-REQ-###`; a revision narrowing or removing
an existing guarantee MUST be a major version and MUST retain retired
requirement identifiers in place, marked "Retired," never reused.

**AEMIC-REQ-099.** Any AEM-001 revision (via its own §13 Amendment
Contract) that changes a requirement this contract restates one layer more
concretely (e.g. AEM-REQ-020's three-value enum) SHALL trigger a
corresponding AEMIC-001 revision before any implementation phase proceeds
against the changed AEM-001 provision; until such a revision is frozen,
AEMIC-001 v1.0 continues to govern implementation exactly as written,
restating AEM-001's own text rather than a hypothetical future one.

---

## 22. Requirement / Test Matrix

Every normative requirement above maps to at least one positive test, and,
where a failure condition exists, at least one negative or adversarial
test. This matrix is the authoritative enumeration; §1–§21's narrative
prose explains the reasoning behind each row.

| Req(s) | Behavior | Positive test | Negative/adversarial test | Component | Deferred dependency |
|---|---|---|---|---|---|
| AEMIC-REQ-015-018 | `EligibleAuthorityDeclaration` construction | Valid six-field construction succeeds; frozen/immutable | Empty `template_ref`/`template_version`/`eligible_identities` each raise; extra field rejected | `models.py` | none |
| AEMIC-REQ-021-023 | `AuthorityEvaluationOutcome` construction | Valid eight-field construction succeeds for each of the three `evaluation_result` values | `citation_text` present with non-`eligible` result raises; `citation_text` absent with `eligible` result raises (both directly against `AuthorityEvaluationOutcome`'s own constructor, and reachable through `evaluate` per AEMIC-REQ-101 below) | `models.py` | none |
| AEMIC-REQ-024-026 | `EvaluationResult` closed enum | Three members constructible and comparable | A fourth/unknown string does not coerce to a valid member | `models.py` | none |
| AEMIC-REQ-072-077, AEMIC-REQ-101 | `evaluate` purity/totality/determinism, and `citation_text` construction-time enforcement (repairs BF-147F-1) | Table test over `(claimed_identity, declaration, citation_text)` → expected outcome for all three results; an `eligible`-yielding call with a non-`None` `citation_text` succeeds and carries it verbatim; repeated identical calls (including identical `citation_text`) produce field-identical outcomes | No Registry/filesystem import reachable from `evaluation.py` (AST-style import-boundary test, mirroring `_FORBIDDEN_IMPORT_ROOTS`); an `eligible`-yielding call with `citation_text=None` raises `MissingCitationTextError`; an `ineligible`/`indeterminate`-yielding call supplied a non-`None` `citation_text` succeeds and produces `citation_text=None` on the outcome (disregarded, not raised, not fabricated) | `evaluation.py` | none |
| AEMIC-REQ-042-044 | `AuthorityRegistry.resolve` contract | In-memory test double returns a Declaration or `None` per fixture | `resolve` never raises for "no Declaration"; ABC cannot be instantiated directly (abstract) | `registry.py` + test double | none |
| AEMIC-REQ-045-046 | Duplicate/historical-version handling | A test-double Registry with two distinct `template_version`s for the same `template_ref` resolves each independently | A test-double Registry simulating a duplicate for one identity tuple triggers `AuthorityRegistryCorruptError` when a future concrete implementation is built | `registry.py` (ABC-level contract); concrete enforcement | concrete Registry implementation |
| AEMIC-REQ-047-049 | Registry-unavailable vs. corrupt vs. `None` | Three independently constructed fixtures (unreachable path, malformed JSON, absent record) each produce the correct one of the three distinct outcomes | Confusing any two of the three is the failure mode this test suite must positively rule out | concrete Registry implementation | concrete Registry implementation |
| AEMIC-REQ-052-063 | Filesystem persistence (atomicity, path safety, restart equivalence) | Round-trip write/read across simulated process restart; atomic-write verified via crash-injection (kill mid-write leaves prior state) | Path traversal (`../`), symlink target, oversized/malformed record each rejected | concrete filesystem Registry | concrete Registry implementation |
| AEMIC-REQ-064-071, AEMIC-REQ-101 | Failure taxonomy completeness and non-collapse | Each of the seven named exceptions (five §13.1, two §13.2) independently triggerable from a distinct fixture, including `MissingCitationTextError` | No condition maps to a bare `ValueError`/`Exception` where a named type exists (a static/AST check over `errors.py` and every `raise` site) | `errors.py`, `evaluation.py`, `registry.py` | none for §13.1; concrete Registry for §13.2 |
| AEMIC-REQ-027-029 | Disclosure-only naming and semantics | Docstring/naming audit: no `authorize`/`grant`/`permit`/`deny` name exists in the public API | `evaluation_result` alone distinguishes `ineligible` from `indeterminate` in every fixture (never conflated) | whole package | none |
| AEMIC-REQ-010-014 | Forbidden imports / dependency direction | Package imports successfully with zero import of any forbidden root | AST-style test (mirroring `_FORBIDDEN_IMPORT_ROOTS`) asserting no forbidden-root import exists anywhere under `src/pcae/authority_evaluation/**`, and that no file outside this package imports from it yet (a "not wired in" regression guard, restating Phase 147D §11) | whole package + a repository-wide grep/AST test | none |
| AEMIC-REQ-087-093 | Serialization stability | `to_payload`/`from_payload` round-trip for both record types, including non-ASCII members | Missing required field, `null` for a required field, and unrecognized `schema_version` each raise `UnsupportedSchemaVersionError`/a §13.1 exception as appropriate | `serialization.py` | none |
| AEMIC-REQ-086 | No existing-behavior regression | Full existing `interactive_workflow`/`governance/publication`/CHGR test suite passes unchanged after this package's own future implementation lands | N/A (a regression suite, not a new negative test) | whole existing suite | implementation phase itself |
| AEMIC-REQ-083-085 | Deferred integration boundary respected | N/A — a scoping requirement | A future implementation phase's own `git diff` shows zero changes outside `src/pcae/authority_evaluation/**` and its own tests | whole future implementation phase | future implementation phase |

Required future test classes (restating the governing prompt's own list,
each already covered by a matrix row above): model validation; identity
normalization (exact-equality, no normalization, AEMIC-REQ-036); version
handling (schema-version mismatch); declaration lookup; duplicate
ambiguity; conflict handling; registry unavailable; malformed storage;
deterministic evaluation; forbidden imports; serialization stability; path
safety; restart equivalence; disclosure-only boundary; no runtime change;
no publication integration.

---

## 23. Finding Disposition

Reassessed explicitly, per the governing prompt's own instruction not to
silently mark any item resolved without stating how:

| Finding | Origin | Disposition under AEMIC-001 |
|---|---|---|
| **F-147C-1** (dormant free-text `eligible_authority` schema field) | Phase 147C | **Reconciled at the implementation level** (§9, AEMIC-REQ-030-035): the field remains the sole citation-text source; `EligibleAuthorityDeclaration` neither duplicates nor requires it structurally; the reconciliation is now falsifiable via §22's serialization/citation tests. Not newly closed beyond Phase 147D's own architecture-level reconciliation — this contract makes it implementation-testable, nothing more. |
| **F-147C-2** (IWC-001 §6/§11 citation-precision cosmetic defect) | Phase 147C | **Unaffected by this contract; remains open.** This is an AEM-001-identity-block citation-text defect, not an implementation-contract concern; correcting it requires touching AEM-001's own text, which is outside this contract's own No-Go Boundary (§19) and AEMIC-001's own scope (§2.2). Remains open for correction at AEM-001's next amendment opportunity, restating Phase 147D §12's own disposition unchanged. |
| **FA-147D-1** (downstream IWC-001/PEC-001 revisions required to reach a published CHGR) | Phase 147D | **Carried forward as an explicit, binding deferred-integration boundary** (§17, AEMIC-REQ-083-085), not resolved — resolution requires separately-governed contract revisions this contract does not itself perform. |
| **FA-147D-2** (Registry-unavailability failure mode) | Phase 147D | **Closed architecturally through a typed, fail-closed contract** (§11.3, §13.2, AEMIC-REQ-047-049, AEMIC-REQ-066-067): `AuthorityRegistryUnavailableError` and `AuthorityRegistryCorruptError` are now binding, distinct, testable exception types, no longer merely a named observation. |
| **FA-147D-3** (citation/declaration drift risk) | Phase 147D | **Retained as a named limitation with explicit, testable behavior** (§9, AEMIC-REQ-034): this contract does not build a consistency-validation mechanism (a deliberate non-policy-language decision, restating AEM-REQ-004), but requires the limitation itself be surfaced in the first implementation's own documentation and named explicitly in this contract's own findings register — not silently marked resolved. |
| **BF-147F-1** (§5/§14's closed `evaluate()` signature provided no channel for `citation_text`, making §6.1's if-and-only-if invariant unsatisfiable for the `eligible` case; AEMIC-REQ-031 was internally self-contradictory) | Phase 147F | **Repaired** (Phase 147E.1, §25): `citation_text` is now `evaluate`'s own fifth parameter (§5, AEMIC-REQ-019), enforced at construction time by AEMIC-REQ-101 (§14.1). `EligibleAuthorityDeclaration`'s closed six-field shape (AEMIC-REQ-015/016) is unchanged — widening it was considered and rejected as foreclosed by AEM-REQ-007's own closed-shape freeze (§25). No other requirement outside §5, §9, §13.1, §14, §15, §20, §22, §23 was touched by this repair. |
| F-147F-2 (exact `str`-equality identity/version matching, AEMIC-REQ-036, performs no Unicode normalization; fails closed) | Phase 147F | **Unaffected by this repair; remains open.** Not related to BF-147F-1 or `citation_text` in any way; this phase repairs BF-147F-1 only (§25). Remains a disclosed, fail-closed Non-Blocking observation for a future contract revision to address if ever warranted. |
| F-147F-3 (`tests/test_phase_144c_publication_coordinator.py`'s `_FORBIDDEN_IMPORT_ROOTS` does not yet name `pcae.authority_evaluation`) | Phase 147F | **Unaffected by this repair; remains open.** A future implementation phase's own concern (§22's forbidden-import test row already requires an equivalent guard); no text in this contract required correction on account of it. |

**AEMIC-REQ-100.** No finding above is marked resolved without an
accompanying disposition explaining exactly how or why it remains open —
restating the governing prompt's own explicit instruction. No Blocking
finding remains open in this register: BF-147F-1, the sole Blocking
finding ever recorded against this contract, is marked **Repaired** above,
with its own disposition explaining exactly what changed (§25 gives the
full account). F-147F-2 and F-147F-3 remain open, Non-Blocking, and
explicitly out of this repair's own scope.

---

## 24. Non-Goals

Restating AEM-001 §15 one layer more concretely, this contract does not,
and no future phase may treat it as if it did:

- implement `pcae.authority_evaluation`, any concrete Registry, any CLI
  command, or any Publication Coordinator change;
- modify `src/pcae/interactive_workflow/**`, `src/pcae/governance/publication/**`,
  `src/pcae/cltr/**`, any schema file, or any existing contract;
- create engineering execution capability, change Permission Broker
  behavior, change lifecycle authority, change Publication authority, or
  change CHGR ownership;
- gate, block, or otherwise condition Confirmation, Readiness,
  Authorization, or Publication on an evaluation outcome;
- introduce a policy language, role model, scope/time-bounding mechanism,
  or cryptographic digest requirement beyond what §4–§18 explicitly freeze;
- resolve GAC-001 §9's Stage 6 decision or TAMC-001/TAMPC-001's own
  authority model;
- change runtime state or capability.

---

## 25. Phase 147E.1 Repair Confirmation

**Version:** 1.1
**Predecessor:** AEMIC-001 v1.0 (Phase 147E)
**Repaired by:** Phase 147E.1 — Authority Evaluation Model Implementation
Contract Repair

**Reason:** Independently reproduced Finding BF-147F-1 (Phase 147F
Independent Verification, Blocking) — `evaluate()`'s closed, four-parameter
signature (v1.0 AEMIC-REQ-019/020/072) provided no channel for
`citation_text`, and `EligibleAuthorityDeclaration`'s closed six-field
shape (AEMIC-REQ-015/016) carried none either, while v1.0 AEMIC-REQ-022
required every `eligible`-result `AuthorityEvaluationOutcome` to carry a
non-`None` `citation_text`, "enforced at construction time, not left to
caller discipline." No well-formed call to `evaluate()` as v1.0 specified
it could satisfy both requirements simultaneously for the `eligible` case;
v1.0 AEMIC-REQ-031's own text was internally self-contradictory, asserting
in one clause that Declarations "copy the citation text... at evaluation
time" while confirming, in the same paragraph, that no field or parameter
existed to carry it. This defect affects documentation only — no
implementation of `pcae.authority_evaluation` exists (confirmed unchanged
by this phase's own re-inspection, mirroring Phase 147F's own §4), so no
in-flight behavior is corrected; absent this repair, a future implementer
could not have produced a well-formed `eligible` outcome through
`evaluate()` without either violating the closed-parameter rule or
bypassing `evaluate()` entirely to construct `AuthorityEvaluationOutcome`
directly, reopening exactly the caller-controlled-citation-fabrication
risk `evaluate()`'s own invariant enforcement exists to prevent.

**Independent reconstruction (performed before this repair edited
AEMIC-001):** The contradiction was independently re-derived directly from
AEMIC-001 v1.0's own text — the closed parameter list at v1.0
AEMIC-REQ-019/020, the closed six-field Declaration shape at
AEMIC-REQ-015/016, and the if-and-only-if invariant at AEMIC-REQ-022 —
before Phase 147F's own report was consulted a second time for comparison
purposes only. The four affected requirements were confirmed: §5
(evaluation inputs, AEMIC-REQ-019/020), §6.1 (the invariant itself,
AEMIC-REQ-022, sound in isolation and requiring no change), §9 (citation
reconciliation, AEMIC-REQ-030-034, where AEMIC-REQ-031 is the specific
self-contradictory requirement), and §14 (the evaluation function
contract, AEMIC-REQ-072-077, whose signature is the other half of the
contradiction).

**Candidate repairs evaluated:**

1. **Add `citation_text` to `EligibleAuthorityDeclaration`.** Rejected —
   not merely inferior but **foreclosed**: `EligibleAuthorityDeclaration`'s
   six-field shape is frozen one layer up, at AEM-001's own AEM-REQ-007
   ("An Eligible Authority Declaration SHALL carry exactly [six fields]...
   No other field is defined for v1.0"). AEMIC-001's own Contract identity
   and status section states AEMIC-001 "MUST NOT be read as amending,
   narrowing, or superseding AEM-001." Adding a seventh field would do
   exactly that, and would additionally misplace the citation
   semantically: `EligibleAuthorityDeclaration` is authored once per
   `(template_ref, template_version)` and used identically for every
   future evaluation against it (eligible or not), whereas `citation_text`
   is meaningful only for the specific `eligible` outcome of one
   particular evaluation call — carrying it on the Declaration would leave
   it present-but-unused on the (far more common) `ineligible` path,
   inviting exactly the kind of "is this field trustworthy here" confusion
   AEMIC-REQ-022's own invariant exists to foreclose at the outcome level.
2. **Add a `citation_text` channel to `evaluate()`.** Selected (§14.1,
   AEMIC-REQ-101). Preserves `EligibleAuthorityDeclaration`'s AEM-001-frozen
   shape untouched; keeps `evaluation_result`'s own determination a pure
   function of exactly the two evidentiary inputs AEM-REQ-016 names
   (unaffected by the new parameter, since `citation_text` carries no
   evaluative weight); reuses the existing, already-precedented pattern of
   `evaluate()` accepting non-evidentiary pass-through parameters
   (`evaluated_at`, `evaluator_version` already work this way in v1.0);
   requires no widening of the public type surface (no sixth public type);
   is directly and symmetrically testable via the existing §13.1 typed-error
   discipline (a new `MissingCitationTextError`, mirroring the existing
   four exceptions' own shape); and does not require any change to
   `AuthorityEvaluationOutcome`'s own shape or invariant (AEMIC-REQ-021/022
   are untouched).
3. **Alternative reconstruction: a distinct outcome-construction function
   (bypassing `evaluate()`) for the `eligible` case, taking `citation_text`
   directly.** Considered and rejected as strictly worse than option 2 for
   equal cost: it would fragment "the sole specified construction path"
   (AEMIC-REQ-072's own current framing, which BF-147F-1's own analysis
   treated as a load-bearing property) into two paths, weakening rather
   than restoring the "single enforcement point" discipline Phase 147F's
   own §18 named as the very property BF-147F-1's un-repaired state
   threatens; it would also require a second public function name (a
   larger surface-area change) to achieve nothing option 2 does not already
   achieve with one optional parameter.

**Comparison (architectural consistency, API clarity, immutability,
security, caller-controlled citation fabrication risk, compatibility with
AEM-001, compatibility with Phase 147D, future Registry implementation,
future CHGR integration):** Option 2 is the minimum correct repair on
every axis compared: it changes the fewest requirements (§5, §9, §13.1,
§14 only — no change to §4/§6/§7/§10/§11/§12/§17/§18/§24); introduces no
new public type; preserves every existing immutability guarantee
(`EligibleAuthorityDeclaration` and `AuthorityEvaluationOutcome` are both
unchanged in shape); does not alter caller-controlled citation fabrication
risk in either direction (§15, AEMIC-REQ-102 — the pre-existing,
already-disclosed AEMIC-REQ-032/033 limitation is neither closed nor
worsened, since a caller supplied the value under v1.0's intended design
too, merely through an unspecified channel); remains fully compatible with
AEM-001 (AEM-REQ-007's closed Declaration shape is untouched; AEM-REQ-016's
two-evidentiary-input purity guarantee for `evaluation_result` is
untouched); requires no change to Phase 147D's own architecture beyond the
one parameter Phase 147D's own §6.2 did not name (a design gap Phase 147D
left, not a design Phase 147D affirmatively chose and this repair now
contradicts); and is fully forward-compatible with both a future concrete
Registry implementation (§12, entirely unaffected — the Registry never
sees `citation_text`) and a future CHGR integration phase (§17, entirely
unaffected — the deferred-integration boundary is unchanged).

**Selected repair:** Option 2. `citation_text: str | None = None` is added
as `evaluate`'s fifth parameter (§5, AEMIC-REQ-019; §14, AEMIC-REQ-072).
`evaluate` enforces the if-and-only-if invariant itself, before
constructing any outcome (§14.1, AEMIC-REQ-101): raising
`MissingCitationTextError` (a new §13.1 exception) if the internally
determined `evaluation_result` is `ELIGIBLE` and `citation_text` is
`None`; disregarding (never raising on, never fabricating from) a
non-`None` `citation_text` supplied alongside an `INELIGIBLE` or
`INDETERMINATE` result, since enforcing that direction is not necessary to
repair BF-147F-1 and would newly place a raising condition on the two
result paths AEM-REQ-024 requires to always succeed.

**Requirement changes:** AEMIC-REQ-019 (5-parameter table, was 4),
AEMIC-REQ-020 (5-parameter closure, reworded), AEMIC-REQ-031 (rewritten to
remove the self-contradiction — `evaluate` now copies `citation_text`,
not "Declarations"), AEMIC-REQ-032 (light edit: "indirectly through
evaluate's caller" → "directly as evaluate's own fifth parameter";
substance unchanged), AEMIC-REQ-033 (same light edit), AEMIC-REQ-064
(new `MissingCitationTextError` row), AEMIC-REQ-065 (new sentence
disposing of the non-eligible-path non-raising question), AEMIC-REQ-072
(5-parameter signature block), AEMIC-REQ-074 (new sentence classifying the
missing-citation condition as malformed input, mirroring AEM-REQ-023's own
precedent), AEMIC-REQ-075 (determinism tuple extended to include
`citation_text`), AEMIC-REQ-077 ("four" → "five" named exceptions),
AEMIC-REQ-095 (first bullet corrected to record and then resolve the
falsification), §22's Requirement/Test Matrix (three rows updated), §23's
Finding Disposition (three rows added: BF-147F-1 Repaired, F-147F-2 and
F-147F-3 unaffected/open). New requirements added, none reusing an
existing identifier: **AEMIC-REQ-101** (§14.1, the construction-time
enforcement rule) and **AEMIC-REQ-102** (§15, the security-disposition
statement). No requirement identifier was renumbered, reassigned, retired,
or reused. `AEMIC-REQ-015`-`018` (`EligibleAuthorityDeclaration`'s own
shape), `AEMIC-REQ-021`-`029` (`AuthorityEvaluationOutcome`'s shape,
`EvaluationResult`, and disclosure-only semantics), and every requirement
in §10–§13.2, §16–§19, §21, §24 are byte-identical to v1.0.

**Security review (repeated, per the governing prompt's own instruction):**
confirmed the repaired contract prevents caller-controlled citation
fabrication no less than v1.0 intended (§15, AEMIC-REQ-102 — the
pre-existing, disclosed AEMIC-REQ-032/033 gap is unchanged); prevents
fabricated eligible outcomes (`MissingCitationTextError` now closes the
one path BF-147F-1 showed was previously either impossible-to-satisfy or
bypassable); prevents inconsistent declaration/outcome pairs
(`declaration_ref`, AEMIC-REQ-038, is unaffected by this repair); and does
not weaken disclosure-only semantics (§8 is untouched; `evaluate` remains
disclosure-shaped, and `citation_text` is still never itself evaluated,
verified, or treated as evidence of authority — AEMIC-REQ-020's own
restated text above).

**Compatibility review:** confirmed this repair requires no schema change
(no `decision_template.schema.json` or `human_governance_record.schema.json`
field is touched — `citation_text`'s source, the existing free-text
`eligible_authority` field, AEMIC-REQ-030, is unchanged); no runtime change
(§3's package still does not exist under `src/pcae/**`); no IWC-001 change
(§17's deferred-integration boundary, AEMIC-REQ-083-086, is unchanged); no
PEC-001 change (same); does not invalidate AEM-001 (confirmed above — no
AEM-REQ text requires modification, and no AEMIC-001 requirement
post-repair narrows or contradicts any AEM-REQ); and invalidates Phase
147D's own architecture only insofar as Phase 147D's §6.2 did not name a
`citation_text` parameter at all — a gap this repair fills, not a
Phase 147D design choice this repair reverses.

**Finding disposition:** BF-147F-1 is marked **Repaired** (§23). F-147F-2
(Unicode normalization) and F-147F-3 (forbidden-import test not yet
extended) are unrelated to BF-147F-1 and remain open, Non-Blocking, and
out of this repair's own scope (§23) — restating the governing prompt's
own scope instruction ("repair only BF-147F-1").

**No-Go boundary confirmation:** This phase did not modify production
code, tests, schemas, AEM-001, IWC-001, IWPC-001, PEC-001, CHGR-001,
runtime, or any authority boundary. Only this contract
(`docs/contracts/AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT.md`),
the Phase 147E.1 report
(`docs/PHASE_147E.1_AUTHORITY_EVALUATION_MODEL_IMPLEMENTATION_CONTRACT_REPAIR.md`),
and ordinary governance bookkeeping (task/phase lifecycle files,
`PROJECT_STATUS.md`, `.pcae/phase-completion-*`) were created or modified
by this phase.

**Overall verdict:** **IMPLEMENTATION CONTRACT REPAIRED.** BF-147F-1 is
resolved; no other defect was introduced; every AEMIC-001 v1.0 guarantee
outside §5/§9/§13.1/§14/§15/§20/§22/§23 is preserved byte-for-byte.

**Recommended next phase:** **147F.1 — Authority Evaluation Model
Implementation Contract Independent Re-Verification.** Must independently
reconstruct the repaired contract again and specifically attempt to
falsify the repaired citation flow, the `evaluate()` API, construction
invariants, and disclosure-only security properties, per this repair's own
governing prompt. This recommendation is not an authorization; no
implementation may begin until the repaired contract is independently
verified.

---

**End of AEMIC-001 v1.1.**
