# Phase 136F — Draft 2020-12 Validation Engine and Strict JSON Parsing Prerequisite

## Status

**PREREQUISITE INFRASTRUCTURE COMPLETE — READY FOR INDEPENDENT VERIFICATION**

This phase implements generic Draft 2020-12 schema-validation
infrastructure only, resolving `PREREQUISITE-136E-1`. It creates no
Stage 3 record schema, shared enum schema, `AuthorityEpoch` schema,
`AuthorityState` schema, `CutoverRequest` schema, `ReadinessPackage`
schema, authorization schema, candidate or certification schema, CAS or
publication schema, recovery or reconciliation schema, notification,
marker, or receipt binding, Stage 3 typed record model, cross-record
semantic validator, authority resolver, authority-state persistence, or
current-authority pointer. No cutover request, readiness package,
authorization, candidate, certification, publication attempt, conflict
record, or recovery journal was created.

**Legacy lifecycle remains the sole production authority. CLTR remains
derivative.** Schema validity, as implemented here, establishes no
lifecycle authority, cutover eligibility, authorization, publication
success, or recovery truth. No authority epoch changed. No CLTR
authority was created. No legacy authority was demoted. No legacy
authority was retired. No production lifecycle behavior changed. No
execution capability was introduced. Runtime remains **Observed**,
maximum capability remains **observe**, execution availability remains
**unavailable**.

Subject contract: **CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0**. Primary
source: `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`
(Phase 136E), which selected `jsonschema>=4.18,<5` as the validation
engine and identified `PREREQUISITE-136E-1` (schema packaging gap).

---

## 1. Dependency

Added `jsonschema>=4.18,<5` to `[project.dependencies]` in
`pyproject.toml` — the repository's first runtime (non-dev) dependency.

Installed version (project `.venv`, Python 3.9.6): **jsonschema 4.25.1**,
within the frozen range.

Transitive dependencies (all installed and inspected in the project
`.venv`):

| Package | Version | License | Notes |
|---|---|---|---|
| jsonschema | 4.25.1 | MIT | Draft 2020-12 validator (`Draft202012Validator`) |
| referencing | 0.36.2 | MIT | `$id`/`$ref` resolution, used by `schema_runtime.registry` |
| jsonschema-specifications | 2025.9.1 | MIT | Bundles JSON Schema meta-schemas **locally**; no network fetch needed for meta-schema validation |
| rpds-py | 0.27.1 | MIT | Native (Rust) persistent data structures backing `referencing` |
| attrs | 26.1.0 | MIT | Used internally by `referencing`/`jsonschema` |

All packages carry MIT licenses, compatible with this project's Apache-2.0
license. `requires-python = ">=3.9"` is unaffected; `jsonschema` 4.25.1
supports Python 3.9+.

No optional format-checking extra (`jsonschema[format]`,
`jsonschema[format-nongpl]`) was installed. `schema_runtime.validation`
does not pass a `FormatChecker` to `Draft202012Validator`, so the
`format` keyword is treated as a non-enforced annotation, per Draft
2020-12 semantics (see §7). Authority-critical ID and digest formats are
left to explicit regex-based validation in future phases, not to
`format`.

**Network behavior at runtime:** none. `jsonschema-specifications` ships
the draft 2020-12 meta-schema as a packaged resource; `Draft202012Validator.check_schema`
and `iter_errors` never perform I/O. `schema_runtime`'s own offline
registry (§6) explicitly refuses any reference not already registered
from local resources (proof: §12).

---

## 2. Strict JSON parser (Layer-1)

Package: `src/pcae/schema_runtime/json_parser.py`, function
`parse_strict_json(data: bytes | str, *, max_bytes=..., require_top_level_object=False) -> JsonParseResult`.

