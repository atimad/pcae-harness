# Phase 144E — Publication Execution Contract Revision (IWC-001/PEC-001 Provenance-Boundary Closure)

## 0. Status

**Phase:** 144E
**Type:** Contract revision (GLP-001 §6.1 Stage 2, applied as a governed
*revision* of an already-frozen Stage 2 artifact, mirroring the
138C→138C.1 and 143H→143I.1 precedents)
**Predecessor:** Phase 144D — Publication Coordinator Independent
Verification (`docs/PHASE_144D_PUBLICATION_COORDINATOR_INDEPENDENT_VERIFICATION.md`)
**Governed subject:** Finding F-1/JC-2 — the provenance-boundary gap
between IWC-001's Publication Readiness Package and CHGR-001 §10's
verbatim-content requirement, independently demonstrated by Phase 144D
and explicitly escalated, unrepaired, to "a governed IWC-001 or PEC-001
contract revision."
**Outcome:** IWC-001 revised v1.1 → v1.2 (§26 added); PEC-001 revised
v1.0 → v1.1 (§20 added). Both revisions are additive. No implementation.

This document is the canonical Phase 144E report. It does not implement
`PublicationCoordinator` or any other class, does not modify
`src/pcae/interactive_workflow/**`, does not modify
`src/pcae/governance/publication/**`, does not modify CHGR-001,
TAMC-001, or TAMPC-001, and does not authorize any future phase to begin.
Runtime remains Observed / observe / unavailable throughout.

---

## 1. Governing Inputs — Read Completely

The following were read in full, directly, before any conclusion in this
document was drafted:

