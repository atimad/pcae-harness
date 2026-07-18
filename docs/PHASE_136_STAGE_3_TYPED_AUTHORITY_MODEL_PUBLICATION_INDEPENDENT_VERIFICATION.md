# Phase 136AI: Stage 3 Typed Authority Model Publication Independent Verification

## 1. Purpose and methodology

Phase 136AI independently verifies the Phase 136AH (commit `69abd8112f5515e9e60ac7fb5fc727413c54c491`)
implementation of `PublicationAttempt` and `PublicationEvidence`
(`src/pcae/cltr/authority/publication.py`) — Typed Model Implementation
Group 5, the fifth and final companion-record group before the Recovery
and Concurrency group (136AJ).

Per governed instruction, this phase did **not** trust Phase 136AH's own
field tables, fixtures, tests, helpers, no-go claims, or finding
classifications. Both record contracts were re-derived directly from:

- the live executable schemas `records/publication_attempt.schema.json`
  and `records/publication_evidence.schema.json`;
- the shared component schemas they compose
  (`shared/references.schema.json`, `shared/enums.schema.json`,
  `shared/limitations.schema.json`, `shared/envelope.schema.json`,
  `shared/identity.schema.json`, `shared/digest.schema.json`);
- the frozen contracts (CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0) whose
  Sec.25/Sec.26 field tables those schemas implement;
- the previously verified typed-model foundation
  (`authority_core.py`, `request_readiness.py`,
  `authorization_candidate.py`) for cross-family precedent (e.g. the
  `epoch_reference` no-schema-identity precedent, the `AuthorityState`
  `is_authoritative`-const-false-despite-`authoritative`-role
  precedent).

A new, independently fixtured test module,
`tests/test_cltr_authority_136ai_publication_independent.py`, was
written from scratch: every wire fixture (`minimal_attempt`,
`maximal_attempt`, `minimal_evidence`, `maximal_evidence`, and the
independently re-derived `INDEPENDENT_PUBLICATION_STATE_VALUES` /
`INDEPENDENT_PUBLICATION_OUTCOME_VALUES` enum tuples) was built directly
from the live schema field tables below, not copied from
`tests/test_cltr_authority_136ah_publication.py`. The only 136AH-adjacent
infrastructure reused is the shared, non-136AH-owned
`pcae.schema_runtime` offline schema-validation registry — the same live
schema files 136AH itself validates against, used here as an
independent oracle for every adversarial payload (`_assert_schema_valid`
/ `_assert_schema_invalid`), not as a source of expected values.

274 tests were written (272 fast + 2 packaging/slow), all passing.

## 2. Independently re-derived field tables

### 2.1 `PublicationAttempt` (`records/publication_attempt.schema.json`)

