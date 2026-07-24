# Phase 144F — Provenance Boundary Implementation

## 0. Status

**Phase:** 144F
**Type:** Implementation (GLP-001 §6.1 Stage 3, closing the additive
contract revision Phase 144E froze)
**Predecessor:** Phase 144E — Publication Execution Contract Revision
(`docs/PHASE_144E_PUBLICATION_EXECUTION_CONTRACT_REVISION.md`)
**Governing authority:** IWC-001 v1.2 §26 (`IWC-REQ-185` through
`IWC-REQ-190`), PEC-001 v1.1 §20 (`PEC-REQ-111` through `PEC-REQ-117`),
CHGR-001 v1.0 §10, Phase 144D, Phase 144E, PROJECT_STATUS.md.
**Runtime:** Observed / observe / unavailable throughout (`pcae runtime
inspect` at phase start and close: unchanged).
**Deliverable:** Widened `PublicationReadinessPackage`/`Preview`/`Session`
dataclasses, updated `PublicationHandoff.build_package`, updated
`governance/publication/record.py`, updated regression suites, this
report.

---

## 1. Governing Inputs — Read Completely

Read in full, directly, before any implementation:

- `docs/contracts/INTERACTIVE_WORKFLOW_CONTRACT.md` (IWC-001 v1.2, §26)
- `docs/contracts/PUBLICATION_EXECUTION_CONTRACT.md` (PEC-001 v1.1, §20)
- `docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md` (CHGR-001
  v1.0), §10 (Provenance Contract)
- `docs/PHASE_144A_PUBLICATION_EXECUTION_OWNERSHIP_ARCHITECTURE.md`
  through `docs/PHASE_144E_PUBLICATION_EXECUTION_CONTRACT_REVISION.md`
- `PROJECT_STATUS.md` (tail, for phase-history continuity)

Source read directly, as evidence of what the frozen contracts actually
require the running code to do, never as contractual authority in its
own right:

- `src/pcae/interactive_workflow/publication_handoff/models.py`
  (`PublicationReadinessPackage`)
- `src/pcae/interactive_workflow/publication_handoff/handoff.py`
  (`PublicationHandoff.build_package`/`validate_completeness`)
- `src/pcae/interactive_workflow/models/session.py` (`Session`)
- `src/pcae/interactive_workflow/preview/models.py` (`Preview`)
- `src/pcae/interactive_workflow/preview/builder.py` (`PreviewBuilder`)
- `src/pcae/interactive_workflow/orchestration/coordinator.py`
  (`WorkflowOrchestrator.stage_preview_construction`)
- `src/pcae/interactive_workflow/confirmation/models.py`
  (`ConfirmationRequest`/`ConfirmationResponse`)
- `src/pcae/governance/publication/record.py`
  (`build_publication_record`)
- `src/pcae/schema_resources/chgr/records/human_governance_record.schema.json`,
  `human_confirmation_evidence.schema.json`,
  `governance_record_provenance.schema.json`,
  `src/pcae/schema_resources/chgr/shared/identity.schema.json`
- `tests/test_iwc_143o_session_coordination_publication_handoff.py`,
  `tests/test_phase_144c_publication_coordinator.py`

---

## 2. Independent Field-Availability Audit (before writing any code)

Before touching any dataclass, every field IWC-REQ-185 names was checked
against what `Session`, `Preview`, `ConfirmationRequest`, and
`ConfirmationResponse` actually carry today, because IWC-REQ-185's own
text says the widened content is "copied unmodified from the bound
Session, Preview, and Confirmation state" — a claim that only holds if
that state already exists somewhere on those objects.

| IWC-REQ-185 field | Available today? | Source before this phase |
|---|---|---|
| Decision Subject | Yes | `Session.subject_ref` |
| Selected option identifier | Yes | `Session.human_selection_id` |
| Rationale / conditions text | Yes | `Session.human_rationale_text`/`human_conditions_text` |
| Confirmation timestamp | Yes | `ConfirmationResponse.confirmed_at` |
| Decision Template version | **No** | `Session.template_ref` is a single opaque identifier string; no version field existed |
| Full closed option-id set presented | **No** | No field, anywhere in `interactive_workflow`, ever recorded this |
| Decision-maker identity evidence (`evidence_kind`/`identifier`/`captured_at`) | **No** | `Session.owner_identity` is a bare string; no evidence-kind or capture-timestamp field existed |
| Exact rendered Preview content | **No** | `Preview` carried only reference tuples and an informational `transition_summary` (144E §3 Option D already flagged this) |
| Confirmation statement | **No** | `ConfirmationResponse` carried no phrase/statement field, only `confirmation_result` (a single-member enum) |

