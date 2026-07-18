# Phase 136AS: Stage 3 Typed Authority Model CompatibilityState Independent Verification

## 1. Purpose and methodology

Phase 136AS independently verifies the Phase 136AR (canonical implementation
commit `11f7d37c1ad1d5daa8e6e4a54d06005a50fbbfce`, finalized in `64f50812`)
implementation of `CompatibilityState`
(`src/pcae/cltr/authority/compatibility_quarantine.py`) -- Typed Model
Implementation Group 10, the tenth companion-record group in the frozen
136Y plan.

Per governed instruction, this phase did **not** trust Phase 136AR's own
field tables, fixtures, tests
(`tests/test_cltr_authority_136ar_compatibility_state.py`), helper
functions, comments, decisions, canonical report, or the name
"CompatibilityState". The record contract was independently re-derived
directly from:

- the live executable schema `records/compatibility_state.schema.json`;
- the shared component schemas it composes (`shared/enums.schema.json`,
  `shared/limitations.schema.json`, `shared/envelope.schema.json`,
  `shared/identity.schema.json`, `shared/digest.schema.json`);
- the frozen contract text quoted in the schema's own `description` fields
  (CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Sec.34, Sec.46, plus Sec.8.2,
  Sec.8.7, Sec.9, Sec.16);
- the previously verified typed-model foundation (`enums.py`, `digest.py`,
  `identity.py`, `envelope.py`, `limitations.py`, `sentinels.py`,
  `errors.py`, `extensions.py`, `opaque.py`, `serialization.py`) for
  cross-family precedent.

A new, independently fixtured test module,
`tests/test_cltr_authority_136as_compatibility_state_independent.py`, was
written from scratch: every wire fixture (`_wire`, `_retired_wire`,
`_disclosure`, and the independently re-derived `ROLE_MEMBERS`,
`COMPATIBILITY_MODE_MEMBERS`, `AUTHORITY_ROLE_MEMBERS`, `REQUIRED_FIELDS`
tuples) was built directly from the live schema's field table and `$defs`,
not copied from the 136AR implementation suite. The only 136AR-adjacent
infrastructure reused is the shared, non-136AR-owned `pcae.schema_runtime`
offline schema-validation registry -- the same live schema file 136AR
itself validates against, used here as an independent oracle for every
adversarial payload (`_assert_schema_valid` / `_assert_schema_invalid`),
not as a source of expected values.

188 tests were written (186 fast + 2 packaging/slow), **all passing with no
production change**. The decisive independence check is an exhaustive
schema-vs-model parity sweep (§4): for every combination of `mode` ×
`authority_role` × `retirement_state`-presence/shape (126 combinations),
the Python model's accept/reject decision was confirmed to exactly equal
the live executable schema's decision.

## 2. Independently re-derived field table

### `CompatibilityState` (`records/compatibility_state.schema.json`)