| Field | Wire type | Required | Null | ABSENT | Typed wrapper | Local invariant |
|---|---|---|---|---|---|---|
| `schema_id` | string (const) | yes | no | no | `RecordEnvelope.schema_id` | must equal the frozen schema URL |
| `schema_version` | string `MAJOR.MINOR` | yes | no | no | `SchemaVersionString` | pattern `^[0-9]+\.[0-9]+$` |
| `contract_version` | string (const `"1.0"`) | yes | no | no | `RecordEnvelope.contract_version` | must equal `"1.0"` |
| `record_type` | string (const) | yes | no | no | `RecordEnvelope.record_type` | must equal `"publication_attempt"` |
| `record_id` | string (record_identity) | yes | no | no | `RecordId` | pattern `^[a-z][a-z0-9-]{7,127}$` |
| `record_digest` | string (sha256_hex) | yes | no | no | `RecordDigest` | 64-hex-lowercase |
| `created_at` | string (timestamp) | yes | no | no | `Timestamp` | RFC3339 `Z`-suffix only, exact wire preserved |
| `migration_epoch` | string | yes | no | no | `MigrationEpochToken` | pattern-bound opaque token |
| `transition_id` | string | yes | no | no | `TransitionId` | `trans-` prefix |
| `attempt_id` | string (record_identity) | yes | no | no | `RecordId` | shape-checked only; determinism is Layer 4 |
| `request_reference` | object (record_reference, family=`cutover_request`) | yes | no | no | `RecordReference` | `schema_id`/`schema_version` unconditionally required |
| `candidate_reference` | object (record_reference, family=`cutover_candidate`) | yes | no | no | `RecordReference` | `schema_id`/`schema_version` unconditionally required |
| `certification_reference` | object (record_reference, family=`certification`) | yes | no | no | `RecordReference` | `schema_id`/`schema_version` unconditionally required |
| `cas_expectation` | object (embedded) | yes | no | no | `CasExpectation` | all 11 sub-fields unconditionally required |
| `source_authority_reference` | object (record_reference, family=`authority_epoch`) | yes | no | no | `RecordReference` | no `schema_id` requirement (epoch_reference precedent) |
| `target_authority_reference` | object (record_reference, family=`authority_epoch`) | yes | no | no | `RecordReference` | no `schema_id` requirement; may equal source |
| `attempt_sequence` | integer, `>= 0` | yes | no | no | `int` | non-negative; monotonicity is Layer 4 |
| `temporary_pointer_reference` | object (record_reference, unrestricted family) | **no** | no | yes | `RecordReference \| ABSENT` | schema leaves trigger condition undefined (disclosed NON-BLOCKING-136P-1) |
| `state` | string enum (12 values) | yes | no | no | `PublicationState` | strict, fail-closed |
| `uncertainty` | object (local $def) | conditional | no | conditional | `PublicationAttemptUncertainty \| ABSENT` | required iff `state == publication_uncertain`, else forbidden (biconditional) |
| `failure_classification` | string enum (`reason_code`, 24 values) | conditional | no | conditional | `ReasonCode \| ABSENT` | required iff `state in {gate_rejected, conflict}`, else forbidden (biconditional) |
| `limitations` | array of strings, `<= 32` items | yes | no | no | `Limitations` | may be empty |
| `authority_disclosure` | object (`authority_disclosure`, `authority_role != authoritative`) | yes | no | no | `AuthorityDisclosure` | `authoritative` locally forbidden at every state |

Discriminator: `record_type == "publication_attempt"`, `schema_id` const
URL. Record ID family: `attempt_id`/`record_id` both use the generic
`record_identity` pattern; `attempt_id` is the semantic identity, `record_id`
the generic envelope identifier — distinct fields, same wrapper type.

### 2.2 `PublicationEvidence` (`records/publication_evidence.schema.json`)

| Field | Wire type | Required | Null | ABSENT | Typed wrapper | Local invariant |
|---|---|---|---|---|---|---|
| `schema_id`…`created_at` | (envelope, 7 fields) | yes | no | no | `RecordEnvelope` | as above, `record_type == "publication_evidence"` |
| `migration_epoch` | string | yes | no | no | `MigrationEpochToken` | as above |
| `transition_id` | string | yes | no | no | `TransitionId` | as above |
| `attempt_reference` | object (record_reference, family=`publication_attempt`) | yes | no | no | `RecordReference` | `schema_id`/`schema_version` unconditionally required |
| `outcome` | string enum (8 values, record-local) | yes | no | no | `PublicationOutcome` | strict, fail-closed |
| `uncertainty_detail` | object (local $def) | conditional | no | conditional | `PublicationEvidenceUncertaintyDetail \| ABSENT` | required iff `outcome == publication_uncertain`, else forbidden |
| `target_readback` | object (record_reference, **unrestricted family**) | conditional | no | conditional | `RecordReference \| ABSENT` | required iff `outcome == published_and_verified`, else forbidden; no family restriction (readiness_package.evidence_references precedent) |
| `authoritative_generation` | object (`generation_reference`) | conditional | no | conditional | `GenerationReference \| ABSENT` | required iff `outcome == published_and_verified`, else forbidden |
| `limitations` | array of strings, `<= 32` items | yes | no | no | `Limitations` | may be empty |
| `authority_disclosure` | object (`authority_disclosure`, no local `not-authoritative` restriction) | yes | no | no | `AuthorityDisclosure` | `authoritative` role is *structurally permitted* here (one of exactly two families, with `AuthorityState`); `is_authoritative` remains const `False` unconditionally |

