# Phase 134E.3 — Phase Report View Composition

## 1. Objective

Implement a deterministic, structured Phase Report View Composition
layer over the verified `phase_report_v1` Evidence Extraction result
(134E.2, independently verified and repaired by 134E.2V). Composition
answers exactly one question: "how shall the extracted canonical
evidence be organized into the thirteen PFR-001 Phase Report sections?"
It never creates engineering evidence, never re-runs extraction, never
queries Canonical Engineering Evidence directly, never infers missing
facts, never strengthens conclusions, and never generates rendered
prose (Markdown/plain-text/HTML) or delivers anything.

## 2. Architectural Position

```
Canonical Engineering Evidence
        |
        v
Evidence Extraction
        |
        v
Phase Report View Composition        <- this phase
        |
        v
Rendering                             (not implemented)
        |
        v
Delivery                              (not implemented)
```

Composition consumes only an already-produced `ExtractionResult` for
the `phase_report_v1` profile. It never bypasses Evidence Extraction —
it accepts no Canonical Engineering Evidence object directly and has
no import of `canonical_engineering_evidence` beyond the three shared
enums (`Applicability`, `FindingClassification`, `PhaseClass`) needed
to interpret extraction values without re-deriving them.

Composition decides: section assignment, grouping, section ordering,
evidence-item ordering, structured labels, phase-class-specific section
treatment, explicit not-applicable treatment, structured completeness
presentation, and disclosed-filtering placement.

Rendering (a later, distinct phase) decides: Markdown syntax,
plain-text layout, HTML layout, line wrapping, and channel-specific
formatting. This phase implements none of that; the responsibilities
are not merged.

Only Phase Report View Composition (`phase_report_v1`) is implemented.
**Operator Report View Composition is explicitly out of scope** — a
Strict Non-Goal of this phase — and is left for a later, dedicated
phase.

## 3. Authority Boundary

Canonical Engineering Evidence remains the only future authoritative
engineering record. Evidence Extraction remains derivative. Phase
Report View Composition is a **derivative structured view** — it never
becomes canonical evidence, independent engineering history,
report-delivery authority, phase-completion authority, repository-state
authority, or notification authority.

**This module is not yet active lifecycle authority.** Nothing in the
current governed reporting/finalization/notification path
(`pcae.core.phase_reports`, `pcae.core.notifications`,
`pcae.core.notification_certification`,
`pcae.core.repository_transition_validator`, or any CLI command)
imports or calls into `pcae.core.phase_report_view`, and this module
imports only `pcae.core.evidence_extraction`,
`pcae.core.canonical_engineering_evidence`, and the standard library.
The current governed reporting and finalization path remains the sole
active authority and is completely unaffected by this phase. Confirmed
via a fresh full-source-tree scan (test suite, below) and by
`git diff --stat` at finalization showing zero files outside this
phase's own allowed-file list touched.

## 4. Composed View Model

`PhaseReportView` (frozen dataclass) contains:

- `view_id`, `view_version` — deterministic identity
  (`phase-report-view:{source_evidence_id}:{profile_id}`), no random
  UUID, no timestamp, no agent/model/process state.
- `source_evidence_id`, `source_record_digest`,
  `source_extraction_digest` — full traceability back to the exact
  Canonical Engineering Evidence record and the exact
  `ExtractionResult` this view was composed from.
- `profile_id`, `profile_version` — always `phase_report_v1` (composing
  from any other profile is fail-closed rejected).
- `phase_id`, `phase_class` — the exact, ungeneralized phase identity
  and phase class carried through unchanged from extraction (never
  re-derived from headings or free text).
