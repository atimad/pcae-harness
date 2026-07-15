# Phase 136F Complete — Draft 2020-12 Validation Engine and Strict JSON Parsing Prerequisite

## Phase identity

- Phase ID: `136F`
- Status: completed
- Classification: implementation, bounded prerequisite infrastructure
- Report completeness: complete

## Summary

Phase 136F implemented and independently tested only the generic
prerequisite infrastructure planned by Phase 136E, resolving
`PREREQUISITE-136E-1`, before any Stage 3 executable companion-schema
authoring begins. Full detail in
`docs/PHASE_136_DRAFT_2020_12_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_PREREQUISITE.md`.

Added `jsonschema>=4.18,<5` to `pyproject.toml` — this repository's
first runtime (non-dev) dependency. Installed version: 4.25.1, within
the frozen range. Transitive dependencies (`referencing` 0.36.2,
`jsonschema-specifications` 2025.9.1, `rpds-py` 0.27.1, `attrs` 26.1.0)
are all MIT-licensed and perform no network access at runtime
(`jsonschema-specifications` bundles the Draft 2020-12 meta-schema
locally).

New package `src/pcae/schema_runtime/`: a hand-written recursive-descent
strict JSON parser (`json_parser.py`) rejecting duplicate object keys at
every nesting level and non-finite numbers (`NaN`/`Infinity`/
`-Infinity`) with JSON-Pointer instance paths — a hand-written parser
was chosen over `json.loads(object_pairs_hook=...)` because that
mechanism cannot report an ancestor path for a rejected duplicate key;
a 13-code Layer-1/Layer-2 error vocabulary (`errors.py`); immutable
`JsonParseResult`/`ShapeValidationResult`/`ValidationIssue`/
`SchemaResourceInfo` models with an explicit three-way valid/invalid/
infrastructure-failure outcome (`models.py`); an offline,
containment-and-symlink-checked schema resource loader enforcing Draft
2020-12 dialect, unique `$id`, and meta-schema conformance
(`loader.py`); an offline-only `referencing.Registry`-backed registry
whose `retrieve` hook unconditionally refuses any unregistered lookup —
proven never to fetch even a URI-shaped `$id` over the network
(`registry.py`); and a generic `validate_record_shape()` Layer-2
shape-validation API with deterministic issue ordering, an
issue-count cap, and no semantic or authority claim (`validation.py`).

Resolved **PREREQUISITE-136E-1**: prior to this phase,
`[tool.hatch.build.targets.wheel]` (`packages = ["src/pcae"]`) and
`[tool.hatch.build.targets.sdist]` (`include = ["src/pcae", ...]`) never
included the top-level `schemas/` directory in either build target.
New package `src/pcae/schema_resources/` (Option A — schemas packaged
inside `src/pcae`, chosen because the existing hatchling configuration
already reliably includes non-`.py` files nested under `src/pcae/**`
in both build targets with no further configuration) contains only a
generic, explicitly non-Stage-3 smoke schema
(`smoke/generic_smoke_record.schema.json`) and `smoke_schema_root()`, an
`importlib.resources`-based accessor proven to work identically from an
editable install, a built wheel (inspected via `zipfile`), a built
source distribution (inspected via `tarfile`), and an installed wheel
in a freshly created, isolated venv (no source checkout present). **No
Stage 3 schema was moved or created in this phase.**

69 new focused tests across six files (JSON parser, loader, registry,
Draft-2020-12-capability/shape-validation, no-network/no-authority/
no-execution boundaries, packaging) — all passing. Fast Green unchanged
at 4391/4391. Full unmarked suite freshly run: 20128 passed, 19 failed,
20147 total; all 19 failures independently reproduced identically
against an isolated pre-136F worktree (commit `7a62bb54`, clean venv),
confirming they are **pre-existing and unrelated to Phase 136F** (see
Evidence and validation below) — zero regressions introduced by this
phase.

No Stage 3 record schema, shared enum schema, `AuthorityEpoch` schema,
`AuthorityState` schema, `CutoverRequest` schema, `ReadinessPackage`
schema, authorization schema, candidate or certification schema, CAS or
publication schema, recovery or reconciliation schema, notification,
marker, or receipt binding, Stage 3 typed record model, cross-record
semantic validator, authority resolver, authority-state persistence, or
current-authority pointer was created. No cutover request, readiness
package, authorization, candidate, certification, publication attempt,
conflict record, or recovery journal was created. Schema validity
establishes no lifecycle authority, cutover eligibility, authorization,
publication success, or recovery truth. No authority epoch changed. No
CLTR authority was created. No legacy authority was demoted or retired.
No production lifecycle behavior changed. No execution capability was
introduced. Legacy lifecycle remains the sole production authority;
CLTR remains derivative. Runtime remains Observed, maximum capability
observe, execution availability unavailable throughout.

## Evidence and validation