This independently confirms 144E §26.2's own root-cause finding
generalizes one layer further than 144E itself audited: 144E verified the
gap at the *Package* boundary; this phase's own audit found four of
IWC-REQ-185's nine fields were not merely dropped at Package construction
but were **never captured anywhere upstream of it either** — no
"discard" was occurring for these four, because there was nothing to
discard. Closing IWC-REQ-185 therefore required widening `Session` and
`Preview` themselves, not only `PublicationReadinessPackage` and
`PublicationHandoff.build_package` as 144E §26.6/§20.5's migration
tables named. This is disclosed here as a judgment call (§3 below), not
silently absorbed into "widen the Package."

---

## 3. Judgment Call — Widening `Session` and `Preview`, Not Only the Package

**Decision:** additively widen `Session` (three new, defaulted fields:
`template_version`, `options_presented`, `decision_maker_evidence_kind`)
and `Preview` (one new, defaulted field: `rendered_content`), in addition
to widening `PublicationReadinessPackage` and updating
`PublicationHandoff.build_package`/`WorkflowOrchestrator.
stage_preview_construction` to thread the new values through.

**Reason:** §2's audit is decisive — four of IWC-REQ-185's nine required
fields have no representation anywhere in `interactive_workflow` prior to
this phase. "Populate every newly required field directly from the
objects already available at package construction time" (this phase's
own governing prompt) presupposes those objects already carry the data;
where they provably do not, the alternative to widening them would be
inventing values at Package-construction time from nothing, which is
exactly the "reconstruction"/"inferred values" this phase's own CHGR
Population section forbids, one layer earlier. Widening `Session`/
`Preview` is additive only (every new field carries a safe, non-breaking
default; no existing field is removed, renamed, or reinterpreted) and
does not redesign the ten-state session model, the AI/Human
Responsibility Contracts, or the Confirmation mechanics — it only adds
places to carry content those existing contracts already presuppose a
real session captures somewhere.

**Scope discipline preserved despite the wider file list:**
`decision_maker_evidence_kind` defaults to `"typed_confirmation_only"`
(CHGR-001's own L0 definition — "evidence of deliberate intent only, no
identity binding beyond whoever operated the session" — which is exactly
what this system's `Session.owner_identity` field alone actually
supports; no L1 `os_authenticated_user` capture path exists anywhere in
this codebase, so defaulting to the L0 characterization is honest, not
an overclaim). No new subsystem dependency was introduced by this
widening: every new field is populated exclusively from arguments
`PublicationHandoff.build_package` and `WorkflowOrchestrator.
stage_preview_construction` already receive.

---

## 4. What Changed

### 4.1 `Session` (`interactive_workflow/models/session.py`)

Added, additively, with safe defaults (`with_state` updated to carry them
through unchanged):

- `template_version: str = ""`
- `options_presented: Tuple[str, ...] = ()`
- `decision_maker_evidence_kind: str = "typed_confirmation_only"`
  (validated against the two `evidence_kind` values CHGR-001's identity
  schema actually defines)

### 4.2 `Preview` (`interactive_workflow/preview/models.py`,
`preview/builder.py`, `orchestration/coordinator.py`)

Added `rendered_content: str = ""` (IWC-REQ-188): the exact, literal
rendered Preview text, captured exactly once at Preview-generation time.
`PreviewBuilder.build`/`WorkflowOrchestrator.stage_preview_construction`
both gained a `rendered_content` parameter that threads straight through
to `Preview`'s constructor — no re-rendering downstream. `rendered_content`
is included in Preview Digest computation (`_canonical_payload`), so any
tampering with it after digest generation is detected exactly like
tampering with any other Preview field (verified by
`test_preview_rendered_content_is_part_of_digest`).

### 4.3 `PublicationReadinessPackage`
(`interactive_workflow/publication_handoff/models.py`)

Added, additively (existing fields unchanged, per IWC-REQ-186):
`decision_subject`, `template_id`, `template_version`,
`selected_option_id`, `rationale_text` (optional), `conditions_text`
(optional), `options_presented`, `decision_maker_identity_evidence` (a
frozen mapping), `preview_rendered_content`, `confirmation_statement`,
`confirmation_timestamp`. All collection/mapping fields are frozen in
`__post_init__` exactly as the pre-existing `evidence_refs`/`metadata`
fields already were (IWC-REQ-187: same immutability discipline extended
to content granularity).

