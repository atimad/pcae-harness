# Phase 134E.2 — Evidence Extraction

## 1. Objective

Implement a deterministic, audience-aware, transport-independent
Evidence Extraction layer over the Canonical Engineering Evidence
executable model (134E.1, independently verified and repaired by
134E.1V). Extraction answers exactly one question: "which canonical
engineering facts are required for a particular derived view?" It
selects and preserves evidence; it does not compose report prose,
summarize findings, render content, deliver notifications, create new
engineering evidence, infer importance through model reasoning, rank
findings subjectively, or activate Canonical Engineering Evidence in
finalization.

## 2. Architectural Position

```
Canonical Engineering Evidence
        |
        v
Evidence Extraction              <- this phase
        |
        v
Derived Evidence View Composition   (134E.3/134E.4, not implemented)
        |
        v
Rendering                            (134E.5, not implemented)
        |
        v
Delivery                             (134E.6, not implemented)
```

Extraction decides which canonical facts are required, optional,
conditionally required, or not applicable for a given (profile,
phase_class) pair, and preserves full traceability for whatever it
selects. View Composition — a later, distinct phase — decides section
organization, headings, grouping, and presentation sequence. This phase
implements none of that; the responsibilities are not merged.

## 3. Authority Boundary

**This module is not yet active lifecycle authority.** Canonical
Engineering Evidence remains the only future authoritative engineering
record; extraction results are derivative selections that never become
independent authorities. Confirmed directly:

- Zero references to `evidence_extraction` in `phase_reports.py`,
  `notifications.py`, `notification_certification.py`,
  `notification_config.py`, `repository_transition_validator.py`, or
  `commands/phase.py`.
