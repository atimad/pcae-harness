# Phase 136V: Compatibility State / Quarantine Record Schema Implementation

## 0. Contract-derived group identification — resolved before coding

The frozen primary contract is `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001` v1.0
(`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`),
repaired by Phase 136D, restated by the 136E implementation plan
(`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`).

Section 46's implementation-group table (verbatim row 11):

> | 11 | `compatibility_state.schema.json` (depends only on group 1);
> `quarantine_record.schema.json` (depends on 2–8) | 1 / 2–8 respectively |
> yes |

This is the **final row** of the table — there is no Group 12. Group 11 is
the last of the 11 frozen executable-schema implementation groups.

**Canonical title.** The roadmap and operator prompt use "Compatibility /
Quarantine" as a shorthand label. The frozen contract's own family names
(§4, row 14 "Quarantine Record", row 19 "Compatibility State Record") do not
share a common suffix the way Group 10's three "Authority Binding" families
did (which is why 136T's title compressed to "Notification/Marker/Receipt
Authority Binding Schema"). This document therefore uses the more exact,
contract-derived title **"Compatibility State / Quarantine Record Schema
Implementation"**, applied consistently across this document, the governed
task contract, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DONE.md`, the
canonical phase report, completion metadata, and the terminal Telegram
delivery.

**Confirmed inherited state at phase start** (independently re-derived from
the actual repository, per Phase 136U's own independent verification and
this phase's own initial inspection — not merely restated from prose):

- 14 production record schemas (Groups 2–8, 10) exist on disk.
- 21 manifest entries (7 shared + 14 records).
- 22 offline registry resources (21 manifest entries + `manifest.schema.json`
  itself).
- No Group 11 schema, no Group 9 schema (permanently absent per §46), no
  Group 12 schema.
- Runtime: Observed / observe / execution unavailable.
- Repository clean, zero commits ahead of `origin/main`.

## 1. Exact Group 11 record families

| # | 135Z / §4 family name | Executable disposition | Artifact |
|---|---|---|---|
| 19 | Compatibility State Record | standalone schema | `records/compatibility_state.schema.json` |
| 14 | Quarantine Record | standalone schema | `records/quarantine_record.schema.json` |

Group 11 is exactly these two families — no third file, no `views/`
resource, no `HistoricalAuthorityReference` schema (§35: explicitly a
runtime-only typed model, never a schema, and not part of Group 11 despite
compatibility/quarantine conceptually referencing historical authority).

## 2. Exact contract sections consulted

§4 (exact executable-schema inventory), §6 (shared definition inventory),
§7 (envelope contract, including §7.2's family-required-fields table), §8.7
(`CompatibilityMode`), §8.8 (`QuarantineState`), §9 (authority-role
contract), §11 (digest contract), §12 (reference contract), §13 (timestamp
contract), §14 (unknown-field / Tier 1 vs Tier 2 contract), §16 (local
conditional-validation contract), §30 (Quarantine schema contract), §34
(CompatibilityState schema contract), §35 (HistoricalAuthorityReference
disposition — confirms exclusion), §38 (not-required family disposition),
§39–§41 (canonicalization/semantic-validation/registry boundaries), §46
(implementation groups), §51.2 (`CSCH-EXEC-REQ-041`, `-043`, `-058` — the
three Group-11-tagged verification-matrix rows).

## 3. Field tables (verbatim contract fields, normalized to this schema's naming)

### 3.1 CompatibilityState (§34)

| Field | Required | Type |
|---|---|---|
| `component` | yes | string (no bounds given) |
| `role` | yes | enum restricted to `{compatibility, historical}` (AuthorityRole §8.2 subset) |
| `allowed_reads` | yes | array of string (no bounds given) |
| `forbidden_authority_use` | yes | `const true` |
| `fallback_disabled` | yes | boolean |
| `mode` | yes | `CompatibilityMode` (§8.7, shared enum) |
| `retirement_state` | conditional | required iff `mode == "legacy_retired"`; **no type given at all** |
| `digest` | yes | `sha256_hex` (realized as universal `record_digest`) |
| `limitations` | yes | array |

Plus the universal envelope (§7.1: `schema_id`, `schema_version`,
`contract_version`, `record_type`, `record_id`, `record_digest`,
`created_at`) and `migration_epoch` (§7.2's universal "all 16 standalone
families" rule) and `authority_disclosure` (universal precedent, established
by every one of the 11 prior families).

### 3.2 QuarantineRecord (§30)

| Field | Required | Type |
|---|---|---|
| `object_type` | yes | enum: `generation`, `publication_attempt`, `authority_state`, `compatibility_state` |
| `object_reference` | yes | `record_reference` (generic, shared/references.schema.json) |
| `reason_code` | yes | `failures.schema.json#/$defs/reason_code` |
| `state` | yes | `QuarantineState` (§8.8, 4 values) |
| `limitations` | yes | array |
| `digest` | yes | `sha256_hex` (realized as universal `record_digest`) |

Plus the universal envelope and `migration_epoch`, `authority_disclosure`
as above. No `phase_id`/`transition_id` (neither family is in §7.2's
required lists for those fields).

## 4. Non-Blocking / Deferred discrepancy disclosures

- **NON-BLOCKING-136V-1.** §7.2's dedicated "Global compatibility records"
  row exempts `compatibility_state` from `phase_id`/`transition_id` but its
  literal text does not also exempt `migration_epoch`, even though the
  row's own rationale ("compatibility state spans phases") could be read to
  suggest a broader exemption. Resolved in favor of the universal,
  unconditional §7.2 rule: `migration_epoch` remains required.
- **NON-BLOCKING-136V-2.** §34 lists `role` as a bare 2-value enum
  restriction of `AuthorityRole` (§8.2) rather than a `$ref` to the shared
  7-value `enums.schema.json#/$defs/authority_role` def with an overlay
  constraint. Implemented as a local 2-value `$defs/compatibility_role`
  enum, since §34 states the restriction as the field's own defining
  property, not an overlay on the shared enum.
- **NON-BLOCKING-136V-3.** §16's compatibility-mode conditional ("`mode` in
  `{legacy_historical, legacy_disabled, legacy_retired}` ⇒ `authority_role`
  must not be `authoritative` and must not be `derivative`") is applied to
  `authority_disclosure.authority_role` (the broader, universal 7-value
  disclosure field), not to the family-local `role` field. `role`'s own
  enum is already unconditionally restricted to `{compatibility,
  historical}` — applying the identical restriction there again under the
  same condition would be a structural no-op. `authority_role`, throughout
  §7–§9, is consistently the name of the `authority_disclosure` struct's
  field; the family-local field is separately and only ever called `role`
  in §34.
- **NON-BLOCKING-136V-4.** `component` and `allowed_reads` carry no
  bounds in §34. Locally-decided bounds were applied (printable-ASCII
  256-char `component`; per-entry 512-char, no-`..`, no-control-character
  `allowed_reads` entries; 64-item array cap), mirroring this repository's
  existing bounded-free-text convention (`shared/limitations.schema.json`).
- **NON-BLOCKING-136V-5.** §16's local-conditional table and
  `CSCH-EXEC-REQ-041` both name the unconditionally-required quarantine
  reason field `quarantine_reason`; §30's own field table and §30's own
  prose ("every quarantine record requires a non-null `reason_code`") both
  name it `reason_code`. Resolved in favor of `reason_code`, per the
  field-table-literalism rule (§30 is the most specific binding clause for
  this family, and is internally self-consistent between its table and its
  prose, whereas §16/`CSCH-EXEC-REQ-041` are the less specific, cross-group
  summary text).
- **NON-BLOCKING-136V-6.** `quarantine_record.object_reference` carries no
  per-`object_type` `record_family` restriction. §30 defines no such
  conditional, and one branch (`object_type: "generation"`) has no
  corresponding `record_family` enum member to restrict to in the first
  place (`shared/enums.schema.json`'s `record_family` enum has no
  `"generation"` entry — generation identity uses the distinct
  `generation_reference` id+digest shape, §12), making a uniform
  conditional restriction structurally impossible to state for every
  branch. Consistent with the established precedent NON-BLOCKING-136R-3
  (no family restriction invented where the contract specifies none).
- **DEFERRED-136V-1.** `retirement_state`'s field-table entry (§34) gives
  no field type at all — not even the bare `"object"` token that
  `staleness_check` had in §33 (resolved by `DEFERRED-136T-1`). Pinned here
  to an empty-shape placeholder object (`additionalProperties: false`, no
  properties) pending a future contract amendment defining its actual
  fields, mirroring the `DEFERRED-136T-1` pattern exactly.

## 5. Required shared/embedded definitions

`compatibility_state.schema.json`: `shared/envelope.schema.json` (schema_version,
timestamp), `shared/identity.schema.json` (record_identity, migration_epoch),
`shared/digest.schema.json` (record_digest), `shared/enums.schema.json`
(compatibility_mode, authority_role via limitations), `shared/limitations.schema.json`
(limitations_array, authority_disclosure).

`quarantine_record.schema.json`: the above plus `shared/references.schema.json`
(record_reference) and `shared/failures.schema.json` (reason_code).

Neither file `$ref`s any `records/*.schema.json` file — confirmed by
`test_136v_compat_references_only_group1_shared_defs` and
`test_136v_quarantine_does_not_reference_compatibility_state_or_vice_versa`.

## 6. Record-local enum additions

- `compatibility_role` (local `$defs`, 2 values: `compatibility`,
  `historical`) — new to `compatibility_state.schema.json` only.
- `object_type` (local `$defs`, 4 values) — new to `quarantine_record.schema.json` only.
- `quarantine_state` (local `$defs`, 4 values, restating §8.8's
  `QuarantineState`) — new to `quarantine_record.schema.json` only.

`CompatibilityMode` (§8.7) was already a **shared** enum, implemented in
`shared/enums.schema.json` at Phase 136H (Group 1) — not new to this phase,
only newly *consumed* by `compatibility_state.mode`.

## 7. Existing / expected production record counts

| Item | Before 136V | After 136V |
|---|---|---|
| Standalone record schemas | 14 | **16** |
| Manifest entries | 21 | **23** |
| Offline registry resources | 22 | **24** |
| Implementation groups with a schema file | 1–8, 10 | **1–8, 10, 11** |

16 records + 7 shared + 1 `README.md` = 24 files under
`schemas/cltr_cutover/`, matching §4.1's frozen full-implementation target
exactly (`bindings/` and `views/` remain reserved-only, 0 files).

## 8. Group 11 dependency edges

- `compatibility_state.schema.json` → `shared/{envelope,identity,digest,enums,limitations}.schema.json`
  only (Group 1). No manifest dependency edge to any Group 2–8 record.
- `quarantine_record.schema.json` → the same 5 shared files plus
  `shared/references.schema.json` and `shared/failures.schema.json`
  (Group 1). §46's "depends on 2–8" is a **conceptual/implementation-
  ordering** prerequisite (quarantine's `object_type` enum names families
  first defined in Groups 2, 5, and — circularly, within this same group —
  11 itself), not a manifest-declared `$ref` dependency: no other family's
  precedent in this package ever adds a direct manifest dependency edge to
  another `records/*.schema.json` file either (every manifest `dependencies`
  array in the whole package lists only `shared/*.schema.json` paths).
  Confirmed by `test_136v_quarantine_record_declares_no_direct_ref_to_group2through8_files`.

## 9. Required creation order

Both files depend only on Group 1 (already frozen at 136H). Neither
`$ref`s the other. Both are independently, concurrently valid — there is no
forced creation order between `compatibility_state` and `quarantine_record`
within Group 11 (confirmed by
`test_136v_group11_creation_order_independent_of_sibling`), matching every
prior group's sibling-independence pattern (e.g. Group 10's three binding
families).

