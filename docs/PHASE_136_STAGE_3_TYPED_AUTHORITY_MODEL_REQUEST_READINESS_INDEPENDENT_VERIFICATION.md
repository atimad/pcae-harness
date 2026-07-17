# Phase 136AE: Stage 3 Typed Authority Model Request and Readiness Independent Verification

## 1. Purpose and methodology

Phase 136AE independently verifies the `CutoverRequest` and
`ReadinessPackage` typed record models implemented by Phase 136AD
(`src/pcae/cltr/authority/request_readiness.py`, commit `b6e981c7`).

Independence discipline: no fixture, helper function, expected-value
table, or finding classification was copied from Phase 136AD's own test
module (`tests/test_cltr_authority_136ad_request_readiness.py`) or its
phase report. A new, standalone test module —
`tests/test_cltr_authority_136ae_request_readiness_independent.py` (130
tests) — was authored from three sources read directly in this phase:

1. The frozen primary contracts —
   `PHASE_135_STAGE_3_COMPANION_SCHEMAS_AND_TYPED_AUTHORITY_MODEL_CONTRACT_FREEZE.md`
   (Sec.6.3, Sec.30) and
   `PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`
   (Sec.19, Sec.20).
2. The live executable schemas — `records/cutover_request.schema.json`,
   `records/readiness_package.schema.json`, and every shared `$ref`
   (`shared/failures.schema.json`, `shared/identity.schema.json`,
   `shared/digest.schema.json`, `shared/references.schema.json`,
   `shared/limitations.schema.json`, `shared/enums.schema.json`).