### 4.4 `PublicationHandoff.build_package`
(`interactive_workflow/publication_handoff/handoff.py`)

Populates every new Package field directly from the `Session`, `Preview`,
and `ConfirmationResponse` objects the method already received as
arguments — no new parameter, no new import, no re-derivation beyond one
deterministic, non-discretionary mapping:
`confirmation_statement = confirmation_response.confirmation_result.value`
(i.e. the literal string `"Accepted"` — the only member
`ConfirmationResult` defines; not an independent judgment, a direct
rendering of already-captured enum content, mirroring PEC-REQ-115's
"MAY construct... never from independent judgment" discipline one layer
earlier). Added a new fail-closed precondition: a `Confirmed` session
missing `human_selection_id` is rejected with
`PublicationHandoffIncompleteError` before Package construction is even
attempted (a session that reached `Confirmed` without ever capturing a
selection cannot supply IWC-REQ-185's required verbatim selected-option
identifier).

`validate_completeness` was extended to require every IWC-REQ-185 field
that is not marked "where supplied" (`decision_subject`, `template_id`,
`template_version`, `selected_option_id`, `options_presented`,
`decision_maker_identity_evidence`, `preview_rendered_content`,
`confirmation_statement`, `confirmation_timestamp`); `rationale_text`/
`conditions_text` remain optional, matching IWC-REQ-185's own text.

### 4.5 `governance/publication/record.py`

`build_publication_record` now populates three new top-level structures —
`human_governance_record`, `human_confirmation_evidence`,
`governance_record_provenance` — directly and only from the widened
Package's verbatim fields (PEC-REQ-112), never independently fetched,
computed, or re-derived (PEC-REQ-113: no new import of
`interactive_workflow` internals was introduced; every value populated
here was already reachable through the Package before this phase's
widening made it substantive rather than reference-only).

**Disclosed, remaining limitation:** `authority_basis_claimed`
(CHGR-001 §10/§11) is *not* populated. It is a claim citing the bound
Decision Template's own `eligible_authority` text (CHGR-REQ-096); no
Decision Template model exists anywhere in this repository carrying an
`eligible_authority` field — `Session.template_ref`/`template_version`
are opaque identifiers only. PEC-REQ-115 states the Coordinator *MAY*
construct this field "where the widened Package's verbatim `template_ref`
content resolves... to that template's own `eligible_authority` text" —
it does not resolve here, so this record does not invent a citation the
Package does not carry. This is the same fail-closed discipline
CHGR-001/PEC-001 apply everywhere else in this codebase: an unavailable
value is disclosed as absent, never fabricated to look complete. Full
schema-envelope fields for the three new structures (their own
independent `record_id`/`record_digest`/`assurance_level`/
`lifecycle_state`, cross-artifact reference digests, as fully separate,
independently schema-validated CHGR artifacts) are likewise not
constructed here — assigning independent canonical identity to three
sub-structures is a materially larger undertaking than "populate this
record's already-existing single JSON body with the Package's verbatim
content," and this phase's own scope (widen the Package; populate its
content into the Coordinator's existing record shape) does not authorize
it. `_KNOWN_LIMITATIONS` was narrowed to state exactly these two residual
items, replacing the prior, now-resolved "package_reference carries
identifier/digest references only" disclosure.

---

## 5. Boundary Preservation — Verified

- `src/pcae/governance/publication/coordinator.py`,
  `models.py`, `storage.py`, `errors.py`, `serialization.py` — **zero
  files touched** (Forbidden Files for this phase; only `record.py`
  changed inside `governance/publication/`).
- `PEC-REQ-018`–`020`'s placement/dependency boundary: unaffected. No new
  import of `pcae.interactive_workflow.session`, `.orchestration`,
  `.evidence`, `.clarification`, `.preview`, `.confirmation`,
  `.state_machine`, `.audit`, or `pcae.cltr` was introduced anywhere
  under `governance/publication/` — re-verified by re-running
  `tests/test_phase_144c_publication_coordinator.py`'s
  `_FORBIDDEN_IMPORT_ROOTS`-parametrized test (`test_coordinator_package_
  has_no_forbidden_imports`), unmodified, still passing.