- `report_status` — a fixed structural marker (`"composed"`); no
  finalization/delivery status is invented here (that remains PFN-001's
  and the active `phase_reports.py`'s concern).
- `completeness` — a `ViewCompleteness` value (COMPLETE /
  COMPLETE_WITH_LIMITATIONS / INCOMPLETE / INVALID), computed per
  Section 9 below.
- `sections` — exactly thirteen `SectionRecord` entries, in PFR-001
  order (Section 6).
- `cross_section_uncertainty`, `cross_section_limitation` — the
  report-level bundle of every uncertainty/limitation category the
  source extraction carried, deduplicated and sorted, independent of
  which section(s) individually reference them.
- `filtering_disclosures` — the report-level bundle of every category
  extraction disclosed as intentionally excluded.
- `diagnostics` — view-level `CompositionDiagnostic` entries
  (currently: `unassigned_required_evidence`, structurally unreachable
  given the fixed category-to-section map, Section 8).

No rendered prose is stored anywhere in this model — every field is a
structured reference (category name, requirement level, applicability,
classification) resolvable against the source `ExtractionResult`, never
a copy of canonical content beyond what extraction already selected.
This keeps the model suitable for a future Markdown, plain-text, HTML,
or JSON renderer without committing to any one of them.

## 5. Section Model

`SectionRecord` (frozen dataclass) represents one PFR-001 section:

- `section_id` (`PFRSectionId`), `order` (1-13, PFR-001 order).
- `applicability` (`SectionApplicability`): MATERIALLY_POPULATED,
  NOT_APPLICABLE, UNAVAILABLE_WITH_DISCLOSURE, INCOMPLETE, or INVALID.
- `completeness` (`SectionCompleteness`): COMPLETE,
  COMPLETE_WITH_LIMITATIONS, INCOMPLETE, or INVALID.
- `evidence_groups` — a tuple of `EvidenceGroupRef` (category,
  requirement level, applicability, `is_primary` flag, and a sorted
  tuple of any `FindingClassification` values found in the selected
  value — both original and post-repair classifications, never only
  the final one).
- `missing_required_categories`, `uncertainty_categories`,
  `limitation_categories`, `filtering_disclosure_categories`,
  `provenance_categories` — deterministic, sorted, per-section subsets
  of the corresponding report-level bundles.
- `diagnostics` — section-level `CompositionDiagnostic` entries.
- `not_applicable_reason` — required (and only present) exactly when
  `applicability == NOT_APPLICABLE`; enforced at construction (a
  `ValueError` on mismatch), so a NOT_APPLICABLE section can never
  exist without a stated reason, and no other section can carry a
  spurious reason field.

A required section never disappears: all thirteen `PFRSectionId`
values are composed unconditionally, every time — a heading alone is
never treated as completeness (Section 9).

## 6. All Thirteen PFR-001 Sections

Section assignment (`_SECTION_CATEGORY_MAP`) is a fixed, explicit
dictionary from `PFRSectionId` to a deterministic tuple of extraction
categories — never heuristic text classification.

| # | Section | Source categories |
|---|---|---|
| 1 | Phase Identity | `identity`, `repository_state`, `commit_and_push` |
| 2 | Executive Summary | `objective`, `engineering_actions`, `architectural_findings`, `implementation_findings`, `verification_findings`, `defects_discovered`, `defects_repaired`, `runtime_state`, `recommended_next_phase` |
| 3 | Architectural Findings | `architectural_findings` |
| 4 | Implementation Findings | `implementation_findings` |
| 5 | Verification Findings | `verification_findings`, `defects_discovered`, `defects_repaired`, `incorrect_assumptions_corrected` |
| 6 | Technical Debt Review | `technical_debt_reviewed`, `technical_debt_introduced` |
| 7 | Notable Engineering Knowledge | `notable_engineering_knowledge` |
| 8 | Governance Results | `governance_results` |
| 9 | Test Results | `test_results` |
| 10 | No-Go Confirmation | `no_go_confirmations` |
| 11 | Architectural Boundary Confirmation | `architectural_boundary_confirmations`, `runtime_state` |
| 12 | Track Progress | `track_progress` |
| 13 | Next Phase | `recommended_next_phase` |

Each of the 21 `EXTRACTION_CATEGORIES` has exactly one *primary*
owning section (`_CATEGORY_PRIMARY_SECTION`) — the section that carries
its full history. A category may additionally be *referenced* by other
sections (e.g. `defects_discovered`/`defects_repaired` are both
referenced by Executive Summary and owned by Verification Findings;
`architectural_findings` is referenced by Executive Summary but owned
by Architectural Findings), but only the primary section's
`EvidenceGroupRef.is_primary` is `True` — cross-section reuse is always
named, never inferred (Section 8).

## 7. Phase-Class Behavior

`_CONDITIONAL_SECTIONS` — Architectural Findings, Implementation
Findings, Verification Findings, No-Go Confirmation — are the sections
whose *absence* of selected content is expected for some phase
classes/profiles, per PFR-001's own phase-class applicability table
(133B Section 6). When every category mapped to one of these sections
comes back unselected *and* extraction's own diagnostics show none of
them as `required`/`invalid`-missing, composition marks the section
`NOT_APPLICABLE` with an explicit, generated reason naming the phase
class and profile — never silent absence, never a fabricated reason.

Every other section (Phase Identity, Executive Summary, Technical Debt
Review, Notable Engineering Knowledge, Governance Results, Test
Results, Architectural Boundary Confirmation, Track Progress, Next
Phase) is mandatory-populated across all six phase classes with no
class-dependent variation, matching 133B Section 6's own uniform
applicability rule.

## 8. Section Assignment Rules and Non-Omission

Every category `extract()` selects is looked up in
`_CATEGORY_PRIMARY_SECTION` and assigned to exactly one primary
section. After composing all thirteen sections, composition computes
`unassigned = selected_categories - assigned_categories` and raises a
`blocking` `unassigned_required_evidence` diagnostic if it is
non-empty. Because `_CATEGORY_PRIMARY_SECTION` is statically defined to
cover every one of the 21 `EXTRACTION_CATEGORIES` (asserted directly by
`test_unassigned_evidence_rejected`), this path is structurally
unreachable today — but the accounting mechanism itself runs on every
composition, not only in tests, so a future category addition that
forgets to name a primary section fails closed immediately rather than
silently dropping evidence.

Findings/repair history is never collapsed to only the final state: a
`RepairRecord`'s `original_finding.classification` (e.g. BLOCKING) and
its own `resulting_status` (e.g. CONFIRMED) are both captured in
`EvidenceGroupRef.finding_classifications`, sorted and deduplicated,
and the full record remains directly retrievable through the
underlying `ExtractionResult.selected_evidence` this view references.

## 9. Completeness

`SectionCompleteness` and `ViewCompleteness` mirror
`ExtractionCompleteness`'s four values. Per-section completeness is
computed from the section's own composed evidence (any BLOCKING-shaped
contradiction -> INVALID; any hard-required-and-missing category ->
INCOMPLETE; a structurally-empty non-conditional section ->
INCOMPLETE, with a `structurally_empty_required_section` diagnostic;
any conditionally-required-and-missing category on an otherwise
populated section -> COMPLETE_WITH_LIMITATIONS; otherwise COMPLETE).