## 10. Sibling independence and dependency graphs

Four graphs built and verified:

1. **JSON Schema `$ref` graph** — both new files' only `$ref` targets are
   `../shared/*.schema.json` or local `#/$defs/...` fragments; neither
   targets `../records/...`. No cycle.
2. **Manifest dependency graph** — `test_136v_full_manifest_dependency_graph_is_acyclic`
   walks every entry's `dependencies` list recursively across all 23
   manifest entries; no cycle detected.
3. **Record identity dependency graph** — neither Group 11 schema's
   `record_id` shape depends on any other record's identity (both use the
   generic `record_identity` shape, §12).
4. **Record digest dependency graph** — both `record_digest` fields are
   shape-checked only (§11); no digest field is computed from another
   record's digest.

**Sibling-independence matrix (Group 11):** `compatibility_state` does not
reference `quarantine_record`; `quarantine_record` does not reference
`compatibility_state` (confirmed by direct text-search of both files, and
by `object_type`'s enum including `"compatibility_state"` as a
*referenceable object kind*, not a schema `$ref` — a quarantine record can
describe a compatibility-state object being quarantined without the schema
file itself depending on `compatibility_state.schema.json`).

No compatibility/quarantine cycle, no quarantine/release cycle, no
authority-state cycle, no binding/compatibility cycle, no future-record
dependency (Group 11 is the final group — there is no Group 12 to depend
on), no immutable record requiring post-creation mutation, no post-hoc
digest completion, no record-v2 workaround.

