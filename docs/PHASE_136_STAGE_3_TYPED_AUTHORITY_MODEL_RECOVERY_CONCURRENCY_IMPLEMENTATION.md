# Phase 136AJ: Stage 3 Typed Authority Model Recovery and Concurrency Implementation

## 1. Purpose and boundaries

This phase implements Typed Model Implementation Group 6 of the frozen
`136Y` plan (`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
Sec.4/Sec.27-28, package layout Sec.7): exactly two record-family models,
`ConcurrencyConflict` and `RecoveryJournalEntry`, schema-backed by
`src/pcae/schema_resources/cltr_cutover/records/concurrency_conflict.schema.json`
and `.../recovery_journal_entry.schema.json` respectively.

Both models are descriptive, immutable, schema-backed typed
representations only. Neither detects a live concurrency conflict,
compares current and expected authority state, executes compare-and-swap,
acquires a lock, retries publication, performs recovery, resumes
execution, replays a lifecycle operation, mutates a record, repairs
authority state, selects a recovery action, persists a journal entry,
resolves a reference, verifies evidence, inspects repository or runtime
state, activates CLTR authority, or demotes/retires legacy authority. A
`ConcurrencyConflict` describes an already-declared conflict; it never
discovers one. A `RecoveryJournalEntry` describes a declared historical
or intended recovery record; it never plans or executes recovery. Legacy
lifecycle remains the sole production authority; CLTR remains derivative.
Runtime remains Observed / observe / unavailable, unchanged by this
phase.

## 2. Binding sources

Precedence followed (identical structure to every prior phase in this
chapter): frozen primary contract (`CLTR-CUTOVER-001`,
`CLTR-CUTOVER-SCHEMAS-001` v1.0, `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001`
v1.0 Sec.27/Sec.28) → verified contract → verified architecture
(Phase 136B) → verified 136Y implementation plan → verified
136Z/136AA/136AB/136AC/136AD/136AE/136AF/136AG/136AH/136AI shared core and
prior record-family models → this governed 136AJ task contract → operator
prompt. No conflict was found between the operator prompt and the frozen
contract requiring a discrepancy disclosure.

Consulted directly: the 136Y plan, the two executable schema files
(`concurrency_conflict.schema.json`, `recovery_journal_entry.schema.json`),
`shared/identity.schema.json`, `shared/digest.schema.json` (including the
already-defined but previously unused `journal_entry_digest` alias),
`shared/references.schema.json`, `shared/enums.schema.json`
(`recovery_state`, 10 values, already shared -- reused unchanged),
`shared/limitations.schema.json`, and the existing shared-core and prior
record-family model source (`src/pcae/cltr/authority/*.py`, excluding
`recovery_concurrency.py` which this phase adds).

Both schemas' own descriptions carry an unusually dense set of prior
disclosures (Sec.27/Sec.28 authored at Phase 136R, well before this
implementation phase), all independently re-verified against the live
schema files rather than trusted at face value:

- **`winner`** (`ConcurrencyConflict`) is required-and-nullable, the one
  deliberate exception to the package's general absent-preferred
  convention: every conflict record must take an explicit position (a
  reference, or `null` for "not yet known"). Confirmed: `winner` is in
  the schema's top-level `required` array and its type union is
  `oneOf(null, record_reference)` -- re-implemented exactly, serialized
  as an always-present key.
- **`expected_state`/`observed_state`** (`ConcurrencyConflict`) carry no
  `record_family` restriction (disclosed as NON-BLOCKING-136R-3);
  re-confirmed against the live schema (plain `record_reference` `$ref`,
  no `allOf`/`const` restriction) and implemented with
  `required_family=None`.
- **`operation_reference`/`prior_state_reference`/`new_state_reference`**
  (`RecoveryJournalEntry`) likewise carry no family restriction
  (NON-BLOCKING-136R-3), re-confirmed identically.
- **`generation_reference`** (`RecoveryJournalEntry`) is typed as the
  dedicated id+digest `generation_reference` shape, not a family-tagged
  `record_reference` (NON-BLOCKING-136R-4) -- re-confirmed against the
  live schema's `$ref` target and reused via the existing shared
  `GenerationReference` wrapper unchanged.
- **`publication_attempt_reference`** (`RecoveryJournalEntry`) is freely
  optional rather than tied to a structural trigger enum
  (NON-BLOCKING-136R-1, same category as `PublicationAttempt`'s own
  `temporary_pointer_reference` precedent) -- re-confirmed absent from
  the schema's `required` array with no `if`/`then` naming it, and left
  freely optional here.
- **`operator_review`/`recovery_action`** (`RecoveryJournalEntry`) are
  each a minimal bounded object with exactly one required disclosure-text
  field (`notes`, `description` respectively) rather than a richer
  invented shape (NON-BLOCKING-136R-1) -- re-confirmed against the live
  `$defs` and reused via the same `_validate_disclosure_text` helper
  publication.py's `PublicationAttemptUncertainty` established.
- **Hash-chain shape** (`RecoveryJournalEntry.prior_entry_digest`): `null`
  only when `sequence == 0` (genesis), a well-formed `sha256_hex`
  otherwise -- re-confirmed as two `allOf`/`if`/`then` branches in the
  live schema, implemented as a single Layer-3 conditional. Chain
  *integrity* (that a given `prior_entry_digest` genuinely matches the
  immediately preceding entry's own digest, and that `sequence` values
  are contiguous with no gap across documents) is explicitly Layer 4,
  never enforced here -- confirmed by allowing a self-referencing digest
  and duplicate `sequence` values across independent documents to
  construct without error (Section 5).

## 3. Confirmed starting state (re-verified this phase)

- `git status --short` clean; `origin/main..HEAD` = 0 commits, before
  this phase's own commits.
- `src/pcae/cltr/authority/` contained exactly the 14 shared-core modules
  plus `authority_core.py`, `request_readiness.py`,
  `authorization_candidate.py`, and `publication.py`; no
  `recovery_concurrency.py`, no `ConcurrencyConflict`/
  `RecoveryJournalEntry` class anywhere in the package or in `src/pcae`
  (grep + AST confirmed). Nine record-family models existed; neither new
  recovery model existed; none of the five later record-family models
  (`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
  `FinalizationReceiptAuthorityBinding`, `CompatibilityState`,
  `QuarantineRecord`) existed.
- Authoritative Phase 136AI commits confirmed by direct `git show`
  inspection, matching the canonical report exactly:
  `80b88e14867cabab06a220a85eb465b4b94a066b` (Stage 3 Typed Authority
  Model Publication Independent Verification) and
  `f9ec0bd2b7ae2c7ccd926fc39bf2501222e8d5b7` (task-memory DONE.md
  repair). This phase found no discrepancy between actual git history
  and the canonical 136AI commit list; the referenced "Claude's separate
  claim of three commits" was not reproduced or repaired -- historical
  report accuracy for 136AI is out of scope for this phase.
- No production module imports `pcae.cltr.authority` (grep confirmed
  across `src/pcae/commands`, `src/pcae/core`, `src/pcae/runtime`, and
  the rest of `src/pcae/cltr` outside the `authority` package itself).
- `pcae runtime inspect`: Runtime state Observed, execution capability
  unavailable, maximum plugin capability observe.
- `pcae health` / `pcae check` / `pcae status coherence`: all passing.

## 4. What was implemented

`src/pcae/cltr/authority/recovery_concurrency.py` (new module):

- **`ConcurrencyConflict`** (Tier 2, `_extensions` permitted, string-
  valued map only): 10 required fields (envelope 7 + `migration_epoch`,
  `actors`, `requests`, `type`, `winner`, `recovery_requirement`,
  `limitations`, `authority_disclosure` -- no `phase_id`/`transition_id`,
  matching the schema's own omission from both required-family lists)
  plus 2 conditionally-present fields (`expected_state`/`observed_state`,
  both iff `type == 'cas_mismatch'`, one-way in the executable schema and
  implemented as the exact two-way Layer-3 restatement the schema itself
  enforces via its `allOf`/`if`/`then`/`else`). `actors` is a
  heterogeneous array (minimum 2 entries) of either a bare
  `PrincipalIdentifier` string or an unrestricted `RecordReference`
  object -- a new `Union[PrincipalIdentifier, RecordReference]` type
  alias (`ActorEntry`), parsed by inspecting the raw JSON value's Python
  type (`str` vs `dict`) rather than a discriminator field, matching the
  schema's own `oneOf` shape. `requests` (minimum 1 entry) is
  family-restricted to `cutover_request` with `schema_id`/
  `schema_version` unconditionally required (Sec.12 cross-family rule).
  `winner` is the required-and-nullable field described in Section 2.
  `recovery_requirement` reuses the already-shared `RecoveryState` enum
  (10 values) unchanged. `type` is a new record-local `ConflictType` enum
  (4 values, home schema `concurrency_conflict.schema.json`).
  `authority_role == 'authoritative'` is rejected.

- **`RecoveryJournalEntry`** (Tier 2, `_extensions` permitted,
  string-valued map only): 14 required fields (envelope 7 +
  `migration_epoch`, `transition_id`, `sequence`, `prior_entry_digest`,
  `operation_reference`, `prior_state_reference`, `new_state_reference`,
  `authority_state_reference`, `generation_reference`,
  `external_effect_state`, `retry_replay_classification`, `state`,
  `limitations`, `authority_disclosure`) plus 3 conditionally/freely-
  optional fields (`publication_attempt_reference`, freely optional per
  the schema's own disclosed gap; `operator_review` iff
  `state in {'reviewed', 'actioned', 'superseded'}`; `recovery_action`
  iff `state == 'actioned'`). `sequence` is validated as a non-negative
  integer (bool excluded); `prior_entry_digest` follows the hash-chain
  shape in Section 2, using the already-defined-but-previously-unused
  `JournalEntryDigest` wrapper. `authority_state_reference` is
  family-restricted to `authority_state`;
  `publication_attempt_reference`, when present, is family-restricted to
  `publication_attempt`; neither carries the cross-family
  `schema_id`/`schema_version` requirement (matching the
  `epoch_reference`-style precedent, not the `request_reference`-style
  one). `generation_reference` reuses the shared `GenerationReference`
  wrapper (id+digest only) per NON-BLOCKING-136R-4. `external_effect_state`
  (4 values) and `retry_replay_classification` (3 values) are new
  record-local inline enums; `state` is a new record-local `JournalState`
  enum (4 values, home schema `recovery_journal_entry.schema.json`).
  `authority_role == 'authoritative'` is rejected.

Two new record-local nested value objects (`OperatorReview`,
`RecoveryAction`) and four new record-local enums (`ConflictType`,
`ExternalEffectState`, `RetryReplayClassification`, `JournalState`),
family-scoped in the new module, matching the existing
non-centralization precedent (136Y plan Sec.5/Sec.12).

`src/pcae/cltr/authority/__init__.py`: updated to export the eight new
public names and to update the module docstring's completed-groups
inventory. No shared-core module (`enums.py`, `references.py`,
`digest.py`, `identity.py`, `limitations.py`, `envelope.py`,
`extensions.py`, `serialization.py`) was modified -- the existing
`RecoveryState` shared enum, `JournalEntryDigest` wrapper, and
`GenerationReference`/`ExtensionMapping` types required no code change to
be reused by either new model.

## 5. Test suite

`tests/test_cltr_authority_136aj_recovery_concurrency.py`: 110 new tests
(107 fast + 3 packaging/slow), independently fixtured (no fixture,
helper, or expected-value table imported from any prior phase's test
module). Covers: minimal and maximal valid construction with schema
validation for both models; every conditional-field branch (both
directions: required-when-present and forbidden-when-absent) for
`ConcurrencyConflict`'s `expected_state`/`observed_state` and
`RecoveryJournalEntry`'s `operator_review`/`recovery_action`/
`prior_entry_digest`-vs-`sequence`; `actors` heterogeneous-array parsing
(all-string, all-reference, and invalid-shape cases) and minimum-length
enforcement; `requests` family-restriction, cross-family
`schema_id`/`schema_version` requirement, and minimum-length enforcement;
`winner`'s always-present-key, nullable serialization; hash-chain shape
(genesis vs. non-genesis, explicit self-reference and duplicate-sequence-
across-documents both proven constructible with no chain-integrity
check); family-restriction enforcement on `authority_state_reference`/
`publication_attempt_reference`, and the no-restriction cases
(`operation_reference`/`prior_state_reference`/`new_state_reference`, and
`ConcurrencyConflict`'s `expected_state`/`observed_state`/`winner`); enum
member-set parity against the live schemas for `RecoveryState` (shared),
`ConflictType`, `ExternalEffectState`, `RetryReplayClassification`, and
`JournalState` (all new, local); `authority_role == 'authoritative'`
rejection on both models unconditionally; `_extensions` string-valued-map
enforcement, explicit-null rejection, and reserved-key-collision
rejection (Tier 2, unlike Group 5's Tier 1 models); schema
`properties`-key-set and `required`-set parity against both live schema
files; frozen-dataclass immutability (including deep-copy-on-construction
of nested `_extensions`/`actors` values), hashability (and its absence
when `_extensions` is present, matching `ExtensionMapping`'s documented
unhashability), and structural equality (including cross-type inequality
between a `ConcurrencyConflict` and a `RecoveryJournalEntry`, and
actor-array-order sensitivity); no-forbidden-symbol source scan
(conflict-detection/CAS/recovery-execution/persistence symbol names, per
the operator prompt's explicit list); an instrumented no-current-state-
comparison proof (`RecordReference.__eq__` never invoked during
construction or serialization); AST-based production-import scan; no-
network/no-subprocess/no-filesystem-write side-effect checks during
construction, serialization, equality, and `repr()`; a fresh
isolated-venv wheel/sdist installation exercise, independent of the
pre-existing narrowed guards in earlier phases' test modules.

## 6. Inherited "narrowing guard" updates (expected, matching precedent)

Every prior phase in this chapter that added a new record-family model
also narrowed the still-forbidden-name lists in earlier phases' own
"exactly N models exist" / "no later-group model exists" guard tests.
This phase follows the identical, established precedent:
`ConcurrencyConflict`/`RecoveryJournalEntry` and
`recovery_concurrency.py` were removed from the still-forbidden lists
in:

- `tests/test_cltr_authority_136z_shared_core.py` (module inventory,
  record-family class guard)
- `tests/test_cltr_authority_136aa_shared_core_independent.py` (public
  API inventory, record-family class guard, on-disk file inventory)
- `tests/test_cltr_authority_136ab_authority_core.py` (later-group class
  guard)
- `tests/test_cltr_authority_136ac_authority_core_independent.py`
  (later-group class guard)
- `tests/test_cltr_authority_136ad_request_readiness.py` (package-wide
  record-family inventory guard -- the separate module-scoped
  `LATER_GROUP_MODEL_NAMES` tuple used only to assert
  `request_readiness.py` itself declares none of the other groups'
  classes was deliberately left unchanged, since it never asserted
  package-wide absence and `ConcurrencyConflict` was never, and is not
  now, declared in that module)
- `tests/test_cltr_authority_136ae_request_readiness_independent.py`
  (later-group class guard)
- `tests/test_cltr_authority_136af_authorization_candidate.py`
  (record-family inventory guard)
- `tests/test_cltr_authority_136ag_authorization_candidate_independent.py`
  (later-group class guard)
- `tests/test_cltr_authority_136ah_publication.py` (record-family
  inventory guard)
- `tests/test_cltr_authority_136ai_publication_independent.py`
  (record-family inventory guard, public-API-surface guard,
  package-wide class-declaration guard). This file's own forward-
  reference-to-unimplemented-family test previously used
  `concurrency_conflict` as its example not-yet-implemented family; it
  was updated to use `quarantine_record` instead (still genuinely
  unimplemented), preserving the test's original intent (a fictitious
  forward reference constructs with no lookup, import, or dynamic class
  construction) without asserting something now false.

Every one of the remaining 5 later-group record-family names
(`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
`FinalizationReceiptAuthorityBinding`, `CompatibilityState`,
`QuarantineRecord`) remains forbidden by every one of these guards,
unchanged and re-verified passing.

**CONFIRMED-136AE-2 preserved unrepaired, as instructed.** The
already-disclosed stale wheel-packaging guard in
`tests/test_cltr_authority_136z_shared_core.py`
(`test_136z_wheel_contains_authority_shared_core_no_record_family_module`)
still forbids `request_readiness.py` in the built wheel, even though
Phase 136AD legitimately added it to the package. This phase did not
touch that specific assertion (it does not name `recovery_concurrency.py`,
so it is not newly triggered by this phase's own change) -- re-run and
re-confirmed identical: unrelated to this phase's scope.

## 7. Findings disclosed this phase

No new Blocking finding was identified specific to
`ConcurrencyConflict`/`RecoveryJournalEntry`. The schema-level discrepancy
disclosures already carried by the frozen schemas (NON-BLOCKING-136R-1,
NON-BLOCKING-136R-3, NON-BLOCKING-136R-4, restated in Section 2) were
re-confirmed against the live schema files and are faithfully
implemented, not repaired or reinterpreted.

Existing findings preserved and disclosed, unchanged:

- **CONFIRMED-136AC-1**: enum construction may raise a bare `ValueError`
  instead of a `TypedModelError` subclass. This module's four new local
  enums (`ConflictType`, `ExternalEffectState`,
  `RetryReplayClassification`, `JournalState`) inherit this same behavior
  via the identical `EnumClass(raw_str)` construction pattern used
  everywhere else in the package. Re-confirmed fail-closed and
  Non-Blocking; no concrete correctness consequence found this phase.
- **CONFIRMED-136AE-2**: see Section 6.
- **NON-BLOCKING-136AI-1**: a publication-schema description overstates
  an `authority_role` restriction the executable schema does not enforce.
  Unrelated to either new schema this phase implements; not touched.
- **BLOCKING-136AI-1 (repaired)**: publication reference `schema_id`/
  `schema_version` shape validation. Re-confirmed intact and unregressed
  -- this phase's own `_record_reference_schema_id_from_payload`/
  `_record_reference_schema_version_from_payload` helpers independently
  re-derive and re-implement the identical shape check (not a shared
  import from `publication.py`, per this package's established
  per-module-ownership convention for Layer-3 construction boilerplate),
  and `publication.py` itself was not modified by this phase.
- Other inherited conditions (136U/136M scope-guard gaps, 135O/135P
  finalization-transaction/migration-evidence failures, bounded
  full-suite limitations, architecture-status phase-line parser defect,
  advisory-runtime-directory baseline failures, Telegram configuration
  evidence not itself proving provider delivery): unrelated to this
  phase's scope, not touched.

No new failure was introduced by this phase's own module path
(`recovery_concurrency.py`) or test module in any adjacent or full-suite
run performed.

## 8. Regression

- `tests/test_cltr_authority_136aj_recovery_concurrency.py`: 110 passed
  (107 fast + 3 slow/packaging), new this phase.
- `tests/test_cltr_authority_136*.py` together (all eleven modules): 1596
  passed / 1 skipped (fast), plus packaging/slow suites passing
  independently across 136ab/136ad/136ag/136ah/136aj.
- CLTR canonicalization + `schema_runtime` (boundaries, JSON parser,
  loader, packaging, registry, validation, 136G independent) suites: all
  passed.
- `pytest -m fast_green`: 4391 passed, 0 failed.
- Bounded full-suite diagnostic (`pytest -q -m "not slow" -n auto`)
  performed; no hang observed in the new recovery/concurrency module or
  its adjacent suites; exact totals recorded in the canonical
  phase-completion report.
- Isolated installed-wheel verification (outside the repository
  checkout): all eleven record-family models import; `ConcurrencyConflict`
  and `RecoveryJournalEntry` construct and round-trip; none of the five
  still-unimplemented later families import.
- `pcae health` / `pcae check` / `pcae status coherence` /
  `pcae doctor task-memory`: all passing throughout.

## 9. No-go confirmation

This phase implemented no `NotificationAuthorityBinding`,
`MarkerAuthorityBinding`, `FinalizationReceiptAuthorityBinding`,
`CompatibilityState`, or `QuarantineRecord`; no conflict detector, no
conflict resolver, no CAS executor, no lock manager, no retry scheduler,
no recovery planner, no recovery executor, no replay engine, no rollback
engine, no journal repository, no persistence, no authority resolver, no
current-authority lookup, no historical-authority lookup, no
compatibility resolver, no quarantine coordinator, no lifecycle
integration, no execution capability, no authority activation, no legacy
demotion or retirement. Runtime remains Observed / observe / unavailable;
legacy lifecycle remains sole production authority; CLTR remains
derivative.

## 10. Telegram finalization evidence

Dispatch attempted: recorded at governed finalization time (see canonical
phase-completion report/metadata). `pcae notify status` confirmed prior
to finalization. Provider-side delivery success is never established by
configuration evidence alone; only the actual dispatch attempt's own
recorded outcome is authoritative.

## 11. Verdict

**RECOVERY AND CONCURRENCY MODEL IMPLEMENTATION COMPLETE WITH
NON-BLOCKING FINDINGS — READY FOR INDEPENDENT VERIFICATION**

## 12. Recommended next phase

Recommended next phase: 136AK — Stage 3 Typed Authority Model Recovery
and Concurrency Independent Verification. This phase does not begin
136AK.
