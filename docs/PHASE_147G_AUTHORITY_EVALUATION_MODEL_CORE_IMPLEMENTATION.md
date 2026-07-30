# Phase 147G — Authority Evaluation Model Core Implementation

## 1. Executive Summary

Phase 147G implements the standalone `pcae.authority_evaluation` package
exactly as frozen by AEMIC-001 v1.2: the immutable domain model
(`EligibleAuthorityDeclaration`, `AuthorityEvaluationOutcome`,
`EvaluationResult`), the pure `evaluate()` function, the read-only
`AuthorityRegistry` ABC (no concrete subclass), the eight-member exception
hierarchy, and `to_payload`/`from_payload` serialization for both record
types. This is the first implementation phase authorized under AEMIC-001;
no phase before it created any file under `src/pcae/authority_evaluation/`.

93 new tests were added in
`tests/test_phase_147g_authority_evaluation.py`, all passing. The full
`fast_green` tier (4391 tests) passes unchanged from its pre-phase
baseline. No file outside `src/pcae/authority_evaluation/**`,
`tests/test_phase_147g_authority_evaluation.py`, this report,
`.pcae/policy.toml` (a new, isolated `authority_evaluation` zone
declaration only), and ordinary governance bookkeeping was modified.

No concrete Registry implementation was built. No Interactive Workflow,
Session, Publication Coordinator, CHGR, readiness-package, runtime, or CLI
integration was performed. Runtime remains Observed / observe /
unavailable throughout.

**Overall Verdict: AUTHORITY EVALUATION MODEL IMPLEMENTED.**

## 2. Implemented Modules

```
src/pcae/authority_evaluation/
  __init__.py       48 lines  -- public re-exports only, no logic
  models.py        161 lines  -- EligibleAuthorityDeclaration,
                                  AuthorityEvaluationOutcome,
                                  EvaluationResult, EVALUATOR_VERSION
  evaluation.py     138 lines  -- the pure evaluate() function
  registry.py        50 lines  -- AuthorityRegistry ABC only
  errors.py           86 lines  -- 1 base + 8 named exceptions
  serialization.py   152 lines  -- to/from payload for both record types
```

No other module was created. No module was split into private
submodules. `registry.py` contains exactly one class
(`AuthorityRegistry`, the ABC) and no concrete subclass — verified by
`test_registry_module_has_no_concrete_registry`, which introspects every
class defined in that module.

## 3. Public API

`pcae.authority_evaluation.__init__` re-exports exactly the fourteen names
AEMIC-REQ-014 requires (verified by `test_public_reexport_surface_is_exact`):

- `EligibleAuthorityDeclaration`, `AuthorityEvaluationOutcome`,
  `EvaluationResult`
- `evaluate`
- `AuthorityRegistry`
- `AuthorityEvaluationError`, `InvalidClaimedIdentityError`,
  `InvalidTemplateReferenceError`, `MalformedDeclarationError`,
  `UnsupportedSchemaVersionError`, `MissingCitationTextError`,
  `TemplateIdentityMismatchError`, `AuthorityRegistryUnavailableError`,
  `AuthorityRegistryCorruptError`

`EVALUATOR_VERSION` (the fixed `"aem-evaluator/1.0"` constant, AEMIC-REQ-040)
and the four `serialization.py` functions
(`declaration_to_payload`/`declaration_from_payload`/`outcome_to_payload`/
`outcome_from_payload`) are public but live on their own modules, not
re-exported from `__init__`, mirroring AEMIC-REQ-014's own closed list
(neither is named in it).

`evaluate`'s signature matches §14 (AEMIC-REQ-072) exactly:

```python
def evaluate(
    template_ref: str,
    template_version: str,
    claimed_identity: str,
    declaration: EligibleAuthorityDeclaration | None,
    evaluated_at: str,
    evaluator_version: str,
    citation_text: str | None = None,
) -> AuthorityEvaluationOutcome: ...
```

## 4. Requirement Coverage

Every AEMIC-001 v1.2 requirement below maps to at least one implementing
location and at least one executable test in
`tests/test_phase_147g_authority_evaluation.py` (module abbreviated `t_147g`).

