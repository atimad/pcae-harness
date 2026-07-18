# Phase 136AH Complete — Stage 3 Typed Authority Model Publication Implementation

## Phase identity

- Phase ID: `136AH`
- Status: completed
- Classification: implementation (Typed Model Implementation Group 5 — `PublicationAttempt`, `PublicationEvidence` only)
- Report completeness: complete

## Scope

Implement exactly two record-family models, `PublicationAttempt` and
`PublicationEvidence`, per the frozen 136Y plan (Typed Model
Implementation Group 5), schema-backed by
`records/publication_attempt.schema.json` and
`records/publication_evidence.schema.json`. No publication execution, no
CAS execution, no evidence verification, no reference resolution, no
persistence, no notification dispatch, no marker/receipt creation, no
later record-family model.

## Summary

New module `src/pcae/cltr/authority/publication.py` implements
`PublicationAttempt` (Tier 1 strict, 14 required fields, 3
conditionally/freely-optional fields) and `PublicationEvidence` (Tier 1
strict, 8 required fields, 3 conditionally-present fields), both frozen,
recursively-immutable dataclasses with independently re-derived field
tables from the live executable schemas.

`PublicationAttempt` enforces its `uncertainty`/`state ==
"publication_uncertain"` and `failure_classification`/`state in
{"gate_rejected", "conflict"}` conditional pairs; reuses the already-shared
12-value `PublicationState` enum and the shared `CasExpectation`
component (its third and final embedding site per the schema's own
disclosure) unchanged; enforces the cross-family
`schema_id`/`schema_version` requirement on `request_reference`/
`candidate_reference`/`certification_reference` while
`source_authority_reference`/`target_authority_reference` correctly omit
it (matching the `epoch_reference` precedent, and may reference the
identical epoch record); `attempt_sequence` is validated as a
non-negative integer with booleans explicitly excluded;
`authority_role == "authoritative"` is unconditionally rejected.

`PublicationEvidence` introduces the new record-local 8-value
`PublicationOutcome` enum (distinct from the 12-value shared
`PublicationState`); enforces its `uncertainty_detail` and
`target_readback` + `authoritative_generation` conditional pairs;
`target_readback` carries no family restriction (matching the
`ReadinessPackage.evidence_references` precedent); is one of exactly two
families where `authority_role == "authoritative"` is structurally
permitted (only alongside a present `authoritative_generation`, i.e.
only in the terminal `published_and_verified` outcome), while
`is_authoritative` nonetheless remains the frozen const `false`
unconditionally, mirroring `AuthorityState`'s own disclosed limitation
(NON-BLOCKING-136J-1).

No `_extensions` escape hatch exists on either family (both Tier 1
strict). No shared-core module (`cas_expectation.py`, `enums.py`,
`references.py`, `digest.py`, `identity.py`, `limitations.py`,
`envelope.py`, `serialization.py`) was modified — the existing
`PublicationState` shared enum, `CasExpectation`, and
`GenerationReference` types required no code change to be reused.

New standalone test module
`tests/test_cltr_authority_136ah_publication.py` (87 tests: 85 fast + 2
`@pytest.mark.slow` packaging tests, all passing), independently
fixtured — no fixture, helper, or expected-value table imported from any
prior phase's own test module. Covers minimal/maximal valid construction
with schema validation for both models; every conditional-field branch
in both directions; family-restriction enforcement including the
cross-family `schema_id`/`schema_version` requirement and the
no-restriction cases; enum member-set parity against the live schemas;
`authority_role == "authoritative"` rejection/permission behavior on
both models; the embedded `cas_expectation` component's
unconditional-field-requiredness; schema `properties`/`required`-set
parity against both live schema files; frozen-dataclass immutability,
hashability, and structural equality (including cross-type inequality);
no-forbidden-symbol source scan (publication/CAS/evidence-verification
symbol names); AST-based production-import scan; no-network/no-subprocess/
no-filesystem-write side-effect checks during construction,
serialization, equality, and `repr()`; a fresh isolated-venv wheel/sdist
installation exercise independent of the earlier phases' own narrowed
guards.

No authentication, publication execution, CAS execution, evidence
verification, or reference resolution was found anywhere in
`publication.py` (AST-scanned for a closed forbidden-symbol list,
screened as actual code constructs rather than disclosure prose;
`socket.socket`, `subprocess.run`/`Popen`, and filesystem-write
monkeypatched to raise during construction/serialization/equality/repr,
none fired). AST import-graph scans confirm zero production-runtime
imports into `pcae.cltr.authority` in either direction, and the
authority package imports no production lifecycle or runtime module.
Fresh wheel/sdist build with isolated installed-wheel construction
(including a fictitious forward reference, constructed with no lookup)
outside the repository checkout succeeded with no undeclared dependency.

Regression: 1394 passed / 2 skipped (fast) and 5 passed (slow/packaging,
across `136ab`/`136ad`/`136ag`/`136ah`) across all nine
`test_cltr_authority_136*` modules together; CLTR canonicalization +
`schema_runtime`/strict-JSON/manifest/registry suites 1232 passed; Fast
Green (`fast_green` marker) 4391 passed, unchanged baseline; a broader
supplementary quick-tier full-repository sweep found 24 pre-existing
failures, all independently confirmed unrelated (none in a file this
phase's diff touches — two of the 24, `test_136m_no_typed_authority_model_module_exists`
and `test_136u_no_runtime_code_references_group10_families_outside_schema_resources`,
were directly inspected and confirmed to trip on Phase 136AB/136AF's own
pre-existing classes/enum values, not on anything from this phase). Full
detail in
`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_PUBLICATION_IMPLEMENTATION.md`.

**CONFIRMED-136AE-2 preserved unrepaired, as instructed.** The
already-disclosed stale wheel-packaging guard in
`tests/test_cltr_authority_136z_shared_core.py`
(`test_136z_wheel_contains_authority_shared_core_no_record_family_module`)
still forbids `request_readiness.py` in the built wheel, though Phase
136AD legitimately added it to the package. This phase's own changes did
not touch that assertion — it does not name `publication.py`, so it is
not newly triggered by this phase's own change.

## No-Go confirmations

- No `ConcurrencyConflict`, `RecoveryJournalEntry`,
  `NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
  `FinalizationReceiptAuthorityBinding`, `CompatibilityState`, or
  `QuarantineRecord` record-family model was implemented.
- No semantic validator, publication service, CAS executor, evidence
  verifier, or provider integration was implemented.
- No repository, persistence, authority resolver, or
  current/historical-authority lookup was implemented.
- No marker writer, receipt writer, notification dispatcher, or
  retry/recovery engine was implemented.
- No production runtime module imports `pcae.cltr.authority`; the
  authority package imports no production lifecycle or runtime module.
- No authority-pointer mutation, lifecycle mutation, legacy
  demotion/retirement, or CLTR authority activation occurred.
- No execution capability was introduced; runtime remains Observed /
  observe / unavailable.
- No production schema was changed by this phase; no repair was made to
  any shared-core module.
- No Blocking finding was identified; CONFIRMED-136AC-1 and
  CONFIRMED-136AE-2 are disclosed as inherited Non-Blocking and were not
  repaired.

## Verdict

**PUBLICATION MODEL IMPLEMENTATION COMPLETE WITH NON-BLOCKING FINDINGS —
READY FOR INDEPENDENT VERIFICATION**

Recommended next phase: 136AI — Stage 3 Typed Authority Model
Publication Independent Verification.

Runtime remains Observed / observe / execution unavailable. Legacy
lifecycle remains the sole production authority; CLTR remains
derivative.
