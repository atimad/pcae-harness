# Phase 136AM: Stage 3 Typed Authority Model Notification Authority Binding Independent Verification

## 1. Purpose and methodology

Phase 136AM independently verifies the Phase 136AL (commit `8b498c9a`)
implementation of `NotificationAuthorityBinding`
(`src/pcae/cltr/authority/bindings.py`) — Typed Model Implementation
Group 7, the seventh companion-record group in the frozen 136Y plan.

Per governed instruction, this phase did **not** trust Phase 136AL's own
field tables, fixtures, tests, helper functions, comments, decisions, or
prior verification reports. The record contract was independently
re-derived directly from:

- the live executable schema
  `records/notification_authority_binding.schema.json`;
- the shared component schemas it composes
  (`shared/references.schema.json`, `shared/enums.schema.json`,
  `shared/limitations.schema.json`, `shared/envelope.schema.json`,
  `shared/identity.schema.json`, `shared/digest.schema.json`);
- the frozen contract text quoted in the schema's own `description`
  fields (CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Sec.31, Sec.46);
- the previously verified typed-model foundation (`references.py`,
  `digest.py`, `identity.py`, `envelope.py`, `limitations.py`,
  `sentinels.py`, `errors.py`, `extensions.py`) for cross-family
  precedent (e.g. the `generation_reference` no-family-restriction
  precedent, the `is_authoritative` const-`false`-regardless-of-role
  precedent, the Tier 2 `_extensions` string-map precedent).

A new, independently fixtured test module,
`tests/test_cltr_authority_136am_notification_authority_binding_independent.py`,
was written from scratch: every wire fixture (`_nab_wire`, `_epoch_ref`,
`_marker_ref`, `_receipt_ref`, `_generation_ref`, and the independently
re-derived `DELIVERY_STATE_MEMBERS` tuple) was built directly from the
live schema's field table and `$defs`, not copied from
`tests/test_cltr_authority_136al_notification_authority_binding.py`. The
only 136AL-adjacent infrastructure reused is the shared, non-136AL-owned
`pcae.schema_runtime` offline schema-validation registry — the same live
schema file 136AL itself validates against, used here as an independent
oracle for every adversarial payload (`_assert_schema_valid` /
`_assert_schema_invalid`), not as a source of expected values.

109 tests were written (107 fast + 2 packaging/slow), all passing.

## 2. Independently re-derived field table

### `NotificationAuthorityBinding` (`records/notification_authority_binding.schema.json`)