**Design decision.** `json.loads(..., object_pairs_hook=...)` was
rejected as the parsing mechanism: `object_pairs_hook` fires bottom-up,
per object literal, with no ancestor path context, so a duplicate key
cannot be reported with a JSON-Pointer instance path using that
mechanism alone. Instead, `schema_runtime` implements a small
hand-written recursive-descent parser (`_Parser` in `json_parser.py`)
that tracks the path stack explicitly and follows RFC 8259 grammar for
objects, arrays, strings (including `\uXXXX` and surrogate-pair
escapes), numbers, and literals.

Behavior:

- Accepts `bytes` (must decode as strict UTF-8; `UnicodeDecodeError` →
  `invalid_utf8`) or `str` (encoded-length checked against the byte
  limit) via one explicit function.
- Rejects duplicate object keys **at every nesting level**, including
  inside array elements, reporting a `duplicate_key` issue with a JSON
  Pointer `instance_path` (e.g. `/items/1/y`).
- Rejects malformed JSON (`invalid_json`), including trailing data
  after a complete value.
- Rejects `NaN`, `Infinity`, and `-Infinity` literals explicitly with a
  distinct `non_finite_number` code — these are non-standard JSON
  extensions that Python's stdlib `json.loads` otherwise accepts
  silently.
- Optionally requires a top-level JSON object
  (`require_top_level_object=True` → `top_level_not_object` if not).
- Enforces a configurable input-size limit (`max_bytes`, default
  `DEFAULT_MAX_INPUT_BYTES` = 5 MiB) before parsing begins.
- Performs no network access, no filesystem path following, and does
  not mutate its input (verified by test).
- Never raises on ordinary invalid input; returns a structured
  `JsonParseResult`. `TypeError` is raised only for programmer misuse
  (an argument that is neither `bytes` nor `str`).

Same-looking-but-distinct Unicode keys (e.g. Latin `"a"` vs Cyrillic
`"а"`) are correctly treated as **not** duplicates, since Python string
equality is codepoint-exact.

---

## 3. Error vocabulary

`src/pcae/schema_runtime/errors.py` defines `ERROR_CODES`, the frozen
set of the thirteen Layer-1/Layer-2 codes specified for this phase:
`invalid_utf8`, `input_too_large`, `invalid_json`, `duplicate_key`,
`non_finite_number`, `top_level_not_object`, `unknown_schema`,
`unsupported_schema_version`, `unsupported_dialect`,
`schema_resource_invalid`, `schema_reference_unresolved`,
`schema_invalid_record`, `internal_validation_error`. These are
deliberately distinct from — and this phase implements none of — future
semantic/authority error categories (identity mismatch, digest
mismatch, stale authorization, CAS rejection, authority conflict,
recovery required).

`ValidationIssue` (in `models.py`) carries `code`, `message`,
`instance_path` (JSON Pointer), `schema_path` (JSON Pointer),
`record_id`, and `schema_id` — no raw secret values, no stack traces.
Programmer-error exceptions (`SchemaRuntimeError` and subclasses
`SchemaResourceError`, `SchemaResourceNotFoundError`,
`SchemaRegistryError`) are reserved for API misuse (an untrusted schema
root, a missing resource, an unregistered registry lookup), not for
ordinary invalid record/schema content.

---

## 4. Result models

`src/pcae/schema_runtime/models.py` defines immutable (`frozen=True`
dataclass) models: `OutcomeStatus` (`VALID` / `INVALID` /
`INFRASTRUCTURE_FAILURE`), `JsonParseResult`, `ShapeValidationResult`,
`ValidationIssue`, `SchemaResourceInfo`. None carries an authority role,
a persistence side effect, or an implicit truth claim — a `VALID`
`ShapeValidationResult` means only that a record's shape matched a
schema. `OutcomeStatus.INFRASTRUCTURE_FAILURE` is kept distinct from
`INVALID` so callers can tell "the record doesn't match the schema"
apart from "the schema/registry infrastructure itself failed" (unknown
schema id, unresolved `$ref`, invalid schema definition).

---

## 5. Offline schema resource loader