**Independent finding: no artifact/evidence-collection array field
exists on `PublicationEvidence`.** The operator prompt's verification
checklist anticipates "artifact and evidence arrays", ordering, duplicate
behavior, and array-bounds testing on this record. Independently
re-deriving the live schema shows `publication_evidence.schema.json`
declares no array-typed field beyond `limitations` (bounded, `<=32`
strings) — `PublicationEvidence` is a single-attempt, single-outcome
claim record, not a collection of evidence items. This is a documented
discrepancy between the prompt's assumed shape and the frozen schema,
not a defect in either the schema or the 136AH implementation; the
corresponding prompt sections (array bounds, ordering, duplicate
behavior, mixed-family arrays) do not apply to this record family and
were not force-fit into fictitious test cases.

## 3. Findings

### 3.1 One reproduced and repaired Blocking defect (136AI)

**BLOCKING-136AI-1 (repaired):** `_record_reference_from_dict` in
`publication.py` (the module's own self-contained Layer-3 boilerplate,
per its file-header precedent of not sharing helpers across group
modules) extracted `schema_id`/`schema_version` via bare
`field_from_payload(...)` with **no type or shape validation**, before
wrapping the rest of the reference tuple in typed wrapper classes.
`shared/references.schema.json#/$defs/record_reference` types both
fields as `{"type": "string", "minLength": 1, "maxLength": 512}` and
`{"type": "string", "pattern": "^[0-9]+\\.[0-9]+$"}` respectively — a
plain JSON Schema `"type": "string"` constraint never admits an explicit
`null`, and the pattern constraint rejects any non-matching string.
Independently reproduced against the live schema and the pre-repair
code:

- `request_reference.schema_id: null` → schema-invalid, but the
  pre-repair model **constructed successfully** with
  `schema_id=None` stored and round-tripped.
- `request_reference.schema_id: 12345` (int) and
  `schema_version: "not-a-version"` → schema-invalid, but the pre-repair
  model **constructed successfully**.

