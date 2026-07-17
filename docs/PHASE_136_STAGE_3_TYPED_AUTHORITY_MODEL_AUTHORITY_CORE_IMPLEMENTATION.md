# Phase 136AB: Stage 3 Typed Authority Model Authority Core Implementation

## 1. Purpose and boundaries

This phase implements Typed Model Implementation Group 2 of the frozen
`136Y` plan (`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
Sec.4/Sec.23): exactly two record-family models, `AuthorityEpoch` and
`AuthorityState`, schema-backed by
`src/pcae/schema_resources/cltr_cutover/records/authority_epoch.schema.json`
and `.../authority_state.schema.json` respectively.

Both models are descriptive, immutable, schema-backed typed
representations only. Neither model establishes current authority,
activates an authority epoch, selects an authority epoch, compares
operational authority, persists authority state, replaces legacy
lifecycle authority, mutates runtime state, authorizes execution, performs
semantic validation, resolves historical authority, or evaluates cutover
readiness. Legacy lifecycle remains the sole production authority; CLTR
remains derivative. Runtime remains Observed / observe / unavailable,
unchanged by this phase.

## 2. Binding sources

Precedence followed (identical structure to every prior phase in this
chapter): frozen primary contract (`CLTR-CUTOVER-SCHEMAS-001` v1.0 Sec.44,
`CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001` v1.0) → verified contract repairs
(none outstanding) → verified architecture (Phase 136B) → verified 136Y
implementation plan → verified 136Z/136AA shared core → this governed
136AB task contract → operator prompt. No conflict was found between the
operator prompt and the frozen contract requiring a discrepancy
disclosure.

Consulted directly: the 136Y plan (Sections 3-29), the two executable
schema files, `shared/identity.schema.json`, `shared/digest.schema.json`,
`shared/references.schema.json`, `shared/enums.schema.json`,
`shared/limitations.schema.json`, the 136Z/136AA shared-core source
(`src/pcae/cltr/authority/*.py`, excluding `authority_core.py` which this
phase adds), and the 136AA independent verification report's explicit
guidance for this phase (Sec.18): "136AB's `from_dict` implementations
should explicitly close finding 136AA-1 by always constructing
enum/wrapper-typed fields via their own type ... before passing them into
a shared-core composite constructor, never passing a raw payload value
through directly" — followed throughout `authority_core.py`.

## 3. Confirmed starting state (re-verified this phase)

- `git status --short` clean; `origin/main..HEAD` = 0 commits, before this
  phase's own commits.
- `src/pcae/cltr/authority/` contained exactly the 14 136Z shared-core
  modules; no `authority_core.py`, no `AuthorityEpoch`/`AuthorityState`
  class anywhere in the package or in `src/pcae` (grep + AST confirmed).
- No production module imports `pcae.cltr.authority` (grep confirmed
  across `src/pcae/commands`, `src/pcae/core`, `src/pcae/runtime`, and
  every sibling `src/pcae/cltr/*.py`).
- Runtime: Observed / observe / unavailable (unchanged).

## 4. Independently derived field tables

### 4.1 `AuthorityEpoch` (`records/authority_epoch.schema.json`)

| Schema field | Model attribute | Wire type | Typed type | Required | Null allowed | ABSENT allowed | Extension behavior |
|---|---|---|---|---|---|---|---|
| `schema_id` | `envelope.schema_id` | string (const) | `str` | yes | no | no | strict const check |
| `schema_version` | `envelope.schema_version` | string | `SchemaVersionString` | yes | no | no | shared type |
| `contract_version` | `envelope.contract_version` | string (const `"1.0"`) | `str` | yes | no | no | shared `RecordEnvelope` const check |
| `record_type` | `envelope.record_type` | string (const `authority_epoch`) | `str` | yes | no | no | strict const check |
| `record_id` | `envelope.record_id` | string | `RecordId` | yes | no | no | shared wrapper |
| `record_digest` | `envelope.record_digest` | string | `RecordDigest` | yes | no | no | shared wrapper |
| `created_at` | `envelope.created_at` | string | `Timestamp` | yes | no | no | shared wrapper, exact string preserved |
| `migration_epoch` | `migration_epoch` | string | `MigrationEpochToken` | yes | no | no | shared wrapper |
| `authority_kind` | `authority_kind` | string enum | `AuthorityKind` | yes | no | no | shared enum, fail-closed |
| `activation_state` | `activation_state` | string enum (3 values) | `ActivationState` (local) | yes | no | no | record-local enum, fail-closed |
| `predecessor_epoch` | `predecessor_epoch` | object or null | `Optional[RecordReference]` (family-restricted to `authority_epoch`) | yes (always present as key) | yes | no | family-restricted via `require_family` |
| `generation_binding` | `generation_binding` | object | `GenerationReference \| AbsentType` | conditional (active ⇒ required, proposed ⇒ forbidden) | no | yes | `ABSENT` default |
| `limitations` | `limitations` | array of string | `Limitations` | yes | no | no | shared type |
| `authority_disclosure` | `authority_disclosure` | object | `AuthorityDisclosure` | yes | no | no | shared type; `authority_role == "authoritative"` locally forbidden (`__post_init__`) |

`activation_state`/`generation_binding` conditional restated verbatim from
the schema's own `allOf`/`if`/`then` as a `__post_init__` invariant (Layer
3, not a new Layer 4/5 rule): `active` ⇒ `generation_binding` required;
`proposed` ⇒ `generation_binding` forbidden; `superseded` ⇒ neither
required nor forbidden (the schema's own `allOf` names no rule for
`superseded`, confirmed by direct re-reading of the schema file).

### 4.2 `AuthorityState` (`records/authority_state.schema.json`)

| Schema field | Model attribute | Wire type | Typed type | Required | Null allowed | ABSENT allowed | Extension behavior |
|---|---|---|---|---|---|---|---|
| `schema_id`..`created_at` | `envelope.*` | (as above) | (as above) | yes | no | no | strict const checks for `schema_id`/`record_type` |
| `migration_epoch` | `migration_epoch` | string | `MigrationEpochToken` | yes | no | no | shared wrapper |
| `transition_id` | `transition_id` | string | `TransitionId` | yes | no | no | shared wrapper |
| `active_authority_epoch` | `active_authority_epoch` | object | `RecordReference` (family-restricted to `authority_epoch`) | yes | no | no | `require_family` |
| `authority_kind` | `authority_kind` | string enum | `AuthorityKind` | yes | no | no | shared enum |
| `authoritative_generation` | `authoritative_generation` | object | `GenerationReference \| AbsentType` | conditional (`authority_kind == cltr` ⇒ required) | no | yes | `ABSENT` default |
| `publication_evidence_reference` | `publication_evidence_reference` | object | `RecordReference` (family-restricted to `publication_evidence`) | yes | no | no | `require_family` |
| `pointer_digest` | `pointer_digest` | string | `PointerDigest` | yes | no | no | shared wrapper |
| `verification_state` | `verification_state` | string enum (3 values) | `VerificationState` (local) | yes | no | no | record-local enum, fail-closed |
| `uncertainty` | `uncertainty` | object | `Uncertainty \| AbsentType` | conditional (`unverified` ⇒ required, `verified` ⇒ forbidden, `verification_failed` ⇒ optional) | no | yes | `ABSENT` default |
| `compatibility_mode` | `compatibility_mode` | string enum | `CompatibilityMode` | yes | no | no | shared enum |
| `limitations` | `limitations` | array of string | `Limitations` | yes | no | no | shared type |
| `authority_disclosure` | `authority_disclosure` | object | `AuthorityDisclosure` | yes | no | no | shared type; `authoritative` structurally permitted here (unlike `AuthorityEpoch`), `is_authoritative` still pinned `False` |

Neither schema declares `_extensions` or embeds `CasExpectation` (both
independently confirmed by direct re-reading of both schema files); no
`ExtensionMapping`/`OpaqueJsonValue`/`CasExpectation` is used by either
model (grep-confirmed against `authority_core.py`'s own source, Section
9's independent test module also asserts this directly).

## 5. Package layout

Single new module, matching the 136Y plan's Section 7 layout exactly:

```
src/pcae/cltr/authority/authority_core.py   # Group 2: AuthorityEpoch, AuthorityState
```

`__init__.py` extended to export `AuthorityEpoch`, `AuthorityState`, and
two small local value types (`ActivationState`, `VerificationState`
enums, `Uncertainty` value object) needed by external callers — no
wildcard export; every export named explicitly, matching the 136Z
precedent.

## 6. Construction / serialization pipeline

`AuthorityEpoch.from_dict(payload, *, schema_version)` and
`AuthorityState.from_dict(payload, *, schema_version)`:

1. Reject unrecognized `schema_version` (`UnsupportedSchemaVersionError`;
   only `"1.0"` recognized by either model today).
2. Reject any top-level payload key outside the schema's own field set
   (`TypedModelConstructionError`), restating `additionalProperties:
   false`.
3. Extract and re-validate every field at the type-construction boundary:
   every enum is constructed via `EnumClass(raw_str)` (exact match, no
   case-folding); every identifier/digest is constructed via its own
   wrapper type; every reference is constructed via a dedicated
   `_record_reference_from_dict`/`_generation_reference_from_dict` helper
   that itself rejects unknown nested keys and applies `require_family`
   where the schema's own `allOf`+`const` restricts it. This explicitly
   closes 136AA-1 (composite fields are never handed a raw payload value
   directly).
4. `predecessor_epoch`/`active_authority_epoch` distinguish "missing key"
   (raises — the key must always be present per the schema) from
   "present with `null`" (only legal for `predecessor_epoch`, the first
   epoch of a lineage) from "present with a reference object", using
   `key in payload` semantics, never `payload.get(key)`.
5. `generation_binding`/`authoritative_generation`/`uncertainty` use
   `field_from_payload` (Section 16-adjacent shared primitive) to
   distinguish "absent" (`ABSENT`) from "present"; none of the three
   schema fields permits an explicit `null`, confirmed by direct
   re-reading of both schema files, so no `AbsentNullMismatchError` case
   applies to Group 2.
6. `__post_init__` restates each family's own schema-level conditional
   exactly once (Section 4 tables above) as a `TypedModelInternalInvariantError`
   — never a new Layer 4/5 rule.

`to_dict(self)` flattens the composed `RecordEnvelope`'s own
`to_dict_fields()` output together with the record-specific fields at the
same top level (matching the wire shape, which has no nested `envelope`
key), omitting any field whose value `is ABSENT`, and recursively
serializing every other value via the shared `serialize_value` primitive
(enums → `.value`; wrapper types → `.to_wire()`; nested reference/
disclosure/limitations dataclasses → `to_dict_fields()`).

Round trip: `from_dict(to_dict(from_dict(payload))) == from_dict(payload)`
verified for every fixture variant (Section 8).

## 7. Strict constants

Both models enforce, at construction: `envelope.schema_id` equals the
exact frozen schema `$id` string; `envelope.record_type` equals the exact
frozen `record_type` const (`"authority_epoch"`/`"authority_state"`).
Neither is re-derived, normalized, or aliased; a wrong value raises
`TypedModelConstructionError`.

## 8. Tests

`tests/test_cltr_authority_136ab_authority_core.py`, 69 tests, covering:
inventory (exactly two record-family models, no later-group class
anywhere in the package); minimal/maximal valid construction for both
models across every conditional branch; exact field mapping; unknown-field
and unknown-enum-value rejection; unsupported-schema-version rejection;
wrong `schema_id`/`record_type` rejection; the full
`activation_state`↔`generation_binding`,
`authority_kind`↔`authoritative_generation`, and
`verification_state`↔`uncertainty` conditional matrices (both legal
combinations and illegal partial-presence); wrong-family reference
rejection for `predecessor_epoch`, `active_authority_epoch`, and
`publication_evidence_reference`; immutability (frozen top-level
assignment, tuple-backed `limitations`, deep-copied `to_dict()` output);
structural equality (including record-ID-equality-does-not-imply-
record-equality); malformed digest/identifier rejection; no-coercion
(boolean-as-string rejected); automated schema-to-model conformance
(field-set and required-set drift detection against the live schema
JSON, enum-member-set drift detection for both local enums);
no-authority-symbol source scan; no-CasExpectation/no-ExtensionMapping/
no-OpaqueJsonValue-usage proof (neither schema needs them); runtime
isolation (no production module imports `pcae.cltr.authority`);
instrumented no-network/no-subprocess/no-filesystem-write/
no-environment-lookup proofs during construction and serialization; and
wheel/sdist/installed-wheel-outside-checkout packaging proofs. All 69
pass.

## 9. Scope-guard narrowing (disclosed)

Three pre-existing test files asserted, correctly at the time they were
written, that no `AuthorityEpoch`/`AuthorityState` class or
`authority_core.py` module existed yet. This phase legitimately
introduces both, so each guard was narrowed to authorize exactly Group 2
while leaving every other later-group name/module forbidden, unchanged
— mirroring the precedent 136Z itself used against a stale 136U guard,
and the precedent 136M's own test comment already cited in anticipation
of this exact phase:

- `tests/test_cltr_authority_136z_shared_core.py`:
  `test_136z_exact_module_inventory`,
  `test_136z_no_record_family_model_class_defined_anywhere_in_package`,
  `test_136z_wheel_contains_authority_shared_core_no_record_family_module`
  — each now carves out `authority_core.py`/`AuthorityEpoch`/
  `AuthorityState` specifically; the other 14 later-group names and
  4 other later-group modules remain asserted absent.
- `tests/test_cltr_authority_136aa_shared_core_independent.py`:
  `test_public_api_matches_independently_derived_inventory`,
  `test_no_record_family_model_class_exists_anywhere_in_package`,
  `test_authority_package_files_present_on_disk_for_packaging` — same
  narrowing.
- `tests/test_cltr_cutover_136m_request_and_readiness_independent_verification.py`:
  `test_136m_no_typed_authority_model_module_exists` — its own comment
  already named this exact precedent in advance; narrowed identically.

No weakening beyond exactly these two class names / this one module name
was made in any of the six narrowed tests; every other later-group name
in each guard's own forbidden list was independently re-confirmed still
present and still checked (re-run, passing).

## 10. Runtime isolation / no-authority / no-side-effect verification

- Grepped `src/pcae/commands`, `src/pcae/core`, `src/pcae/runtime`, and
  every sibling module under `src/pcae/cltr` (excluding `authority/`
  itself) for `from pcae.cltr.authority`/`import pcae.cltr.authority`:
  zero hits (unchanged from 136AA).
- AST-scanned `authority_core.py` for function/method definitions matching
  a list of forbidden authority-selection/execution symbol names
  (`resolve_authority`, `current_authority`, `activate_epoch`,
  `is_current`, `can_transition`, `should_activate`, `is_ready`, etc.):
  zero hits.
- Instrumented `hashlib.sha256`, `socket.socket.connect`,
  `subprocess.Popen`, `builtins.open` (write modes), and
  `os.environ.get` during construction and serialization of fixtures for
  both models: zero calls in every case.

## 11. Packaging

`authority_core.py` is included via the existing
`[tool.hatch.build.targets.wheel] packages = ["src/pcae"]` rule — no
`pyproject.toml` change. Verified (not changed): wheel contains
`pcae/cltr/authority/authority_core.py` and excludes every later-group
module name; sdist includes it; an installed wheel in a fresh venv,
invoked from outside the repository checkout, successfully constructs and
serializes an `AuthorityEpoch` fixture. No new dependency was added
(`pyproject.toml` still declares only `jsonschema>=4.18,<5`).

## 12. Regression results (fresh, this phase, under `.venv` Python 3.9.6)

| Suite | Result |
|---|---|
| `tests/test_cltr_authority_136ab_authority_core.py` (new, 69 tests) | 69 passed |
| `tests/test_cltr_authority_136z_shared_core.py` + `tests/test_cltr_authority_136aa_shared_core_independent.py` (rerun fresh, post-narrowing) | 445 passed |
| All three files together | 514 passed |
| `-k "cltr or canonicaliz or schema_runtime or manifest or registry" -n auto` (bounded, ~40s) | 4061 passed, 9 failed, 8 skipped, deselected remainder |
| `-m fast_green -n auto` | 4391 passed (matches 136AA's own baseline exactly) |
| Bounded full-suite diagnostic (`-n auto`, 240s bound) | did not complete within the bound |

The 9 bounded-sweep failures are unchanged from 136AA's own disclosed set:
1 is the pre-existing 136U scope-guard regression against
`RecordFamily.RECEIPT_AUTHORITY_BINDING` (136AA-3, still not this task
contract's scope to repair); 8 are the pre-existing, unrelated
`test_cltr_135o_integration.py`/`test_cltr_migration_135p_verification.py`
completion-status-mismatch cluster (136AA-4). Neither cluster references
`cltr.authority` (grep-reconfirmed). No new failure was introduced by this
phase; the 6-test scope-guard narrowing (Section 9) accounts for the
6 fixed failures relative to the pre-narrowing sweep.

The bounded full-suite diagnostic not completing within 240 seconds is
the same pre-existing, previously-disclosed condition (`NON-BLOCKING-136W-3`,
independently observed a sixth time here); this phase does not become a
test-infrastructure repair phase for it, per its own explicit boundary and
136Y Sec.33's stated non-triggering condition (the stall has not begun
intersecting this phase's own new test file specifically).

## 13. Findings

| ID | Classification | Summary |
|---|---|---|
| 136AB-1 | CONFIRMED, repaired this phase (not a defect — anticipated maintenance) | Three pre-existing scope guards (136Z, 136AA, 136M) required the identical Group-2 narrowing already anticipated in 136M's and 136AA's own prior disclosures; narrowed exactly as anticipated, no other name touched. |
| 136AA-3 (inherited) | CONFIRMED, requires follow-up (not this phase's scope) | Pre-existing 136U scope guard still incorrectly flags `RecordFamily.RECEIPT_AUTHORITY_BINDING`; unchanged by this phase, still a small future-phase follow-up. |
| 136AA-4 (inherited) | CONFIRMED, inherited/unrelated | The 8 pre-existing `test_cltr_135o_integration.py`/`test_cltr_migration_135p_verification.py` failures, unrelated to `cltr.authority`, unchanged by this phase. |

No Blocking finding was identified against this phase's Blocking criteria
(wrong field mapping, record-discriminator drift, schema-family drift,
absence/null collapse, enum coercion, wrong identifier/digest family,
reference-family collapse, lossy round trip, timestamp normalization,
mutable nested state, digest computation, CAS evaluation, reference
resolution, repository lookup, persistence, runtime import, authority
selection, operational state-machine logic, extra record-family model,
packaging omission, installed-wheel failure).

## 14. Limitations

- `from_json` (a thin convenience wrapper composing strict JSON parsing +
  schema validation + `from_dict`, mentioned as optional in 136Y plan
  Sec.16) was not built this phase — out of this task's exact scope
  ("package exports needed for these two models"); `from_dict`/`to_dict`
  fully cover this phase's construction/serialization scope. A future
  phase may add it without any change to `from_dict`'s own contract.
- The two inherited findings (136AA-3, 136AA-4) remain open, unchanged,
  disclosed above, not repaired by this phase (out of its bounded scope).

## 15. Telegram / notification disclosure

Per this phase's own explicit instruction, and in light of 136AA's
disclosed Telegram anomaly (Sec.20 of the 136AA independent verification
report — dispatch occurred despite every isolated presence check showing
`PCAE_NOTIFY_ENABLED` unset), the operator was asked explicitly before
finalization whether to enable dispatch for this phase. A safe presence
check (reporting only whether the variable is present, never its value)
was run immediately before finalization. This report states plainly,
using the four categories this phase's instructions require, which one
occurred — recorded in `.pcae/phase-completion-metadata.json` and the
canonical completion report at finalization time, not asserted in
advance here.

## 16. Acceptance criteria checklist

- [x] Exactly two record-family models implemented (Section 1, Section 8).
- [x] Every field independently derived from the executable schema, not
      copied solely from 136Y prose (Section 4).
- [x] Record type / schema-family constants strictly enforced (Section 7).
- [x] Absent vs null preserved distinctly (Section 4, Section 6, Section 8).
- [x] Enums strict, fail-closed (Section 8).
- [x] Identifier/digest families preserved via distinct wrapper types
      (Section 4, Section 8).
- [x] References never resolved/dereferenced (Section 10).
- [x] No `CasExpectation` usage (neither schema embeds it, Section 4).
- [x] Both models frozen, recursively immutable, lossless round trip
      (Section 6, Section 8).
- [x] No later record-family models, no semantic validators, no
      repositories, no persistence, no authority resolver, no production
      runtime import (Section 9, Section 10).
- [x] No side effects (Section 10).
- [x] Schema-to-model conformance automated (Section 8).
- [x] Packaging verified (Section 11).
- [x] Focused and regression suites pass, with inherited failures
      explicitly disclosed (Section 12).
- [x] No unresolved Blocking finding remains (Section 13).
- [x] Runtime remains Observed / observe / unavailable (unchanged).

## 17. Verdict

**AUTHORITY CORE MODEL IMPLEMENTATION COMPLETE WITH NON-BLOCKING FINDINGS
— READY FOR INDEPENDENT VERIFICATION**

## 18. Recommended next phase

**136AC — Stage 3 Typed Authority Model Authority Core Independent
Verification.** This phase does not begin 136AC.

## 19. No-go confirmation

This phase implemented no `CutoverRequest`, `ReadinessPackage`,
`HumanAuthorization`, `CutoverCandidate`, `Certification`,
`PublicationAttempt`, `PublicationEvidence`, `ConcurrencyConflict`,
`RecoveryJournalEntry`, `NotificationAuthorityBinding`,
`MarkerAuthorityBinding`, `FinalizationReceiptAuthorityBinding`,
`CompatibilityState`, or `QuarantineRecord`; no semantic validator, no
cross-record repository, no persistence, no authority resolver, no
compatibility resolver, no quarantine coordinator, no publication
coordinator, no recovery coordinator, no lifecycle integration, no
execution capability, no authority activation, no legacy
demotion/retirement. Runtime remains Observed / observe / unavailable;
legacy lifecycle remains sole production authority; CLTR remains
derivative.