`src/pcae/schema_runtime/loader.py`. `load_schema_resource(path, *,
root, max_bytes)` and `load_schema_package(root, *,
max_resource_bytes)`:

- Resolve an explicit, caller-supplied local root (`Path.resolve(strict=True)`);
  never treats an externally supplied absolute path as trusted on its
  own — an absolute or relative candidate is lexically normalized
  (`os.path.normpath`) and checked with `Path.relative_to(root)`
  **before** any filesystem access, rejecting traversal (`../..`) and
  out-of-root absolute paths.
- Rejects a symlinked leaf file directly.
- Rejects an intermediate symlinked directory by comparing the fully
  resolved path (`Path.resolve(strict=True)`, which follows all
  symlinks) against the lexically normalized path — any divergence
  means a symlink was traversed, and the load is refused.
- Distinguishes a missing resource (`SchemaResourceNotFoundError`) from
  an invalid one (`SchemaResourceError`).
- Requires every resource to parse strictly (via `parse_strict_json`,
  `require_top_level_object=True`), declare `$schema` equal to
  `"https://json-schema.org/draft/2020-12/schema"`, declare a non-empty
  string `$id`, and pass `Draft202012Validator.check_schema` (meta-schema
  conformance).
- Enforces a configurable per-resource byte limit
  (`DEFAULT_MAX_SCHEMA_RESOURCE_BYTES` = 1 MiB).
- `load_schema_package` enumerates `*.schema.json` files
  deterministically (`sorted` by POSIX path) and rejects a duplicate
  `$id` within the package.
- Exposes read-only `SchemaResourceInfo` (schema id, package-relative
  path, dialect, SHA-256 digest, size) — no filesystem mutation.
- Performs no network access.

---

## 6. Offline registry foundation

`src/pcae/schema_runtime/registry.py`, `build_offline_registry(*roots)`
→ `SchemaRegistry`, built on `referencing.Registry` /
`referencing.Resource`. The registry's `retrieve` hook is
`_refuse_retrieve`, which unconditionally raises
`SchemaRegistryError` for any URI not already registered from a
verified local resource — a URI-shaped `$id` (e.g.
`https://pcae.test/...`) is resolved purely from local registration,
never authorizing a network fetch. Duplicate `$id` across multiple
roots is rejected. A configurable resource-count ceiling
(`DEFAULT_MAX_REGISTRY_RESOURCES` = 500) is enforced. The registry
performs no network fetching, exposes no authority behavior, mutates no
repository state, and does not inspect production lifecycle state.

---

## 7. Generic shape-validation API (Layer-2)

`src/pcae/schema_runtime/validation.py`,
`validate_record_shape(record, *, schema_id, registry, max_issues) ->
ShapeValidationResult`. Requires an already strictly-parsed record and
an explicitly named `schema_id`; constructs `Draft202012Validator(schema,
registry=registry.referencing_registry)`. Unknown `schema_id` and
unresolved `$ref` (`referencing.exceptions.Unresolvable`) both fail
closed as `INFRASTRUCTURE_FAILURE`, distinct from `INVALID`. Issues are
deterministically ordered (sorted by `(absolute_path, validator
keyword)`) and capped at `max_issues`. Carries no semantic or authority
claim, and performs no mutation, network, subprocess, shell, or backend
invocation (proof: §17–19).

**Format keyword.** No `FormatChecker` is passed to `Draft202012Validator`,
so per Draft 2020-12, `format` remains an annotation only — a
malformed-looking value under a `"format": "email"` constraint still
validates. This is deliberate, tested (`test_136f_format_is_explicitly_not_enforced_by_default`),
and documented rather than silently assumed; authority-critical ID and
digest formats are left to future explicit regex-based checks, not to
`format`.

---

## 8. Draft 2020-12 capability proof