3. The verified 136Y implementation plan
   (`PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
   Sec.9, absent-vs-null design).

Every wire fixture, expected constant, expected enum set, and expected
conditional shape in the new test module was derived from these sources
directly, then compared against the Phase 136AD implementation's actual
behavior.

## 2. Independently re-derived field tables

### 2.1 `CutoverRequest` (`records/cutover_request.schema.json`)

| Schema field | Wire type | Required | Null allowed | ABSENT allowed | Typed wrapper | Local invariant |
|---|---|---|---|---|---|---|
| `schema_id` | string (const) | yes | no | no | `RecordEnvelope.schema_id` | must equal frozen schema URL |
| `schema_version` | string `MAJOR.MINOR` | yes | no | no | `SchemaVersionString` | pattern `^[0-9]+\.[0-9]+$` |
| `contract_version` | string (const `"1.0"`) | yes | no | no | `RecordEnvelope.contract_version` | const `"1.0"` |
| `record_type` | string (const) | yes | no | no | `RecordEnvelope.record_type` | must equal `"cutover_request"` |
| `record_id` | string, pattern | yes | no | no | `RecordId` | `^[a-z][a-z0-9-]{7,127}$` |
| `record_digest` | string, pattern | yes | no | no | `RecordDigest` | `^[0-9a-f]{64}$` |
| `created_at` | string, timestamp | yes | no | no | `Timestamp` | RFC3339 `Z`-suffix only |
| `phase_id` | string, pattern | yes | no | no | `PhaseIdentity` | `^[A-Za-z0-9.]{1,16}$` |
| `migration_epoch` | string, pattern | yes | no | no | `MigrationEpochToken` | `^(?!.*\.\.)[a-z0-9._-]{1,64}$` |
| `target` | string (const via allOf) | yes | no | no | `AuthorityKind` | const `"cltr"` |
| `source_authority` | string (const via allOf) | yes | no | no | `AuthorityKind` | const `"legacy"` |
| `source_epoch` | object (family-restricted reference) | yes | no | no | `RecordReference` | `record_family == "authority_epoch"` |
| `target_epoch` | object (family-restricted reference) | yes | no | no | `RecordReference` | `record_family == "authority_epoch"` |
| `evidence_requirements` | array of enum strings | yes (may be empty) | n/a | n/a | `Tuple[ReasonCode, ...]` | `maxItems: 24`, `uniqueItems: true` |
| `readiness_package_reference` | object (family-restricted reference, schema_id/schema_version required) | yes | no | no | `RecordReference` | `record_family == "readiness_package"`, `schema_id`/`schema_version` unconditionally required |
| `authorization_requirement` | boolean (const) | yes | no | no | `bool` | const `true` |
| `final_revision` | string, 1-256, printable ASCII | yes | no | no | `str` | pattern `^[\x20-\x7E]*$` |
| `state` | string enum (10 values) | yes | no | no | `RequestState` | fail-closed enum |
| `reason_code` | string enum (24 values) | **no** | **collapses to absent (Sec.6.3)** | yes | `Optional[ReasonCode] = None` | the one named exception |
| `limitations` | array of strings | yes (may be empty) | n/a | n/a | `Limitations` | `maxItems: 32` |
| `authority_disclosure` | object | yes | no | no | `AuthorityDisclosure` | `authority_role != "authoritative"` locally forbidden |

No `_extensions` field exists anywhere in this schema (Tier 1, strict,
`additionalProperties: false`, no escape hatch) — independently confirmed
against the live schema file (`"_extensions" not in schema["properties"]`).

### 2.2 `ReadinessPackage` (`records/readiness_package.schema.json`)

| Schema field | Wire type | Required | Null allowed | ABSENT allowed | Typed wrapper | Local invariant |
|---|---|---|---|---|---|---|
| `schema_id` … `created_at` | (same 6 envelope fields as above) | yes | no | no | `RecordEnvelope` | schema_id/record_type const |
| `phase_id` | string, pattern | yes | no | no | `PhaseIdentity` | as above |
| `transition_id` | string, pattern | yes | no | no | `TransitionId` | `^trans-[a-z0-9-]{2,122}$` |
| `migration_epoch` | string, pattern | yes | no | no | `MigrationEpochToken` | as above |
| `evidence_references` | array of generic references | yes (may be empty) | n/a | n/a | `Tuple[RecordReference, ...]` | `maxItems: 64`, **no `uniqueItems`**, no family restriction |
| `prerequisite_status` | string enum (3 values) | yes | no | no | `PrerequisiteStatus` | fail-closed enum |
| `findings` | array of `finding` objects | yes (may be empty) | n/a | n/a | `Tuple[Finding, ...]` | `maxItems: 128`, no uniqueness |
| `state` | string enum (5 values) | yes | no | no | `ReadinessState` | see conflict conditional, §3 below |
| `gate_result` | string enum (4 values) | **no** | **forbidden** | yes | `GateResult \| AbsentType = ABSENT` | generic ABSENT rule (no relaxation) |
| `limitations` | array of strings | yes (may be empty) | n/a | n/a | `Limitations` | `maxItems: 32` |
| `authority_disclosure` | object | yes | no | no | `AuthorityDisclosure` | as above |
| `_extensions` | object, string-valued map | **no** | **forbidden** | yes | `ExtensionMapping \| AbsentType = ABSENT` | `maxProperties: 32`, values must be strings only |

`Finding` (`$defs/finding`): `id` (pattern `^[A-Za-z0-9._-]{1,64}$`,
required), `verdict` (enum, 5 values: `CONFIRMED`, `NON-BLOCKING`,
`BLOCKING`, `PREREQUISITE`, `DEFERRED`, required), `title` (disclosure
text, 1-500 printable ASCII, required). `additionalProperties: false`.

## 3. Findings

All 130 independently-authored tests pass against the Phase 136AD
implementation exactly as it stands. No repair to `CutoverRequest` or
`ReadinessPackage` was required.

### 3.1 CONFIRMED-136AE-1 (Non-Blocking) — reason_code null vs. Layer 1 schema type

Contract Sec.6.3 (restated by the verified 136Y plan, Sec.9) authorizes
exactly one absent-vs-null relaxation: `CutoverRequest`'s own optional
field (`reason_code`) collapses "key absent" and "key present with
explicit `null`" to the same `None`. Phase 136AD's implementation does
this correctly (`payload.get("reason_code")`, independently re-verified
by `test_136ae_reason_code_omitted_becomes_none`,
`test_136ae_reason_code_explicit_null_becomes_none`, and
`test_136ae_reason_code_omitted_and_explicit_null_construct_equal_instances`).

Independently re-deriving the underlying shared schema
(`shared/failures.schema.json#/$defs/reason_code`), however, shows its
`type` is `"string"` only — no `"null"` in a type union. Direct
`jsonschema` Draft 2020-12 validation of a `CutoverRequest` payload with
`"reason_code": null` therefore **fails** at the raw schema (Layer 1)
layer, confirmed by
`test_136ae_explicit_null_for_reason_code_fails_live_schema_validation`.

This is a genuine two-layer discrepancy, disclosed but **not Blocking**:

- Layer 2 (`CutoverRequest.from_dict`) is a standalone construction API
  that does not require its caller to have first passed the payload
  through Layer 1 (`jsonschema`) validation — this matches every other
  typed model in this package, and matches how both 136AD's and this
  phase's own fixtures invoke `from_dict()` directly.
- The Layer 2 relaxation is exactly what contract Sec.6.3 and 136Y plan
  Sec.9 authorize; the model does not accept anything the contract
  forbids.
- No wire payload that has already passed Layer 1 validation can ever
  present `reason_code: null` to Layer 2 in the first place (Layer 1
  rejects it first) — so the practical exposure of this discrepancy is
  limited to payloads hand-constructed or otherwise not yet
  schema-validated, which is the documented, intended use of
  `from_dict()` as a standalone construction entry point.

No repair made. Recommend a future phase reconcile the shared
`reason_code` schema comment/type union with Sec.6.3's prose if a
Layer-1-reachable null is ever required; out of this phase's bounded
scope.

### 3.2 CONFIRMED-136AE-2 (Non-Blocking, inherited, out of scope) — stale wheel packaging guard in 136Z suite

`tests/test_cltr_authority_136z_shared_core.py::test_136z_wheel_contains_authority_shared_core_no_record_family_module`
(a `@pytest.mark.slow` test, excluded from Fast Green) asserts
`pcae/cltr/authority/request_readiness.py` is **absent** from the built
wheel. That assertion was correct through Phase 136AB but became stale
the moment Phase 136AD legitimately added `request_readiness.py` to the
package — the guard's `forbidden_modules` tuple was never updated to
drop it.

Confirmed via direct wheel inspection in this phase
(`python -m build --wheel`, `zipfile.namelist()`) that
`pcae/cltr/authority/request_readiness.py` and both schema files
(`cutover_request.schema.json`, `readiness_package.schema.json`) are
correctly present in the built wheel, and that the installed wheel
constructs both models successfully outside the repository checkout
(§6 below). The wheel's actual contents are correct; only the stale
136Z-owned test assertion is wrong.

This is a pre-existing regression inherited from Phase 136AD (the test
file was not touched by 136AE), unrelated to `CutoverRequest`'s or
`ReadinessPackage`'s own correctness, and lives in a file outside this
phase's allowed-file scope
(`tests/test_cltr_authority_136z_shared_core.py` is a 136Z-owned focused
test file, not part of Group 3's implementation or its own focused/
independent test modules). Repairing it would require touching a file
this task's governed contract does not authorize and would broaden
136AE beyond its bounded independent-verification purpose. Disclosed,
not repaired; recommended as a one-line follow-up (drop
`"request_readiness"` from that test's `forbidden_modules` tuple)
alongside Phase 136AF or a dedicated hygiene task.

### 3.3 Inherited findings re-confirmed, not re-litigated

- **CONFIRMED-136AC-1** (bare `ValueError` on enum construction):
  independently reproduced by
  `test_136ae_enum_construction_raises_bare_value_error_not_typed_model_error`.
  Unchanged classification (Non-Blocking: fails closed, accepts no
  invalid data, does not alter wire behavior).
- **Eight 135O/135P failures**: re-run in isolation
  (`tests/test_cltr_135o_integration.py`,
  `tests/test_cltr_migration_135p_verification.py`) — exactly 8 failures,
  identical identity (finalization-transaction receipt classification),
  fully unrelated to Request/Readiness models. No new failure.
- **136U scope-guard gap**: unchanged; not exercised by this phase's
  additions (confirmed via the adjacent `test_cltr_authority_136*` suite
  run, §5).

No other Blocking or Non-Blocking finding was produced.

## 4. Constant, discriminator, and enum enforcement — independently confirmed

- `target == "cltr"`, `source_authority == "legacy"`,
  `authorization_requirement is True`: each independently re-derived
  from the live schema's `const`, and each confirmed to reject every
  wrong value tested (wrong string, wrong case, leading/trailing
  whitespace, `False`, `1`, `"true"`, `None`) without ever silently
  overwriting the caller's value with the expected constant.
- `record_type`/`schema_id` discriminators: confirmed exact-match only,
  rejecting cross-family substitution, case variants, and trailing
  whitespace.
- `RequestState` (10), `ReadinessState` (5), `PrerequisiteStatus` (3),
  `GateResult` (4), `FindingVerdict` (5): every member set independently
  re-enumerated from the live schema and confirmed to match the Python
  enum exactly; construction of any value outside the closed set raises
  (bare `ValueError`, §3.3).

## 5. Conflict conditional — independently derived exact shape

The schema's `allOf`/`if`/`then` clause is exactly:

```
if state == "conflict":
    then findings must contain at least one item matching $defs/blocking_finding
```

This is **one-directional only**. It does not require the converse (a
`BLOCKING` finding present does not force `state == "conflict"`).
Independently confirmed both at the raw schema layer
(`test_136ae_schema_also_accepts_non_conflict_with_blocking_finding`) and
at the typed-model layer
(`test_136ae_non_conflict_state_with_blocking_finding_is_accepted_not_forced_to_conflict`)
— a `ReadinessPackage` with `state="partial"` and a `BLOCKING` finding
constructs successfully. Phase 136AD's implementation enforces exactly
this one-directional rule (matching the schema), despite its own
docstring/comment using an "iff" ("`<->`") characterization that is
imprecise prose but does not reflect an over-strict *implementation* —
the code itself checks only the `if`-direction. No repair needed; noted
as a documentation-wording imprecision only, not a code defect.

## 6. `_extensions` Tier 2 rule — independently confirmed scope

- Applies to `ReadinessPackage` **only** — `CutoverRequest` has no
  `_extensions` field at all (Tier 1, strict), independently confirmed
  against the live schema and against the dataclass field list.
- Values must be strings only (`additionalProperties: {"type": "string"}`);
  every non-string value type tested (int, bool, list, dict, `None`) is
  rejected. There is no "applies recursively" case: a nested
  object/array is rejected outright at the top level of that value, not
  traversed further.
- `maxProperties: 32`, matching `ExtensionMapping.MAX_EXTENSION_PROPERTIES`.
- Extension keys colliding with a canonical field name are rejected.
- Empty string values and an empty `_extensions` object are both
  accepted.

## 7. References, digests, timestamps, immutability, equality, serialization

- Every reference field (`source_epoch`, `target_epoch`,
  `readiness_package_reference`, `evidence_references[]`) preserves
  shape only; constructing with a syntactically valid but nonexistent
  target succeeds (`test_136ae_construction_succeeds_with_nonexistent_but_syntactically_valid_references`),
  and no socket/subprocess call occurs during construction
  (monkeypatched to raise if invoked).
- `evidence_references` has no local family restriction (generic
  `record_reference` shape) and no `uniqueItems` — duplicates, and same-
  id-different-digest pairs, are preserved verbatim in original order,
  never sorted or deduplicated.
- `evidence_requirements` correctly enforces `uniqueItems: true` and
  `maxItems: 24`.
- `findings` and `evidence_references` correctly enforce their
  respective `maxItems` (128, 64) with no uniqueness constraint.
- Digest/identifier wrapper types perform shape validation only; no
  `hashlib` call exists anywhere in `request_readiness.py`.
- Timestamps: every valid fractional-second precision and the exact `Z`
  wire form round-trip byte-for-byte; non-`Z` offset forms (`+00:00`,
  `-05:00`) are rejected outright, never normalized.
- Recursive immutability confirmed: mutating a caller's input list after
  construction does not affect the built model; `to_dict()` output
  mutation does not affect the model; `ExtensionMapping` deep-copies its
  input and exposes no direct-mutation path; `Finding` entries are
  themselves frozen dataclasses.
- Equality is structural and field-order-sensitive for evidence
  reference arrays (reordering evidence produces an unequal instance);
  same `record_id` with different content is not equal.
  `ReadinessPackage` is unhashable exactly when `_extensions` holds a
  real `ExtensionMapping` (unhashable by design); it remains hashable
  when `_extensions` is the default `ABSENT` sentinel.
- Minimal, maximal, and every conditional-branch round trip
  (`wire → model → wire`) reproduces the exact input dict for both
  families, independently re-validated against the live schema before
  and after.

## 8. No readiness evaluation / no request authorization / no evidence verification

AST-level scan of `request_readiness.py` for a closed list of forbidden
behavior symbols (`is_ready`, `calculate_readiness`,
`evaluate_readiness`, `can_cutover`, `approve`, `authorize`,
`is_authorized`, `execute_request`, `schedule_cutover`, etc.) — screened
as actual code constructs (function defs, assigned names, attribute
access), not a raw substring match against the module's own disclosure
prose — finds none. `dir()` on both classes exposes no forbidden method
name. A `ReadinessPackage` with `state="ready"`,
`prerequisite_status="unmet"`, and an unresolved `NON-BLOCKING` finding
still constructs successfully — the model performs no cross-field
readiness-sufficiency evaluation. A `CutoverRequest` with
`state="authorized"` constructs with no side channel proving
authorization actually occurred.

## 9. Runtime isolation and no-side-effect verification

- No file under `src/pcae/commands`, `src/pcae/core`, `src/pcae/runtime`,
  or any other `pcae.cltr` flat module imports `pcae.cltr.authority`
  (regex-scanned).
- `pcae.cltr.authority`'s own modules import no production lifecycle,
  finalization, notification, marker, receipt, commands, core, or
  runtime module (AST-scanned).
- Package import, both constructors, both serializers, equality, and
  `repr()` were exercised with `socket.socket`/`subprocess.Popen`
  monkeypatched to raise `AssertionError` on any call — none fired.

## 10. Scope-guard verification

`request_readiness.py`'s own class inventory contains exactly
`CutoverRequest` and `ReadinessPackage` among all record-family model
names (confirmed via AST). The four adjacent scope-guarded test files
(`test_cltr_authority_136z_shared_core.py`,
`test_cltr_authority_136aa_shared_core_independent.py`,
`test_cltr_authority_136ab_authority_core.py`,
`test_cltr_authority_136ac_authority_core_independent.py`) contain no
wildcard/`allow_all`-style broadening. See §3.2 for the one stale
(over-strict, not weakened) guard found in the 136Z suite.

## 11. Packaging verification

- `python -m build --wheel --sdist` succeeded; the wheel contains
  `pcae/cltr/authority/request_readiness.py` and both new schema files.
- Installed the built wheel (plus `jsonschema`) into a fresh venv
  outside the repository checkout; constructed a `CutoverRequest`
  end-to-end (`from_dict` → `to_dict` round trip) with no repository
  path, no network access, and no undeclared dependency. Confirmed
  `HumanAuthorization` and the other eleven later models are absent from
  the installed package (`hasattr` check).

## 12. Regression results

| Suite | Command | Result |
|---|---|---|
| New 136AE independent suite | `pytest tests/test_cltr_authority_136ae_request_readiness_independent.py -q` | 130 passed |
| 136AD/136AC/136AB/136AA/136Z together | `pytest tests/test_cltr_authority_136a{a,b,c,d}_*.py tests/test_cltr_authority_136z_shared_core.py -q` | 866 passed, 1 skipped, 1 failed (§3.2, pre-existing, unrelated) |
| Fast Green | `pytest -m "fast_green" -n auto -ra --durations=20 -q` | 4391 passed |
| CLTR canonicalization + schema_runtime suites | `pytest tests/test_cltr_canonicalization.py tests/test_schema_runtime_*.py -q` | 146 passed |
| 135O/135P inherited-failure suites | `pytest tests/test_cltr_135o_integration.py tests/test_cltr_migration_135p_verification.py -q` | 8 failed (identical, pre-existing, disclosed), 21 passed |
| Wheel/sdist build + isolated install | `python -m build --wheel --sdist`, install in fresh venv | pass |

`passed_with_disclosed_inherited_failures` applies to the 135O/135P run
(exact failure identity and unrelatedness demonstrated, §3.3) and to the
136Z packaging-guard suite (exact failure identity, pre-existing, and
unrelated to Request/Readiness correctness, §3.2). No new failure was
observed anywhere in this phase's regression evidence. A complete,
unbounded full-repository suite run was not attempted in this phase
(consistent with the documented, inherited "repeated full-suite bounded
incompleteness" condition and this phase's explicit no-broad-
infrastructure-repair boundary); the targeted suites above are the
bounded diagnostic for this phase and show no hang, no new failure, and
no stall contribution from `request_readiness.py`.

## 13. Verdict

**REQUEST AND READINESS MODELS VERIFIED WITH NON-BLOCKING FINDINGS —
READY FOR AUTHORIZATION AND CANDIDATE MODEL IMPLEMENTATION**

No unresolved Blocking finding remains. Two Non-Blocking findings are
disclosed (§3.1, §3.2), neither repaired, both out of this phase's
bounded scope or intentionally reserved for a dedicated follow-up.
`CutoverRequest` and `ReadinessPackage` remain exactly as implemented by
Phase 136AD; no code change was made to
`src/pcae/cltr/authority/request_readiness.py` in this phase. Runtime
remains Observed / observe / execution unavailable. Legacy lifecycle
remains the sole production authority; CLTR remains derivative.

Recommended next phase: **136AF — Stage 3 Typed Authority Model
Authorization and Candidate Implementation** (implementing only
`HumanAuthorization`, `CutoverCandidate`, `Certification`).

## 14. Telegram finalization disclosure

See `.pcae/phase-completion-report.md` for the actual dispatch-attempt
and evidence-persistence facts recorded at finalization time.