| Req(s) | Behavior | Implementation | Test(s) |
|---|---|---|---|
| AEMIC-REQ-006, 007, 014 | Package root, required modules, re-export stability | `src/pcae/authority_evaluation/**`, `__init__.py` | `test_package_has_exactly_the_required_modules`, `test_public_reexport_surface_is_exact` |
| AEMIC-REQ-008, 009 | Concrete Registry deferred; test double lives in `tests/` | `registry.py` (ABC only) | `test_registry_module_has_no_concrete_registry`; `_InMemoryRegistry`/`_UnavailableRegistry`/`_CorruptRegistry` (test doubles, `tests/`) |
| AEMIC-REQ-010-013 | Forbidden imports; zero-dependency direction | every module (stdlib + sibling-only imports) | `test_authority_evaluation_package_has_no_forbidden_imports` (parametrized over every package file); `test_evaluation_module_has_no_registry_import` |
| AEMIC-REQ-015-018 | `EligibleAuthorityDeclaration` construction, closed 6-field shape, immutability | `models.py` | `TestEligibleAuthorityDeclaration` (11 tests: valid construction, immutability, equality/hashing, each empty-field case, empty `eligible_identities`, non-str member, malformed timestamp, wrong `schema_version`, extra-field rejection) |
| AEMIC-REQ-019, 020 | `evaluate`'s seven-parameter closed input shape | `evaluation.py` | `TestEvaluateHappyPaths`, `TestEvaluateMalformedInputs` |
| AEMIC-REQ-021-023 | `AuthorityEvaluationOutcome` construction, closed 8-field shape, immutability | `models.py` | `TestAuthorityEvaluationOutcome` (7 tests) |
| AEMIC-REQ-022 | `citation_text` iff `ELIGIBLE` invariant | `models.py` `__post_init__` | `test_citation_present_on_non_eligible_raises`, `test_citation_absent_on_eligible_raises`, `test_outcome_cross_field_invariant_enforced_on_deserialize` |
| AEMIC-REQ-024-026 | `EvaluationResult` closed 3-member `Enum`, not a bare `str` | `models.py` | `TestEvaluationResult` (4 tests) |
| AEMIC-REQ-027-029 | Disclosure-only naming; `evaluation_result` distinguishes `ineligible` from `indeterminate` | whole package (naming); `evaluation.py` (branch logic) | `TestDisclosureOnlySemantics` (3 tests) |
| AEMIC-REQ-030-035 | Citation-text sourcing via `evaluate`'s own fifth parameter (F-147C-1 reconciliation, restated) | `evaluation.py` | `test_eligible`, `test_eligible_without_citation_raises` |
| AEMIC-REQ-036 | Exact `str` equality, no normalization | `evaluation.py` (identity comparisons), `test_unicode_round_trips_byte_for_byte` | Unicode round-trip confirms no transformation |
| AEMIC-REQ-037 | `(template_ref, template_version)` as the canonical identity tuple | `evaluation.py` | `TestEvaluateTemplateIdentityMismatch` |
| AEMIC-REQ-038 | `declaration_ref` deterministically derived, storage-agnostic | `evaluation.py` `_declaration_ref` | `test_eligible` (`declaration_ref == "tpl-1::v1"`), `test_ineligible` |
| AEMIC-REQ-039-041 | `schema_version` fixed literals; unsupported-version rejection | `models.py`, `serialization.py` | `test_wrong_schema_version_raises` (both types); `test_declaration_unrecognized_schema_version_raises`, `test_outcome_unrecognized_schema_version_raises` |
| AEMIC-REQ-042-044 | `AuthorityRegistry` ABC, one abstract method, pure/repeatable, `None`-not-raise for absence | `registry.py` | `TestAuthorityRegistry` (9 tests incl. ABC-cannot-instantiate) |
| AEMIC-REQ-045-049 | Duplicate/conflict, unavailable, corrupt — three distinct conditions (concrete-Registry-dependent, ABC-level contract demonstrated via test doubles) | `registry.py` contract; `_UnavailableRegistry`/`_CorruptRegistry` test doubles | `test_unavailable_registry_raises_distinct_from_corrupt_and_none`, `test_corrupt_registry_raises_distinct_from_unavailable_and_none`, `test_two_distinct_versions_resolve_independently` |
| AEMIC-REQ-050-051 | No ordering/enumeration on the ABC; authoring-time immutability named limitation | `registry.py` (no such method exists) | N/A — scoping requirement, confirmed by `registry.py`'s own one-method shape |
| AEMIC-REQ-052-063 | Filesystem persistence contract | **Deferred** — no concrete Registry in this phase | N/A per AEMIC-REQ-008; frozen for a future phase |
| AEMIC-REQ-064-071 | Failure taxonomy: 6 §13.1 + 2 §13.2 exceptions, no generic collapse | `errors.py` | `TestExceptionHierarchy` (9 tests); `test_no_bare_exception_types_collapse_named_errors` |
| AEMIC-REQ-072-077 | `evaluate` purity/totality/no-Registry-dependency/determinism/no-side-effects | `evaluation.py` | `TestEvaluateHappyPaths`, `TestEvaluateDeterminism`, `test_evaluate_has_no_registry_dependency` |
| AEMIC-REQ-078-079, 102, 107 | Security properties table; citation-fabrication risk unchanged; matching identity ≠ authority | `evaluation.py`, `models.py` | `test_matching_identity_does_not_by_itself_prove_authority`; `TestEvaluateMalformedInputs` (citation enforcement) |
| AEMIC-REQ-080-082 | Auditability: 8 stable fields (`evaluated_at` observational) | `models.py` | `TestAuthorityEvaluationOutcome`, `TestSerialization` |
| AEMIC-REQ-083-086 | Deferred integration boundary; no existing-behavior regression | N/A — no integration performed | Full `fast_green` suite (4391 passed) confirms zero regression |
| AEMIC-REQ-087-093 | Serialization: canonical dict, Unicode, mandatory-field emission, schema-version-first check | `serialization.py` | `TestSerialization` (14 tests incl. Unicode, missing/null field, unrecognized `schema_version`, unrecognized `evaluation_result`) |
| AEMIC-REQ-094 | No-Go boundary (this phase) | N/A | `git status --short` before/after (§8 below) |
| AEMIC-REQ-101 | `MissingCitationTextError` construction-time enforcement | `evaluation.py` | `test_eligible_without_citation_raises`, `test_ineligible_with_stray_citation_is_disregarded_not_raised`, `test_indeterminate_with_stray_citation_is_disregarded_not_raised` |
| AEMIC-REQ-103-106 | Template identity sourcing/mismatch, exact error precedence, non-collapse | `evaluation.py` | `TestEvaluateTemplateIdentityMismatch`, `TestEvaluateErrorPrecedence` (4 tests) |

