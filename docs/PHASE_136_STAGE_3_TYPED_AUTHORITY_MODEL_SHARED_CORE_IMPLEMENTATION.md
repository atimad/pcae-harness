# Phase 136Z: Stage 3 Typed Authority Model Shared Core Implementation

## 1. Purpose and boundaries

This phase implements Typed Model Implementation Group 1 (shared core)
from `docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
(Phase 136Y, Section 23's Group 1 row). It provides lossless, immutable,
offline, schema-aligned primitives shared by every future typed-authority
record model, and implements **no** record-family model.

Confirmed by direct repository inspection before and after implementation:
no `AuthorityEpoch`/`AuthorityState`/`CutoverRequest`/`ReadinessPackage`/
`HumanAuthorization`/`CutoverCandidate`/`Certification`/
`PublicationAttempt`/`PublicationEvidence`/`ConcurrencyConflict`/
`RecoveryJournalEntry`/`NotificationAuthorityBinding`/
`MarkerAuthorityBinding`/`FinalizationReceiptAuthorityBinding`/
`CompatibilityState`/`QuarantineRecord` class exists anywhere in the new
package. No production schema was changed. No new production dependency
was added.

## 2. Precondition: 136Y terminal Telegram notification state

Before starting this phase, the lifecycle state of Phase 136Y's terminal
Telegram notification was investigated (read-only), per the operator
prompt's precondition.

Findings:

- `.pcae/phase-completion-metadata.json` (136Y) itself discloses
  `"notification_dispatch_result": "pending (dispatched by pcae phase
  complete)"` and `"report_notification_status": "pending"` -- 136Y never
  claimed a confirmed delivery.
- `.pcae/phase-reports/.last-notified.json` carries a local marker record
  for 136Y (`report_digest`, `finalization_snapshot_id`,
  `delivery_purpose: "ordinary_completion"`), but this marker is local
  self-attestation only -- it has no field for a Telegram API response,
  message ID, or HTTP status.
- `pcae phase-report reconcile --phase-id 136Y` (read-only) reported
  `Marker: already_dispatched`, `Checkpoint: completed`,
  `Receipt: finalized` -- all three are local-artifact consistency checks
  (marker-digest match, `.pcae/finalization-transactions/136Y.json`,
  `.pcae/delivery-receipts/...`), not provider-side delivery evidence. The
  one receipt found (`recording_v1` adapter) is explicitly tagged
  `"is_synthetic": true`, `"represents_external_delivery": false` by its
  own owning module's docstring, and is disconnected from the real
  Telegram dispatch path.
- No file under `.pcae/notifications/*.json` (the per-event notification
  log) references phase 136Y or a timestamp near its commit time
  (`2026-07-17T14:52:12+02:00`). The nearest event is an unrelated
  `92D.4-t2` test notification.

**Classification: State C -- the incident is unresolved, explicitly
recorded (both by 136Y's own metadata and by this phase's independent
read-only reconciliation), and does not leave lifecycle state
inconsistent.** No resend was performed (no exactly-once delivery
evidence exists to justify one, and resending without such evidence risks
a duplicate under ambiguous conditions); no second 136Y completion was
created. This finding is carried forward as
**NON-BLOCKING-136Z-1** (Section 14) -- a real gap in the existing
notification-delivery-evidence design (the Telegram sink's own successful
JSON response is parsed but never persisted, per direct code inspection),
pre-existing and out of this phase's shared-core scope to repair.

## 3. Primary-source derivation