`tests/test_schema_runtime_validation.py`, against generic test-only
fixture schemas in `tests/fixtures/schema_runtime/valid_package/`
(`root_features.schema.json`, `shared_defs.schema.json`,
`format_check.schema.json`; none is a Stage 3 production schema). Proven
directly: `$defs`, local `$ref` (`#/$defs/widget`), cross-file
registry-resolved `$ref` (`shared-defs.schema.json#/$defs/nonEmptyString`),
`if`/`then`/`else`, `oneOf`, `allOf`, `additionalProperties: false`,
`unevaluatedProperties: false` (including nested-unknown-property
rejection inside an array item), explicit non-enforcement of `format`,
unresolved-reference rejection, and no network fallback during
validation (monkeypatched `socket.socket`).

---

## 9. Duplicate-key proof

`tests/test_schema_runtime_json_parser.py` covers: top-level duplicate,
nested-object duplicate, duplicate inside an array-element object,
duplicate at four levels of nesting, same-looking-but-distinct Unicode
keys (correctly accepted, not flagged), repeated keys with different
values (still rejected), and JSON-Pointer path escaping (`~0`/`~1`) in
the reported `instance_path`.
`tests/test_schema_runtime_loader.py::test_136f_duplicate_key_inside_schema_file_rejected`
proves schema **resources** also go through the same strict parser —
`tests/fixtures/schema_runtime/duplicate_key_schema_package/dup_key.schema.json`
contains a literal duplicate top-level `"type"` key and is rejected at
load time. Both record input and schema resources are strictly parsed;
no ordinary `json.load`/`json.loads` call bypassing `parse_strict_json`
exists anywhere in `schema_runtime` or `schema_resources` (proof:
`test_136f_no_forbidden_imports_in_source` plus manual `grep` audit
recorded in the phase-completion report).

---

## 10. Input limits

Centrally recorded in `src/pcae/schema_runtime/limits.py`:

| Limit | Default | Purpose |
|---|---|---|
| `DEFAULT_MAX_INPUT_BYTES` | 5 MiB | Generic record/document parse input |
| `DEFAULT_MAX_SCHEMA_RESOURCE_BYTES` | 1 MiB | Individual schema resource file |
| `DEFAULT_MAX_ISSUE_COUNT` | 200 | Returned validation issues per call |
| `DEFAULT_MAX_REGISTRY_RESOURCES` | 500 | Resources accepted into one registry |

**Nesting depth.** No explicit recursion-depth counter is enforced in
the hand-written recursive-descent parser; CPython's own interpreter
recursion limit (`sys.getrecursionlimit()`, default 1000) is the
practical backstop against pathologically deep input, mediated first by
the 5 MiB byte-size ceiliing. This is a known, disclosed limitation
(§"Limitations" below and §"Findings"), not a silent gap — no test
claims a lower nesting bound is enforced.

---

## 11. Packaging resolution (PREREQUISITE-136E-1)

**Baseline gap.** Before this phase, `[tool.hatch.build.targets.wheel]`
scoped only `packages = ["src/pcae"]`, and `[tool.hatch.build.targets.sdist]`
scoped only `src/pcae`, `README.md`, `LICENSE`, `pyproject.toml`. The
top-level `schemas/` directory was never included in either build
target — confirmed both by inspection and by the packaging tests below.

**Decision: Option A — package schemas inside the Python package.**
Chosen over retaining and separately packaging the top-level `schemas/`
directory, because `packages = ["src/pcae"]` already reliably includes
non-`.py` files nested under `src/pcae/**` in both the wheel and sdist
without any additional hatchling configuration (verified empirically —
no `artifacts`/`force-include` directive was needed), and because
`importlib.resources` gives package-relative, install-mode-independent
lookup (editable, wheel, or sdist-built install) with no source-tree-relative
fallback required.