## 11. Group atomicity

Both Group 11 manifest entries are tagged `implementation_group: 11`.
Fail-closed behavior tested for: one schema file missing while its manifest
entry remains (`test_136v_manifest_detects_missing_group11_sibling_file`,
raises on `load_and_verify_manifest`); tampered file content
(`test_136v_manifest_detects_content_tamper_on_new_record`, raises
`ManifestIntegrityError`). This is **delivery atomicity** (both files land
in the same governed commit, both manifest entries or neither) — no runtime
transaction is introduced; §1's Layer boundaries are unchanged.

## 12. Strictness tier

Both `compatibility_state.schema.json` and `quarantine_record.schema.json`
are **Tier 2** (§14's explicit per-file list already includes both by
name): `additionalProperties` closed except for a single reserved
`_extensions` key, itself a string-valued-only object (`{"type": "object",
"additionalProperties": {"type": "string"}}`, `maxProperties: 32`).
Confirmed: unknown top-level fields rejected; `_extensions` accepts a
string-valued map; `_extensions` rejects non-string values, `null`, and
scalar values; `_extensions` cannot smuggle an alternate `authority_role`,
compatibility `mode`, or quarantine `state` claim (canonical fields remain
authoritative regardless of `_extensions` content — tested explicitly).

## 13. Authority-role boundary