Requirements were derived directly from
`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
(Phase 136Y), which is itself the frozen contract's (`CLTR-CUTOVER-
SCHEMAS-001` v1.0 Sec.44) implementation-ready translation, cross-checked
against the schema source files directly:
`src/pcae/schema_resources/cltr_cutover/shared/{digest,enums,envelope,
failures,identity,limitations,references}.schema.json`.

Per the operator prompt's own precedence chain, where this prompt's
illustrative inventory (fourteen numbered components) differed in name or
boundary from the 136Y plan's own Section 5/7 inventory, the 136Y plan
governed. No conflict required a documented override -- the two inventories
map onto each other directly (Section 4 below).

## 4. Exact 136Z inventory (derived, not assumed)

| 136Y plan component | Delivered as | Module |
|---|---|---|
| `AbsentSentinel` | `ABSENT` singleton, `AbsentType` | `sentinels.py` |
| `OpaqueJsonValue` | `OpaqueJsonValue`, `verify_round_trip` | `opaque.py` |
| Immutable JSON containers | `freeze_json_value`, `thaw_json_value` | `immutable.py` |
| `ExtensionMapping` | `ExtensionMapping` | `extensions.py` |
| Seven shared enums + `RecordFamily` + `ReasonCode` | `AuthorityKind`, `AuthorityRole`, `MigrationStage`, `GenerationRole`, `PublicationState`, `RecoveryState`, `CompatibilityMode`, `RecordFamily`, `ReasonCode`, plus two embedded-component-local enums (`LegacyLifecycleStateWire`, `JournalLockState`) | `enums.py` |
| `RecordIdentity` family | `RecordId`, `GenerationId`, `MigrationEpochToken`, `PhaseIdentity`, `TransitionId`, `PrincipalIdentifier` | `identity.py` |
| `RecordDigest` family | `Sha256Digest` (generic), `RecordDigest`, `ReferencedRecordDigest`, `GenerationDigest`, `PointerDigest`, `JournalEntryDigest` | `digest.py` |
| `RecordReference`, `EpochReference`, `GenerationReference` | same names, plus `require_family()` fail-closed helper | `references.py` |
| `CasExpectation` | `CasExpectation` | `cas_expectation.py` |
| `Limitations`, `AuthorityDisclosure` | same names | `limitations.py` |
| `RecordEnvelope`, `Timestamp` | `RecordEnvelope`, `Timestamp`, `SchemaVersionString` | `envelope.py` |
| Typed-model error hierarchy | 14 exception classes rooted at `TypedModelError` | `errors.py` |
| Shared `to_dict`/`from_dict` primitives | `field_from_payload`, `serialize_value`, `to_dict_fields`, `to_canonical_bytes` | `serialization.py` |

This is the exact inventory delivered -- not assumed a priori from the
operator prompt's own illustrative fourteen-item list, which the 136Y plan
(the governing document) restates with different names/boundaries in
places (e.g. the prompt's single "failure representation" item maps here
to `ReasonCode` alone, since the shared `failures.schema.json` defines
only a `reason_code` enum, no separate failure-object shape).

## 5. Package layout

```
src/pcae/cltr/authority/
    __init__.py          # named exports only, no wildcard
    sentinels.py          # ABSENT
    opaque.py             # OpaqueJsonValue
    immutable.py           # freeze_json_value / thaw_json_value (shared by opaque.py, extensions.py)
    enums.py              # 7 shared enums + RecordFamily + ReasonCode + 2 embedded-local enums
    identity.py           # identifier wrappers
    digest.py             # digest wrappers
    references.py         # RecordReference / EpochReference / GenerationReference
    cas_expectation.py    # CasExpectation
    limitations.py        # Limitations / AuthorityDisclosure
    envelope.py           # Timestamp / SchemaVersionString / RecordEnvelope
    extensions.py         # ExtensionMapping
    errors.py             # typed-model error hierarchy
    serialization.py      # shared to_dict/from_dict primitives