- `docs/contracts/**` — zero files touched (this is an implementation
  phase; the contract text IWC-001 v1.2/PEC-001 v1.1 already froze in
  Phase 144E governs this phase's obligations unchanged).

---

## 6. Provenance Integrity — Verified

- Every new field is captured exactly once, at the moment
  `PublicationHandoff.build_package` (or, for `rendered_content`,
  `PreviewBuilder.build`) runs, and is never recomputed, regenerated, or
  modified after that point (`PublicationReadinessPackage`/`Preview`
  remain `@dataclass(frozen=True)`; `test_package_provenance_fields_are_
  immutable` independently confirms both attribute reassignment and
  in-place mutation of the frozen `decision_maker_identity_evidence`
  mapping are rejected).
- No duplicate source of truth was introduced: `record.py`'s three new
  structures read the Package's own fields directly; nothing is fetched
  from `Session`/`Preview`/`ConfirmationResponse` a second time at
  record-construction time.

---

## 7. Tests

### 7.1 New tests (`tests/test_iwc_143o_session_coordination_publication_handoff.py`)

- `test_package_carries_verbatim_provenance_from_session_preview_confirmation`
  — every new field populated correctly from a real Confirmed-session
  flow.
- `test_package_carries_optional_rationale_and_conditions_where_supplied`
  — optional fields populate when supplied.
- `test_package_rejects_confirmed_session_missing_human_selection_id` —
  fail-closed precondition.
- `test_package_provenance_fields_are_immutable` — attribute and
  in-place-mapping mutation both rejected.
- `test_package_serialization_round_trips_widened_fields` — full
  serialize/deserialize round-trip over the widened shape.
- `test_preview_rendered_content_is_part_of_digest` — two Previews
  differing only in `rendered_content` produce different digests.
- `_Blank` mock classes (pre-existing `validate_completeness` tests)
  updated with the new blank attributes so they continue to exercise the
  pre-existing-field validation path without an `AttributeError`.

### 7.2 New tests (`tests/test_phase_144c_publication_coordinator.py`)

- `_package()` helper updated to construct a fully-populated widened
  Package (every 144C test that calls it now exercises the widened
  shape).
- `test_published_record_carries_verbatim_chgr_provenance_content` —
  after a real `PublicationCoordinator.execute()`, reads the persisted
  JSON record from disk and asserts `human_governance_record`/
  `human_confirmation_evidence`/`governance_record_provenance` carry the
  Package's exact verbatim content, and that `record_digest` was
  recomputed over the full body including the new structures (never a
  stale digest computed before they were added).

### 7.3 Regression

| Suite | Command | Result |
|---|---|---|
| 143O + 144C combined | `pytest tests/test_iwc_143o_session_coordination_publication_handoff.py tests/test_phase_144c_publication_coordinator.py -q` | 83 passed |
| Forbidden-import boundary | `pytest tests/test_phase_144c_publication_coordinator.py -k "forbidden or lives_outside" -q` | 8 passed |
| Broad interactive_workflow/publication/preview/143/144 filter | `pytest tests/ -k "iwc or interactive_workflow or publication or preview or 143 or 144" -q` | 1551 passed, 1 skipped, 6 failed (all 6 are pre-existing wheel/sdist packaging failures, independently reconfirmed present on `main` before this phase's changes via `git stash`) |
| `fast_green` | `pytest -m fast_green -n auto -q` | 4391 passed — matches Phase 144D's own recorded baseline exactly |
| Full repository suite | `pytest -n auto -q` | 72 failed, 26274 passed, 10 skipped |

Full-suite failure triage: every one of the 72 failures was checked by
name against this phase's diff (`git diff --stat`, touching only
`governance/publication/record.py`, seven `interactive_workflow/**`
files, and two test files). None references `interactive_workflow`,
`publication`, `preview`, `confirmation`, `session`, `143`, or `144` in a
way connected to this phase's own subject matter: the two matches
containing "publication" (`test_cltr_authority_136ah_publication.py`) and
"143e" (`test_chgr_packaging.py::test_143e_*`) are, respectively, the
unrelated CLTR Typed-Authority-Model "publication" record family
(`pcae.cltr.authority`, independently confirmed structurally disjoint
from CHGR by IWC-001 §19.1/CHGR-001 §19.1 and untouched by this phase)
and CHGR schema wheel-packaging (`schema_resources/chgr/**`, also
untouched). All are wheel/sdist `python -m build` subprocess failures or
known order-dependent flakes, independently reconfirmed present on `main`
prior to this phase's changes by re-running two representative failures
(`test_chgr_packaging.py::test_143e_wheel_contains_all_six_chgr_record_schemas`,
`test_cltr_cutover_136u_...::test_136u_no_runtime_code_references_group10_families_outside_schema_resources`)
against a stashed, unmodified working tree — both fail identically on
`main`. `test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`
appeared as a full-suite failure but passed standalone both before and
after this phase's changes, confirming pre-existing order-dependent
flakiness under parallel full-suite execution, not a regression this
phase introduced. The failure count (72) differs from Phase 144D's
recorded baseline (40) and Phase 144C's own recorded count (73) for this
same class of pre-existing, environment-dependent failure; this phase
does not reconcile that count-drift, consistent with Phase 144D §10's own
disclosure that this drift is unrelated to any specific phase's diff.

---

## 8. Validation

```
$ pcae check
PCAE check passed.

$ pcae health
Health check: warnings resolved (task-memory gap closed by recording the
prior idle-task closure in tasks/DONE.md); otherwise healthy.

$ pcae doctor execution-chain
Execution chain doctor (all): OK — 0 errors, 0 warnings.

$ pcae doctor task-memory
Task memory: clean.

$ pcae doctor git-lock
Status: ok.

$ pcae push check
Push readiness check: Health healthy, Check passed, Task memory clean,
mode nothing_to_push (prior to this phase's own commit).
```

Runtime confirmed unchanged: `pcae runtime inspect` reports Runtime
state Observed, execution capability unavailable, maximum plugin
capability observe, identical before and after this phase.

---

## 9. Explicit No-Go — Confirmed Observed

This phase did not: redesign Interactive Workflow's ten-state model,
AI/Human Responsibility Contracts, or Confirmation mechanics (only
additive, defaulted fields were added to `Session`/`Preview`); redesign
Publication Coordinator (zero files under
`src/pcae/governance/publication/coordinator.py`/`models.py`/`storage.py`/
`errors.py`/`serialization.py` touched); redesign CHGR (`CHGR-001`,
every `schema_resources/chgr/**` file byte-identical); introduce a
Coordinator read interface into `interactive_workflow/**` (no new import
was added anywhere under `governance/publication/`); introduce any new
CLI command; introduce any runtime capability; or weaken
`_FORBIDDEN_IMPORT_ROOTS`/the AST-enforced boundary test (re-run
unmodified, still passing).

---

## 10. Exit Criteria — Self-Assessment

1. `PublicationReadinessPackage` implements `IWC-REQ-185`–`190` — §4.1–4.3.
   ✅
2. `PublicationCoordinator`/`record.py` implements `PEC-REQ-111`–`117` —
   §4.5. ✅ (with the disclosed `authority_basis_claimed` and
   schema-envelope limitations, §4.5, honestly stated rather than
   fabricated)
3. CHGR fields populated solely from immutable package content — §4.5,
   §6. ✅
4. No new subsystem dependencies; AST boundary enforcement intact — §5.
   ✅
5. Runtime remains unchanged — §8. ✅
6. Full regression passes — §7.3 (all non-passing results independently
   reconfirmed pre-existing/unrelated). ✅
7. No contract reinterpretation occurred — this phase implemented
   IWC-001 v1.2/PEC-001 v1.1 exactly as Phase 144E froze them; the
   `Session`/`Preview` widening (§3) is a disclosed implementation
   judgment call about *where* to source data those contracts already
   presuppose exists, not a reinterpretation of any `IWC-REQ`/`PEC-REQ`
   text. ✅

---

## 11. Recommended Next Phase

**144G — Provenance Boundary Independent Verification.** Would
independently re-derive (not trust this phase's own framing) whether
`IWC-REQ-185`–`190` and `PEC-REQ-111`–`117` are genuinely satisfied by
this phase's implementation, adversarially test the widened Package's
immutability/authority-neutrality/publication-neutrality discipline,
confirm the `Session`/`Preview` widening judgment call (§3 above) was
necessary and sufficient rather than over- or under-scoped, and assess
whether the disclosed `authority_basis_claimed`/schema-envelope
limitations (§4.5) constitute a new Blocking finding requiring a further
contract revision, mirroring the 144C→144D precedent.

**This recommendation does not authorize 144G.**