`authority_role: "authoritative"` is locally forbidden on both files —
§9's 12-file list explicitly names both `quarantine_record` and
`compatibility_state`. Additionally, `compatibility_state.authority_disclosure.authority_role`
is further restricted to `{historical, compatibility}` when `mode` is one
of `legacy_historical`, `legacy_disabled`, or `legacy_retired` (§16,
`CSCH-EXEC-REQ-043`, see NON-BLOCKING-136V-3). `quarantine_record` carries
no additional restriction beyond the universal "not authoritative" rule —
a quarantine record may legitimately disclose `authority_role: "quarantined"`.
All allowed and forbidden values tested (`test_136v_compat_restricted_mode_forbids_non_historical_compatibility_role`
parametrized over 3 modes × 5 forbidden roles = 15 cases;
`test_136v_compat_authoritative_role_forbidden_unconditionally`,
`test_136v_quarantine_authoritative_role_forbidden_unconditionally`).

## 14. Compatibility and quarantine boundaries

Neither schema performs, claims, or enables: migration execution, adapter
selection, artifact rewriting, upgrade/downgrade authorization, operational
interoperability claims, current-authority mutation, semantic-compatibility
truth (`compatibility_state`); or file movement, renaming, directory
creation, authority revocation, runtime execution blocking, release,
repair, destruction, lifecycle mutation, notification/marker/receipt
creation (`quarantine_record`). Schema validity proves local wire shape
only (§1, §40). Confirmed by symbol-absence scans
(`test_136v_no_compatibility_execution_symbol_referenced`,
`test_136v_no_quarantine_mutation_symbol_referenced`) and by the complete
absence of filesystem-mutation code anywhere in the two new schema files
(pure JSON documents — no code exists to mutate anything).

