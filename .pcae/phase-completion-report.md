# Phase 136AB Complete — Stage 3 Typed Authority Model Authority Core Implementation

## Phase identity

- Phase ID: `136AB`
- Status: completed
- Classification: implementation (Typed Model Implementation Group 2 — `AuthorityEpoch`, `AuthorityState` only; no other record-family model)
- Report completeness: complete

## Scope

Implement exactly the two Typed Model Implementation Group 2 record
models (`AuthorityEpoch`, `AuthorityState`) from the frozen 136Y
implementation plan, backed by
`src/pcae/schema_resources/cltr_cutover/records/authority_epoch.schema.json`
and `.../authority_state.schema.json`. Descriptive, immutable,
schema-backed representations only. No authority resolution, no epoch
activation/selection, no CAS evaluation, no persistence, no runtime
integration, no other record-family model.

## Summary

Implemented `src/pcae/cltr/authority/authority_core.py`: two frozen,
recursively immutable dataclasses (`AuthorityEpoch`, `AuthorityState`)
plus two record-local enums (`ActivationState`, `VerificationState`) and
one small local value object (`Uncertainty`). Every field independently
re-derived from the two executable schema files (Section 4 of the
companion documentation, not copied from 136Y plan prose). Strict
`from_dict(payload, *, schema_version)`/`to_dict()` construction and
serialization; strict `schema_id`/`record_type` constant enforcement;
`ABSENT`-vs-`null` distinction preserved per field
(`generation_binding`/`authoritative_generation`/`uncertainty` use
`ABSENT`; `predecessor_epoch` is the one field always present as a key
but nullable); fail-closed enum handling throughout; family-restricted
`RecordReference` usage for `predecessor_epoch`, `active_authority_epoch`,
and `publication_evidence_reference` (never resolved or dereferenced,
`require_family` enforced). Every schema-level conditional
(`activation_state`↔`generation_binding`,
`authority_kind`↔`authoritative_generation`,
`verification_state`↔`uncertainty`) is restated exactly once as a
`__post_init__` invariant, never a new semantic rule. Neither schema
embeds `CasExpectation` or declares `_extensions`; neither is used by
either model. Explicitly closes finding 136AA-1 (every composite
enum/wrapper-typed field constructed via its own type before being handed
to a shared-core composite constructor, never a raw payload value passed
through directly).

69 new focused tests
(`tests/test_cltr_authority_136ab_authority_core.py`), all passing,
covering: inventory (exactly two record-family models, no later-group
class anywhere in the package); minimal/maximal valid construction across
every conditional branch for both models; exact field mapping; unknown-
field/unknown-enum-value/unsupported-schema-version/wrong-constant
rejection; the full three conditional matrices (legal and illegal
combinations); wrong-family reference rejection for all three restricted
reference fields; immutability (frozen assignment, tuple-backed
`limitations`, deep-copied `to_dict()` output); structural equality
(including record-ID-equality-does-not-imply-record-equality); malformed
digest/identifier rejection; no-coercion; automated schema-to-model
conformance/drift-detection (field-set, required-set, and enum-member-set
comparison against the live schema JSON); no-authority-symbol source
scan; no-`CasExpectation`/`ExtensionMapping`/`OpaqueJsonValue`-usage
proof; runtime isolation; instrumented no-network/no-subprocess/
no-filesystem-write/no-environment-lookup/no-digest-computation proofs;
and wheel/sdist/installed-wheel-outside-checkout packaging proofs.

Three pre-existing scope guards (136Z's, 136AA's, and 136M's own
anticipatory "no typed-authority-model module/class yet" tests) were
narrowed to authorize exactly `AuthorityEpoch`/`AuthorityState`/
`authority_core.py`, leaving every other later-group record-model name
and module forbidden, unchanged — mirroring 136Z's own precedent against
a stale 136U guard, and the precedent 136M's own test comment already
anticipated verbatim.

Fresh regression evidence: the new 69-test module plus both prior
shared-core suites (`test_cltr_authority_136z_shared_core.py`,
`test_cltr_authority_136aa_shared_core_independent.py`) — 514 passed
together. `cltr_cutover`/`schema_runtime` filtered sweep: 4061 passed, 9
failed (identical to 136AA's own disclosed 9 — 1 pre-existing 136U
scope-guard regression against `RecordFamily.RECEIPT_AUTHORITY_BINDING`,
8 pre-existing unrelated `test_cltr_135o_integration.py`/
`test_cltr_migration_135p_verification.py` completion-status-mismatch
failures — zero new failures). Fast Green: 4391 passed (unchanged
baseline). Full unmarked suite re-attempted fresh under a 240-second
bound; did not complete — consistent with the ongoing, previously
disclosed stall (`NON-BLOCKING-136W-3`), disclosed as non-blocking and
not claimed as passed.

No production schema was changed. No new production dependency was
introduced. No record-family model beyond Group 2 was implemented; no
semantic validator, repository, persistence, or authority resolver
exists. No production runtime module imports `pcae.cltr.authority`.
Legacy lifecycle remains the sole production authority; CLTR remains
derivative; runtime remains Observed / observe / execution unavailable.

Verdict: **AUTHORITY CORE MODEL IMPLEMENTATION COMPLETE WITH
NON-BLOCKING FINDINGS — READY FOR INDEPENDENT VERIFICATION**.

## Findings

- 136AB-1 (CONFIRMED, repaired this phase — anticipated maintenance, not
  a defect): three pre-existing scope guards required the identical
  Group-2 narrowing already anticipated by 136M's and 136AA's own prior
  disclosures; narrowed exactly as anticipated, no other name touched.
- 136AA-3 (inherited, CONFIRMED, still not this phase's scope to repair):
  pre-existing 136U scope guard still incorrectly flags
  `RecordFamily.RECEIPT_AUTHORITY_BINDING`.
- 136AA-4 (inherited, CONFIRMED, unrelated): the 8 pre-existing
  `test_cltr_135o_integration.py`/`test_cltr_migration_135p_verification.py`
  failures, unrelated to `cltr.authority`.

No Blocking finding was identified.

## Recommended next phase

**136AC — Stage 3 Typed Authority Model Authority Core Independent
Verification.** This phase does not begin 136AC.

## No-Go confirmation

No `CutoverRequest`, `ReadinessPackage`, `HumanAuthorization`,
`CutoverCandidate`, `Certification`, `PublicationAttempt`,
`PublicationEvidence`, `ConcurrencyConflict`, `RecoveryJournalEntry`,
`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
`FinalizationReceiptAuthorityBinding`, `CompatibilityState`, or
`QuarantineRecord` was implemented; no semantic validator, cross-record
repository, persistence, authority resolver, compatibility resolver,
quarantine coordinator, publication coordinator, recovery coordinator,
lifecycle integration, execution capability, authority activation, or
legacy demotion/retirement logic was implemented. Runtime remains
Observed / observe / unavailable; legacy lifecycle remains sole
production authority; CLTR remains derivative.

Full detail:
`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_AUTHORITY_CORE_IMPLEMENTATION.md`.