New package: `src/pcae/schema_resources/`, currently containing only
`smoke/generic_smoke_record.schema.json` — a generic, explicitly
non-Stage-3 smoke schema — and `__init__.py` exposing
`smoke_schema_root()`, a context manager wrapping
`importlib.resources.files(__package__) / "smoke"` via
`importlib.resources.as_file(...)` to yield a real filesystem `Path`
regardless of install mode. **No Stage 3 schema was moved or created
here in 136F.** The actual Stage 3 package (`schemas/cltr_cutover/` or
its packaged equivalent) is explicitly deferred to a later phase; this
phase proves only that the packaging mechanism works, using a generic
resource.

`pyproject.toml` required no change to `[tool.hatch.build.targets.wheel]`
or `[tool.hatch.build.targets.sdist]` beyond what already existed —
`packages = ["src/pcae"]` and `include = ["src/pcae", ...]` both already
cover `src/pcae/schema_resources/**` since it is a subpackage of
`src/pcae`.

---

## 12. Package-data tests

`tests/test_schema_runtime_packaging.py`:

- **Editable install** (`test_136f_editable_install_resource_lookup`,
  not `slow`): `smoke_schema_root()` resolves to a real file with `$id`
  present, from the project's own editable install. **Passed.**
- **Wheel** (`test_136f_wheel_contains_smoke_schema_and_no_stage3_directory`,
  `slow`): builds a wheel via `python -m build --wheel` into a temp
  dir, opens it with `zipfile`, asserts
  `pcae/schema_resources/smoke/generic_smoke_record.schema.json` is
  present, and asserts no `cltr_cutover`, no `.pcae/`, and no
  `session.json` entries exist in the archive. **Passed.**
- **Source distribution** (`test_136f_sdist_contains_smoke_schema_and_no_stage3_directory`,
  `slow`): builds an sdist via `python -m build --sdist`, opens it with
  `tarfile`, asserts the smoke schema is present and no `cltr_cutover`
  or `.pcae/` entries exist. **Passed.**
- **Installed-wheel, isolated environment**
  (`test_136f_installed_wheel_resource_lookup_in_isolated_venv`,
  `slow`): builds the wheel, creates a fresh `venv` in a temp
  directory, `pip install --no-deps`s the wheel into it (no source
  checkout present), and runs a subprocess probe importing
  `pcae.schema_resources.smoke_schema_root()` and asserting the file
  exists — proving no source-tree-relative fallback is required in
  installed mode. **Passed.**

No unintended secrets or runtime records (`.pcae/`, `session.json`) were
found in either archive. The Stage 3 schema package
(`schemas/cltr_cutover/`) does not exist on disk and is absent from both
archives.

---

## 13. Schema manifest foundation

**Deferred.** Implementing the generic manifest mechanism selected by
136E (manifest version, schema id/version, resource path, SHA-256
digest, dialect, resource family, dependencies) was evaluated against
the "must not materially broaden 136F" boundary. `SchemaResourceInfo`
(§4–5) already carries the per-resource fields a manifest would need
(schema id, relative path, dialect, SHA-256 digest, size), computed
deterministically at load time, which keeps the packaging and registry
design manifest-compatible without introducing a separate manifest file
format, duplicate-ID cross-file bookkeeping, or dependency-graph
concerns in this phase. Full manifest implementation (a persisted,
versioned manifest file with its own schema) is deferred explicitly to
the first schema-core implementation phase, consistent with the phase
boundary's list of prohibited Stage 3 constructs.

---

## 14. Schema integrity

Every loaded schema resource (§5) is verified to: parse strictly;
declare `$schema` as the Draft 2020-12 dialect URI; declare a non-empty
string `$id`; pass `Draft202012Validator.check_schema` (meta-schema
conformance); have a unique `$id` within its package; and remain
contained within the trusted package root. File-digest verification
(SHA-256) is computed and exposed on every `SchemaResourceInfo`, ready
for manifest-based cross-checking once a manifest is implemented (§13).
Schema validity is never treated as record validity or authority
anywhere in this package.

---

## 15. Symlink and containment safety

