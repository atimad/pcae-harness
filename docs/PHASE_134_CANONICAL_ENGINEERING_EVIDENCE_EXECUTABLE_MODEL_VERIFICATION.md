# Phase 134E.1V — Canonical Engineering Evidence Executable Model Independent Verification

## 1. Executive Summary

This phase independently verified `src/pcae/core/canonical_engineering_
evidence.py` (134E.1) against Track 133's architecture/contract/
verification/implementation-plan, Track 134's architecture/contract/
verification/implementation-plan, PFR-001, PFN-001, and current PCAE
identity/evidence/deterministic-model conventions — re-deriving
requirements from source rather than trusting 134E.1's report,
documentation, or its own 52 tests.

**Result: two genuine BLOCKING defects found and repaired.** Both were
found by direct adversarial probing before writing any new test —
confirming the phase brief's own premise that names like "canonical,"
"deterministic," and "immutable," and a passing test suite, are not
sufficient evidence on their own. After repair, 37 fresh adversarial
tests plus the original 52 tests (89 total) pass, and all existing
lifecycle regressions remain unchanged.

## 2. Verification Methodology

Read the actual source of `canonical_engineering_evidence.py` fresh, then
constructed direct adversarial probes in a Python REPL *before* writing
any test file — attempting exactly the failure modes the phase brief
enumerates (external mutation of a "finalized" record, applicability
dispositions that could bypass disclosure/mandatory-present checks) — to
independently discover defects rather than confirm the absence of
defects the implementation phase already tested for. Two defects were
confirmed this way. Only after confirming and understanding both defects
were the fixes designed and a permanent regression-test file written.

## 3. Source-Derived Model Architecture (Re-Confirmed)

`CanonicalEngineeringEvidence` groups the eleven Track 133 evidence
categories (133D §7/133E §7) into: identity (`EvidenceIdentity` wrapping
`EvidencePhaseIdentity`), classification (`phase_class`, `task_id`),
narrative fields, six finding tuples, two repair tuples, governance/test
snapshots, three state snapshots, two confirmation tuples, a provenance
tuple, uncertainty/limitation tuples, a correction envelope, an
applicability mapping, and versioning/lifecycle fields (`schema_version`,
`created_at`, `state`, `finalized_at`). This matches 134E.1's own
documentation; independent re-reading of the source found no undisclosed
field or hidden behavior.

## 4. Authority Boundary Result: CONFIRMED

Verified directly, not assumed:

- `grep`-equivalent source scan of `phase_reports.py`, `notifications.py`,
  `notification_certification.py`, `notification_config.py`,
  `repository_transition_validator.py`, and `commands/phase.py` for the
  string `canonical_engineering_evidence`: **zero matches**
  (`test_no_existing_lifecycle_module_imports_the_new_evidence_model`).
- No command constructs, finalizes, or persists a
  `CanonicalEngineeringEvidence` instance.
- No `latest.*` pointer, canonical report, or metadata file references
  this model.
- No parallel active evidence authority exists — the model has no
  persistence layer at all (confirmed: zero `open()`/filesystem calls
  under `builtins.open` patched to raise,
  `test_full_construction_and_finalization_touches_no_filesystem`).

No hidden activation found.

## 5. Package Isolation Result: CONFIRMED

