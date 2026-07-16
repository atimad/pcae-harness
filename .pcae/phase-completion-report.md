# Phase 136G Complete — Validation Engine and Strict JSON Parsing Independent Verification

## Phase identity

- Phase ID: `136G`
- Status: completed
- Classification: independent verification, with two Blocking-defect repairs within the generic schema-runtime boundary
- Report completeness: complete

## Summary

Phase 136G independently re-derived, reproduced, mutated, and
adversarially attacked the generic Draft 2020-12 validation-engine,
strict-parser, loader, registry, and shape-validation infrastructure
introduced by Phase 136F (`src/pcae/schema_runtime/`,
`src/pcae/schema_resources/`), trusting none of 136F's own tests, report
prose, or classifications. Full detail in
`docs/PHASE_136_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_INDEPENDENT_VERIFICATION.md`.

Read both `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`
(2246 lines, Phase 136E) and
`docs/PHASE_136_DRAFT_2020_12_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_PREREQUISITE.md`
(563 lines, Phase 136F) in full, plus every line of 136F's implementation
source and test files, before writing a single new test.

Wrote **68 new, independent adversarial tests**
(`tests/test_schema_runtime_136g_independent_verification.py`) against
**fresh fixture schemas** authored by this phase
(`tests/fixtures/schema_runtime_136g/`), deliberately exercising Draft
2020-12 features 136F's own fixtures did not cover (`prefixItems`,
`contains`/`minContains`/`maxContains`, `dependentRequired`, `$anchor`,
Boolean schemas), plus fresh attacks on the strict parser, resource
limits, loader containment, registry no-network/determinism behavior,
duplicate-`$id` substitution, the shape-validation API's robustness,
error-vocabulary reachability, no-authority (including a dynamic-import
defeat attempt 136F's own doc explicitly flagged as untested), and
filesystem non-mutation.

**Found and repaired two genuine Blocking defects**, both within the
generic schema-runtime boundary:

1. **`BLOCKING-136G-1`/`-1b`** — `parse_strict_json` (a ~500-level-deep,
   byte-tiny nested document) and, independently, `validate_record_shape`
   (a ~300-level-deep record validated against a self-referential
   schema) could each raise an **uncaught `RecursionError`**, directly
   contradicting the parser's own documented "never raises on ordinary
   invalid input" contract. Repaired with a new
   `DEFAULT_MAX_NESTING_DEPTH` (`limits.py`, enforced in
   `json_parser.py`'s `_Parser._check_depth`) and a new
   `DEFAULT_MAX_RECORD_DEPTH` (`limits.py`, enforced in `validation.py`
   via a newly added, **explicitly iterative (non-recursive)**
   depth-scan function `_exceeds_max_depth`, so the guard itself cannot
   be defeated by the same class of attack). Both limits are exposed as
   new, independently configurable keyword arguments
   (`max_depth`/`max_record_depth`) consistent with the existing
   `max_bytes`/`max_issues` parameter style. No new error code was
   needed for the parser path (reuses `invalid_json`); the record-depth
   path reuses the previously-unreachable `internal_validation_error`
   code, which is now genuinely produced.
2. **`BLOCKING-136G-2`** — `validate_record_shape(..., max_issues=0)`
   silently reported `OutcomeStatus.VALID` for a genuinely, unambiguously
   invalid record (missing a required field), because status was
   decided from the *truncated* issue tuple (`errors[:max_issues]`)
   rather than the full, untruncated validator error list — a
   fail-open misclassification. Repaired by deciding status from the
   untruncated `errors` list; the returned `issues` tuple is still
   correctly truncated to `max_issues`, but no longer drives `status`.

Both repairs are covered by new regression tests
(`test_136g_deeply_nested_array_fails_closed_instead_of_crashing`,
`test_136g_deeply_nested_object_fails_closed_instead_of_crashing`,
`test_136g_nesting_just_under_limit_still_accepted`,
`test_136g_max_depth_is_configurable_per_call`,
`test_136g_deeply_nested_record_against_recursive_schema_fails_closed_instead_of_crashing`,
`test_136g_record_depth_just_under_limit_still_validated`,
`test_136g_record_depth_guard_is_configurable_per_call`,
`test_136g_record_depth_guard_uses_iterative_not_recursive_walk_and_survives_extreme_depth`,
`test_136g_max_issues_zero_returns_no_issues_but_marks_invalid`,
`test_136g_max_issues_one_returns_exactly_one`,
`test_136g_excessive_max_issues_does_not_error`), and by an updated
136F-era self-referential-mapping test now asserting the strictly
correct (and more robust) outcome.

Independently rebuilt the dependency in a second, fully clean-room
virtual environment (system Python 3.14.5, no lockfile): `pip` resolved
`jsonschema` 4.26.0 / `referencing` 0.37.0 — both newer than 136F's
pinned 4.25.1/0.36.2, both still within the frozen `>=4.18,<5` range —
confirming future patch/minor upgrades do not silently change the
selected `Draft202012Validator` class or observable behavior.
Independently proved no-network behavior against a wider set of
transport primitives than 136F's own tests exercised
(`socket.create_connection`, `socket.getaddrinfo`,
`urllib.request.urlopen`, in addition to 136F's `socket.socket`).
Independently proved the no-authority AST/text-scan boundary cannot be
defeated by a dynamic-import mechanism
(`importlib.import_module`/`__import__`/`eval`/`exec` — zero such
mechanisms exist anywhere in the package) — an item 136F's own doc
explicitly flagged as an open independent-verification requirement.

Disclosed several non-blocking findings, none Blocking: `CONFIRMED-136G-1`
(two of the frozen vocabulary's 13 codes, `unsupported_schema_version`
and `unsupported_dialect`, remain unreachable dead code — a third,
`internal_validation_error`, became reachable as a side effect of the
`BLOCKING-136G-1b` repair); `CONFIRMED-136G-2` (format non-enforcement
independently reconfirmed with a fresh schema); `CONFIRMED-136G-3`/`-4`
(dependency-failure exception wrapping is fail-closed but inconsistent
between a fully-absent `jsonschema` and a below-floor version); and
`CONFIRMED-136G-5` (an unresolved, symlink-backed trusted root causes a
fail-closed — safe-direction — false containment rejection). One
`PREREQUISITE-136G-1` finding is deferred to 136H (`validate_record_shape`'s
`Mapping` contract is documentation-only, not runtime-enforced). One
`DEFERRED-136G-1` (schema-authored ReDoS risk, out of this phase's
trusted-schema-root threat model) and `DEFERRED-136G-2` (schema manifest
implementation, independently reconfirmed correctly deferred) are
carried forward.

134 non-slow schema_runtime tests pass (69 from 136F + 68 from 136G − 3
`slow`-deselected), plus 3 slow packaging tests — **137 passed, 0
failed** total. Fast Green re-run **after both repairs**: **4391
passed**, identical to the 136F baseline, zero regressions. Full
unmarked suite freshly run in this phase's own environment after both
repairs: **20196 passed, 19 failed, 20215 total, 1122.39s**. The 19
failures are byte-for-byte the same node IDs and assertion messages
136F's own report already classified as pre-existing (unrelated to
`schema_runtime`); 20196 is exactly 136F's 20128 plus this phase's 68
new tests, confirming zero new regressions.

No Stage 3 companion executable schema, shared enum schema,
`AuthorityEpoch`/`AuthorityState`/`CutoverRequest`/`ReadinessPackage`
schema, authorization/candidate/certification/CAS/publication schema,
recovery/reconciliation schema, notification/marker/receipt binding,
Stage 3 typed record model, cross-record semantic validator, authority
resolver, authority-state persistence, or current-authority pointer was
created. No cutover request, readiness package, authorization,
candidate, certification, publication attempt, conflict record, or
recovery journal was created. Schema validity establishes no lifecycle
authority, cutover eligibility, authorization, publication success, or
recovery truth. No authority epoch changed. No CLTR authority was
created. No legacy authority was demoted or retired. No production
lifecycle behavior changed. No execution capability was introduced.
Legacy lifecycle remains the sole production authority; CLTR remains
derivative. Runtime remains Observed, maximum capability observe,
execution availability unavailable throughout.

## Evidence and validation

- Governed phase commits: main verification/repair commit and
  finalization commit(s) (hashes recorded after this report is
  committed, per the same multi-commit pattern used by 136F).
- Governance and read-only inspection commands actually run and their
  results (re-run fresh, this phase, after both repairs):
  - `pcae health`: healthy.
  - `pcae check`: passed.
  - `pcae status coherence`: coherent.
  - `pcae doctor task-memory`: clean.
  - `pcae push check`: ready before, pushed after, `origin/main..HEAD`
    is `0`.
  - `pcae runtime inspect`: Observed / observe / execution unavailable,
    unchanged before and after this phase's changes.
  - `pcae notify status`: Telegram configured, enabled, ready for
    outbound delivery.
  - Read-only reconciliation for 136A–136F, re-run at phase start and
    again before finalization (mutation: none, inspection only in every
    case): 136A `conflict`/`not_dispatched`; 136B `not_delivered`/
    `not_dispatched`; 136C `not_delivered`/`not_dispatched`; 136D
    `not_delivered`/`not_dispatched`; 136E `not_delivered`/
    `not_dispatched`; 136F `reconciled`/`already_dispatched`. 136D's and
    136E's own frozen report text claimed `reconciled` at their own
    finalization time, but a fresh independent re-check today observes
    `not_delivered` for both — an extension of the identical pattern
    136E's own report already disclosed for 136C ("incomplete
    bookkeeping in [the prior phase's] own freeze-time narrative, not a
    change in underlying evidence"). Disclosed, not repaired, not
    redispatched, per explicit read-only-reconciliation instruction.
    136F itself reconciles cleanly.
- Combined `tests/test_schema_runtime_*.py` (136F's 69 + 136G's 68):
  **137 passed, 0 failed** (134 non-slow + 3 slow packaging, all
  explicitly run).
- Fast Green (`python -m pytest -m fast_green -n auto`), re-run **after**
  both repairs: **4391 passed**, identical to the 136F baseline —
  confirms zero regressions from either repair.
- Full unmarked suite (`python -m pytest -n auto`), freshly run in this
  phase's own environment after both repairs: **20196 passed, 19
  failed, 20215 total, 1122.39s (0:18:42)**. All 19 failing node IDs
  (`test_advisory_runtime_contract.py`, `test_advisory_runtime_architecture.py`,
  `test_phase_reports.py`, `test_rendering_134e5.py`,
  `test_finalization_transaction_134e10.py` (5), `test_cltr_migration_135p_verification.py`
  (4 parametrized), `test_bootstrap_todo_consistency.py` (2),
  `test_cltr_135o_integration.py` (4)) are byte-for-byte identical to
  136F's own already-classified, already-independently-reproduced
  pre-existing failure set; none touch `schema_runtime`/`schema_resources`.
  See `docs/PHASE_136_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_INDEPENDENT_VERIFICATION.md`
  §20 for full detail.
- Independent dependency re-verification: `pip show` re-queried directly
  (not copied from 136F's report) for `jsonschema`, `referencing`,
  `jsonschema-specifications`, `rpds-py`, `attrs` — versions and MIT
  licenses reconfirmed. A second, fully clean-room venv (system Python
  3.14.5, `python3 -m venv`, no lockfile, no cache reuse) independently
  confirmed `pip`-resolved `jsonschema` 4.26.0 / `referencing` 0.37.0
  (newer, still in-range) with the full schema_runtime suite passing
  identically.
- No-network proof, widened beyond 136F's own scope: monkeypatched
  `socket.socket`, `socket.create_connection`, `socket.getaddrinfo`, and
  `urllib.request.urlopen`; attempted unregistered `https://`, `http://`,
  `file://`, `data:`, `ftp://`, and custom-scheme `$ref` resolution — all
  fail closed with zero calls to any blocked primitive.
- No-authority/no-execution proof, widened beyond 136F's own scope:
  independently scanned for dynamic-execution mechanisms
  (`importlib.import_module`, `__import__(`, `getattr(sys.modules`,
  `exec(`, `eval(`) across every source file in both packages — zero
  matches, closing the specific open item 136F's own doc flagged.
  Independently grepped the entire `src/pcae/` tree outside
  `schema_runtime`/`schema_resources` for any reference to either
  package — zero matches, confirming genuinely unwired infrastructure.
- Filesystem-mutation proof: byte-for-byte snapshot comparison
  (`mtime_ns`, `size`) of `.pcae/`, `schemas/`, `tasks/`,
  `PROJECT_STATUS.md`, `CHANGELOG.md` before/after a representative
  cross-section of parse/registry/validate calls — zero mutation.

Full per-section detail (methodology, all 23 attack categories, every
finding with independent reproduction, packaging re-verification,
determinism proofs, and residual risk) is in
`docs/PHASE_136_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_INDEPENDENT_VERIFICATION.md`.

## Findings

- `BLOCKING-136G-1`/`-1b` (repaired): uncaught `RecursionError` in both
  `parse_strict_json` and `validate_record_shape` on deeply nested
  input; closed with new, independently configurable
  `DEFAULT_MAX_NESTING_DEPTH`/`DEFAULT_MAX_RECORD_DEPTH` limits and
  regression tests.
- `BLOCKING-136G-2` (repaired): `max_issues=0` silently reported `VALID`
  for a genuinely invalid record (fail-open); closed by deciding status
  from the untruncated validator error list.
- `CONFIRMED-136G-1`: two of 13 frozen error-vocabulary codes
  (`unsupported_schema_version`, `unsupported_dialect`) remain
  unreachable dead code; disclosed, not repaired (would require a larger
  loader-API restructuring better deferred to 136H's first real caller).
- `CONFIRMED-136G-2`: format non-enforcement independently reconfirmed
  with a fresh `format: date-time` schema.
- `CONFIRMED-136G-3`: absent-`jsonschema` import failure is a
  `SchemaResourceError`, not an `ImportError`; disclosed, non-blocking.
- `CONFIRMED-136G-4`: below-floor `jsonschema` install produces an
  unwrapped `ModuleNotFoundError` for the `referencing` import
  specifically; only reachable via a manually broken install; disclosed,
  non-blocking.
- `CONFIRMED-136G-5`: an unresolved, symlink-backed trusted root (e.g.
  macOS's `/var` → `/private/var`) causes a fail-closed (safe-direction)
  false containment rejection; disclosed, non-blocking; workaround
  (pre-resolve the root) independently verified.
- `PREREQUISITE-136G-1`: `validate_record_shape`'s `Mapping` contract is
  documentation-only, not runtime-enforced (no `isinstance(record, dict)`
  guard); deferred to 136H, the first phase expected to give this API a
  real caller.
- `DEFERRED-136G-1`: schema-authored ReDoS risk from catastrophic
  `pattern` regexes; out of this phase's trusted-schema-root threat
  model; flagged for the security review of whichever phase first
  authors real `pattern` keywords.
- `DEFERRED-136G-2`: schema manifest implementation; independently
  reconfirmed correctly deferred to the first schema-core implementation
  phase (`SchemaResourceInfo` already carries every field a manifest
  would need).

Zero unresolved Blocking findings.

## Safety and no-go confirmation

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. 136G independently verified generic schema-validation
infrastructure only. No Stage 3 companion executable schema or Stage 3
fixture was created. No Stage 3 typed model or semantic validator was
implemented. No authority resolver, authority state, or authority
pointer was implemented or changed. No cutover request, readiness
package, authorization, candidate, certification, publication attempt,
conflict record, or recovery journal was created. Schema validity does
not establish lifecycle authority, cutover eligibility, authorization,
publication success, or recovery truth. No authority epoch changed. No
CLTR authority was created. No legacy authority was demoted. No legacy
authority was retired. No production lifecycle behavior changed. No
execution capability was introduced. Runtime remains Observed, maximum
capability remains observe, and execution availability remains
unavailable.

`schemas/cltr_cutover/` does not exist on disk. No Stage 3 record schema
exists. No typed Stage 3 model exists. No semantic validator exists. No
authority namespace exists. No authority pointer exists or changed. No
production artifact changed because of this phase's verification and
repair work.

## Final verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR COMPANION EXECUTABLE
SCHEMA SHARED CORE.** Every item in the strict phase boundary's
permitted list was exercised; every item in the prohibited list was
verified absent. Two genuine Blocking defects were found and repaired
within the generic schema-runtime boundary; zero unresolved Blocking
findings remain. "Ready for companion executable schema shared core"
applies only to the next bounded schema-implementation phase (136H) and
does not authorize authority behavior or Stage 3 activation.

## Recommended next phase

**136H — Companion Executable Schema Shared Core Implementation.** May
implement only: shared schema definitions; identifiers; digests;
references; timestamps; limitations; disclosures; enums; a schema
manifest foundation; fixtures and tests for that shared core. Must not
implement authority-bearing record schemas. Must explicitly re-derive
`DEFAULT_MAX_RECORD_DEPTH`/`DEFAULT_MAX_NESTING_DEPTH` against its own
actual schema shapes, and make a deliberate decision about
`PREREQUISITE-136G-1` (the `Mapping` runtime contract) before giving
`validate_record_shape` its first real caller.