`tests/test_schema_runtime_loader.py` covers: absolute path outside
root, `../` traversal, a leaf symlink pointing outside the root, and a
symlinked intermediate subdirectory used to smuggle a file back "inside"
the root lexically. All four are rejected by `load_schema_resource`
(§5). No external schema can be trusted through symlink substitution —
containment is checked against the fully resolved (symlink-following)
path, not merely the lexical one.

---

## 16. No-network proof

`tests/test_schema_runtime_registry.py::test_136f_registry_rejects_unregistered_lookup_without_network`
and `test_136f_uri_shaped_id_resolves_locally_never_fetched`, plus
`tests/test_schema_runtime_boundaries.py::test_136f_validation_infrastructure_performs_no_network_io`,
all monkeypatch `socket.socket` to raise `AssertionError` if called, and
prove: (a) a URI-shaped `$id` resolves purely from local registration,
with no socket ever opened; (b) an unregistered lookup fails via
`SchemaRegistryError`/`Unresolvable`, not via a network attempt; (c) an
ordinary `validate_record_shape` call against a locally-registered
schema completes successfully with sockets forbidden.

---

## 17. No-authority proof

`tests/test_schema_runtime_boundaries.py`:
`test_136f_no_authority_module_references_in_source` (AST/text scan for
`pcae.cltr`, `current_authority`, `authority_state`, `authority_epoch`,
`cltr-authority` substrings across every `.py` file in
`schema_runtime`/`schema_resources`), `test_136f_module_does_not_import_cltr_package`
(inspects every public binding in `pcae.schema_runtime` for a
`pcae.cltr`-rooted `__module__`), and
`test_136f_no_authority_namespace_created_on_disk` (asserts
`.pcae/cltr-authority/` and `schemas/cltr_cutover/` do not exist after
the full test run). The new infrastructure does not import
authority-resolution modules, does not read a current-authority pointer,
does not inspect migration state, does not create `.pcae/cltr-authority/`,
does not create production report/marker/receipt/checkpoint files, does
not dispatch notifications, and does not change an authority epoch. A
`ShapeValidationResult.VALID` classifies only shape conformance, never
production authority (§4, §7).

---

## 18. No-execution proof

`tests/test_schema_runtime_boundaries.py::test_136f_no_forbidden_imports_in_source`
(AST import scan for `subprocess`, `socket`, `shlex`,
`http.client`/`http.server`, `urllib.request`, `urllib3`, `requests`,
`ftplib`, `telnetlib`, `smtplib`) and
`test_136f_no_subprocess_or_os_system_calls_in_source` (AST call-site
scan for `subprocess.run`/`call`/`Popen`, `os.system`, `os.popen`)
confirm none of these are imported or called anywhere in
`src/pcae/schema_runtime/` or `src/pcae/schema_resources/`. (Packaging
*tests* under `tests/test_schema_runtime_packaging.py` do use
`subprocess`/`venv` to build and probe wheels — that is test-only
tooling, outside the production package boundary these proofs cover,
and is itself read-only with respect to repository/production state.)
Runtime remains **Observed**, maximum capability remains **observe**,
execution availability remains **unavailable** (confirmed via `pcae
runtime inspect` before finalization, §"Before finalization").

---

## 19. Test-only schemas

All fixture schemas live under `tests/fixtures/schema_runtime/` (nine
package directories: `valid_package`, `duplicate_id_package`,
`duplicate_key_schema_package`, `invalid_dialect_package`,
`invalid_schema_package`, `missing_id_package`,
`unresolved_ref_package`, plus dynamically-generated `tmp_path`
fixtures for containment/symlink/size-limit tests). None uses a Stage 3
record name (`AuthorityEpoch`, `AuthorityState`, `CutoverRequest`,
`ReadinessPackage`, etc.), none carries authority semantics, and all are
clearly test-only — the sole *packaged* schema resource is the
non-Stage-3 `generic_smoke_record.schema.json` used exclusively to prove
the packaging mechanism (§11–12).

---

## 20. CLI boundary