## 5. Field Source Matrix

Every mandatory `AuthorityEvaluationOutcome` field, per branch, has exactly
one canonical construction source — all within `evaluate()` itself
(`evaluation.py`):

| Field | Producing function | Input source | Validation | Branch applicability |
|---|---|---|---|---|
| `template_ref` | `evaluate()` | `evaluate`'s own `template_ref` parameter, verbatim | Non-empty `str` → `InvalidTemplateReferenceError` (checked first, AEMIC-REQ-104 step 1) | ELIGIBLE, INELIGIBLE, INDETERMINATE (all three) |
| `template_version` | `evaluate()` | `evaluate`'s own `template_version` parameter, verbatim | Non-empty `str` → `InvalidTemplateReferenceError` (step 1) | All three |
| `claimed_identity` | `evaluate()` | `evaluate`'s own `claimed_identity` parameter, verbatim | Non-empty `str` → `InvalidClaimedIdentityError` (step 2) | All three |
| `evaluation_result` | `evaluate()` | Derived: `ELIGIBLE` iff `declaration is not None and claimed_identity in declaration.eligible_identities`; `INELIGIBLE` iff `declaration is not None` and not a member; `INDETERMINATE` iff `declaration is None` | Closed 3-member `EvaluationResult` (step 4) | Determines the branch itself |
| `declaration_ref` | `evaluate()` via `_declaration_ref(template_ref, template_version)` | Deterministic concatenation of `evaluate`'s own two identity parameters (never an opaque storage ID) | Non-`None` iff `declaration is not None`; `None` iff `INDETERMINATE` | ELIGIBLE/INELIGIBLE: non-`None`; INDETERMINATE: `None` |
| `citation_text` | `evaluate()` | Caller-supplied `citation_text` parameter, copied verbatim | `MissingCitationTextError` if `ELIGIBLE` and `None` (step 5); disregarded (never fabricated, never raised) if supplied alongside `INELIGIBLE`/`INDETERMINATE` | ELIGIBLE: non-`None`; INELIGIBLE/INDETERMINATE: always `None` regardless of caller input |
| `evaluated_at` | `evaluate()` | Caller-supplied `evaluated_at` parameter, verbatim | Non-empty, parseable ISO-8601 (`AuthorityEvaluationOutcome.__post_init__`) | All three (observational, not part of the determinism-equality tuple's content guarantee, AEMIC-REQ-080) |
| `evaluator_version` | `evaluate()` | Caller-supplied `evaluator_version` parameter, verbatim (callers pass this package's own `EVALUATOR_VERSION` constant) | Non-empty `str` | All three |
| `schema_version` | `AuthorityEvaluationOutcome.__post_init__` | Fixed literal `OUTCOME_SCHEMA_VERSION` (`"aem-outcome/1.0"`) | Must equal exactly | All three |

Step 3 (template identity mismatch, `TemplateIdentityMismatchError`) is
checked only when `declaration is not None`, strictly before step 4
(`evaluation_result` determination) — verified deterministic and
non-masking by `TestEvaluateErrorPrecedence`.

## 6. Exception Hierarchy

```
AuthorityEvaluationError (base)
├── InvalidClaimedIdentityError          (§13.1, domain)
├── InvalidTemplateReferenceError        (§13.1, domain)
├── MalformedDeclarationError            (§13.1, domain/authoring)
├── UnsupportedSchemaVersionError        (§13.1, domain)
├── MissingCitationTextError             (§13.1, domain)
├── TemplateIdentityMismatchError        (§13.1, domain/workflow)
├── AuthorityRegistryUnavailableError    (§13.2, infrastructure)
└── AuthorityRegistryCorruptError        (§13.2, infrastructure)
```

All eight are direct subclasses of `AuthorityEvaluationError` (verified by
`test_direct_subclass_of_base`, which asserts `exc_type.__bases__ ==
(AuthorityEvaluationError,)` for each). `test_no_bare_exception_types_collapse_named_errors`
confirms `errors.py` defines exactly these nine classes (base + eight),
no fewer, no generic collapse. `test_registry_exceptions_never_raised_by_evaluate`
confirms `evaluate()`'s own exception boundary never includes either
§13.2 exception.

## 7. Serialization

`declaration_to_payload`/`declaration_from_payload` and
`outcome_to_payload`/`outcome_from_payload` each: produce a plain `dict`
suitable for `json.dumps(..., sort_keys=True)`; check `schema_version`
before attempting any other field (AEMIC-REQ-093); raise
`UnsupportedSchemaVersionError` for an unrecognized version;
raise `MalformedDeclarationError` for any other missing, `null`, or
structurally invalid field (including a hand-crafted
`evaluation_result`/`citation_text` combination that would violate §6.1's
invariant — the underlying `AuthorityEvaluationOutcome` constructor is the
single enforcement point, reused rather than duplicated at the
serialization boundary). `eligible_identities` is serialized as a sorted
list for deterministic output despite being an unordered `frozenset` at
the model layer. Unicode members round-trip byte-for-byte with no
normalization (`test_unicode_round_trips_byte_for_byte`). No digest is
computed over either record type (AEMIC-REQ-092, unimplemented by
deliberate, disclosed design).

## 8. Registry Boundary

`registry.py` contains exactly one class: the `AuthorityRegistry` ABC,
with exactly one abstract method,
`resolve(template_ref: str, template_version: str) -> EligibleAuthorityDeclaration | None`.
No concrete subclass, no filesystem backend, no persistence, no caching,
no discovery logic exists anywhere under `src/pcae/authority_evaluation/`.
`evaluate()` never imports `registry.py` and never calls `resolve`
(`test_evaluation_module_has_no_registry_import`,
`test_evaluate_has_no_registry_dependency`) — the Registry lookup is
always performed upstream by `evaluate`'s own caller, with the result
passed in as the `declaration` parameter. Three test doubles
(`_InMemoryRegistry`, `_UnavailableRegistry`, `_CorruptRegistry`) live in
`tests/test_phase_147g_authority_evaluation.py` only, never in
`src/pcae/authority_evaluation/`, per AEMIC-REQ-009.

## 9. Security Review

Every property in AEMIC-001 §15's table is preserved unweakened:

- **Declaration spoofing / template substitution**: exact set-membership
  and exact `(template_ref, template_version)` matching only — no
  wildcard, regex, role-indirection, or partial/fuzzy match exists
  anywhere in `evaluation.py`.
- **Request/declaration identity mismatch**: `TemplateIdentityMismatchError`
  fails closed before `evaluation_result` is determined or any outcome is
  constructed (`TestEvaluateTemplateIdentityMismatch`,
  `TestEvaluateErrorPrecedence`).
- **Duplicate ambiguity, Registry poisoning, path traversal**: all remain
  concrete-Registry-implementation concerns, out of this phase's own
  scope (AEMIC-REQ-008); the ABC itself exposes no write path at all.
- **Replay / stale declarations**: `evaluate` is a pure function with no
  stateful replay concept at this layer;
  `EligibleAuthorityDeclaration`/`AuthorityEvaluationOutcome` are both
  immutable once constructed (verified by `test_immutable` on each type).
- **Authority escalation / circular trust**: `declared_by` is recorded for
  provenance only and is never evaluated
  (`evaluation.py` never reads it); no import anywhere in the package
  reaches Runtime, Permission Broker, or execution capability
  (`test_authority_evaluation_package_has_no_forbidden_imports`).
- **Outcome misuse as authorization**: no public name contains
  `authorize`/`grant`/`permit`/`allow`/`deny`
  (`test_no_public_name_implies_authorization`); a matching identity check
  does not, by itself, imply eligibility — `claimed_identity` must
  separately be a set member
  (`test_matching_identity_does_not_by_itself_prove_authority`).

This package's own disclosure-only semantics (§8) are unaffected by any
implementation decision made in this phase; no type, function, or module
grants, blocks, or conditions Confirmation, Readiness, Authorization, or
Publication.

## 10. Test Coverage

93 new tests in `tests/test_phase_147g_authority_evaluation.py`, organized
into 12 test classes plus 6 module-level tests, covering: model
construction/validation/immutability/equality/hashing for both record
types; the closed `EvaluationResult` enum; `evaluate`'s happy paths for
all three branches; malformed inputs for every §13.1 condition; template
identity mismatch; exact error-precedence ordering (4 dedicated tests);
determinism (including a no-side-effects-on-`declaration` check); the
`AuthorityRegistry` ABC via three distinct in-memory test doubles;
serialization round-trip including Unicode, missing/null fields, and
unrecognized `schema_version`/`evaluation_result`; disclosure-only naming
audit; the forbidden-import/package-boundary AST guard (parametrized over
every package file); and the full exception hierarchy.

```
python -m pytest tests/test_phase_147g_authority_evaluation.py -q
93 passed in 0.07s
```

Regression check — full `fast_green` tier:

```
python -m pytest -m fast_green -n auto -q
4391 passed, 105 warnings in 110.05s
```

(105 warnings are pre-existing `PytestCollectionWarning`s from unrelated
dataclasses literally named `Test*` in `src/pcae/core/canonical_engineering_evidence.py`,
unaffected by this phase.)

Regression check — full suite (`python -m pytest -n auto -q`): 26853
passed, 73 failed, 10 skipped on the first full run (before the fix
below); 26856 passed, 70 failed, 10 skipped on a second full run (after
the fix, and with `test_shell_gate`/`test_decision_log` no longer flaking).
`--lf` (last-failed) reruns isolated one genuine defect this phase itself
introduced —
`tasks/TODO.md`/`PROJECT_STATUS.md` consistency tests failed because this
phase's own first draft of `PROJECT_STATUS.md`'s "## Current Phase"
section wrote `Recommended next: **147H...` instead of the exact
`Recommended next phase: **147H...` wording
`_extract_recommended_next_phase_values` (`src/pcae/core/phase_reports.py`)
requires; fixed in place, re-verified by
`python -m pytest tests/test_bootstrap_todo_consistency.py -q` (one
additional test now passes). The remaining failures on both full-suite
runs are unrelated pre-existing conditions, none referencing
`authority_evaluation`: wheel/sdist packaging tests
(`test_136f`/`test_143e`/`test_136a*`/`test_cltr_cutover_136*`) failing on
`python -m build --wheel` in this environment; two advisory-runtime
directory-shape tests; one finalization-ordering test
(`test_phase_137i1`); one rendering-regression test
(`test_rendering_134e5`); and three `tasks/TODO.md` staleness tests whose
`🔜 Next` marker still names Phase 137T, a drift that long predates this
phase (a standalone roadmap-tracking reconciliation, disclosed separately
at §13/PROJECT_STATUS.md as open and unscheduled, not folded into Chapter
147). `python -m pytest --lf -q` before the fix: 70 failed, 3 passed
(environment flakiness: `test_shell_gate`/`test_decision_log` failed on
the first full run, passed on rerun). After the fix: 69 failed on `--lf`,
one fewer, confirming the fix closed exactly the one test this phase's own
diff affected and introduced no other regression.

## 11. No-Go Confirmation

This phase did not:

- implement any concrete `AuthorityRegistry` (filesystem or otherwise);
- modify `src/pcae/interactive_workflow/**`, `src/pcae/governance/**`, or
  `src/pcae/cltr/**`;
- modify any schema file under `src/pcae/schema_resources/**`;
- modify AEM-001, AEMIC-001, IWC-001, IWPC-001, PEC-001, CHGR-001,
  TAMC-001, TAMPC-001, or GAC-001;
- add any CLI/transport command or flag;
- gate, block, or condition Confirmation, Readiness, Authorization, or
  Publication on anything this package computes;
- change `Session`, `PublicationReadinessPackage`,
  `PublicationCoordinator`, or CHGR construction/verification/inspection;
- enable execution capability of any kind, or change runtime state,
  policy, or strategic lineage.

Files created or modified by this phase: the six
`src/pcae/authority_evaluation/**` modules;
`tests/test_phase_147g_authority_evaluation.py`; this report;
`.pcae/policy.toml` (one new, isolated `authority_evaluation` zone
declaration with zero cross-zone dependency, mirroring the existing
per-zone declaration pattern — required only because
`pcae check`/`task`'s own zone-membership machinery needs a name for the
new file paths this phase introduces, not a widening of any existing
zone's own authority); and ordinary governance bookkeeping (task lifecycle
files, `tasks/DONE.md`, `PROJECT_STATUS.md`,
`.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`).

## 12. Overall Verdict

**AUTHORITY EVALUATION MODEL IMPLEMENTED.**

Every module named at AEMIC-REQ-007 exists with exactly the shape §3-§18
freeze. No concrete Registry exists (AEMIC-REQ-008, by design). Every
mandatory `AuthorityEvaluationOutcome` field has exactly one reachable,
closed-input construction source for every one of the three
`EvaluationResult` branches, including `INDETERMINATE` (the BF-147F.1-1
repair's own central guarantee, now implemented and tested). The failure
taxonomy is coherent and non-collapsing. Error precedence is exact and
independently verified never to mask an earlier check behind a later one.
Determinism, serialization, disclosure-only semantics, and Registry
isolation all hold under adversarial test. The full pre-existing test
suite passes unchanged.

## 13. Recommended Next Phase

**147H — Authority Evaluation Model Core Independent Implementation
Verification.** Must independently reconstruct the implementation from
AEMIC-001 v1.2 alone, attempt to falsify every production behavior claimed
above, independently derive the field-source mapping (§5 here) from first
principles rather than trusting this report's own account of it, re-attack
determinism, serialization, exception ordering, disclosure-only semantics,
and Registry isolation, and verify that the implementation matches the
contract rather than merely passing its own self-authored tests. This
recommendation is not an authorization.
