# Phase 136AH: Stage 3 Typed Authority Model Publication Implementation

## 1. Purpose and boundaries

This phase implements Typed Model Implementation Group 5 of the frozen
`136Y` plan (`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
Sec.4/Sec.23, package layout Sec.7): exactly two record-family models,
`PublicationAttempt` and `PublicationEvidence`, schema-backed by
`src/pcae/schema_resources/cltr_cutover/records/publication_attempt.schema.json`
and `.../publication_evidence.schema.json` respectively.

Both models are descriptive, immutable, schema-backed typed
representations only. Neither publishes an artifact, writes lifecycle
state, promotes a candidate, updates an authority pointer, verifies
publication success, verifies evidence, resolves a reference, executes
compare-and-swap, retries publication, recovers a failed publication,
dispatches a notification, or creates a marker or receipt. A
`PublicationAttempt` describes an attempted publication operation; it
never itself performs one. A `PublicationEvidence` preserves a claimed
publication outcome; it never itself verifies that outcome is true.
Legacy lifecycle remains the sole production authority; CLTR remains
derivative. Runtime remains Observed / observe / unavailable, unchanged
by this phase.

## 2. Binding sources

Precedence followed (identical structure to every prior phase in this
chapter): frozen primary contract (`CLTR-CUTOVER-001`,
`CLTR-CUTOVER-SCHEMAS-001` v1.0, `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001`
v1.0 Sec.25/Sec.26) → verified contract → verified architecture
(Phase 136B) → verified 136Y implementation plan → verified
136Z/136AA/136AB/136AC/136AD/136AE/136AF/136AG shared core and prior
record-family models → this governed 136AH task contract → operator
prompt. No conflict was found between the operator prompt and the frozen
contract requiring a discrepancy disclosure.

Consulted directly: the 136Y plan, the two executable schema files
(`publication_attempt.schema.json`, `publication_evidence.schema.json`),
`shared/identity.schema.json`, `shared/digest.schema.json`,
`shared/references.schema.json` (including the embedded `cas_expectation`
and `generation_reference` `$def`s), `shared/enums.schema.json`
(`publication_state`, 12 values, already shared -- reused unchanged),
`shared/failures.schema.json`, `shared/limitations.schema.json`, and the
existing shared-core and prior record-family model source
(`src/pcae/cltr/authority/*.py`, excluding `publication.py` which this
phase adds).

Disclosed schema-carried notes (not new to this phase, restated for
completeness): `publication_attempt.schema.json` names
`temporary_pointer_reference` as "present only during in-flight
publication" (NON-BLOCKING-136P-1) without a structural enum trigger --
this model leaves the field freely optional, exactly as the schema
itself does, rather than inventing an unfrozen `if`/`then` condition.
`publication_evidence.schema.json` permits `authority_role ==
"authoritative"` only in the terminal `published_and_verified` outcome
(NON-BLOCKING-136P-2) while `is_authoritative` remains the frozen const
`false` unconditionally, mirroring `AuthorityState`'s own disclosed
limitation (NON-BLOCKING-136J-1) -- both are honored as-is.

## 3. Confirmed starting state (re-verified this phase)

- `git status --short` clean; `origin/main..HEAD` = 0 commits, before
  this phase's own commits.
- `src/pcae/cltr/authority/` contained exactly the 14 shared-core modules
  plus `authority_core.py`, `request_readiness.py`, and
  `authorization_candidate.py`; no `publication.py`, no
  `PublicationAttempt`/`PublicationEvidence` class anywhere in the
  package or in `src/pcae` (grep + AST confirmed).
- No production module imports `pcae.cltr.authority` (grep confirmed
  across `src/pcae/commands`, `src/pcae/core`, `src/pcae/runtime`, and
  the rest of `src/pcae/cltr` outside the `authority` package itself).
- `pcae runtime inspect`: Runtime state Observed, execution capability
  unavailable, maximum plugin capability observe.
- `pcae health` / `pcae check` / `pcae status coherence`: all passing.

## 4. What was implemented

`src/pcae/cltr/authority/publication.py` (new module):

- **`PublicationAttempt`** (Tier 1, strict, no `_extensions`): 14
  required fields (envelope 7 + `migration_epoch`, `transition_id`,
  `attempt_id`, `request_reference`, `candidate_reference`,
  `certification_reference`, `cas_expectation`,
  `source_authority_reference`, `target_authority_reference`,
  `attempt_sequence`, `state`, `limitations`, `authority_disclosure` --
  no `phase_id`, matching the schema's own omission) plus 3
  conditionally/freely-optional fields (`temporary_pointer_reference`,
  freely optional per the schema's own disclosed gap;
  `uncertainty` iff `state == 'publication_uncertain'`;
  `failure_classification` iff `state in {'gate_rejected', 'conflict'}`).
  `request_reference`/`candidate_reference`/`certification_reference` are
  family-restricted with `schema_id`/`schema_version` unconditionally
  required (Sec.12 cross-family rule); `source_authority_reference`/
  `target_authority_reference` are family-restricted to
  `authority_epoch` without that requirement (matching the
  `epoch_reference` `$def` precedent, and may reference the identical
  epoch record). `attempt_sequence` is validated as a non-negative
  integer (bool excluded). `state` reuses the already-shared
  `PublicationState` enum (12 values) unchanged. `cas_expectation`
  reuses the shared `CasExpectation` component (third and final
  embedding site, per the schema's own disclosure) via the same parsing
  helper pattern established in `authorization_candidate.py`.
  `authority_role == 'authoritative'` is rejected.

- **`PublicationEvidence`** (Tier 1, strict, no `_extensions`): 8
  required fields (envelope 7 + `migration_epoch`, `transition_id`,
  `attempt_reference`, `outcome`, `limitations`, `authority_disclosure`)
  plus 3 conditionally-present fields (`uncertainty_detail` iff
  `outcome == 'publication_uncertain'`; `target_readback` and
  `authoritative_generation`, both iff `outcome ==
  'published_and_verified'`). `attempt_reference` is family-restricted
  to `publication_attempt` with `schema_id`/`schema_version`
  unconditionally required. `outcome` is a new record-local
  `PublicationOutcome` enum (8 values, home schema
  `publication_evidence.schema.json`, distinct from the 12-value shared
  `PublicationState`). `target_readback` carries no family restriction
  (matching the `ReadinessPackage.evidence_references` precedent).
  `authoritative_generation` reuses the shared `GenerationReference`
  wrapper (id+digest only, matching `AuthorityState`'s own
  `authoritative_generation` precedent). `authority_role ==
  'authoritative'` is structurally permitted only alongside a present
  `authoritative_generation` (i.e. only in `published_and_verified`);
  `is_authoritative` nonetheless remains the frozen const `false`
  unconditionally, unchanged.

Two new record-local nested value objects
(`PublicationAttemptUncertainty`, `PublicationEvidenceUncertaintyDetail`)
and one new record-local enum (`PublicationOutcome`), family-scoped in
the new module, matching the existing non-centralization precedent
(136Y plan Sec.5/Sec.12).

`src/pcae/cltr/authority/__init__.py`: updated to export the five new
public names and to update the module docstring's completed-groups
inventory. No shared-core module (`cas_expectation.py`, `enums.py`,
`references.py`, `digest.py`, `identity.py`, `limitations.py`,
`envelope.py`, `serialization.py`) was modified -- the existing
`PublicationState` shared enum, `CasExpectation`, and
`GenerationReference` types required no code change to be reused by
either new model.

## 5. Test suite

`tests/test_cltr_authority_136ah_publication.py`: 87 new tests (85 fast +
2 packaging/slow), independently fixtured (no fixture, helper, or
expected-value table imported from any prior phase's test module).
Covers: minimal and maximal valid construction with schema validation for
both models; every conditional-field branch (both directions:
required-when-present and forbidden-when-absent) for
`PublicationAttempt`'s `uncertainty`/`failure_classification` and
`PublicationEvidence`'s `uncertainty_detail`/`target_readback`/
`authoritative_generation`; family-restriction enforcement on every
family-tagged reference field, including the cross-family
`schema_id`/`schema_version` requirement, and the no-restriction cases
(`source_authority_reference`/`target_authority_reference`,
`target_readback`); enum member-set parity against the live schemas for
`PublicationState` (shared) and `PublicationOutcome` (new, local);
`authority_role == 'authoritative'` rejection on `PublicationAttempt`
unconditionally, and its schema-permitted acceptance on
`PublicationEvidence` only alongside `authoritative_generation`, with
`is_authoritative` always `False`; `attempt_sequence` non-negative-integer
and boolean-exclusion enforcement; the embedded `cas_expectation`
component's unconditional-field-requiredness; schema `properties`-key-set
and `required`-set parity against both live schema files; frozen-dataclass
immutability, hashability, and structural equality (including
cross-type inequality between a `PublicationAttempt` and a
`PublicationEvidence` sharing no identity relationship); no-forbidden-symbol
source scan (publication/CAS/evidence-verification symbol names); AST-based
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
`PublicationAttempt`/`PublicationEvidence` and `publication.py` were
removed from the still-forbidden lists in:

- `tests/test_cltr_authority_136z_shared_core.py` (module inventory,
  record-family class guard)
- `tests/test_cltr_authority_136aa_shared_core_independent.py` (public
  API inventory, record-family class guard, on-disk file inventory)
- `tests/test_cltr_authority_136ab_authority_core.py` (later-group class
  guard, wheel-content guard)
- `tests/test_cltr_authority_136ac_authority_core_independent.py`
  (later-group class guard)
- `tests/test_cltr_authority_136ad_request_readiness.py` (record-family
  inventory guard, wheel-content guard)
- `tests/test_cltr_authority_136ae_request_readiness_independent.py`
  (later-group class guard)
- `tests/test_cltr_authority_136af_authorization_candidate.py`
  (record-family inventory guard)
- `tests/test_cltr_authority_136ag_authorization_candidate_independent.py`
  (later-group class guard, wheel-content guard)

Every one of the remaining 7 later-group record-family names
(`ConcurrencyConflict`, `RecoveryJournalEntry`,
`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
`FinalizationReceiptAuthorityBinding`, `CompatibilityState`,
`QuarantineRecord`) remains forbidden by every one of these guards,
unchanged and re-verified passing.

**CONFIRMED-136AE-2 preserved unrepaired, as instructed.** The
already-disclosed stale wheel-packaging guard in
`tests/test_cltr_authority_136z_shared_core.py`
(`test_136z_wheel_contains_authority_shared_core_no_record_family_module`)
still forbids `request_readiness.py` in the built wheel, even though
Phase 136AD legitimately added it to the package. This phase did not
touch that specific assertion (it does not name `publication.py`, so it
is not newly triggered by this phase's own change) -- re-run and
re-confirmed identical: unrelated to this phase's scope.

## 7. Findings disclosed this phase

No new Blocking finding was identified specific to
`PublicationAttempt`/`PublicationEvidence`. The two schema-level
discrepancy disclosures already carried by the frozen schemas
(NON-BLOCKING-136P-1, NON-BLOCKING-136P-2, restated in Section 2) were
re-confirmed against the live schema files and are faithfully
implemented, not repaired or reinterpreted.

Existing findings preserved and disclosed, unchanged:

- **CONFIRMED-136AC-1**: enum construction may raise a bare `ValueError`
  instead of a `TypedModelError` subclass. This module's one new local
  enum (`PublicationOutcome`) inherits this same behavior via the
  identical `EnumClass(raw_str)` construction pattern used everywhere
  else in the package. Re-confirmed fail-closed and Non-Blocking; no
  concrete correctness consequence found this phase.
- **CONFIRMED-136AE-2**: see Section 6.
- Other inherited conditions (136U/136M scope-guard gaps, 135O/135P
  finalization-transaction/migration-evidence failures, bounded
  full-suite limitations, architecture-status phase-line parser defect,
  Telegram configuration evidence not itself proving provider delivery):
  unrelated to this phase's scope, not touched.

## 8. Regression

- `tests/test_cltr_authority_136ah_publication.py`: 87 passed (85 fast +
  2 slow/packaging), new this phase.
- `tests/test_cltr_authority_136*.py` together (all nine modules): 1394
  passed / 2 skipped (fast), plus 5 passed (slow/packaging across
  136ab/136ad/136ag/136ah).
- CLTR canonicalization + `schema_runtime`/strict-JSON/manifest/registry
  suites: 1232 passed.
- Isolated installed-wheel verification (outside the repository
  checkout): all nine record-family models import; `PublicationAttempt`
  and `PublicationEvidence` construct and round-trip; a fictitious
  forward reference constructs without lookup; `CasExpectation` remains
  data-only.
- `pcae health` / `pcae check` / `pcae status coherence` /
  `pcae doctor task-memory`: all passing throughout.

(Exact full-suite `pytest -n auto` totals are recorded in the canonical
phase-completion report; the counts above are the phase-scoped and
adjacent-regression evidence directly exercised by this phase's own
changes.)

## 9. No-go confirmation

This phase implemented no `ConcurrencyConflict`, `RecoveryJournalEntry`,
`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
`FinalizationReceiptAuthorityBinding`, `CompatibilityState`, or
`QuarantineRecord`; no semantic validator, no publication service, no CAS
executor, no evidence verifier, no provider integration, no repository,
no persistence, no authority resolver, no current-authority lookup, no
historical-authority lookup, no marker writer, no receipt writer, no
notification dispatcher, no retry engine, no recovery coordinator, no
lifecycle mutation, no authority-pointer mutation, no legacy demotion or
retirement, no CLTR authority activation, no execution capability. Runtime
remains Observed / observe / unavailable; legacy lifecycle remains sole
production authority; CLTR remains derivative.

## 10. Telegram finalization evidence

Dispatch attempted: recorded at governed finalization time (see canonical
phase-completion report/metadata). `pcae notify status` confirmed prior
to finalization: Telegram sink configured, enabled, token/chat_id
present. Provider-side delivery success is never established by
configuration evidence alone; only the actual dispatch attempt's own
recorded outcome is authoritative.

## 11. Verdict

**PUBLICATION MODEL IMPLEMENTATION COMPLETE WITH NON-BLOCKING FINDINGS —
READY FOR INDEPENDENT VERIFICATION**

## 12. Recommended next phase

**136AI — Stage 3 Typed Authority Model Publication Independent
Verification.** This phase does not begin 136AI.