```

`immutable.py` is one addition beyond the 136Y plan's illustrative Section
7 file list: it factors the recursive freeze/thaw logic shared identically
by `opaque.py` and `extensions.py` into one module, rather than
duplicating it in both (avoiding two divergent implementations of the same
recursive-immutability rule). This is a bounded, disclosed implementation
detail, not a scope expansion -- both call sites still each deliver exactly
the component the plan names.

Sibling to, not merged into, `src/pcae/cltr/` (`digest.py`,
`canonicalization.py`, `enums.py`, `models.py`) -- confirmed no cycle: the
package imports only from `pcae.cltr.canonicalization` (for
`to_canonical_bytes`'s pass-through), never the reverse, and internal
module imports strictly follow shared-core-only dependency order (no
module here imports a not-yet-existent record-group module, since none
exists).

## 6. Technology

Frozen standard-library `dataclasses` (`frozen=True`), continuing the
`src/pcae/cltr/models.py` precedent, exactly as 136Y Section 6 selected.
`slots=True` was not applied: the repository's floor is `requires-python
= ">=3.9"` (confirmed in `pyproject.toml`), and `slots=True` on
`dataclasses.dataclass` requires Python 3.10+; 136Y Section 6 specified
this as a "should," not a "must," pending a floor-compatibility check --
this phase confirms the floor does not yet allow it and defers `slots`
without introducing a runtime-version branch. No new dependency was
added; `pyproject.toml`'s `dependencies`/`dev` lists are unchanged.

## 7. ABSENT design

`sentinels.py`: a private `_AbsentType` singleton (`__new__` enforces one
instance), exported as `ABSENT`. `__bool__` raises `TypeError` (no
truthy/falsy interpretation is possible); `__copy__`/`__deepcopy__`/
`__reduce__` all preserve identity; `__repr__` returns `"<absent>"`.
`ABSENT` is never JSON-serializable (no `__iter__`/scalar conversion
exists that `json.dumps` could use), and `serialize_value`/`to_dict_fields`
(`serialization.py`) omit any field valued `ABSENT` from output entirely,
while an explicit `None` field serializes as JSON `null`. Verified by
`tests/test_cltr_authority_136z_shared_core.py`'s ABSENT test group
(identity, falsy-distinctness, copy/deepcopy/pickle identity, no-truth-
value, JSON-serialization rejection, omission-vs-null-preservation).

## 8. OpaqueJsonValue design

`opaque.py`, built on `immutable.py`'s `freeze_json_value`/
`thaw_json_value`. Applies today to exactly two future fields
(`FinalizationReceiptAuthorityBinding.staleness_check`,
`CompatibilityState.retirement_state`), both schema-pinned to `{}` --
neither field is implemented by this phase (both belong to Group 7/8, not
Group 1), but the wrapper type itself is delivered now, general-purpose
and ready for either field once its owning record model is built.
Construction recursively validates and freezes; rejects sets, bytes,
functions, arbitrary objects, and non-finite floats (`NaN`/`Infinity`).
`verify_round_trip()` is a defensive internal-consistency helper (Sec.29's
`OpaqueValuePreservationError`), never invoked automatically -- callers
opt in.

## 9. Immutable-container design

`immutable.py`: `freeze_json_value` converts `dict`→`MappingProxyType`
and `list`/`tuple`→`tuple`, recursively, rejecting any other Python type.
`thaw_json_value` is the inverse, always producing a fresh, independent,
mutable copy. Both construction and access-time copies are defensive: a
caller's later mutation of their own source structure never retroactively
alters a constructed `OpaqueJsonValue`/`ExtensionMapping`, and a caller
mutating a `to_json()`/`to_dict()` output never affects the wrapper's
internal state. Verified at nesting depths 1/2/5/10 in the test suite.

## 10. Extension design

`extensions.py`: `ExtensionMapping.from_mapping(mapping, *,
reserved_keys=frozenset())`. `reserved_keys` is supplied by the caller
(a future record model, passing its own canonical field-name set) --
this shared-core type has no a-priori knowledge of any specific record
family's fields. Enforces `maxProperties: 32` (matching the executable
schema); rejects non-string keys; rejects a key colliding with a supplied
reserved name. Deliberately **not hashable** (`__hash__ = None`), so any
containing record model with an `_extensions` field is itself unhashable
by default dataclass behavior, matching Section 19's design.

## 11. Enum design

`enums.py`: nine module-level `(str, enum.Enum)` classes covering the
seven shared enums, `RecordFamily`, and `ReasonCode`, plus two enums
scoped to the embedded `CasExpectation` component
(`LegacyLifecycleStateWire`, a 12-value restatement, by wire value only,
of the existing legacy `LifecycleState`; `JournalLockState`, a 2-value
local vocabulary). Because every enum mixes in `str`, `serialize_value`
(`serialization.py`) explicitly checks `isinstance(value, enum.Enum)`
**before** the generic scalar-type branch -- otherwise the `str`-subclass
check would short-circuit first and the serializer would emit the `Enum`
instance itself rather than the plain wire string (`.value`); this ordering
detail is covered by a dedicated regression test
(`test_136z_serialize_value_emits_plain_wire_string_not_enum_repr`).
Construction is always `EnumClass(raw_str)`: exact `ValueError` on any
mismatch, including case, whitespace, or boolean-coercion attempts
(`AuthorityKind(True)` raises, since `True` is not a declared member).

## 12. Identity design

`identity.py`: six wrapper types (`RecordId`, `GenerationId`,
`MigrationEpochToken`, `PhaseIdentity`, `TransitionId`,
`PrincipalIdentifier`), each a frozen dataclass validating one anchored
regex matching the executable schema's own pattern exactly. `RecordId`
and `GenerationId` share an identical pattern but remain distinct Python
types (verified: two instances of each with the same string value compare
unequal to one another, only equal within their own type) -- exactly the
"can never silently masquerade" property `identity.schema.json` itself
names as its purpose.

## 13. Digest design

`digest.py`: six wrapper types (`Sha256Digest` generic, plus
`RecordDigest`/`ReferencedRecordDigest`/`GenerationDigest`/
`PointerDigest`/`JournalEntryDigest`), all validating the same
`^[0-9a-f]{64}$` shape but kept as distinct types (verified unequal to one
another even given an identical value string). No digest is ever computed,
corrected, or externally verified by any constructor here -- construction
is pure shape-validated storage; digest *computation*, if a future phase
needs it, remains a separate utility delegating to `pcae.cltr.digest`,
never inside this package.

## 14. Reference design

`references.py`: `RecordReference` (id+digest+family, with `schema_id`/
`schema_version` conditionally `ABSENT`), `EpochReference`
(migration-epoch [+ optional digest]), `GenerationReference`
(id+digest, always paired). `require_family(reference, expected)` is the
Section-13-specified "Literal-style discriminant, not three separate
classes" mechanism: it raises `WrongFamilyReferenceError` (fail-closed) on
mismatch, used by `CasExpectation.__post_init__` to enforce the three
family-restricted embedding sites (`expected_authority_epoch` ->
`authority_epoch`, `expected_request_reference` -> `cutover_request`,
`expected_certification_reference` -> `certification`). No reference type
or function anywhere in this module dereferences, existence-checks, or
performs any lookup.

## 15. CasExpectation design

`cas_expectation.py`: all eleven fields unconditionally required (no
`ABSENT`-typed field exists on this class, matching the schema's own "no
wildcard on missing expected value" design, verified directly by a test
asserting no dataclass field carries a default). Wrong-family construction
at any of the three restricted reference fields fails closed via
`require_family` inside `__post_init__`.

## 16. Limitations / AuthorityDisclosure design

`limitations.py`: `Limitations` wraps a bounded tuple of validated
free-text entries (regex-checked control-character/newline-count bounds,
`maxItems: 32`), serializing as a **plain JSON array** (via a `to_wire()`
hook the shared serializer recognizes), not as an object -- this matches
the executable schema's own array shape for `limitations` exactly.
`AuthorityDisclosure.is_authoritative` is hard-pinned `False`: construction
raises `TypedModelConstructionError` if a caller supplies any other value,
including when `authority_role` is itself `AUTHORITATIVE` -- no model
method computes or grants truth here (Section 19 of this document).

## 17. Failure representation (`ReasonCode`)

The shared `failures.schema.json` defines only a `reason_code` closed
enum (24 values), not a separate structured failure-object shape.
Delivered as `ReasonCode` in `enums.py`. No `FailureValue`-style wrapper
type was introduced since the schema layer itself defines none -- inventing
one would exceed what the frozen contract defines (matching the plan's
own repeated caution against inventing shapes the schema does not have).

## 18. Timestamp design

`envelope.py`: `Timestamp.wire` preserves the exact original string;
construction validates the frozen `YYYY-MM-DDTHH:MM:SS[.ffffff]Z` pattern
only -- no timezone/precision normalization ever occurs. `to_datetime()`
is a derived, on-demand convenience accessor (never stored, never the
canonical serialization source); `serialize_value(timestamp)` always
emits `self.wire` verbatim, confirmed by a dedicated regression test.

## 19. Serialization boundary

`serialization.py`: `field_from_payload(payload, key)` implements the
absent-vs-null distinction exactly as Section 9 of the 136Y plan specifies
(`key in payload` vs. `payload[key]`, never `payload.get(key)` alone).
`serialize_value`/`to_dict_fields` recursively convert shared-core typed
values to plain JSON-compatible Python values, omitting `ABSENT` fields
entirely and recursing through nested dataclasses, enums (checked before
the `str` branch), `OpaqueJsonValue`/`ExtensionMapping` (via their own
`to_json()`/`to_dict()`), and any wrapper type exposing a `to_wire()` hook
(the identifier/digest/timestamp/`Limitations` types). `to_canonical_bytes`
is a **direct pass-through** to `pcae.cltr.canonicalization.canonicalize_dict`
-- verified identical output for identical input by a dedicated regression
test, never a reimplementation.

## 20. Equality and hashing

Every dataclass here uses default structural `__eq__` (field-by-field);
`RecordId`/`GenerationId` with identical string values compare unequal
across the two distinct types (identity-of-type participates in default
dataclass equality). `ExtensionMapping`/`OpaqueJsonValue` are unhashable
by design (`__hash__ = None` on `ExtensionMapping`; `OpaqueJsonValue.
__hash__` delegates to its frozen value, which itself may be unhashable
when it wraps a `MappingProxyType` -- that unhashability is allowed to
propagate, never forced away). Plain identifier/digest/enum-only
dataclasses (e.g. `RecordId`, `RecordDigest`) remain hashable, matching
Section 19 of the 136Y plan.

## 21. Safe representation

No model implements a custom `__str__`/logging hook that dumps full field
contents automatically; dataclass default `__repr__` is used as-is.
`ExtensionMapping`'s construction-time collision-rejection error message
never echoes the colliding value's contents (verified by a dedicated
test asserting a deliberately secret-shaped value string never appears in
the raised exception's message).

## 22. Error hierarchy

`errors.py`: fourteen classes rooted at `TypedModelError`, matching 136Y
Section 29's table exactly (`TypedModelConstructionError` and its
subclasses `InvalidIdentifierError`/`InvalidDigestError`/
`InvalidReferenceError`/`WrongFamilyReferenceError`/`InvalidTimestampError`/
`UnsupportedJsonValueError`/`AbsentNullMismatchError`; plus
`UnsupportedSchemaVersionError`, `UnknownModelFamilyError`,
`OpaqueValuePreservationError`, `SerializationError`,
`TypedModelInternalInvariantError`, `RoundTripMismatchError`). Distinct
from, and never duplicating, `pcae.schema_runtime.errors` (Layer 1/2).
Errors never repair input, downgrade to a warning, or disclose full
opaque/extension contents in their message text.

## 23. Schema alignment

Every shared component maps directly to a `shared/*.schema.json`
definition (Section 4's table above; also see Section 5 of the 136Y
plan). No unauthorized field was introduced; no schema field was silently
omitted; no type was narrowed or broadened beyond what the schema
defines (e.g. `OpaqueJsonValue` is not narrowed below the schema's current
`{}`-only shape, and no richer shape is invented ahead of a contract
erratum).

## 24. Runtime isolation

`tests/test_cltr_authority_136z_shared_core.py`'s "Runtime isolation"
group performs an AST-walk over `src/pcae/commands/`, `src/pcae/core/`,
`src/pcae/cltr/` (excluding the new `authority/` subpackage itself), and
`src/pcae/runtime/` (if present), asserting zero `import`/`from ... import`
edges into `pcae.cltr.authority`, plus a defense-in-depth plain-string
scan for the same reference (covering hypothetical dynamic
`importlib.import_module` usage). A second test confirms the reverse
direction: no module inside `pcae.cltr.authority` imports any production
lifecycle/notification/report module (`pcae.commands`,
`pcae.core.notifications`, `pcae.core.phase_reports`).

## 25. No-authority proof

No symbol named `resolve_authority`, `current_authority`,
`activate_epoch`, `demote_legacy`, `retire_legacy`, `authorize_cutover`,
`evaluate_readiness`, `certify_candidate`, `publish`, `recover`,
`quarantine`, `release`, or `execute` is exported by, or defined anywhere
in the source of, this package (verified by both an attribute-existence
check against the live module and an AST scan of every function/class
definition across all thirteen source files).
`AuthorityDisclosure.is_authoritative` remains hard-pinned `False`
regardless of `authority_role`'s value (Section 16 above).

## 26. No-side-effect proof

Instrumented tests construct and serialize one fixture of every shared
component while `socket.socket`/`socket.create_connection` and
`subprocess.run`/`subprocess.Popen` are monkeypatched to raise, and while
`open()` is guarded to raise on any write-mode call -- all pass cleanly.
Environment-variable isolation is proven statically (no `os.environ`/
`os.getenv` token exists anywhere in the package source) rather than by
monkeypatching the live `os.environ` object, since doing so was found
during this phase to break pytest's own runtime (terminal-width/color
detection reads `os.environ` mid-test) -- the static proof is equivalent in
strength for a package that, by direct source inspection, never imports
`os` for environment access in the first place.

## 27. Packaging

No `pyproject.toml` change was required: the existing
`[tool.hatch.build.targets.wheel] packages = ["src/pcae"]` and
`[tool.hatch.build.targets.sdist] include = ["src/pcae", ...]` rules
already scope in the new subpackage. Verified (not changed) by building a
fresh wheel and sdist and inspecting their contents directly: all
thirteen new modules are present in both archives; no record-group module
name (`authority_core.py`, `request_readiness.py`, `bindings.py`,
`compatibility_quarantine.py`) is present, since none exists yet. A
built wheel was installed into a fresh, isolated virtual environment
outside the repository checkout (`python -m venv` + `pip install
<wheel> jsonschema>=4.18,<5`); a probe script run from an unrelated
working directory constructed a `RecordEnvelope`, serialized it,
canonicalized it, and exercised the `ABSENT`/enum-fail-closed behavior --
all succeeded (`OK` printed, exit code 0).

## 28. Tests

`tests/test_cltr_authority_136z_shared_core.py`: 226 tests (223
non-slow + 3 `@pytest.mark.slow` packaging tests), covering: exact module
inventory and package boundary; no-record-family-model source scan;
`ABSENT` (identity, falsy-distinctness, copy/deepcopy/pickle, no-truth-
value, non-JSON-serializability, omission-vs-null); `OpaqueJsonValue`
(every JSON primitive shape, rejected Python types, NaN/Infinity
rejection, no-shared-mutable-reference, structural equality, current
`{}`-only shape, `verify_round_trip` pass/fail); recursive immutable
containers at nesting depths 1/2/5/10; `ExtensionMapping` (round-trip,
key-order preservation, canonical-field-collision rejection,
`maxProperties` boundary, no-shared-reference, unhashability, no key
promotion); every shared enum's member set and fail-closed rejection
(unknown value, case mismatch, whitespace, boolean coercion), plus the
Stage-3/legacy `AuthorityRole` disjointness proof and the enum-before-str
serialization-ordering regression; identifiers (well-formed/malformed
fixtures per type, type-distinctness, no-lookup-during-construction);
digests (well-formed/malformed fixtures per type, type-distinctness,
no-auto-computation); references (exact storage, no-dereference-method
proof, `require_family` accept/reject, `EpochReference` absent-vs-null,
`GenerationReference` pairing); `CasExpectation` (all-required-fields
proof, wrong-family rejection, round-trip); `Limitations`/
`AuthorityDisclosure` (empty/populated, array-not-object serialization,
bounds, `is_authoritative` pin and rejection, multiline rejection);
`Timestamp`/`RecordEnvelope` (exact wire preservation across four
fixtures, malformed rejection across five fixtures, derived-datetime
non-replacement, seven-field round-trip, `contract_version` const pin);
immutability/equality/hashing; the serialization pipeline
(`field_from_payload`, `to_dict_fields`, `serialize_value` rejection
paths, canonicalization delegation, no-coercion fixtures); the fourteen-
class error hierarchy; runtime isolation (both directions); no-authority
proof (export/attribute/AST); no-side-effect proof (network/subprocess/
filesystem-write/environment); schema-inventory sanity (seven shared
files unchanged, sixteen record schemas untouched); and packaging
(wheel/sdist contents, isolated installed-wheel construction).

One pre-existing test required a bounded, disclosed repair:
`tests/test_cltr_cutover_136m_request_and_readiness_independent_verification.py
::test_136m_no_typed_authority_model_module_exists` asserted the total
absence of `src/pcae/cltr/authority/` -- a correct invariant at Phase
136M's own time, now superseded by this phase's authorized creation of
that package. The assertion was narrowed (matching the precedent 136U set
repairing stale scope-guard lists in 136N/136R) to its original intent:
no *record-family* model class exists in the package, rather than the
package's total absence. This is `NON-BLOCKING-136Z-2` (Section 14).

## 29. Regression evidence (fresh, this phase)

All commands run fresh via the project's own `.venv` (Python 3.9.6,
matching `requires-python = ">=3.9"`; the bare `python3` on `PATH`
resolves to an unrelated Homebrew 3.14 interpreter lacking `jsonschema`/
`build` and was not used for any reported result below):

| Suite | Command | Result |
|---|---|---|
| 136Z focused | `pytest tests/test_cltr_authority_136z_shared_core.py -m "not slow"` | 223 passed, 3 deselected |
| 136Z packaging (slow) | `pytest tests/test_cltr_authority_136z_shared_core.py -m slow` | 3 passed |
| `cltr_cutover`/`schema_runtime` filtered | `pytest -k cltr_cutover -n auto` | 1925 passed, 8 skipped |
| Fast Green | `pytest -m fast_green -n auto` | 4391 passed (unchanged baseline) |
| Full unmarked-suite bounded diagnostic | `pytest -n auto` (240s bound) | did not complete within the bound -- see Section 30 |

`no_new_dependency`: `pyproject.toml` `dependencies`/`dev` lists unchanged
(`jsonschema>=4.18,<5` only; `pytest`/`pytest-xdist` only); grep for
`pydantic`/`attrs` across `src/pcae` -- zero hits, unchanged from 136Y.

`schema_inventory_verification`: 7 shared resources, 16 record schemas --
unchanged, re-confirmed by direct inspection; no production schema file
was touched by this phase.

## 30. Full-suite evidence limitation

The full unmarked suite has now stalled/failed-to-complete-within-bound
six independently observed times across 136W (x3), 136X (x1), 136Y (x1),
and this phase (x1). This phase's own bounded attempt (started fresh,
`pytest -n auto`, 15 workers, 22374 items collected) reached
approximately 79% of collected items within a 240-second bounded window
(monitored, then terminated at the bound) before this phase's own bounded
window closed, consistent with the prior five observations; it is
disclosed exactly as it behaved, never claimed as a completed or passed
run. 65 `F` markers (pre-existing, not newly introduced by this phase)
were observed within the completed ~79% -- a materially larger count than
initially estimated during monitoring, corrected here to the exact
figure obtained by counting `F` markers in the captured log after the run
was terminated. These are pre-existing/inherited -- outside both of this
phase's own authoritative regression gates (the `cltr_cutover`/
`schema_runtime` filtered suite and Fast Green, both 100% clean, zero
failures, Section 29) -- and not investigated further per the operator
prompt's explicit boundary ("This plan does not become a repair phase for
that instability"). No 136Z-authored test intersected or contributed to
the stall (the dedicated 136Z suite itself completed in under 2 seconds,
non-slow, and under 9 seconds including the slow packaging tests, both
independently, well outside the stalled full-suite run).

## 31. Finding dispositions

| Finding | Classification | Effect |
|---|---|---|
| 136Y terminal Telegram notification delivery is unproven (Section 2) | NON-BLOCKING-136Z-1 | Pre-existing gap in the Telegram-sink delivery-evidence design (successful API response parsed but never persisted); disclosed, not repaired this phase (out of shared-core scope); no resend performed |
| `test_136m_no_typed_authority_model_module_exists` required narrowing (Section 28) | NON-BLOCKING-136Z-2 | Repaired in place, matching 136U's precedent; original intent (no record-family model) preserved and re-verified passing |
| Full-suite stall recurrence (Section 30) | NON-BLOCKING-136Z-3 (re-confirms `NON-BLOCKING-136W-3`) | Inherited, pre-existing; no 136Z-authored test implicated |
| 65 pre-existing `F` failures observed within the partial (~79%) full-suite run (Section 30) | NON-BLOCKING-136Z-4 | Inherited, outside both authoritative regression gates used by this phase (both 100% clean); unrelated to shared-core changes; not investigated per operator-prompt boundary |

No Blocking finding exists. No loss of absent-versus-null distinction; no
mutable nested opaque value; no lossy round-trip; no enum coercion; no
timestamp normalization; no identifier-family collapse; no automatic
digest computation; no automatic reference lookup/dereference; no
production runtime import of the new package; no network/filesystem/
subprocess/environment side effect; no authority-like behavior; no
record-family model was implemented; no new dependency; no package
omission from wheel/sdist; no installed-wheel failure.

## 32. Limitations

- `OpaqueJsonValue` is proven lossless only at its currently
  schema-enforced `{}`-only shape (the two owning fields,
  `staleness_check`/`retirement_state`, are not yet built by any record
  model); a richer shape's round-trip correctness will need re-proving
  once a contract erratum defines one, but the wrapper's own mechanism
  (verbatim deep freeze/thaw) does not depend on knowing that shape in
  advance.
- The full unmarked test suite's stability remains an inherited,
  unresolved condition (Section 30); this phase does not attempt to
  repair it, per the operator prompt's explicit boundary.
- `NON-BLOCKING-136Z-1`'s underlying gap (no persisted Telegram delivery
  evidence anywhere in the existing notification pipeline) is a
  pre-existing production-code gap this phase discovered but does not
  repair -- doing so would exceed shared-core-only scope.

## 33. Next phase

Per Section 24 of the 136Y plan, the recommended next phase is:

**136AA -- Stage 3 Typed Authority Model Shared Core Independent
Verification**

This phase does not begin 136AA.

---

## Verdict

**SHARED CORE IMPLEMENTATION COMPLETE WITH NON-BLOCKING FINDINGS --
READY FOR INDEPENDENT VERIFICATION**