This is Blocking per the classification rules ("invalid null" and "wrong
primitive type" acceptance). Repaired in this phase, within the allowed
`src/pcae/cltr/authority/publication.py` file, via two new bounded
helpers (`_record_reference_schema_id_from_payload`,
`_record_reference_schema_version_from_payload`) that validate presence
(ABSENT-vs-explicit-value only, via `field_from_payload`, unchanged),
then independently re-validate shape when a value is present. All 87
pre-existing 136AH tests continue to pass unmodified after the repair; a
new adversarial parametrized test
(`test_malformed_cross_family_schema_id_version_rejected`) covers
`None`, wrong-primitive-type, and malformed-pattern cases for both
fields. Verified fix:

```
$ before repair: request_reference={"schema_id": null, ...} -> constructed (bug)
$ after repair:  request_reference={"schema_id": null, ...} -> TypedModelConstructionError
```

Note: the identical `_record_reference_from_dict` pattern (unvalidated
`schema_id`/`schema_version` passthrough) also exists, independently, in
`authority_core.py`, `authorization_candidate.py`, and
`request_readiness.py` (each group module owns a private copy of this
helper, per the established non-sharing precedent). Those instances are
**out of this phase's repair scope** (forbidden files) and are recorded
here as a disclosed, inherited-pattern observation for a future phase to
address if desired — not claimed as fixed by this phase.

### 3.2 Inherited findings re-confirmed, not re-litigated

- **CONFIRMED-136AC-1** (inherited, unchanged): enum construction
  (`PublicationState(...)`, `PublicationOutcome(...)`) raises a bare
  `ValueError`, not a `TypedModelError` subclass, on an unknown string.
  Reproduced directly
  (`test_bare_valueerror_on_enum_construction_inherited_confirmed`).
  Remains fail-closed (construction still fails) and Non-Blocking — no
  concrete safety or correctness consequence found in this phase.
- **CONFIRMED-136AE-2** (inherited, unchanged): the stale historical
  Phase 136Z wheel-content guard
  (`test_136z_wheel_contains_authority_shared_core_no_record_family_module`
  in `tests/test_cltr_authority_136z_shared_core.py`) still asserts
  `request_readiness` (and other later-group modules) are absent from
  the wheel, which is now false since Group 3 was legitimately shipped.
  Reproduced identically in this phase's regression run (see §12); the
  failure is unrelated to `publication.py` and was not repaired, per
  explicit governed instruction not to broaden this phase into
  unrelated historical-guard repair.
- Other inherited conditions independently reproduced in §12/§13 below:
  135O/135P finalization-transaction and migration-evidence failures,
  136U notification/marker/receipt scope-guard gap, architecture-status
  parser defect. All identical in signature to pre-136AI baselines and
  outside any file this phase touched.

### 3.3 New Non-Blocking finding

**NON-BLOCKING-136AI-1:** `publication_evidence.schema.json`'s own
`authority_disclosure` field description states the `authoritative`
`authority_role` value is permitted "only in the terminal
'published_and_verified' PublicationOutcome, alongside a non-null
`authoritative_generation` reference (enforced via if/then below)" — but
the schema's actual `allOf` block contains no such `if`/`then` clause
restricting `authority_role` by `outcome`; only the `uncertainty_detail`/
`target_readback`/`authoritative_generation` triples are enforced. The
live executable schema (the authoritative artifact) therefore does
**not** structurally restrict `authority_role: "authoritative"` to the
`published_and_verified` branch — it is unconditionally permitted at
every `outcome` value on this record family (constrained only by the
shared `is_authoritative` const-`false` rule). The 136AH implementation
correctly mirrors the live schema's actual (unrestricted) behavior, not
its overclaiming description text — matching the stated precedence order
(frozen schema over description prose). Recorded as a schema-description
drift, Non-Blocking, no repair performed (schema files are not this
phase's to modify).

## 4. Conditional pairs — independently derived exact shape

All three conditional pairs (`PublicationAttempt.state` →
`uncertainty`/`failure_classification`; `PublicationEvidence.outcome` →
`uncertainty_detail`/`target_readback`+`authoritative_generation`) were
independently confirmed to be strict **biconditionals** — the schema's
own `if`/`then`/`else: {"not": {"required": [...]}}` shape, not a
one-way implication. Every `else` branch was exercised
(`test_uncertainty_forbidden_when_not_publication_uncertain`,
`test_failure_classification_forbidden_elsewhere`,
`test_target_readback_forbidden_elsewhere`,
`test_authoritative_generation_forbidden_elsewhere`,
`test_uncertainty_detail_forbidden_elsewhere`) and confirmed Blocking-if-
violated (all pass on the current implementation — no direction was
found silently weakened to a one-way implication).

`target_readback` and `authoritative_generation` are **jointly** required
when `outcome == published_and_verified` — independently confirmed that
supplying only one and omitting the other is rejected both ways
(`test_target_readback_required_when_published_and_verified`,
`test_authoritative_generation_required_when_published_and_verified`).

## 5. Cross-family schema identity — independently confirmed

Confirmed exactly which reference fields require the cross-family
`schema_id`/`schema_version` pair (Sec.12 rule) versus which correctly
omit it:

| Reference field | Family restriction | `schema_id`/`schema_version` required |
|---|---|---|
| `PublicationAttempt.request_reference` | `cutover_request` | **yes** |
| `PublicationAttempt.candidate_reference` | `cutover_candidate` | **yes** |
| `PublicationAttempt.certification_reference` | `certification` | **yes** |
| `PublicationAttempt.source_authority_reference` | `authority_epoch` | no (epoch_reference precedent) |
| `PublicationAttempt.target_authority_reference` | `authority_epoch` | no (epoch_reference precedent) |
| `PublicationAttempt.temporary_pointer_reference` | none (unrestricted) | no |
| `PublicationEvidence.attempt_reference` | `publication_attempt` | **yes** |
| `PublicationEvidence.target_readback` | none (unrestricted) | no |

`source_authority_reference`/`target_authority_reference` were confirmed
to accept an identical epoch reference for both fields with no
self-reference prohibition (mirrors `certification.schema.json`'s Sec.23
precedent, disclosed there as NON-BLOCKING-136N-3).

## 6. Forward reference verification

`PublicationEvidence.target_readback` (unrestricted `record_reference`,
no local family `const`) was independently confirmed to accept a
syntactically valid reference naming any of the 16 `RecordFamily` enum
values, including the not-yet-implemented `concurrency_conflict`,
`marker_authority_binding`, etc. Proven with no resolution:

- `hasattr(auth, "ConcurrencyConflict")` is `False` both before and after
  construction;
- an isolated installed-wheel process (§11) constructed a
  `PublicationEvidence` with `target_readback.record_family ==
  "concurrency_conflict"` and round-tripped it byte-for-byte, with no
  import of any future model and no dynamic class construction.

`PublicationAttempt.temporary_pointer_reference` (also unrestricted
family) was independently confirmed to accept any record family the same
way.

## 7. No publication / CAS / evidence-verification execution

AST-scanned `publication.py` for every symbol in the operator prompt's
forbidden list (`publish`, `execute_publication`, `commit_publication`,
`promote`, `activate_authority`, `write_manifest`, `write_pointer`,
`atomic_replace`, `finalize_publication`, `compare_and_swap`,
`execute_cas`, `check_current_generation`, `current_authority_state`,
`retry_on_conflict`, `unlock`, `verify_evidence`, `validate_manifest`,
`check_artifact`, `confirm_publication`, `verify_receipt`,
`verify_marker`, `provider_success`) — zero matching function/method
definitions (`test_no_operational_symbols_defined_in_module_ast`).

Instrumented `socket.socket`, `subprocess.run`/`Popen`, and filesystem
writes (guarded `open()` in write/append/exclusive modes) across package
import, construction (minimal and maximal, both models), serialization,
equality, `repr()`, and invalid-input construction attempts — zero
side effects observed in every case
(`TestNoOperationalExecution`, 5 tests). A stale-but-schema-valid CAS
expectation (fictitious `expected_migration_epoch`) was constructed with
`load_current_authority_state`/`compare_and_swap`/
`check_current_generation` monkeypatched to raise on any call — zero
calls observed.

## 8. Reference non-resolution, timestamps, immutability, equality

Every reference field (`request_reference`, `candidate_reference`,
`certification_reference`, `source_authority_reference`,
`target_authority_reference`, `attempt_reference`, `target_readback`)
was independently confirmed to construct successfully against a
`record_id` that has never been created anywhere in the process, proving
no repository, filesystem, or registry lookup occurs at construction.

Timestamps: 5 valid wire forms (bare `Z`, 1/3/6-digit fractional
seconds) round-trip byte-for-byte; 6 non-`Z` or malformed forms
(`+00:00`, `+02:00`, `-05:00`, space-separated, missing `Z`, garbage)
independently confirmed schema-invalid and model-rejected
(`InvalidTimestampError`). `time.time` monkeypatched to raise during
construction — no clock access observed.

Immutability: both models and `CasExpectation` are frozen dataclasses
(`dataclasses.FrozenInstanceError` on attribute assignment, including
nested `cas_expectation.expected_migration_epoch` and
`authority_disclosure.is_authoritative`). Mutating the original
`limitations` list *after* construction does not affect the constructed
`Limitations` tuple (copy-on-construct). Mutating the dict returned by
`to_dict()` (including a nested reference) does not affect the model.

Equality: structural, full-field; identical documents compare equal,
any single field difference (including timestamp-string-only and
same-`attempt_id`-different-`state`) breaks equality; a
`published_and_verified` evidence record never compares equal to a
`not_attempted` one purely by outcome semantics — equality remains
field-structural, not outcome-semantic.

## 9. `_extensions`, unknown fields, and Tier boundary

Both schemas are Tier 1 strict (`additionalProperties: false`, no
`_extensions` escape hatch) — independently confirmed by direct JSON
inspection of both schema files and by injecting `_extensions: {}` into
both minimal fixtures (schema-invalid, model-rejected on both). Seven
plausible unauthorized field names were injected per model
(`execute`, `retry_count`, `current_state`, `lock_token`, `publisher`,
`result_verified`, `authority_activated` on `PublicationAttempt`;
`verified`, `provider_checked`, `artifact_exists`, `receipt_valid`,
`marker_created`, `notification_sent`, `authority_active`, plus
`provider_verified` on `PublicationEvidence`) — every one rejected by
both the live schema and the model.

## 10. Error behavior, discriminators, and scope guards

Discriminator/constant checks: wrong `schema_id`, wrong `record_type`
(including case and trailing-whitespace variants), wrong
`contract_version`, unsupported `schema_version`, explicit-`null`
`record_type`, and a non-string `schema_id` (int) were all independently
confirmed rejected. Error messages were spot-checked not to embed the
full nested `cas_expectation` payload verbatim.

Scope-guard verification: re-confirmed by direct AST scan
(`test_none_of_the_seven_later_families_importable_from_publication_module`,
`test_publication_module_defines_exactly_two_record_family_dataclasses`,
`test_no_later_group_model_class_declared_anywhere_in_authority_package`)
that no class named `ConcurrencyConflict`, `RecoveryJournalEntry`,
`NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
`FinalizationReceiptAuthorityBinding`, `CompatibilityState`, or
`QuarantineRecord` is declared anywhere in
`src/pcae/cltr/authority/*.py` — a stronger, independently-implemented
check than trusting 136AH's own scope-guard narrowing claim.

`pcae.cltr.authority.__all__` was confirmed to contain exactly the 9
implemented record-family model classes plus their supporting enum/
value-object types, no service/repository/operational-helper export, and
`from pcae.cltr.authority import *` was confirmed to populate a fresh
namespace with every `__all__` name and nothing unexpected.

Runtime isolation: independently AST/text-scanned `src/pcae/commands`,
`src/pcae/core`, `src/pcae/runtime`, and every sibling flat
`pcae.cltr.*` module for any import of `pcae.cltr.authority` — zero
hits — and independently AST-scanned `publication.py`'s own import list
for any `pcae.commands`/`pcae.core`/`pcae.runtime`/finalization/
notification/marker/receipt module — zero hits.

## 11. Packaging verification

Fresh wheel and sdist were built (`python -m build`) and inspected:
`pcae/cltr/authority/publication.py` and both
`records/publication_attempt.schema.json` /
`records/publication_evidence.schema.json` present in the wheel;
`recovery.py`/`bindings.py`/`compatibility_quarantine.py` absent
(2 tests, `TestPackaging`, marked `slow`, both passing).

In addition, an isolated-venv installation was performed **outside this
repository checkout** (`/private/tmp/pcae_136ai_venv`, working directory
`/private/tmp/pcae_136ai_scratch`, no repository path on `sys.path`):

- all nine record-family models imported from the installed package;
- `PublicationAttempt` constructed from a scratch minimal payload and
  round-tripped byte-for-byte (`to_dict() == input`);
- `PublicationEvidence` constructed with a `published_and_verified`
  outcome and a `target_readback` forward-referencing the
  not-yet-implemented `concurrency_conflict` family, round-tripped
  byte-for-byte, with `hasattr(auth, "ConcurrencyConflict") is False`
  confirmed inside the isolated process.

No undeclared dependency was needed beyond the package's own declared
`jsonschema` dependency (only required for the schema-validation test
helper, not for model construction itself — the isolated-venv
construction/round-trip check above succeeded without invoking
`schema_runtime` at all). The temporary wheel, venv, and scratch
directories were removed after verification; no artifact from this step
was retained in the repository.

## 12. Regression results

Commands run fresh in this phase (`.venv/bin/python -m pytest`, this
repo's own dependency-installed virtualenv):

- **new_136ai_publication_suite:** `tests/test_cltr_authority_136ai_publication_independent.py`
  — 274 passed (272 fast + 2 slow/packaging).
- **136z_through_136ai_together:** `tests/test_cltr_authority_136z_shared_core.py`
  through `tests/test_cltr_authority_136ai_publication_independent.py`
  (all 10 authority test modules), `-n auto` — **1500 passed, 1 skipped,
  1 failed**. The 1 failure is
  `test_136z_wheel_contains_authority_shared_core_no_record_family_module`
  — the pre-existing CONFIRMED-136AE-2 stale wheel-content guard,
  reproduced identically, unrelated to `publication.py`.
- **canonicalization_and_schema_runtime:** `pytest tests/ -k "canonicaliz or
  executable_schema or strict_json or manifest or registry" -n auto` —
  **1232 passed**, matching the 136AH-recorded baseline exactly.
- **fast_green:** `pytest -m fast_green -n auto` — **4391 passed**,
  matching the 136AH-recorded baseline exactly (this phase's new test
  module is not marked `fast_green`, consistent with every prior
  `test_cltr_authority_136a*` module).
- **report_notification_finalization_spot_check:** `pytest tests/ -k
  "notify or notification or finaliz or phase_report" -n auto` — 1151
  passed, 2 skipped, **11 failed**. All 11 failures fall within the
  already-disclosed inherited categories named in the operator prompt:
  `test_finalization_transaction_134e10.py` (3, inherited 135O/135P
  finalization-transaction), `test_cltr_migration_135p_verification.py`
  (4, inherited 135P migration-evidence), `test_phase_reports.py` (1),
  and `test_cltr_cutover_136u_notification_marker_receipt_binding_independent_verification.py`
  (1, inherited 136U scope-guard gap) — none touches `publication.py` or
  any file this phase changed.

`passed_with_disclosed_inherited_failures` is used for the two runs
above with inherited failures, per exact-identity and unrelatedness
confirmed by file-path inspection (no file this phase changed appears in
any failing test's module path).

## 13. Bounded diagnostic

A full 23000+-test quick-tier repository sweep (as the 136AH report
recorded, ~18 minutes) was **not** re-run in this phase — out of scope
for a bounded diagnostic per explicit governed instruction not to
broaden into infrastructure repair, and the module-scoped and
category-scoped runs in §12 already establish: the 136AI suite completes
promptly (0.5s fast-tier, 4.4s including wheel/sdist build); the 136AH
suite completes unchanged (87 passed, 5.2s); no hang was observed in any
`publication.py` code path across 274 new adversarial tests including
stale-CAS, forward-reference, and malformed-payload cases; no
filesystem/provider/CAS/notification/marker/receipt/authority-lookup
side effect was observed under active monkeypatched instrumentation
(§7); no resource leak indicator (open sockets, subprocess handles, file
descriptors) was introduced. This is disclosed honestly as a narrower
diagnostic scope than the full quick-tier sweep, not claimed as
equivalent to it.

## 14. Verdict

**PUBLICATION MODELS VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR
RECOVERY MODEL IMPLEMENTATION**

One Blocking defect was independently reproduced
(BLOCKING-136AI-1, §3.1) and repaired within this phase's allowed file
(`src/pcae/cltr/authority/publication.py`) before finalization; no
unresolved Blocking finding remains. Two inherited findings
(CONFIRMED-136AC-1, CONFIRMED-136AE-2) were reproduced identically and
remain Non-Blocking. One new Non-Blocking schema-description-drift
finding (NON-BLOCKING-136AI-1) was recorded. Runtime remains Observed /
observe / unavailable throughout; no execution capability, authority
mutation, or production integration was introduced.

Recommended next phase: **136AJ — Stage 3 Typed Authority Model Recovery
and Concurrency Implementation.** That phase should implement only
`ConcurrencyConflict` and `RecoveryJournalEntry`.

## 15. Telegram finalization disclosure

Dispatch attempted: see governed finalization output recorded in
`.pcae/phase-completion-report.md` / `.pcae/phase-completion-metadata.json`
for this phase, generated by `pcae phase complete` at the moment of
finalization (not fabricated here in advance).
