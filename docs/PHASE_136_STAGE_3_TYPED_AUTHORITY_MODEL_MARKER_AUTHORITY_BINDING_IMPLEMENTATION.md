# Phase 136AN: Stage 3 Typed Authority Model Marker Authority Binding Implementation

## 1. Purpose and boundaries

This phase implements Typed Model Implementation Group 8 of the frozen
`136Y` plan (`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
Sec.4/Sec.32, package layout Sec.7): exactly one record-family model,
`MarkerAuthorityBinding`, schema-backed by
`src/pcae/schema_resources/cltr_cutover/records/marker_authority_binding.schema.json`.
The 136Y plan's own Group 7 illustratively bundled three families
(`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
`FinalizationReceiptAuthorityBinding`) into a single `bindings.py` module;
Phase 136AL already narrowed that to `NotificationAuthorityBinding` alone.
This phase narrows the remaining scope further to exactly one additional
family, `MarkerAuthorityBinding`, added to the same already-authorized
`bindings.py` module -- consistent with every prior phase in this chapter
narrowing its own scope to a specific subset of an illustrative group.

`MarkerAuthorityBinding` is a descriptive, immutable, schema-backed typed
representation only. It never creates, writes, updates, deletes, renames,
publishes, discovers, or enumerates markers, resolves marker locations,
inspects marker files, validates marker existence, compares marker
freshness, reconciles marker state, reads marker contents, writes marker
contents, modifies marker metadata, synchronizes markers, activates
authority, resolves authority, determines current authority, compares
authorities, transfers authority, mutates an authority pointer, or
modifies lifecycle state. It describes a claimed production marker's
association with a specific generation; it never proves a marker was
actually written, is fresh, or that a duplicate-delivery conflict is
actually resolved. Legacy lifecycle remains the sole production
authority; CLTR remains derivative. Runtime remains Observed / observe /
unavailable, unchanged by this phase.

## 2. Binding sources

Precedence followed (identical structure to every prior phase in this
chapter): frozen primary contract (`CLTR-CUTOVER-001`,
`CLTR-CUTOVER-SCHEMAS-001` v1.0, `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001`
v1.0 Sec.32/Sec.46) → verified contract → verified architecture
(Phase 136B) → verified 136Y implementation plan → verified
136Z/.../136AM shared core and prior record-family models → this
governed 136AN task contract → operator prompt. No conflict was found
between the operator prompt and the frozen contract requiring a
discrepancy disclosure.

Consulted directly: the 136Y plan, the executable schema
(`marker_authority_binding.schema.json`), `shared/identity.schema.json`,
`shared/digest.schema.json`, `shared/references.schema.json`,
`shared/enums.schema.json` (`record_family`, reused unchanged),
`shared/limitations.schema.json`, and the existing shared-core and prior
record-family model source (`src/pcae/cltr/authority/*.py`), in
particular `authority_core.py`'s `AuthorityEpoch.predecessor_epoch` field
(the closest existing precedent for a nullable, family-restricted
`RecordReference` field) and `recovery_concurrency.py`'s
`ConcurrencyConflict.winner` field (the closest existing precedent for a
required-and-nullable reference field).

The schema's own description carries several disclosures, independently
re-verified against the live schema file rather than trusted at face
value:

- **NON-BLOCKING-136T-2**: the schema's field table (Sec.32) lists
  `created_at`, `authority_role`, and `digest` as bare top-level fields
  rather than as part of the uniform envelope/`authority_disclosure`
  struct used by every other already-implemented family; this
  implementation applies the uniform envelope + `authority_disclosure`
  struct precedent (`created_at` is the standard envelope field,
  `authority_role` is `authority_disclosure.authority_role`, `digest` is
  the standard `record_digest` field) rather than inventing a second,
  structurally inconsistent representation.
- **NON-BLOCKING-136T-3**: Sec.32's table does not list a `limitations`
  field for this family; this schema nonetheless includes it (every one
  of the 12 already-implemented families carries the universal
  `limitations` array, and Sec.14 groups all three binding schemas into
  the same Tier 2 policy) -- treated as a table omission, not an
  intentional exclusion, and implemented as a required field.