View-level completeness starts at the source `ExtractionResult`'s own
`completeness` value as a **floor** and is only ever moved to an
equal-or-worse rank (`complete` < `complete_with_limitations` <
`incomplete` < `invalid`) if composition independently detects a
defect (a blocking section/view diagnostic, or any section reaching
INCOMPLETE/INVALID). Composition never reports a better rank than
extraction's own (Non-Strengthening, Section 10) — `_worse()` is a pure
total-order comparison used everywhere completeness is combined.

An extraction result already reported `INVALID` is rejected outright
(`compose_phase_report_view` raises before composing anything) — there
is nothing safe to compose from a genuine contradiction.

## 10. Non-Omission and Non-Strengthening

**Non-Omission**: every selected extraction category is accounted for
by the assignment mechanism (Section 8); every uncertainty/limitation
category present on the source `ExtractionResult` is copied, sorted
and deduplicated, into the report-level `cross_section_uncertainty`/
`cross_section_limitation` bundles regardless of which section(s) also
reference it individually; every filtering disclosure is copied into
`filtering_disclosures`. Nothing extraction disclosed is dropped by
composition.

**Non-Strengthening**: composition never transforms a classification.
`FindingClassification` values are copied verbatim from the selected
value's own `FindingRecord`/`RepairRecord` objects — never re-derived,
never inferred, never merged into a single "resolved" state. UNKNOWN/
UNAVAILABLE/OMITTED_INVALID_INPUT dispositions are never composed as
NOT_APPLICABLE (a category only becomes NOT_APPLICABLE-shaped in a
section when the extraction profile itself marked it not applicable
for the phase class **and** the evidence record agrees by leaving it
genuinely absent — never when the evidence record disclosed it as
missing-with-uncertainty). `GovernanceResultItem`/`TestResultItem`
status strings (e.g. `"warning"`, `"failed"`) are never rewritten;
composition only ever reads `.status`/`.value`, never assigns to them
(these are frozen dataclasses; mutation is impossible at the language
level regardless).

