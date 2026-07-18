# Phase 136AO: Stage 3 Typed Authority Model Marker Authority Binding Independent Verification

## 1. Purpose and methodology

Phase 136AO independently verifies the Phase 136AN (commit `f95f5044`)
implementation of `MarkerAuthorityBinding`
(`src/pcae/cltr/authority/bindings.py`) — Typed Model Implementation
Group 8, the eighth companion-record group in the frozen 136Y plan.

Per governed instruction, this phase did **not** trust Phase 136AN's own
field tables, fixtures, tests, helper functions, comments, decisions, or
prior verification reports. The record contract was independently
re-derived directly from:

- the live executable schema
  `records/marker_authority_binding.schema.json`;
- the shared component schemas it composes
  (`shared/references.schema.json`, `shared/enums.schema.json`,
  `shared/limitations.schema.json`, `shared/envelope.schema.json`,
  `shared/identity.schema.json`, `shared/digest.schema.json`);
- the frozen contract text quoted in the schema's own `description`
  fields (CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Sec.32, Sec.46);
- the previously verified typed-model foundation (`references.py`,
  `digest.py`, `identity.py`, `envelope.py`, `limitations.py`,
  `sentinels.py`, `errors.py`, `extensions.py`) for cross-family
  precedent (e.g. the `generation_reference` no-family-restriction
  precedent, the `is_authoritative` const-`false`-regardless-of-role
  precedent, the Tier 2 `_extensions` string-map precedent, the Sec.12
  cross-family schema_id/schema_version requirement already exercised on
  `marker_reference`/`receipt_reference` in the Group 7 schema).

A new, independently fixtured test module,
`tests/test_cltr_authority_136ao_marker_authority_binding_independent.py`,
was written from scratch: every wire fixture (`_mab_wire`,
`_duplicate_ref`, `_generation_ref`, and the independently re-derived
`MARKER_STATE_MEMBERS` tuple) was built directly from the live schema's
field table and `$defs`, not copied from
`tests/test_cltr_authority_136an_marker_authority_binding.py`. The only
136AN-adjacent infrastructure reused is the shared, non-136AN-owned
`pcae.schema_runtime` offline schema-validation registry — the same live
schema file 136AN itself validates against, used here as an independent
oracle for every adversarial payload (`_assert_schema_valid` /
`_assert_schema_invalid`), not as a source of expected values.

100 tests were written (98 fast + 2 packaging/slow), all passing.

## 2. Independently re-derived field table

### `MarkerAuthorityBinding` (`records/marker_authority_binding.schema.json`)