AST-level import inspection (134E.1's own test, re-confirmed) and fresh
behavioral probes: zero internal PCAE imports; construction, validation,
finalization, serialization, and digest computation never touch the
filesystem (verified by patching `builtins.open` to raise and running the
full lifecycle) or the network (no `socket`/`urllib`/`requests` reference
anywhere in the module). No prohibited dependency on notification,
Telegram, delivery adapters, rendering, phase report generation,
Repository Intelligence, or execution systems.

## 6. Identity Result: CONFIRMED, one NON-BLOCKING refinement noted

`EvidenceIdentity.evidence_id = f"{phase_id}#{record_version}"` — no
random UUID, no entropy, no agent/model dependency (confirmed:
`test_no_caller_identity_field_exists_on_the_model`,
`test_synthetic_caller_provenance_does_not_change_identity_or_validation`
across five synthetic callers), no rendering/delivery-state dependency.
`EvidencePhaseIdentity` mirrors `phase_reports.CanonicalPhaseIdentity`'s
shape by convention only — no new phase-identity authority (confirmed by
the same import-isolation check in §5).

**Challenge on sufficiency**: `phase_id#version` correctly distinguishes
corrected/superseded records (version increments) but does **not**
distinguish two different `task_id` values completing the same
`phase_id` independently — `task_id` is a separate field, not part of
identity. Classified **NON-BLOCKING**: this is consistent with the frozen
cardinality rule (133D §3/§5/§13 — exactly one record *per governed
phase*, not per task), and the phase brief itself permits classifying
insufficiency as non-blocking "when correction workflow activates" (which
134E.1 explicitly does not implement). Documented as a refinement input
for whenever the correction workflow is built
(`test_identity_does_not_distinguish_multiple_tasks_under_one_phase_
documented_gap`).

## 7. Phase-Class Result: CONFIRMED after repair

Six `PhaseClass` values confirmed present and independently exercised for
all six (134E.1's own test + this phase's re-run). Review/hardening is
confirmed to be **one executable value representing a documented
folding**, not an ambiguity: the module's own docstring states it maps
onto 133C §6's six existing columns rather than adding a seventh — this
phase independently confirms 133C §6 says exactly that ("review/hardening
phases... map onto the existing six columns without requiring new rows"),
so no ambiguity exists.

**BLOCKING defect found and repaired** (see §9): the phase-class
mandatory-present check for `IMPLEMENTATION`/`VERIFICATION` originally
rejected only the `NOT_APPLICABLE` disposition specifically, allowing
`UNAVAILABLE`, `UNKNOWN`, or `OMITTED_INVALID_INPUT` to silently bypass
the "this category must be present" rule for exactly the two phase
classes the frozen contract (133B §6) names as having a mandatory-present
exception.

## 8. Applicability-State Result: CONFIRMED after repair

Five dispositions are mutually distinguishable, deterministically
serialized (string enum values), and validation-aware.

**BLOCKING defect found and repaired** (see §9): `OMITTED_INVALID_INPUT`
was excluded from the "must be explained by an uncertainty/limitation
entry" check that already covered `UNKNOWN`/`UNAVAILABLE` — meaning a
category could be marked "input was invalid, silently dropped" with zero
disclosure anywhere in the record, and still finalize successfully. This
directly violated Non-Omission (133E §10) and the phase's own explicit
instruction ("do not invent empty success claims").

Probed and confirmed **safe** after repair: `NOT_APPLICABLE` cannot
bypass phase-class obligations (rejected for the two mandatory-present
classes); empty values cannot masquerade as `PRESENT`
(`contradictory_status`, confirmed for every one of the twelve categories
simultaneously in a fresh probe,
`test_empty_present_cannot_masquerade_across_multiple_categories`).

## 9. Repairs

Two BLOCKING defects, both in `src/pcae/core/canonical_engineering_
evidence.py`, repaired at the smallest responsible boundary:

**Repair 1 — shallow immutability.** `@dataclass(frozen=True)` only
blocks attribute *reassignment*; it never copied or froze a mutable
list/dict handed in as a constructor argument. A caller-held reference to
that same list/dict could be mutated *after* `finalize()`, silently
changing the "immutable" record's content and digest. Reproduced directly
(pre-repair): constructing with a plain `list` for `engineering_actions`,
finalizing, then appending to the *original* list object changed
`compute_digest()`'s output. Repaired by adding tuple-conversion for every
tuple-typed field and `MappingProxyType`-with-enum-coercion for
`applicability` in `CanonicalEngineeringEvidence.__post_init__`, plus the
same tuple-conversion in `UncertaintyItem`, `LimitationItem`, and
`CommitPushInfo`'s own `__post_init__` (the three other dataclasses in
the module holding a tuple-typed field a caller could substitute a list
for). Regression tests: `test_deep_immutability_*` (4 tests).

**Repair 2 — applicability-disclosure/mandatory-present bypass.** (a)
Added `OMITTED_INVALID_INPUT` to the disposition set requiring an
uncertainty/limitation disclosure. (b) Changed the phase-class
mandatory-present check from "reject specifically `NOT_APPLICABLE`" to
"reject anything other than `PRESENT`," closing the `UNAVAILABLE`/
`UNKNOWN`/`OMITTED_INVALID_INPUT` bypass for `IMPLEMENTATION`/
`VERIFICATION` phases. Regression tests:
`test_omitted_invalid_input_requires_disclosure_regression`,
`test_implementation_phase_cannot_bypass_mandatory_present_via_any_
disposition` (parametrized over all four non-`PRESENT` dispositions),
`test_verification_phase_cannot_bypass_mandatory_present`.

Both repairs stay within the isolated model — no active-lifecycle
integration was introduced, and the original 52 tests plus fast-green
still pass (§16).

## 10. Findings/Repair Model Result: CONFIRMED

Three classifications remain distinct (enum, rejects invalid string
values). Repairs preserve original findings — verified with two
independent repairs in one record, each retaining its own original
finding's classification untouched
(`test_multiple_repairs_each_preserve_their_own_original_finding`). A
repair of one finding cannot alter an unrelated finding still listed in
`defects_discovered`
(`test_partial_repair_does_not_alter_unrelated_findings`). Construction
already rejects a "repair" of an already-`CONFIRMED` finding (134E.1's own
test, re-confirmed).

## 11. Provenance Result: CONFIRMED, one NON-BLOCKING gap noted

`EvidenceProvenanceRecord` requires `covers`, `source_artifact`,
`derivation_path`, `verification_state` non-empty at construction — no
path lets derived report text stand in as the sole source (the type has
no such field). **NON-BLOCKING**: nothing currently validates that
`covers` names a real category on the record it's attached to — a
typo'd/fabricated category name is silently accepted
(`test_provenance_covers_nonexistent_category_not_currently_validated_
documented_gap`). This is a traceability-quality gap, not an authority
gap: no category's disposition or content is affected by a stray
provenance record, so no invalid evidence can finalize silently because
of it.

## 12. Uncertainty/Limitation Result: CONFIRMED after repair (§9),
otherwise CONFIRMED

First-class dedicated structures (not free text), confirmed to survive
serialization and round-trip
(`test_uncertainty_and_limitations_survive_round_trip`), confirmed to
affect the digest (`test_digest_covers_uncertainty_content`,
`test_digest_covers_limitations_content`), confirmed to preserve
`affected_evidence` references through construction (deep-frozen, §9
Repair 1) and round-trip. The pre-repair `OMITTED_INVALID_INPUT` gap (§8)
was the one path allowing a valid-finalization record to silently discard
material uncertainty — now closed.

## 13. Immutability Result: CONFIRMED after repair (§9)

Frozen dataclasses alone were **not** accepted as sufficient proof, per
the phase's own instruction — and correctly so: the shallow-freeze defect
(§9 Repair 1) was real and reproducible. After repair: every tuple-typed
field across all four affected dataclasses (`CanonicalEngineeringEvidence`,
`UncertaintyItem`, `LimitationItem`, `CommitPushInfo`) is force-converted
to an actual `tuple` at construction time, and `applicability` is
force-converted to a `MappingProxyType`, so no externally-held mutable
reference can alter a constructed (let alone finalized) record. Confirmed
directly: mutating the original list/dict object after construction no
longer changes the record's fields or digest (`test_deep_immutability_*`,
4 tests, all passing post-repair).

