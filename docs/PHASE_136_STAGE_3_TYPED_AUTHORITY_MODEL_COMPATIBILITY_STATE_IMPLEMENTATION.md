# Phase 136AR: Stage 3 Typed Authority Model CompatibilityState Implementation

## 1. Purpose and boundaries

This phase implements Typed Model Implementation Group 10 of the frozen
`136Y` plan (`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
Sec.4/Sec.34, package layout Sec.7): exactly one record-family model,
`CompatibilityState`, schema-backed by
`src/pcae/schema_resources/cltr_cutover/records/compatibility_state.schema.json`
(Phase 136V, Implementation Group 11 of the schema-authoring chapter; the
schema-layer group numbering and the typed-model group numbering are
distinct sequences, as with every prior family in this chapter).
`CompatibilityState` is implemented in a new module,
`src/pcae/cltr/authority/compatibility_quarantine.py`, containing only
`CompatibilityState`; `QuarantineRecord` (the module's other eventual
occupant per the 136Y plan's file layout) remains unimplemented.

`CompatibilityState` is a descriptive, immutable, schema-backed typed
representation only. It never calculates, infers, or determines
compatibility; negotiates or selects a version; compares installed
packages; inspects runtime versions, dependencies, artifacts, schema
registries, repository history, Git state, or environment configuration;
loads or validates the existence of a referenced object; performs,
proposes, or executes migration; transforms a record or converts a
schema; reconciles incompatible states or resolves conflicts; decides
fallback behavior; activates or disables a compatibility mode; determines
upgrade or downgrade readiness or safety; authorizes or blocks a cutover;
mutates lifecycle state; creates, quarantines, isolates, moves,
classifies, releases, or deletes any record or artifact; or activates,
resolves, determines, compares, or transfers authority. It describes a
declared legacy-compatibility-layer classification for one named
component; it never itself performs a migration, selects a migration
adapter, rewrites a record, authorizes an upgrade or downgrade, claims
operational interoperability, mutates current authority, or establishes
semantic compatibility truth. Legacy lifecycle remains the sole
production authority; CLTR remains derivative. Runtime remains
Observed / observe / unavailable, unchanged by this phase.

## 2. Binding sources

Precedence followed (identical structure to every prior phase in this
chapter): frozen primary contract (`CLTR-CUTOVER-001`,
`CLTR-CUTOVER-SCHEMAS-001` v1.0, `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001`
v1.0 Sec.34/Sec.46) -> verified contract -> verified architecture
(Phase 136B) -> verified 136Y implementation plan -> verified
136Z/.../136AQ shared core and prior record-family models -> this
governed 136AR task contract -> operator prompt. No conflict was found
between the operator prompt and the frozen contract requiring a
discrepancy disclosure.

Consulted directly: the 136Y plan, the executable schema
(`compatibility_state.schema.json`, which itself carries an extensive
inline provenance block disclosing NON-BLOCKING-136V-1 through -4 and
DEFERRED-136V-1 from the schema-authoring phase), `shared/identity.schema.json`
(`migration_epoch`), `shared/enums.schema.json` (`compatibility_mode`,
reused unchanged from `enums.py`'s existing `CompatibilityMode`),
`shared/limitations.schema.json` (`authority_disclosure`, `limitations`),
and the existing shared-core and prior record-family model source
(`src/pcae/cltr/authority/*.py`), in particular `bindings.py`'s
`FinalizationReceiptAuthorityBinding` (the closest existing precedent for
a mode-gated conditional field plus a mode-gated `authority_disclosure`
restriction) and `opaque.py`'s `OpaqueJsonValue` (already anticipating
`CompatibilityState.retirement_state` in its own module docstring,
written during Phase 136Z's shared-core groundwork).

## 3. Confirmed starting state (re-verified this phase)

- Previous authoritative phase: 136AQ (Independent Verification of
  `FinalizationReceiptAuthorityBinding`), commits `af9a0eaa`/`d04e77bb`.
- Fourteen record-family models present in the authority package prior
  to this phase: `AuthorityEpoch`, `AuthorityState`, `CutoverRequest`,
  `ReadinessPackage`, `HumanAuthorization`, `CutoverCandidate`,
  `Certification`, `PublicationAttempt`, `PublicationEvidence`,
  `ConcurrencyConflict`, `RecoveryJournalEntry`,
  `NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
  `FinalizationReceiptAuthorityBinding`. Confirmed by direct AST walk of
  `src/pcae/cltr/authority/*.py` before any edit in this phase.
- `CompatibilityState` and `QuarantineRecord` both absent, confirmed by
  the same walk.
- Runtime state confirmed Observed / observe / unavailable via
  `pcae runtime` prior to this phase's edits.

## 4. What was implemented

`src/pcae/cltr/authority/compatibility_quarantine.py` (new module):
`CompatibilityState`, a frozen dataclass, plus its record-local
`CompatibilityRole` enum (`{compatibility, historical}`, a local
2-value restatement of the shared 7-value `AuthorityRole`, per
NON-BLOCKING-136V-2). Fields, derived directly from the live schema's
`required`/`properties`/`$defs`: the 7 universal envelope fields
(`RecordEnvelope`), `migration_epoch` (`MigrationEpochToken`, always
required per Sec.7.2's universal rule — `compatibility_state` is exempted
from `phase_id`/`transition_id` but not from `migration_epoch`, per
NON-BLOCKING-136V-1), `component` (bounded free-text, 1-256 printable
ASCII characters), `role` (`CompatibilityRole`), `allowed_reads` (array
of bounded free-text path strings, max 64 items, each 1-512 characters,
forbidding the literal `..` substring and C0/C1 control characters),
`forbidden_authority_use` (schema-pinned `const: true`), `fallback_disabled`
(plain boolean), `mode` (the pre-existing shared `CompatibilityMode` enum
from `enums.py`, reused unchanged — the schema `$ref`s the same shared
6-value enum, not a record-local restatement), `retirement_state`
(conditionally required iff `mode == 'legacy_retired'`, forbidden
otherwise; represented as `OpaqueJsonValue` pinned to accept only `{}`,
per DEFERRED-136V-1 — the frozen contract gives this field no type at
all, so the schema itself pins it to an empty-shape placeholder,
enforced at the field's own construction site exactly as
`FinalizationReceiptAuthorityBinding.staleness_check` was in Phase 136AP
for the analogous DEFERRED-136T-1 gap), `limitations`, and
`authority_disclosure` — the last locally restricted so
`authority_role != 'authoritative'` unconditionally (Sec.9's 12-file
list), and further restricted to `{historical, compatibility}` whenever
`mode` is `legacy_historical`, `legacy_disabled`, or `legacy_retired`
(Sec.16, NON-BLOCKING-136V-3) — with no restriction invented for the
other three `mode` values beyond the unconditional "not authoritative"
rule (anti-strengthening). `_extensions` is Tier 2 (string-valued map
only, Sec.14), matching every prior Tier-2 family's pattern.

`src/pcae/cltr/authority/__init__.py`: exports `CompatibilityState` and
`CompatibilityRole`, added to `__all__` under a new "Group 10" section
following the file's established per-group sectioning.

No RecordReference-typed field exists on `CompatibilityState` — the
schema declares none (`component` is bare shape-checked free text, not a
reference; Sec.34 explicitly disclaims verifying the named component
exists) — so no reference-lookup, cross-family restriction, or
`schema_id`/`schema_version`-on-a-reference logic was needed for this
family, unlike every binding-family predecessor.

No Blocking, non-Blocking, or Deferred defect was independently
demonstrated against any shared-core primitive this phase; `opaque.py`
already anticipated this exact field (see Sec.2 above) and required no
change.

## 5. Test suite

New dedicated module
`tests/test_cltr_authority_136ar_compatibility_state.py` (118 tests: 115
fast + 3 packaging, all passing), independently fixtured directly from
the live executable schema — not from any earlier record-family test
module's fixture helpers. Covers: exact field inventory and discriminator
match against the live schema; exact `schema_id`/`schema_version`
requirements (missing, wrong, unsupported); every required field missing
individually; the `mode`/`retirement_state` conditional in both
directions (`legacy_retired` requires it, every other mode forbids it
even when present and schema-valid-shaped); the `mode`/
`authority_disclosure.authority_role` conditional in both directions,
parametrized across all 4 disallowed roles under each of the 3
restricting modes, and an explicit anti-strengthening sweep confirming
all 6 non-authoritative roles remain permitted under each of the 3
unrestricted modes; the unconditional `authority_role != 'authoritative'`
rule; the `forbidden_authority_use` const-true pin; `component` and
`allowed_reads` bound/pattern enforcement (empty, over-length, non-ASCII,
`..`-substring, control characters, over-count); `CompatibilityRole` and
`CompatibilityMode` enum strictness; `_extensions` Tier-2 behavior
(reserved-key collision, non-string value, explicit null, absence);
`retirement_state` opaque round-trip and its DEFERRED-136V-1 empty-shape
pin; structural equality, no-identifier-only-equality, recursive
immutability, and construction-input-mutation isolation; the full
no-compatibility-engine / no-quarantine / no-authority-activation /
no-reference-lookup symbol and import scan; no-network / no-subprocess /
no-filesystem-write side-effect checks; own-module scope guard (exactly
`CompatibilityState`, `QuarantineRecord` still absent); fresh wheel/sdist
build; and an isolated venv installation exercise (construct, round-trip,
and confirm `QuarantineRecord` is not importable) outside the repository
working tree.

## 6. Inherited "narrowing guard" updates (expected, matching precedent)

Following the established per-phase pattern (Phase 136AL/AN/AP each
narrowed prior chapters' still-forbidden-name guards), sixteen earlier
test modules' `LATER_GROUP_MODEL_NAMES`-equivalent tuples (`test_cltr_authority_136z_shared_core.py`
through `test_cltr_authority_136aq_finalization_receipt_authority_binding_independent.py`)
had `"CompatibilityState"` removed from their still-forbidden list, each
with an appended "Narrowed further by Phase 136AR" comment documenting
the change; `"QuarantineRecord"` remains forbidden everywhere, unchanged.
`test_cltr_authority_136z_shared_core.py`'s and
`test_cltr_authority_136aa_shared_core_independent.py`'s module-inventory
and packaging-file-list assertions gained `compatibility_quarantine.py`
as a now-expected file. Four independent-companion modules'
`test_*_no_forbidden_family_source_file_exists` guards (136AK, 136AM,
136AO, 136AQ), which asserted `compatibility_quarantine.py` must not yet
exist on disk, were narrowed to assert the module now legitimately
exists instead — the same "expected scope-guard evolution" the operator
prompt names, not a production regression repair. This is expected scope
narrowing, not opportunistic cleanup: only tuples/assertions whose literal
truth value flipped because `CompatibilityState` is now a legitimately
implemented class were touched; docstring/prose mentions of
`CompatibilityState` as a forward reference were left as-is (they remain
accurate historical statements about the phase in which they were
written).

## 7. Findings disclosed this phase

None. No Blocking, non-Blocking, or Deferred defect was independently
demonstrated in any shared-core primitive or prior record-family model
this phase.

## 8. Regression

`test_cltr_authority_136*` together: 2351 passed / 2 failed / 1 skipped
(`-m "not slow"`) — both failures pre-existing/inherited stale
wheel-content guards (`test_136ab_wheel_contains_authority_core_module`,
`test_136ad_wheel_contains_request_readiness_module`), independently
reproduced byte-for-byte identical against the 136AQ baseline commit
(`35b4f5ec`) before this phase's edits, confirming zero new regression.
Thirteen additional `-m slow` wheel-content-guard failures across the
136AG/AH/AI/AJ/AK/AL/AM/AN/AO/AP/AQ/Z modules were likewise independently
reproduced identically against the same 136AQ baseline (all failing on
an already-present `bindings`/`recovery`/`request_readiness` entry before
ever reaching the `compatibility_quarantine` check in the same forbidden
tuple) — the "known inherited category: stale wheel-content guard
failures" the governed task itself names; none repaired, per the
Blocking Repair Policy's "do not repair unrelated inherited failures."
Fast Green: 4391 passed, 0 failed, matching the 136AM/136AO/136AP/136AQ-
recorded baseline exactly. Bounded quick-tier sweep
(`-m "not slow and not phase_closure"`): 23697 passed / 25 failed / 9
skipped. All 25 failures independently classified: two are the same
pre-existing authority wheel-content guards named above; two
(`test_136m_no_typed_authority_model_module_exists`,
`test_136u_no_runtime_code_references_group10_families_outside_schema_resources`)
are pre-existing stale 136M/136U schema-layer scope guards, confirmed
unrelated to this phase by removing `compatibility_quarantine.py` and
re-running — `test_136m_...` fails identically on `ConcurrencyConflict`
(a Group-6 family from Phase 136AJ) with the module absent, and
`test_136u_...` fails on `bindings.py`/`enums.py` only, never
mentioning `compatibility_quarantine.py`; the remaining 21 fall in the
operator prompt's own named inherited categories (advisory-runtime-
directory baseline, 134E.5/134E.8 rendering and architecture-status
baselines, 134E.10 finalization-transaction baseline, 135O/135P
migration-evidence baseline, bootstrap-TODO staleness). Zero new
failures attributable to this phase. Fresh wheel/sdist build plus
isolated venv installation (outside the repository working tree)
confirmed all fifteen record-family models import, construct, and
round-trip correctly, with `QuarantineRecord` confirmed not importable.

## 9. No-go confirmation

- `QuarantineRecord` was not implemented (confirmed via AST class-name
  scan across the entire authority package, and via
  `pytest.raises(AttributeError): auth.QuarantineRecord`).
- No quarantine capability, compatibility engine, compatibility resolver,
  version negotiation, migration execution, record transformation, or
  schema conversion was introduced (confirmed via forbidden-symbol AST
  scan and forbidden-import AST scan of `compatibility_quarantine.py`).
- No runtime compatibility decision, artifact inspection, reference
  lookup, authority activation, or lifecycle mutation was introduced.
- No legacy authority demotion or CLTR authority activation occurred.
- No production runtime module (`pcae.commands`, `pcae.core`,
  `pcae.runtime`, sibling CLTR runtime modules) imports
  `pcae.cltr.authority` (confirmed via source-text and AST import scan).
- Runtime remains Observed / observe / unavailable (confirmed via
  `pcae runtime` after this phase's edits).

## 10. Telegram finalization evidence

Recorded via the governed `pcae phase complete` / `pcae task transition`
finalization path; see `.pcae/phase-completion-report.md` and
`.pcae/phase-completion-metadata.json` for the canonical machine-readable
record of this phase's completion, matching this document's phase
identifier and result.

## 11. Verdict

**COMPATIBILITYSTATE MODEL IMPLEMENTED — READY FOR INDEPENDENT
VERIFICATION.** Exactly one new record-family model implemented
(`CompatibilityState`); `QuarantineRecord` remains absent; the authority
package now exposes exactly fifteen record-family models. No Blocking
defect found or repair required this phase.

## 12. Recommended next phase

**136AS — Stage 3 Typed Authority Model CompatibilityState Independent
Verification.** Per governed instruction, Phase 136AS was not begun in
this phase.