## 15. Fixtures and focused tests

Fixtures are inline Python dict-builder functions (`_valid_compat`,
`_valid_quarantine`) in the new test module, matching this package's
established convention — no prior implementation group under
`schemas/cltr_cutover` uses separate on-disk JSON fixture files; every one
of 136H–136U's focused modules builds fixtures as Python factories in the
module itself. `tests/test_cltr_cutover_136v_compatibility_state_quarantine_record_schema.py`:
121 fast tests + 2 slow packaging tests (123 total), covering: exact
inventory, manifest/registry counts, Tier 2 strictness, every valid
`CompatibilityMode`/`QuarantineState`/`object_type` branch, every
conditional (`legacy_retired` ⇄ `retirement_state`, mode-restricted
`authority_role`), enum rejection, missing-required-field rejection
(16-field parametrized sweep), malformed digest/timestamp rejection,
`_extensions` smuggling-resistance, wrong-family/malformed-reference
rejection, dependency-graph acyclicity, no-network/no-mutation/no-authority/
no-execution boundaries, editable-install and installed-wheel offline
validation.

## 16. Manifest and registry verification

23 manifest entries (7 shared + 16 records), deterministic sorted order
preserved, both new entries tagged `implementation_group: 11`,
`status: "frozen"`. 24 offline registry resources (23 manifest entries +
`manifest.schema.json`). Both new `schema_id`s present and unique. Manifest
digest recomputation performed for both new files
(`c2087a7d...62867` for `compatibility_state.schema.json`,
`788b176b...121dc22` for `quarantine_record.schema.json`) — both verified
against actual on-disk bytes via `load_and_verify_manifest`.

## 17. Packaging and installed-wheel verification

Wheel and sdist freshly built and inspected: both new record schemas
present at their exact packaged paths; no `bindings/` or `views/`
directory; no `.pcae/cltr-authority/` content. Installed into a fresh
isolated venv outside the repository checkout; offline registry build and
record validation exercised from that isolated environment, confirming 24
registry resources load correctly post-install.

## 18. No-network / no-runtime-behavior / no-authority / no-execution verification

`socket.socket` and `socket.create_connection` monkeypatched to raise
during registry construction and validation — zero network calls
(`test_136v_no_network_during_registry_and_validation`). No
`subprocess`/`os.system`/`eval`/`exec`/`socket` token appears in either new
schema file (pure JSON, so this is a structural guarantee, not merely an
absence-of-usage claim). No persistence directory created during
validation. Validation never mutates the input record (deep-equality
check before/after). No `.pcae/cltr-authority/` directory exists. No
compatibility-execution or quarantine-mutation symbol referenced anywhere
in the two new files.

## 19. Inherited finding review

Reviewed 136M, 136N, 136P, 136Q, 136R, 136S, 136T, 136U findings. None of
the prior Non-Blocking/Deferred findings concern `compatibility_state` or
`quarantine_record` field content directly (they concern other families'
field-table gaps, generation-reference typing choices, or Group 8/10-
specific disclosures) — Group 11 leaves all of them **unchanged**. The one
finding this phase directly interacts with is **BLOCKING-136U-1**'s repair
(the `LATER_GROUP_RECORD_FILES`-derivation structural fix): this phase's
own scope-guard migration across 12 prior test modules preserved that
derivation pattern everywhere it already existed (136N, 136R) and did not
reintroduce a second, separately-hardcoded `forbidden_stems` copy anywhere
— confirmed by re-running every migrated module and by the absence of any
new hardcoded duplicate list. The stale duplicated-guard defect class did
**not** recur.