## 14. Correction/Supersession Result: CONFIRMED

Confirmed prepared-fields-only (no correction workflow implemented — a
Strict Non-Goal, correctly honored). `CorrectionMetadata`'s own
`__post_init__` already rejected `is_correction=True` without both
`supersedes_evidence_id` and `reason` (134E.1's own test, re-confirmed).
Fresh probe: a record-level mismatch between
`identity.correction_of` and `correction.supersedes_evidence_id` is
caught (`correction_identity_mismatch`, re-confirmed with a fresh
scenario). The simplest self-referential cycle (a record declaring itself
its own correction target) is rejected at the identity level, since
`record_version == 1` cannot declare `correction_of`
(`test_correction_cycle_self_reference_rejected_at_identity_level`). No
automatic report regeneration or lifecycle activation occurs from setting
correction fields — confirmed by the same authority-isolation check (§4).

## 15. Versioning Result: CONFIRMED

`SUPPORTED_SCHEMA_VERSIONS = {"1.0"}`; construction with `"2.0"` or `""`
fails closed at `__post_init__` time, never silently coerced
(`test_unsupported_version_fails_closed_not_coerced`). Version is
distinct from `record_version` (correction revision) — confirmed by
inspection: `schema_version` lives on `CanonicalEngineeringEvidence`
directly, `record_version` lives inside `EvidenceIdentity`, never
conflated in any field or check.

## 16. Secret Exclusion Result: CONFIRMED for tested fields, one
NON-BLOCKING scope gap noted

The existing heuristic (`objective`, `engineering_actions`,
`notable_engineering_knowledge`) correctly rejects a fresh Telegram-
bot-token-shaped injection in a *new* field not covered by 134E.1's own
tests (`notable_engineering_knowledge`,
`test_secret_in_notable_engineering_knowledge_rejected`). **NON-BLOCKING**:
the scan does not cover `governance_results`/`test_results` status
strings, `provenance.source_command`, or repository/runtime state free
text — confirmed by direct probe
(`test_secret_shape_not_scanned_in_governance_or_repository_fields_
documented_gap`, a secret-shaped string embedded in
`source_command` was *not* flagged). No production caller populates these
fields from untrusted/unsanitized input today, so this is classified as
a documented scope gap for a future hardening pass, not a live escape —
matching the phase brief's own guidance ("do not invent a broad
secret-scanning subsystem during verification... classify risk
accurately").

## 17. Agent/Model Independence Result: CONFIRMED

Constructed semantically equivalent evidence under five synthetic caller
identities (DeepSeek, Claude, Codex, an unknown future agent, direct
human CLI) recorded only in `provenance.source_command` — identity,
validation outcome, and finding semantics were identical across all five
(`test_synthetic_caller_provenance_does_not_change_identity_or_
validation`, parametrized). Confirmed no field on
`CanonicalEngineeringEvidence`, `EvidenceIdentity`, or
`EvidenceProvenanceRecord` even contains "agent"/"model"/"caller" in its
name (`test_no_caller_identity_field_exists_on_the_model`). Digest
behavior is intentionally documented: caller-identity text embedded in
`provenance.source_command` legitimately changes the digest *because
provenance content is material evidence*, not because caller identity has
special authority — this is the same "provenance is material" rule
already established for `observed_at` (§ Digest below), applied
consistently.

## 18. Repository Intelligence Independence Result: CONFIRMED

Zero references to `repository_intelligence`/`RepositoryIntelligence`
anywhere in the module (134E.1's own test, re-confirmed with a fresh
substring scan). No cross-reference field exists that could embed or
redefine a Repository Intelligence artifact — the model has no
Repository-Intelligence-shaped field at all.

## 19. Digest Result: CONFIRMED after repair (§9)

Independently reconstructed the algorithm by reading source: SHA-256 over
`json.dumps(d, sort_keys=True, default=str)` where `d` excludes
`record_digest` and the two approved timestamps (`created_at`,
`finalized_at`). Fresh probes confirm: material changes (objective,
uncertainty, limitations, provenance content) change the digest;
non-material changes (which approved timestamp was used) do not; digest
is stable across ten independent, non-timestamp-varying constructions in
the same process and across two separate OS processes (§ below). One
digest-scope nuance independently confirmed and documented, not a defect:
`provenance.observed_at` **does** affect the digest (it is a distinct,
material observation timestamp, not an approved record-lifecycle
timestamp) — confirmed deliberately different from `created_at`/
`finalized_at`'s exclusion
(`test_digest_includes_material_provenance_observed_at`).

**Cross-process stability**: confirmed via two independent subprocess
invocations constructing byte-identical evidence and computing the
digest — both produced the same 64-character hex digest
(`test_cross_process_digest_stability`).

**Semantic omission probe**: reordering two otherwise-identical findings
produces a *different* digest — documented, not repaired, as NON-BLOCKING
(§20), since findings are narrative/ordered artifacts by design, not
mathematical sets, and no frozen contract text requires order-invariance
of raw construction input (only that the *same* construction reproduces
the *same* digest, which holds).

## 20. Non-Blocking Findings Summary

1. Identity does not distinguish multiple tasks under one phase (§6) —
   refinement input for a future correction-workflow phase.
2. Provenance `covers` is not validated against real category names (§11)
   — traceability-quality gap, no authority impact.
3. Secret-shape scan does not cover governance/test-result strings,
   provenance `source_command`, or repository/runtime free text (§16) —
   no current untrusted-input path into those fields.
4. Reordered-but-otherwise-identical findings produce different digests
   (§19) — findings are intentionally order-preserving narrative
   artifacts, not unordered sets; the determinism guarantee that actually
   matters ("same construction twice → same digest") holds and is
   verified.

None of these four permits invalid evidence to finalize silently, none
expands lifecycle authority, and none is required by the frozen contract
to be otherwise — all four are recorded as inputs for later
Track 134 sub-phases (134E.2 onward) or a future hardening pass, not
repaired here, per the phase's own repair rule ("repair only genuine
BLOCKING defects").

## 21. Verdict Table

| Dimension | Verdict |
|---|---|
| Authority boundary | CONFIRMED |
| Package isolation | CONFIRMED |
| Evidence identity | CONFIRMED (1 NON-BLOCKING refinement) |
| Phase identity reuse | CONFIRMED |
| Task identity behavior | CONFIRMED |
| Phase-class coverage | CONFIRMED after repair |
| Applicability-state semantics | CONFIRMED after repair |
| Normalization | CONFIRMED (1 NON-BLOCKING — ordering, §19/20) |
| Ordering | CONFIRMED (insertion-order preserving by design) |
| Serialization | CONFIRMED |
| Round-trip behavior | CONFIRMED |
| Digest correctness | CONFIRMED after repair |
| Digest semantic scope | CONFIRMED |
| Validation completeness | CONFIRMED after repair |
| Fail-closed behavior | CONFIRMED after repair |
| Findings | CONFIRMED |
| Repair history preservation | CONFIRMED |
| Provenance | CONFIRMED (1 NON-BLOCKING gap) |
| Uncertainty | CONFIRMED after repair |
| Limitations | CONFIRMED after repair |
| Non-Omission compatibility | CONFIRMED after repair |
| Immutability | CONFIRMED after repair (was BLOCKING pre-repair) |
| Correction/supersession preparedness | CONFIRMED |
| Versioning | CONFIRMED |
| Secret exclusion | CONFIRMED for tested fields (1 NON-BLOCKING scope gap) |
| Agent/model independence | CONFIRMED |
| Repository Intelligence independence | CONFIRMED |
| Runtime independence | CONFIRMED |
| Delivery/rendering independence | CONFIRMED |
| Existing lifecycle compatibility | CONFIRMED |
| Internal consistency | CONFIRMED |

## 22. Focused Test Results

- Original 134E.1 suite: 52 passed (unmodified except the two model
  repairs; all 52 still pass post-repair).
- New 134E.1V adversarial suite: 37 passed, covering all 20 required
  fresh-probe areas plus regression tests for both repaired defects.
- Combined: 89 passed.

## 23. Regression Results

Re-ran (unmodified): `tests/test_finalization_configuration_identity_
cross_agent_134b3.py`, `tests/test_external_notification_isolation_
134b1.py`, `tests/test_external_delivery_isolation_134b2_verification.py`,
`tests/test_phase_reports.py`, `tests/test_finalization_gate_
enforcement.py`, `tests/test_phase_report_trust_hard_fail.py`,
`tests/test_notification_certification_idempotency.py`,
`tests/test_phase.py` — see final report for the exact combined count;
all passed, confirming phase completion, report generation/promotion,
metadata repair, notification dispatch, delivery authorization, automatic
configuration resolution, task lifecycle, and repository transition
validation are all unchanged by this phase's two model-internal repairs.

## 24. Fast-Green Result

See the governed phase-completion report for the exact count (expected
4389/4390 passed, the same pre-existing, unrelated, environment-state
failure carried since 134B.2, reproduced and documented, not silently
reported as passing).

## 25. Readiness for Evidence Extraction

Track 134's implementation sequence may proceed to **134E.2 — Evidence
Extraction** once this phase completes: the Canonical Engineering
Evidence executable model is now genuinely deeply immutable and
fail-closed against the two BLOCKING defects found, remains isolated from
active lifecycle authority, and the four NON-BLOCKING observations are
recorded as inputs, not blockers, for 134E.2 and later sub-phases. This
phase does not implement Evidence Extraction and does not begin 134E.2.