- The module's only internal import is `pcae.core.canonical_engineering_
  evidence`; everything else is standard library
  (`test_module_has_only_cee_and_stdlib_imports`).
- No filesystem, network, subprocess, or rendering call anywhere in the
  module (`test_no_filesystem_or_network_behavior`,
  `test_no_rendering_dependency`, `test_no_transport_or_telegram_
  dependency`).
- Extraction never mutates the source evidence record — confirmed by
  digest stability across repeated extraction calls
  (`test_existing_evidence_model_remains_immutable_after_extraction`).

The current governed reporting, finalization, and notification path is
completely unchanged and unaffected by this phase.

## 4. Extraction Profiles

A small, explicit profile registry (`register_profile()`/`get_profile()`
— a dict, not a plugin framework) holds `ExtractionProfile` instances.
Each profile is a pure policy: `profile_id`, `profile_version`,
`supported_phase_classes`, and a fixed-order tuple of `CategoryRule`
entries, one per extraction category, each mapping every one of the six
`PhaseClass` values to an explicit `RequirementLevel` — no implicit
defaults, no category silently unspecified for any phase class
(`ExtractionProfile.__post_init__` raises if any category is missing a
rule; `CategoryRule.__post_init__` raises if any phase class is missing
a requirement level). Profile registration order never affects
extraction output for an existing profile — each profile's own category
order is fixed at construction time
(`test_future_profile_extensibility_without_existing_profile_change`
registers a brand-new profile and confirms the Phase Report profile's
own serialized rule set is byte-identical before and after).

Two profiles are implemented: `phase_report_v1` and `operator_report_v1`.

### 4.1 Extraction Categories

Twenty-one categories, each mapping 1:1 to an exact
`CanonicalEngineeringEvidence` field name — no invented pseudo-categories,
direct traceability from category name to canonical source field:
`identity`, `objective`, `engineering_actions`, `architectural_findings`,
`implementation_findings`, `verification_findings`, `defects_discovered`,
`defects_repaired`, `incorrect_assumptions_corrected`, `technical_debt_
reviewed`, `technical_debt_introduced`, `notable_engineering_knowledge`,
`governance_results`, `test_results`, `repository_state`, `runtime_state`,
`no_go_confirmations`, `architectural_boundary_confirmations`,
`track_progress`, `recommended_next_phase`, `commit_and_push`.

Twelve of these are tracked by CEE's own `applicability` mapping
(134E.1's `REQUIRED_APPLICABILITY_CATEGORIES`); the remaining nine are
scalar/always-populated fields a FINALIZED record cannot exist without,
and are treated as `PRESENT` by construction.

**Deliberately absent**: "notification/finalization result." Track 133F
confirmed this exclusion directly ("notification dispatch result...
correctly outside the Canonical Engineering Evidence model," owned by
PFN-001 instead). Extraction cannot select a fact the canonical record
does not carry, and does not invent one — it does not query
notification/delivery state and imports nothing from
`pcae.core.notifications`.

## 5. Phase Report Extraction Profile

Selects evidence for all thirteen PFR-001 sections
(`test_all_pfr_categories_represented_in_phase_report_extraction`
confirms every PFR-001 source category is covered — selected, disclosed
as filtered, or recorded as missing). Per 133B §6's own applicability
table:

- `implementation_findings`: `REQUIRED` only for `IMPLEMENTATION`;
  `NOT_APPLICABLE` for architecture/contract/planning/verification;
  `CONDITIONALLY_REQUIRED` for review/hardening (may legitimately
  include implementation work).
- `verification_findings`: `REQUIRED` only for `VERIFICATION`;
  `NOT_APPLICABLE` for architecture/contract/planning;
  `CONDITIONALLY_REQUIRED` for implementation (regression summary, per
  133B §6) and review/hardening.
- `architectural_findings`: `REQUIRED` by default (architecture,
  contract, planning, review/hardening); `CONDITIONALLY_REQUIRED` for
  implementation/verification (may or may not touch architecture).
- `technical_debt_reviewed`: `REQUIRED` for every class (133B §5: at
  least one explicit pass, even if "no change," is always required).
- `technical_debt_introduced`: `OPTIONAL` everywhere (not every phase
  introduces new debt).
- `defects_discovered`/`defects_repaired`/`incorrect_assumptions_
  corrected`: `CONDITIONALLY_REQUIRED` everywhere — must be represented
  with an explicit disposition (CEE's own construction already
  guarantees this for all twelve applicability-tracked categories), need
  not be non-empty.
- `no_go_confirmations`: `CONDITIONALLY_REQUIRED` everywhere.
- Every other category (identity, objective, engineering_actions,
  notable_engineering_knowledge, governance_results, test_results,
  repository_state, runtime_state, architectural_boundary_confirmations,
  track_progress, recommended_next_phase, commit_and_push): `REQUIRED`
  for all six classes, per 133B §6's default ("all other sections
  mandatory across all six phase classes with no class-dependent
  variation").

## 6. Operator Report Extraction Profile

Broader than the Phase Report profile by design — a minimal status/
tests/next-phase-only extraction is explicitly invalid for this profile,
confirmed by test
(`test_operator_report_status_only_extraction_is_invalid`). Differs from
the Phase Report profile specifically in making `defects_discovered`,
`defects_repaired`, `incorrect_assumptions_corrected`, and
`technical_debt_reviewed` hard `REQUIRED` (not merely conditionally
required) across all phase classes, so an operator — especially on
mobile — can always determine what defects were found, what was
repaired, what assumptions were corrected, and what debt was reviewed,
without needing a separate content check
(`test_operator_decision_completeness_categories_represented`).
`architectural_findings`/`implementation_findings`/`verification_
findings` follow the same class-conditioned rules as the Phase Report
profile (an operator cannot be told about architecture/implementation/
verification work that genuinely didn't happen for a given phase class).

## 7. Phase-Class Awareness

Both profiles define an explicit requirement level for every one of the
six `PhaseClass` values (architecture, contract, planning, implementation,
verification, review_hardening) for every one of the twenty-one
categories — 42 category-rule objects × 6 phase classes = 252 explicit,
inspectable requirement-level entries per profile, none defaulted
implicitly. Confirmed per phase class by parametrized test
(`test_phase_report_extraction_per_phase_class`,
`test_operator_report_extraction_per_phase_class`).

## 8. Extraction Result Model

`ExtractionResult` (frozen, deep-immutable via the same tuple/
`MappingProxyType`-forcing discipline 134E.1V's own repair established)
carries: `source_evidence_id`, `source_record_digest`, `profile_id`,
`profile_version`, `phase_class`, `selected_evidence` (tuple of
`SelectedEvidenceItem`), `missing_required`, `uncertainty`, `limitations`,
`provenance`, `filtering_disclosures`, `completeness`, `diagnostics`.
Never flattened into free text — `to_dict()`/`compute_digest()` follow
the identical convention 134E.1 established (sorted-key JSON,
`extraction_digest` field excluded from its own input).

Each `SelectedEvidenceItem` preserves: `category`, `source_evidence_id`,
`value` (the exact, untouched canonical value — never re-derived,
summarized, or copied-and-altered), `applicability`, `requirement_level`,
`provenance` (filtered to that category), `verification_state`,
`uncertainty_refs`/`limitation_refs` (filtered to that category),
`selection_reason`.

## 9. Completeness

`ExtractionCompleteness`: `COMPLETE`, `COMPLETE_WITH_LIMITATIONS`,
`INCOMPLETE`, `INVALID`. Deterministic classification rule, evaluated in
priority order:

1. `INVALID` — any `REQUIRED` category the evidence author explicitly
   marked `NOT_APPLICABLE` for a phase class the profile requires it for
   (a genuine contradiction between profile expectation and evidence
   author's own judgment).
2. `INCOMPLETE` — any `REQUIRED` category missing for any other reason
   (`UNKNOWN`/`UNAVAILABLE`/`OMITTED_INVALID_INPUT`, always disclosed per
   CEE's own 134E.1V-repaired validation).
3. `COMPLETE_WITH_LIMITATIONS` — any `CONDITIONALLY_REQUIRED` category
   missing, or any selected category carrying an attached uncertainty/
   limitation entry.
4. `COMPLETE` — none of the above.

All four outcomes are ordinary, inspectable return values — extraction
never raises for an evidence-completeness shortfall relative to a
profile's requirements (`test_complete_result`, `test_complete_with_
limitations_result`, `test_incomplete_result`, `test_invalid_result`).
A valid, finalized CEE record can still extract as `INCOMPLETE` or
`INVALID` for a specific profile requiring more than the evidence
author disclosed as applicable — extraction-level completeness is
strictly more demanding than, and distinct from, source-record validity.

## 10. Non-Omission

A `REQUIRED` category never disappears silently: every non-`PRESENT`
required category is recorded in `missing_required` with an
`ExtractionDiagnostic`. Findings, repaired defects, unresolved defects,
corrected assumptions, technical debt, notable engineering knowledge,
architectural boundaries, and repository/runtime state are all selected
verbatim when present, never filtered away by profile policy — filtering
is permitted only for genuinely `NOT_APPLICABLE`/`OPTIONAL`-and-absent
categories, and every such omission produces a `FilteringDisclosure`
naming the excluded category, the profile rule responsible, materiality,
and whether the full evidence remains available from the canonical
record.

**Even a profile-declared `NOT_APPLICABLE` category never discards real
content the evidence author actually provided**: if a profile marks a
category `NOT_APPLICABLE` for a phase class but the evidence record
genuinely has `PRESENT` content there, extraction selects it anyway
(marked `OPTIONAL`, with an explicit selection reason noting the
profile/evidence disagreement) rather than silently dropping real
evidence to match the profile's expectation.

## 11. Non-Strengthening

Extraction never transforms canonical certainty or classification.
`SelectedEvidenceItem.value` is always the exact canonical tuple/record
object — extraction never constructs a new `FindingRecord` or alters a
`classification`/`resulting_status` field. Confirmed directly:
`NON_BLOCKING`/`BLOCKING` findings survive extraction with their
classification unchanged (`test_no_strengthening_classifications_
unchanged`); an `UNAVAILABLE` category is never silently treated as
`PRESENT` (`test_no_strengthening_unknown_not_promoted_to_present`); a
repaired finding's `original_finding` (with its original, unrepaired
classification) is preserved alongside `resulting_status`, never reduced
to only the repaired outcome (`test_repaired_finding_history_preserved`).

## 12. Uncertainty and Limitations

First-class, automatically preserved. Every `ExtractionResult` carries
the full `uncertainty`/`limitations` tuples from the source evidence
record unfiltered by profile policy — a profile cannot exclude
uncertainty or limitation records even if it excludes the category they
describe. `SelectedEvidenceItem.uncertainty_refs`/`limitation_refs` link
each selected item back to any uncertainty/limitation entries that
reference it. Orphan references (an uncertainty/limitation entry naming
a category outside the known 21-category set) are rejected with a
`ValueError` — defense-in-depth re-checking what CEE's own construction-
time validation should already have prevented, not a new authority
(`test_orphan_uncertainty_rejected`, `test_orphan_limitation_rejected`).

## 13. Filtering Disclosure

Every category a profile excludes (`NOT_APPLICABLE` with no real
content, or `OPTIONAL` and absent) produces a `FilteringDisclosure`:
`excluded_category`, `profile_rule` (the exact rule text), `material`
(currently always `False` for the two implemented profiles — neither
profile treats any of its own optional/not-applicable exclusions as
materially significant; a future profile may set this differently), and
`still_available_in_canonical_record` (currently `False` for both
profiles, since an excluded-and-absent category has no content to be
"still available" — this field exists for a future case where a profile
excludes a category that genuinely does have canonical content).

## 14. Determinism

Verified across: input ordering (category iteration order is the
profile's own fixed `category_rules` tuple order, never dependent on
dict/set iteration); repeated execution in the same process
(`test_deterministic_ordering`, `test_deterministic_serialization`,
`test_stable_extraction_digest`); independent, equivalent reconstruction
(`test_byte_determinism`); different OS processes
(`test_cross_process_determinism`, two independent subprocess
invocations producing an identical 64-character digest); synthetic agent
provenance (`test_agent_model_independence`, four synthetic callers,
identical completeness outcome); profile registration ordering
(`test_future_profile_extensibility_without_existing_profile_change`).

## 15. Validation and Failure

Fail-closed (`ValueError`, never silently coerced) for: unsupported
profile id (`test_unknown_profile_fails_closed`), unsupported profile
version when explicitly pinned (`test_unsupported_profile_version_
fails_closed`), unsupported phase class for the profile, a non-FINALIZED
or otherwise-invalid source evidence record
(`test_invalid_canonical_evidence_rejected`), and orphan uncertainty/
limitation references. Silent empty success is structurally prohibited:
`extract()` raises if it would otherwise return zero selected items
while classifying the result `COMPLETE`
(`test_empty_successful_extraction_prohibited`) — unreachable in
practice for any genuinely finalized record, since identity/governance_
results/test_results/repository_state/runtime_state are always selected,
but guarded explicitly per the phase's own instruction.

Profile-declared "evidence strengthening" and transport/model-identity
dependence are prevented structurally, not by a runtime check:
`ExtractionProfile`/`CategoryRule` have no field that could reference
caller identity, transport, or rendering format, and `SelectedEvidenceItem.
value` is always the untouched canonical value — there is no code path
through which a profile rule could alter a classification.

## 16. Extensibility

A future profile (changelog, milestone report, release report,
verification report, audit view, analytics) registers via the same
`register_profile()` call with its own `CategoryRule` set — no change to
`CanonicalEngineeringEvidence`, no change to either existing profile, no
channel-specific logic, no new authority, no duplicated extraction
machinery (`extract()` itself is entirely profile-agnostic). Confirmed
directly by registering a synthetic future profile mid-test-suite and
verifying the Phase Report profile's own behavior is byte-identical
before and after.

## 17. Package Boundaries

`src/pcae/core/evidence_extraction.py`. Depends only on
`canonical_engineering_evidence` and the standard library. No dependency
on the Phase Report renderer, Operator Report composer, Telegram,
notification dispatch, delivery adapters, filesystem persistence,
network, Repository Intelligence query/service, or execution systems —
all confirmed by source-level tests, not merely by design intent.

## 18. Compatibility

No existing behavior changed. `phase_reports.py`,
`notification_certification.py`, `notifications.py`,
`notification_config.py`, `repository_transition_validator.py`, and
every CLI command are untouched. PFN-001 and PFR-001 remain unmodified.
`canonical_engineering_evidence.py` is untouched by this phase — 134E.2
only consumes it, read-only.

## 19. Limitations (of this phase's own scope)

- No live evidence capture — extraction operates only on already-
  constructed, already-finalized `CanonicalEngineeringEvidence` records.
- No Derived Evidence View composition — extraction results are not
  rendered or organized into report sections; that is 134E.3/134E.4.
- No rendering, delivery, or receipt integration — reserved for
  134E.5–134E.7.
- Only two profiles implemented (Phase Report, Operator Report); the
  registry supports more, but changelog/milestone/release/verification/
  audit/analytics profiles are explicitly not built in this phase, per
  the phase brief's own scope limit.
- `material`/`still_available_in_canonical_record` on `FilteringDisclosure`
  are always `False` for the two current profiles — no scenario in
  either profile currently produces a materially-significant or
  still-available filtered exclusion; the fields exist for a future
  profile that needs them.

## 20. Explicit Statement

**Evidence Extraction implemented in this phase is not yet active
lifecycle authority.** It is an isolated, disconnected layer consuming
the already-isolated Canonical Engineering Evidence model. The current
governed reporting and finalization path remains the sole operational
authority for phase completion, notification, and identity resolution.
