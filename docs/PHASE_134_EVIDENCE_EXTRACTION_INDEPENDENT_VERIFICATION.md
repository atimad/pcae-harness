# Phase 134E.2V — Evidence Extraction Independent Verification

## 1. Executive Summary

This phase independently verified `src/pcae/core/evidence_extraction.py`
(134E.2) against Track 133's Engineering Evidence architecture/contracts,
Track 134's lifecycle architecture/contract, 134D's implementation plan,
the Canonical Engineering Evidence executable model, PFR-001, and
current PCAE deterministic-model conventions — re-deriving requirements
from source rather than trusting 134E.2's report, documentation, or its
64 tests.

**Result: two genuine BLOCKING defects found and repaired.** Both were
found by direct adversarial probing in a Python REPL before writing any
test — confirming the phase brief's own premise that explicit profile
tables, a passing test suite, and the absence of Telegram imports are
not sufficient evidence on their own. After repair, 33 fresh adversarial
tests plus the original 64 tests (97 total) pass, and all existing
lifecycle and evidence-model regressions remain unchanged.

## 2. Verification Methodology

Read the actual source of `evidence_extraction.py` fresh, then
constructed direct adversarial probes targeting the phase brief's own
named risk areas — profile registry integrity ("duplicate identifiers
fail closed," "no profile can overwrite an existing profile silently")
and rule-matrix integrity ("missing matrix entries," "duplicate
entries," "conflicting entries," "unreachable rules") — *before* writing
any test file, to independently discover defects rather than confirm
the absence of defects the implementation phase already tested for. Two
defects were confirmed this way, matching two of the phase brief's own
explicitly-named probe targets almost verbatim.

## 3. Source-Derived Architecture (Re-Confirmed)

`extract(evidence, profile_id, *, profile_version=None) -> ExtractionResult`
is the sole entry point. A small explicit dict-based registry
(`register_profile()`/`get_profile()`) holds `ExtractionProfile`
instances, each a fixed-order tuple of `CategoryRule` entries mapping
every one of 21 extraction categories to an explicit `RequirementLevel`
per `PhaseClass`. `SelectedEvidenceItem` preserves full traceability
(source identity, applicability, requirement level, provenance,
uncertainty/limitation references, selection reason) for every selected
canonical value. Independent re-reading of the source found no
undisclosed field, no hidden category, and no undocumented behavior
beyond the two defects below.

## 4. Authority Boundary Result: CONFIRMED

Verified directly:

- Fresh full-tree scan (`test_no_active_lifecycle_imports_fresh_scan`,
  scanning every non-test `.py` file under `src/pcae`, not just the six
  files 134E.2's own test checked) for the string `evidence_extraction`:
  **zero matches** outside the module itself.
- No command constructs, extracts from, or persists an
  `ExtractionResult`.
- No `latest.*` pointer, canonical report, or metadata file references
  this module.
- Extraction cannot mutate `CanonicalEngineeringEvidence` — confirmed by
  digest stability across three separate extraction calls on the same
  record (`test_extraction_never_mutates_source_evidence_digest`).
- `ExtractionResult` has no field claiming canonical/engineering
  authority; it carries `source_evidence_id`/`source_record_digest` as
  references back to the one authority, never a competing one.

No hidden activation found.

## 5. Package Isolation Result: CONFIRMED

Fresh behavioral probe (not just source inspection): patched
`builtins.open` to raise, then ran a full construct → extract →
serialize → digest cycle for both profiles — zero filesystem access
(`test_no_filesystem_network_rendering_or_delivery_side_effects`). No
`socket`/`urllib`/`requests`/`subprocess` reference anywhere in the
module. No rendering symbol (`render_markdown`, `to_markdown`,
`to_html`) or transport/adapter symbol (`TelegramSink(`, `dispatch(`,
`NotificationSink`) is used or imported — confirmed by source-text scan
distinguishing legitimate docstring prose (which *names* rendering and
delivery as the next architectural stages) from actual code dependency.

## 6. Profile Registry Result: BLOCKING defect found and repaired (§13)

Challenged every item in the brief's own registry checklist:

- Profile identifiers stable: confirmed (`profile_id` is an immutable
  string field).
- Versions explicit: confirmed (`profile_version` required non-empty).
- **Duplicate identifiers fail closed: NOT confirmed pre-repair —
  BLOCKING.** `register_profile()` unconditionally overwrote any
  existing entry. Reproduced directly: registered a `profile_id=
  "phase_report_v1"` profile with every category marked
  `NOT_APPLICABLE` and version `"999.0"`; `get_profile("phase_report_v1")`
  immediately returned the fake profile — the real one was gone with no
  error, no warning, no trace.
- Profile lookup deterministic: confirmed (dict keyed by exact string,
  no fuzzy matching).
- Registration order does not affect an *existing* profile's own
  behavior: confirmed (`test_registry_order_independence`), separate
  from the overwrite defect above (which is about *replacing* a profile
  under the *same* id, not about order between *different* ids).
- Unsupported profile/version fail closed: confirmed (134E.2's own
  tests, re-confirmed).
- Future profile registration does not modify existing profile behavior:
  confirmed (`test_future_profile_isolation_from_existing_profiles`,
  identity comparison via `is`, not just value equality).
- No profile can overwrite an existing profile silently: **fixed** in
  this phase (§13).

Runtime mutation of the registry: the only *supported* mutation surface
is `register_profile()`, which — after this phase's fix — routes every
registration through both `ExtractionProfile`'s own construction-time
validation and the new duplicate-id check. A caller holding a direct
reference to the private `_PROFILE_REGISTRY` module attribute could
still bypass this (Python has no true private state); classified
**NON-BLOCKING**, documented, matching ordinary "private by convention"
practice elsewhere in this codebase — no production code path does this.

## 7. Rule-Matrix Result: BLOCKING defect found and repaired (§13)

Independently enumerated all 21 categories × 6 phase classes × 2
profiles = 252 cells per profile. **Missing matrix entries**: correctly
rejected at construction (134E.2's own check, re-confirmed —
`test_missing_profile_matrix_entry_rejected`). **Duplicate/conflicting
entries: NOT caught pre-repair — BLOCKING.** Reproduced directly: built
a 22-rule set for the 21 known categories (one category, `objective`,
ruled twice — once `REQUIRED`, once `NOT_APPLICABLE`) and successfully
constructed an `ExtractionProfile`; `requirement_for("objective", ...)`
silently returned only the first-registered rule (`REQUIRED`), with the
conflicting second rule permanently unreachable dead code and zero
construction-time error. **Unreachable rules**: this *is* the unreachable-
rule failure mode — closed by the same fix. **Category spelling
mismatches**: `CategoryRule.__post_init__` already rejects any category
not in `EXTRACTION_CATEGORIES` (134E.2's own check, unaffected by this
repair). **Phase-class alias mismatches**: not applicable — `PhaseClass`
is a closed enum; `CategoryRule.requirement_by_phase_class` is keyed by
the enum itself, not strings, so no alias/spelling drift is possible by
construction. **Rule behavior differing from its declared requirement
level**: none found — `extract()`'s branch logic for
REQUIRED/CONDITIONALLY_REQUIRED/OPTIONAL/NOT_APPLICABLE was independently
re-traced line by line and matches the documented semantics exactly (§9).

No implicit default converts an unspecified category into optional or
excluded — confirmed structurally: every category must have an explicit
rule for every phase class, or construction fails.

## 8. Phase Report Profile Result: CONFIRMED

Re-derived all thirteen PFR-001 obligations independently (not from
134E.2's own mapping) and confirmed each is covered by at least one
extraction category, selected, disclosed as filtered, or recorded as
missing (`test_all_pfr_categories_represented_in_phase_report_
extraction`, 134E.2's own test, re-verified still passing post-repair).
Probed whether a structurally valid but informationally empty extraction
could claim completeness: confirmed **no** — `COMPLETE` requires every
`REQUIRED` category to carry real, non-empty content (CEE's own
`contradictory_status` check already prevents `PRESENT` + empty at
construction; `test_required_but_empty_evidence_cannot_be_constructed_
as_present` confirms this defense exists one layer below extraction
too, not only within it).

## 9. Operator Report Profile Result: CONFIRMED

Fresh probes beyond 134E.2's own status-only test: a **near-status-only**
record (adds `engineering_actions` and `notable_engineering_knowledge`
— one step past bare status/tests/next-phase — but still omits
defects/repairs/corrected-assumptions/debt-review entirely) still never
reaches `COMPLETE`
(`test_near_status_only_operator_report_rejected` — reaches `INVALID`,
an even stronger rejection, since `architectural_findings` is `REQUIRED`
for an `ARCHITECTURE`-class phase under this profile and was marked
`NOT_APPLICABLE`). All 18 decision-completeness categories the brief
names (objective, decisions, implementation/design/planning/
verification evidence, defects, repairs, corrected assumptions,
unresolved findings, technical debt, architectural significance,
what-changed/what-didn't, preserved boundaries, tests, governance,
repository state, runtime state, next phase, notable knowledge) trace to
an extraction category the Operator Report profile marks `REQUIRED` or
`CONDITIONALLY_REQUIRED` for the relevant phase classes — the one
deliberate, documented exception is "finalization or delivery result,"
which does not exist as a category anywhere in this system because
Track 133F confirmed it is owned by PFN-001, not Canonical Engineering
Evidence (134E.2's own documented, correct exclusion, re-confirmed by
this phase, not repaired).

## 10. Phase-Class Result: CONFIRMED

Independently probed all six phase classes against both profiles.
Confirmed: an architecture phase's `implementation_findings` is
`NOT_APPLICABLE` (never silently `PRESENT`-but-empty); a verification
phase's `verification_findings` is `REQUIRED` (methodology/findings
mandatory); an implementation phase's `implementation_findings` is
`REQUIRED` (substantive evidence mandatory); review/hardening phases'
`implementation_findings`/`verification_findings` are
`CONDITIONALLY_REQUIRED` (may legitimately include either). No planning-
specific decomposition/risk/acceptance-criteria category exists in the
underlying 134E.1 evidence model itself (only `objective`,
`engineering_actions`, and the finding/debt categories are available) —
this is a 134E.1 evidence-model scope boundary, not a 134E.2 extraction
defect; extraction correctly cannot select evidence the source model
does not carry. Documented as a **NON-BLOCKING** observation for a
future evidence-model or profile refinement, not repaired here (out of
this phase's scope).

## 11. Requirement-Level Result: CONFIRMED (§7's repair closes the one
real gap)

Fresh probes: required-marked-not-applicable now correctly produces
`INVALID`, not a silent bypass (§7, §13). Conditionally-required
evidence is confirmed to be a static, deterministic per-(profile,
phase_class) tier rather than a dynamically-evaluated cross-field
condition — documented as an intentional, deterministic design choice
(`test_conditionally_required_is_a_static_per_phase_class_tier_
documented`), not a defect: a condition depending on other field
content would make extraction depend on the very data it describes,
adding complexity the phase brief's "no implicit default" instruction
does not actually require. Optional-and-material evidence is never
silently excluded — every exclusion (`NOT_APPLICABLE`-and-absent or
`OPTIONAL`-and-absent) produces a `FilteringDisclosure`
(`test_material_optional_evidence_filtering_always_disclosed`).
Unknown/unavailable required evidence both correctly produce
`INCOMPLETE`, never silently treated as optional/not-applicable
(`test_unknown_versus_unavailable_both_produce_incomplete_for_
required`).

## 12. Selected-Evidence Traceability Result: CONFIRMED

Every `SelectedEvidenceItem` carries `source_evidence_id` (matching the
canonical record's own `evidence_id`), the raw `value` (never copied-
and-altered), `applicability`, `requirement_level`, category-filtered
`provenance`, `verification_state`, `uncertainty_refs`/`limitation_refs`,
and `selection_reason`. Probed whether copied values could detach from
source identity/digest: confirmed **no** — `ExtractionResult.source_
record_digest` is computed directly from the source evidence object at
extraction time and independently re-verified equal to
`evidence.compute_digest()` in every test that checks it.

## 13. Repairs

Two BLOCKING defects, both in `src/pcae/core/evidence_extraction.py`,
repaired at the smallest responsible boundary:

**Repair 1 — silent profile overwrite.** `register_profile()` now
compares any existing entry for the same `profile_id` against the
incoming profile (dataclass equality, covering every field including
nested `category_rules`); an identical re-registration is a harmless
no-op, anything else raises `ValueError` naming both versions and
refusing the overwrite. Regression tests:
`test_duplicate_profile_registration_rejected`, plus confirmation that
idempotent re-registration of the exact same profile still works.

**Repair 2 — undetected duplicate/conflicting category rules.**
`ExtractionProfile.__post_init__` now checks for duplicate category
names in `category_rules` *before* checking coverage, raising
`ValueError` naming the duplicated categories. Regression test:
`test_missing_profile_matrix_entry_rejected` (existing, re-confirmed)
plus a fresh duplicate-rule probe in this phase's own suite.

Both repairs stay within the isolated module — no active-lifecycle
integration was introduced, and the original 64 tests plus fast-green
still pass (§20).

## 14. Findings/Repairs Preservation Result: CONFIRMED

Fresh probes beyond 134E.2's own coverage: a repaired `BLOCKING` finding
retains its original classification and description verbatim alongside
`resulting_status`
(`test_repaired_blocking_finding_history_preserved`); an unresolved,
separate `BLOCKING` finding in `defects_discovered` is never inferred as
resolved merely because an unrelated repair exists elsewhere
(`test_partial_repair_remains_unresolved_in_defects_discovered`); a
corrected assumption preserves both the original incorrect assumption's
description and the correction action
(`test_corrected_assumption_history_preserved`).

## 15. Technical Debt / Corrected Assumptions Result: CONFIRMED

`technical_debt_reviewed` and `technical_debt_introduced` are confirmed
never conflated — independently populated with distinguishable content
and both correctly selected as separate categories
(`test_technical_debt_reviewed_vs_introduced_not_confused`). Corrected-
assumption history (§14) confirms model/agent-misattribution-style
corrections (e.g. 134B.3's own DeepSeek-attribution correction) would
remain fully visible through this same mechanism, since `RepairRecord`'s
shape is identical regardless of what kind of finding it repairs.

## 16. Notable Engineering Knowledge Result: CONFIRMED

Confirmed the category is selected verbatim (134E.2's own test) and that
its provenance survives extraction fully attached
(`test_notable_knowledge_provenance_preserved`) — both the knowledge
text and its traceable source are available to a future View Composition
consumer, not just the bare text.

## 17. Uncertainty / Limitation Result: CONFIRMED

Fresh probes: an uncertainty entry describing an `OPTIONAL`-and-filtered
category still appears in the result's top-level `uncertainty` tuple
(`test_uncertainty_survives_even_when_its_category_is_optional_and_
filtered`) — filtering a category never filters the uncertainty/
limitation records describing it. Same confirmed for limitations on a
`CONDITIONALLY_REQUIRED`-and-absent category
(`test_limitation_survives_even_when_its_category_is_conditionally_
required_and_absent`). A required category disclosed via uncertainty is
confirmed to still count as missing for completeness purposes — the
disclosure documents the gap, it does not close it
(`test_filtering_disclosure_does_not_satisfy_required_evidence`).

## 18. Completeness Classification Result: CONFIRMED

Fresh, deliberately paired probe: two evidence records differing only in
whether a required category is `NOT_APPLICABLE` (a genuine
contradiction) versus `UNKNOWN`-with-disclosure (a disclosed gap)
produce **different** completeness outcomes — `INVALID` versus
`INCOMPLETE` respectively (`test_invalid_distinct_from_incomplete`) —
confirming these are not merely two labels for the same underlying
condition. `COMPLETE_WITH_LIMITATIONS` confirmed to still carry every
limitation record, not just a flag
(`test_complete_with_limitations_preserves_all_limitations`).

## 19. Non-Omission / Non-Strengthening Result: CONFIRMED

Non-Omission: every material category probed (findings, repairs,
unresolved defects, corrected assumptions, technical debt, notable
knowledge, uncertainty, limitations, no-go/architectural boundaries,
repository/runtime state) is confirmed non-omissible under the profiles'
own rules, or explicitly disclosed when genuinely absent — no silent-
omission path found beyond the two repaired defects, neither of which
was itself a silent-omission bug (they were registry/matrix-integrity
bugs, not evidence-loss bugs). Non-Strengthening: confirmed structurally
— `SelectedEvidenceItem.value` is always the exact canonical object, and
no code path in `extract()` constructs a new `FindingRecord` or alters a
`classification`/`resulting_status` field; a `BLOCKING` finding's
classification survives unchanged through extraction in every test that
checks it (134E.2's own tests, re-confirmed, plus this phase's repaired-
finding probes).

## 20. Determinism Result: CONFIRMED

Verified across: differently-shaped input (findings/debt/uncertainty/
limitations/provenance all populated together, not just individually,
`test_cross_process_byte_determinism_with_findings_and_uncertainty`);
two independent OS processes producing an identical 64-character digest;
profile registration ordering (§6); synthetic caller provenance (§21).
No mutable global state affects output — the only module-level mutable
state is `_PROFILE_REGISTRY` itself, and this phase's own repair (§13)
makes it fail-closed against the one mutation that could have affected
determinism (silent overwrite of an existing profile mid-process).

## 21. Serialization/Digest Result: CONFIRMED

Independently reconstructed: `ExtractionResult.compute_digest()` follows
the identical SHA-256-over-sorted-JSON convention 134E.1 established,
with `extraction_digest` excluded from its own input. No approved-
timestamp field exists on `ExtractionResult` to require special
exclusion — extraction inherits determinism entirely from its source
evidence's own already-timestamp-excluded digest, confirmed by direct
inspection (no `created_at`/`finalized_at`-shaped field on the result).
Material evidence changes alter the digest (134E.2's own tests,
re-confirmed); presentation/delivery state cannot alter it because no
such field exists on the result at all.

## 22. Validation/Failure Result: CONFIRMED (post-repair)

Every failure mode the brief names was probed: invalid canonical
evidence, missing profile, missing version match, missing phase-class
support, missing/conflicting matrix rules (§7, repaired), orphan
uncertainty/limitation references (134E.2's own tests, re-confirmed),
orphan repair references (confirmed structurally impossible — §23),
duplicate selected categories (confirmed structurally impossible — the
category loop iterates a fixed, duplicate-free tuple and selects at most
one item per category per branch), prohibited material omission,
profile-dependent strengthening (structurally impossible — no such code
path exists), transport-/model-dependent behavior (structurally
impossible — no such field exists), empty successful extraction
(explicitly guarded). All failures raise `ValueError` with an
inspectable message; none is silently swallowed.

## 23. Duplicate / Orphan Handling Result: CONFIRMED

"Orphan repair reference" is confirmed **structurally impossible** by
design, not merely untested: `RepairRecord` embeds its full
`original_finding` object rather than referencing a finding by ID —
there is no foreign-key-shaped field that could point to something
nonexistent. A repair whose original finding does not also appear in
`defects_discovered` (a defect found and fixed within the same phase,
never separately listed as "discovered") is fully valid and fully
traceable on its own
(`test_orphan_repair_reference_structurally_impossible`).

## 24. Future-Profile Extensibility Result: CONFIRMED (post-repair)

A synthetic profile registered mid-test-suite leaves both existing
profiles byte-identical (identity comparison via `is`, stronger than
134E.2's own value-equality check) — confirmed the shared `CategoryRule`/
`MappingProxyType` structures cannot be mutated through any reference a
future profile might hold
(`test_shared_rule_structure_cannot_be_mutated_through_category_rule`,
raises `TypeError` on a direct mutation attempt).

## 25. Agent/Model and Transport Independence Result: CONFIRMED

Fresh probes: `extract()`'s own signature contains no transport/channel-
shaped parameter; embedding transport-sounding text
(`"future-transport-xyz-adapter"`) or an unknown-future-agent identifier
in `provenance.source_command` changes neither completeness nor which
categories are selected
(`test_synthetic_future_transport_context_cannot_alter_extraction`,
`test_unknown_future_agent_provenance_independence`). No field on
`ExtractionProfile`/`CategoryRule`/`ExtractionResult` references caller,
model, or transport identity.

## 26. Current Lifecycle Compatibility Result: CONFIRMED

Re-ran (unmodified): the full Canonical Engineering Evidence suite
(134E.1, 134E.1V), phase-report/finalization/identity/notification
regressions, 134B.1–134B.3 regressions, and the phase-identity-parsing
repair suite (134E.1V's own finalization repair). See §27 for the exact
combined count. All passed, confirming no existing behavior changed.

## 27. Focused Test Results

- Original 134E.2 suite: 64 passed (unmodified except the two model
  repairs; all 64 still pass post-repair).
- New 134E.2V adversarial suite: 33 passed, covering all 30 required
  fresh-probe areas plus regression tests for both repaired defects.
- Combined: 97 passed.

## 28. Regression Results

See the governed phase-completion report for the exact combined
regression count across the Canonical Engineering Evidence suite,
phase-report/finalization/identity/notification suites, and 134B.1–
134B.3 — all passed.

## 29. Fast-Green Result

See the governed phase-completion report for the exact count (expected
4389/4390 passed, the same pre-existing, unrelated, environment-state
failure carried since 134B.2, reproduced and documented, not silently
reported as passing).

## 30. Verdict Table

| Dimension | Verdict |
|---|---|
| Authority boundary | CONFIRMED |
| Package isolation | CONFIRMED |
| Profile registry design | CONFIRMED after repair (was BLOCKING) |
| Profile identity/versioning | CONFIRMED |
| Phase Report profile completeness | CONFIRMED |
| Operator Report profile decision completeness | CONFIRMED |
| Phase-class coverage | CONFIRMED (1 NON-BLOCKING — planning-phase category scope) |
| Rule-matrix completeness | CONFIRMED after repair (was BLOCKING) |
| Requirement-level semantics | CONFIRMED |
| Selected-evidence traceability | CONFIRMED |
| Findings preservation | CONFIRMED |
| Repair-history preservation | CONFIRMED |
| Technical-debt preservation | CONFIRMED |
| Corrected-assumption preservation | CONFIRMED |
| Notable-knowledge preservation | CONFIRMED |
| Uncertainty preservation | CONFIRMED |
| Limitation preservation | CONFIRMED |
| Provenance preservation | CONFIRMED |
| Filtering disclosure | CONFIRMED |
| Completeness classification | CONFIRMED |
| Non-Omission | CONFIRMED |
| Non-Strengthening | CONFIRMED |
| Determinism | CONFIRMED |
| Serialization | CONFIRMED |
| Digest behavior | CONFIRMED |
| Validation/failure behavior | CONFIRMED |
| Silent-empty-result prevention | CONFIRMED |
| Duplicate handling | CONFIRMED |
| Profile extensibility | CONFIRMED after repair |
| Agent/model independence | CONFIRMED |
| Transport independence | CONFIRMED |
| Rendering independence | CONFIRMED |
| Repository Intelligence independence | CONFIRMED |
| Current lifecycle compatibility | CONFIRMED |
| Internal consistency | CONFIRMED |

## 31. Remaining Observations (NON-BLOCKING)

1. No planning-phase-specific decomposition/risk/acceptance-criteria
   category exists because the underlying 134E.1 evidence model does not
   carry one (§10) — an evidence-model scope question, not an extraction
   defect.
2. "Conditionally required" is a static per-(profile, phase_class) tier,
   not a dynamically-evaluated cross-field condition (§11) — an
   intentional, documented design choice.
3. Direct manipulation of the private `_PROFILE_REGISTRY` module
   attribute bypasses `register_profile()`'s checks (§6) — matches
   ordinary "private by convention" Python practice; no production code
   path does this.

None of these three permits invalid evidence to extract silently, none
expands lifecycle authority, and none is required by the frozen contract
to be otherwise.

## 32. Readiness for Phase Report View Composition

Track 134's implementation sequence may proceed to **134E.3 — Phase
Report View Composition** once this phase completes: Evidence Extraction
is now genuinely fail-closed against both BLOCKING defects found, its
profile registry cannot silently corrupt itself, its rule matrices
cannot silently contain dead/conflicting rules, it remains isolated from
active lifecycle authority, and the three NON-BLOCKING observations are
recorded as inputs, not blockers, for 134E.3 and later sub-phases. This
phase does not implement Phase Report View composition and does not
begin 134E.3.