## 11. Uncertainty, Limitations, and Filtering Disclosures

Uncertainty/limitation categories are surfaced at two levels
simultaneously: per-section (`SectionRecord.uncertainty_categories`/
`limitation_categories`, derived from each selected item's own
`uncertainty_refs`/`limitation_refs`) and report-level
(`PhaseReportView.cross_section_uncertainty`/
`cross_section_limitation`, the full deduplicated bundle from the
source `ExtractionResult`). Neither view is a substitute for the
other — a reader (or future renderer) inspecting only one section would
still see that section's own disclosures; a reader wanting the full
picture reads the report-level bundle. Filtering disclosures follow
the identical two-level pattern
(`filtering_disclosure_categories`/`filtering_disclosures`).

## 12. Determinism

Composition is a pure function of `(ExtractionResult, view_version)`.
Every collection on `PhaseReportView`/`SectionRecord` is sorted or
placed in a fixed, pre-determined order at construction time (the
static `PFR_SECTION_ORDER` tuple for sections; `sorted(set(...))` for
uncertainty/limitation/filtering/provenance category bundles) — never
dictionary or registry insertion order. Verified across: repeated
in-process composition from the same `ExtractionResult`
(`test_deterministic_section_ordering`,
`_deterministic_item_ordering`, `_deterministic_serialization`,
`_stable_view_digest`); a fresh subprocess re-derivation
(`test_cross_process_determinism`, matching 134E.1/134E.2's own
cross-process convention); and no dependency anywhere in the module on
agent identity, model identity, transport, rendering context, or
delivery context (Section 13).

## 13. Validation and Failure

`compose_phase_report_view()` is fail-closed (raises `ValueError`) for:

- an unsupported `view_version`;
- an extraction result produced under a profile other than
  `phase_report_v1` (e.g. `operator_report_v1` is rejected outright —
  composition never silently accepts a result built for a different
  audience);
- an `ExtractionCompleteness.INVALID` extraction result;
- a missing `source_evidence_id`/`source_record_digest`;
- an orphan uncertainty/limitation reference on a selected item
  pointing to an unknown category (defense in depth — this should
  already be unreachable given Evidence Extraction's own orphan check,
  re-verified here by constructing a deliberately corrupted
  `ExtractionResult` via `dataclasses.replace`);
- a structurally empty successful report (every section
  NOT_APPLICABLE/UNAVAILABLE_WITH_DISCLOSURE) — refused even if every
  individual check above passed, matching the identical
  silent-empty-success guard 134E.2 established for extraction itself.

It returns normally (never raises) for every ordinary
evidence-completeness outcome — COMPLETE, COMPLETE_WITH_LIMITATIONS, or
INCOMPLETE are all inspectable results read from
`PhaseReportView.completeness` and per-section `SectionRecord.
completeness`/`.diagnostics`, never hidden behind an exception.

## 14. Planning-Phase Observation (carried forward from 134E.2V)

134E.2V's NON-BLOCKING observation asked whether the current Canonical
Engineering Evidence categories and extraction result contain enough
structured evidence for a meaningful Planning-phase Phase Report.
Composed directly: `test_phase_class_report[planning]` and
`test_status_only_report_rejected`/`test_empty_successful_report_
prohibited` (both exercised against `PhaseClass.PLANNING`) confirm a
Planning-phase evidence record composes into all thirteen sections with
the same structural guarantees as every other phase class, using only
existing fields — no expansion of the canonical model was needed and
none was made. **Result: the existing category set is sufficient for a
faithful Planning-phase Phase Report View.** No BLOCKING insufficiency
was found; the observation is resolved for this phase's scope and
requires no further action here.

## 15. Conditional-Requirement Observation (carried forward)

134E.2V also observed that conditionally-required semantics are
currently static (fixed per profile/phase-class at construction time)
rather than dynamically evaluated against a record's actual content.
Composition does not invent dynamic conditions — it treats the
extraction result's own `RequirementLevel`/`missing_required`/
`diagnostics` as authoritative and unconditionally trusts them. No new
limitation was discovered by composition beyond the one 134E.2V already
recorded; it remains an open, non-blocking observation for a future
phase, unrepaired here per this phase's own explicit instruction not to
repair it absent proof of a genuine BLOCKING defect (none was found).

