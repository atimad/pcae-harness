# Phase 136AT: Stage 3 Typed Authority Model QuarantineRecord Implementation

## 1. Purpose and boundaries

This phase implements Typed Model Implementation Group 11 of the frozen
`136Y` plan (`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
Sec.4/Sec.30, package layout Sec.7): exactly one record-family model,
`QuarantineRecord`, schema-backed by
`src/pcae/schema_resources/cltr_cutover/records/quarantine_record.schema.json`
(Phase 136V, Implementation Group 11 of the schema-authoring chapter).
`QuarantineRecord` is added to the existing
`src/pcae/cltr/authority/compatibility_quarantine.py` module alongside
`CompatibilityState` (Phase 136AR) — the module's other, already-
implemented occupant per the 136Y plan's file layout.
`QuarantineRecord` is the sixteenth and final Stage 3 record-family
model; after this phase every Stage 3 record-family model is
implemented.

`QuarantineRecord` is a descriptive, immutable, schema-backed typed
representation only. Per the live schema's own description: "A
QuarantineRecord document describes a claimed current-authority-
integrity failure for a named object; it never itself moves, renames,
deletes, releases, repairs, or blocks execution of an artifact, revokes
authority, mutates lifecycle state, or triggers a
notification/marker/receipt." It does not implement quarantine storage,
quarantine commands, quarantine lifecycle transitions, quarantine policy
or eligibility evaluation, quarantine release/deletion/restoration
behavior, quarantine reconciliation, artifact inspection, reference
lookup/resolution, publication or lifecycle blocking, remediation or
rollback execution, or authority activation/transfer/demotion. Legacy
lifecycle remains the sole production authority; CLTR remains
derivative. Runtime remains Observed / observe / unavailable, unchanged
by this phase.

## 2. Binding sources

Precedence followed (identical structure to every prior phase in this
chapter): frozen primary contract (`CLTR-CUTOVER-001`,
`CLTR-CUTOVER-SCHEMAS-001` v1.0, `CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001`
v1.0 Sec.30/Sec.46) -> verified contract -> verified architecture
(Phase 136B) -> verified 136Y implementation plan -> verified
136Z/.../136AS shared core and prior record-family models -> this
governed 136AT task contract -> operator prompt. No conflict was found
between the operator prompt and the frozen contract requiring a
discrepancy disclosure.

Consulted directly: the 136Y plan, the executable schema
(`quarantine_record.schema.json`, which itself carries an extensive
inline provenance block disclosing NON-BLOCKING-136V-5 (the
`quarantine_reason`-versus-`reason_code` field-name discrepancy,
resolved in favor of `reason_code` per the field-table-literalism rule)
and NON-BLOCKING-136V-6 (no `object_type`-to-`record_family` conditional
invented, since `object_type`'s `generation` value has no corresponding
`record_family` enum member) from the schema-authoring phase),
`shared/references.schema.json` (`record_reference`, the plain,
unrestricted shape — already implemented as `RecordReference` in
`references.py`), `shared/failures.schema.json` (`reason_code`, the
shared 24-value enum — already implemented as `ReasonCode` in
`enums.py`), `shared/identity.schema.json` (`migration_epoch`),
`shared/limitations.schema.json` (`authority_disclosure`, `limitations`),
and the existing shared-core and prior record-family model source
(`src/pcae/cltr/authority/*.py`), in particular `bindings.py`'s
`_record_reference_from_dict`/`_require_cross_family_reference_fields`
helpers (the closest existing precedent for constructing a
`RecordReference` from a wire payload) and `compatibility_quarantine.py`'s
own `CompatibilityState` (the closest existing precedent for a
module-local Tier-2 record family with an unconditionally-forbidden
`authority_role == 'authoritative'` restriction).

## 3. Confirmed starting state (re-verified this phase)

- Previous authoritative phase: 136AS (Independent Verification of
  `CompatibilityState`), commits `bea5fab1`/`1e7c1c0c`/`6bf4a792`/`88663b37`.
- Fifteen record-family models present in the authority package prior
  to this phase: `AuthorityEpoch`, `AuthorityState`, `CutoverRequest`,
  `ReadinessPackage`, `HumanAuthorization`, `CutoverCandidate`,
  `Certification`, `PublicationAttempt`, `PublicationEvidence`,
  `ConcurrencyConflict`, `RecoveryJournalEntry`,
  `NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
  `FinalizationReceiptAuthorityBinding`, `CompatibilityState`. Confirmed
  by direct AST walk of `src/pcae/cltr/authority/*.py` before any edit
  in this phase.
- `QuarantineRecord` absent, confirmed by the same walk and by
  `pytest.raises(AttributeError): auth.QuarantineRecord` (both later
  updated by this phase, as expected).
- `RecordFamily.QUARANTINE_RECORD` and every `ReasonCode` value already
  present in the shared `enums.py` (naming the slug/vocabulary does not
  imply an implemented class).
- Runtime state confirmed Observed / observe / unavailable via
  `pcae runtime inspect` prior to this phase's edits.

## 4. What was implemented

`src/pcae/cltr/authority/compatibility_quarantine.py` (existing module,
extended): `QuarantineRecord`, a frozen dataclass, plus its two
record-local enums, `ObjectType` (4 values:
`{generation, publication_attempt, authority_state, compatibility_state}`)
and `QuarantineState` (4 values:
`{quarantined, under_review, released, permanently_retired}`). Fields,
derived directly from the live schema's `required`/`properties`/`$defs`:
the 7 universal envelope fields (`RecordEnvelope`), `migration_epoch`
(`MigrationEpochToken`, always required per Sec.7.2's universal rule —
`quarantine_record` is not in the `phase_id`-required or
`transition_id`-required family lists, but is not exempted from
`migration_epoch`), `object_type` (`ObjectType`), `object_reference`
(`RecordReference`, the plain shared `record_reference` shape with *no*
per-`object_type` `record_family` restriction — NON-BLOCKING-136V-6:
`object_type`'s `generation` value has no corresponding `record_family`
enum member, making a uniform conditional restriction structurally
impossible for every branch, so none is invented here; verified both by
constructing every `(object_type, record_family)` combination, including
deliberately mismatched ones, and by an explicit schema-text assertion
that `properties.object_reference` is the bare `$ref` with no `allOf`
wrapper), `reason_code` (the shared `ReasonCode` enum, reused unchanged
from `enums.py`), `state` (`QuarantineState`), `limitations`, and
`authority_disclosure` — the last locally restricted so
`authority_role != 'authoritative'` unconditionally (Sec.9's 12-file
list; "quarantine becoming authority" is the specific prevention named
in Sec.30), with **no other conditional**: Sec.16's own
conditional-validation table lists no other within-document conditional
for this family beyond the unconditional `reason_code` requirement (itself
already enforced via the top-level `required` list), so no
release-evidence, expiry, or retained-state field prohibition was
invented, matching the schema's own explicit disclaimer that such
conditionals are "not contract-defined anywhere in Sec.16 or Sec.30."
`_extensions` is Tier 2 (string-valued map only, Sec.14), matching every
prior Tier-2 family's pattern.

A local `_quarantine_record_object_reference_from_dict` helper
constructs `RecordReference` from the wire payload with no
`required_family` restriction (`None`), and independently re-derives
`schema_id`/`schema_version` optional-field validation (bounded string /
`MAJOR.MINOR` pattern) rather than importing `bindings.py`'s private
helpers — matching every sibling module's own precedent of owning its
Layer-3 construction boilerplate locally. `schema_id`/`schema_version`
on `object_reference` are optional, not unconditionally required: unlike
`bindings.py`'s `marker_reference`/`receipt_reference` sites (which
apply a documented, field-specific cross-family-required rule), the live
`quarantine_record.schema.json` schema itself declares no such
requirement on `object_reference` (`shared/references.schema.json`'s own
`record_reference` `$def` lists only `record_id`/`record_digest`/
`record_family` as required), so no such rule is invented here
(anti-strengthening, verified by an explicit test constructing a valid
`object_reference` with `schema_id`/`schema_version` both absent).

`src/pcae/cltr/authority/__init__.py`: exports `QuarantineRecord`,
`ObjectType`, and `QuarantineState`, added to `__all__` under a new
"Group 11" section following the file's established per-group
sectioning; the package module docstring updated to record that every
Stage 3 record-family model is now implemented.

No Blocking, non-Blocking, or Deferred defect was independently
demonstrated against any shared-core primitive this phase; `RecordReference`,
`ReasonCode`, and `RecordFamily.QUARANTINE_RECORD` were all already
correctly shaped for this use with no change required.

## 5. Test suite

New dedicated module
`tests/test_cltr_authority_136at_quarantine_record.py` (118 tests, all
fast — no `slow`-marked packaging test failed when exercised), independently
fixtured directly from the live executable schema — not from any
earlier record-family test module's fixture helpers, and not importing
Phase 136AR/136AS/136V/136W fixtures or expectations. Covers: exact
field inventory and discriminator match against the live schema; exact
`schema_id`/`schema_version` requirements (missing, wrong, unsupported);
every required field missing individually; the full `object_type` x
`reason_code` x `state` enum inventories (every value of each
constructs and round-trips); the `object_type`/`object_reference.record_family`
independence anti-strengthening sweep (six combinations, including
mismatched ones, e.g. `object_type="generation"` paired with
`record_family="quarantine_record"`); `object_reference` construction
with and without the optional `schema_id`/`schema_version` cross-family
fields; malformed/missing `object_reference` sub-fields (missing
`record_family`, malformed digest, unknown `record_family` value,
unknown extra key, malformed `schema_version`); the unconditional
`authority_role != 'authoritative'` rule plus an anti-strengthening
sweep confirming all 6 non-authoritative roles remain permitted;
structural equality, no-identifier-only/no-state-only/no-digest-only
equality, recursive immutability, construction-input-mutation isolation,
and deserialized-output-mutation isolation; the full
no-quarantine-operation / no-reference-lookup / no-authority-activation
/ no-lifecycle-mutation symbol and import scan (against the operator
prompt's full 24-name forbidden-symbol list); no-network /
no-subprocess / no-filesystem-write side-effect checks; a valid-but-
nonexistent-reference construction with no lookup; full
`CompatibilityState` regression protection (construction, round-trip,
known-keys set, retirement_state conditional, role enum, forbidden-
authoritative-role rejection, immutability, and export presence, all
re-asserted unchanged); own-module scope guard (exactly
`CompatibilityState` and `QuarantineRecord`, all sixteen families present
package-wide, no seventeenth invented); fresh wheel/sdist build; and an
isolated venv installation exercise (construct and round-trip both
`CompatibilityState` and `QuarantineRecord`) outside the repository
working tree.

## 6. Inherited "narrowing guard" updates (expected, matching precedent)

Following the established per-phase pattern (Phase 136AL/AN/AP/AR each
narrowed prior chapters' still-forbidden-name guards), every earlier
test module's `LATER_GROUP_MODEL_NAMES`-equivalent tuple
(`test_cltr_authority_136z_shared_core.py` through
`test_cltr_authority_136as_compatibility_state_independent.py`, plus the
sibling `<N>_MUST_NOT_EXIST_RECORD_FAMILIES` variants in the
`-independent` verification modules and `TWO_MUST_NOT_EXIST_RECORD_FAMILIES`
in `test_cltr_authority_136aq_finalization_receipt_authority_binding_independent.py`)
had `"QuarantineRecord"` removed from its still-forbidden list — now
empty in every case, since `QuarantineRecord` was the last remaining
later-group name — each with an appended "Narrowed further by Phase
136AT" comment documenting the change. `test_cltr_authority_136ar_compatibility_state.py`'s
and `test_cltr_authority_136as_compatibility_state_independent.py`'s
own module-inventory, public-export, and own-module-scope-guard
assertions (previously proving `QuarantineRecord` absent from
`compatibility_quarantine.py`) were flipped to assert it is now present,
each narrowly, with the substantive regression coverage for
`CompatibilityState` left unchanged. `test_cltr_authority_136ai_publication_independent.py`'s
`test_forward_reference_to_unimplemented_family_accepted_no_resolution`
(which used `quarantine_record` as its illustrative "not yet
implemented" forward-reference example) was narrowed to no longer
assert `QuarantineRecord`'s absence, while preserving the substantive
property under test — a `record_reference` never triggers dynamic class
resolution regardless of the referenced family's own implementation
status. This is expected scope narrowing, not opportunistic cleanup:
only tuples/assertions whose literal truth value flipped because
`QuarantineRecord` is now a legitimately implemented class were touched;
docstring/prose mentions of `QuarantineRecord` as a forward reference
were left as-is where they remain accurate historical statements about
the phase in which they were written (e.g. `bindings.py`'s own
module docstring, which correctly states neither `CompatibilityState`
nor `QuarantineRecord` is implemented *in that module*).

## 7. Findings disclosed this phase

None. No Blocking, non-Blocking, or Deferred defect was independently
demonstrated in any shared-core primitive or prior record-family model
this phase.

## 8. Regression

`test_cltr_authority_136*`/`test_cltr_cutover_136*` together (`-m "not slow"`):
4578 passed / 4 failed / 9 skipped. All four failures pre-existing/
inherited, independently reproduced identically against the 136AS
baseline commit (`88663b37`) before this phase's edits (confirmed via
`git stash`): `test_136ab_wheel_contains_authority_core_module` and
`test_136ad_wheel_contains_request_readiness_module` (stale
wheel-content guards, already failing due to `compatibility_quarantine.py`'s
Phase-136AR-era presence, unrelated to this phase's own
`QuarantineRecord` addition), and
`test_136m_no_typed_authority_model_module_exists` /
`test_136u_no_runtime_code_references_group10_families_outside_schema_resources`
(the operator prompt's own named "stale 136M/136U schema-layer scope
guard" inherited category). Zero new regressions. Fast Green
(`-m "not slow"`, full repository): matches the 136AS-recorded baseline
plus this phase's own 118 new tests, with the same four pre-existing
failures and no new ones. Fresh wheel/sdist build plus isolated venv
installation (outside the repository working tree) confirmed all
sixteen record-family models import, construct, and round-trip
correctly, with `QuarantineRecord` now importable and `CompatibilityState`
behavior unchanged.

## 9. No-go confirmation

- No quarantine storage, quarantine command, quarantine lifecycle
  transition, quarantine policy/eligibility evaluation, quarantine
  release/deletion/restoration behavior, or quarantine reconciliation
  was introduced (confirmed via forbidden-symbol AST scan of
  `compatibility_quarantine.py` against the operator prompt's full
  24-name forbidden-symbol list).
- No artifact inspection or reference lookup/resolution was introduced
  — a syntactically valid but nonexistent `object_reference` constructs
  successfully with no filesystem/repository access.
- No publication-blocking, lifecycle-blocking, remediation-execution, or
  rollback-execution behavior was introduced.
- No authority activation, resolution, comparison, or transfer, and no
  legacy authority demotion or CLTR authority activation, occurred.
- No lifecycle mutation (phase closing, task closing, report promotion,
  completion-metadata mutation) was introduced by the *production*
  module; the governed task/phase-report lifecycle itself was completed
  through the standard `pcae task`/`pcae phase-report`/`pcae phase
  complete` commands, not by direct file substitution.
- No production runtime module (`pcae.commands`, `pcae.core`,
  `pcae.runtime`, sibling CLTR runtime modules) imports
  `pcae.cltr.authority` (confirmed via source-text and AST import scan).
- `compatibility_quarantine.py` imports no operational quarantine code,
  no filesystem-mutation utility (`pathlib`/`os`/`shutil` writes),
  `subprocess`, `socket`, `requests`/`urllib`, or `smtplib` (confirmed
  via a full transitive import listing of the module).
- Runtime remains Observed / observe / unavailable (confirmed via
  `pcae runtime inspect` after this phase's edits).

## 10. Telegram finalization evidence

Recorded via the governed `pcae phase complete` / `pcae task transition`
finalization path; see `.pcae/phase-completion-report.md` and
`.pcae/phase-completion-metadata.json` for the canonical machine-readable
record of this phase's completion, matching this document's phase
identifier and result.

## 11. Verdict

**QUARANTINERECORD MODEL IMPLEMENTED — READY FOR INDEPENDENT
VERIFICATION.** Exactly one new record-family model implemented
(`QuarantineRecord`); the authority package now exposes exactly sixteen
record-family models — every Stage 3 record-family model is now
implemented. No Blocking defect found or repair required this phase.

## 12. Recommended next phase

**136AU — Stage 3 Typed Authority Model QuarantineRecord Independent
Verification.** Per governed instruction, Phase 136AU was not begun in
this phase.