## 20. Full-suite baseline comparison

Combined Groups 1–11 + schema-runtime suite (fast, `-m "not slow"`): 1866
passed, 8 skipped, 7 deselected (0 failed). Packaging + 136V's own slow
tests: 5 passed. Fast Green: 4391/4391 passed, exactly matching 136U's own
count (this phase's new module carries no `fast_green` marker, consistent
with every prior implementation-group phase). Full unmarked suite result
and comparison against 136U's disclosed 21820 passed / 22 failed / 1
skipped baseline is recorded in the finalization commands' output; any
new failure touching `cltr_cutover`, `schema_runtime`, manifest, or
packaging is treated as Blocking per the governing instruction.

## 21. Lifecycle reporting debt (carried forward, unchanged)

The recurring false Architecture Status limitation claim, historical
stale-report-body risk, full-suite baseline instability, and
lifecycle-state-sensitive repository-mutation test categories are
unchanged by this phase. 136V does not attempt lifecycle-reporting repair
(not directly blocking this phase's finalization).

## 22. Limitations / deferred work

- `DEFERRED-136V-1`: `retirement_state`'s internal shape remains
  unspecified by the frozen contract; pinned to an empty placeholder
  pending a future contract amendment.
- `PREREQUISITE-136C-1` (carried forward from §30's own text): full
  production-integrity recovery (the actual un-quarantining procedure)
  remains a deferred activation prerequisite for any future Stage 3
  cutover — this phase implements the descriptive schema only.
- No `HistoricalAuthorityReference` schema was implemented (§35 explicitly
  excludes it from Group 11 — and from any schema group).
- No Stage 3 typed Python model, derived record view, or broad
  cross-record semantic validator was implemented for either family
  (Layer 4+ remains future work per §40).

## 23. Whether this is the final executable-schema group

**Yes.** Group 11 is the last row of §46's table. With Group 11 complete,
all 11 frozen executable-schema implementation groups have production
schema files (Groups 1–8, 10, 11) except Group 9, which the frozen
contract itself assigns no schema file, ever (§46, §35, §37). No Group 12
exists or is defined anywhere in the frozen contract.

## 24. Required final report confirmations

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. Phase 136V implemented only executable-schema Implementation
Group 11 as frozen by `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001`. The exact
Group 11 title, inventory, prerequisites, field tables, conditional rules,
and dependency structure were derived from the frozen primary contract
before implementation. No Group 12+ schema was implemented. The
`compatibility_state` schema remains descriptive data only — schema
validity does not establish operational compatibility, successful
migration, upgrade safety, downgrade safety, or runtime interoperability.
The `quarantine_record` schema remains descriptive data only — schema
validity does not establish that an artifact was physically quarantined,
blocked, released, repaired, deleted, or made safe. No compatibility
migration, compatibility resolution, quarantine mutation, artifact
movement, artifact deletion, release operation, or lifecycle transition
occurred. No Stage 3 typed record model, derived record view, or broad
cross-record semantic validator was implemented. No cryptographic
verification, runtime evaluator, resolver, coordinator, authority-state
persistence, or authority pointer was implemented or changed. No runtime
Group 11 object was created or persisted. The stale duplicated later-group
scope-guard class repaired by 136U was not reintroduced. No authority
epoch changed. No CLTR authority was created. No legacy authority was
demoted. No legacy authority was retired. No production lifecycle behavior
changed. No execution capability was introduced. Runtime remains Observed,
maximum capability remains observe, and execution availability remains
unavailable.

## 25. Recommended next phase

**136W — Compatibility State / Quarantine Record Schema Independent
Verification.** Must independently attack: exact Group 11 inventory, every
field table, conditional branches, compatibility classifications,
quarantine classifications, authority role, extension behavior,
family-specific references, sibling independence, all dependency graphs,
immutable creation order, atomic group completeness, manifest correctness,
scope-guard migration, package completeness, installed-wheel offline
behavior, no compatibility execution, no quarantine mutation, no
authority, no execution. Not started by 136V.