## 16. Private Registry Observation (carried forward)

134E.2V's third observation — do not directly depend on or mutate
Evidence Extraction's private `_PROFILE_REGISTRY` — is satisfied by
construction: `phase_report_view.py` calls only `extract()` indirectly
(it never calls `extract()` itself; callers pass an already-produced
`ExtractionResult`) and imports no registry internals
(`_PROFILE_REGISTRY`, `register_profile`, `get_profile` are all absent
from this module's import list). Confirmed by
`test_existing_extraction_profile_unchanged`, which reads the public
`get_profile()` API only.

## 17. Package Boundaries

`pcae.core.phase_report_view` imports only:

- `pcae.core.evidence_extraction` (the `ExtractionResult`,
  `SelectedEvidenceItem`, `ExtractionCompleteness`, `RequirementLevel`,
  and `PROFILE_ID_PHASE_REPORT` types/constants it composes from);
- `pcae.core.canonical_engineering_evidence` (only the shared
  `Applicability`, `FindingClassification`, `PhaseClass` enums, needed
  to interpret already-selected values without re-deriving them);
- the standard library (`hashlib`, `json`, `dataclasses`, `enum`,
  `typing`).

It does not import, reference, or depend on: a Markdown/plain-text/HTML
renderer, Telegram, notification dispatch, delivery adapters,
filesystem persistence, network, Repository Intelligence query/service
behavior, or execution systems. Verified by
`test_no_renderer_dependency`, `test_transport_independence_no_
telegram_import`, `test_no_telegram_dependency`,
`test_no_filesystem_or_network_behavior`, and
`test_no_active_lifecycle_imports` (a source-line scan restricted to
actual `import`/`from` statements, avoiding the false-positive class
134E.2's own test suite already discovered and documented: a
docstring's *prose description* of what a module does *not* depend on
must never be mistaken for an actual dependency).

## 18. Serialization and View Digest

`PhaseReportView.to_dict()`/`compute_digest()` and
`SectionRecord.to_dict()` follow the identical convention 134E.1/134E.2
established: stable section order (the fixed `PFR_SECTION_ORDER`
tuple), stable item order (every collection pre-sorted or
pre-determined at construction time), explicit `view_version`, source
identity/digest, extraction profile/version, completeness, uncertainty,
limitations, filtering disclosures, diagnostics — and no secrets, no
rendered markup (this model has no field capable of holding either).
`compute_digest()` is a SHA-256 over the canonical sorted-key JSON
serialization, excluding the digest field itself; there is no approved
timestamp on this model to exclude (composition carries no timestamp of
its own — it inherits all determinism from its source extraction's own
digest). The digest changes whenever section assignments or
completeness materially change (`test_digest_changes_on_material_
section_change`) and whenever uncertainty or limitations change
(`test_digest_changes_on_uncertainty_change`,
`test_digest_changes_on_limitation_change`), and remains stable under
equivalent input ordering and across process boundaries
(`test_stable_view_digest`, `test_cross_process_determinism`).
Round-trip support through `json.dumps`/`json.loads` is confirmed
(`test_round_trip_serialization`); the model does not implement a
`from_dict()` constructor (unlike the two upstream models) because
`PhaseReportView` is a one-way derived product of composition, never
reconstructed independently — a future renderer consumes `to_dict()`'s
output directly rather than reconstructing dataclass instances from it.

## 19. Limitations

- **Operator Report View Composition is not implemented** — this phase
  is scoped to `phase_report_v1` only, per its own Strict Non-Goals; a
  later, dedicated phase must implement the `operator_report_v1`
  equivalent, reusing the same section/completeness/Non-Omission
  machinery this phase establishes where applicable.
- **No rendering, no delivery** — `PhaseReportView` produces no
  Markdown, plain-text, HTML, or JSON *output document*; `to_dict()`
  returns a structured Python dict, not a rendered artifact. A future
  Rendering phase consumes this structure; a future Delivery phase
  transports whatever Rendering produces.
- **No active lifecycle integration** — nothing in the current governed
  reporting/finalization/notification path is aware this module exists.
  A future integration phase must explicitly wire it in, and must do so
  without weakening any of the invariants this phase and its two
  predecessors (134E.1/134E.1V, 134E.2/134E.2V) established.
- The three NON-BLOCKING observations carried forward from 134E.2V
  (Sections 14-16 above) remain open for future phases except where
  this phase's own investigation resolved them (Section 14, planning-
  phase sufficiency — resolved; Sections 15-16 — still open, unrepaired
  as instructed).