No public CLI was added. `schema_runtime` and `schema_resources` are
library-level infrastructure only, exercised by focused tests. A
production `pcae cltr schema validate` command remains deferred until
real Stage 3 schemas exist and this package is independently verified
(136G, recommended next phase).

---

## Focused test results

| File | Tests | Result |
|---|---|---|
| `tests/test_schema_runtime_json_parser.py` | 22 | passed |
| `tests/test_schema_runtime_loader.py` | 14 | passed |
| `tests/test_schema_runtime_registry.py` | 5 | passed |
| `tests/test_schema_runtime_validation.py` | 12 | passed |
| `tests/test_schema_runtime_boundaries.py` | 12 | passed |
| `tests/test_schema_runtime_packaging.py` | 4 (3 `slow`) | passed |
| **Total** | **69** | **69 passed, 0 failed** |

## Regression runs

| Run | Result |
|---|---|
| Focused `schema_runtime` suite (`tests/test_schema_runtime_*.py`) | 69 passed |
| Fast Green (`-m fast_green -n auto`) | 4391 passed (unchanged from 136E baseline) |
| Full unmarked suite (`-n auto`) | see phase-completion report for exact freshly-run count |

## Limitations

- No explicit parser-level recursion-depth limit; mitigated only by the
  5 MiB input-size ceiling and the CPython interpreter recursion limit
  (§10). A future phase should add an explicit depth counter if deeply
  nested Stage 3 records are anticipated.
- No manifest file format is implemented yet (§13); per-resource
  metadata needed for one is already computed and available.
- `format` is explicitly unenforced (§7, §1); any future need to
  validate formats (dates, URIs, etc.) as hard assertions requires an
  explicit `FormatChecker` decision in a later phase, not silent
  reliance on `jsonschema`'s optional extras.
- "Encoded traversal" containment coverage (§15) is filesystem-path-based
  (`os.path.normpath` + symlink-resolution comparison); no URL-style
  percent-encoding applies to local filesystem paths, so that sub-case
  of item 15 in the phase brief is covered by the general traversal and
  symlink tests rather than a separate encoded-URL test.

## Independent verification requirements (for 136G)

The next phase must independently attack, not merely re-read:

- **Validator-version assumptions**: confirm `Draft202012Validator`
  behavior is not silently version-dependent beyond the frozen
  `>=4.18,<5` range.
- **Registry behavior**: attempt reference-resolution edge cases beyond
  what 136F's fixtures cover (e.g. `$anchor`, `$recursiveRef`-adjacent
  constructs excluded from Draft 2020-12).
- **Network isolation**: attempt validation paths not covered by the
  `socket.socket` monkeypatch (e.g. DNS resolution primitives, other
  transport mechanisms).
- **Package-data inclusion**: verify wheel/sdist inclusion holds across
  a clean-room build (not just this phase's own build), and that
  `MANIFEST.in`-style tooling changes elsewhere in the repo cannot
  silently regress it.
- **Duplicate-key rejection**: attempt bypasses via alternative encodings
  or parser entry points not exercised here.
- **Symlink containment**: attempt more exotic filesystem escapes (hard
  links, bind mounts, case-insensitive filesystem aliasing).
- **Error determinism**: verify issue ordering is stable across Python
  versions/platforms, not just within this environment.
- **Issue-limit behavior**: verify `max_issues` truncation doesn't hide
  a more severe issue behind a less severe one.
- **No-authority boundary**: verify the AST/text-scan proofs in
  `test_schema_runtime_boundaries.py` cannot be defeated by dynamic
  imports (`importlib.import_module` with a computed string) that a
  static scan would miss.

## Recommended next phase

**136G — Validation Engine and Strict JSON Parsing Independent
Verification.** 136G must independently attack Draft 2020-12
conformance, duplicate-key rejection, offline-only registry behavior,
packaging, containment, no-network behavior, no-authority behavior, and
no-execution behavior. It must not begin Stage 3 schema authoring.