| Field | Wire type | Required | Null | ABSENT | Typed wrapper | Local invariant |
|---|---|---|---|---|---|---|
| `schema_id` | string (const) | yes | no | no | `RecordEnvelope.schema_id` | must equal the frozen schema URL `.../compatibility_state.schema.json` |
| `schema_version` | string `MAJOR.MINOR` | yes | no | no | `SchemaVersionString` | pattern `^[0-9]+\.[0-9]+$`; only `"1.0"` supported by the model |
| `contract_version` | string (const `"1.0"`) | yes | no | no | `RecordEnvelope.contract_version` | must equal `"1.0"` |
| `record_type` | string (const) | yes | no | no | `RecordEnvelope.record_type` | must equal `"compatibility_state"` |
| `record_id` | string (record_identity) | yes | no | no | `RecordId` | pattern `^[a-z][a-z0-9-]{7,127}$` |
| `record_digest` | string (sha256_hex) | yes | no | no | `RecordDigest` | 64-hex-lowercase; restates Sec.34's `digest` field (NON-BLOCKING-136V-1 pattern) |
| `created_at` | string (timestamp) | yes | no | no | `Timestamp` | RFC3339 `Z`-suffix only; **shape only**, never calendar validity |
| `migration_epoch` | string | yes | no | no | `MigrationEpochToken` | pattern-bound opaque token; required despite the cross-phase family exemption from `phase_id`/`transition_id` (NON-BLOCKING-136V-1) |
| `component` | string | yes | no | no | `str` | `minLength 1`, `maxLength 256`, pattern `^[\x20-\x7E]*$` (printable ASCII) (NON-BLOCKING-136V-4) |
| `role` | enum (2, local) | yes | no | no | `CompatibilityRole` | `{compatibility, historical}`; distinct from `authority_disclosure.authority_role` (NON-BLOCKING-136V-2) |
| `allowed_reads` | array of strings | yes | no | no | `tuple[str, ...]` | `maxItems 64`; each entry `minLength 1`, `maxLength 512`, forbids literal `..` and C0/C1 control chars; may be empty (NON-BLOCKING-136V-4) |
| `forbidden_authority_use` | boolean (const `true`) | yes | no | no | `bool` (frozen `True`) | schema-pinned `true`; the model rejects any other value and re-checks in `__post_init__` |
| `fallback_disabled` | boolean | yes | no | no | `bool` | free boolean; no coupling to `mode`/`role` invented |
| `mode` | enum (6, shared) | yes | no | no | `CompatibilityMode` | `{legacy_authoritative, legacy_adapter, legacy_read_only, legacy_historical, legacy_disabled, legacy_retired}` |
| `retirement_state` | object, empty-shape placeholder only | conditional | no (schema type is `object`, never nullable) | yes | `OpaqueJsonValue \| AbsentType` | DEFERRED-136V-1: `additionalProperties: false`, no `properties` -- only `{}` is schema-valid; **required iff `mode == legacy_retired`, forbidden otherwise** |
| `limitations` | array of strings | yes | no | no | `Limitations` | may be empty |
| `authority_disclosure` | object | yes | no | no | `AuthorityDisclosure` | `authority_role != "authoritative"` locally forbidden (Sec.9's 12-file list); `is_authoritative` const `false`; further restricted to `{historical, compatibility}` when `mode ∈ {legacy_historical, legacy_disabled, legacy_retired}` (Sec.16, NON-BLOCKING-136V-3) |
| `_extensions` | object, string-valued | no | no | yes | `ExtensionMapping` | Tier 2, ≤32 keys, string values only; explicit `null` rejected by the model |

Independently confirmed: `additionalProperties: false` at the top level
(unknown-key rejection, 18 declared properties total); exactly **16**
required fields (confirmed programmatically against the live schema's own
`required` array, `test_136as_required_field_set_matches_live_schema`); no
`phase_id`/`transition_id` fields; **no reference-family field of any kind**
(§7). The schema-declared `schema_id` const and `record_type` const were
confirmed byte-equal to the module's own
`_COMPATIBILITY_STATE_SCHEMA_ID`/record-type constants.

## 3. Findings

### 3.1 BLOCKING

**None.** No Blocking defect was independently reproduced. Every field,
wrapper type, required/optional classification, both conditionals (both
directions), the local 2-value `role` enum, the shared 6-value `mode`
enum, the locally-forbidden `authoritative` `authority_role`, the
`forbidden_authority_use` const, the `retirement_state` empty-shape pin,
and the `component`/`allowed_reads` field bounds independently derived in
§2 above matched
`src/pcae/cltr/authority/compatibility_quarantine.py` exactly.

Of particular note: the `retirement_state` field is wrapped in the
general-purpose, field-agnostic `OpaqueJsonValue` type (`opaque.py`),
exactly the wrapper whose field-agnostic contract caused the Blocking
`staleness_check` weakening independently found and repaired in the
immediately-prior sibling verification phase 136AQ (DEFERRED-136T-1). The
136AR implementation **already** enforces the field-specific empty-object
restriction at the field's own construction site
(`_retirement_state_from_payload`, which rejects any non-`{}` mapping and
any non-object value **before** wrapping in `OpaqueJsonValue.from_json`),
citing DEFERRED-136V-1 and the 136AQ/DEFERRED-136T-1 precedent explicitly.
This phase independently reproduced both the schema-invalidity of a
populated/non-object `retirement_state` (via the schema oracle) and the
model's construction-time rejection of the identical payloads
(`test_136as_retirement_state_nonempty_object_rejected_by_model`,
`test_136as_retirement_state_non_object_rejected`), confirming the
DEFERRED-136T-1-class weakening is **not** present in this family. The
general-purpose `OpaqueJsonValue` contract is correctly left un-narrowed;
the restriction lives at the call site only.

### 3.2 Inherited findings re-confirmed, not re-litigated

Reproduced identically in this phase's regression run (§13 below), all
unrelated to `compatibility_quarantine.py`'s `CompatibilityState` code
path, and outside every file this phase's strict allowed-file list covers
(each was independently confirmed to reproduce with this phase's own new
test file removed from the tree, proving they are inherited, not
introduced):

- **The stale wheel-content guard class of finding** (first reconfirmed at
  136AM, re-observed through 136AQ, still present):
  `tests/test_cltr_authority_136ab_authority_core.py::test_136ab_wheel_contains_authority_core_module`
  and
  `tests/test_cltr_authority_136ad_request_readiness.py::test_136ad_wheel_contains_request_readiness_module`
  assert `authority_core.py`/`request_readiness.py` are absent from a
  freshly built wheel -- false since those modules were added in earlier
  groups. Inherited; outside this phase's allowed files to repair.
- **136M typed-authority-model scope guard**
  (`test_cltr_cutover_136m_request_and_readiness_independent_verification.py::test_136m_no_typed_authority_model_module_exists`):
  a scope guard that has been progressively narrowed group-by-group but not
  re-narrowed for Group 10; it became stale as legitimate typed-model
  families accreted. Inherited; Non-Blocking.
- **136U Group-10-reference scope guard**
  (`test_cltr_cutover_136u_notification_marker_receipt_binding_independent_verification.py::test_136u_no_runtime_code_references_group10_families_outside_schema_resources`):
  asserts no tracked source outside `schema_resources/` references a
  Group 10 family; became false the moment Phase 136AR legitimately
  implemented `CompatibilityState` (Group 10) in
  `compatibility_quarantine.py`. This is an inherited consequence of the
  136AR implementation itself, not of this verification phase; it is outside
  this phase's allowed files (that test file is not in the allowed list) and
  is Non-Blocking (a stale guard, not a real boundary breach -- §15/§16
  independently confirm `CompatibilityState` has no runtime integration).

### 3.3 New Non-Blocking observations

None beyond §3.2's re-observations. The schema's own self-disclosed
discrepancy resolutions were independently re-derived from the schema text
directly and independently confirmed to match the implementation's actual
field typing in every fixture and assertion:

- **NON-BLOCKING-136V-1**: `record_digest` restates Sec.34's `digest`;
  `migration_epoch` remains required despite the cross-phase family's
  exemption from `phase_id`/`transition_id`.
- **NON-BLOCKING-136V-2**: `role` is a bare local 2-value enum
  (`{compatibility, historical}`), a restatement of the shared 7-value
  `AuthorityRole`, distinct from `authority_disclosure.authority_role`.
- **NON-BLOCKING-136V-3**: Sec.16's compatibility-mode conditional applies
  to `authority_disclosure.authority_role` (the broader 7-value field), not
  to the local `role` field.
- **NON-BLOCKING-136V-4**: `component` and `allowed_reads` carry
  locally-decided bounds; independently confirmed neither invents an
  ordering, uniqueness, or existence requirement.

## 4. Conditionals -- independently derived exact shapes, both directions, exhaustive parity

The live schema encodes two conditionals via a top-level `allOf` with two
`if`/`then`(/`else`) blocks (independently confirmed structurally by
`test_136as_conditional_definitions_present_in_live_schema`):

1. **`mode == legacy_retired` ⟺ `retirement_state` present.** Required when
   the mode is `legacy_retired` (`then: {required: [retirement_state]}`);
   the key is **forbidden entirely** for every other mode
   (`else: {not: {required: [retirement_state]}}`) -- not merely
   null-valued. Both directions independently confirmed schema-invalid /
   model-rejecting: retired-without-retirement
   (`test_136as_retired_without_retirement_state_rejected`) and
   any-other-mode-with-retirement
   (`test_136as_non_retired_forbids_retirement_state`, parametrized over the
   five non-retired modes).
2. **`mode ∈ {legacy_historical, legacy_disabled, legacy_retired}` ⇒
   `authority_disclosure.authority_role ∈ {historical, compatibility}`.**
   A `then`-only block (no `else`): for the three *restricted* modes the
   disclosure role is narrowed; for the three *unrestricted* modes
   (`legacy_authoritative`, `legacy_adapter`, `legacy_read_only`) only the
   unconditional "not `authoritative`" rule applies. Both branches
   independently confirmed
   (`test_136as_restricted_mode_forbids_non_historical_compatibility_role`,
   `test_136as_restricted_mode_permits_historical_compatibility_role`,
   `test_136as_unrestricted_mode_permits_broader_authority_role`).

### 4.1 Exhaustive schema-vs-model conditional parity

`test_136as_exhaustive_schema_vs_model_conditional_parity` iterates all
6 modes × 7 `authority_role` values × 3 `retirement_state` states
(absent / `{}` / `{"unexpected_key": 1}`) = **126 combinations**, and
asserts the model's accept/reject decision equals the live schema oracle's
in every one. Zero mismatches: the model neither **weakens** nor
**strengthens** the executable schema on the conditional surface. A
separate field-level parity sweep over `component`, `allowed_reads`,
`_extensions`, enums, and discriminators (31 cases) likewise produced zero
mismatches.

### 4.2 Guarded against unauthorized semantic strengthening/weakening

- **`role` is independent of `authority_role`**: `role="historical"` with
  `authority_role="operational"` under an unrestricted mode is valid -- no
  cross-field coupling was invented
  (`test_136as_role_is_independent_of_authority_role`).
- **Unrestricted modes are not narrowed**: `legacy_authoritative` /
  `legacy_adapter` / `legacy_read_only` accept `derivative`/`operational`/
  `evidence`/`quarantined` disclosure roles -- the mode restriction was not
  over-broadened to all modes
  (`test_136as_unrestricted_mode_permits_broader_authority_role`).
- **No unauthorized weakening (the DEFERRED-136V-1 surface)**: a populated
  or non-object `retirement_state` is rejected by the model exactly as by
  the schema (§3.1), so the general-purpose `OpaqueJsonValue` wrapper does
  not silently weaken the field's empty-shape pin.

## 5. Enum verification

Three enum surfaces were independently enumerated from the live schema and
cross-checked against the implementation's `enum.Enum` subclasses
member-for-member (exact set equality, not subset):

| Enum | Schema-declared members | Home schema |
|---|---|---|
| `CompatibilityRole` (`role`) | `compatibility`, `historical` | `compatibility_state.schema.json` `#/$defs/compatibility_role` (own, 2-value) |
| `CompatibilityMode` (`mode`) | `legacy_authoritative`, `legacy_adapter`, `legacy_read_only`, `legacy_historical`, `legacy_disabled`, `legacy_retired` | `shared/enums.schema.json` `#/$defs/compatibility_mode` (Sec.8.7, 6-value) |
| `AuthorityRole` (`authority_disclosure.authority_role`) | 7 values, `authoritative` locally forbidden here | `shared/enums.schema.json` `#/$defs/authority_role` (Sec.8.2) |

Every valid member of `role` and `mode` was independently round-tripped
through both the schema oracle and the model (with conditional companion
fields supplied where required). Every invalid variant -- wrong case
(`Compatibility`, `COMPATIBILITY`, `Legacy_Adapter`), leading/trailing
whitespace, unknown strings, empty string, `null`, integers, booleans --
was independently confirmed rejected by both. The two-value `role` enum was
confirmed to reject the five `AuthorityRole` members it does **not** share
(`operational`, `authoritative`, `derivative`, `evidence`, `quarantined`),
independently proving it is a genuine 2-value restatement and not an alias
of the broader shared enum.

`authority_role == "authoritative"` was independently confirmed rejected at
the record's own local invariant layer
(`test_136as_authority_role_authoritative_locally_forbidden`), and
`is_authoritative` was confirmed pinned to a frozen `False`, rejecting an
explicit `True` (`test_136as_is_authoritative_true_rejected`).

## 6. Absent vs null verification

- `retirement_state`: `ABSENT` by default under any non-retired mode, never
  emitted on serialization when absent; when present it must be exactly `{}`
  (§3.1); explicit `null` is rejected by the schema's plain `object` type
  and by the model's `_require_mapping`.
- `_extensions`: `ABSENT` by default; explicit `null` independently
  confirmed rejected; a populated string-valued map round-trips exactly; a
  non-string value is rejected; a reserved-key collision is rejected; the
  `maxProperties: 32` bound independently confirmed against both the live
  schema and the model.

## 7. Reference verification (absence confirmed)

`CompatibilityState` has **no** reference-family field of its own -- no
`record_reference`, `generation_reference`, `epoch_reference`,
`publication_evidence_reference`, `marker_reference`, `record_family`, or
any nested `schema_id`/`schema_version`-pinned reference object. This was
independently confirmed two ways: (a) the live schema's `properties` object
declares none of those keys and the serialized schema contains no
`references.schema.json` `$ref`
(`test_136as_no_reference_family_fields_present`); (b) no dataclass field
name on `CompatibilityState` contains "reference"
(`test_136as_model_defines_no_reference_wrapper_fields`). No reference
wrapper was silently added or omitted.

## 8. Field-specific shape verification (`retirement_state`, `component`, `allowed_reads`)

- **`retirement_state`** (DEFERRED-136V-1, the field this phase focuses on
  most closely, given the `OpaqueJsonValue` wrapper precedent): schema pins
  to `type: object`, `additionalProperties: false`, no `properties` -- only
  `{}` is schema-valid. Independently confirmed empty-object accepted;
  any-key-present rejected; non-object rejected -- by both the schema oracle
  and the model at its own construction boundary
  (`test_136as_retirement_state_*`).
- **`component`**: `minLength 1` / `maxLength 256` / printable-ASCII pattern
  independently confirmed at each boundary (empty, 256, 257, non-ASCII,
  tab/newline control chars) against both schema and model
  (`test_136as_component_boundaries`).
- **`allowed_reads`**: `maxItems 64`; entry `minLength 1` / `maxLength 512`;
  literal `..` and C0/C1 control chars forbidden. Independently confirmed at
  each boundary (1 entry, 512-char entry, 64 entries, 65 entries, 513-char
  entry, empty entry, `../escape`, mid-string `path/../x`, `\x00`, `\x7f`)
  against both schema and model (`test_136as_allowed_reads_boundaries`).

## 9. Anti-strengthening verification

The following reasonable-sounding compatibility assumptions were
independently confirmed **not** enforced by the schema or the model (a
syntactically valid but semantically unusual payload must be accepted):

- the named `component` need not exist or be installed
  (`test_136as_component_need_not_exist_or_be_installed`);
- an `allowed_reads` path need not actually be readable
  (`test_136as_allowed_reads_need_not_actually_be_readable`);
- `fallback_disabled: true` imposes no other requirement
  (`test_136as_fallback_disabled_true_does_not_require_any_other_field`);
- `legacy_*` does not imply retired/disabled/deprecated -- a
  `legacy_authoritative` document with an `operational` disclosure is valid
  (`test_136as_legacy_does_not_imply_retired_or_disabled`);
- a calendar-invalid but shape-valid timestamp (`2026-13-45T99:99:99Z`) is
  accepted -- the timestamp definition validates shape only, never calendar
  semantics (`test_136as_calendar_invalid_but_shape_valid_timestamp_accepted`);
- duplicate `allowed_reads` / `limitations` entries are accepted (no
  `uniqueItems` constraint invented)
  (`test_136as_duplicate_allowed_reads_entries_accepted`,
  `test_136as_duplicate_limitations_entries_accepted`).

## 10. Compatibility, quarantine and authority boundary verification

An independently-compiled forbidden-symbol list spanning every
compatibility-engine, quarantine, and authority-exercise capability named
in the operator prompt (`determine_compatibility`, `calculate_compatibility`,
`infer_compatibility`, `compare_versions`, `negotiate_version`,
`select_version`, `is_compatible`, `resolve_compatibility`, `reconcile`,
`resolve_conflict`, `select_fallback`, `plan_migration`,
`execute_migration`, `convert_schema`, `convert_record`, `transform_record`,
`activate_mode`, `disable_mode`, `determine_upgrade_readiness`,
`determine_downgrade_readiness`, `authorize_cutover`, `block_cutover`,
`inspect_installed_packages`, `inspect_dependencies`, `inspect_repository`,
`inspect_git`, `discover_schemas`, `quarantine`, `isolate_record`,
`classify_record`, `release_record`, `delete_record`, `move_record`,
`evaluate_eligibility`, `write_marker`, `reconcile_quarantine`,
`activate_authority`, `resolve_authority`, `determine_current_authority`,
`compare_authorities`, `transfer_authority`, `mutate_authority_pointer`,
`demote_authority`, `finalize_lifecycle`, `advance_lifecycle_state`,
`authorize_publication`) was AST-scanned against
`compatibility_quarantine.py` -- **zero matching function/method
definitions**
(`test_136as_module_defines_no_engine_quarantine_or_authority_exercise_symbols`).
The model's entire public method surface was independently confirmed to be
exactly `{from_dict, to_dict}` -- representation only, no engine, decision,
activation, or mutation method
(`test_136as_module_public_api_is_representation_only`).

## 11. Quarantine-boundary / QuarantineRecord absence

Despite the filename `compatibility_quarantine.py`, no `QuarantineRecord`
class or function is **defined**, exported (`__all__` is exactly
`{CompatibilityRole, CompatibilityState}`), or importable
(`test_136as_no_quarantine_record_definition_anywhere_in_module`,
`test_136as_module_all_exports_exactly_role_enum_and_state_model`). The
`quarantine_record` slug legitimately remains in the frozen shared
`record_family` nomenclature enum (it is a closed-vocabulary name, not an
implemented class); this phase independently confirmed the slug persists
while the class does not
(`test_136as_no_scope_guard_permits_quarantine_record_family_slug`). Across
the whole authority package, exactly **fifteen** record-family model classes
exist (AST + runtime-export + isolated-install), with `QuarantineRecord`
absent from all three
(`test_136as_exactly_fifteen_record_family_classes_exist_via_ast`,
`test_136as_package_export_inventory_via_runtime_import`,
`test_136as_isolated_install_all_fifteen_families_import_and_round_trip`).

## 12. Scope-guard integrity

The 136AR implementation reportedly narrowed sixteen earlier chapter scope
guards to admit the now-legitimate Group 10 family. This phase
independently inspected the immediately-prior sibling verification suite's
forbidden-family list
(`test_136as_sibling_136aq_scope_guard_still_forbids_quarantine_record`):
its `*_MUST_NOT_EXIST_*` tuple still contains `QuarantineRecord` and
contains **none** of the fifteen implemented families -- i.e. it was
narrowly updated (dropping `CompatibilityState` from the forbidden list)
without being over-broadened to bar an implemented family or narrowed to
drop `QuarantineRecord`. Classification: **necessary-and-narrowly-updated**.
The two stale guards in §3.2 (136M/136U) that were **not** re-narrowed for
Group 10 are classified **unnecessary-but-Non-Blocking** (stale assertions,
not boundary breaches; §16 independently confirms no real boundary is
crossed). No scope guard was found that now permits `QuarantineRecord` or
arbitrary later-group records.

## 13. Regression results

Commands run fresh in this phase (`.venv` interpreter, this repo's own
dependency-installed virtualenv):

- **new_136as_independent_suite:**
  `tests/test_cltr_authority_136as_compatibility_state_independent.py` --
  **188 passed** (186 fast + 2 slow/packaging), 0 failed. No production
  change was required to make any test pass.
- **136ar + 136aq focused suites:**
  `test_cltr_authority_136ar_compatibility_state.py` +
  `test_cltr_authority_136aq_finalization_receipt_authority_binding_independent.py`,
  `-m "not slow"` -- **222 passed**, 5 deselected, 0 failed.
- **all `cltr_authority_136*` + `cltr_cutover_136*` modules:** `-m "not
  slow"` -- **4456 passed, 9 skipped, 4 failed**. The four failures are the
  inherited-and-independently-reconfirmed §3.2 stale guards
  (`test_136ab_wheel_contains_authority_core_module`,
  `test_136ad_wheel_contains_request_readiness_module`,
  `test_136m_no_typed_authority_model_module_exists`,
  `test_136u_no_runtime_code_references_group10_families_outside_schema_resources`).
  Each was independently confirmed to reproduce identically **with this
  phase's own new test file removed from the tree**, proving they are
  inherited, not introduced. Zero new failure attributable to this phase.
- **fast_green:** `pytest -m fast_green -n auto` -- **4391 passed, 0
  failed**, matching the 136AQ-recorded baseline exactly (this phase's new
  independent test module is not marked `fast_green`, consistent with every
  prior `test_cltr_authority_136a*` independent module).
- **packaging_verification:** fresh wheel build + isolated venv install
  (`test_136as_wheel_build_contains_group_10_module_and_no_quarantine`,
  `test_136as_isolated_install_all_fifteen_families_import_and_round_trip`)
  -- both pass; the wheel contains `compatibility_quarantine.py`; the
  isolated install exposes exactly the fifteen expected record families and
  excludes `QuarantineRecord`.

## 14. Immutability, equality, and determinism verification

`CompatibilityState` is independently confirmed a frozen dataclass;
mutating a source `list`/`dict` (the `allowed_reads` list, the `limitations`
list, the `_extensions` mapping, the `authority_disclosure` dict) after
construction never affects the already-constructed model; mutating the
`to_dict()` output (its `allowed_reads` list, its `_extensions` dict, or any
scalar) never affects the model -- `to_dict()` returns fresh containers, not
aliases into frozen internals. `copy.deepcopy` produces a structurally-equal
but non-identical object.

Equality was independently confirmed structural, not identifier-only or
digest-only: two records sharing `record_id`/`record_digest` but differing
`mode` are unequal; changing any one of nine fields (`role`, `mode`,
`component`, `fallback_disabled`, `allowed_reads`, `migration_epoch`,
`limitations`, `authority_disclosure`, `_extensions`) yields inequality.
Round-trip is deterministic and lossless (`from_dict → to_dict → from_dict`
is byte-stable); construction errors are deterministic across repeated
attempts.

## 15. Runtime isolation and side-effect verification

Independently re-scanned every `.py` file under `src/pcae/commands/`,
`src/pcae/core/`, `src/pcae/cltr/` (excluding the `authority/` subpackage),
and `src/pcae/runtime/` via AST import-statement inspection: zero imports of
`pcae.cltr.authority` in any of them
(`test_136as_no_production_module_imports_authority_package`).
`compatibility_quarantine.py` itself imports none of `socket`,
`subprocess`, `shutil`, `requests`, `urllib`, `smtplib`, `telegram`,
`slack_sdk`, `os`, `pathlib`, `pcae.commands`, `pcae.core`, `pcae.runtime`,
`pcae.cltr.notification`, or `pcae.cltr.marker`, and contains no
`os.environ`/`getenv`/`subprocess`/`socket`/`git` reference. A separate,
independent transitive-dependency walk from `compatibility_quarantine.py`
through every `pcae.cltr.authority.*` import edge confirmed no reachable
module imports a transport/filesystem dependency -- a fresh construction of
the import graph, not a reuse of any prior phase's scan.

Side effects were instrumented across module (re-)import, construction,
serialization, equality, and `repr()`: `socket.socket.connect`,
`subprocess.run`/`Popen` monkeypatched to raise, and `open()` guarded to
raise on any access -- **zero side effects observed** in every case.
`CompatibilityState` has no runtime integration whatsoever.

## 16. No-Go confirmations

- `QuarantineRecord` not implemented; no quarantine capability introduced
  anywhere in `compatibility_quarantine.py` (§10, §11).
- No compatibility engine/resolver, version negotiation, migration
  execution, record transformation/schema conversion, runtime compatibility
  decision, artifact inspection, or reference lookup introduced (§10).
- No authority activation/transfer, legacy authority demotion, CLTR
  authority activation, lifecycle mutation, or publication authorization
  introduced (§10, §15).
- No execution capability of any kind: import, construction, serialization,
  deserialization, equality, and `repr()` all independently confirmed
  side-effect-free (§15).
- Runtime remains Observed / observe / unavailable: this phase made no
  production change and never touches `pcae.runtime`; the isolation scan
  (§15) independently confirms `compatibility_quarantine.py` is unreachable
  from and does not reach any runtime-execution module.

## 17. Recommendation

No Blocking finding was independently reproduced; **no production change was
made** (`compatibility_quarantine.py` is unmodified). The Phase 136AR
implementation of `CompatibilityState` is independently verified to be a
faithful, exact realization of the live executable schema -- neither
weakening nor strengthening it on any field, enum, conditional, boundary,
or wrapper surface.

Recommended next phase: **136AT -- Stage 3 Typed Authority Model
QuarantineRecord Implementation.** Per governed instruction, Phase 136AT was
**not** begun in this phase.
