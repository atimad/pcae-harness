# Phase 136AC: Stage 3 Typed Authority Model Authority Core Independent Verification

## Contract identifier

Independently verifies Phase 136AB (commit `2b0665e6`, "Stage 3 Typed
Authority Model Authority Core Implementation") against:

- CLTR-001 v1.0
- CLTR-SCHEMA-001 v1.0.1
- CLTR-CUTOVER-001 v1.0
- CLTR-CUTOVER-SCHEMAS-001 v1.0
- CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0
- Stage 3 Companion Schemas and Typed Authority Model Contract
- Phase 136Y implementation plan (`77566be5`)
- executable schemas `records/authority_epoch.schema.json`,
  `records/authority_state.schema.json`, and every shared schema they
  reference (`shared/envelope.schema.json`, `shared/identity.schema.json`,
  `shared/digest.schema.json`, `shared/enums.schema.json`,
  `shared/references.schema.json`, `shared/limitations.schema.json`)
- previously verified foundation commits: 136Z (`9fd2a645`), 136AA
  (`a072527b`)
- PFN-001 / PFR-001

Precedence when conflicts arise: frozen primary contract > verified contract
repairs > verified architecture > 136Y plan > 136Z/136AA shared core >
this governed verification contract > operator prompt. No conflict between
the frozen contract and the 136AB implementation was found (Sec.14).

## 1. Methodology

This verification independently re-derived both models' field tables,
discriminators, conditional-branch rules, and enum vocabularies directly
from the two executable schema files (`json.load` on the raw schema
documents, plus `pcae.schema_runtime.build_offline_registry` /
`validate_record_shape` -- shared, non-authority-specific Layer 2
infrastructure, not 136AB test code -- for real JSON-Schema-validated
cross-checks), then constructed its own adversarial payloads and fixtures
from scratch in a new test module,
`tests/test_cltr_authority_136ac_authority_core_independent.py` (104
independent test functions, several parametrized). No fixture, helper
function, expected-field-set constant, or expected-value literal was
imported from `tests/test_cltr_authority_136ab_authority_core.py`; that
module was read only to confirm this phase was not duplicating its
existing coverage, never as a source of expected values.

Every payload constructed for this verification was independently checked
against the live schema via `validate_record_shape` before being fed to the
typed-model constructor, so a construction failure on a schema-valid
payload (or a construction success on a schema-invalid payload) would be
caught as a genuine model/schema drift, not a fixture-authoring mistake.

## 2. Independently re-derived field tables

### AuthorityEpoch (`records/authority_epoch.schema.json`)

| Schema field | Wire type | Required | Null allowed | ABSENT allowed | Typed wrapper | Conditional rule |
|---|---|---|---|---|---|---|
| schema_id | string (const) | yes | no | no | plain str | fixed const |
| schema_version | string | yes | no | no | `SchemaVersionString` | MAJOR.MINOR |
| contract_version | string (const "1.0") | yes | no | no | plain str | fixed const |
| record_type | string (const "authority_epoch") | yes | no | no | plain str | fixed const |
| record_id | string | yes | no | no | `RecordId` | `^[a-z][a-z0-9-]{7,127}$` |
| record_digest | string | yes | no | no | `RecordDigest` | 64-hex sha256 |
| created_at | string | yes | no | no | `Timestamp` | RFC3339 `Z`-suffixed |
| migration_epoch | string | yes | no | no | `MigrationEpochToken` | opaque, lowercase |
| authority_kind | enum (2) | yes | no | no | `AuthorityKind` | legacy/cltr |
| activation_state | enum (3) | yes | no | no | `ActivationState` | proposed/active/superseded |
| predecessor_epoch | object or null | yes (key) | **yes** | no | `RecordReference` (family-restricted) | null only for lineage root |
| generation_binding | object | **no** | no | **yes** | `GenerationReference` | required iff active; forbidden iff proposed |
| limitations | array of string | yes | no | no | `Limitations` | may be empty |
| authority_disclosure | object | yes | no | no | `AuthorityDisclosure` | `authority_role != "authoritative"` locally forbidden |

### AuthorityState (`records/authority_state.schema.json`)

| Schema field | Wire type | Required | Null allowed | ABSENT allowed | Typed wrapper | Conditional rule |
|---|---|---|---|---|---|---|
| schema_id / schema_version / contract_version / record_type / record_id / record_digest / created_at | -- | yes (all 7) | no | no | envelope wrappers | fixed consts as above, `record_type = "authority_state"` |
| migration_epoch | string | yes | no | no | `MigrationEpochToken` | -- |
| transition_id | string | yes | no | no | `TransitionId` | `^trans-[a-z0-9-]{2,122}$` |
| active_authority_epoch | object | yes | no | no | `RecordReference` (family-restricted to `authority_epoch`) | -- |
| authority_kind | enum (2) | yes | no | no | `AuthorityKind` | -- |
| authoritative_generation | object | **no** | no | **yes** | `GenerationReference` | required iff `authority_kind == "cltr"` |
| publication_evidence_reference | object | yes | no | no | `RecordReference` (family-restricted to `publication_evidence`) | forward reference; target need not exist |
| pointer_digest | string | yes | no | no | `PointerDigest` | 64-hex sha256 |
| verification_state | enum (3) | yes | no | no | `VerificationState` | unverified/verified/verification_failed |
| uncertainty | object | **no** | no | **yes** | `Uncertainty` | required iff unverified; forbidden iff verified; optional iff verification_failed |
| compatibility_mode | enum (6) | yes | no | no | `CompatibilityMode` | -- |
| limitations | array of string | yes | no | no | `Limitations` | may be empty |
| authority_disclosure | object | yes | no | no | `AuthorityDisclosure` | `authority_role == "authoritative"` structurally permitted here only; `is_authoritative` still const false |

Both tables were confirmed to match `authority_core.py`'s actual accepted/
serialized key set exactly (`test_epoch_model_known_keys_matches_schema_property_set`,
`test_state_model_serialized_keys_subset_of_schema_properties`, plus the
per-field construction/round-trip tests in Sections 2-9 of the new test
module). No drift was found in either direction.

## 3. Discriminators, absence/null, enums, identifiers/digests/references,
timestamps

All independently re-derived and re-tested (Sections 3-6 of the test
module): wrong/malformed/absent record_type and schema_id are rejected;
`predecessor_epoch`/`generation_binding`/`authoritative_generation`/
`uncertainty` correctly distinguish omitted vs. explicit `null` vs. typed
value, matching the schema's own `required`/`oneOf`/conditional-`allOf`
shape exactly; every wrong-family reference (`predecessor_epoch`,
`active_authority_epoch`, `publication_evidence_reference`) is rejected via
`WrongFamilyReferenceError`; digests and identifiers reject malformed
length/case/prefix; a syntactically valid reference to a target that has
never existed constructs successfully with no filesystem/socket access
(verified by monkeypatching `open`/`socket.socket`); timestamps preserve
the exact wire string including fractional-second precision and are never
normalized between `Z` and `+00:00` forms (the two are treated as distinct,
and the `+00:00` form is rejected outright, not silently accepted);
construction never reads the wall clock (`datetime.datetime.now`/`utcnow`
monkeypatched to raise).

## 4. Serialization, immutability, equality

`to_dict()` round trips every field exactly for both minimal and maximal
payloads (all activation/verification-state branches, independently swept
against the live schema again post-round-trip); mutating a `to_dict()`
result or the original constructor input dict after construction never
affects the model; frozen-dataclass assignment raises
`dataclasses.FrozenInstanceError` at every tested nesting level (top-level
field, nested `Limitations.entries` tuple, nested `AuthorityDisclosure`);
equality is exact structural equality -- same record ID or same digest with
one differing field (including a bare timestamp-string difference) compares
unequal.

## 5. No operational authority semantics; no semantic validation

AST inspection of `authority_core.py` confirms none of the fifteen
forbidden operational names (`is_current`, `activate`, `demote`, `resolve`,
`persist`, `enforce_cas`, `authorize`, etc.) are defined anywhere in the
module, and both model classes expose only dunder methods plus
`from_dict`/`to_dict`. Schema-valid-but-operationally-fabricated payloads
(an `AuthorityEpoch` naming a predecessor that has never existed; an
`AuthorityState` naming an epoch and publication-evidence record that have
never existed) construct successfully without error -- confirming Layer 3
performs no cross-record existence or currency check, per contract Sec.1/
Sec.40. Neither model declares a `cas_expectation` field; `hashlib.sha256`
is never invoked (monkeypatched and asserted unreached) during construction
or serialization of either model.

## 6. No later models; public API; scope guards

AST class-definition scan of every `.py` file in
`src/pcae/cltr/authority/` found none of the fourteen later-group record
names defined anywhere; `pcae.cltr.authority.__all__` contains neither a
later-group name nor an unauthorized internal helper; every name in
`__all__` resolves, and `from pcae.cltr.authority import *` binds exactly
the `__all__` set (no more, no less).

`tests/test_cltr_cutover_136m_request_and_readiness_independent_verification.py`'s
scope guard (last touched in the same 136AB commit) now forbids exactly
the fourteen later-group names and no longer names `AuthorityEpoch`/
`AuthorityState` -- correctly narrowed, matching the same disclosed-
amendment precedent 136AA already used for 136Z. Re-run and green
(Sec.9).

## 7. Runtime isolation; side effects

Independent AST import-graph scan of `src/pcae/commands`, `src/pcae/core`,
`src/pcae/runtime` (the latter does not exist in this checkout -- skipped,
not silently passed) and every sibling `pcae.cltr` module outside
`pcae/cltr/authority/` found zero imports of `pcae.cltr.authority`.
`pcae.cltr.authority`'s own modules import nothing from `pcae.commands`,
`pcae.core`, or `pcae.runtime`. `subprocess.run`/`Popen`, `socket.socket`,
`os.getenv`, and write-mode `open()` were all monkeypatched to raise/count
during construction, serialization, and error paths of both models; no
call was observed.

## 8. Packaging / installed-wheel verification

Built `pcae_harness-0.2.0-py3-none-any.whl` and `.tar.gz` sdist fresh via
`python -m build`. Both archives include all fifteen files of
`src/pcae/cltr/authority/` including `authority_core.py`. Installed the
wheel into a fresh `venv` outside the repository checkout (`/tmp`), then
from a `/tmp` working directory (not the repo checkout) imported
`AuthorityEpoch`/`AuthorityState`, constructed one minimal instance of
each, called `to_dict()`, and confirmed none of the fourteen later-group
names are attributes of the installed `pcae.cltr.authority` package. The
installed package declares one runtime dependency (`jsonschema`); no
undeclared dependency was required.

## 9. Finding: enum-field construction failures raise bare `ValueError`,
not a `TypedModelError` subclass (CONFIRMED-136AC-1, NON-BLOCKING)

All four `EnumClass(raw_str)` call sites in `authority_core.py`
(`activation_state` -> `ActivationState`, `authority_kind` ->
`AuthorityKind`, `verification_state` -> `VerificationState`,
`compatibility_mode` -> `CompatibilityMode`, and transitively
`authority_role` -> `AuthorityRole` inside `_authority_disclosure_from_dict`)
let Python's stdlib `Enum.__new__` raise a bare `ValueError` uncaught on an
unrecognized member, rather than wrapping it in
`TypedModelConstructionError`. The module's own docstring and the frozen
contract's Error-Hierarchy Verification requirement both describe every
Layer 3 construction failure -- explicitly including "wrong enum" -- as
part of the shared `TypedModelError` hierarchy.

Reproduced directly:

```
>>> auth.AuthorityEpoch.from_dict({..., "activation_state": "Proposed", ...}, schema_version="1.0")
ValueError: 'Proposed' is not a valid ActivationState
>>> isinstance(exc, auth.TypedModelError)
False
```

136AB's own focused test suite already encodes this behavior as expected
(`tests/test_cltr_authority_136ab_authority_core.py::test_136ab_authority_epoch_unknown_enum_value_rejected`
and its `..._activation_state_rejected` sibling both assert
`pytest.raises(ValueError)`, not `pytest.raises(auth_errors.TypedModelConstructionError)`)
rather than disclosing it as a limitation -- exactly the kind of
implementation-derived expectation this phase was chartered not to trust
blindly. Independently re-derived and reproduced here as
`test_epoch_enum_field_rejection_is_bare_valueerror_not_typedmodelerror`
and `test_state_enum_field_rejection_is_bare_valueerror_not_typedmodelerror`.

**Classification: NON-BLOCKING.** The value is still rejected -- fail-closed,
no coercion, no silent acceptance, no repair of caller input -- so none of
the frozen Acceptance Criteria's Blocking categories ("enum drift or
coercion", "absence/null collapse", etc.) are triggered by this finding;
only the *exception type* is inconsistent with the module's own stated
error taxonomy. No repair was made in this phase (bounded repair is
authorized only for reproduced Blocking defects); this finding is
disclosed for a future bounded hardening pass, not deferred silently.

## 10. Regression results (fresh, this phase, `.venv` Python 3.9.6)

| Suite | Result |
|---|---|
| `tests/test_cltr_authority_136ac_authority_core_independent.py` (new, this phase) | 104 passed, 1 skipped (`src/pcae/runtime` absent in this checkout) |
| `tests/test_cltr_authority_136ab_authority_core.py` | all passed |
| `tests/test_cltr_authority_136aa_shared_core_independent.py` | all passed |
| `tests/test_cltr_authority_136z_shared_core.py` | all passed |
| Combined `test_cltr_authority_136a{a,b,c}*` + `136z` | 514 passed |
| Combined `test_cltr_authority_*` + `test_cltr_cutover_136*` + `test_cltr_canonicalization` + `test_cltr_digest` + `test_cltr_models` + `test_cltr_validation` + `test_schema_runtime_*` + `test_runtime_registry_*` + `test_runtime_enforcement_no_go_registry_contract` + `test_runtime_service_registry_architecture` | 3220 passed, 9 skipped, **1 failed** (inherited, see Sec.11) |
| `tests/test_cltr_135o_integration.py` + `tests/test_cltr_migration_135p_verification.py` | 21 passed, **8 failed** (inherited, see Sec.11) |
| Wheel + sdist build | succeeded, both include `authority_core.py` |
| Installed-wheel isolated-venv verification | passed (Sec.8) |

Commands used: `python -m pytest <paths> -q` from the repository root under
the project `.venv`; `python -m build --wheel --sdist --outdir <scratch>`;
manual `venv`/`pip install`/`python -c` sequence outside the repo checkout
for the installed-wheel check.

## 11. Inherited regression failures (disclosed, not repaired)

Nine failures reproduced, matching the counts and identities Phase 136AB
already disclosed as inherited and unrelated:

- **One 136U scope-guard failure**:
  `test_cltr_cutover_136u_notification_marker_receipt_binding_independent_verification.py::test_136u_no_runtime_code_references_group10_families_outside_schema_resources`,
  failing because `src/pcae/cltr/authority/enums.py`'s `RecordFamily` enum
  (introduced in Phase 136Z, unchanged by 136AB) literally contains the
  strings `notification_authority_binding`/`marker_authority_binding`/
  `receipt_authority_binding` as enum member values, tripping a
  `git grep`-based scope guard written before that shared enum existed.
  136AA's own independent verification report already identified and
  disclosed this exact failure (its Sec.9, "pre-existing Phase 136U scope
  guard breaks on 136Z's frozen `RecordFamily` enum"). `enums.py` was not
  touched by the 136AB commit; this failure is unrelated to
  `AuthorityEpoch`/`AuthorityState`.
- **Eight 135O/135P migration/integration failures**: all eight in
  `tests/test_cltr_135o_integration.py` (4) and
  `tests/test_cltr_migration_135p_verification.py` (4, one parametrized
  ×4) concern legacy finalization-transaction receipt/migration-evidence
  status strings (`"completed"` vs.
  `"completed_receipt_best_effort_incomplete"`) in code paths that never
  import or reference `pcae.cltr.authority`.

No new failure appeared in any suite run this phase. Per the governing
contract, overall regression status for this phase is classified
`passed_with_disclosed_inherited_failures`: no new failures, failure
identities match prior evidence, no changed Authority Core code path is
involved in any of the nine, and the focused Authority Core independent
verification suite (Sec.10, first two rows) is fully green.

## 12. Full-suite diagnostic

Per the phase charter, this phase does not attempt to run the full
unmarked suite (already disclosed as repeatedly stalling across prior
phases, unrelated to Authority Core) and does not attempt suite-
infrastructure repair. The bounded diagnostic above (3220+21+104 tests
across every Authority Core-adjacent, CLTR-cutover, schema-runtime, and
registry suite, plus the two suites containing all nine known inherited
failures) completed without hanging, and specifically exercised every test
file that imports `pcae.cltr.authority` directly. No new deadlock,
resource leak, or Authority Core contribution to the previously observed
stall was found within this bounded scope.

## 13. Findings summary

| ID | Severity | Summary |
|---|---|---|
| CONFIRMED-136AC-1 | NON-BLOCKING | Enum-field rejection (`activation_state`, `authority_kind`, `verification_state`, `compatibility_mode`, `authority_role`) raises bare `ValueError`, not a `TypedModelError` subclass. Fail-closed; error-taxonomy consistency only. See Sec.9. |

No Blocking finding was identified. No repair was made or was required.

## 14. Acceptance criteria checklist

- [x] Both model contracts independently re-derived (Sec.2)
- [x] Every schema field accounted for (Sec.2)
- [x] Exact discriminators enforced (Sec.3)
- [x] Required/optional fields match (Sec.2)
- [x] Nullability matches (Sec.2, Sec.3)
- [x] Absence and null remain distinct (Sec.3)
- [x] Enums strict (Sec.3; error-type finding disclosed non-blocking, Sec.9)
- [x] Identifier families exact (Sec.3)
- [x] Digest families exact (Sec.3)
- [x] References do not resolve (Sec.3)
- [x] CAS remains descriptive -- neither model has a CAS field at all (Sec.5)
- [x] Timestamps preserve original wire strings (Sec.3)
- [x] Limitations/disclosures/extensions round trip (Sec.4; neither schema declares `_extensions`, confirmed absent on both models)
- [x] Nested values remain immutable (Sec.4)
- [x] Serialization lossless (Sec.4)
- [x] Schema drift detection exists (Sec.2, Sec.10 new suite)
- [x] No cross-record semantic validation (Sec.5)
- [x] No operational authority behavior (Sec.5)
- [x] No later model exists (Sec.6)
- [x] No production runtime import (Sec.7)
- [x] No side effect (Sec.7)
- [x] Wheel and sdist include both models (Sec.8)
- [x] Installed-wheel verification passes (Sec.8)
- [x] Focused and adjacent regressions pass (Sec.10, Sec.11)
- [x] No unresolved Blocking finding remains (Sec.13)
- [x] Runtime remains Observed / observe / unavailable (`pcae runtime inspect`, this session)

## 15. Verdict

**AUTHORITY CORE VERIFIED WITH NON-BLOCKING FINDINGS
-- READY FOR REQUEST AND READINESS MODEL IMPLEMENTATION**

## 16. Recommended next phase

Recommended next phase: 136AD -- Stage 3 Typed Authority Model Request and
Readiness Implementation. That phase should implement only
`CutoverRequest` and `ReadinessPackage`.

## 17. No-go confirmation

This phase implemented no later record-family model, semantic validator,
repository, persistence, resolver, or execution capability. The fourteen
later-group model names and their record modules remain forbidden and
absent (Sec.6).

## 18. Telegram / notification evidence

Recorded verbatim in `.pcae/phase-completion-report.md` at finalization
time, per the governed finalization procedure; not duplicated here to
avoid a stale copy diverging from the canonical report.