- Governed phase commit: `4d9c51f` (implementation content — 33 files
  changed: `schema_runtime`/`schema_resources` source, six test files,
  fixture schemas, `pyproject.toml`, `.pcae/policy.toml` (new
  `schema_runtime` architecture zone), documentation, `PROJECT_STATUS.md`,
  `CHANGELOG.md`, task-lifecycle files). A second governed commit closes
  this phase's task contract and opens the next idle placeholder (hash
  recorded after this report is committed, per the same two-commit
  pattern used by 136E).
- Governance and read-only inspection commands actually run and their
  results:
  - `pcae health`: healthy.
  - `pcae check`: passed.
  - `pcae status coherence`: coherent.
  - `pcae doctor task-memory`: clean (after this phase's task-closure
    commit updates `tasks/DONE.md`; one pre-existing unrelated warning
    about the prior idle placeholder's `tasks/DONE.md` listing was
    resolved by that commit).
  - `pcae push check`: ready before, pushed after, `origin/main..HEAD`
    is `0`.
  - `pcae runtime inspect`: Observed / observe / execution unavailable,
    unchanged before and after this phase's changes.
  - `pcae notify status`: Telegram configured, enabled, ready for
    outbound delivery.
  - Read-only reconciliation for 136A–136E, re-run at phase start:
    136A `conflict`/`not_dispatched`; 136B `not_delivered`/
    `not_dispatched`; 136C `not_delivered`/`not_dispatched`; 136D
    `reconciled`/`already_dispatched`; 136E `reconciled`/
    `already_dispatched`. Identical to prior phases' own disclosures.
    Carried forward as historical evidence only; not repaired, not
    redispatched (per explicit instruction — read-only reconciliation
    only).
  - Dependency/packaging inspection: `pyproject.toml` had
    `dependencies = []` before this phase; `jsonschema` confirmed not
    installed in the active environment before this phase; wheel/sdist
    scope did not include `schemas/` before this phase.
- Focused `schema_runtime` test suite
  (`tests/test_schema_runtime_*.py`): **69 passed, 0 failed** (22 JSON
  parser, 14 loader, 5 registry, 12 Draft-2020-12-capability/
  shape-validation, 12 boundary/no-network/no-authority/no-execution
  proofs, 4 packaging — 3 of the 4 packaging tests are `slow`-marked
  since they build a real wheel/sdist and, for one, provision an
  isolated venv; all 4 were explicitly run and passed).