## 20. Explicit Statement: Not Rendered, Not Delivered, Not Active

`PhaseReportView` is a structured, in-memory Python dataclass model. It
is never rendered to Markdown, plain-text, or HTML by this phase; it is
never written to any file, delivered to any notification sink, or
otherwise transported anywhere by this phase; and it is never consulted
by any currently active PCAE governance path (`pcae phase-report
create`, `pcae phase complete`, PFN-001 dispatch, or any CLI command).
The current governed reporting and finalization path
(`pcae.core.phase_reports`) remains the sole active authority,
completely unaffected by this phase, confirmed by a fresh full-tree
source scan (`test_no_consumer_references_phase_report_view_yet`) and
by the corresponding, correspondingly-updated 134E.2V regression
(`test_no_active_lifecycle_imports_fresh_scan`, narrowed to admit this
phase's own expected new isolated consumer, per Section 21 below).

## 21. Technical Debt Review

**134E.2V's own `test_no_active_lifecycle_imports_fresh_scan` asserted
zero consumers of `evidence_extraction` anywhere in the source tree.**
This was correct at the time it was written (no successor phase yet
existed) but was always going to be falsified by 134E.3's own
architecture — Phase Report View Composition is precisely the next,
still-isolated layer the roadmap always intended to add. **Repaired**
(not a new defect discovered by this phase; a pre-declared, expected
consequence of this phase's own scope) by narrowing the test's
assertion from "no file besides `evidence_extraction.py` itself may
reference `evidence_extraction`" to "no file besides
`evidence_extraction.py` and the one new, named, still-isolated
`phase_report_view.py` may reference it" — the invariant the test
actually protects (no *active-lifecycle* consumer) is unweakened; only
the previously-too-strict literal wording ("zero consumers of any
kind") is corrected to match the architecture's own always-intended
shape. This repair is recorded here rather than silently made, per
Non-Omission.

No other inherited technical debt item from 134E.1/134E.1V/134E.2/134E.2V
was found to be within this phase's scope. The three NON-BLOCKING
observations 134E.2V carried forward are addressed in Sections 14-16
above (one resolved, two remain open and unrepaired as instructed).

## 22. Notable Engineering Knowledge

A test asserting "zero consumers of X" is only valid as a *snapshot* of
an architecture mid-construction — the moment a subsequent phase adds
the very consumer the architecture always intended, that test's literal
wording becomes stale even though the *invariant* it protects (no
premature *active-lifecycle* wiring) remains fully valid. This is a
durable lesson for this repository's own multi-phase "layer, then
independently verify the layer, then build the next layer" pattern:
every "not yet active lifecycle authority" isolation test written for
layer N should be phrased, from the start, in terms of "no
*active-lifecycle* module references this" rather than "no module of
any kind references this," so a correctly-scoped layer N+1 does not
require a defensive correction to layer N's own verification suite —
exactly the correction this phase had to make to 134E.2V's own test
(Section 21). Future isolation-boundary tests in this lineage should
adopt the narrower, more precise phrasing from the outset.

## 23. Readiness Assessment

Phase Report View Composition is implemented, independently
self-tested (this phase's own 88 focused tests), and integrated into
the existing regression posture (928 combined focused+regression tests
across 134E.1/134E.1V/134E.2/134E.2V/134B.1-3/phase-identity-repair, all
passing; fast_green 4390/4390 passing this run). It remains fully
isolated from active lifecycle authority. **It has not been
independently verified by a dedicated adversarial verification phase**
— per this phase's own governing instruction, that is 134E.3V's job,
not this phase's own self-certification. 134E.3V must not begin from
this document's own claims as sufficient evidence; it must re-derive
them.

Recommended next phase: **134E.3V — Phase Report View Composition
Independent Verification.**