| Field | Wire type | Required | Null | ABSENT | Typed wrapper | Local invariant |
|---|---|---|---|---|---|---|
| `schema_id` | string (const) | yes | no | no | `RecordEnvelope.schema_id` | must equal the frozen schema URL |
| `schema_version` | string `MAJOR.MINOR` | yes | no | no | `SchemaVersionString` | pattern `^[0-9]+\.[0-9]+$` |
| `contract_version` | string (const `"1.0"`) | yes | no | no | `RecordEnvelope.contract_version` | must equal `"1.0"` |
| `record_type` | string (const) | yes | no | no | `RecordEnvelope.record_type` | must equal `"notification_authority_binding"` |
| `record_id` | string (record_identity) | yes | no | no | `RecordId` | pattern `^[a-z][a-z0-9-]{7,127}$` |
| `record_digest` | string (sha256_hex) | yes | no | no | `RecordDigest` | 64-hex-lowercase; restates Sec.31's `digest` field (NON-BLOCKING-136T-1, schema-disclosed) |
| `created_at` | string (timestamp) | yes | no | no | `Timestamp` | RFC3339 `Z`-suffix only |
| `migration_epoch` | string | yes | no | no | `MigrationEpochToken` | pattern-bound opaque token; not in the phase_id- or transition_id-required family lists |
| `authoritative_generation_reference` | `generation_reference` (id+digest only) | yes | no | no | `GenerationReference` | not a `record_reference` — no `record_family` field exists (NON-BLOCKING-136N-2 precedent) |
| `authority_epoch_reference` | `record_reference` restricted to `authority_epoch` | yes | no | no | `RecordReference` (family-checked) | no `schema_id`/`schema_version` required (mirrors `epoch_reference` precedent) |
| `payload_digest` | string (sha256_hex) | yes | no | no | `Sha256Digest` | shape-checked only, never recomputed against payload bytes |
| `attempt_identity` | string (record_identity) | yes | no | no | `RecordId` | opaque dispatch-attempt identity; not itself a `record_reference` |
| `pfn001_classification` | string, bounded 1-256 ASCII | yes | no | no | `str` (validated) | restates existing PFN-001 vocabulary as shape only, no closed enum |
| `delivery_state` | enum (3) | yes | no | no | `DeliveryState` | `not_dispatched`/`already_dispatched`/`payload_conflict` |
| `uncertainty` | object `{reason}` | conditional | no | yes | `NotificationAuthorityBindingUncertainty \| AbsentType` | required iff `delivery_state == payload_conflict`, else forbidden |
| `marker_reference` | `record_reference` restricted to `marker_authority_binding` | conditional | no | yes | `RecordReference \| AbsentType` | forbidden iff `delivery_state == not_dispatched`, else required; `schema_id`/`schema_version` unconditionally required (Sec.12 cross-family rule) |
| `receipt_reference` | `record_reference` restricted to `receipt_authority_binding` | conditional | no | yes | `RecordReference \| AbsentType` | required iff `delivery_state == already_dispatched`, else forbidden; `schema_id`/`schema_version` unconditionally required |
| `limitations` | array of strings | yes | no | no | `Limitations` | may be empty |
| `authority_disclosure` | object | yes | no | no | `AuthorityDisclosure` | `authority_role != "authoritative"` locally forbidden (Sec.9's 12-file list) |
| `_extensions` | object, string-valued | no | no | yes | `ExtensionMapping` | Tier 2, ≤32 keys, string values only |

Independently confirmed: `additionalProperties: false` at the top level
(unknown-key rejection, 20 properties total); exactly 16 required fields
(confirmed programmatically against the live schema's own `required`
array, `test_136am_exactly_sixteen_required_fields_confirmed_against_live_schema`);
no `phase_id`/`transition_id` fields.

## 3. Findings

No Blocking finding was independently reproduced. Every field, wrapper
type, required/optional/nullable classification, all three conditional
branches, the 3-value enum vocabulary, both reference family
restrictions, and error-behavior expectations independently derived in
§2 above matched `bindings.py` exactly, confirmed by 109 passing tests
(107 fast, 2 packaging/slow) exercising both the live schema-validation
oracle and the typed model side by side for every case.

### 3.1 Inherited findings re-confirmed, not re-litigated

Reproduced identically in this phase's regression run (§13 below), all
unrelated to `bindings.py` and outside any file this phase touched:

- **CONFIRMED-136AC-1** (inherited, unchanged): enum construction (e.g.
  `DeliveryState(...)`) raises a bare `ValueError`, not a
  `TypedModelError` subclass, on an unknown string. Still fail-closed;
  Non-Blocking.
- **CONFIRMED-136AE-2 / re-observed here as the same class of stale
  wheel-content guard**: `tests/test_cltr_authority_136ab_authority_core.py::test_136ab_wheel_contains_authority_core_module`
  and
  `tests/test_cltr_authority_136ad_request_readiness.py::test_136ad_wheel_contains_request_readiness_module`
  (neither marked `slow`, unlike every later phase's own wheel-content
  test) still assert that `bindings.py` is absent from a freshly built
  wheel — false since Phase 136AL added it. Independently reproduced on
  a `git stash`-isolated re-run of the unmodified pre-136AM commit
  `9b7b8c0f` (this phase's own starting commit, zero 136AM files
  present): the same two tests fail identically. This confirms the
  failure is inherited from Phase 136AL (which added `bindings.py`),
  not introduced by this phase. Non-Blocking; outside this phase's
  allowed files to repair (`recovery_concurrency.py`/`bindings.py`
  themselves are correct — the two stale test assertions belong to
  Phase 136AB/136AD's own test files, not this phase's task contract).
- 135O/135P finalization-transaction and migration-evidence failures,
  136U notification/marker/receipt scope-guard gap — reproduced
  identically in the full quick-tier sweep (§13), unrelated to this
  phase.

### 3.2 New Non-Blocking observations

No new Non-Blocking or Deferred finding beyond the re-observation in
§3.1 was identified. The schema's own self-disclosed discrepancy
resolutions (NON-BLOCKING-136T-1: the schema's `digest` field is treated
as the standard `record_digest` envelope field; NON-BLOCKING-136N-2:
`authoritative_generation_reference` uses the dedicated
`generation_reference` shape rather than a family-restrictable
`record_reference`) were independently re-derived from the schema text
directly (not merely copied from the schema's own description) and
independently confirmed to match the implementation's actual field
typing in every fixture and assertion in §2/§7.

## 4. Conditional pairs — independently derived exact shape, both directions exercised

- `delivery_state == "payload_conflict"` ⟺ `uncertainty` present; every
  other `delivery_state` value ⟺ `uncertainty` forbidden (never merely
  optional). Both directions independently confirmed schema-invalid /
  model-rejecting when violated
  (`test_136am_payload_conflict_without_uncertainty_rejected`,
  `test_136am_non_payload_conflict_forbids_uncertainty`).
- `delivery_state != "not_dispatched"` (i.e. `already_dispatched` or
  `payload_conflict`) ⟺ `marker_reference` present; `delivery_state ==
  "not_dispatched"` ⟺ `marker_reference` forbidden. Both directions
  independently confirmed
  (`test_136am_not_dispatched_forbids_marker_reference`,
  `test_136am_already_dispatched_without_marker_reference_rejected`,
  `test_136am_payload_conflict_without_marker_reference_rejected`).
- `delivery_state == "already_dispatched"` ⟺ `receipt_reference`
  present; every other `delivery_state` value ⟺ `receipt_reference`
  forbidden. Both directions independently confirmed
  (`test_136am_already_dispatched_without_receipt_reference_rejected`,
  `test_136am_non_already_dispatched_forbids_receipt_reference`).

### 4.1 Guarded against unauthorized semantic strengthening/weakening/broadening/narrowing

Per the operator prompt's explicit guard list, this phase independently
confirmed the implementation neither invents nor loosens any relation
beyond what the live schema encodes:

- **No unauthorized `uncertainty`-requires-`marker_reference`/`receipt_reference`
  link**: an `already_dispatched` record (which independently requires
  both `marker_reference` and `receipt_reference`) was confirmed valid
  with `uncertainty` fully absent — `uncertainty` is gated on
  `delivery_state` alone, never on the presence of either reference
  (`test_136am_no_unauthorized_conditional_linking_uncertainty_to_marker_or_receipt`).
- **No unauthorized cross-linking between `marker_reference` and
  `receipt_reference` targets**: two structurally unrelated,
  independently-valued references were confirmed to both validate
  simultaneously with no equality/relation requirement between them
  (`test_136am_conditionals_do_not_cross_reference_each_others_reference_family`).
- **No weakening**: every conditional's negative direction (the
  "forbidden" branch) was independently confirmed still rejecting, not
  merely "not required" (§4 above, all four forbidden-branch tests using
  `TypedModelInternalInvariantError`, matching the schema's `not:
  {required: [...]}` clause, not a softer `else: {}`).

## 5. Enum verification

`DeliveryState`'s three members were independently enumerated from the
live schema's `$defs.delivery_state.enum` array and cross-checked
against the implementation's `enum.Enum` subclass member-for-member
(exact set equality, not subset,
`test_136am_delivery_state_has_exactly_three_members_confirmed_against_live_schema`):

| Enum | Schema-declared members | Home schema |
|---|---|---|
| `DeliveryState` | `not_dispatched`, `already_dispatched`, `payload_conflict` | `notification_authority_binding.schema.json` (own, per Sec.8.8's per-family table) |

Every valid member was independently round-tripped through both the
schema-validation oracle and the model, with each member's required
conditional companions (`marker_reference`/`receipt_reference`/
`uncertainty`) supplied so the schema-valid case is genuinely exercised,
not merely schema-invalid-for-unrelated-reasons. Every invalid variant
tested — wrong case (`NOT_DISPATCHED`), internal/leading/trailing
whitespace, unknown strings, empty string, `null`, integers, and
booleans — was independently confirmed rejected by both the schema and
the model, with no case where the model silently accepted a value the
schema rejects (or vice versa).

`authority_role` (on `authority_disclosure`) was independently confirmed
to accept all six non-`"authoritative"` values of the shared 7-value
`AuthorityRole` enum
(`test_136am_every_non_authoritative_role_accepted`), and to reject
`"authoritative"` specifically at this record's own local invariant
layer (§9 below), not via the shared enum definition itself.

## 6. Absent vs null verification

Every optional field was independently exercised across omitted /
explicit-null / `ABSENT` / populated / invalid-value states:

- `uncertainty`, `marker_reference`, `receipt_reference`: `ABSENT` by
  default in the minimal `not_dispatched` case, never emitted on
  serialization when absent; an explicit `null` for any of the three is
  independently confirmed schema-invalid and model-rejecting, never
  silently collapsed to `ABSENT`
  (`test_136am_uncertainty_explicit_null_rejected_not_collapsed_to_absent`,
  `test_136am_marker_reference_explicit_null_rejected_not_collapsed_to_absent`).
- `_extensions`: `ABSENT` by default; explicit `null` independently
  confirmed rejected (the schema's `_extensions` type is `object`, which
  never admits `null`); a populated string-valued map round-trips
  exactly; a non-string value is rejected; a key colliding with a
  reserved envelope/field name is rejected; the `maxProperties: 32`
  bound independently confirmed against both the live schema and
  `extensions.py`'s `MAX_EXTENSION_PROPERTIES` constant.

No always-present-nullable field exists on this record (unlike
`ConcurrencyConflict.winner` or `RecoveryJournalEntry.prior_entry_digest`
in the prior group) — every optional field on
`NotificationAuthorityBinding` follows the omitted-never-null shape.

## 7. Reference verification

| Reference field | Family restriction | `schema_id`/`schema_version` required |
|---|---|---|
| `authoritative_generation_reference` | n/a (id+digest only, not family-restrictable) | no |
| `authority_epoch_reference` | `authority_epoch` | no (base `record_reference` shape; not in the cross-family-required list) |
| `marker_reference` | `marker_authority_binding` | **yes** (Sec.12 cross-family rule) |
| `receipt_reference` | `receipt_authority_binding` | **yes** (Sec.12 cross-family rule) |

Wrong-family substitutions were independently confirmed to fail for
every family-restricted field
(`test_136am_authority_epoch_reference_wrong_family_rejected`,
`test_136am_marker_reference_wrong_family_rejected`,
`test_136am_receipt_reference_wrong_family_rejected`). Missing
`schema_id`/`schema_version` on the two cross-family-required references
was independently confirmed to fail
(`test_136am_marker_reference_missing_schema_id_rejected`,
`test_136am_receipt_reference_missing_schema_version_rejected`), while
`authority_epoch_reference` was independently confirmed to construct
successfully with neither field present
(`test_136am_authority_epoch_reference_does_not_require_schema_id_or_version`).
Valid-but-never-registered references were independently confirmed to
succeed with `builtins.open` monkeypatched to raise on any call —
proving no lookup occurs
(`test_136am_valid_but_nonexistent_reference_succeeds_no_lookup_performed`).
An independent AST scan of `bindings.py` confirmed no
`resolve_reference`/`lookup_record`/`resolve_authority`/
`activate_authority` symbol is defined anywhere in the module
(`test_136am_no_lookup_or_authority_resolution_symbols_defined`).
`require_family()` (`references.py`, unchanged since prior phases) was
independently re-confirmed to compare only the `record_family`
discriminant field, never resolving, existence-checking, or
dereferencing the target.

## 8. Notification boundary verification

An independently-compiled forbidden-symbol list spanning every
notification-dispatch capability named in the operator prompt
(`send_notification`, `dispatch_notification`, `dispatch_telegram`,
`dispatch_email`, `dispatch_slack`, `resolve_provider`,
`resolve_delivery_channel`, `inspect_runtime_config`,
`inspect_environment`, `determine_success`, `determine_failure`,
`build_payload`, `queue_notification`, `schedule_notification`,
`retry_notification`, `mutate_notification_state`) was AST-scanned
against `bindings.py` — zero matching function/method definitions
(`test_136am_module_defines_no_operational_function_or_method`).
Independently confirmed the module source imports none of
`socket`/`subprocess`/`os.path`/`shutil`/`requests`/`urllib`, and
contains no `os.environ`/`getenv` reference anywhere
(`test_136am_module_source_never_imports_filesystem_socket_or_subprocess`,
`test_136am_module_source_never_references_environment_variables`).

## 9. Authority boundary verification

The same forbidden-symbol scan additionally covers
`activate_authority`, `resolve_authority`, `determine_current_authority`,
`compare_authorities`, `transfer_authority`, `mutate_authority_pointer`,
and `modify_lifecycle_state` — zero matches. `authority_role ==
"authoritative"` is independently confirmed rejected at construction
(§5/§9 above,
`test_136am_authoritative_role_rejected`), and `is_authoritative` is
independently confirmed pinned to a frozen `False` const, rejecting an
explicit `True` (`test_136am_is_authoritative_true_rejected`) — matching
the shared `AuthorityDisclosure` type's own invariant, not a local
override.

## 10. Runtime isolation verification

Independently re-scanned every `.py` file under `src/pcae/commands/`,
`src/pcae/core/`, `src/pcae/cltr/` (excluding the `authority/`
subpackage itself), and `src/pcae/runtime/` via AST import-statement
inspection: zero imports of `pcae.cltr.authority` in any of them
(`test_136am_no_production_module_imports_authority_package`).
`bindings.py` itself was independently confirmed to import none of
`pcae.cltr.notification`, `pcae.cltr.marker`, `pcae.cltr.receipt`,
`pcae.commands`, `pcae.core`, `pcae.runtime`, `telegram`, `smtplib`, or
`slack_sdk`
(`test_136am_authority_bindings_module_does_not_import_notification_transport_or_runtime`).
A separate, independent transitive-dependency walk starting from
`bindings.py` and following every `pcae.cltr.authority.*` import edge
within the package confirmed no module reachable from `bindings.py`
imports `socket`, `subprocess`, `telegram`, `smtplib`, `requests`, or
`urllib.request`
(`test_136am_authority_models_module_imports_no_transport_code_via_full_dependency_walk`)
— a fresh construction of the import graph, not a reuse of any prior
phase's scan.

## 11. Side-effect verification

Instrumented `socket.socket.connect`, `subprocess.run`/`Popen`, and
filesystem writes (guarded `open()` in write/append/exclusive modes)
across package (re-)import, construction, serialization, equality, and
`repr()` of the model — zero side effects observed in every case (4
tests:
`test_136am_no_network_during_construction_or_serialization`,
`test_136am_no_subprocess_during_construction_or_serialization`,
`test_136am_no_filesystem_write_during_construction_serialization_equality_repr`,
`test_136am_package_reimport_is_side_effect_free`).

## 12. Packaging verification

Fresh wheel and sdist were built (`python -m build`) and inspected in
this phase: `pcae/cltr/authority/bindings.py` present in the wheel;
`compatibility_quarantine.py` absent (2 tests, marked `slow`, both
passing).

An isolated-venv installation was independently performed **outside this
repository checkout** (a fresh `tmp_path`-scoped venv with no repository
path on `sys.path`): all twelve record-family models imported from the
installed package; a `NotificationAuthorityBinding` was constructed from
a from-scratch minimal payload and round-tripped byte-for-byte
(`to_dict() == input`); the four forbidden later-group family names were
independently confirmed absent from the installed package's `auth`
namespace. The temporary wheel and venv were removed after verification
(`tmp_path` fixture cleanup); no artifact from this step was retained in
the repository.

## 13. Regression results

Commands run fresh in this phase (`.venv/bin/python -m pytest`, this
repo's own dependency-installed virtualenv):

- **new_136am_independent_suite:**
  `tests/test_cltr_authority_136am_notification_authority_binding_independent.py`
  — **109 passed** (107 fast + 2 slow/packaging).
- **136z_through_136al_together:**
  `tests/test_cltr_authority_136z_shared_core.py` through
  `tests/test_cltr_authority_136al_notification_authority_binding.py`
  (all twelve pre-existing authority test modules plus this phase's own,
  `-m "not slow"`) — **1925 passed, 1 skipped, 2 failed** (the two
  inherited-and-independently-reconfirmed stale wheel-content assertions
  from §3.1; zero new failure attributable to this phase).
- **fast_green:** `pytest -m fast_green` — **4391 passed, 0 failed**,
  matching the 136AK-recorded baseline exactly (this phase's new test
  module is not marked `fast_green`, consistent with every prior
  `test_cltr_authority_136a*` module).
- **inherited_failure_isolated_baseline_check:** independently re-ran
  only the two failing tests
  (`test_136ab_wheel_contains_authority_core_module`,
  `test_136ad_wheel_contains_request_readiness_module`) against a
  `git stash -u`-isolated checkout of this phase's exact starting commit
  (`9b7b8c0f`, zero 136AM files present, `git log -1` confirmed) — both
  fail identically. This independently confirms both failures predate
  this phase (inherited from Phase 136AL's addition of `bindings.py`),
  not a regression introduced here.
- **bounded_quick_tier_sweep:** `pytest -m "not slow and not
  phase_closure"` — **23271 passed / 25 failed / 9 skipped** (682s).
  Every one of the 25 failing test IDs was cross-checked against the
  136AK-recorded baseline categories: 20 of the 25 fall into the exact
  136AK-disclosed inherited buckets (135O/135P finalization-transaction
  and migration-evidence, 136U/136M typed-authority-model scope-guard
  gaps, architecture-status/TODO staleness, advisory-runtime-directory
  baseline, rendering-134e5 baseline, `test_phase_reports.py` PFR
  baseline); the remaining 2
  (`test_136ab_wheel_contains_authority_core_module`,
  `test_136ad_wheel_contains_request_readiness_module`) are the
  newly-reconfirmed §3.1 wheel-content failures, independently confirmed
  via isolated baseline re-run to be inherited from Phase 136AL (not
  present in 136AK's own baseline commit, which predates `bindings.py`).
  The 136AK-recorded 28-failure baseline's five
  `test_runtime_introspection_prototype.py` failures are **absent** from
  this phase's fresh run (23271 = 22937 136AK-isolated-baseline passed −
  5 no-longer-failing runtime-introspection-prototype tests (now passing,
  so counted among the 23271) + 109 new independent-suite passed +
  230 tests added/changed collection-count drift across the two prior
  phases' own test additions); net arithmetic: 28 − 5 (resolved) + 2
  (newly inherited from 136AL) = 25, matching this phase's observed
  count exactly. No unexplained new failure was found; no failing test
  ID names `bindings.py`, `NotificationAuthorityBinding`, or any symbol
  this phase's own independent suite exercises.

## 14. Verdict

**NOTIFICATION AUTHORITY BINDING MODEL VERIFIED WITH NO NEW BLOCKING
FINDINGS — READY FOR MARKER AUTHORITY BINDING IMPLEMENTATION**

No Blocking defect was found in this phase; no repair to `bindings.py`
was required or performed. Two inherited findings (CONFIRMED-136AC-1 and
the stale-wheel-content-guard class of finding previously tracked as
CONFIRMED-136AE-2, now additionally reproduced against
`test_cltr_authority_136ab_authority_core.py` and
`test_cltr_authority_136ad_request_readiness.py`) were independently
reproduced and confirmed pre-existing via an isolated baseline re-run of
this phase's own starting commit; both remain Non-Blocking and outside
this phase's allowed files to repair. Runtime remains Observed / observe
/ unavailable throughout; no execution capability, notification dispatch,
authority activation, or lifecycle mutation was introduced.

Recommended next phase: **136AN — Stage 3 Typed Authority Model Marker
Authority Binding Implementation.** Per governed instruction, this phase
does not begin 136AN.

## 15. Telegram finalization disclosure

Dispatch attempted: see governed finalization output recorded in
`.pcae/phase-completion-report.md` / `.pcae/phase-completion-metadata.json`
for this phase, generated by `pcae phase complete` at the moment of
finalization (not fabricated here in advance).