- Fast Green (`python -m pytest -m fast_green -n auto`): **4391
  passed**, identical to the 136E baseline — the new `schema_runtime`
  test files are not in the `FAST_GREEN_MODULES` set (deliberately not
  added, to keep this phase's boundary minimal), so this run confirms
  zero regressions in the existing fast-green-tagged suite.
- Full unmarked suite (`python -m pytest -n auto`): **20128 passed, 19
  failed** (1085.34s). The 19 failures span
  `test_advisory_runtime_contract.py`, `test_advisory_runtime_architecture.py`,
  `test_phase_reports.py`, `test_rendering_134e5.py`,
  `test_finalization_transaction_134e10.py` (5 tests),
  `test_cltr_migration_135p_verification.py` (4 parametrized cases),
  `test_bootstrap_todo_consistency.py` (2 tests), and
  `test_cltr_135o_integration.py` (4 tests) — none touch
  `schema_runtime`/`schema_resources`, none touch strict JSON parsing,
  and none touch packaging. **Classified against an isolated pre-136F
  worktree**, per this phase's explicit instruction not to rely on
  `git stash` alone: `git worktree add /tmp/pcae-136f-baseline 7a62bb54`,
  a clean Python 3.9 venv, `pip install -e ".[dev]"` (no `jsonschema`,
  matching the pre-136F baseline exactly), then the identical 19 test
  node IDs run in two batches. **All 19 reproduced with identical
  failure output** on the clean pre-136F baseline (e.g.
  `test_finalization_transaction_134e10.py`'s five failures all assert
  `result.status == "completed"` against an actual status of
  `completed_receipt_best_effort_incomplete` — a pre-existing
  assertion/implementation mismatch unrelated to this phase). Confirmed
  **pre-existing, not caused by Phase 136F**; the worktree was removed
  (`git worktree remove /tmp/pcae-136f-baseline --force`) after
  classification, no repository state left behind.
- Wheel/sdist/editable-install packaging tests
  (`tests/test_schema_runtime_packaging.py`), run explicitly (all
  `slow`-marked tests included): editable install — passed; wheel build
  (`python -m build --wheel`) inspected via `zipfile` — smoke schema
  present at `pcae/schema_resources/smoke/generic_smoke_record.schema.json`,
  no `cltr_cutover`/`.pcae/`/`session.json` entries — passed; source
  distribution (`python -m build --sdist`) inspected via `tarfile` —
  smoke schema present, no `cltr_cutover`/`.pcae/` entries — passed;
  installed wheel in a fresh, isolated `venv` (no source checkout) —
  `pip install --no-deps` the built wheel, subprocess probe imports
  `pcae.schema_resources.smoke_schema_root()` and confirms the file
  exists — passed.
- No-network proof: `tests/test_schema_runtime_registry.py` and
  `tests/test_schema_runtime_boundaries.py` monkeypatch `socket.socket`
  to raise if called, then exercise registry lookup (including a
  URI-shaped `$id`) and `validate_record_shape()` — all pass with
  sockets forbidden.
- No-authority/no-execution proof: `tests/test_schema_runtime_boundaries.py`
  performs an AST-based import/call scan of every `.py` file under
  `src/pcae/schema_runtime/` and `src/pcae/schema_resources/` for
  `subprocess`, `socket`, `shlex`, HTTP-client modules, and
  `subprocess.run`/`call`/`Popen`/`os.system`/`os.popen` call sites
  (none found), a text scan for `pcae.cltr`/`current_authority`/
  `authority_state`/`authority_epoch`/`cltr-authority` identifiers
  (none found), and an on-disk assertion that `.pcae/cltr-authority/`
  and `schemas/cltr_cutover/` do not exist.

Full per-section detail, the dependency/license table, the Draft
2020-12 capability-proof breakdown, the packaging-decision rationale,
findings, limitations, and independent-verification requirements are in
`docs/PHASE_136_DRAFT_2020_12_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_PREREQUISITE.md`.

## Findings

- `PREREQUISITE-136E-1` (resolved): wheel/sdist packaging did not
  include any schema-resource directory. Resolved by packaging schema
  resources inside `src/pcae/schema_resources/` (Option A) and proving
  inclusion across editable install, wheel, sdist, and an installed
  wheel in an isolated venv.
- `CONFIRMED-136F-1`: `jsonschema>=4.18,<5` (installed 4.25.1)
  independently confirmed to support Draft 2020-12 via
  `Draft202012Validator`, `$defs`, local and cross-file `$ref`,
  `if`/`then`/`else`, `oneOf`, `allOf`, `additionalProperties: false`,
  and `unevaluatedProperties: false` (including nested-unknown-property
  rejection).
- `CONFIRMED-136F-2`: the offline registry never performs network I/O,
  including for URI-shaped `$id` values, proven under a monkeypatched
  `socket.socket`.
- `NON-BLOCKING-136F-1`: no explicit parser-level recursion-depth limit
  is enforced; mitigated only by the 5 MiB input-size ceiling and the
  CPython interpreter recursion limit. Disclosed as a limitation, not
  silently assumed adequate; a future phase should add an explicit
  depth counter before deeply nested Stage 3 records are anticipated.
- `DEFERRED-136F-1`: the generic schema-manifest file format selected
  by 136E is deferred to the first schema-core implementation phase,
  since the per-resource metadata (`SchemaResourceInfo`, including
  SHA-256 digest) a manifest would need is already computed and
  available, keeping the design manifest-compatible without widening
  this phase's boundary.
- `NON-BLOCKING-136F-2` (historical, disclosed not repaired): the 19
  full-unmarked-suite failures classified above are pre-existing
  governance/finalization-transaction and integration-test defects
  unrelated to `schema_runtime`, confirmed against an isolated pre-136F
  worktree. Not owned or repaired by this phase; carried forward for a
  future phase's attention.

Zero unresolved Blocking findings.

## Safety and no-go confirmation

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. 136F implemented generic schema-validation infrastructure
only. No Stage 3 companion executable schema was created. No Stage 3
fixture, typed record model, semantic validator, authority resolver,
authority state, or authority pointer was implemented or changed. No
cutover request, readiness package, authorization, candidate,
certification, publication attempt, conflict record, or recovery
journal was created. Schema validity does not establish lifecycle
authority, cutover eligibility, authorization, publication success, or
recovery truth. No authority epoch changed. No CLTR authority was
created. No legacy authority was demoted. No legacy authority was
retired. No production lifecycle behavior changed. No execution
capability was introduced. Runtime remains Observed, maximum capability
remains observe, and execution availability remains unavailable.

`schemas/cltr_cutover/` does not exist on disk. No Stage 3 record
schema exists. No typed Stage 3 model exists. No semantic validator
exists. No authority namespace exists. No authority pointer exists or
changed. No production artifact changed because of this phase's
validation infrastructure.

## Final verdict

**PREREQUISITE INFRASTRUCTURE COMPLETE — READY FOR INDEPENDENT
VERIFICATION.** Every item in the strict phase boundary's permitted
list was implemented; every item in the prohibited list was verified
absent. Zero unresolved Blocking findings. "Ready for independent
verification" does not mean ready for Stage 3 schema authoring — Phase
136G (independent verification of this phase's own infrastructure) must
complete first.

## Recommended next phase

**136G — Validation Engine and Strict JSON Parsing Independent
Verification.** Must independently attack Draft 2020-12 conformance,
duplicate-key rejection, offline-only registry behavior, packaging,
containment, no-network behavior, no-authority behavior, and
no-execution behavior. Must not begin Stage 3 schema authoring.