- `generation_reference` is typed using the dedicated
  `generation_reference` shape (id+digest only), consistent with the
  NON-BLOCKING-136N-2/NON-BLOCKING-136T-1 precedent already applied to
  `NotificationAuthorityBinding.authoritative_generation_reference`.
- `duplicate_of` is a nullable, self-family-restricted (`record_family`
  const `marker_authority_binding`) `record_reference`, conditionally
  present (required key iff `state == 'conflict'`, forbidden otherwise;
  nullable when present -- `null` means "the first, duplicated marker is
  not yet known"), with `schema_id`/`schema_version` unconditionally
  required even though the family is identical to the referencing
  record's own family, per Sec.12's cross-family reference rule applied
  to a distinct-document cross-reference.
- `compatibility_fallback_forbidden` is schema-pinned to the frozen
  `const true`; this model rejects any other boolean value, and rejects
  non-boolean values outright, matching every other frozen-`const`
  field's existing enforcement precedent in this package.
- `authority_role` `'authoritative'` is locally forbidden on this record
  (Sec.9's 12-file list); `is_authoritative` remains the frozen `const
  false` regardless, matching every other non-`AuthorityState`/
  `PublicationEvidence` family's precedent.

## 3. Confirmed starting state (re-verified this phase)

- `git status --short` clean; `origin/main..HEAD` = 0 commits, before
  this phase's own commits (canonical commit `a32dfd2d`, Phase 136AM).
- `src/pcae/cltr/authority/bindings.py` contained exactly one
  record-family model, `NotificationAuthorityBinding`; no
  `MarkerAuthorityBinding` class existed anywhere in the package or in
  `src/pcae` (grep + AST confirmed). Twelve record-family models
  existed; `MarkerAuthorityBinding` did not exist; none of the three
  remaining later record-family models
  (`FinalizationReceiptAuthorityBinding`, `CompatibilityState`,
  `QuarantineRecord`) existed.
- No production module imports `pcae.cltr.authority` (grep confirmed
  across `src/pcae/commands`, `src/pcae/core`, `src/pcae/runtime`, and
  the rest of `src/pcae/cltr` outside the `authority` package itself).
- Runtime state Observed, execution capability unavailable, maximum
  plugin capability observe (unchanged by this phase).
- `pcae health` / `pcae status coherence`: passing (after opening this
  phase's governed task contract; the inherited idle placeholder task
  was closed first).

## 4. What was implemented

`src/pcae/cltr/authority/bindings.py` (existing module, extended):

- **`MarkerAuthorityBinding`** (Tier 2, `_extensions` permitted,
  string-valued map only): 9 required fields (envelope 7 +
  `migration_epoch`, `generation_reference`, `state`,
  `compatibility_fallback_forbidden`, `limitations`,
  `authority_disclosure` -- no `phase_id`/`transition_id`, matching the
  schema's own omission from both required-family lists) plus one
  conditionally-present, nullable field:
  - `duplicate_of` iff `state == 'conflict'` (present as either `null`
    or a self-family `record_reference` with `schema_id`/`schema_version`
    unconditionally required; forbidden -- key must be entirely absent --
    for every other `state` value).

  implemented as the exact three-way tri-state (`ABSENT` /
  `None` / `RecordReference`) Layer-3 restatement the schema's own
  `allOf`/`if`/`then`/`else` conditional-presence rule plus its
  `oneOf`-null nested-field nullability jointly require.
  `generation_reference` reuses the shared `GenerationReference` wrapper.
  `state` is a new record-local `MarkerState` enum (4 values: `absent`,
  `written`, `stale`, `conflict`; home schema
  `marker_authority_binding.schema.json`). `compatibility_fallback_forbidden`
  is validated as the frozen boolean `const true`. `authority_role ==
  'authoritative'` is rejected.

No new record-local nested value object was required; `MarkerState` is
the only new record-local enum, family-scoped in the same module,
matching the existing non-centralization precedent (136Y plan
Sec.5/Sec.12).

`src/pcae/cltr/authority/__init__.py`: updated to export the two new
public names (`MarkerAuthorityBinding`, `MarkerState`) and to update the
module docstring's completed-groups inventory. No shared-core module
(`enums.py`, `references.py`, `digest.py`, `identity.py`,
`limitations.py`, `envelope.py`, `extensions.py`, `serialization.py`) was
modified -- the existing `GenerationReference`, `RecordReference`,
`require_family`, and `ExtensionMapping` types required no code change to
be reused. `RecordFamily.MARKER_AUTHORITY_BINDING` already existed in
`enums.py` (introduced alongside the other 15 companion family slugs);
no enum change was required.

## 5. Test suite

`tests/test_cltr_authority_136an_marker_authority_binding.py`: 53 new
tests (51 fast + 2 packaging/slow), independently fixtured (no fixture,
helper, or expected-value table imported from any prior phase's test
module). Covers: minimal valid construction for each non-`conflict`
`state` value (`absent`, `written`, `stale`) with schema validation;
`conflict` state with both a reference and an explicit `null`
`duplicate_of`; the `state`/`duplicate_of` conditional in both directions
(`conflict` without `duplicate_of` rejected; every non-`conflict` state
with either a reference or an explicit `null` `duplicate_of` rejected);
self-family restriction enforcement on `duplicate_of` (wrong-family
reference rejected, missing `schema_id`/`schema_version` rejected);
`compatibility_fallback_forbidden` frozen-`const`-`true` enforcement
(both `false` and non-boolean values rejected); `authority_role ==
'authoritative'` rejection; `MarkerState` enum member-set parity against
the live schema and enum strictness (no case-insensitive fallback);
`_extensions` string-valued-map enforcement (Tier 2, empty object
permitted), reserved-key-collision rejection, and non-string-value
rejection; schema `properties`-key-set and `required`-set parity against
the live schema file; frozen-dataclass immutability (including
deep-copy-on-construction of `limitations`), structural-equality tests;
no-forbidden-symbol source scan (marker-management/authority-activation
symbol names, per the operator prompt's explicit no-go list); AST-based
production-import scan; no-network/no-subprocess/no-filesystem-write
side-effect checks during construction, serialization, equality, and
`repr()`; a fresh isolated-venv wheel/sdist installation exercise,
independent of the pre-existing narrowed guards in earlier phases' test
modules.

## 6. Inherited "narrowing guard" updates (expected, matching precedent)

Every prior phase in this chapter that added a new record-family model
also narrowed the still-forbidden-name lists in earlier phases' own
"exactly N models exist" / "no later-group model exists" guard tests.
This phase follows the identical, established precedent:
`MarkerAuthorityBinding` was removed from the still-forbidden lists in:

- `tests/test_cltr_authority_136z_shared_core.py` (record-family class
  guard)
- `tests/test_cltr_authority_136aa_shared_core_independent.py` (public
  API inventory, record-family class guard)
- `tests/test_cltr_authority_136ab_authority_core.py` (later-group class
  guard)
- `tests/test_cltr_authority_136ac_authority_core_independent.py`
  (later-group class guard)
- `tests/test_cltr_authority_136ad_request_readiness.py` (package-wide
  record-family inventory guard)
- `tests/test_cltr_authority_136ae_request_readiness_independent.py`
  (later-group class guard)
- `tests/test_cltr_authority_136af_authorization_candidate.py`
  (record-family inventory guard)
- `tests/test_cltr_authority_136ag_authorization_candidate_independent.py`
  (later-group class guard)
- `tests/test_cltr_authority_136ah_publication.py` (record-family
  inventory guard)
- `tests/test_cltr_authority_136ai_publication_independent.py`
  (record-family inventory guard)
- `tests/test_cltr_authority_136aj_recovery_concurrency.py`
  (record-family inventory guard)
- `tests/test_cltr_authority_136ak_recovery_concurrency_independent.py`
  (record-family inventory guard)
- `tests/test_cltr_authority_136al_notification_authority_binding.py`
  (own-module `LATER_GROUP_MODEL_NAMES`, exact-public-exports guard
  updated to include the new module-level exports)
- `tests/test_cltr_authority_136am_notification_authority_binding_independent.py`
  (record-family inventory guard)

Every one of the remaining 3 later-group record-family names
(`FinalizationReceiptAuthorityBinding`, `CompatibilityState`,
`QuarantineRecord`) remains forbidden by every one of these guards,
unchanged and re-verified passing.

**Pre-existing inherited failures, confirmed unchanged and out of
scope.** Verified identical on the clean pre-phase baseline (via `git
stash`) before and after this phase's own changes -- none newly
introduced:

- `tests/test_cltr_authority_136ab_authority_core.py::test_136ab_wheel_contains_authority_core_module`
  and `tests/test_cltr_authority_136ad_request_readiness.py::test_136ad_wheel_contains_request_readiness_module`
  (the already-disclosed CONFIRMED-136AE-2 stale wheel-packaging guard
  lineage, unrelated to `bindings.py`; already present, unchanged, before
  this phase's own changes).

## 7. Findings disclosed this phase

No new Blocking finding was identified specific to
`MarkerAuthorityBinding`. All discrepancies between the schema's own
field-table prose and its live JSON Schema body were already disclosed
by the schema itself (NON-BLOCKING-136T-2, NON-BLOCKING-136T-3,
cross-referencing NON-BLOCKING-136N-2/NON-BLOCKING-136T-1) and
independently re-verified against the live schema file, not merely
restated from the schema's own description text.

## 8. Regression

- `tests/test_cltr_authority_136an_marker_authority_binding.py`: 53
  passed (51 fast + 2 slow/packaging), new this phase.
- `tests/test_cltr_authority_*.py` (all Stage 3 typed-authority-model
  suites) together: 1987 passed / 2 failed (both pre-existing/inherited,
  see Section 6) / 1 skipped (`-m "not slow"`).
- `pytest -m fast_green`: 4391 passed, 0 failed.
- `pcae status coherence` / `pcae health`: both passing after this
  phase's governed task contract was opened (idle placeholder task
  closed first).

## 9. No-go confirmation

This phase implemented no `FinalizationReceiptAuthorityBinding`,
`CompatibilityState`, or `QuarantineRecord`; no marker creator, no marker
writer, no marker updater, no marker deleter, no marker renamer, no
marker publisher, no marker discovery, no marker enumeration, no
marker-location resolver, no marker-file inspector, no marker-existence
validator, no marker-freshness comparator, no marker-state reconciler, no
marker-contents reader or writer, no marker-metadata modifier, no
marker synchronizer, no authority resolver, no current-authority lookup,
no authority comparator, no authority transfer, no authority-pointer
mutation, no lifecycle-state mutation, no execution capability, no
authority activation, no legacy demotion or retirement. Runtime remains
Observed / observe / unavailable; legacy lifecycle remains sole
production authority; CLTR remains derivative.

## 10. Telegram finalization evidence

Dispatch attempted: recorded at governed finalization time (see canonical
phase-completion report/metadata). `pcae notify status` confirmed prior
to finalization. Provider-side delivery success is never established by
configuration evidence alone; only the actual dispatch attempt's own
recorded outcome is disclosed.

## 11. Verdict

VERIFIED. `MarkerAuthorityBinding` is implemented as a frozen, immutable,
schema-backed, lossless typed representation only, with no operational
marker-management behavior, no authority activation, and no lifecycle
mutation. Thirteen record-family models now exist (`AuthorityEpoch`,
`AuthorityState`, `CutoverRequest`, `ReadinessPackage`,
`HumanAuthorization`, `CutoverCandidate`, `Certification`,
`PublicationAttempt`, `PublicationEvidence`, `ConcurrencyConflict`,
`RecoveryJournalEntry`, `NotificationAuthorityBinding`,
`MarkerAuthorityBinding`). Three remain absent
(`FinalizationReceiptAuthorityBinding`, `CompatibilityState`,
`QuarantineRecord`).

## 12. Recommended next phase

136AO — Stage 3 Typed Authority Model Marker Authority Binding
Independent Verification. Per instruction, this phase stops here; 136AO
is not started.
