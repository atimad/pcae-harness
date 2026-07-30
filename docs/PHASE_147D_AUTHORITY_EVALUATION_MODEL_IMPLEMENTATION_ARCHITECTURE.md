# Phase 147D — Authority Evaluation Model Implementation Architecture

## Contract identity and status

**Phase:** 147D
**Mode:** Implementation Architecture (documentation-only; no production
code, schema, contract, or runtime file modified; no implementation
authorized)
**Predecessor:** 147C — Authority Evaluation Model Contract Independent
Verification (VERIFIED WITH NON-BLOCKING FINDINGS)
**Subject:** AEM-001 v1.0 — Authority Evaluation Model Contract
(`docs/contracts/AUTHORITY_EVALUATION_MODEL_CONTRACT.md`), FROZEN,
independently verified with two Non-Blocking findings (F-147C-1, F-147C-2)
**Runtime baseline:** Observed / observe / unavailable — unaffected by
this phase; reconfirmed at §15 below.

---

## 1. Executive Summary

Phase 147C left AEM-001 v1.0 verified, with two Non-Blocking findings and
a clear directive: 147D should design the implementation architecture for
AEM-001 without modifying production code, and should explicitly take
F-147C-1 (the dormant, free-text `eligible_authority` field already
present in `decision_template.schema.json`) as a first-class input to the
Decision Template Authority Registry's design.

This phase independently reconstructs the implementation requirements
from AEM-001, IWC-001, IWPC-001, CHGR-001, PEC-001, TAMC-001/TAMPC-001,
and GAC-001 primary text, plus direct re-inspection of
`src/pcae/interactive_workflow/**`, `src/pcae/governance/publication/**`,
and `src/pcae/schema_resources/chgr/**`. Two convergent conclusions follow
directly from that inspection, both load-bearing for every section below:

1. **AEM-001's own evaluation mechanism — the `EligibleAuthorityDeclaration`
   model, the pure evaluation function, and the Decision Template Authority
   Registry's lookup contract — can be designed and, in a future phase,
   built as a wholly new, self-contained package** (`pcae.authority_evaluation`,
   §5–§6 below) with **zero dependency on, and zero required modification
   to**, IWC-001, IWPC-001, PEC-001, or CHGR-001's own owned files. This
   mirrors exactly how AEM-001 itself was frozen as a new companion
   contract rather than an amendment to any of the four.