| Field | Wire type | Required | Null | ABSENT | Typed wrapper | Local invariant |
|---|---|---|---|---|---|---|
| `schema_id` | string (const) | yes | no | no | `RecordEnvelope.schema_id` | must equal the frozen schema URL |
| `schema_version` | string `MAJOR.MINOR` | yes | no | no | `SchemaVersionString` | pattern `^[0-9]+\.[0-9]+$` |
| `contract_version` | string (const `"1.0"`) | yes | no | no | `RecordEnvelope.contract_version` | must equal `"1.0"` |
| `record_type` | string (const) | yes | no | no | `RecordEnvelope.record_type` | must equal `"marker_authority_binding"` |
| `record_id` | string (record_identity) | yes | no | no | `RecordId` | pattern `^[a-z][a-z0-9-]{7,127}$` |
| `record_digest` | string (sha256_hex) | yes | no | no | `RecordDigest` | 64-hex-lowercase; restates Sec.32's `digest` field (NON-BLOCKING-136T-2, schema-disclosed) |
| `created_at` | string (timestamp) | yes | no | no | `Timestamp` | RFC3339 `Z`-suffix only |
| `migration_epoch` | string | yes | no | no | `MigrationEpochToken` | pattern-bound opaque token; not in the phase_id- or transition_id-required family lists |
| `generation_reference` | `generation_reference` (id+digest only) | yes | no | no | `GenerationReference` | not a `record_reference` — no `record_family` field exists (NON-BLOCKING-136N-2/136T-1 precedent) |
| `state` | enum (4) | yes | no | no | `MarkerState` | `absent`/`written`/`stale`/`conflict` |
| `duplicate_of` | nullable `record_reference` restricted to `marker_authority_binding` (self-family) | conditional | **conditionally permitted** | yes (forbidden entirely unless `state == conflict`) | `RecordReference \| None \| AbsentType` | required (key present) iff `state == conflict`; key forbidden entirely otherwise (not merely "must be null"); when present, nullable, and when non-null must be a self-family reference with `schema_id`/`schema_version` unconditionally required (Sec.12 cross-family rule, applied even to a same-family cross-*document* reference) |
| `compatibility_fallback_forbidden` | boolean (const `true`) | yes | no | no | `bool` (validated) | schema-pinned to `true`; documents the prohibition, not itself an operational enforcement |
| `limitations` | array of strings | yes | no | no | `Limitations` | may be empty |
| `authority_disclosure` | object | yes | no | no | `AuthorityDisclosure` | `authority_role != "authoritative"` locally forbidden (Sec.9's 12-file list) |
| `_extensions` | object, string-valued | no | no | yes | `ExtensionMapping` | Tier 2, ≤32 keys, string values only |

Independently confirmed: `additionalProperties: false` at the top level
(unknown-key rejection, 15 properties total); exactly 13 required fields
(confirmed programmatically against the live schema's own `required`
array,
`test_136ao_exactly_thirteen_required_fields_confirmed_against_live_schema`);
no `phase_id`/`transition_id` fields.

## 3. Findings

No Blocking finding was independently reproduced. Every field, wrapper
type, required/optional/nullable classification, the single
`state`/`duplicate_of` conditional (both directions, including the
distinct null-vs-absent shape), the 4-value enum vocabulary, the
self-family reference restriction, and error-behavior expectations
independently derived in §2 above matched `bindings.py` exactly,
confirmed by 100 passing tests (98 fast, 2 packaging/slow) exercising
both the live schema-validation oracle and the typed model side by side
for every case.

### 3.1 Inherited findings re-confirmed, not re-litigated

Reproduced identically in this phase's regression run (§13 below), all
unrelated to `bindings.py` and outside any file this phase touched:

- **CONFIRMED-136AC-1** (inherited, unchanged): enum construction (e.g.
  `MarkerState(...)`) raises a bare `ValueError`, not a `TypedModelError`
  subclass, on an unknown string. Still fail-closed; Non-Blocking.
- **The stale wheel-content guard class of finding, first reconfirmed at
  136AM as a re-observation of CONFIRMED-136AE-2**:
  `tests/test_cltr_authority_136ab_authority_core.py::test_136ab_wheel_contains_authority_core_module`
  and
  `tests/test_cltr_authority_136ad_request_readiness.py::test_136ad_wheel_contains_request_readiness_module`
  (neither marked `slow`, unlike every later phase's own wheel-content
  test) still assert that `bindings.py` is absent from a freshly built
  wheel — false since Phase 136AL added it, and still false now that
  Phase 136AN additionally extended it with `MarkerAuthorityBinding`.
  Independently reproduced in this phase's own fresh full-suite run
  (§13): the same two tests fail identically. This phase made no change
  to `bindings.py` or to either of the two stale test files, so the
  failure is unambiguously inherited (first introduced by Phase 136AL's
  addition of `bindings.py`, already reconfirmed by 136AM, still present
  and unrepaired at this phase's own unmodified starting commit
  `922e2b5e`); Non-Blocking; outside this phase's allowed files to
  repair (they belong to Phase 136AB/136AD's own test files, not this
  phase's task contract).
- 135O/135P finalization-transaction and migration-evidence failures,
  136U notification/marker/receipt scope-guard gap — reproduced
  identically in the full quick-tier sweep (§13), unrelated to this
  phase.

### 3.2 New Non-Blocking observations

No new Non-Blocking or Deferred finding beyond the re-observation in
§3.1 was identified. The schema's own self-disclosed discrepancy
resolutions (NON-BLOCKING-136T-2: the schema's `digest`/`created_at`/
`authority_role` fields are treated as the standard envelope/
`authority_disclosure` fields rather than a second, structurally
inconsistent representation; NON-BLOCKING-136T-3: the `limitations`
field is included even though Sec.32's own field table omits it, treated
as a table omission consistent with the other two Tier-2
binding-adjacent families) were independently re-derived from the schema
text directly (not merely copied from the schema's own description) and
independently confirmed to match the implementation's actual field
typing in every fixture and assertion in §2/§6/§7.

## 4. Conditional pairs — independently derived exact shape, both directions exercised

- `state == "conflict"` ⟺ the `duplicate_of` **key is present** (required
  when `conflict`, key forbidden entirely — not merely null-valued —
  for every other state). Both directions independently confirmed
  schema-invalid / model-rejecting when violated
  (`test_136ao_conflict_without_duplicate_of_rejected`,
  `test_136ao_non_conflict_forbids_duplicate_of_reference`,
  `test_136ao_non_conflict_forbids_duplicate_of_explicit_null`).
- When `state == "conflict"` and `duplicate_of` is present, its value is
  independently confirmed to admit **both** `null` and a
  self-family-restricted `record_reference` — the schema's own `oneOf`
  shape, not narrowed to only one of the two branches
  (`test_136ao_conflict_permits_both_null_and_reference_duplicate_of`).

### 4.1 Guarded against unauthorized semantic strengthening/weakening/broadening/narrowing

Per the operator prompt's explicit guard list, this phase independently
confirmed the implementation neither invents nor loosens any relation
beyond what the live schema encodes:

- **No unauthorized "duplicate marker identity must differ" rule**: a
  `duplicate_of` reference whose `record_id` is identical to the
  referencing record's own `record_id` was independently confirmed to
  construct and schema-validate successfully — the schema is shape-only
  and never compares a nested reference's identity against the
  document's own envelope
  (`test_136ao_no_unauthorized_semantics_duplicate_identity_may_equal_self_or_anything_shape_only`).
- **No unauthorized "duplicate target must exist" rule**: a
  syntactically valid but never-registered `duplicate_of` reference was
  independently confirmed to construct successfully with `builtins.open`
  monkeypatched to raise on any call, proving no existence lookup occurs
  (`test_136ao_valid_but_nonexistent_reference_succeeds_no_lookup_performed`).
- **No unauthorized "duplicate target must be older" or "matching
  metadata" rule**: no such comparison field, timestamp ordering check,
  or cross-document metadata equality exists anywhere in `bindings.py`
  (confirmed by the AST forbidden-symbol scan in §8/§9, which finds no
  `compare_marker_freshness` or similar comparator defined).
- **No unauthorized "conflict implies repository inconsistency" or
  "non-conflict implies marker validity" claim**: the model performs no
  interpretation of `state` beyond the bare enum value and the single
  `duplicate_of` presence/absence gate — every non-`conflict` state
  (`absent`, `written`, `stale`) independently round-trips with no
  additional required or forbidden field beyond `duplicate_of`'s own
  absence
  (`test_136ao_state_every_valid_member_accepted_with_conditionals_satisfied`).
- **No weakening**: the negative direction of the conditional (the
  "forbidden" branch) was independently confirmed still rejecting an
  explicit `null` in addition to a populated reference, not merely
  "not required" (`test_136ao_non_conflict_forbids_duplicate_of_explicit_null`,
  using `TypedModelInternalInvariantError`, matching the schema's `not:
  {required: [duplicate_of]}` clause, which forbids the key's presence
  outright, not a softer "value must be null" relaxation).

## 5. Enum verification

`MarkerState`'s four members were independently enumerated from the live
schema's `$defs.marker_state.enum` array and cross-checked against the
implementation's `enum.Enum` subclass member-for-member (exact set
equality, not subset,
`test_136ao_state_has_exactly_four_members_confirmed_against_live_schema`):

| Enum | Schema-declared members | Home schema |
|---|---|---|
| `MarkerState` | `absent`, `written`, `stale`, `conflict` | `marker_authority_binding.schema.json` (own, per Sec.8.8's per-family table) |

Every valid member was independently round-tripped through both the
schema-validation oracle and the model, with `conflict` additionally
supplying its required `duplicate_of` companion so the schema-valid case
is genuinely exercised, not merely schema-invalid for an unrelated
reason. Every invalid variant tested — wrong case (`ABSENT`), leading/
trailing whitespace, unknown strings, empty string, `null`, integers,
and booleans — was independently confirmed rejected by both the schema
and the model, with no case where the model silently accepts a value the
schema rejects (or vice versa).

`authority_role` (on `authority_disclosure`) was independently confirmed
to accept all six non-`"authoritative"` values of the shared 7-value
`AuthorityRole` enum
(`test_136ao_every_non_authoritative_role_accepted`), and to reject
`"authoritative"` specifically at this record's own local invariant
layer (§9 below), not via the shared enum definition itself.

## 6. Absent vs null verification

Every optional field was independently exercised across omitted /
explicit-null / `ABSENT` / populated / invalid-value states:

- `duplicate_of`: `ABSENT` by default in the minimal (non-`conflict`)
  case, never emitted on serialization when absent
  (`test_136ao_duplicate_of_absent_by_default`). Unlike every optional
  field on `NotificationAuthorityBinding` (all omitted-never-null),
  `duplicate_of` is the first field in this group's own record family
  where an explicit `null` is a *permitted* value — but only when the
  gating condition (`state == "conflict"`) holds; the key's presence
  itself, not merely its value, remains the gated quantity when
  `state != "conflict"`
  (`test_136ao_non_conflict_forbids_duplicate_of_explicit_null`).
- `_extensions`: `ABSENT` by default; explicit `null` independently
  confirmed rejected (the schema's `_extensions` type is `object`, which
  never admits `null`); a populated string-valued map round-trips
  exactly; a non-string value is rejected; a key colliding with a
  reserved envelope/field name is rejected; the `maxProperties: 32`
  bound independently confirmed against both the live schema and
  `extensions.py`'s `MAX_EXTENSION_PROPERTIES` constant.

## 7. Reference verification

| Reference field | Family restriction | `schema_id`/`schema_version` required |
|---|---|---|
| `generation_reference` | n/a (id+digest only, not family-restrictable) | no |
| `duplicate_of` | `marker_authority_binding` (self-family) | **yes** (Sec.12 cross-family rule, independently confirmed to apply even though the reference target shares this record's own family — a distinct-document cross-reference, not a same-document embedding) |

Wrong-family substitution was independently confirmed to fail
(`test_136ao_duplicate_of_wrong_family_rejected`). Missing `schema_id`/
`schema_version` on `duplicate_of` was independently confirmed to fail
(`test_136ao_duplicate_of_missing_schema_id_rejected`,
`test_136ao_duplicate_of_missing_schema_version_rejected`), while
`generation_reference` was independently confirmed to carry neither
field by construction (its shape has no such properties at all —
`additionalProperties: false` on the `generation_reference` $def,
`test_136ao_generation_reference_has_no_schema_id_or_version_fields`).
A valid-but-never-registered `duplicate_of` reference was independently
confirmed to succeed with `builtins.open` monkeypatched to raise on any
call — proving no lookup occurs
(`test_136ao_valid_but_nonexistent_reference_succeeds_no_lookup_performed`).
An independent AST scan of `bindings.py` confirmed no
`resolve_reference`/`lookup_record`/`resolve_authority`/
`activate_authority` symbol is defined anywhere in the module
(`test_136ao_no_lookup_or_authority_resolution_symbols_defined`).
`require_family()` (`references.py`, unchanged since prior phases) was
independently re-confirmed to compare only the `record_family`
discriminant field, never resolving, existence-checking, or
dereferencing the target.

## 8. Marker boundary verification

An independently-compiled forbidden-symbol list spanning every
marker-management capability named in the operator prompt
(`create_marker`, `write_marker`, `update_marker`, `delete_marker`,
`rename_marker`, `publish_marker`, `discover_marker`,
`enumerate_markers`, `resolve_marker_location`, `inspect_marker_file`,
`validate_marker_existence`, `compare_marker_freshness`,
`reconcile_marker_state`, `read_marker_contents`,
`write_marker_contents`, `modify_marker_metadata`, `synchronize_markers`)
was AST-scanned against `bindings.py` — zero matching function/method
definitions
(`test_136ao_module_defines_no_marker_management_function_or_method`).
Independently confirmed the module source imports none of
`socket`/`subprocess`/`os.path`/`shutil`/`requests`/`urllib`, and
contains no `os.environ`/`getenv` reference anywhere
(`test_136ao_module_source_never_imports_filesystem_socket_or_subprocess`,
`test_136ao_module_source_never_references_environment_variables`).

## 9. Authority boundary verification

The same forbidden-symbol scan additionally covers
`activate_authority`, `resolve_authority`, `determine_current_authority`,
`compare_authorities`, `transfer_authority`, `mutate_authority_pointer`,
and `modify_lifecycle_state` — zero matches. `authority_role ==
"authoritative"` is independently confirmed rejected at construction
(§5/§9 above, `test_136ao_authoritative_role_rejected`), and
`is_authoritative` is independently confirmed pinned to a frozen `False`
const, rejecting an explicit `True`
(`test_136ao_is_authoritative_true_rejected`) — matching the shared
`AuthorityDisclosure` type's own invariant, not a local override.
`compatibility_fallback_forbidden` is independently confirmed pinned to
a frozen `True` const, rejecting both an explicit `False` value and a
non-boolean type
(`test_136ao_compatibility_fallback_forbidden_must_be_true`,
`test_136ao_compatibility_fallback_forbidden_wrong_type_rejected`) —
this documents the prohibition on compatibility fallback but is not
itself an operational enforcement mechanism, matching the schema's own
disclosed description.

## 10. Runtime isolation verification

Independently re-scanned every `.py` file under `src/pcae/commands/`,
`src/pcae/core/`, `src/pcae/cltr/` (excluding the `authority/`
subpackage itself), and `src/pcae/runtime/` via AST import-statement
inspection: zero imports of `pcae.cltr.authority` in any of them
(`test_136ao_no_production_module_imports_authority_package`).
`bindings.py` itself was independently confirmed to import none of
`pcae.cltr.notification`, `pcae.cltr.marker`, `pcae.cltr.receipt`,
`pcae.commands`, `pcae.core`, `pcae.runtime`, `telegram`, `smtplib`,
`slack_sdk`, `pathlib`, or `os`
(`test_136ao_authority_bindings_module_does_not_import_marker_management_or_runtime`).
A separate, independent transitive-dependency walk starting from
`bindings.py` and following every `pcae.cltr.authority.*` import edge
within the package confirmed no module reachable from `bindings.py`
imports `socket`, `subprocess`, `telegram`, `smtplib`, `requests`,
`urllib.request`, `pathlib`, or `shutil`
(`test_136ao_authority_models_module_imports_no_transport_or_filesystem_code_via_full_dependency_walk`)
— a fresh construction of the import graph, not a reuse of any prior
phase's scan.

## 11. Side-effect verification

Instrumented `socket.socket.connect`, `subprocess.run`/`Popen`, and
filesystem writes (guarded `open()` in write/append/exclusive modes)
across package (re-)import, construction, serialization, equality, and
`repr()` of the model — zero side effects observed in every case (4
tests:
`test_136ao_no_network_during_construction_or_serialization`,
`test_136ao_no_subprocess_during_construction_or_serialization`,
`test_136ao_no_filesystem_write_during_construction_serialization_equality_repr`,
`test_136ao_package_reimport_is_side_effect_free`).

## 12. Immutability and equality verification

`MarkerAuthorityBinding` is independently confirmed a frozen dataclass
(`test_136ao_is_frozen_dataclass`); mutating a source `dict`/`list`
(the generation reference, the duplicate-of reference, the limitations
list, and the extensions mapping) after construction is independently
confirmed to never affect the already-constructed model (4 tests, §10
in the test module). `copy.deepcopy` independently confirmed to produce
a structurally-equal but non-identical object.

Equality was independently confirmed structural, not identifier-only or
digest-only: two records sharing the same `record_id`/`record_digest`
but differing `state` values are unequal
(`test_136ao_equality_rejects_identifier_only_and_digest_only_comparison`);
changing `state`, `migration_epoch`, or the null-vs-populated shape of
`duplicate_of` (holding `state == "conflict"` constant) each
independently changes equality
(`test_136ao_equality_changes_when_any_field_changes`).

## 13. Regression results

Commands run fresh in this phase (`.venv/bin/python -m pytest`, this
repo's own dependency-installed virtualenv):

- **new_136ao_independent_suite:**
  `tests/test_cltr_authority_136ao_marker_authority_binding_independent.py`
  — **100 passed** (98 fast + 2 slow/packaging).
- **136z_through_136an_together:** all fourteen pre-existing authority
  test modules (`test_cltr_authority_136z_shared_core.py` through
  `test_cltr_authority_136an_marker_authority_binding.py`) plus this
  phase's own, `-m "not slow"` — **2074 passed, 1 skipped, 2 failed**
  (the two inherited-and-independently-reconfirmed stale wheel-content
  assertions from §3.1; zero new failure attributable to this phase).
- **fast_green:** `pytest -m fast_green` — **4391 passed, 0 failed**,
  matching the 136AK/136AM-recorded baseline exactly (this phase's new
  test module is not marked `fast_green`, consistent with every prior
  `test_cltr_authority_136a*` module).
- **bounded_quick_tier_sweep:** `pytest -m "not slow and not
  phase_closure"` — results recorded in §13.1 below.

### 13.1 Bounded quick-tier sweep

`pytest -m "not slow and not phase_closure"` — **23415 passed / 30
failed / 9 skipped** (1878s). Every failing test ID was independently
cross-checked against the categories already disclosed by prior phases'
reports (136AN/136AM/136AK): 23 of the 30 fall into the exact
previously-disclosed inherited buckets (135O/135P finalization-
transaction and migration-evidence, 136U/136M typed-authority-model
scope-guard gaps, architecture-status/TODO staleness,
advisory-runtime-directory baseline, `test_rendering_134e5.py` baseline,
`test_phase_reports.py` PFR baseline); 2 are the newly-reconfirmed §3.1
wheel-content failures (`test_136ab_wheel_contains_authority_core_module`,
`test_136ad_wheel_contains_request_readiness_module`); the remaining 5
(`test_runtime_introspection_prototype.py`, all five of its tests) are a
previously-disclosed flaky/order-dependent category — 136AK's own
baseline recorded these five as failing, while 136AM's fresh run
recorded them as passing; this phase's fresh run again shows them
failing. `test_runtime_introspection_prototype.py` is unrelated to
`pcae.cltr.authority`, `bindings.py`, or any file this phase's own
independent module exercises; no failing test ID names `bindings.py`,
`MarkerAuthorityBinding`, or any symbol this phase's own independent
suite exercises. No unexplained new failure was found.

No isolated `git stash`-based baseline re-run was separately performed
this phase: this phase made **no change to `bindings.py`, `enums.py`,
or any other production source file** (no repair was required — see §3),
so this phase's own unmodified starting commit (`922e2b5e`) already
constitutes the exact isolated baseline; the identical two-failure
result in the `136z_through_136an_together` run above (against this
phase's own working tree, itself byte-identical to `bindings.py` at
`922e2b5e`) directly demonstrates the two wheel-content failures predate
and are unaffected by this phase.

## 14. Verdict

**MARKER AUTHORITY BINDING MODEL VERIFIED WITH NO NEW BLOCKING
FINDINGS — READY FOR FINALIZATION RECEIPT AUTHORITY BINDING
IMPLEMENTATION**

No Blocking defect was found in this phase; no repair to `bindings.py`
was required or performed. Two inherited findings (CONFIRMED-136AC-1 and
the stale-wheel-content-guard class of finding previously tracked as
CONFIRMED-136AE-2 and reconfirmed at 136AM) were independently
reproduced and confirmed pre-existing; both remain Non-Blocking and
outside this phase's allowed files to repair. Runtime remains Observed /
observe / unavailable throughout; no marker creation, marker write,
marker discovery, marker reconciliation, marker synchronization,
authority activation, or lifecycle mutation was introduced.

Recommended next phase: **136AP — Stage 3 Typed Authority Model
Finalization Receipt Authority Binding Implementation.** Per governed
instruction, this phase does not begin 136AP.

## 15. Telegram finalization disclosure

Dispatch attempted: see governed finalization output recorded in
`.pcae/phase-completion-report.md` / `.pcae/phase-completion-metadata.json`
for this phase, generated by `pcae phase complete` at the moment of
finalization (not fabricated here in advance).