- `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` (IWC-001 v1.1, prior
  to this phase's own edit)
- `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`
  (CHGR-001 v1.0), §8–§12 in full, §20 (Governance Responsibility
  Contract) and §22 (Amendment Contract) for compatibility purposes
- `docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md` (PEC-001 v1.0, prior
  to this phase's own edit), in full
- `docs/contracts/TYPED_AUTHORITY_MODEL_CONSUMPTION_CONTRACT.md`
  (TAMC-001) and
  `docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md`
  (TAMPC-001), for §7/compatibility purposes (record-family disjointness)
- `docs/PHASE_143G_..._ARCHITECTURE.md` through
  `docs/PHASE_143P_..._CERTIFICATION.md` (Phase 143A–143P), for
  Interactive Workflow architectural context
- `docs/PHASE_144A_PUBLICATION_EXECUTION_OWNERSHIP_ARCHITECTURE.md`
- `docs/PHASE_144B_PUBLICATION_EXECUTION_CONTRACT_FREEZE.md`
- `docs/PHASE_144C_PUBLICATION_COORDINATOR_IMPLEMENTATION.md`
- `docs/PHASE_144D_PUBLICATION_COORDINATOR_INDEPENDENT_VERIFICATION.md`,
  in full, including §7 (JC-2 Independent Assessment) and §12 (Findings
  Register)
- `PROJECT_STATUS.md` (tail, for current phase-history continuity)

The following source files were read directly, treated as evidence of
what the frozen contracts' text actually permits and what a future
implementation would actually consume — never as contractual authority in
their own right, mirroring PEC-001's own citation discipline (§0 above,
"contract text only"):

- `src/pcae/interactive_workflow/publication_handoff/models.py`
  (`PublicationReadinessPackage`)
- `src/pcae/interactive_workflow/publication_handoff/handoff.py`
  (`PublicationHandoff.build_package`)
- `src/pcae/interactive_workflow/models/session.py` (`Session`)
- `src/pcae/interactive_workflow/preview/models.py` (`Preview`)
- `src/pcae/interactive_workflow/preview/builder.py` (`PreviewBuilder`)
- `src/pcae/governance/publication/record.py`
  (`build_publication_record`)
- `src/pcae/schema_resources/chgr/records/human_governance_record.schema.json`
- `src/pcae/schema_resources/chgr/records/human_confirmation_evidence.schema.json`
- `src/pcae/schema_resources/chgr/records/governance_record_provenance.schema.json`
- `src/pcae/schema_resources/chgr/shared/identity.schema.json`
- `tests/test_phase_144c_publication_coordinator.py`
  (`_FORBIDDEN_IMPORT_ROOTS`, the AST-enforced import-boundary test)

Phase 144D is treated as evidence of a demonstrated finding, never as
contractual authority. Every conclusion below is independently re-derived
from the governing contracts and the actual source above; where this
document's conclusion matches 144D's own framing, that is disclosed as
independent convergence, not as inherited trust.

---

## 2. Independent Problem Statement

**Why can a Publication Coordinator implementing PEC-001 not presently
produce a production-complete CHGR while preserving Interactive Workflow
boundaries, Publication Coordinator boundaries, CHGR ownership, and
immutable evidence?**

Independently re-derived, not trusted from JC-2's wording:

1. CHGR-001 §10 (Provenance Contract) requires a published CHGR to carry
   provenance sufficient to reconstruct, among other things, "the exact
   preview content the human actually confirmed, stored verbatim"
   (CHGR-REQ-085), what was selected (CHGR-REQ-084), and who provided the
   decision (CHGR-REQ-083). The frozen `human_governance_record.schema.json`
   independently confirms this at the schema layer: `decision_subject`,
   `selected_option_id`, `decision_maker_identity_evidence`, and
   `authority_basis_claimed` are all listed in its top-level `required`
   array.
2. PEC-REQ-018–020 require the Publication Coordinator to be external to
   `interactive_workflow/**`, `cltr/**`, and the PCAE phase-lifecycle
   tree. PEC-REQ-058 requires its sole input to be a
   `PublicationReadinessPackage`, "unmodified from `interactive_workflow`'s
   own frozen shape." PEC-REQ-065 assigns that shape's ownership
   exclusively to `interactive_workflow/**`.
3. Independently reading `PublicationReadinessPackage`
   (`publication_handoff/models.py`) field-by-field: `package_id`,
   `session_id`, `session_state`, `transition_sequence_number`,
   `evidence_refs`, `clarification_refs`, `audit_refs`, `preview_id`,
   `preview_digest`, `confirmation_request_id`, `confirmation_response_id`,
   `built_at`, `metadata`, `schema_version`. None of these is
   `decision_subject`, `selected_option_id`, `decision_maker_identity_evidence`,
   `authority_basis_claimed`, `human_rationale_text`, `human_conditions_text`,
   or verbatim preview content — every field is an identifier, an enum
   member, an int, or a digest.
4. Therefore: the Coordinator's *only* permitted input (item 2) does not
   carry the content CHGR-001 §10 requires (item 1), and the Coordinator
   is contractually forbidden from obtaining that content any other way
   (item 2's boundary). This is a **structural impossibility**, not an
   implementation oversight: no implementation of PEC-001 v1.0 against
   IWC-001 v1.1's `PublicationReadinessPackage`, however carefully
   written, could produce a CHGR-001 §10-complete record, because the one
   value it is permitted to read does not contain the required content
   and it is forbidden from reading anything that does.

This independently reconfirms Phase 144D's F-1/JC-2 finding was correctly
classified: Non-Blocking against PEC-001 v1.0's own literal text (which
never itself promised a specific field list — PEC-REQ-059 said only
"unchanged from existing `PublicationHandoff.build_package` output"), and
Blocking against CHGR-001 §10 conformance (which no implementation
respecting PEC-REQ-018–020's boundary could satisfy against the package
as it existed).

---

## 3. Root Cause Analysis

Four candidate explanations were independently evaluated.

### Option A — `PublicationReadinessPackage` carries insufficient provenance

**Independently confirmed as the root cause.** Direct reading of
`PublicationHandoff.build_package`
(`interactive_workflow/publication_handoff/handoff.py`) shows the method
receives, as its own arguments, the full `Session` object — with
`human_selection_id`, `human_rationale_text`, `human_conditions_text`,
`owner_identity`, `template_ref`, and `subject_ref` all populated — and
the full `Preview`, `ConfirmationRequest`, and `ConfirmationResponse`
objects. At the exact moment the Package is constructed, every value
CHGR-001 §10 requires is already present, in memory, inside the one
component (`PublicationHandoff`) IWC-001 §11.4 names as the Package's
sole production constructor. The method then builds a
`PublicationReadinessPackage` using only `session.session_id`,
`session.session_state`, and reference/digest fields drawn from
`preview`/`confirmation_request`/`confirmation_response` — discarding
every substantive value it was handed. The data is not missing; it is
present and then dropped at construction time. This is decisive:
insufficient Package content is the mechanism of the gap, independently
verified by reading the exact line where the substantive values are
available and not used.

### Option B — Publication Coordinator lacks a contractually authorized read path

**Independently evaluated and rejected as the primary cause**, though not
without merit as an alternative fix (§4, Model 2 below). A read path
*would* close the gap, but adopting it as the primary mechanism would
require either relaxing PEC-REQ-018–020's placement/dependency boundary
(weakening an invariant with no compensating benefit, since the same data
is already reachable at Package-construction time without any new
coupling) or duplicating `PublicationHandoff`'s existing
package-construction responsibility inside a second, Coordinator-owned
read interface (violating PEC-REQ-013's one-owner-per-responsibility
invariant and PEC-REQ-086's least-privilege invariant, since the
Coordinator would then depend on two ways to obtain the same content).
Root cause, in the "what defect must be fixed" sense, is that the Package
does not carry data already available where it is built — not that the
Coordinator structurally cannot ever be given the data.

### Option C — CHGR-001 expects information outside every frozen ownership boundary

**Independently rejected.** Every value CHGR-001 §10 requires is
independently confirmed to already exist inside `interactive_workflow/**`'s
own frozen ownership boundary (`Session`, `Preview`,
`ConfirmationRequest`, `ConfirmationResponse` are all owned there, per
IWC-001 §18's Governance Responsibility Contract, unmodified). No value
CHGR-001 §10 requires originates outside any contract this repository
already governs. Option C is false.

### Option D — another independently derived explanation

None found. A secondary, non-blocking observation was independently
made and is disclosed for completeness: `Preview`
(`interactive_workflow/preview/models.py`) itself never persists literal
rendered preview text — only `evidence_refs`/`clarification_refs`/
`audit_refs` and an optional, informational `transition_summary`. This
means the "verbatim preview content" CHGR-REQ-085 requires is not merely
excluded from the Package; as of today it is not durably materialized as
a string anywhere in the Interactive Workflow layer at all, only rendered
transiently and digested. This is not a separate root cause — it is the
same root cause (Option A: insufficient Package/Preview content) applied
one layer earlier, to Preview generation rather than Package
construction, and is addressed by the same revision (§26.3
IWC-REQ-188 below, which requires the verbatim rendered content to be
*captured*, not merely digested, at Preview-generation time).

**Conclusion: Option A**, with the Option D observation folded into the
same fix. Citations: `PublicationReadinessPackage` field list
(`publication_handoff/models.py:65–78`); `PublicationHandoff.build_package`'s
full-`Session`/`Preview`/`ConfirmationRequest`/`ConfirmationResponse`
signature and its narrower package construction
(`publication_handoff/handoff.py:56–150`); `Preview`'s reference-only
field list (`preview/models.py:58–67`); CHGR-001 §10's verbatim-content
requirement (CHGR-REQ-083–088); `human_governance_record.schema.json`'s
`required` array.

---

## 4. Alternative Architecture Evaluation

### Model 1 — Expand `PublicationReadinessPackage`

**Adopted.**

- **Advantages:** Requires no new coupling for the Publication
  Coordinator; PEC-REQ-018–020's placement boundary and the AST-enforced
  import-boundary test are entirely unaffected. Shape ownership stays
  exactly where PEC-REQ-065 already assigns it
  (`interactive_workflow/**`). The data is already present at
  `PublicationHandoff.build_package`'s call site (§3 above) — this model
  requires zero new data-fetching, only retaining values already in
  scope. Minimal, additive, and the smallest possible diff against both
  contracts' existing text.
- **Disadvantages:** Widens what a future implementation must add to two
  already-frozen dataclasses (`PublicationReadinessPackage`, and
  transitively `Preview`, to actually persist rendered content) — a
  real but bounded implementation cost, deferred to a future phase, not
  incurred by this contract-only revision.
- **Authority implications:** None. Every added field is a verbatim copy
  of data the Human Decision already produced; nothing about
  authorization, readiness, or execution semantics changes (PEC-REQ-009,
  PEC-REQ-028 unaffected).
- **Compatibility:** Full — CHGR-001, TAMC-001, TAMPC-001 all unmodified;
  PEC-001's own §17 requirement set (PEC-REQ-001–110) needs no wording
  change, only an additive §20 describing consumption of the wider
  Package.
- **Migration cost:** One future implementation phase, touching only
  `interactive_workflow/publication_handoff/**`,
  `interactive_workflow/preview/**`, and
  `governance/publication/record.py` — no CLI, storage, or runtime
  change required.

### Model 2 — Grant Publication Coordinator a frozen read-only provenance interface

**Evaluated, not adopted as primary; retained as a named future
extension point (unchanged from PEC-001 §14's existing extensibility
contract).**

- **Advantages:** Would avoid widening the Package's own shape; the
  Coordinator could resolve `session_id` to full content on demand.
- **Disadvantages:** Requires either relaxing the AST-enforced
  import-boundary test (weakening PEC-REQ-018–020 with no compensating
  benefit, since the same content is reachable without any new coupling
  under Model 1) or introducing an entirely new frozen interface class
  whose own shape, ownership, and versioning would themselves need
  governing — a strictly larger contract-surface increase than Model 1
  for the same outcome. Duplicates `PublicationHandoff`'s existing
  package-construction responsibility (violates PEC-REQ-013's
  one-owner-per-responsibility invariant: two paths would now produce
  the same content).
- **Authority implications:** A read interface reachable by the
  Coordinator, if built carelessly, is a larger attack surface for
  authority-neutrality (PEC-REQ-085/086) than a Package field that is
  merely widened; not disqualifying, but a genuine cost Model 1 avoids
  entirely.
- **Compatibility:** Full, in principle, but at a materially larger
  contract-surface cost than Model 1 for an equivalent outcome.
- **Migration cost:** Larger than Model 1 — a new interface class,
  its own contract text, and a relaxation of an existing enforced
  boundary test, for no capability Model 1 does not already provide.

### Model 3 — Hybrid: migrate only selected provenance into the Package, retrieve the rest via a frozen read interface

**Evaluated, not adopted.** No genuine partition was found where some
CHGR-001 §10 field is better served by a live read than by a verbatim
copy at Confirmation time: every required field is fixed, immutable, and
fully determined at the moment Confirmation completes (IWC-001 §10.3's
"exact-content binding"; §7's Decision Existence Contract). A live read
path would only ever return the same frozen value a copy already
captures, at strictly higher architectural cost (Model 2's costs, for a
subset of fields). A hybrid is strictly dominated by Model 1 here.

### Model 4 — Any superior architecture independently derived

None found. Every CHGR-001 §10 field this phase examined is already
determined, in full, and available inside `interactive_workflow/**`'s own
boundary at the exact moment `PublicationHandoff.build_package` runs;
no architecture that does not either (a) copy that data into the Package
at that moment, or (b) grant a new read path to re-fetch the same
already-fixed data, was found to exist. (a) is strictly cheaper and
strictly more compatible with every existing invariant; Model 1 is
adopted.

---

## 5. Contract Revision — What Changed

Both IWC-001 and PEC-001 were revised. Neither CHGR-001, TAMC-001, nor
TAMPC-001 was touched (Forbidden Files for this phase; independently
unnecessary per §3/§4 above — the gap is a boundary-content gap between
two already-compatible contracts, not a defect in CHGR-001's own already
correct §10 text).

### 5.1 IWC-001 v1.1 → v1.2 (`docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` §26)

Added `IWC-REQ-185` through `IWC-REQ-190`:

| Req | Obligation |
|---|---|
| IWC-REQ-185 | Package SHALL additionally carry, verbatim: Decision Subject; Decision Template identity+version; selected option id; rationale/conditions text; full option set presented; decision-maker identity evidence; exact rendered Preview content; confirmation act evidence |
| IWC-REQ-186 | Additive only — no existing field/requirement changed |
| IWC-REQ-187 | Added fields subject to existing immutability/authority-neutrality/publication-neutrality discipline |
| IWC-REQ-188 | Verbatim Preview content captured once, deterministically, at Preview-generation time; never re-rendered downstream |
| IWC-REQ-189 | §18.4's Publication Handoff execution-ownership deferral is unchanged — this widens content only, not who executes |
| IWC-REQ-190 | Widened Package remains bound to one `Confirmed` session, sole-constructed by `PublicationHandoff`, subject to all existing preconditions |

### 5.2 PEC-001 v1.0 → v1.1 (`docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md` §20)

Added `PEC-REQ-111` through `PEC-REQ-117`:

| Req | Obligation |
|---|---|
| PEC-REQ-111 | PEC-REQ-054's CHGR-001 §10 obligation is now satisfiable from the widened Package alone |
| PEC-REQ-112 | Coordinator SHALL carry every IWC-REQ-185 field through, unmodified, into the CHGR record's provenance capture |
| PEC-REQ-113 | Dependency boundary unchanged — no import of `interactive_workflow` internals to obtain any field; all arrives via the Package |
| PEC-REQ-114 | PEC-REQ-058's "frozen shape" now refers to the v1.2-widened shape; no contradiction, since PEC-001 never itself owned the shape (PEC-REQ-065) |
| PEC-REQ-115 | `authority_basis_claimed` MAY be constructed deterministically from the widened Package's verbatim template citation; no independent eligibility judgment |
| PEC-REQ-116 | No new validation/weighting authority granted; PEC-REQ-048's existing package-provenance check extends unchanged |
| PEC-REQ-117 | No PEC-REQ-001–110 requirement narrowed, superseded, or reworded |

---

## 6. Compatibility Matrix

| Contract | Modified? | Compatibility disposition |
|---|---|---|
| IWC-001 | Yes — v1.1 → v1.2, additive §26 | Self-compatible: no `IWC-REQ-001`–`184` reworded; §26.4 regression review independently reconfirms all 20 prior sections unaffected in mechanics |
| PEC-001 | Yes — v1.0 → v1.1, additive §20 | Self-compatible: no `PEC-REQ-001`–`110` reworded; §20.3 regression review independently reconfirms all 19 prior sections unaffected in mechanics |
| CHGR-001 | No | Unaffected; this revision moves the system strictly closer to already-frozen CHGR-001 §10 text, never redefining it |
| TAMC-001 | No | Unaffected; independently reconfirmed structurally disjoint — no field this revision adds is a Typed Authority Model record type |
| TAMPC-001 | No | Unaffected, same reasoning |
| GLP-001 / GAC-001 / PGP-001 / PPA-001 / AGOC-001 | No | Unaffected; this revision is itself an instance of GLP-001 §6.1 Stage 2 discipline (a governed contract revision), not a modification of the framework contracts |
| Phase 134/135/137V (finalization/lifecycle/GLP) | No | Unrelated domain, independently reconfirmed unaffected (no field this revision adds touches phase/task lifecycle) |
| `src/pcae/interactive_workflow/**` | No (code) | Zero files under this path in this phase's diff (Forbidden Files) |
| `src/pcae/governance/publication/**` | No (code) | Zero files under this path in this phase's diff (Forbidden Files) |

No contradiction remains between any two governing contracts after this
revision.

---

## 7. Migration Strategy

**144C implementation → future implementation:**

| Step | Layer | Kind of change | Files (future phase, not this one) |
|---|---|---|---|
| 1 | IWC-001-side | Implementation update | `interactive_workflow/publication_handoff/models.py` (widen `PublicationReadinessPackage`), `interactive_workflow/preview/models.py` (persist rendered content), `interactive_workflow/publication_handoff/handoff.py` (thread the new values through `build_package`) |
| 2 | PEC-001-side | Implementation update | `governance/publication/record.py` (`build_publication_record` populates CHGR-001 §10 fields from the widened Package; `_KNOWN_LIMITATIONS` narrowed or removed) |
| 3 | Verification | Independent re-verification | A future phase mirroring 144D's own precedent, verifying the widened Coordinator against both revised contracts |

This phase performs none of the three steps. §5.1/§5.2's Migration
Effect and Migration Strategy subsections (IWC-001 §26.6, PEC-001 §20.5)
state this in full; both are documentation-only relative to any
in-flight implementation, since `PublicationCoordinator`,
`PublicationReadinessPackage`, `Preview`, and every other existing class
remain byte-identical in code after this phase.

Determination: migration requires **implementation update**, not
documentation-only and not a further contract update — both revised
contracts already state, in full, everything a future implementation
needs to satisfy.

---

## 8. Requirement Traceability

```
144D Finding F-1/JC-2
  (CHGR built by Coordinator lacks selected_option_id,
   decision_maker_identity_evidence, authority_basis_claimed,
   decision_subject, verbatim preview content)
        |
        v
Root cause (§3 above): Option A — PublicationReadinessPackage
carries insufficient provenance; data exists inside
interactive_workflow/** at Package-construction time but is
discarded, not fetched from outside any boundary (Option C false)
and not primarily a missing-read-path problem (Option B secondary)
        |
        v
Contract revision:
  IWC-001 §26 IWC-REQ-185..190 (Package widened, additive)
  PEC-001 §20 PEC-REQ-111..117 (Coordinator consumption described,
    additive)
        |
        v
Future implementation obligations (144F or equivalent, NOT
authorized by this phase):
  - Widen PublicationReadinessPackage per IWC-REQ-185
  - Persist verbatim rendered Preview content per IWC-REQ-188
  - Thread widened values through PublicationHandoff.build_package
  - Populate human_governance_record/human_confirmation_evidence/
    governance_record_provenance schema fields from the widened
    Package per PEC-REQ-112
  - Independent re-verification of the widened implementation
    (144D-precedent pattern)
```

Every `IWC-REQ-185`–`190` and `PEC-REQ-111`–`117` traces to exactly one
cell of this chain; none is orphaned, and none introduces an obligation
not already implied by CHGR-001 §10's pre-existing, unmodified text.

---

## 9. Findings Resolution

| Finding | Prior disposition (144D) | This phase's disposition |
|---|---|---|
| F-1/JC-2 — CHGR record reference-only, missing verbatim CHGR-001 §10 content | Blocking for production Publication; escalated, unrepaired, to a governed contract revision | **Contract-level closure.** Root cause independently re-derived (§3), minimum additive revision frozen (§5). **Not implementation-closed** — a future phase must still widen the actual dataclasses and `record.py` per §7's migration strategy before a real CHGR can be schema-valid. This phase closes the *contract* gap only, exactly as its own scope (contract revision, no implementation) requires. |
| F-2 (144D, Observation) — `PublicationExecutionContext` never constructed in real path | Observation, no PEC-REQ violated | Out of this phase's scope (implementation-only finding); unaffected by this revision |
| F-3 (144D, Non-Blocking) — forbidden-import test omits `pcae.core`/`pcae.commands` | Non-Blocking, deferred | Out of this phase's scope (test-coverage gap); this revision's PEC-REQ-113 restates the *substantive* boundary the incomplete test only partially enforces, but does not itself repair the test |
| F-4 (144D, Observation) — architecture enforcement mode advisory, not hard gate | Pre-existing, out of scope | Unaffected; out of this phase's scope |

---

## 10. Implementation Constraints (for a future implementation phase)

A future implementation phase closing this contract revision:

- SHALL widen `PublicationReadinessPackage` (`interactive_workflow/publication_handoff/models.py`)
  to add IWC-REQ-185's fields, additively — no existing field removed or
  renamed.
- SHALL widen `Preview` (`interactive_workflow/preview/models.py`) or an
  equivalent artifact to durably capture the exact rendered content at
  generation time, per IWC-REQ-188 — a pure-function capture, not a
  re-render.
- SHALL update `PublicationHandoff.build_package`
  (`interactive_workflow/publication_handoff/handoff.py`) to thread the
  now-available `Session`/`Preview`/`Confirmation*` values it already
  receives into the widened Package, without adding any new external
  dependency.
- SHALL update `governance/publication/record.py`'s
  `build_publication_record` to populate `human_governance_record.schema.json`,
  `human_confirmation_evidence.schema.json`, and
  `governance_record_provenance.schema.json`'s required fields from the
  widened Package, per PEC-REQ-112, and SHALL NOT introduce any new
  import of `interactive_workflow` internals to do so (PEC-REQ-113).
- SHALL NOT relax `_FORBIDDEN_IMPORT_ROOTS`
  (`tests/test_phase_144c_publication_coordinator.py`); the widened
  Package makes the existing boundary sufficient, not obsolete.
- SHALL be independently re-verified (144D-precedent pattern) before any
  claim of full CHGR-001 §10 conformance.
- SHALL NOT introduce any runtime capability change; Runtime remains
  Observed/observe/unavailable until a separately governed phase
  explicitly authorizes otherwise.

This phase authorizes none of the above; it only specifies the
constraints a future, separately governed phase must operate within.

---

## 11. Ownership Preservation — Verified

| Owner | Responsibility | Preserved? |
|---|---|---|
| Interactive Workflow | Decision, evidence, readiness (incl. Package construction/completeness) | Yes — unchanged; widened Package remains sole-owned by `PublicationHandoff` (IWC-REQ-190) |
| Publication Coordinator | Publication execution (verification + atomic write) | Yes — unchanged; PEC-REQ-113 explicitly restates no new dependency |
| CHGR | Canonical record | Yes — CHGR-001 untouched |
| Human Operator | Authorization | Yes — PEC-001 §5/§6 untouched; no new authority path introduced |

No responsibility migrated. IWC-001 §26.4 and PEC-001 §20.3's regression
reviews independently confirm every section of both contracts other than
the two additive sections is unaffected in mechanics.

---

## 12. Authority Boundary — Verified

Publication Readiness ≠ Publication Authorization ≠ Publication
Execution remains fully intact:

- PEC-REQ-009–017 (Core Invariants), PEC-REQ-028–033 (Authority
  Contract), and PEC-REQ-034–046 (Authorization Event Contract) are
  untouched by this revision — none is cited, referenced, or reworded by
  §20.
- No field IWC-REQ-185 adds is an authority token, a publication
  decision, or an execution-state flag (IWC-REQ-187, restating
  PEC-REQ-061–064 unchanged).
- No automatic publication, implicit authorization, inferred authority,
  or authority transfer is introduced: the widened Package still requires
  a separately-verified `PublicationAuthorizationEvent` before any write
  (PEC-REQ-050, untouched); widening *what* the Coordinator writes once
  authorized does not change *whether* it is authorized to write.

---

## 13. Provenance Contract (frozen by this revision)

| Property | Frozen content |
|---|---|
| Required provenance | Decision Subject, Template identity+version, selected option id, decision-maker identity evidence, exact rendered Preview content, confirmation act evidence, options presented (IWC-REQ-185) |
| Optional provenance | Rationale text, conditions text (IWC-REQ-185, "where supplied") |
| Forbidden provenance | Authority tokens, publication-state/-result fields, CHGR identifiers (IWC-REQ-187, restating PEC-REQ-061–064) |
| Ownership | Constructed solely by `PublicationHandoff` (IWC-REQ-190); consumed, never re-derived, by the Publication Coordinator (PEC-REQ-112) |
| Lifecycle | Captured once, at Package-construction/Preview-generation time; immutable thereafter (IWC-REQ-187, IWC-REQ-188) |
| Immutability | Full — no field mutable after construction (restating PEC-REQ-060 unchanged, extended to content granularity) |
| Visibility | Carried only within the Package/CHGR provenance chain; no new external visibility introduced |
| Retention | Governed by IWC-001 §14 (Package/session retention) and CHGR-001 §10/§12.1 (post-publication retention) once a CHGR exists — unchanged by this revision |
| Authority | None — provenance content never constitutes or implies authorization (IWC-REQ-187, PEC-REQ-009/028 unchanged) |
| Replay semantics | Unchanged — PEC-REQ-007/008/041/042/078/080/087 govern replay at the Coordinator's entry point regardless of Package content richness |

---

## 14. Security Review

| Property | Preserved by this revision? | Basis |
|---|---|---|
| Authority neutrality | Yes | No added field grants or implies authority (§12 above; IWC-REQ-187) |
| Immutable evidence | Yes | Added fields immutable from capture, per IWC-REQ-187/188, mirroring PEC-REQ-089 unchanged |
| Deterministic publication | Yes | PEC-REQ-047/090 untouched; widened content changes what is written, never how deterministically it is written |
| Replay resistance | Yes | PEC-REQ-007/008/041/042/078/080/087 untouched |
| Least privilege | Yes | PEC-REQ-113 explicitly forbids any new Coordinator dependency; content arrives solely via the already-existing Package boundary |
| Explicit authorization | Yes | PEC-REQ-028–046 untouched; §12 above |
| One-owner-per-responsibility | Yes | §11 above; no responsibility reassigned |

---

## 15. Validation

Run at phase start and again at phase close (documentation-only phase;
no source under `src/` or `tests/` is touched):

```
$ pcae check
PCAE check passed.

$ pcae health
(see raw output below)

$ pcae doctor
(see raw output below)

$ pcae push readiness
(see raw output below)

$ pytest -m fast_green -n auto -q
(see raw output below)
```

Raw command output is captured verbatim in this phase's own governed
session log; summarized results:

- `pcae check`: passed, both before and after this phase's edits.
- `pcae health`: healthy, both before and after.
- `pcae doctor`: no defect attributable to this phase's diff (contract
  documentation only).
- `pcae push readiness`: clean prior to commit; re-run after commit,
  before push.
- `fast_green`: unaffected — this phase's diff touches
  `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md`,
  `docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md`,
  `docs/PHASE_144E_PUBLICATION_EXECUTION_CONTRACT_REVISION.md`,
  `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**` only — zero files under
  `src/` or `tests/`, so no test outcome can be caused by this phase's
  diff.

Runtime confirmed unchanged: `pcae runtime inspect` reports Runtime
state Observed, execution capability unavailable, maximum plugin
capability observe, identical before and after this phase.

---

## 16. Explicit No-Go — Confirmed Observed

This phase did not: modify `PublicationCoordinator` or any
`src/pcae/governance/publication/**` file; redesign Interactive Workflow
(zero `src/pcae/interactive_workflow/**` files touched); redesign CHGR
architecture (`CHGR-001` byte-identical); implement any new API or CLI
command; implement any runtime capability; implement any provenance
interface; or implement any contract revision in code. Both contract
revisions are additive text only, confirmed by `git diff --stat`
touching only the files listed in §15 above.

---

## 17. Exit Criteria — Self-Assessment

1. Provenance-boundary inconsistency independently re-derived — §2, §3. ✅
2. Root cause demonstrated — §3 (Option A, with citations). ✅
3. Minimum contract revision frozen — §5 (IWC-001 §26, PEC-001 §20, both
   additive). ✅
4. Ownership remains coherent — §11. ✅
5. Authority neutrality preserved — §12. ✅
6. Compatibility restored — §6 (no contradiction remains between any two
   governing contracts). ✅
7. Migration path documented — §7. ✅
8. No implementation occurred — §16. ✅
9. Runtime remains unchanged — §15. ✅

---

## 18. Recommended Next Phase

**144F — Provenance Boundary Implementation.** Would implement
IWC-001 §26 (IWC-REQ-185–190) and PEC-001 §20 (PEC-REQ-111–117) against
the actual `interactive_workflow/publication_handoff/**`,
`interactive_workflow/preview/**`, and `governance/publication/record.py`
source, then independently re-verify the widened implementation
(144D-precedent pattern), closing Finding F-1 in substance rather than
in contract text alone.

**This recommendation does not authorize 144F.**
