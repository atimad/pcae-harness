# Phase 136AU: Stage 3 Typed Authority Model QuarantineRecord Independent Verification

## 1. Purpose and boundaries

This phase independently verifies Phase 136AT's Typed Model
Implementation Group 11 (`QuarantineRecord`) by completely re-deriving
the contract directly from the frozen `136Y` plan
(`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
Sec.4/Sec.30), the live executable schema
(`src/pcae/schema_resources/cltr_cutover/records/quarantine_record.schema.json`),
and the shared definitions it composes
(`shared/references.schema.json`, `shared/failures.schema.json`,
`shared/enums.schema.json`, `shared/identity.schema.json`,
`shared/digest.schema.json`, `shared/limitations.schema.json`,
`shared/envelope.schema.json`) — without trusting Phase 136AT's
implementation, its own test suite
(`tests/test_cltr_authority_136at_quarantine_record.py`), its
documentation, its canonical report, prior prompts, prior expected-value
tables, or existing quarantine-domain behavior elsewhere in PCAE.

## 2. Independently re-derived contract

Re-derived directly from the live schema, before inspecting the 136AT
implementation or its test expectations:

- **Discriminator**: `record_type` const `"quarantine_record"`.
- **`schema_id`**: const
  `https://pcae.local/schemas/cltr_cutover/records/quarantine_record.schema.json`.
- **`contract_version`**: const `"1.0"`.
- **`schema_version`**: `MAJOR.MINOR` shape; the model supports only `"1.0"`.
- **14 required fields**: `schema_id`, `schema_version`,
  `contract_version`, `record_type`, `record_id`, `record_digest`,
  `created_at`, `migration_epoch`, `object_type`, `object_reference`,
  `reason_code`, `state`, `limitations`, `authority_disclosure`.
- **1 optional field**: `_extensions` (Tier 2, string-valued map,
  `maxProperties: 32`).
- **`object_type`**: record-local 4-value enum
  `{generation, publication_attempt, authority_state, compatibility_state}`.
- **`state`**: record-local 4-value `QuarantineState` (Sec.8.8)
  `{quarantined, under_review, released, permanently_retired}`.
- **`reason_code`**: the shared 24-value `ReasonCode` vocabulary,
  unconditionally required (Sec.16's `quarantine_record (always)` row,
  NON-BLOCKING-136V-5's `reason_code`-versus-`quarantine_reason` naming
  resolution).
- **`object_reference`**: the generic shared `record_reference` shape
  (`record_id` + `record_digest` + `record_family` required;
  `schema_id`/`schema_version` conditionally present) — **no**
  per-`object_type` `record_family` restriction is defined anywhere in
  the schema (NON-BLOCKING-136V-6): `object_type`'s `generation` value
  has no corresponding `record_family` enum member, making a uniform
  restriction structurally impossible to state for every branch.
- **`authority_disclosure.authority_role`**: shared 7-value enum, but
  `"authoritative"` is locally forbidden on this record family (Sec.9's
  12-file list; "quarantine becoming authority" is the specific
  prevention named in Sec.30).
- **No `phase_id`/`transition_id` fields** — `quarantine_record` is not
  in Sec.7.2's `phase_id`-required or `transition_id`-required family
  lists.
- **`migration_epoch` remains required** despite the above (Sec.7.2's
  universal rule; no family is exempted from it).
- **No other within-document conditional.** Unlike `CompatibilityState`
  (two `allOf`/`if`/`then`/`else` blocks), the live
  `quarantine_record.schema.json` schema defines no top-level `if`,
  `then`, `else`, or `allOf` beyond the nested `authority_disclosure`
  `allOf` restricting `authority_role`. Sec.16's own
  conditional-validation table names no other within-document
  conditional for this family; the operator prompt's illustrative
  conditional examples (release evidence, expiry, retained-state field
  prohibitions) are confirmed absent from both Sec.16 and Sec.30, and
  are therefore correctly not implemented.

## 3. Verification method

Every fixture and assertion in the new test module
(`tests/test_cltr_authority_136au_quarantine_record_independent.py`,
199 tests: 197 fast + 2 packaging) was derived directly from the live
schema file and the frozen contract text quoted in its `description`
fields, independently fixtured — not copied from
`test_cltr_authority_136at_quarantine_record.py`'s own fixture helpers,
and not importing any 136AT/136AS/136V/136W fixtures or expected-value
tables. The decisive independence check is an exhaustive
schema-vs-model parity sweep (`test_136au_exhaustive_schema_vs_model_object_type_state_reason_parity`):
for every combination of `object_type` (4), `state` (4), and
`authority_role` (7) — 112 combinations — the Python model's
accept/reject decision is compared directly against the live executable
schema's own validation decision via `pcae.schema_runtime`. Zero
mismatches: the model neither weakens nor strengthens the schema.

Covered, independently of the 136AT test suite: exact field inventory
and discriminator match; `schema_id`/`schema_version`/`contract_version`
requirements (missing, wrong, unsupported); every required field
missing individually; the full `object_type` x `state` x `reason_code`
enum inventories (every value of each constructs and round-trips);
`object_reference` construction with every `record_family` value
regardless of `object_type` (anti-strengthening: no per-`object_type`
restriction invented); `object_reference` with and without the optional
`schema_id`/`schema_version` fields, including explicit-null rejection;
malformed/missing `object_reference` sub-fields (missing
`record_family`, malformed digest, malformed `record_id`, malformed
`schema_version`, unknown extra key); a syntactically valid but
nonexistent reference constructing successfully with no lookup;
sixteen anti-strengthening cases confirming quarantine-domain
assumptions the schema does not encode (referenced-object existence,
release evidence, terminal-state immutability, state/role coupling,
object_type/record_family coupling, calendar-invalid-but-shape-valid
timestamps, duplicate limitations entries) are correctly *not*
enforced; structural equality (not identifier-only, digest-only, or
state-only); recursive immutability (frozen dataclass, source-mutation
isolation, output-mutation isolation, deep-copy independence);
deterministic round-trip and construction-error determinism; the full
quarantine-boundary / existing-quarantine-subsystem-isolation symbol
and import scan; `CompatibilityState` regression re-confirmation (field
inventory, `legacy_retired` conditional, construction, round-trip,
package export); scope-guard integrity (no sibling guard over-broadened
to forbid a now-implemented family); runtime isolation (transitive
import walk from `compatibility_quarantine.py`, no production module
imports `pcae.cltr.authority`); no-side-effect verification
(monkeypatched socket/subprocess/filesystem); and packaging (fresh
wheel/sdist build, isolated venv installation outside the repository,
exact sixteen-model export inventory).

## 4. Findings

**No Blocking defect was independently demonstrated.** The 136AT
implementation matches the independently re-derived contract exactly:

- The 14-field required-field set, the `additionalProperties: false`
  closure, and the single optional `_extensions` field all match the
  live schema exactly.
- `object_type` and `state` enums match the live schema's `$defs`
  exactly (4 members each); `reason_code` matches the shared 24-value
  vocabulary exactly; `authority_role`'s local `"authoritative"`
  forbiddance is enforced in `QuarantineRecord.__post_init__`
  (`compatibility_quarantine.py:655-660`), firing on every construction
  path including direct dataclass construction, not only `from_dict`.
- `object_reference` correctly reuses the generic
  `shared/references.schema.json#/$defs/record_reference` shape with no
  invented per-`object_type` restriction, confirmed both by the parity
  sweep and by direct schema-text inspection
  (`test_136au_object_reference_is_generic_record_reference_with_no_restriction`).
  `schema_id`/`schema_version` are correctly optional (via the `ABSENT`
  sentinel) rather than defaulted to `None` or unconditionally required.
- No lookup, existence check, or repository access occurs at
  construction time for `object_reference` — confirmed by constructing
  a reference to a deliberately nonexistent `record_id`.
- The shared wrapper types this family reuses (`RecordId`,
  `MigrationEpochToken`, `RecordDigest`/`ReferencedRecordDigest`,
  `Timestamp`, `SchemaVersionString`, `RecordReference`, `ReasonCode`,
  `RecordFamily`, `AuthorityDisclosure`, `Limitations`,
  `ExtensionMapping`) were independently re-checked against
  `shared/identity.schema.json`, `shared/digest.schema.json`,
  `shared/envelope.schema.json`, `shared/limitations.schema.json`, and
  `shared/failures.schema.json`'s own patterns/enums/bounds and found
  to match exactly — no field-specific narrowing was needed for this
  family (unlike `CompatibilityState`'s `retirement_state`, which
  required a field-site-local empty-object-only restriction on top of
  the general-purpose `OpaqueJsonValue` wrapper, DEFERRED-136V-1).
  `QuarantineRecord` uses no `OpaqueJsonValue`-wrapped field at all.
- `CompatibilityState`'s 16-field contract, both of its conditionals
  (`mode == 'legacy_retired'` ⟺ `retirement_state` required;
  restricted-mode `authority_role` narrowing), and its package export
  are independently reconfirmed unchanged by Phase 136AT's edits.
- No sibling scope guard (`test_cltr_authority_136aq_*`,
  `test_cltr_cutover_136m_*`, `test_cltr_cutover_136u_*`, and every
  other `MUST_NOT_EXIST`-style tuple across the `test_cltr_*136*.py`
  modules) was found over-broadened to forbid any of the sixteen
  currently-implemented families.
- No production module outside `src/pcae/cltr/authority/` imports
  `pcae.cltr.authority`; `compatibility_quarantine.py`'s transitive
  import graph contains no `socket`, `subprocess`, `shutil`,
  `requests`/`urllib`, `smtplib`, `pathlib`, or `os.path` dependency.
  No quarantine command is wired into `src/pcae/cli.py`.

No production implementation change was made this phase — per the
Blocking Repair Policy, `compatibility_quarantine.py` is unmodified.

## 5. Regression

`test_cltr_authority_136*.py` + `test_cltr_cutover_136*.py` together
(`-m "not slow"`, freshly reproduced, not trusted from any prior
count): 4771 passed / 4 failed / 9 skipped (this phase's own 197 new
fast tests included). All four failures are the same pre-existing,
independently-reproduced inherited category named in the 136AT report
and reconfirmed unchanged this phase:
`test_136ab_wheel_contains_authority_core_module`,
`test_136ad_wheel_contains_request_readiness_module` (stale
wheel-content guards), `test_136m_no_typed_authority_model_module_exists`,
`test_136u_no_runtime_code_references_group10_families_outside_schema_resources`
(stale 136M/136U schema-layer scope guards). Zero new regressions.

Fast Green (`-m "fast_green"`, full repository, `-n auto`): 4391
passed, 0 failed — matches the 136AT-recorded baseline exactly (this
phase's new independent-verification module is not tagged
`fast_green`, matching every sibling `-independent` module's own
precedent).

Fresh wheel/sdist build (`python -m build --wheel --sdist`) plus an
isolated venv installation exercise, both performed independently
outside the pytest-driven `@pytest.mark.slow` tests as an additional
direct check, confirmed all sixteen record-family models import,
construct, and round-trip correctly from a scratch working directory,
with `QuarantineRecord` and `CompatibilityState` both importable and
functioning identically to the in-repository behavior.

## 6. No-go confirmation

- No quarantine storage, filesystem operation, command, resolver,
  eligibility engine, release/deletion/reconciliation behavior,
  artifact inspection, or reference lookup was introduced (none existed
  before this phase either; this phase made no production change).
- No publication-blocking, lifecycle-blocking, rollback, or remediation
  execution was introduced.
- No authority activation, transfer, resolution, comparison, or legacy
  authority demotion occurred; no CLTR authority activation occurred.
- No lifecycle mutation occurred outside the standard governed
  `pcae task`/`pcae phase-report`/`pcae phase complete` finalization
  path.
- No execution capability was introduced. Runtime remains Observed /
  observe / unavailable (confirmed via `pcae runtime inspect` after
  this phase's edits).

## 7. Telegram finalization evidence

Recorded via the governed `pcae phase complete` finalization path; see
`.pcae/phase-completion-report.md` and
`.pcae/phase-completion-metadata.json` for the canonical
machine-readable record of this phase's completion, matching this
document's phase identifier and result.

## 8. Verdict

**QUARANTINERECORD MODEL INDEPENDENTLY VERIFIED — NO BLOCKING FINDING.**
The 136AT implementation matches the independently re-derived contract
exactly across field inventory, discriminator, enums, conditionals (and
their deliberate absence beyond the two identified), reference shape,
anti-strengthening posture, quarantine boundary, runtime isolation, and
packaging. `CompatibilityState` behavior is independently reconfirmed
unchanged. No production implementation change was made this phase.

## 9. Recommended next phase

**136AV — Stage 3 Typed Authority Model Whole-Model Integration
Verification.** Per governed instruction, Phase 136AV was not begun in
this phase.