2. **Making that mechanism's output actually reachable by a published CHGR
   requires two further, separately-governed contract amendments** — an
   IWC-001 minor revision widening `PublicationReadinessPackage` (mirroring
   Phase 144F's own IWC-REQ-185 precedent for `decision_maker_identity_evidence`)
   and a PEC-001/`record.py` consumption change reading the new field(s)
   — **neither of which is authorized by AEM-001 itself** (AEM-001 §0
   explicitly declines to redefine IWC-001 or PEC-001) **nor by this
   phase**. This is disclosed explicitly at §7 (Lifecycle Integration)
   and §12 (Findings) as the single most important architectural
   consequence of this phase's research, refining — not contradicting —
   Phase 147A §6.5's projected phase sequence.

F-147C-1 is reconciled (§4) by retaining `decision_template.schema.json`'s
existing free-text `eligible_authority` field **unchanged** (no schema
modification is authorized by this phase or by AEM-001) and assigning it,
architecturally, the role AEM-REQ-026/§7 already anticipates: the
human-readable **citation source** for `AuthorityEvaluationOutcome.citation_text`
— confirmed by `human_governance_record.schema.json`'s own
`authority_basis_claimed` description, which already says the claim cites
"the template's own `eligible_authority` field." The new,
additive `EligibleAuthorityDeclaration.eligible_identities: frozenset[str]`
is a distinct, machine-evaluable membership set, keyed to the same
`(template_ref, template_version)` pair, that AEM-001 defines for the
first time. No duplication conflict exists because the two fields serve
disclosed, non-overlapping purposes; a disclosed (non-blocking) drift risk
between them is named at §4.4 and §9.

No production code, schema, contract, or runtime file is modified by this
phase. This document is itself the sole deliverable.

**Overall Verdict: IMPLEMENTATION ARCHITECTURE COMPLETE WITH OBSERVATIONS.**

---

## 2. Independent Architectural Reconstruction

Reconstructed directly from primary sources, cross-checked against
147C's own independent verification rather than assumed from it.

### 2.1 What AEM-001 requires a future implementation to build

Re-deriving from AEM-001's own text (§4–§8, §12.1):

- A closed, immutable `EligibleAuthorityDeclaration` record (AEM-REQ-007):
  `template_ref`, `template_version`, `eligible_identities: frozenset[str]`,
  `declared_at`, `declared_by`, `schema_version`.
- A pure, deterministic, total evaluation function (AEM-REQ-009,
  AEM-REQ-016) mapping `(claimed_identity, Declaration | None)` to exactly
  one `AuthorityEvaluationOutcome` (AEM-REQ-018): `template_ref`,
  `template_version`, `claimed_identity`, `evaluation_result` (closed
  three-value enum, AEM-REQ-020), `declaration_ref`, `citation_text`,
  `evaluated_at`, `evaluator_version`, `schema_version`.
- A read-only Registry lookup contract (AEM-REQ-010–012):
  `resolve(template_ref, template_version) -> EligibleAuthorityDeclaration | None`,
  pure, never raising, `None` for "no declaration" as an ordinary outcome.
- A closed failure model (AEM-REQ-023–025): raise only on structurally
  malformed input (empty `claimed_identity`/`template_ref`/`template_version`,
  or a Declaration with an empty `eligible_identities` set); never raise
  on "no declaration" (`indeterminate`) or "not a member" (`ineligible`).
- A disclosure-only consumption rule (AEM-REQ-026–029): only
  `PublicationCoordinator`, never the evaluation function's own caller,
  populates `authority_basis_claimed`, and only from an `eligible` outcome's
  verbatim `citation_text` — and the Coordinator itself never invokes
  evaluation (AEM-REQ-028): the outcome must already exist, verbatim,
  inside whatever Package the Coordinator receives.

### 2.2 What AEM-001 explicitly defers to this phase

AEM-001 §4.6 and §12 name exactly two things as 147D's own decision
within AEM-001's bounds:

- Registry storage mechanics, file format, atomicity, and Decision
  Template authoring workflow (§4.6) — this phase's own decision "within
  this contract's bounds," explicitly distinguished from IWPC-001 §13's
  situation (a pre-existing `SessionRepository` ABC to extend) because no
  analogous `DecisionTemplate` Python artifact exists.
- Which schema field an `evaluation_result` disclosure for `ineligible`/
  `indeterminate` outcomes occupies in a CHGR's `limitations`/`extensions`
  array (AEM-REQ-029) — "the exact schema field this occupies is
  Implementation Planning's (147D) decision, not frozen by this contract
  beyond the disclosure obligation itself."

### 2.3 What AEM-001 explicitly forbids this phase (and every future phase) from doing

- Introducing any enforcement/gating behavior (AEM-REQ-003, AEM-REQ-037).
- Introducing a policy language, role model, or scope/time-bounding
  mechanism beyond the closed set-membership shape (AEM-REQ-004).
- Modifying `src/pcae/interactive_workflow/**`, `src/pcae/governance/
  publication/**`, `src/pcae/cltr/**`, or any of IWC-001, IWPC-001,
  PEC-001, CHGR-001, TAMC-001, TAMPC-001, GAC-001, GLP-001 (§15 Non-Goals).
- Exposing any new CLI/transport surface for evaluation results without a
  separately governed IWPC-001 revision (AEM-REQ-038, §11.2).
- Resolving GAC-001 §9's Stage 6 decision or interacting with TAMC-001/
  TAMPC-001's CLTR authority model (§9, §10).

### 2.4 Direct source re-inspection (independent of 147C's own findings, cross-checked against them)

- `src/pcae/interactive_workflow/models/session.py`: `Session.template_ref`
  (non-empty `str`, line 87) and `Session.template_version`
  (defaulted `""`, line 97) are both bare, unvalidated-beyond-emptiness
  fields; no authority-related field exists on `Session` today. Confirmed
  unchanged since 147C.
- `src/pcae/interactive_workflow/publication_handoff/models.py`:
  `PublicationReadinessPackage`'s complete field list carries
  `template_id`, `template_version` (verbatim from `Session`,
  Phase 144F/IWC-REQ-185), and `decision_maker_identity_evidence`
  (a `Mapping` with `evidence_kind`/`identifier`/`captured_at`) — no
  authority-evaluation field of any kind. `handoff.py`'s `build_package`
  constructs every field as a verbatim copy from its own arguments,
  never independently computing or fetching anything — the exact
  discipline any future widening must continue (§7 below).
- `src/pcae/governance/publication/coordinator.py`: imports only
  `pcae.interactive_workflow.errors` and
  `pcae.interactive_workflow.publication_handoff.{handoff,models}` —
  confirmed by direct read, not merely by docstring claim.
  `_PROHIBITED_PACKAGE_FIELDS` = `{chgr_id, publication_state,
  publication_result, authority_token, execution_state}` — a live,
  code-enforced constraint on any future Package field name.
- `tests/test_phase_144c_publication_coordinator.py:362-401`:
  `_FORBIDDEN_IMPORT_ROOTS` — `pcae.interactive_workflow.{session,
  orchestration,evidence,clarification,preview,confirmation,
  state_machine,audit}`, `pcae.cltr` — mechanically, via `ast`-parsing
  every import in the `governance/publication` package, enforces
  PEC-REQ-113. Any future Registry/evaluation code reachable from
  `governance/publication/**` by direct import (as opposed to arriving
  through the already-widened Package) would fail this test.
- `src/pcae/schema_resources/chgr/records/decision_template.schema.json`:
  `eligible_authority` — required, `{"type": "string", "minLength": 1,
  "maxLength": 500}` — confirmed unchanged since Phase 143E/147C.
- `src/pcae/schema_resources/chgr/records/human_governance_record.schema.json`:
  `authority_basis_claimed` — optional, `{"type": "string", "minLength":
  1, "maxLength": 500}`, description: "The governing authority basis this
  record claims (**citing the template's own `eligible_authority` field**
  and its governing contract clause)... present only when a Decision
  Template `eligible_authority` citation resolves to construct it from."
  This is the schema's own textual confirmation that the free-text field
  is meant to be the citation source — directly supporting §4's
  reconciliation below.
- `src/pcae/interactive_workflow/persistence/repository.py`:
  `SessionRepository(ABC)` — five abstract methods (`create`, `load`,
  `persist`, `exists`, `list_session_ids`), zero concrete implementation,
  explicit "never a default, storage-backed behavior here" discipline —
  confirmed as the strongest prior-art pattern for a Registry ABC
  frozen in one phase with its concrete implementation deferred to a
  later, separately-governed phase (Phase 145D built
  `FilesystemSessionRepository`, atomic-write via `tempfile.mkstemp` +
  `os.replace`, path-safety and symlink-rejection, own
  `STORE_SCHEMA_VERSION` distinct from the record's own `schema_version`,
  explicit guard against overlap with `CHGR_STORAGE_PREFIX`).
- `docs/COMMANDS.md` / `src/pcae/commands/governance_record.py`:
  `pcae governance-record template inspect <path>` already exists as a
  read-only, path-based Decision Template artifact inspector
  (`inspect_artifact_at_path`, checking `record_family ==
  "decision_template"`) — not a registry lookup, but the closest existing
  CLI-surface analog a future authority-registry command would sit beside,
  if one is ever separately authorized under a governed IWPC-001 revision.

No new "eligible_authority mechanism of any kind" was found beyond what
147C already disclosed (F-147C-1). No contradiction between this phase's
own re-inspection and 147C's findings was found.

---

## 3. Existing-State Architecture

Complete inventory of every location that will eventually participate in
authority evaluation, as they exist today (all unmodified by this phase):

| Location | Current state | Future participation |
|---|---|---|
| `decision_template.schema.json`'s `eligible_authority` | Required free-text string, unconsumed by any code (F-147C-1) | Citation-source text for `AuthorityEvaluationOutcome.citation_text` (§4) |
| `Session.template_ref` / `.template_version` | Bare, non-empty-validated `str` fields (`session.py:87,97`) | The `(template_ref, template_version)` pair the Registry resolves against (unmodified in shape, AEM-REQ-022) |
| `Session.owner_identity` | Bare, non-empty-validated `str` (session-owner concept, IWC-001) | The evaluation function's `claimed_identity` input (AEM-REQ-014) — no new identity field |
| `PublicationReadinessPackage` | No authority-evaluation field of any kind (confirmed §2.4) | Future widening target (a further governed IWC-001 revision, §7) — the sole path an outcome could reach `PublicationCoordinator` |
| `PublicationHandoff.build_package` | Constructs every Package field as a verbatim copy of its own arguments; no independent computation | Natural, IWC-001-owned invocation point for a future evaluation call (§7) — not this phase's or AEM-001's own authority to add |
| `PublicationCoordinator` | Imports only `publication_handoff.{handoff,models}`; AST-enforced forbidden-import boundary (PEC-REQ-113) | Never invokes evaluation itself (AEM-REQ-028); only ever cites an already-verbatim `citation_text` arriving through the Package |
| `build_publication_record` (`record.py`) | Hard-codes the "authority_basis_claimed is not populated" limitation text; `_authority_basis_disclosure_present` fail-closed check already exists | Future consumption point: conditionally populate `authority_basis_claimed` from a widened Package field, else continue the existing disclosed-absence discipline (§7) |
| `human_governance_record.schema.json`'s `authority_basis_claimed` | Optional string field, already reserved, unpopulated today | Populated only from an `eligible` outcome's `citation_text` (AEM-REQ-026) |
| `CHGR-001 §20.5` | Explicitly declines to assign "runtime consumption" ownership to any existing role | No existing role is silently assigned Registry/evaluation ownership by this phase (§6) |
| `SessionRepository` / `FilesystemSessionRepository` | Concrete ABC + filesystem implementation (Phase 143K/145D) | Structural prior-art pattern for the Registry ABC and its own eventual concrete implementation (§6.3) — not itself extended or reused directly |
| `pcae governance-record template inspect <path>` | Read-only, path-based artifact inspector | Closest existing CLI analog for any future authority-registry read surface (not built, not authorized here) |
| TAMC-001/TAMPC-001's `authority_epoch`/`authority_state` (`src/pcae/cltr/authority/*.py`) | Structurally unrelated CLTR lifecycle-transition authority (AEM-REQ-033) | No participation; explicitly out of scope (§9 below, restating AEM-001 §9) |
| GAC-001 §9's Stage 6 governance-adoption decision | Undischarged, per `docs/GPC6_REQ_075B_HUMAN_AUTHORITY_ELECTION.md` | No participation; explicitly out of scope (§10 below, restating AEM-001 §10) |

---

## 4. F-147C-1 Reconciliation

**F-147C-1** (147C §8): AEM-001's claim that no `eligible_authority`
mechanism "of any kind" exists is factually overbroad — a required,
free-text `eligible_authority` field already exists in
`decision_template.schema.json`, unconsumed, in a shape incompatible with
AEM-REQ-007's `frozenset[str]`.

### 4.1 Does the existing schema field become canonical?

No, not for the operative membership check. It remains canonical for
exactly what CHGR-001 §6 already requires of it: a template's own
human-readable statement of "the eligible human authority who may make
the decision." `human_governance_record.schema.json`'s own
`authority_basis_claimed` description ("citing the template's own
`eligible_authority` field") already assumes this role for it — this
phase's reconciliation makes that assumption architecturally explicit
rather than inventing a new role for the field.

### 4.2 Is it deprecated?

No. Deprecating it would require a `decision_template.schema.json`
change, which neither AEM-001 nor this phase authorizes (§13 below,
No-Go Boundary). It also serves CHGR-001 §6's own requirement
independently of AEM-001's existence — deprecating it would remove a
CHGR-001-mandated field for a reason CHGR-001 itself does not require.

### 4.3 Does it migrate?

No migration is required or performed. No `decision_template` artifact
exists anywhere in this repository today carrying real (non-fixture)
content (147C §7, "Migration implications: none for existing data — no
`AuthorityEvaluationOutcome` or Declaration exists anywhere today"). There
is nothing to migrate *from*; a future `EligibleAuthorityDeclaration` is
purely additive, authored alongside (never derived mechanically from) an
existing template's free-text field.

### 4.4 Does registry ownership change? Does duplication exist?

No existing ownership changes: the schema field remains owned by
CHGR-001 §6/Phase 143E's schema-authoring discipline; the new
`EligibleAuthorityDeclaration`/Registry is owned by AEM-001 exclusively
(a new artifact class this contract itself defines). A **disclosed,
non-blocking duplication risk** exists: a template author could write
free text describing eligible authority (e.g., "the Finance Lead or
Alice") while separately declaring an `eligible_identities` set
containing different literal claimed-identity strings, and nothing in
AEM-001 v1.0 or this architecture mechanically checks the two for
consistency. This mirrors AEM-001 §4.4's own closed-set-only judgment
call: introducing a consistency-validation rule between free text and a
structured set would begin to resemble the policy-language expansion
IWPC-REQ-003 forbids this contract family from inventing, so this phase
does **not** propose one. Instead: **a future, separately governed
Decision Template *authoring* workflow** (which does not exist today —
§2.4) **SHOULD**, as an operational discipline rather than a schema or
evaluation-function rule, prompt an author declaring an
`EligibleAuthorityDeclaration` to ensure its `eligible_identities` set is
consistent with the same template's `eligible_authority` free text — a
disclosed recommendation, not a mechanism this phase or AEM-001 builds
(§9 below names this explicitly as a Findings item, not a Blocking
defect).

### 4.5 Migration implications; compatibility implications

None for existing data (§4.3). Compatibility: the schema field's shape
(`string`, 1–500 chars) is untouched; `EligibleAuthorityDeclaration` is a
wholly new, additive artifact class living outside
`decision_template.schema.json` entirely (§6.1) — no consumer of the
existing schema is affected by this reconciliation in any way.

---

## 5. Implementation Architecture

### 5.1 Authority Evaluation Service — shape

No single "service" class is architected as a stateful, long-lived
component — AEM-REQ-009/016 require evaluation to be a pure, total
function, and AEM-REQ-011/012 require the Registry lookup to be pure.
Consistent with `PublicationHandoff`'s own "stateless... every method's
output is a pure function of its arguments" discipline (mirrored, not
copied, since `PublicationHandoff` is IWC-001's own artifact), this
phase architects two free functions plus one ABC, grouped under a new,
self-contained package: `pcae.authority_evaluation` (§6).

### 5.2 Evaluation inputs

- `claimed_identity: str` — already-collected, verbatim `Session.owner_identity`
  (or an equivalent already-collected claimed identity a future caller
  supplies; this phase invents no new collection mechanism, AEM-REQ-014).
- `declaration: EligibleAuthorityDeclaration | None` — the Registry's own
  `resolve(template_ref, template_version)` return value, passed in by
  the caller (the evaluation function itself never calls the Registry;
  a thin orchestration wrapper, §6.2, does, keeping the evaluation
  function itself free of any I/O dependency and trivially unit-testable).

### 5.3 Evaluation outputs

Exactly one `AuthorityEvaluationOutcome` (AEM-REQ-018), never a
partial/streaming/multi-value result.

### 5.4 Evaluation lifecycle

1. A future, separately-governed caller (§7) resolves `(template_ref,
   template_version)` against the Registry, obtaining a `Declaration` or
   `None`.
2. The same caller invokes the pure evaluation function with the claimed
   identity and that result.
3. The function returns exactly one `AuthorityEvaluationOutcome`,
   immediately (AEM-REQ-016: total, non-raising for well-formed input).
4. The outcome is either consumed immediately (e.g., threaded into a
   widened Package field, §7) or discarded; this phase defines no
   persistence mechanism for the outcome itself beyond what AEM-REQ-031
   already permits deferring.

### 5.5 Authority registry interaction

`AuthorityRegistry.resolve(template_ref, template_version) ->
EligibleAuthorityDeclaration | None` — an ABC (§6.3), mirroring
`SessionRepository`'s own "define the interface only; no concrete
storage backend implemented or selected here" discipline (repository.py
lines 21-23), for the same disclosed reason AEM-001 §4.6 already gives:
no pre-existing extensible artifact exists for Decision Templates, so
storage mechanics are architected here (§6.4) but not implemented.

### 5.6 Publication interaction

Exactly as AEM-REQ-028 requires: `PublicationCoordinator` never imports
or invokes anything from `pcae.authority_evaluation` directly (this
would violate the AST-enforced `_FORBIDDEN_IMPORT_ROOTS`-style boundary
in spirit even though `pcae.authority_evaluation` is not itself on that
literal list today — extending that test's root list to include the new
package the moment any code under `governance/publication/**` is tempted
to import it directly is this phase's own recommended test-architecture
addition, §11). The only permitted path for an outcome to influence a
CHGR is: evaluation runs upstream (§7), its `citation_text` (when
`eligible`) becomes a verbatim field on a widened Package, and
`build_publication_record` reads that verbatim field exactly as it
already reads `decision_maker_identity_evidence`.

### 5.7 CHGR interaction

`build_publication_record` (a future, separately-governed PEC-001-
conforming change, §7) reads the widened Package's new field(s) and:
- if the carried `evaluation_result == "eligible"`, populates
  `authority_basis_claimed` from the carried `citation_text` verbatim
  (AEM-REQ-026);
- otherwise, continues emitting the existing disclosed-absence
  `limitations` entry, optionally naming the specific `evaluation_result`
  (`ineligible`/`indeterminate`/"no evaluation attempted") per AEM-REQ-029,
  in a new `limitations` or `extensions` entry — this phase recommends
  (not mandates) an `extensions.authority_evaluation` object
  (`{"evaluation_result": "ineligible", "declaration_ref": "..."}`) as
  the natural home, using CHGR-001 §12's open-`extensions`-container
  precedent, since `extensions` is explicitly documented as unable to
  "override any normative field... or alter authority semantics" —
  exactly the disclosure-only property AEM-REQ-029 requires.

### 5.8 Failure paths

See §8 (Failure Architecture) below — this phase separates "evaluation
input failure" (§8.1, AEM-REQ-023) from "Registry unavailability" (§8.2,
a new failure mode this phase must architect for since no equivalent
exists in AEM-001's own text, which assumes the Registry always answers).

### 5.9 Audit trail

Every `AuthorityEvaluationOutcome` that contributes a `citation_text` to
a published CHGR is reconstructible after the fact from: the CHGR's own
`authority_basis_claimed` text, the session's `template_ref`/
`template_version` (already persisted per IWPC-001 §12/§13), and the
Declaration the citation was drawn from (Registry-resolvable, assuming
availability — AEM-REQ-030's own disclosed caveat, restated unchanged
here). This phase adds no new audit mechanism beyond what AEM-REQ-030
already specifies; a durable log of `ineligible`/`indeterminate` outcomes
(distinct from what reaches a CHGR) is named as an open design question
at §11 (Test Architecture) and §14 (Migration), not resolved here
(AEM-REQ-031 explicitly defers this).

### 5.10 Persistence

Two independent persistence questions, kept explicitly separate:

1. **Declaration persistence** (the Registry's own storage) — architected
   at §6.4 as a filesystem-backed store, one JSON document per
   `(template_ref, template_version)` pair, mirroring
   `FilesystemSessionRepository`'s atomic-write/path-safety/symlink-
   rejection discipline. Storage root: a new, dedicated path — this phase
   recommends `.pcae/authority-declarations/` (never
   `.pcae/governance-records/`, `CHGR_STORAGE_PREFIX`, mirroring
   `SessionRepository`'s own explicit-overlap-guard discipline, §6.4).
2. **`AuthorityEvaluationOutcome` persistence** — AEM-REQ-031 explicitly
   leaves this open beyond the CHGR-population case (§5.7). This phase
   does not architect a durable outcome log as a requirement; §11 names
   it as a test-architecture question a future phase may resolve, not a
   gap this phase must close.

### 5.11 Caching

None is architected. AEM-REQ-012's purity guarantee ("repeated calls with
identical inputs... SHALL return identical results") means caching is a
pure performance optimization with no correctness implication, and no
performance requirement in AEM-001, IWC-001, IWPC-001, or PEC-001 names a
latency budget that would justify introducing one. Introducing caching
prematurely risks a staleness bug precisely because Declarations are
immutable once evaluated against (AEM-REQ-008) — a cache would need
invalidation logic for a case (in-place Declaration mutation) AEM-REQ-008
already forbids from occurring, making a cache pure overhead with a
disclosed staleness footgun for zero present benefit. **Non-goal for
v1.0**, revisitable only if a future phase demonstrates an actual
performance need (§14).

### 5.12 Extension points

Restating AEM-REQ-042 in implementation terms:
- `EvaluationResult`'s three values are architected as a closed Python
  `Enum`, extendable only via a future major-version module (never a
  runtime-configurable set).
- `EligibleAuthorityDeclaration`'s optional-field slots (e.g. a future
  `expires_at`) are architected as keyword-only, defaulted dataclass
  fields — additive, non-breaking to any consumer reading only the
  required fields (mirroring `Session`'s and `PublicationReadinessPackage`'s
  own additive-field discipline, e.g. Phase 144F's `template_version`).
- The Registry ABC's `resolve` signature is frozen at this phase's
  architecture; any concrete storage backend (filesystem, later a
  database) satisfies it without changing the ABC.

---

## 6. Component Architecture

New package: `pcae.authority_evaluation` (does not yet exist; this phase
architects, does not create, it). Sibling to `pcae.interactive_workflow`,
`pcae.governance.publication`, and `pcae.cltr` — never nested inside any
of them, so that no forbidden-import test needs modification merely to
accommodate this package's own internal structure (§11).

### 6.1 `pcae.authority_evaluation.models`

**Responsibility:** define the two immutable record types AEM-001 §4.1/§5.3
freezes.
**Ownership:** sole owner of `EligibleAuthorityDeclaration` and
`AuthorityEvaluationOutcome` shape.
**Inputs:** constructor arguments only (no I/O).
**Outputs:** frozen dataclass instances (mirroring `Session`,
`PublicationReadinessPackage`'s own `@dataclass(frozen=True)` +
`__post_init__` structural-validation-only discipline — semantic
validation, e.g. "is this identity actually eligible," lives elsewhere,
exactly as `Session.__post_init__` never checks transition legality).
**Invariants:** `eligible_identities` non-empty and immutable
(`frozenset`); `schema_version` fixed per AEM-REQ-007/018 ("aem-declaration/1.0",
"aem-outcome/1.0"); no field beyond AEM-001's own closed shape (structural
`ValueError` on missing required field, matching `Session`'s pattern).
**Dependencies:** none beyond the standard library (`dataclasses`,
`enum`, `types.MappingProxyType` if any mapping field is ever added —
none is required by AEM-001 v1.0's own shape).

### 6.2 `pcae.authority_evaluation.evaluation`

**Responsibility:** the pure evaluation function (AEM-REQ-009, AEM-REQ-016).
**Ownership:** sole owner of the `evaluate` function's logic.
**Inputs:** `claimed_identity: str`, `declaration: EligibleAuthorityDeclaration
| None`, `evaluated_at: str`, `evaluator_version: str`.
**Outputs:** `AuthorityEvaluationOutcome`.
**Invariants:** total (never raises for well-formed input, AEM-REQ-016);
deterministic (AEM-REQ-009); three-valued closed result (AEM-REQ-020);
`citation_text` populated if and only if `evaluation_result == "eligible"`
(AEM-REQ-018's own field description).
**Dependencies:** `pcae.authority_evaluation.models`,
`pcae.authority_evaluation.errors` only. Zero dependency on
`interactive_workflow`, `governance.publication`, or `cltr` — this
function's own unit tests can construct every input by hand, with no
Session, Package, or Registry fixture required (§11).

### 6.3 `pcae.authority_evaluation.registry` (ABC only)

**Responsibility:** the lookup contract (AEM-REQ-010–012).
**Ownership:** sole owner of `AuthorityRegistry`'s abstract interface.
**Inputs/Outputs:** `resolve(template_ref: str, template_version: str) ->
EligibleAuthorityDeclaration | None`.
**Invariants:** read-only (AEM-REQ-011: no `create`/`persist`/`delete`
method exists on this ABC at all — a stronger boundary than
`SessionRepository`'s own five-method ABC, since AEM-REQ-011 restricts
every *consumer this contract or any contract citing it defines* to
read-only access; Declaration *authoring* is explicitly deferred to
§4.6/§6.4's own separate concrete-implementation phase, which MAY expose
a write path on its own concrete class without that path being part of
this ABC — mirroring how `FilesystemSessionRepository` implements
`SessionRepository`'s `create` method without the *abstract* interface
itself needing to expose anything beyond what every consumer needs).
**Dependencies:** `pcae.authority_evaluation.models` only.

### 6.4 Concrete Registry implementation (architected, not built)

Deferred per AEM-001 §4.6 — this phase names the design a future,
separately-governed implementation phase should follow, without
implementing it:

- **Storage layout:** one JSON document per `(template_ref,
  template_version)` pair, filename derived deterministically from both
  (mirroring `FilesystemSessionRepository`'s one-file-per-record layout),
  under a new root — **not** `.pcae/governance-records/`
  (`CHGR_STORAGE_PREFIX`) and **not** `.pcae/decision-sessions/`
  (`SessionRepository`'s own root) — this phase recommends
  `.pcae/authority-declarations/`.
- **Atomicity:** `tempfile.mkstemp` in the same directory, write + flush +
  `os.fsync`, `os.replace` — identical pattern to
  `FilesystemSessionRepository._write_atomic` and
  `governance/publication/storage.py`'s `_write_atomic_json`, so this is
  a proven, already-audited pattern in this codebase, not a novel one.
- **Path safety:** filename derived only from `template_ref`/
  `template_version` through the same validated-identifier discipline
  `SessionRepository`'s `_validated_path`/`validate_session_id` already
  establish (reject `/`, `\`, `..`; confirm resolved-path-parent equals
  storage root; reject symlinks on every read/write) — this phase
  recommends reusing the *pattern*, never importing
  `interactive_workflow.persistence`'s own private helpers directly (that
  would itself create an unwanted cross-package dependency this
  architecture otherwise keeps at zero, §6.2).
- **Immutability enforcement:** `resolve` never overwrites; a future
  authoring path (not this phase's concern) must itself refuse to
  overwrite an already-evaluated-against Declaration (AEM-REQ-008) — an
  authoring-time check, not a `resolve`-time one, since `resolve` has no
  visibility into whether a Declaration has been evaluated against.
- **`schema_version` field:** `"aem-declaration/1.0"` per AEM-REQ-007,
  independent of any store-level schema version a concrete implementation
  might also define (mirroring `FilesystemSessionRepository`'s own
  `STORE_SCHEMA_VERSION` vs. `Session.schema_version` distinction).

### 6.5 `pcae.authority_evaluation.errors`

**Responsibility:** the malformed-input failure family (AEM-REQ-023).
**Ownership:** sole owner of this package's exception hierarchy.
**Shape:** a base `AuthorityEvaluationError`, with the three malformed-
input conditions each either sharing one exception type (distinguished by
message) or three distinct subclasses — this phase recommends three
distinct subclasses (`InvalidClaimedIdentityError`,
`InvalidTemplateReferenceError`, `MalformedDeclarationError`), mirroring
`PublicationHandoffIncompleteError`'s own single-purpose-exception
granularity rather than a single generic `ValueError`, since AEM-REQ-025
already anticipates a future CLI/transport surface mapping failures onto
"that surface's own existing closed error taxonomy" — a small number of
named, distinguishable exception types maps more legibly onto a future
closed error taxonomy than one generic type would.
**Dependencies:** none.

### 6.6 `pcae.authority_evaluation.serialization`

**Responsibility:** deterministic `to_payload`/`from_payload` for both
record types, mirroring `interactive_workflow.serialization`'s own
per-schema submodule pattern (e.g. `publication_handoff_schema`).
**Ownership:** sole owner of this package's wire format.
**Invariants:** round-trip-stable; `schema_version`-tagged, so a future
schema evolution (AEM-REQ-044) can detect and reject a stale payload,
mirroring IWPC-001's own schema-version-checked deserialization
discipline.
**Dependencies:** `pcae.authority_evaluation.models` only.

### 6.7 Sequence — evaluation invoked at decision-selection time (illustrative; not authorized)

```
Human operator                CLI/transport            AuthorityRegistry        evaluate()
      |                            |                          |                       |
      |--- decision-session ------>|                          |                       |
      |    select --as-identity -->|                          |                       |
      |                            |--- resolve(template_ref, |                       |
      |                            |    template_version) --->|                       |
      |                            |<-- Declaration | None ---|                       |
      |                            |--- evaluate(claimed_identity, declaration) ------>|
      |                            |<---------------------- AuthorityEvaluationOutcome-|
      |                            |  (outcome discarded, logged, or threaded          |
      |                            |   into Session/Package -- future, separately     |
      |                            |   governed IWC-001/IWPC-001 revision, sec 7)      |
```

This sequence is illustrative of where evaluation's inputs (`template_ref`,
`template_version`, `claimed_identity`) are already available together for
the first time in today's codebase (`decision-session select`,
IWPC-REQ-192) — it is **not** an authorization to wire evaluation into
that command; doing so requires the IWPC-001/IWC-001 revisions named at
§7, out of this phase's own scope.

### 6.8 Sequence — outcome reaching a published CHGR (illustrative; not authorized)

```
Session (widened, future IWC-001 rev)   PublicationHandoff        PublicationReadinessPackage (widened)   PublicationCoordinator   build_publication_record
        |                                       |                              |                                    |                        |
        |-- authority_evaluation_outcome ------>|                              |                                    |                        |
        |   (verbatim, already-computed)        |-- copies verbatim fields --->|                                    |                        |
        |                                       |   (mirrors decision_maker_   |                                    |                        |
        |                                       |    identity_evidence, 144F)  |--- package (never invokes eval) -->|                        |
        |                                       |                              |                                    |--- reads verbatim ----->|
        |                                       |                              |                                    |    citation_text field  |
        |                                       |                              |                                    |    (never re-derives)   |
```

---

## 7. Lifecycle Integration

```
Decision Template
      |  (eligible_authority free text, unchanged, F-147C-1;
      |   EligibleAuthorityDeclaration, new, additive, keyed to
      |   the same template_ref/template_version)
      v
Interactive Workflow  (Session: template_ref, template_version,
      |                 owner_identity -- all pre-existing, unmodified)
      |
      |  <-- AUTHORITY IS EVALUATED HERE, if a future, separately
      |      governed extension of Session/decision-selection invokes
      |      pcae.authority_evaluation.evaluate() against the Registry's
      |      resolve() result. This phase architects the mechanism;
      |      it does NOT authorize wiring it into Session or any CLI
      |      command -- that requires its own governed IWC-001/IWPC-001
      |      revision (see below).
      v
Confirmation  (IWC-001, unmodified -- authority evaluation, if it ran
      |        upstream, is merely CARRIED forward from this point on,
      |        never re-evaluated, never gating Confirmation, AEM-REQ-037)
      v
Readiness  (PublicationHandoff.build_package -- AUTHORITY IS CARRIED,
      |     never evaluated, here: a widened Package would copy an
      |     already-computed outcome's fields verbatim, exactly as
      |     decision_maker_identity_evidence already is, 144F precedent)
      v
Publication  (PublicationCoordinator -- AUTHORITY IS CARRIED, never
      |        evaluated, here: AEM-REQ-028 forbids the Coordinator from
      |        invoking evaluation; it only ever cites an already-verbatim
      |        Package field, mirroring PEC-REQ-115's "MAY construct...
      |        never independent judgment")
      v
CHGR generation  (build_publication_record -- AUTHORITY IS CARRIED,
      |           never evaluated, here: reads the widened Package's
      |           verbatim citation_text/evaluation_result fields;
      |           populates authority_basis_claimed only if eligible,
      |           else continues the existing disclosed-absence rule)
      v
Verification  (an Independent Contract/Implementation Verifier MAY
      |         verify CONFORMANCE only -- that evaluation_result is
      |         correctly, deterministically derivable from its own
      |         recorded inputs and the Declaration cited -- never
      |         substantive eligibility adjudication, AEM-REQ-039)
      v
Inspection  (decision-session status/readiness, governance-record
             inspect -- MAY report an already-computed outcome
             verbatim; SHALL NOT compute, re-derive, or infer one,
             AEM-REQ-040)
```

**Precisely where authority is evaluated vs. merely carried:** evaluation
occurs at exactly one point in this entire lifecycle — wherever a future,
separately-governed extension invokes `pcae.authority_evaluation.evaluate()`,
which is architecturally most natural immediately after (or at)
`decision-session select` (IWPC-REQ-192), since that is the first point
`template_ref`, `template_version`, and `claimed_identity` are all
simultaneously available together (§6.7). Every subsequent stage —
Confirmation, Readiness, Publication, CHGR generation, Verification,
Inspection — only ever *carries* an already-computed outcome forward,
verbatim, never recomputing or re-deriving it (restating AEM-REQ-019's
immutability discipline and AEM-REQ-040's "reporting, never evaluation"
rule end-to-end across the full lifecycle, not just at the Inspection
layer AEM-001 §11.4 names explicitly).

**The un-authorized gap this phase discloses, not closes:** wiring the
evaluation call into `decision-session select` (or any other Session-
state-transition command) requires modifying `Session` and/or
`PublicationReadinessPackage` — both IWC-001-owned artifacts — which
AEM-001 itself declines to redefine (§0) and this phase's own No-Go
Boundary (§13) forbids. **A future IWC-001 minor-revision phase**
(mirroring Phase 144F's own IWC-001 v1.2 §26 precedent exactly) is
therefore a precondition for AEM-001's mechanism ever becoming live end-
to-end — this is disclosed as Finding FA-147D-1 at §12, not silently
assumed away.

---

## 8. Failure Architecture

### 8.1 Malformed evaluation input (AEM-REQ-023)

`InvalidClaimedIdentityError` / `InvalidTemplateReferenceError` /
`MalformedDeclarationError` (§6.5) — raised, never silently substituted,
for empty `claimed_identity`, empty `template_ref`/`template_version`, or
a resolved Declaration with an empty `eligible_identities` set. Fail-
closed: none of these conditions may ever resolve to `eligible`
(AEM-REQ-032).

### 8.2 Registry lookup failure (new failure mode this phase must name)

AEM-001's own text assumes the Registry always answers (`Declaration` or
`None`, AEM-REQ-010) but does not address what happens if a concrete
Registry implementation's own storage layer fails (a filesystem read
error, corrupted JSON, permission failure) — an operational concern
AEM-001 deliberately leaves to Implementation Planning (§4.6). This
phase architects: a concrete Registry implementation MUST raise a
distinct, new exception (e.g. `AuthorityRegistryUnavailableError`,
mirroring `PersistenceUnavailableError`'s own "read/write failures
propagate... without partial state mutation; no silent retry" discipline)
rather than returning `None` (which AEM-REQ-010 reserves exclusively for
"no Declaration exists," a semantically different condition from "the
Registry could not be consulted"). Conflating storage failure with "no
Declaration" would violate AEM-REQ-024's closed condition list by
misreporting an operational fault as a substantive `indeterminate`
evaluation result — this phase names the distinction explicitly so a
future implementation does not conflate them.

### 8.3 Version mismatch / conflicting declarations

Not reachable under AEM-REQ-008's immutability rule (a Declaration, once
evaluated against, cannot be edited) combined with the Registry's own
one-`(template_ref, template_version)`-key-per-Declaration invariant — a
concrete implementation's own authoring-time uniqueness check (not this
phase's own evaluation-path concern) is the correct enforcement point,
architected at §6.4 but not built.

### 8.4 Unsupported / future authority types

Restating AEM-REQ-021/AEM-REQ-042: a fourth `EvaluationResult` value is
a future major-revision concern, never a runtime-detected "unsupported
type" failure mode — v1.0's closed three-value enum has no "unknown"
case to fail on beyond `indeterminate` itself.

---

## 9. Security Architecture

| Property | Architectural mitigation |
|---|---|
| Spoofing | No new identity-collection mechanism (AEM-REQ-014); `claimed_identity` is exactly the already-collected, already-transported `--owner-id`. This phase introduces no new trust boundary for identity itself. |
| Authority substitution | `eligible_identities` is a closed, literal-string set (AEM-REQ-006); no role-indirection or wildcard membership exists that a substituted identity could exploit (§4.4's closed-shape judgment call, restated). |
| Replay | `AuthorityEvaluationOutcome` is immutable once produced (AEM-REQ-019); a future consumer never re-executes evaluation against stale inputs to produce a different outcome for the same triple — evaluation is a pure function of its inputs, so "replay" in the CSRF/session sense does not apply; the only relevant replay concern (re-publishing an already-consumed Package) is PEC-001's own, unaffected boundary (`AuthorizationReplayError`, unmodified). |
| Stale authority | AEM-REQ-008's immutability rule forecloses "the Declaration changed underneath an already-evaluated outcome" — a Declaration is permanently fixed once evaluated against. |
| Privilege escalation | Evaluation is disclosure-only (AEM-REQ-003, AEM-REQ-037); no evaluation outcome, however constructed, ever grants execution capability, Runtime access, or Permission Broker authority (§2.2/§8 unaffected, confirmed unmodified at §15). |
| Circular trust | `EligibleAuthorityDeclaration.declared_by` is recorded for provenance only, never itself evaluated recursively (AEM-REQ-013, disclosed, not hidden, D-7 at AEM-001 §14). This phase's architecture does not close this gap and does not pretend to — a future, separately governed, explicitly-scoped revision would be required to evaluate Declaration authorship itself, and this phase does not propose one. |
| Registry poisoning | The Registry ABC exposes no write path at all (§6.3); a concrete implementation's own authoring-time controls (out of this phase's scope, §4.6) are the correct enforcement point for who may author a Declaration — this phase names the boundary (read-only consumer access) without designing the authoring-side access control itself, since CHGR-001 §20's existing Implementer/Verifier responsibility mapping already covers Decision Template authorship generally (AEM-REQ-013) and this phase invents no new role. |
| Audit integrity | AEM-REQ-030's reconstructibility guarantee is restated unchanged at §5.9; this phase adds no new audit mechanism, and names (§8.2) exactly one new failure mode (Registry unavailability) an audit trail would need to distinguish from a substantive `indeterminate` result. |
| Field-name collision with existing security boundaries | Any future Package-widening field name (§7) MUST NOT collide with `PublicationCoordinator._PROHIBITED_PACKAGE_FIELDS` (`chgr_id`, `publication_state`, `publication_result`, **`authority_token`**, `execution_state`) — a concrete, code-enforced constraint this phase surfaces explicitly so a future implementation phase does not accidentally choose a colliding name (e.g. naming a field literally `authority_token` would be rejected by the Coordinator's own existing guard, a useful defense-in-depth accident worth preserving rather than working around). |

No security property is weakened by this architecture. The one disclosed
gap (Declaration-authorship circular trust) is named, not hidden, and was
already disclosed at AEM-001 §4.7/§14 D-7 — this phase adds no new
disclosed gap beyond §7's cross-contract dependency finding (FA-147D-1)
and §9's own duplication-risk finding (restating §4.4).

---

## 10. Migration Architecture

**Backward compatibility:** total. No existing artifact, schema, or
behavior changes shape. A `decision_template` document with no
`EligibleAuthorityDeclaration` behaves exactly as every `decision_template`
document behaves today (`eligible_authority` free text present, no
operative membership check, `authority_basis_claimed` correctly absent
downstream) — AEM-001's own compatibility policy (§0) restated at the
implementation-architecture layer.

**Dormant field handling (F-147C-1):** the existing free-text
`eligible_authority` field requires no migration; it is retained,
unchanged, permanently, as the citation-source role §4 assigns it.

**Incremental rollout:** the natural rollout order, restating the
dependency chain §7 discloses:
1. Build `pcae.authority_evaluation` in complete isolation (§6) — fully
   testable with zero Session/Package/Registry-implementation
   dependency, since the evaluation function's own unit tests need only
   hand-constructed `EligibleAuthorityDeclaration` fixtures (§11).
2. Build a concrete Registry implementation (§6.4) — testable in
   isolation against the ABC, no Session/Package dependency either.
3. **Separately**, propose and govern an IWC-001 minor revision widening
   `PublicationReadinessPackage` (and, if evaluation is to run at
   `decision-session select` time, `Session` itself) — this is the first
   point production behavior actually changes, and it is out of AEM-001's
   and this phase's own authority (§7, Finding FA-147D-1).
4. **Separately**, propose and govern a PEC-001-conforming change to
   `record.py` consuming the widened Package's new field(s).
5. Only after steps 3–4 are independently governed and frozen does an
   end-to-end "a Decision Template declares eligible authority; a
   published CHGR discloses a real `authority_basis_claimed`" path exist.

**Feature gating:** not architected as a runtime flag or config toggle —
each of the five steps above is itself a natural, disclosed gate (an
ungoverned step simply does not exist in the running system yet,
mirroring how `PublicationHandoff` existed for multiple phases before any
`PublicationCoordinator` consumed it). No `if feature_enabled(...)`
branch is architected anywhere; the existing "if this field resolves,
populate it; otherwise disclose its absence" conditional
(`build_publication_record`'s own current structure) already is the
correct and sufficient gating mechanism once step 4 above is built.

**Rollback strategy:** since steps 1–2 touch no existing file, rollback
is deleting the new package/module tree, no different from removing any
other never-wired-in module. Steps 3–4, once governed and built, would
roll back exactly as Phase 144F's own widening would (removing the added
optional fields is non-breaking to any consumer that reads only
pre-existing fields, per each dataclass's own additive-field discipline).

---

## 11. Test Architecture

- **Unit tests** (`pcae.authority_evaluation.evaluation`): pure-function
  table tests over `(claimed_identity, declaration)` → expected
  `AuthorityEvaluationOutcome`, requiring no Session, Package, Registry-
  implementation, or filesystem fixture — mirroring
  `PreviewBuilder`'s/`ConfirmationController`'s own fixture-free
  pure-function test style (Phase 143N).
- **Unit tests** (`pcae.authority_evaluation.models`): structural
  `__post_init__` validation (empty-field rejection, immutability,
  `schema_version` fixed value) — mirroring `Session`'s/
  `PublicationReadinessPackage`'s own construction-test style.
- **Unit tests** (a future concrete Registry implementation):
  atomic-write correctness, path-safety/symlink-rejection, `resolve`
  purity across repeated calls, `None`-vs-exception distinction (§8.2) —
  mirroring `FilesystemSessionRepository`'s own test suite
  (`test_phase_145d_session_repository_filesystem_implementation.py`) as
  the closest structural precedent.
- **Integration tests**: none are architected at this phase for the
  cross-package flow (§7's Sequence diagrams), since that flow itself
  requires the not-yet-governed IWC-001/PEC-001 revisions; an integration
  test exercising "Session → Package → CHGR" for authority specifically
  cannot exist correctly until those revisions land (a test written
  against un-governed behavior would itself be evidence of ungoverned
  implementation — this phase declines to pre-write one).
- **Adversarial tests**: malformed `claimed_identity`/`template_ref`/
  `template_version` (empty string, non-string type); a Declaration with
  an empty `eligible_identities` set; a claimed identity not in the set
  (`ineligible`); no Declaration at all (`indeterminate`); a
  Registry-unavailable condition (§8.2) distinguished from `indeterminate`;
  repeated `resolve()` calls confirming byte-identical results
  (AEM-REQ-012).
- **Lifecycle tests**: confirming evaluation, wherever it eventually runs,
  never blocks Confirmation/Readiness/Publication for `ineligible`/
  `indeterminate` outcomes (restating AEM-REQ-003/037) — this can and
  should be tested even before §7's cross-contract revisions land, by
  constructing a hand-built `AuthorityEvaluationOutcome` and confirming no
  existing IWC-001/PEC-001 code path conditions any behavior on it (a
  negative test: grep-style/AST-style assertion that no such conditional
  exists anywhere in `interactive_workflow`/`governance/publication`
  today, extending `test_phase_144c_publication_coordinator.py`'s own
  `_FORBIDDEN_IMPORT_ROOTS` style pattern to also assert
  `pcae.authority_evaluation` is not yet imported anywhere outside its
  own package/tests — a "not wired in yet" regression guard, valuable
  precisely because it fails loudly the moment an ungoverned integration
  attempt is made).
- **Publication tests**: deferred until §7's PEC-001-conforming
  `record.py` change is itself governed and built; this phase names the
  test shape (verify `authority_basis_claimed` population is
  conditioned exactly on `evaluation_result == "eligible"`, verify the
  `limitations`/`extensions` disclosure fires for every other case,
  mirroring `_authority_basis_disclosure_present`'s own existing
  fail-closed check) without writing it.
- **Migration tests**: none required (§10 — no existing data to migrate).
- **Compatibility tests**: a `decision_template.schema.json` document
  with only the pre-existing `eligible_authority` free-text field and no
  `EligibleAuthorityDeclaration` continues to validate and behave
  identically to today — an explicit regression test recommended for
  whichever future phase first builds `pcae.authority_evaluation`,
  confirming F-147C-1's reconciliation (§4) does not silently require
  every existing/future `decision_template` document to carry a
  Declaration.

---

## 12. Findings

**Reassessed from 147C:**

- **F-147C-1** (dormant schema field) — **reconciled**, not merely
  re-disclosed: §4 assigns the existing free-text `eligible_authority`
  field the citation-source role AEM-REQ-026/§7 and the CHGR schema's own
  description already anticipate, with no schema modification, no
  migration, and a disclosed (non-blocking) drift risk named at §4.4/§9
  rather than mechanically closed. Status: **Non-Blocking, Addressed by
  Architecture**.
- **F-147C-2** (citation-precision cosmetic defect, IWC-001 §6 vs §11
  mislabeling) — unrelated to implementation architecture; unaffected by
  this phase; remains open for correction at AEM-001's next amendment
  opportunity (AEM-001 §13), not this phase's own file to touch. Status:
  **Non-Blocking, Unchanged, Out of This Phase's Scope**.

**New findings this phase:**

- **FA-147D-1 (Non-Blocking, Architectural Dependency).** AEM-001's
  evaluation mechanism (`pcae.authority_evaluation`, §6) can be built in
  complete isolation with zero required modification to IWC-001,
  IWPC-001, PEC-001, or CHGR-001's own files — but making that
  mechanism's output reach a published CHGR requires two further,
  separately-governed contract-revision phases (an IWC-001 Package/
  Session-widening revision, and a PEC-001/`record.py` consumption
  change), neither authorized by AEM-001 or this phase (§7, §10).
  Disclosed here rather than silently assumed; recommended as an
  explicit insertion into Phase 147A §6.5's projected sequence (§17
  below), refining rather than contradicting it.
- **FA-147D-2 (Non-Blocking, Observation).** No Registry-unavailability
  failure mode is named anywhere in AEM-001's own text (§8.2); this
  phase names one, distinct from AEM-REQ-010's `None`-for-"no Declaration"
  case, as a necessary addition any concrete Registry implementation
  phase must include — not a defect in AEM-001 (an operational concern
  properly deferred to Implementation Planning per §4.6), but a gap this
  phase must not leave silently unaddressed.
- **FA-147D-3 (Non-Blocking, Observation).** A duplication-drift risk
  exists between the schema's free-text `eligible_authority` field and a
  future `EligibleAuthorityDeclaration.eligible_identities` set for the
  same template (§4.4) — disclosed as an operational-discipline
  recommendation for a future, not-yet-existing Decision Template
  authoring workflow, not a mechanism this phase or AEM-001 builds
  (consistent with AEM-001 §4.4's own closed-set-only, no-policy-language
  judgment call).

No Blocking findings. No contract contradiction, no hidden authority
expansion, no runtime-boundary violation, and no premature production
code, schema, or contract modification were found or introduced.

---

## 13. No-Go Boundary Confirmation

This phase did **not**:
- implement any production code, module, class, or function under
  `src/pcae/**` (`pcae.authority_evaluation` does not exist after this
  phase; every code excerpt above is illustrative architecture prose,
  not a diff);
- modify `decision_template.schema.json`, `human_governance_record.schema.json`,
  or any other schema file;
- modify AEM-001, IWC-001, IWPC-001, PEC-001, CHGR-001, TAMC-001,
  TAMPC-001, GAC-001, or GLP-001 — all confirmed byte-for-byte unmodified;
- modify runtime, Permission Broker, or any execution-capability file;
- change authority, alter policy, or alter strategic lineage;
- enable execution capability of any kind.

Only this report and ordinary governance bookkeeping (task/phase
lifecycle files, `PROJECT_STATUS.md`, `.pcae/phase-completion-*`) were
created or modified by this phase, confirmed by `git status --short`
before and after writing this report (§15).

---

## 14. Deliverable Notes on Deferred Design Questions

Named explicitly as remaining outside this phase's own scope, consistent
with AEM-001 §12/§15's own Non-Goals, not newly foreclosed or newly
resolved here:

- Whether caching is ever warranted (§5.11) — a future phase's decision,
  contingent on an actual demonstrated performance need.
- Whether a durable `ineligible`/`indeterminate` outcome log is built
  (§5.9, §5.10.2) — AEM-REQ-031 leaves this open; this phase does not
  close it.
- The exact `limitations`/`extensions` schema shape for `evaluation_result`
  disclosure (§5.7) — this phase recommends `extensions.authority_evaluation`
  as the natural home but does not freeze it; a future Implementation
  Contract Freeze phase (§17) is the correct place to make this binding.
- Recursive evaluation of `declared_by` (Declaration authorship) — AEM-001
  §4.7/§12 names this out of scope; this phase does not reopen it.

---

## 15. Governance Verification

Commands run before and after this report was written:

- `pcae check` — passed.
- `pcae health` — healthy; required PCAE files all present; policy
  validation valid; agent lock held by `claude-local`; session
  continuity verified; git status clean.
- `pcae doctor task-memory` — clean, no inconsistencies detected.
- `pcae runtime inspect` — Runtime status `not_implemented`, Runtime
  state `Observed`, Execution capability `unavailable`, Maximum plugin
  capability `observe`, Registry status `empty`, Plugin count `0` —
  identical before and after this phase; unchanged.
- `pcae push check` — clean (`nothing_to_push`) at phase start; branch
  `main`, working tree clean, health healthy, check passed, task memory
  clean.

No policy file (`.pcae/policy.toml`) was touched. No strategic-lineage
file (`.pcae/strategic-lineage.json`) was touched. Runtime remained
`Observed`/`observe`/`unavailable` throughout.

---

## 16. Overall Verdict

**IMPLEMENTATION ARCHITECTURE COMPLETE WITH OBSERVATIONS.**

AEM-001 v1.0's evaluation mechanism is fully architectable as a new,
self-contained package with zero required modification to any existing
contract-owned file. F-147C-1 is reconciled by assigning the existing
dormant schema field its already-implied citation-source role, with no
schema change and a disclosed, non-mandatory drift-risk recommendation.
The "Observations" qualifier reflects three Non-Blocking findings (§12):
a disclosed cross-contract dependency this phase cannot itself resolve
(FA-147D-1, requiring future IWC-001/PEC-001 revisions outside this
phase's and AEM-001's own authority), a named-but-unresolved Registry-
availability failure mode (FA-147D-2), and a named-but-unresolved
schema/set duplication-drift risk (FA-147D-3) — none of which blocks this
phase's own architecture from being sound, implementable, and faithful to
AEM-001 as frozen.

---

## 17. Recommended Next Phase

**147E — Authority Evaluation Model Implementation Contract Freeze.**

This recommendation is not an authorization.

*Disclosed refinement, not a contradiction:* Phase 147A §6.5 originally
projected phase 5 of this chapter's sequence as "147E — Implementation."
This phase's own research (§7, Finding FA-147D-1) surfaces that a
Contract Freeze step converting this architecture document's own design
decisions (§5–§11 above) into a binding, falsifiable implementation
contract — before any source file is written — is warranted, mirroring
exactly how AEM-001 itself was frozen (147B) before being verified (147C)
and only then architected for implementation (this phase). A subsequent
147F would then perform Implementation Contract Independent Verification,
147G the actual Implementation, and so on — a one-phase insertion
relative to 147A's own projection, not a departure from GLP-001's
established Architecture → Contract Freeze → Verification discipline
this repository has applied consistently since Chapter 143.

Separately and not folded into Chapter 147: a standalone Phase 107A
execution-capability gap re-derivation, roadmap-tracking reconciliation,
and GLP-PILOT-C6 Stage 3 resumption all remain open, disclosed, and
unscheduled — unaffected by this phase.

---

**End of Phase 147D implementation architecture document.**
