# Phase 136E — Stage 3 Companion Executable Schema Implementation Plan

## Status

**IMPLEMENTATION PLAN COMPLETE WITH OPEN PREREQUISITES — READY FOR
VALIDATION-ENGINE PREREQUISITE**

This document is planning-only. It adds no dependency, no executable
schema, no fixture, no parser, no loader, no registry, no validator, no
typed model, no runtime code. It does not modify production behavior. It
does not implement authority state, authority resolution, or Stage 3
activation. It does not change production authority or demote/retire
legacy authority. It does not introduce execution.

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. Runtime remains **Observed**, maximum capability remains
**observe**, execution availability remains **unavailable**.

Subject contract: **CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0**, frozen
Phase 136C (`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`),
independently verified with prerequisites and two documentation-only
Blocking repairs by Phase 136D
(`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_INDEPENDENT_VERIFICATION.md`).

---

## 0. Historical lifecycle disposition (read-only, not repaired here)

Per this phase's brief, the following reconciliations were re-run
read-only (`mutation: none` in every case) and are recorded, not acted
on:

| Phase | `pcae phase-report reconcile` result |
|---|---|
| 136A | `reconciliation_status: conflict`, `marker_state: not_dispatched`, `checkpoint_state: completed`, `receipt_state: finalized` |
| 136B | `status: reconciled`, `marker: already_dispatched`, `checkpoint: completed`, `receipt: finalized` |
| 136C | `status: not_delivered`, `marker: not_dispatched`, `checkpoint: completed`, `receipt: finalized` |
| 136D | `status: reconciled`, `marker: already_dispatched`, `checkpoint: completed`, `receipt: finalized` |

**136B discrepancy classification.** The phase brief for 136E states that
136D reported 136B as `not_delivered`/`not_dispatched`, differing from
136C's own recorded observation that 136B was `reconciled`/
`already_dispatched`. Independently re-running `pcae phase-report
reconcile --phase-id 136B` in this phase reproduces `status:
not_delivered`, `marker: not_dispatched` — i.e., the same result 136D
reported, not the "reconciled" state 136C claimed to have observed at its
own freeze time. Because the underlying `.pcae/phase-reports/` and
`.pcae/finalization-transactions/` state for 136B has not been mutated by
either 136C, 136D, or this phase (no phase in this chain is permitted to
redispatch or mutate 136B), and because a stateless read-only
reconciliation command computed on unchanged inputs is expected to be
deterministic, this is classified **incomplete bookkeeping**: 136C's own
freeze-time narrative describing 136B as "reconciled" was either an
inaccurate restatement at the time it was written, or reflected a
transient marker/checkpoint state that had not yet settled to its current
persisted form — not a case of the underlying evidence changing between
136C and 136D/136E. There is exactly one promoted 136B generation and no
duplicate delivery evidence in either observation. This is **not** used as
Stage 3 or executable-schema readiness evidence of any kind by this plan,
and it is **not repaired** by this phase. It is carried forward as
disclosed governance debt for a future documentation-hygiene phase, per
explicit instruction not to redispatch or mutate 136B.

136A's `conflict` status is unchanged from every prior phase's
observation and remains disclosed historical lifecycle evidence only,
also not repaired here.

---

## 1. Planning scope

Phase 136E plans:

- validation-engine tooling selection (§3) and dependency introduction
  (§4);
- strict JSON parsing (§5);
- schema file creation targets — package layout (§6), exact inventory
  (§7), `$id` strategy (§8), `$ref` graph (§9), shared definitions (§10),
  enums (§11), envelope composition (§12);
- fixtures (§14);
- schema registry (§17);
- strict shape validation and a validation API (§18);
- tests (§23);
- verification boundaries and independent-verification strategy (§24);
- packaging (§25).

It does **not** plan or implement:

- semantic cross-record validation (owned by a future Layer 4 semantic
  validator, §22 handoff table);
- authority resolution (Layer 6, CLTR-CUTOVER-001 §4);
- live CAS (Layer 5);
- publication (Layer 5/6);
- authorization freshness (Layer 4/5, wall-clock comparison);
- recovery truth (Layer 4, cross-document journal verification);
- production cutover;
- Stage 3 activation.

---

## 2. Current baseline

Directly re-confirmed by this phase's own inspection (see §"Initial
inspection commands run" below for the exact commands):

- **No Stage 3 schema package.** `schemas/cltr_cutover/` does not exist.
  `find schemas -type f` returns only the pre-existing, unrelated
  `schemas/repository_intelligence/**` tree (1 `README.md` + 8 files under
  `artifacts/` + 13 files under `shared/` = 22 files total).
- **No Draft 2020-12 validator dependency.** `pyproject.toml`'s `[project]`
  table declares `dependencies = []`. `pip show jsonschema` returns
  `WARNING: Package(s) not found: jsonschema` — no JSON Schema engine of
  any kind is installed in the active environment.
- **No strict duplicate-key parser dedicated to this package.** The only
  runtime consumers of `schemas/repository_intelligence/**`
  (`tests/test_phase_120e_repository_knowledge_snapshot.py`,
  `test_phase_126e_dependency_knowledge_graph_prototype.py`,
  `test_phase_127e_historical_memory_prototype.py`) call a hand-rolled
  `_check_required(obj, schema)` helper that checks only `required` key
  presence and, when `additionalProperties is False`, that no key outside
  `properties` appears. No `pattern`, `enum`, `type`, `if`/`then`/`else`,
  `oneOf`, `$ref` resolution, or `unevaluatedProperties` semantics are
  exercised anywhere in this repository today (136D §3, independently
  reconfirmed here).
- **No schema registry, no schema manifest, no schema fixtures, no typed
  models, no semantic validator** exist for Stage 3 companion records
  anywhere in `src/pcae/` (confirmed: no `AuthorityKind`,
  `PublicationState`, `CompatibilityMode`, or `GenerationRole` Python enum
  exists anywhere in `src/`, per 136C §0.5, independently re-confirmed by
  136D and not contradicted by this phase's own re-inspection).
- **Legacy authority remains sole production authority**
  (`ProductionAuthority.LEGACY`, `src/pcae/cltr/migration/enums.py`). No
  authority epoch has changed.

**Packaging and dependency facts, from direct inspection of
`pyproject.toml`:**

| Fact | Value |
|---|---|
| Build backend | `hatchling.build` (`[build-system]`) |
| Package name | `pcae-harness`, version `0.2.0` |
| `requires-python` | `>=3.9` |
| `dependencies` | `[]` (empty — zero runtime dependencies today) |
| `optional-dependencies.dev` | `pytest>=8.0`, `pytest-xdist>=3.0` |
| Wheel package scope | `packages = ["src/pcae"]` (`[tool.hatch.build.targets.wheel]`) |
| Sdist scope | explicit include list: `src/pcae`, `README.md`, `LICENSE`, `pyproject.toml` (`[tool.hatch.build.targets.sdist]`) — **`schemas/` is not currently in the sdist include list** (relevant to §25) |
| Test config | `pytest`, `testpaths = ["tests"]`, `pythonpath = ["src"]`, markers `slow`/`integration`/`phase_closure`/`fast_green` |

---

## 3. Disposition of PREREQUISITE-136D-1

**Finding restated exactly:** no JSON Schema Draft 2020-12-conformant
validation engine currently exists in the repository; `pyproject.toml`
declares zero runtime dependencies and existing schema consumers perform
only limited key-presence checks, not full Draft 2020-12 validation. This
must be resolved in planning before executable schema implementation
begins.

### 3.1 Candidate comparison

| Criterion | `jsonschema` (python-jsonschema) | `fastjsonschema` | Custom hand-rolled validator | Vendoring |
|---|---|---|---|---|
| Draft 2020-12 support | Yes — `jsonschema.validators.Draft202012Validator`, the reference-grade Python implementation, actively maintained against every published JSON Schema draft including 2020-12 | Partial/uneven — historically lagged draft support and prioritizes generated-code speed over spec completeness; 2020-12 support has been less consistently maintained across releases | N/A — would have to be built from scratch | N/A — same code, different distribution channel |
| Offline reference resolution | Yes — `jsonschema.validators.Registry` (replacing the deprecated `RefResolver`) supports fully offline, filesystem-backed `Resource`/`Registry` composition with no implicit network fetch when constructed without a retrieval function | Yes, but with a smaller, less-documented offline-resolution API | Would have to be hand-built, duplicating a well-tested subsystem | Same code as `jsonschema`, so same properties, plus packaging/update burden |
| Registry API | Yes — first-class `Registry`/`Resource` objects designed exactly for this offline, local-tree use case (matches this contract's §41 registry requirements closely) | No equivalent first-class registry abstraction | N/A | Same as `jsonschema` |
| Format validation | Optional, via `jsonschema.FormatChecker` — off by default (matches this contract's §13/§2 "format is advisory only" requirement without extra configuration) | Optional, more limited format-checker surface | N/A | Same as `jsonschema` |
| Dependency footprint | Small, pure-Python, one transitive dependency (`referencing`, `attrs`, `rpds-py` — the last is a small Rust extension wheel with broad platform coverage) | Small, but includes a C-extension/codegen path with more platform-specific build concerns | Zero footprint, but zero spec coverage | Full `jsonschema` footprint plus a vendoring/update-tracking burden with no offsetting benefit |
| Python-version compatibility | Actively supports Python 3.8+ across recent major versions, compatible with this repository's `requires-python = ">=3.9"` | Also broadly compatible, similar floor | N/A | Same as `jsonschema` |
| Maintenance | Very actively maintained (python-jsonschema org, frequent releases, tracks new JSON Schema drafts promptly) | Maintained, smaller release cadence, historically slower to adopt new drafts | N/A — this repository would own 100% of the maintenance burden for spec-conformance code, a materially different risk profile than depending on an external package | Same code as `jsonschema`, but this repository would additionally own the vendoring/update process |
| Security | No known systemic CVE history at time of this plan; standard PyPI/typosquatting due-diligence applies same as any dependency | Same general profile | No CVE surface from a third party, but a hand-rolled validator open to its own spec-compliance bugs is itself a correctness/security risk (e.g. a `pattern` that's silently ignored is a fail-open bug, not a fail-closed one) | Same code as `jsonschema`, same due-diligence, plus the vendoring process itself is an added supply-chain surface (stale, un-patched vendored copies are a known anti-pattern) |
| License | MIT — compatible with this repository's Apache-2.0 license | BSD-3-Clause — also compatible | N/A | Same as whichever package is vendored |
| Deterministic behavior | Deterministic given a fixed schema + document + registry (no network I/O when constructed offline) | Also deterministic under the same conditions | Deterministic by construction, but only as deterministic as the hand-written logic is correct | Same as `jsonschema` |
| Network behavior | No network access at all when the `Registry`/`Resource` API is used with pre-loaded local resources and no retrieval function is configured — matches this contract's absolute "no network fetch" requirement (§2, §41) by construction, not by discipline | Same, when configured offline | No network surface at all (nothing to configure) | Same as `jsonschema` |
| Integration effort | Low — well-documented `Registry.from_resources(...)`/`validate(..., registry=...)` API maps directly onto this package's `shared/`+`records/` two-tier `$ref` layout (§9) | Low-to-moderate — codegen-first design is a slightly different integration shape (compiles a schema to a Python function ahead of validation) that fits less naturally with this contract's "validate one document against one of 16 record schemas, chosen at call time" access pattern | High — every keyword this contract actually uses (`oneOf`, `if`/`then`, `pattern`, `const`, `enum`, nested `$ref`, the two-tier `additionalProperties` policy) would need independent, tested reimplementation | Low integration effort (identical to `jsonschema`), but ongoing high maintenance effort |
| Error reporting | `ValidationError` objects carry a JSON-Pointer-shaped `.path`/`.absolute_path`, `.schema_path`, `.validator`, and `.message` — directly usable for this contract's planned "machine-readable errors, JSON pointer locations" requirement (§18, §19) without additional translation code | `fastjsonschema` raises a single exception type with a formatted message string but weaker structured-path information by default | N/A — would have to build this from scratch | Same as `jsonschema` |
| Testability | Widely used, extensively tested upstream; this repository's own tests would test *our* schemas and *our* integration, not re-test the validator's own spec conformance (out of scope, correctly deferred to the upstream project's own test suite) | Same general shape | This repository would have to write and maintain its own spec-conformance test suite in addition to its own schema tests — a large, ongoing, unbounded testing burden with no corresponding contract benefit | Same as `jsonschema`, plus the vendoring process itself needs its own re-verification tests after every update |

**Custom validation is rejected**, per the task's own instruction to
reject it "unless there is compelling evidence." No compelling evidence
was found: this contract's schemas make substantive use of `oneOf` tagged
unions, `if`/`then` conditionals, anchored `pattern` regexes, closed
`enum` vocabularies, and a two-tier `additionalProperties` policy — a
correct, fail-closed reimplementation of even this subset of Draft
2020-12 is a nontrivial, ongoing engineering and security commitment with
no offsetting benefit over a mature, actively-maintained upstream
implementation, and a subtly incorrect hand-rolled validator (e.g. one
that silently treats an unanchored `pattern` as passing) would be a
fail-open bug in exactly the fail-closed contract this package exists to
enforce.

**Vendoring is rejected.** This repository's packaging conventions
(`pyproject.toml`'s `dependencies = []` today is a *policy choice not yet
exercised*, not a *policy against ever having a dependency* — the
`optional-dependencies.dev` group already carries `pytest`/`pytest-xdist`
as ordinary PyPI dependencies) show no evidence of a no-runtime-dependency
mandate that would require vendoring; adding one well-scoped runtime
dependency via ordinary `dependencies = [...]` is consistent with how this
repository already manages its dev dependencies, and vendoring would add
a real, ongoing update-tracking and security-patching burden this
repository has no existing process for.

### 3.2 Selected validation engine

**Selected: `jsonschema` (the `python-jsonschema` PyPI package), used via
its `Draft202012Validator` and offline `Registry`/`Resource` API.**

Rationale, in one paragraph: it is the reference-grade Python
implementation of the exact dialect this contract already froze (136B
§2, 136C §2 — Draft 2020-12), its `Registry`/`Resource` offline-resolution
API maps directly onto this contract's two-tier `shared/`+`records/`
local-`$ref` layout (§9 below) without requiring any custom resolution
code, it has no network access by construction when used offline, its
`ValidationError` objects already carry the JSON-Pointer-style path
information this contract's planned error model (§19) needs, its license
(MIT) is compatible with this repository's Apache-2.0 license, and its
dependency footprint (`referencing`, `attrs`, `rpds-py`) is small and
broadly platform-compatible with this repository's `requires-python
= ">=3.9"` floor.

### 3.3 Version constraint strategy

`jsonschema>=4.18,<5` in `pyproject.toml`'s `dependencies` list.

- **Floor (`>=4.18`):** version 4.18 is the first `jsonschema` release
  where the modern `Registry`/`Resource` offline-resolution API (replacing
  the deprecated `RefResolver`) is the documented, stable path — pinning
  the floor here avoids depending on the deprecated resolver API this plan
  does not intend to use.
- **Ceiling (`<5`):** a future `jsonschema` 5.x major release is treated,
  per this repository's own existing minor/major discipline (135Z §42,
  restated by 136C §15 for this package's own schema versioning), as a
  potential breaking change requiring a deliberate, reviewed dependency
  bump — not an automatic transitive upgrade.
- **Lockfile:** this repository currently has no dependency lock file
  (confirmed: no `uv.lock`, `poetry.lock`, or `requirements*.txt` with
  pinned hashes found under the repository root during this phase's
  inspection). The dependency-introduction phase (§4) must decide,
  as part of its own scope, whether to add one — this plan does not
  presuppose that decision, since introducing a lock-file mechanism is
  itself a packaging-policy change beyond a single dependency addition.
- **No dependency is added in 136E.** This section states the planned
  constraint for the future dependency-introduction phase (§4) to apply;
  `pyproject.toml` is unmodified by this phase (confirmed in §"No-
  implementation proof" below).

---

## 4. Dependency introduction plan

**Disposition: a separate, bounded prerequisite phase — not folded into
schema implementation.**

Rationale: PREREQUISITE-136D-1 is a repository-wide tooling gap (zero
runtime dependencies today), not a schema-content question. Introducing
the first-ever runtime dependency to this repository is qualitatively
different from writing schema JSON — it changes the wheel/sdist
dependency graph, needs its own installability and offline-behavior
verification, and benefits from an independent verification pass focused
entirely on "did we correctly add and validate a dependency" before any
schema-content review has to also carry that burden. Bundling it into
Group 1 schema authoring would force Group 1's own independent
verification (§24) to review both dependency-introduction correctness and
schema-content correctness at once, diluting both. A separate bounded
phase is therefore preferred, consistent with this plan's general "prefer
a separate bounded phase if dependency risk is material" instruction.

The bounded prerequisite phase (135F in the roadmap, §33) must include:

- **Packaging change.** Add `jsonschema>=4.18,<5` to `pyproject.toml`'s
  `[project].dependencies` list (currently `[]`).
- **Dependency installation.** Install into the repository's development
  environment (via `pip install -e .[dev]` or equivalent) and confirm a
  clean install with no conflicting transitive pin against `pytest`/
  `pytest-xdist`.
- **Import smoke test.** A new test module (e.g.
  `tests/test_phase_136f_validation_engine_smoke.py`) that imports
  `jsonschema`, constructs a `Draft202012Validator`, and validates a
  trivial inline schema/document pair — proving the import path and basic
  API surface work in this repository's actual test environment, not just
  locally.
- **Draft 2020-12 meta-schema support.** A test that validates
  `jsonschema.Draft202012Validator.META_SCHEMA` against itself (a
  standard self-consistency check) and that `Draft202012Validator` is the
  validator class actually selected for every schema file this plan will
  eventually add (each declares `"$schema":
  "https://json-schema.org/draft/2020-12/schema"`, §8 below).
- **Offline resolution test.** A test that constructs a `Registry` from
  two or more in-memory or fixture schema resources with a `$ref` between
  them, resolves it, and validates successfully — proving the offline
  `Registry`/`Resource` composition pattern this plan's `$ref` graph (§9)
  depends on actually works in this repository's environment before any
  real Stage 3 schema is written against it.
- **No-network test.** A test that constructs a `Registry` with **no**
  retrieval function configured and asserts that resolving an
  unregistered external `$ref` raises (rather than silently attempting a
  network fetch) — a direct, executable proof of this contract's absolute
  "no network fetch" requirement (136C §2, §41), not merely a documented
  claim.
- **Compatibility with supported Python versions.** Confirm `jsonschema`'s
  own declared Python-version floor is compatible with this repository's
  `requires-python = ">=3.9"` (as of this plan, `jsonschema` 4.x supports
  3.8+, so no floor conflict is expected — the dependency-introduction
  phase must re-verify this against the exact `jsonschema` version pinned
  at that time, since upstream floors can rise between this plan and that
  phase's execution).
- **Dependency metadata.** Confirm `jsonschema`'s own `dependencies`
  (`attrs`, `rpds-py`, `referencing`, and `importlib-resources`/
  `pkgutil-resolve-name` on older Pythons) are individually license- and
  platform-compatible; record this in the dependency-introduction phase's
  own report, not merely assumed here.
- **License/security review.** Confirm `jsonschema`'s MIT license text and
  perform a basic supply-chain check (package identity on PyPI, maintainer
  history, no known open CVE at time of pinning) before the dependency is
  added — this is a lightweight, repository-scale check, not a full
  third-party security audit, consistent with this repository having no
  existing formal dependency-security-review process to extend.
- **Fast Green.** The dependency-introduction phase's own commits must
  pass this repository's existing `fast_green` test tier unaffected
  (the addition of one new, isolated test module should not perturb any
  existing test).
- **Independent verification.** A dedicated independent-verification
  phase (135G in the roadmap, §33) re-runs all of the above from a fresh
  perspective before Group 1 schema authoring begins.

---

## 5. Strict JSON parsing plan

JSON Schema validation begins only after duplicate-safe parsing — this
package's own schema-validation layer (Layer 2, 136C §1) sits strictly
above Layer 1 parsing (136C §2's duplicate-key-handling row: "Layer 1
... rejects duplicate object keys before the document reaches Layer 2").

**Planned approach: `json.loads(text, object_pairs_hook=<duplicate-
rejecting hook>)` is sufficient — no third-party JSON parser is planned.**

- **UTF-8 input.** Every schema-package input document is read as UTF-8
  text (`open(path, "r", encoding="utf-8")` or `bytes.decode("utf-8")`
  with `errors="strict"`, never `"replace"`/`"ignore"`) before being
  handed to `json.loads`. Python's built-in `json` module already assumes
  a `str` or a UTF-8-encoded `bytes`/`bytearray` (per RFC 8259) — this
  plan states the encoding discipline explicitly rather than relying on
  `json`'s default `bytes` auto-detection, matching this repository's
  existing digest/canonicalization code's own explicit-UTF-8 discipline
  (`pcae.cltr.canonicalization`).
- **Duplicate-key rejection.** `object_pairs_hook` is the correct, minimal
  mechanism: a small function receiving the list of `(key, value)` pairs
  in document order, which raises a `DuplicateKeyError`-style exception
  the moment a repeated key is seen, rather than the default dict-building
  behavior (`dict(pairs)`) which silently keeps only the last value for a
  repeated key. This mirrors the plain-Python-stdlib approach this
  repository would need to write once and reuse — no dependency is needed
  for this specific concern, and `jsonschema` itself does not perform
  duplicate-key detection (JSON Schema validates a parsed object; by the
  time a `dict` reaches a validator, duplicate keys have already been
  silently collapsed — confirmed by inspecting `jsonschema`'s own public
  API, which accepts a plain object with no duplicate-key awareness).
- **Top-level object requirement.** Every one of the 16 standalone
  companion-record documents (§7) must parse to a JSON *object* at the
  top level, never an array, string, number, boolean, or `null` — enforced
  by a simple `isinstance(parsed, dict)` check performed immediately after
  parsing, before schema validation begins (a cheap, decisive rejection
  that avoids handing a malformed top-level shape to the schema validator
  at all).
- **Input-size limits.** A maximum input byte-length constant (planned
  starting value: 1 MiB per document — deliberately generous relative to
  this contract's actual field list, since every companion record is a
  flat-ish object of scalar/reference fields, not a bulk-data carrier;
  §27 below revisits the exact figure) checked **before** parsing begins
  (`len(raw_bytes) > MAX_INPUT_BYTES` rejected pre-parse), to bound
  worst-case parse time and memory for an untrusted or corrupted input
  file.
- **Nesting-depth considerations.** Python's `json` module has no built-in
  recursion-depth cap independent of the interpreter's own recursion
  limit; this plan schedules an explicit nesting-depth check (a bounded
  recursive or iterative walk of the parsed structure, rejecting depth
  beyond a fixed planned ceiling, e.g. 32 levels — generous relative to
  this contract's own deepest planned nesting, which is at most a handful
  of levels: envelope → embedded `cas_expectation` → its own scalar
  fields) to close the classic "deeply nested JSON causing a
  `RecursionError` or excessive stack use" resource-exhaustion vector,
  since this concern is **not** addressed by `object_pairs_hook` or by
  `jsonschema` itself.
- **Number handling.** `json.loads`'s default behavior (JSON integers
  become Python `int`, JSON floats become Python `float`) is planned to be
  used unmodified — this contract's own fields are either strings
  (identifiers, digests, timestamps, enums), booleans, or a small number
  of genuinely-integer fields (`attempt_sequence`, `sequence`,
  §7 table) with no field requiring arbitrary-precision decimal handling;
  `parse_float`/`parse_int` overrides are therefore planned as
  unnecessary, not merely unconsidered.
- **Invalid Unicode.** Handled by the UTF-8 `errors="strict"` decode step
  above, prior to `json.loads` — a byte sequence that is not valid UTF-8
  is rejected at the decode boundary, never silently repaired or passed
  through to the parser.
- **Non-finite numbers.** `json.loads`'s default `parse_constant`
  behavior accepts `NaN`, `Infinity`, and `-Infinity` as valid tokens by
  default (a documented Python `json` extension beyond strict RFC 8259) —
  this plan schedules passing an explicit `parse_constant` callback that
  raises on any of these three tokens, since no field in this contract is
  ever legitimately non-finite (every numeric field is either a bounded
  count or absent) and silently accepting `NaN`/`Infinity` into, e.g., a
  digest-adjacent computation would be a correctness hazard.
- **Error vocabulary.** Parse-time failures are planned to surface as one
  of a small, closed set of reason codes distinct from schema-validation
  reason codes (§19): `parse_invalid_utf8`, `parse_duplicate_key`,
  `parse_not_an_object`, `parse_oversized_input`, `parse_excessive_nesting`,
  `parse_non_finite_number`, `parse_malformed_json` (the generic
  `json.JSONDecodeError` catch-all). These are Layer 1 errors, structurally
  distinct from Layer 2 schema-validation errors (§19), so that a consumer
  can distinguish "this was not even well-formed JSON" from "this was
  well-formed JSON that didn't match the schema."
- **Source-location diagnostics.** `json.JSONDecodeError` already carries
  `.lineno`/`.colno`/`.pos` for native parse failures; the custom
  duplicate-key hook is planned to raise an exception carrying the
  duplicate key's name and the (approximate, pair-order-derived) position
  it was seen at, for parity with native parse-error diagnostics.
- **No network or filesystem traversal at parse time.** The parsing layer
  operates on an already-read, in-memory string/bytes value; it never
  itself opens a file, follows a symlink, or resolves a path — path
  resolution and traversal-safety (rejecting `..`, absolute paths) are
  handled entirely by the identifier/locator `pattern` constraints already
  frozen in the contract (136C §10, §12) and by the future registry's own
  filesystem-loading code (§17), not by the JSON parser.

**No parser implementation exists in 136E** — this section plans the
future strict-parsing module's exact behavior; no `src/` file is created
or modified by this phase (confirmed in §"No-implementation proof").

---

## 6. Schema package layout plan

Frozen (136C §3, unchanged by this plan — this plan **reconfirms**, does
not redefine, the target layout):

```
schemas/cltr_cutover/
  README.md
  shared/
    envelope.schema.json
    enums.schema.json
    identity.schema.json
    digest.schema.json
    references.schema.json
    failures.schema.json
    limitations.schema.json
  records/
    authority_epoch.schema.json
    authority_state.schema.json
    cutover_request.schema.json
    readiness_package.schema.json
    human_authorization.schema.json
    cutover_candidate.schema.json
    certification.schema.json
    publication_attempt.schema.json
    publication_evidence.schema.json
    concurrency_conflict.schema.json
    recovery_journal_entry.schema.json
    quarantine_record.schema.json
    notification_authority_binding.schema.json
    marker_authority_binding.schema.json
    receipt_authority_binding.schema.json
    compatibility_state.schema.json
  bindings/
    (reserved, empty at implementation start — 136C §3.1)
  views/
    (reserved, empty at implementation start — 136C §3.1, §36)
```

**Separation of concerns, planned:**

- **Schema definitions** — the tree above (`schemas/cltr_cutover/**`),
  version-controlled source, never machine-generated at runtime.
- **Fixtures** — planned under a **sibling, not nested**, path:
  `tests/fixtures/cltr_cutover/<family>/{valid,invalid}/*.json` (mirroring
  this repository's existing fixture convention of keeping test data under
  `tests/`, distinct from `schemas/`, so that `schemas/cltr_cutover/`
  remains exclusively schema-definition content with no test-data
  admixture — confirmed as the correct precedent by inspecting how
  `schemas/repository_intelligence/**`'s own consuming tests source their
  test documents inline/fixture-adjacent under `tests/`, never under
  `schemas/`).
- **Runtime records** — once Stage 3 is eventually implemented (far
  beyond this plan's scope), actual persisted companion records live under
  `.pcae/cltr-authority/...` (135Z §38.2, 136B §7's compatibility-state
  namespace repair, 136C §34), never under `schemas/` (136C §3.2's
  explicit "no runtime record of any kind may be stored under
  `schemas/cltr_cutover/`" rule, restated here as a binding constraint on
  every future implementation group).
- **Generated artifacts** — none are planned. This package's schema files
  are hand-authored and version-controlled directly; no code-generation
  step is planned to produce them (consistent with `schemas/
  repository_intelligence/**`'s own precedent — no generator exists for
  that tree either). If a future documentation-generation step is added
  (§30), its output is planned to live under `docs/generated/` or
  equivalent, never mixed into `schemas/cltr_cutover/`.

**No files are created under this layout in 136E.**

---

## 7. Exact file inventory

Restating and freezing-for-implementation 136C §4's inventory (16
standalone schemas + 7 shared `$defs` files + 1 embedded component + 1
`README.md` = 24 files at full implementation), with implementation
grouping and fixture-set assignment added by this plan:

| # | Path | `$id` suffix | Family | `schema_version` (planned initial) | Implementation group (§13) | Dependencies (`$ref` targets) | Fixture set | Verification owner |
|---|---|---|---|---|---|---|---|---|
| — | `shared/envelope.schema.json` | `shared/envelope.schema.json` | shared | `1.0` | Group 1 | `identity.schema.json`, `digest.schema.json`, `references.schema.json`, `limitations.schema.json`, `enums.schema.json`, `failures.schema.json` | `tests/fixtures/cltr_cutover/shared/envelope/` | Group 1 verification (136H/136I in roadmap) |
| — | `shared/enums.schema.json` | `shared/enums.schema.json` | shared | `1.0` | Group 1 | none | `tests/fixtures/cltr_cutover/shared/enums/` | Group 1 verification |
| — | `shared/identity.schema.json` | `shared/identity.schema.json` | shared | `1.0` | Group 1 | none | `tests/fixtures/cltr_cutover/shared/identity/` | Group 1 verification |
| — | `shared/digest.schema.json` | `shared/digest.schema.json` | shared | `1.0` | Group 1 | none | `tests/fixtures/cltr_cutover/shared/digest/` | Group 1 verification |
| — | `shared/references.schema.json` | `shared/references.schema.json` | shared | `1.0` | Group 1 | `identity.schema.json`, `digest.schema.json`, `enums.schema.json` | `tests/fixtures/cltr_cutover/shared/references/` (includes embedded `cas_expectation` fixtures) | Group 1 verification |
| — | `shared/failures.schema.json` | `shared/failures.schema.json` | shared | `1.0` | Group 1 | none | `tests/fixtures/cltr_cutover/shared/failures/` | Group 1 verification |
| — | `shared/limitations.schema.json` | `shared/limitations.schema.json` | shared | `1.0` | Group 1 | none | `tests/fixtures/cltr_cutover/shared/limitations/` | Group 1 verification |
| 1 | `records/authority_epoch.schema.json` | `records/authority_epoch.schema.json` | AuthorityEpoch | `1.0` | Group 2 | `shared/*` (envelope, enums, identity, digest, references, limitations) | `tests/fixtures/cltr_cutover/records/authority_epoch/` | Group 2 verification (136J/136K) |
| 2 | `records/authority_state.schema.json` | `records/authority_state.schema.json` | AuthorityState | `1.0` | Group 2 | `shared/*` + `authority_epoch` family reference (by `record_reference`, not `$ref`) | `tests/fixtures/cltr_cutover/records/authority_state/` | Group 2 verification |
| 3 | `records/cutover_request.schema.json` | `records/cutover_request.schema.json` | CutoverRequest | `1.0` | Group 3 | `shared/*` | `tests/fixtures/cltr_cutover/records/cutover_request/` | Group 3 verification (136L/136M) |
| 4 | `records/readiness_package.schema.json` | `records/readiness_package.schema.json` | ReadinessEvidencePackage | `1.0` | Group 3 | `shared/*` | `tests/fixtures/cltr_cutover/records/readiness_package/` | Group 3 verification |
| 5 | `records/human_authorization.schema.json` | `records/human_authorization.schema.json` | HumanAuthorization | `1.0` | Group 4 | `shared/*` | `tests/fixtures/cltr_cutover/records/human_authorization/` | Group 4 verification (136N/136O) |
| 6 | `records/cutover_candidate.schema.json` | `records/cutover_candidate.schema.json` | CutoverCandidate | `1.0` | Group 4 | `shared/*` (including embedded `cas_expectation`) | `tests/fixtures/cltr_cutover/records/cutover_candidate/` | Group 4 verification |
| 7 | `records/certification.schema.json` | `records/certification.schema.json` | Certification | `1.0` | Group 4 | `shared/*` (including embedded `cas_expectation`) | `tests/fixtures/cltr_cutover/records/certification/` | Group 4 verification |
| 8 | `records/publication_attempt.schema.json` | `records/publication_attempt.schema.json` | PublicationAttempt | `1.0` | Group 5 | `shared/*` (including embedded `cas_expectation`) | `tests/fixtures/cltr_cutover/records/publication_attempt/` | Group 5 verification (136P/136Q) |
| 9 | `records/publication_evidence.schema.json` | `records/publication_evidence.schema.json` | PublicationEvidence | `1.0` | Group 5 | `shared/*` | `tests/fixtures/cltr_cutover/records/publication_evidence/` | Group 5 verification |
| 10 | (embedded `$def`, `shared/references.schema.json#/$defs/cas_expectation`) | n/a — no standalone `$id` | CasExpectation | `1.0` (versioned with its owning file) | Group 1 (defined) / used by Groups 4–5 | none of its own; `$ref`-included at 2 sites | covered by `cutover_candidate`/`publication_attempt` fixture sets | Group 1 + Group 4/5 verification |
| 11 | `records/concurrency_conflict.schema.json` | `records/concurrency_conflict.schema.json` | ConcurrencyConflict | `1.0` | Group 5 | `shared/*` | `tests/fixtures/cltr_cutover/records/concurrency_conflict/` | Group 5 verification |
| 12 | `records/recovery_journal_entry.schema.json` | `records/recovery_journal_entry.schema.json` | RecoveryJournalEntry | `1.0` | Group 5 | `shared/*` | `tests/fixtures/cltr_cutover/records/recovery_journal_entry/` | Group 5 verification |
| — | (row 13, ReconciliationResult) | n/a — no schema file | derived view | n/a | not scheduled (optional `views/` doc only, §30) | n/a | n/a | n/a |
| 14 | `records/quarantine_record.schema.json` | `records/quarantine_record.schema.json` | QuarantineRecord | `1.0` | Group 5 | `shared/*` | `tests/fixtures/cltr_cutover/records/quarantine_record/` | Group 5 verification |
| — | (row 15, Authority Transition Receipt) | n/a — not required | absorbed | n/a | n/a | n/a | n/a | n/a |
| 16 | `records/notification_authority_binding.schema.json` | `records/notification_authority_binding.schema.json` | NotificationAuthorityBinding | `1.0` | Group 6 | `shared/*` | `tests/fixtures/cltr_cutover/records/notification_authority_binding/` | Group 6 verification (136R/136S in extended roadmap) |
| 17 | `records/marker_authority_binding.schema.json` | `records/marker_authority_binding.schema.json` | MarkerAuthorityBinding | `1.0` | Group 6 | `shared/*` | `tests/fixtures/cltr_cutover/records/marker_authority_binding/` | Group 6 verification |
| 18 | `records/receipt_authority_binding.schema.json` | `records/receipt_authority_binding.schema.json` | FinalizationReceiptAuthorityBinding | `1.0` | Group 6 | `shared/*` | `tests/fixtures/cltr_cutover/records/receipt_authority_binding/` | Group 6 verification |
| 19 | `records/compatibility_state.schema.json` | `records/compatibility_state.schema.json` | CompatibilityState | `1.0` | Group 6 | `shared/*` | `tests/fixtures/cltr_cutover/records/compatibility_state/` | Group 6 verification |
| — | (row 20, HistoricalAuthorityReference) | n/a — no schema file, typed-model-only | runtime-only | n/a | not scheduled (typed-model phase, far beyond this plan) | n/a | n/a | n/a |
| — | `README.md` | n/a | documentation | n/a | Group 1 (package scaffolding) | n/a | n/a | Group 1 verification |

**Exact totals** (restating 136C §4.1, independently reconfirmed by this
plan's own count of the table above):

- Shared definition files: **7**.
- Standalone record schemas: **16**.
- Binding schemas: **3** (rows 16–18, counted within the 16 above, not
  additionally).
- Derived views: **0** schema files (row 13 documented only, optionally).
- Manifest/registry metadata files: **0 today**; a manifest is planned as
  optional (§16) and, if adopted, would add exactly 1 file
  (`schemas/cltr_cutover/manifest.json` or equivalent).
- Fixture directories: **23** (7 shared + 16 record, one directory per
  file in the table above, each split into `valid/`/`invalid/`
  subdirectories per §14).
- Embedded schema components: **1** (`cas_expectation`, 2 `$ref` sites).
- Not-required families: **1** (row 15).
- Runtime-only typed models: **1** (row 20).

**Reconciliation of the verified 20-family classification:** every one
of 135Z's 20 rows, as re-confirmed unchanged through 136A → 136B → 136C →
136D, has exactly one disposition in the table above — 16 standalone
files, 1 embedded component, 1 derived view (no file), 1 not-required (no
file), 1 runtime-only (no file). This plan changes no classification; it
only adds implementation-group and fixture-set metadata on top of the
already-frozen inventory.

---

## 8. `$id` strategy

**Frozen by 136C §2/§3 (`https://pcae.local/schemas/cltr_cutover/<relative-
path>.schema.json`), reconfirmed here as the implementation-time
convention; this plan adds no new `$id` decision beyond confirming it
matches this repository's existing convention.**

- **Form:** repository-local, HTTPS-*shaped* identifiers under a
  non-resolvable `pcae.local` host — never fetched over the network at
  validation time (enforced structurally in §4 by configuring the
  `jsonschema` `Registry` with no retrieval function at all, so an
  attempted network-shaped `$id` resolution is not merely discouraged but
  structurally impossible).
- **Base ID:** `https://pcae.local/schemas/cltr_cutover/`.
- **Per-file ID:** base + the file's own path relative to
  `schemas/cltr_cutover/` (e.g.
  `https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json`).
- **Version inclusion:** **not** encoded in the `$id` path itself — version
  is carried by the in-document `schema_version` field (136C §15), not by
  a versioned URL path segment. Rationale: 136C §15 already establishes a
  minor-forward-compatible, major-breaking versioning discipline scoped
  to the file's own content; embedding a version number into the `$id`
  path would create a second, path-based versioning axis that could
  drift from the in-document `schema_version` field, and would force
  every `$ref` in the package to be rewritten on every version bump
  rather than only the referencing file's `schema_version` claim
  changing. This is consistent with `schemas/repository_intelligence/`'s
  own precedent, which does not version-stamp its `$id` paths either.
- **Family identity:** carried by the in-document `record_type` `const`
  field (136C §7.1), not by the `$id` — the `$id` identifies the *schema
  file*, `record_type` identifies the *record family* a validated document
  claims to be; these are related but distinct (a future minor-version
  schema file for the same family keeps the same `$id` path and the same
  `record_type` value, only `schema_version` changes).
- **Collision handling:** the future registry (§17) rejects at load time
  if two files declare the same `$id` (restating 136C §41's registry
  contract) — this is a load-time uniqueness check over the fixed,
  version-controlled file tree, not a runtime collision-resolution
  mechanism, since collisions in a hand-authored, code-reviewed schema
  tree are a authoring bug to catch immediately, not a runtime condition
  to gracefully handle.
- **Historical versions:** because version is not path-encoded, a
  "historical" schema version (needed to re-validate an old record against
  its original `schema_version`, 136C §15) is planned to be resolved by
  the future registry keeping, in memory, more than one loaded
  `Draft202012Validator` instance per `$id` — one per distinct
  `schema_version` string the registry has ever loaded from the current
  file tree plus any explicitly archived prior-version schema files under
  a planned `schemas/cltr_cutover/archive/<version>/` path (not created in
  this plan; scheduled only if and when a real minor/major bump first
  occurs — no archived version exists yet, since no schema exists yet).
- **Resolver mapping:** the registry's `$id → filesystem path` map is
  computed once, at registry construction time, by walking
  `schemas/cltr_cutover/{shared,records}/**/*.schema.json` and reading
  each file's own declared `$id` — never by string-transforming a path
  into an assumed `$id` (avoids a class of bug where a file's declared
  `$id` and its filesystem path silently diverge without detection).

---

## 9. `$ref` graph plan

**No cycles.** Every `$ref` in this package points from a `records/` file
into a `shared/` file, or from one `shared/` file into another `shared/`
file at a strictly lower layer (§9.1 below) — never from `records/` into
`records/`, and never from a `shared/` file back up into `records/`. This
is independently re-confirmed acyclic by 136D §13 ("no circular reference
graph exists among the frozen `$ref` targets... confirmed by re-scanning
every `$ref` mention"), and this plan's own topological ordering below
depends on, and does not weaken, that acyclicity.

### 9.1 Shared-file dependency layers (bottom to top)

```
Layer A (no internal $ref):  identity.schema.json, digest.schema.json,
                              enums.schema.json, failures.schema.json,
                              limitations.schema.json
Layer B ($ref → Layer A):    references.schema.json
                                (→ identity.schema.json, digest.schema.json,
                                   enums.schema.json)
Layer C ($ref → Layer A+B):  envelope.schema.json
                                (→ identity.schema.json, digest.schema.json,
                                   references.schema.json,
                                   limitations.schema.json, enums.schema.json,
                                   failures.schema.json)
```

### 9.2 Record-family cross-record binding (via `record_reference`, not `$ref`)

Cross-*record* relationships (e.g. `CutoverCandidate` referencing a
`CutoverRequest`) are **never** expressed as a `$ref` from one
`records/*.schema.json` file into another. They are expressed as the
shared `record_reference` shape (`id` + `digest` + `record_family`,
136C §12) — a `$ref` only to `shared/references.schema.json`, carrying an
*opaque string* naming the target family, not a live schema-graph edge.
This is the deliberate design (independently reconfirmed sound by 136D
§13) that keeps the **schema-authoring** dependency graph flat (every
`records/` file only ever depends on `shared/`) even though the
**runtime record-creation** order (§9.3) is a longer chain — 136D §20
explicitly distinguishes these two graphs and confirms a fix to one does
not imply a fix to the other, which this plan preserves by never
conflating them.

### 9.3 Runtime record-creation order (not a `$ref` graph — documented for
implementation-sequencing context only, restating 136C §19.1 as repaired
by 136D)

```
AuthorityEpoch (proposed)
    │
    ▼
ReadinessEvidencePackage  ──────────┐
    │                                │
    ▼                                │
CutoverRequest (references           │
  readiness_package_reference,       │
  unconditionally required)          │
    │                                │
    ▼                                │
HumanAuthorization (references       │
  request + readiness + target       │
  epoch) ◄─────────────────────────┘
    │
    ▼
CutoverCandidate (references
  stage2_generation + embeds
  cas_expectation)
    │
    ▼
Certification (references
  candidate + request + readiness +
  authorization)
    │
    ▼
PublicationAttempt (references
  request + candidate + certification,
  embeds cas_expectation)
    │
    ▼
PublicationEvidence (references
  attempt)
    │
    ▼
AuthorityState (references epoch +
  publication_evidence)
```

`ConcurrencyConflict`, `RecoveryJournalEntry`, `QuarantineRecord`, and the
three binding families attach to this chain at their own respective
points (concurrency/journal/quarantine reference whichever operation
they concern; the bindings reference the generation/epoch/marker/receipt
they extend) without introducing a cycle back into the chain above.

### 9.4 Topological implementation order (schema-*authoring* graph, §9.1–§9.2 combined)

1. Layer A shared files (`identity`, `digest`, `enums`, `failures`,
   `limitations`) — no dependencies, must exist first.
2. Layer B (`references.schema.json`, including the embedded
   `cas_expectation` `$def`) — depends only on Layer A.
3. Layer C (`envelope.schema.json`) — depends on Layer A + B.
4. Any of the 16 `records/*.schema.json` files, in any order relative to
   each other (they share no `$ref` dependency on one another) — but
   **grouped** per §13 below for independent-verification-boundary
   reasons, not schema-authoring-dependency reasons.

---

## 10. Shared definitions implementation plan

| Definition | Schema file | Constraint | Reuse | Invalid fixtures (representative) | Semantic-validator limitation |
|---|---|---|---|---|---|
| `record_identity` (generic `record_id`) | `identity.schema.json` | `^[a-z][a-z0-9-]{7,127}$` (family-prefixed, lowercase, 8–128 chars total, per 136C §10) | every `records/*.schema.json`'s own `record_id` field | wrong-case, path separator, empty, over-length, missing prefix | does not verify the ID was actually *derived* from its owning record's bound-field tuple (136C §10's own disclosed boundary) |
| `sha256_hex` (digest) | `digest.schema.json` | `^[0-9a-f]{64}$`, exact match to `src/pcae/cltr/digest.py`'s actual implementation (136D §12, independently reproduced against source) | every digest-typed field package-wide | uppercase hex, 63/65-char length, non-hex character, `sha256:`-prefixed form | does not recompute the digest against canonical bytes (Layer 3) |
| `record_reference` | `references.schema.json` | object `{record_id, record_digest, record_family, schema_id?, schema_version?}`, `additionalProperties: false` | every cross-record-referencing field | missing `record_family`, wrong-family string, extra key | does not verify the referenced record actually exists or actually matches the claimed family (Layer 4) |
| `timestamp` | (inline per-field `pattern`, not a separate shared file — 136C §13 keeps this as a `pattern` string reused via `$ref` from `digest.schema.json`-adjacent scope or duplicated `pattern` string; this plan schedules a small dedicated `$def` inside `envelope.schema.json` rather than a 7th "timestamp" file, since only `envelope.schema.json` and family-local `*_at` fields need it) | `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$` | every `*_at`/`created_at`/`issued_at`/`expires_at` field | numeric offset (`+00:00`), missing `Z`, leap second, sub-microsecond precision | does not compare against wall-clock "now" (Layer 4/5) or verify UTC-vs-local intent beyond the literal `Z` suffix |
| `version` (`schema_version`, `contract_version`) | `envelope.schema.json` inline | `schema_version`: `^\d+\.\d+$`; `contract_version`: `const "1.0"` at freeze time | every `records/*.schema.json` | non-numeric segment, 3-segment semver, wrong `contract_version` const | does not verify actual minor/major-compatibility behavior at validation time beyond static shape (136C §15's compatibility rule is a Layer 6 policy, not a Layer 2 assertion) |
| `epoch` (`migration_epoch`) | `identity.schema.json` | `^[a-z0-9._-]{1,64}$`, no `/`, no `..` | every companion record (136C §7.2: required on all 16 families) | path separator, traversal string, empty, over-length | does not verify the epoch value corresponds to a real, currently-active migration epoch (Layer 4) |
| `limitations` array | `limitations.schema.json` | array of non-empty strings, each length-bounded (§15 below resolves the exact bound) | every `records/*.schema.json` | empty-string entry, over-length entry, non-array value | free text is inherently not machine-verifiable beyond shape/length (Layer 4 for content review, if ever needed) |
| `authority_disclosure` | `limitations.schema.json` (co-located, since it is conceptually a limitations/disclosure concern per 136B §8) | object `{authority_role, is_authoritative: const false, disclosure_text}` — `is_authoritative` `const false` on every companion record | every `records/*.schema.json` except the two narrow §9-contract exceptions (`authority_state`, `publication_evidence`, both still conditionally, never unconditionally, `true`) | `is_authoritative: true` on a forbidden family, missing `disclosure_text` | does not verify the *live* authority state matches this record's own claim (Layer 6) |
| `principal_identifier` | `identity.schema.json` | `^[A-Za-z0-9._@-]{1,256}$`, ASCII-only (136C §10) | `human_authorization.schema.json` only (136C §6.1: "only on `human_authorization.schema.json`") | Unicode confusable, path separator, over-length, empty | does not verify the principal identity against any real identity-provider or authentication system (explicitly out of scope, 135Z §8.3) |
| `proof reference` (`proof_reference`) | `references.schema.json` (reuses `record_reference`, not a new shape) | same as `record_reference`; never a raw signature blob | `human_authorization.schema.json`, `certification.schema.json` (verifier evidence) | a field containing what looks like an embedded credential/signature blob rather than an opaque reference | shape alone cannot distinguish an opaque reference from an embedded secret by content — this is explicitly a documentation/convention-level guarantee, not a schema-enforceable one (136D §23, honestly disclosed) |
| `reason_code` | `failures.schema.json` | closed `enum`, no wildcard/catch-all member | every field requiring a machine-readable reason (§19's error model, quarantine `reason_code`, conditional `staleness`/`invalidation` objects) | unknown string value, empty string | does not verify the reason code was *correctly assigned* for the actual failure that occurred (Layer 4) |

**Overly broad generic definitions avoided:** `record_identity` and
`sha256_hex` are deliberately kept as bare, narrowly-patterned string
shapes rather than a single "opaque identifier" `$def` that both digests
and record IDs would share — 136B §8 already made this exact
narrowness decision (documented as the reason `generation_reference`
pairs an ID+digest rather than allowing a bare unpaired ID field
anywhere), and this plan preserves it rather than introducing a looser
convenience type.

---

## 11. Enum implementation plan

**Disposition: grouped by domain, in two tiers — 7 shared cross-family
enums centralized in `shared/enums.schema.json`, 14 family-local enums
co-located in their owning `records/*.schema.json` file — restating and
freezing-for-implementation 136B §10/136C §8's already-decided split; this
plan adds no new enum-organization decision.**

Rationale for not centralizing all 21 into one file: the 7 shared enums
(`AuthorityKind`, `AuthorityRole`, `MigrationStage`, `GenerationRole`,
`PublicationState`, `RecoveryState`, `CompatibilityMode`) are genuinely
cross-family vocabulary, referenced from multiple `records/` files, and
centralizing them lets a single `$ref` update cover every consumer on a
future enum revision. The 14 local enums (`RequestState`,
`ReadinessState`, `AuthorizationState`, `CandidateState`,
`CertificationState`, `GateResult`, `PublicationOutcome`, `ConflictType`,
`JournalState`, `ReconciliationState`, `QuarantineState`, `DeliveryState`,
`MarkerState`, `ReceiptState`) are each scoped to exactly one owning
family; centralizing them into one giant enum file would create a false
appearance of cross-family shared vocabulary where none exists, and would
make a single family's local-state-machine revision touch a shared file
every other family's schema also depends on — exactly the "unsafe
coupling" this section's brief warns against.

**Test plan per enum (applies uniformly to all 21):**

- **Exact case.** A fixture using the correctly-cased wire value passes;
  a fixture using a differently-cased variant (e.g. `Legacy` for
  `legacy`) fails — proving no implicit case-folding occurs.
- **Aliases.** A fixture using a plausible-but-unlisted synonym (e.g.
  `active` where the enum requires `authoritative_generation`) fails —
  proving no alias table is silently consulted.
- **Unknown values.** A fixture using a value outside the enum's `enum`
  array entirely (e.g. a made-up string) fails closed — the direct
  executable proof of 136C §8's "unknown-value behavior: reject" rule for
  every one of the 21 enums.
- **Wrong-domain enum reuse.** A fixture substituting one family's local
  enum value into a field typed for a different family's enum (e.g. using
  a `CandidateState` value where `CertificationState` is expected) fails
  — proving the two enums are not silently interchangeable despite both
  being small closed string sets.
- **Version extension.** A fixture using a value that is valid in a
  *future*, not-yet-existing minor-version enum extension is explicitly
  planned to still **fail** against the *current* schema version (136C
  §8's "a new enum member may only be added via a `schema_version` minor
  bump on the owning file, never silently" rule) — the test proves that
  the current schema file does not pre-emptively accept an as-yet-unadded
  future value.

---

## 12. Envelope implementation plan

**Disposition: `allOf` composition of the shared `companion_envelope`
`$def` with each family's own local `properties`/`required`/
`additionalProperties`, never `unevaluatedProperties` — restating and
freezing-for-implementation 136B §9/136C §2's already-decided mechanism.**

- **Mechanism:** each `records/*.schema.json` file's top-level schema is
  `{"allOf": [{"$ref": "../shared/envelope.schema.json#/$defs/companion_envelope"}, {<this file's own object schema, its own "properties"/"required"/"additionalProperties": false>}]}`.
  This is the one, explicitly bounded use of `allOf` this contract permits
  (136C §2: "`allOf` [is] permitted only to compose a record's own `$defs`
  with the shared envelope `$def`; never used to merge two independently-
  `additionalProperties`-constrained subschemas").
- **Why not `unevaluatedProperties`:** the classic `allOf` +
  `additionalProperties: false` interaction hazard (a well-known JSON
  Schema pitfall where each `allOf` branch's own `additionalProperties:
  false` only "sees" that branch's own `properties`, so a property defined
  in a *sibling* `allOf` branch is incorrectly rejected as "additional")
  is avoided **by construction**, not by using `unevaluatedProperties` to
  paper over it: the envelope `$def` itself carries no
  `additionalProperties: false` of its own (only the *outer*,
  file-specific schema does, listing every field — both envelope-derived
  and family-local — in its own single `properties` block). This plan
  therefore schedules each `records/*.schema.json` file's own
  `properties` block to **explicitly re-list every envelope field
  alongside its own family-local fields**, with exactly one
  `additionalProperties: false` (or the Tier-2 `_extensions`-only variant,
  §14 below) at the outer level — the envelope `$ref` supplies the
  *type constraints* for each field (via each field's own `$ref` into
  `identity.schema.json`/`digest.schema.json`/etc.), while the outer
  file's `properties`/`required` supplies the *closure* — avoiding
  `unevaluatedProperties` entirely, exactly as 136C §2 requires ("This
  package does not compose schemas via `allOf` in a way that would
  require `unevaluatedProperties`").
- **Draft 2020-12 behavior accounted for:** `additionalProperties` in
  Draft 2020-12 (like every prior draft) only inspects the *same
  subschema's own* `properties`/`patternProperties` when deciding what
  counts as "additional" — this plan's "re-list every field in the outer
  file's own `properties`" approach is the direct, correct way to satisfy
  that constraint without invoking `unevaluatedProperties`'s
  cross-branch-aware (and more implementation-variable-across-validators)
  behavior.
- **Nested unknown-field tests planned:** for every one of the 16
  standalone families, a fixture is planned that adds an unknown key
  **nested inside** an already-valid embedded object (e.g. inside the
  `cas_expectation` embedded `$def`, or inside a `revocation_metadata`
  conditional object) — not just at the top level — since a naive
  implementation could correctly close the top-level envelope while
  leaving a nested embedded object's own `additionalProperties`
  unconstrained; this is planned as its own fixture category (§14) rather
  than assumed covered by the top-level unknown-field fixture.

---

## 13. Schema implementation groups

Derived from the dependency graph (§9) and the fixed 16-family
disposition (§7), grouping by both dependency order and blast-radius
(authority-bearing Tier 1 families grouped separately from evidentiary
Tier 2 families where the dependency graph allows it, so that an
independent-verification pass over a purely evidentiary group is not
blocked on, or diluted by, an authority-bearing group's own review):

### Group 1 — Core profiles and shared definitions

- `shared/envelope.schema.json`, `shared/enums.schema.json`,
  `shared/identity.schema.json`, `shared/digest.schema.json`,
  `shared/references.schema.json` (including embedded `cas_expectation`),
  `shared/failures.schema.json`, `shared/limitations.schema.json`,
  `schemas/cltr_cutover/README.md`.
- **Dependency prerequisites:** the dependency-introduction prerequisite
  phase (§4) must be complete and independently verified first — Group 1
  is the first group whose own tests actually exercise `jsonschema`.
- **Expected tests:** meta-schema self-validity of every shared file, all
  21 enum tests (§11), all shared-`$def` fixture tests (§10, §14), the
  `$ref` graph's Layer A→B→C resolution test (offline, no network).
- **No-go criteria:** any shared `$def` found to require network
  resolution; any enum found to silently accept an unlisted value; any
  circular `$ref` among the 7 shared files.

### Group 2 — Authority core

- `records/authority_epoch.schema.json`, `records/authority_state.schema.json`.
- **Dependency prerequisites:** Group 1 complete and independently
  verified.
- **Expected tests:** all §7 fixture-set categories for both families;
  the AuthorityEpoch proposed-vs-active conditional (§16 row 1 of 136C);
  AuthorityState's tagged-union `current_authoritative_object`/
  `oneOf` composition.
- **No-go criteria:** either schema found capable of expressing
  `authority_role: authoritative` unconditionally (violating 136C §9);
  the proposed/active conditional found expressible in a way that permits
  a freshly-proposed epoch to validate with `activation_state: active`.

### Group 3 — Request and readiness

- `records/cutover_request.schema.json`, `records/readiness_package.schema.json`.
- **Dependency prerequisites:** Group 1 complete and independently
  verified. (Not Group 2 — §9.2 confirms no `$ref` dependency of
  `cutover_request`/`readiness_package` on `authority_epoch`/
  `authority_state`; only shared `record_reference` shapes are used. Group
  3 may in principle proceed in parallel with Group 2; this plan schedules
  it sequentially after Group 2 anyway, per §13's own closing instruction
  to prefer sequential, reviewable groups over parallel unverified
  authority-relevant work, since both groups sit close to the authority
  boundary.)
- **Expected tests:** the repaired non-circular creation-order fixtures
  (§9.3 — a `cutover_request` fixture whose `readiness_package_reference`
  points at an independently-fixtured `readiness_package`, proving the
  BLOCKING-136D-1 repair is reflected in actual schema behavior, not just
  contract prose); `readiness_package`'s `state == "conflict"` ⇒
  non-empty `BLOCKING`-verdict `findings` conditional.
- **No-go criteria:** any schema construction that reintroduces the
  repaired circular "request v1/v2" shape; `readiness_package_reference`
  found optional rather than unconditionally required.

### Group 4 — Authorization and candidate

- `records/human_authorization.schema.json`,
  `records/cutover_candidate.schema.json`, `records/certification.schema.json`.
- **Dependency prerequisites:** Groups 1–3 complete and independently
  verified (this group's `record_reference` fields conceptually point at
  Group 2 and Group 3 families, even though no `$ref` edge exists —
  fixture authoring for this group needs Group 2/3's fixture IDs/digests
  as realistic reference values).
- **Expected tests:** `risk_acknowledgement`/`scope` `const` enforcement;
  `revocation_state`/`used_state` conditional pairs; the embedded
  `cas_expectation`'s all-11-fields-required (no-wildcard) property,
  fixtured twice (once embedded in `cutover_candidate`, once in
  `certification`'s own `cas_expectation` field — wait, `certification`
  carries a `cas_expectation` per 136C §23's own field table, confirming
  both embedding sites this plan's §9.1/§7 table already lists).
- **No-go criteria:** any `cas_expectation` field found omittable while
  still schema-valid (reintroducing the wildcard-on-missing-value hazard
  136C §11.2/136D §8 identify as this contract's single most
  safety-critical rule).

### Group 5 — CAS, publication, recovery, and quarantine

- `records/publication_attempt.schema.json`,
  `records/publication_evidence.schema.json`,
  `records/concurrency_conflict.schema.json`,
  `records/recovery_journal_entry.schema.json`,
  `records/quarantine_record.schema.json`.
- **Dependency prerequisites:** Groups 1–4 complete and independently
  verified.
- **Expected tests:** the seven/eight-value `PublicationOutcome`
  pairwise-distinctness tests (§11); `publication_uncertain` never
  collapsing into a failure outcome; the recovery-journal hash-chain
  field shape (`prior_entry_digest` null only at `sequence == 0`);
  quarantine's unconditional `reason_code` requirement.
- **No-go criteria:** any construction allowing `publication_uncertain`
  and a failure outcome to be simultaneously schema-satisfiable for the
  same document (a same-document contradiction, distinct from the
  legitimate Layer-4 concern of comparing two documents); any quarantine
  fixture found valid without a `reason_code`.

### Group 6 — Terminal bindings and compatibility

- `records/notification_authority_binding.schema.json`,
  `records/marker_authority_binding.schema.json`,
  `records/receipt_authority_binding.schema.json`,
  `records/compatibility_state.schema.json`.
- **Dependency prerequisites:** Groups 1–5 complete and independently
  verified (receipt binding's `publication_evidence_reference`
  conditional, §16 row 9 of 136C, conceptually depends on Group 5's
  `PublicationEvidence` family existing first for realistic fixture
  authoring).
- **Expected tests:** the `receipt_state == "finalized"` ⇒ all-three-
  references-required conditional; `compatibility_state`'s
  `mode`-restricted `authority_role` (never `authoritative`/`derivative`
  once in a historical/disabled/retired mode); the repaired
  `compatibility-state/` history-subdirectory persistence-path
  *documentation* (this is a Layer 6/deployment property, not a
  schema-shape property per 136D §34 — no schema-level test asserts a
  filesystem path, but the schema file's own `description` fields must
  match the BLOCKING-136D-2-repaired path text).
- **No-go criteria:** any binding schema found capable of declaring
  `authority_role: authoritative`; any compatibility-state fixture in a
  historical/disabled/retired mode found valid with `authority_role:
  authoritative` or `derivative`.

**Every group's implementation phase is followed by its own independent-
verification phase before the next group begins** (§24, §33) — this plan
does not schedule implementing all six groups in one unverified pass; the
dependency analysis above (each later group's fixtures needing realistic,
already-fixtured reference values from earlier groups, and the
authority-adjacent groups 2–5 benefiting from independent review before
compounding) supports sequential, verified groups over a single big-bang
implementation.

---

## 14. Fixture plan

For every one of the 16 standalone schemas (plus the 7 shared `$defs`
files and the embedded `cas_expectation` component), fixtures are planned
under `tests/fixtures/cltr_cutover/{shared,records}/<family>/{valid,invalid}/`
covering, per family, every category 136C §42 already obligates plus this
plan's own nested-unknown-field addition (§12):

- minimal valid document (only required fields);
- maximal valid document (every optional field populated);
- one fixture per enum value for every enum-typed field on that family;
- missing required field (one fixture per required field, or — where a
  family has an unusually large required-field count, e.g.
  `cutover_request`'s ten-plus fields — a documented representative
  subset explicitly justified in that family's own fixture `README`);
- extra field at the top level (Tier 1: any extra key rejected; Tier 2:
  any key other than `_extensions` rejected);
- extra field nested inside an embedded object (§12's addition — at least
  one fixture per family that has an embedded/conditional object field);
- wrong type (a string where an object is expected, a number where a
  string is expected, etc. — at least one representative case per family,
  not necessarily every field);
- malformed ID (violates the `record_identity` pattern, §10);
- malformed digest (violates the `sha256_hex` pattern, §10);
- unsupported schema version (a `schema_version` claiming a nonexistent
  major version, per §15's compatibility rule);
- null versus absent (one fixture per family demonstrating the §7.4
  distinction — a conditionally-absent field represented as explicit
  `null` must fail; an always-present-nullable field represented as
  absent must fail);
- state-condition violation (one fixture per `if`/`then` row in 136C §16
  that applies to that family);
- reference family mismatch (a `record_reference` whose `record_family`
  value does not match the field's documented expected family);
- traversal string (a `storage_locator` or identifier field containing
  `..` or a leading `/`, for the three binding families that carry
  `storage_locator`, §12 of 136C);
- remote URI (a `$ref`-shaped or `$id`-shaped string injected into an
  ordinary data field, to prove the schema's own `pattern` constraints —
  not a live `$ref` resolution — reject a URL-shaped value where a plain
  identifier is expected);
- oversized text (a `limitations` entry, or another free-text field per
  §15's resolved bounds, exceeding the planned maximum length);
- secret-containing invalid example (a `principal_identity` or
  `replay_binding`/`proof_reference`-shaped field populated with an
  obviously secret-shaped string, e.g. a bearer-token-shaped value —
  documented, per §10's table, as a fixture whose *rejection* is a
  documentation/convention check, since shape alone cannot always
  distinguish a secret from an opaque reference; where the pattern *can*
  mechanically reject it — e.g. a field with a strict opaque-token regex
  that a realistic secret shape would violate — the fixture is a true
  schema-level negative test);
- Unicode edge cases (a non-ASCII character in an ASCII-only-patterned
  identifier field; a right-to-left override or zero-width character in
  a free-text `limitations` entry, to confirm the fixture-level behavior
  matches the documented Unicode policy, §15).

**Fixtures are static, deterministic JSON files, hand-authored and
version-controlled** (never generated at test-run time from randomized
input) — consistent with this repository's existing fixture conventions.
**No fixture may contain real credentials or production data** — every
identifier, digest, and principal value in every fixture is a clearly
synthetic placeholder (e.g. digests are the SHA-256 of a fixed, documented
placeholder string, never a copied real repository digest; principal
identifiers are synthetic names, never a real operator's actual
identity).

---

## 15. Free-text bounds plan

Every human-readable field across the 16 families, classified:

| Field | Family/families | Classification | Planned max length | Newline behavior | Control-character behavior | Unicode policy | Reason codes mandatory? | Truncation | Large payloads |
|---|---|---|---|---|---|---|---|---|---|
| `limitations[]` entries | all 16 | limitation | 2,000 characters per entry, max 32 entries per array | permitted (a limitation may be a short multi-line note), but no more than 8 newline characters per entry | forbidden — any C0/C1 control character other than `\n`/`\t` rejected by `pattern` | full Unicode permitted, NFC-normalization is a Layer 3 concern (not schema-asserted, consistent with §39's canonicalization boundary) | no — `limitations` is explicitly free text, not a reason-code field | rejected outright at the max length (not silently truncated) — a caller producing an over-length limitation must shorten it before writing, since silent truncation could hide safety-relevant detail | not applicable (limitations are inherently short prose, never a large-payload carrier) |
| `disclosure_text` (`authority_disclosure`) | all 16 | diagnostic/disclosure | 500 characters | forbidden (single-line only — this is a short, fixed-purpose disclosure sentence, not free-form prose) | forbidden | ASCII + common Latin-1 punctuation only (a stricter policy than `limitations`, since this field's content is drawn from a small, contract-defined set of disclosure sentences, not open operator input) | no | rejected outright | not applicable |
| `recovery_action` (`recovery_journal_entry`) | RecoveryJournalEntry | operator note | 4,000 characters | permitted, up to 16 newlines | forbidden except `\n`/`\t` | full Unicode | **yes, in addition to free text** — `recovery_action` is required only alongside `state == "actioned"`, and this plan schedules an additional, machine-readable `reason_code` field (drawn from `failures.schema.json`) alongside it, so the free text is a supplement to, never a substitute for, a checkable code | rejected outright | referenced, not embedded — if an operator's recovery action produced a long log/output artifact, this plan schedules that artifact being stored elsewhere (e.g. under `.pcae/cltr-authority/...` evidence, outside the schema-governed record itself) and referenced by `record_reference`, never pasted into this field wholesale |
| `risk_acknowledgement`-adjacent free text (none exists — `risk_acknowledgement` itself is `const true`, not free text) | HumanAuthorization | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| operator note / `staleness`/`invalidation` reason (`certification.staleness.reason_code`, `certification.invalidation.reason_code`) | Certification | diagnostic | n/a — these are `reason_code` enum fields already, not free text, per 136C §23's own table; no separate free-text companion field is planned, since the enum is sufficient | n/a | n/a | n/a | yes — already a `reason_code` | n/a | n/a |
| error detail (planned future `ShapeValidationResult` error messages, §18/§19) | not a schema field — this is the *validator's own output*, not a persisted record field | diagnostic (validator output, not record content) | 1,000 characters per individual error message (a defensive cap on validator-generated diagnostic text, not a schema-governed field) | permitted | forbidden except `\n` | full Unicode (validator messages may quote user-supplied strings) | no — the structured `.validator`/`.schema_path`/`.absolute_path` fields on each error are the machine-readable part; the message string is human-readable supplementary text | truncated with an explicit `"...[truncated]"` marker if it would exceed the cap (distinct from persisted-record fields above, since a validator error message concatenating multiple deeply-nested paths could legitimately grow long, and silently dropping the whole message would be a worse outcome than a marked truncation for a purely diagnostic, non-persisted string) | not applicable |
| `component` (`compatibility_state`) | CompatibilityState | identifier-like, not free prose | 128 characters | forbidden | forbidden | ASCII identifier characters only (`[A-Za-z0-9._-]`) — this is closer to an identifier than to human prose, so it is patterned accordingly rather than treated as unbounded free text | no | rejected outright | not applicable |
| `principal_identity` | HumanAuthorization | identifier-like (already patterned, §10) | already bounded, 1–256 chars per 136C §10 — restated here for completeness, not a new bound | n/a (identifier, not prose) | forbidden (already ASCII-only per pattern) | ASCII-only (already frozen) | n/a | n/a | n/a |

No field is left unbounded. Every free-text field above resolves the
Non-Blocking 136D finding (family row-order presentation and unbounded
free-text length gap) for the free-text portion specifically; the
family-row-order cosmetic finding (NON-BLOCKING-136D-1) is a documentation
presentation issue in 136C's own prose table, out of this plan's scope
(it does not affect any schema file's actual content) and remains
open for a future minor documentation pass, as 136D itself recommended.

---

## 16. Schema manifest plan

**Disposition: a deterministic schema manifest is required, and is
scheduled before registry implementation (Group 1, alongside the shared
`$defs` files — not deferred to a later group).**

A manifest file, `schemas/cltr_cutover/manifest.json` (schema-governed by
a new, 8th shared-adjacent file, `manifest.schema.json`, or — to avoid
growing the frozen 7-file `shared/` inventory §7 already reconciles
exactly — planned instead as `schemas/cltr_cutover/manifest.schema.json`
sitting at the package root next to `README.md`, outside `shared/`, since
it describes the *package itself*, not a reusable `$def` any record
schema references), containing one entry per file in §7's inventory:

- `schema_id` (matching that file's own `$id`);
- `schema_version` (matching that file's own declared `schema_version`
  `const`/pattern);
- `file_path` (relative to `schemas/cltr_cutover/`);
- `file_digest` (SHA-256 of the file's own bytes, using the same
  `sha256_hex` shape as every other digest in this package — a
  tamper-evidence mechanism over the schema files themselves, distinct
  from any record's own `record_digest`);
- `family` (the `record_type` value the file governs, or `shared` for
  `shared/` files);
- `implementation_group` (1–6, per §13);
- `dependencies` (the file's own `$ref` targets, by `$id`);
- `status` (`frozen` | `draft` — all entries `frozen` once a group's
  independent verification passes, never `draft` in a committed state
  the registry would load);
- `contract_version` (`"CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001/1.0"`).

**Benefits addressed:**

- **Registry integrity:** the registry (§17) loads the manifest first and
  cross-checks every manifest entry's `file_digest` against the actual
  file on disk before trusting any schema content — a tampered or
  corrupted schema file is detected before it is ever used to validate a
  real record.
- **Duplicate detection:** the manifest's own `schema_id` and `(family,
  schema_version)` columns are checked for uniqueness at manifest-
  authoring/CI time, independent of and in addition to the registry's own
  runtime duplicate check (§17) — a belt-and-braces pairing, not a
  redundant one, since the manifest check runs even in contexts (e.g. a
  documentation build) that never construct a live registry.
- **Package completeness:** a test (§23) asserts the manifest's entry
  count exactly matches §7's frozen inventory (24 files, 16 records + 7
  shared + `README.md`, `README.md` itself carrying no digest-checked
  schema content but still listed for completeness) — catching an
  accidentally-omitted or accidentally-added file immediately.
- **Offline resolution:** the manifest's `dependencies` column is
  cross-checked against each file's actual `$ref` targets, giving the
  registry a pre-computed, offline-verifiable dependency list before it
  even opens each file for parsing.
- **Tamper detection:** as above (`file_digest`).
- **Deterministic tests:** since the manifest is a single, hand-
  maintained (or CI-generated-and-committed, decision deferred to the
  implementation phase itself) JSON file, tests over "does the package
  match its manifest" are simple, fast, and fully deterministic — no
  filesystem-walk-order dependency.

---

## 17. Registry implementation plan

A future, offline-only registry module (planned location:
`src/pcae/cltr/cutover_schemas/registry.py` or equivalent — exact module
path deferred to the implementation phase, not fixed by this plan) is
planned to provide:

- **Schema ID lookup:** `registry.get(schema_id: str) -> Draft202012Validator`,
  keyed by each file's own declared `$id`.
- **Version lookup:** `registry.get(schema_id: str, schema_version: str) ->
  Draft202012Validator`, resolving a specific historical or current
  version per §8's historical-version strategy.
- **Manifest verification:** on construction, the registry loads
  `manifest.json` first, then walks the actual file tree, verifying every
  manifest entry's `file_digest` matches the real file and that no file on
  disk is missing from the manifest (and vice versa) — a two-way
  completeness/integrity check, not a one-way lookup.
- **Duplicate rejection:** construction fails (raises, does not warn) if
  two files declare the same `$id`.
- **Unresolved-reference failure:** construction fails if any `$ref`
  target named inside a loaded schema file cannot be resolved within the
  local `Registry`/`Resource` set — proactively, at load time, not lazily
  on first validation attempt, so a broken reference is caught before any
  record is ever validated against it.
- **Deterministic ordering:** files are walked in a fixed, sorted
  (lexicographic relative-path) order, so duplicate-detection and
  unresolved-reference error messages are reproducible across runs and
  across machines.
- **No network fetching:** the underlying `jsonschema.Registry` is
  constructed with no retrieval function configured, ever — a structural,
  not merely documented, guarantee (§4's no-network test proves this at
  the dependency-introduction layer; the registry inherits the same
  guarantee by never overriding it).
- **Explicit supported dialect:** the registry rejects, at load time, any
  schema file whose `$schema` value is not exactly the frozen Draft
  2020-12 URI — no silent dialect auto-detection.
- **Cache behavior:** the registry loads and parses every schema file
  exactly once per process lifetime (or per explicit `reload()` call); it
  does not re-read files from disk on every `get()` call.
- **Error types:** a small, closed exception hierarchy —
  `SchemaRegistryError` (base), `DuplicateSchemaIdError`,
  `UnresolvedReferenceError`, `ManifestIntegrityError`,
  `UnknownSchemaError`, `UnsupportedDialectError`, `UnsupportedVersionError`
  — each carrying enough structured detail (the offending `$id`, file
  path, or version) for a caller to react programmatically, not merely
  print a message.
- **Read-only behavior:** the registry never writes to
  `schemas/cltr_cutover/` or to any runtime namespace; it is a pure
  read-and-index component.

**The registry must not:** resolve authority (no method reads or returns
anything about "current" authority); inspect runtime authority state (no
dependency on `.pcae/cltr-authority/...` at all — the registry only ever
reads `schemas/cltr_cutover/**`); mutate the repository (no write path
exists in the planned API surface); download schemas (no retrieval
function, ever, per the no-network guarantee above).

Registry implementation itself is **not** performed in this plan — it is
scheduled as part of a future implementation group (136P in the roadmap,
§33), after the schema content it indexes (Groups 1–6) is complete and
independently verified, since a registry over an incomplete or
still-changing schema set would need to be re-verified on every
subsequent group's completion, an avoidable ordering cost.

---

## 18. Validation API plan

Planned conceptual interface (illustrative signature; exact module path
and parameter names are an implementation-phase decision, not frozen by
this plan):

```python
def validate_record_shape(
    record: Mapping[str, object],
    *,
    schema_id: str,
    schema_version: str,
) -> ShapeValidationResult:
    ...
```

- **Strict parsed input:** `record` is planned to always be the output of
  §5's strict-parsing layer (duplicate-key-rejected, size/depth-bounded,
  UTF-8-decoded) — `validate_record_shape` itself does not re-parse raw
  bytes/text; it operates on an already-parsed, already-strict Python
  object graph, keeping Layer 1 (parsing) and Layer 2 (schema validation)
  as two composable, independently testable functions rather than one
  monolithic entry point.
- **Schema selection:** `schema_id` + `schema_version` are resolved
  through the registry (§17); an unknown pair raises `UnknownSchemaError`
  (or `UnsupportedVersionError` for a recognized `schema_id` with an
  unrecognized `schema_version`) rather than falling back to a "best
  guess" schema — restating 136C §41's fail-closed unknown-schema rule at
  the API boundary.
- **Result type:** `ShapeValidationResult` is planned as an immutable
  value object carrying `valid: bool`, `errors: tuple[ShapeValidationError,
  ...]` (empty iff `valid`), `schema_id: str`, `schema_version: str` — a
  data-only object, never itself raising for an ordinary invalid-input
  case (see next bullet).
- **Machine-readable errors, JSON pointer locations:** each
  `ShapeValidationError` carries `json_pointer: str` (e.g.
  `/authorization_requirement`, derived from `jsonschema`'s own
  `ValidationError.absolute_path`, converted to RFC 6901 JSON Pointer
  syntax), `keyword: str` (the failing JSON Schema keyword, e.g.
  `"required"`, `"pattern"`, `"enum"` — from `ValidationError.validator`),
  `message: str` (human-readable, length-capped per §15's error-detail
  row), and `reason_code: str | None` (a best-effort mapping from the
  failing keyword/context to one of §19's closed Layer-2 reason codes,
  `None` only if no mapping applies, never a silently-omitted field).
- **No exceptions for normal invalid input:** a schema-invalid record is
  planned to return `ShapeValidationResult(valid=False, errors=(...))`,
  never raise — reserving exceptions (§17's error hierarchy) for genuine
  operational failures (unknown schema, registry integrity failure,
  internal validator error), consistent with this repository's general
  preference for typed result objects over exceptions for expected,
  data-dependent outcomes (matching the existing `pcae phase-report
  reconcile` command's own "returns a structured result, does not raise
  for an ordinary conflict" pattern).
- **Explicit unsupported-schema errors:** `UnknownSchemaError`/
  `UnsupportedVersionError` (§17) are raised, not returned inside
  `ShapeValidationResult`, since an unresolvable `schema_id` is an
  operational/programmer error (the caller asked for something that does
  not exist), categorically different from "the caller's data doesn't
  match a schema that does exist."
- **No semantic claims:** `ShapeValidationResult.valid = True` means
  exactly and only "this document is shape-valid against this schema
  version" — it carries no field, flag, or method suggesting anything
  about identity recomputation, digest correctness, cross-record
  consistency, authority, or any other Layer 3–6 property (136C §1's
  "must not claim to validate" list, restated as an API-design constraint
  here).
- **No mutation:** `validate_record_shape` never writes to disk, never
  mutates `record` in place, never has any side effect beyond returning
  its result — a pure function over its two inputs (the record and the
  schema selector).

**Not implemented in 136E.**

---

## 19. Error-model plan

Two structurally distinct error families, planned:

**Layer 1 (parsing) errors** (§5): `parse_invalid_utf8`,
`parse_duplicate_key`, `parse_not_an_object`, `parse_oversized_input`,
`parse_excessive_nesting`, `parse_non_finite_number`,
`parse_malformed_json`.

**Layer 2 (schema validation) errors**, planned as a closed reason-code
set distinct from, and never conflated with, the parsing set above or
with any future Layer 3+ error:

| Reason code | Meaning |
|---|---|
| `unknown_schema` | `schema_id` not found in the registry |
| `unsupported_dialect` | a schema file's own `$schema` is not Draft 2020-12 (an authoring-time/registry-load-time error, never a per-record validation outcome) |
| `unsupported_version` | `schema_version` requested does not exist for a known `schema_id`, or a document's own `schema_version` fails the major-compatibility rule (§15 of 136C) |
| `reference_failure` | a `$ref` inside a schema file cannot be resolved offline (a registry-construction-time error, §17) |
| `schema_invalid_record` | the generic top-level outcome when a record fails one or more schema constraints — always accompanied by the specific per-error `keyword`/`json_pointer` detail (§18), never returned bare |
| `unknown_field` | a Tier 1 `additionalProperties: false` rejection, or a Tier 2 rejection of a key other than `_extensions` |
| `wrong_enum` | an `enum`-keyword failure |
| `missing_field` | a `required`-keyword failure |
| `conditional_failure` | an `if`/`then` (or `oneOf` tagged-union) branch failure |
| `size_limit` | a Layer 1 or Layer 2 length/size-bound rejection (e.g. an over-length `limitations` entry, §15) |
| `internal_validator_error` | any unexpected exception from within the validation engine itself, wrapped rather than propagated raw — surfaced distinctly so a caller can tell "your data was invalid" apart from "our validator broke" |

**Kept distinct from future (not implemented here) error classes:**
`digest_mismatch`, `identity_mismatch`, `stale_authorization`,
`cas_rejected`, `authority_conflict` — these are all Layer 3–6 outcomes
(136C §1's exclusion list, §22 handoff table below); this plan's Layer 2
reason-code set contains none of them, and the planned
`ShapeValidationResult` (§18) has no field capable of asserting any of
them, structurally preventing a future implementer from accidentally
returning a digest-mismatch verdict out of a function whose entire job is
shape validation.

---

## 20. Format-checking plan

| Candidate `format` | Planned disposition |
|---|---|
| `date-time` | **Explicit `pattern`, not bare `format`** — used as `description`-only annotation (136C §13's own "advisory only" framing) while the actual assertion is the anchored regex (§10 of this plan). This avoids depending on validator-specific `format`-assertion opt-in behavior (Draft 2020-12 makes `format` annotation-only by default per-spec) for a shape-critical field. |
| URI/URN | **Not used as `format: uri`.** Every identifier-shaped field in this package (`record_id`, `migration_epoch`, `phase_id`, `transition_id`, `principal_identifier`, the `$id` values themselves) has its own explicit, narrower `pattern` (§10 of 136C) — a generic URI-format check would be both looser (accepting shapes this contract does not want) and would not itself forbid traversal/absolute-path hazards the way the dedicated `pattern`s do. |
| UUID | **Not used anywhere** — this contract's identifiers are deterministic, content-derived, family-prefixed strings (136C §10), never raw UUIDs (explicitly: `transition_id` is "deterministic digest-derived, never a raw UUID," restating `CLTR-CUTOVER-001` §7). |
| email | **Not used** — `principal_identifier`'s pattern (`[A-Za-z0-9._@-]`) *permits* an email-*shaped* string as one valid form (since operator identities are sometimes email-shaped) but does not assert `format: email`, since 135Z §8.3 explicitly treats principal-identity verification as out of this contract's scope; asserting `format: email` would falsely imply a validation guarantee (that the value is a deliverable email address) this layer does not and cannot provide. |
| hostname | **Not used** — no field in this package represents a hostname. |
| custom digest format | **Explicit `pattern`** (`^[0-9a-f]{64}$`, §10 of this plan / 136C §11) — not a `format` keyword at all, since JSON Schema has no built-in `format` value for this shape; a `pattern` is the only correct mechanism. |
| custom identifier formats | **Explicit `pattern`** per identifier family (§10 of 136C), same reasoning as digest. |

**Optional versus asserted format behavior, planned:** this package uses
**zero** `format`-keyword assertions in "assertion mode" anywhere — every
shape-critical constraint is expressed as an explicit `pattern` instead,
consistent with 136C §2's own rule ("this package **must not** rely on
`format` alone for structural rejection — every shape-critical field ...
**must** also carry an explicit `pattern` regex"). Where a `format`
keyword does appear (`date-time`, purely for documentation/tooling
annotation value, e.g. IDE hinting), it is understood by every
implementer and every test to be non-authoritative — the accompanying
`pattern` is what a test actually asserts against.

---

## 21. Canonicalization integration plan

No integration code is written in 136E. The planned future integration
sequence, reusing `pcae.cltr.canonicalization`/`pcae.cltr.digest`
unchanged (never reimplemented — 136B §14/§15, 136C §39, independently
reconfirmed unmodified by 136D):

1. **Strict parsing** (§5, Layer 1) — duplicate-key rejection, UTF-8
   decode, size/depth bounds.
2. **Schema validation** (§18, Layer 2) — `validate_record_shape()`
   against the appropriate `schema_id`/`schema_version`.
3. **Canonicalization** (Layer 3, existing code, unchanged) — performed
   **only after** step 2 succeeds; a schema-invalid document is never
   passed into `pcae.cltr.canonicalization`, since canonicalizing a
   structurally-wrong document is meaningless work and could mask a
   Layer 2 rejection behind a confusing Layer 3 error.
4. **Digest verification** (Layer 3, existing `pcae.cltr.digest`,
   unchanged) — performed after canonicalization, comparing the
   record's own claimed `record_digest`/`digest` field against the
   freshly recomputed digest over the canonical form.
5. **Separation of error classes:** a canonicalization/digest failure at
   step 3–4 is planned to surface as a Layer 3 error, structurally
   distinct from every Layer 1/Layer 2 reason code in §19 — never
   reported as `schema_invalid_record` even though both are, loosely,
   "this document is wrong" outcomes, since a caller needs to know
   whether the fix is "reshape your JSON" (Layer 2) or "your digest
   doesn't match your content" (Layer 3), two very different remediation
   paths.
6. **Reuse, no reimplementation:** no new canonicalization or digest
   function is planned anywhere in the Stage 3 companion-schema codebase
   — every reference to "canonicalize" or "digest" in this plan means
   calling the existing `pcae.cltr.canonicalization`/`pcae.cltr.digest`
   functions, unchanged, exactly as 136B §43 and 136C §39 already commit
   to.

---

## 22. Semantic-validation handoff plan

Mapping every one of the 62 `CSCH-EXEC-REQ` requirements (136C §51, as
repaired by 136D) to its owning layer. Rather than restate all 62 rows
individually (they are already published verbatim in 136C §51 and
independently re-verified complete by 136D §6), this plan gives the
**layer-ownership pattern** every requirement falls into, with
representative examples, and confirms **no requirement is unowned**:

| Layer | Owns | Representative `CSCH-EXEC-REQ` examples | Implemented by |
|---|---|---|---|
| Layer 1 (parsing) | duplicate-key rejection, UTF-8, top-level object shape | requirements underlying the "Layer 1 (JSON parsing ...) rejects duplicate object keys before ... Layer 2" row of 136C §2 | §5 (this plan); a future strict-parsing module |
| Layer 2 (schema validation, this package's entire scope) | field presence/type/pattern/enum, envelope composition, unknown-field closure, local `if`/`then` conditionals, embedded-component completeness | the great majority of the 62 requirements — every per-family field-table requirement (§17–§34 of 136C), the two-tier `additionalProperties` policy requirements, all 9 `if`/`then` rows | Groups 1–6 (§13), this plan's schema-authoring scope for a *future* phase |
| Layer 3 (canonicalization/digest) | key sorting, NFC normalization, compact serialization, digest recomputation | requirements whose 136C text explicitly says "Layer 3 responsibility" (digest recomputation, canonical byte layout, deterministic array ordering) | existing `pcae.cltr.canonicalization`/`digest.py`, reused unchanged (§21) |
| Layer 4 (semantic/cross-record validation) | identity recomputation, cross-record invariant checks (`CSCH-INV-1`..`15` in full cross-document form), authorization freshness, certification staleness, CAS-expectation-vs-live-state comparison, authority-state/generation binding, quarantine exclusion, marker/receipt generation consistency, compatibility non-authority enforcement, historical non-current checks | 136C §40's explicit ten-item list | a future semantic-validator phase, far beyond this plan's scope |
| Layer 5 (live-state/CAS) | compare-and-swap against actual filesystem/pointer state, publication success | requirements 136C §1 explicitly excludes from Layer 2's own claims | a future publication-implementation phase |
| Layer 6 (authority resolution) | current-authority determination, resolver logic | requirements 136C §1 explicitly excludes | a future authority-resolver phase (post-dates even semantic validation) |

**No requirement becomes unowned:** every one of the 62 rows in 136C
§51's matrix carries its own "Source §" and (where applicable) "Semantic
dependency" column identifying which layer closes it; 136D §1.3
independently re-checked every row's semantic-dependency column for
plausibility and found none in error. This plan does not re-litigate that
already-independently-verified mapping; it restates the layer-ownership
*pattern* so a future semantic-validator architecture phase can start
from a clear "what Layer 2 already covers, what remains" boundary without
re-deriving it from the raw 62-row matrix each time.

---

## 23. Test implementation plan

Planned test modules (paths illustrative, e.g.
`tests/test_phase_136h_cltr_cutover_schema_group1.py` per group, matching
this repository's existing `test_{phase_id}_{description}` convention),
covering:

- meta-schema validity (every schema file validates against the Draft
  2020-12 meta-schema itself);
- package completeness (manifest-vs-filesystem cross-check, §16);
- exact schema inventory (24-file count, 16+7+1 split, §7);
- unique `$id` (no two files share an `$id`, §8/§17);
- offline references (every `$ref` resolves without a retrieval
  function configured, §4/§9);
- no remote fetch (a configured-with-no-retrieval-function `Registry`
  raises rather than fetching, §4);
- manifest integrity (`file_digest` matches actual file bytes, §16);
- valid fixtures (every `valid/` fixture passes, per family, §14);
- invalid fixtures (every `invalid/` fixture fails, with the *expected*
  reason code/keyword asserted, not merely "it failed," per family,
  §14/§19);
- nested unknown properties (§12's addition — an unknown key nested
  inside an embedded object is rejected, not just top-level unknown
  keys);
- branch exclusivity (a `oneOf` tagged-union fixture satisfying more than
  one branch simultaneously is rejected — proving the discriminator
  `const` actually excludes the wrong branch, not merely that the right
  branch is accepted);
- enums (§11's five-category test plan, all 21 enums);
- versions (major/minor compatibility rule, §15 of 136C);
- IDs (§10 pattern tests, all five identifier families);
- digests (§11/§10 pattern tests);
- timestamps (§13/§10 pattern tests);
- free-text bounds (§15's length/newline/control-character/Unicode
  tests, per classified field);
- secrets (§14's secret-containing-invalid-example fixtures);
- traversal (§14's traversal-string fixtures for the three
  `storage_locator`-bearing binding families);
- size limits (§5/§27's input-byte and nesting-depth rejections);
- deterministic registry (§17 — two independently constructed registry
  instances over the same file tree produce identical load order and
  identical error messages on an injected duplicate/broken-reference
  fixture set);
- validation API (§18 — `ShapeValidationResult` shape, JSON-pointer
  correctness, no-raise-on-ordinary-invalid-input behavior);
- no mutation (every test above asserts the working tree is unchanged
  after the test runs — no schema file, fixture, or registry call writes
  anything);
- no subprocess/network/backend behavior (existing repository convention
  — no test in this suite spawns a subprocess or touches the network;
  confirmed as a planned constraint on this suite's own authoring, not
  merely inherited by accident).

**Test-tier placement, planned:** the majority of this suite is planned
for the existing `fast_green` marker (fast, deterministic,
governance/core-relevant per this repository's own tier definition,
`pyproject.toml`'s `[tool.pytest.ini_options]` markers section); no test
in this suite is expected to need `slow`/`integration`/`phase_closure`
markers, since none of it spawns a subprocess or exercises the CLI
end-to-end — it is pure library-level schema/fixture validation.

---

## 24. Independent verification strategy

Every one of the six implementation groups (§13) receives its own,
freshly-scoped independent-verification phase before the next group
begins (§33's roadmap), following this repository's own established
independent-verification discipline (135X, 136A, 136D all modeled the
same rigor this plan schedules forward):

- **Re-derive requirements:** each verification phase independently
  re-extracts the subset of the 62-item `CSCH-EXEC-REQ` matrix (136C §51)
  that its own group claims to satisfy, rather than accepting the
  implementation phase's own self-reported completion.
- **Create adversarial fixtures:** beyond the implementation phase's own
  fixture set (§14), each verification phase authors its own,
  independently-constructed adversarial fixtures targeting the same
  attack classes 136D's own methodology used (missing-value wildcards,
  enum aliasing, unknown-field smuggling, cross-family reference
  substitution).
- **Test unknown-field composition:** specifically re-tests the `allOf`+
  no-`unevaluatedProperties` closure (§12) with fixtures the
  implementation phase did not itself author.
- **Inspect reference graph:** independently re-walks every `$ref` in the
  group's own files (not trusting the manifest's own `dependencies`
  column at face value) to confirm no cycle and no unresolved target.
- **Test dependency absence/failure:** for Group 1 specifically (and
  spot-checked for later groups), a test that temporarily removes/
  uninstalls `jsonschema` (or simulates its absence via import mocking)
  and confirms the package fails closed with a clear error rather than a
  confusing traceback or, worse, a silent partial-validation fallback.
- **Test offline behavior:** re-runs the no-network test (§4) against the
  group's own actual schema files, not just the dependency-introduction
  phase's synthetic smoke-test schemas.
- **Test schema substitution:** a fixture that is valid against one
  family's schema but is submitted with a different family's `schema_id`
  — must be rejected (proving `record_type`'s `const` restriction, §7.1
  of 136C, actually prevents cross-family substitution at the API layer,
  §18).
- **Test manifest tampering:** a fixture manifest with a deliberately
  wrong `file_digest` for one entry — the registry (§17) must refuse to
  load, not silently proceed.
- **Test family-ID mismatch:** a `record_reference` whose `record_family`
  does not match the actual family of the digest/ID it names (a
  synthetic, deliberately-mismatched fixture) — confirms the structural,
  Layer-2-visible half of this defense (136B §7's "record_family... field
  is checked for existence, not yet for live-content correctness")
  behaves exactly as documented, no more and no less.
- **Test semantic-boundary honesty:** for every family, confirm no
  schema-level field or `const` value could be mistaken for a Layer 4+
  claim (e.g. that `authority_role: authoritative` being schema-
  expressible on `authority_state`/`publication_evidence` never implies
  the schema itself confirms current authority — re-testing 136D §19's
  own "documentation-only assertion... cannot itself enforce across
  documents" finding against the actual implemented schema text, not
  just the contract prose).
- **Use isolated baselines:** each verification phase is instructed,
  consistent with prior 135X/136A/136D practice, to re-derive its
  conclusions from the primary contract texts (135W, 135Z, 136C as
  repaired by 136D) and from direct inspection of the actual committed
  schema/fixture/code, not from the immediately-prior phase's own
  narrative summary of itself.
- **Classify findings:** using the same five-way classification this plan
  and its predecessors use (`CONFIRMED`/`NON-BLOCKING`/`BLOCKING`/
  `PREREQUISITE`/`DEFERRED`), with any `BLOCKING` finding repaired,
  documentation-and-schema-content-only (never silently reinterpreted),
  before that group is considered closed.

---

## 25. Packaging plan

- **Editable installs:** `schemas/cltr_cutover/**` must be reachable from
  an editable install (`pip install -e .`) the same way
  `schemas/repository_intelligence/**` already is today — since both live
  at the repository root, not inside `src/pcae/`, an editable install's
  `sys.path` insertion of `src/` does **not** automatically make
  `schemas/` importable/locatable; this plan confirms (by inspecting how
  the three existing `repository_intelligence`-consuming tests actually
  locate their schema files) that the existing pattern is a
  repository-root-relative path lookup (e.g. via a `Path(__file__).parents[...]`
  walk from the test file, or a fixed repository-root-detection helper),
  **not** a Python-package-resource lookup — the future Stage 3
  registry (§17) is planned to follow this exact same repository-root-
  relative convention for consistency, rather than inventing a second
  schema-location strategy.
- **Wheels:** `pyproject.toml`'s current `[tool.hatch.build.targets.wheel]`
  scopes the wheel to `packages = ["src/pcae"]` only — `schemas/` is
  **not** currently included in a built wheel. This is a real,
  independently-identified packaging gap this plan surfaces (not present
  in any prior contract phase's own text): if a *deployed* (non-editable,
  non-repository-checkout) install of `pcae-harness` ever needs to load
  `schemas/cltr_cutover/**` at runtime (e.g. for a future `pcae cltr
  schema validate` CLI, §26, if ever built), the wheel would not carry
  the schema files today. This plan schedules the dependency-introduction
  or Group-1 implementation phase to **decide and record**, not silently
  assume, whether `schemas/` needs to be added to
  `[tool.hatch.build.targets.wheel].packages` (e.g. via Hatch's
  `force-include` mechanism to place `schemas/cltr_cutover` under
  `src/pcae/schemas/cltr_cutover` in the built wheel, or an equivalent
  package-data mechanism) — this plan does not resolve the question
  itself, since resolving it means touching `pyproject.toml`, which is
  outside 136E's `Allowed Files` scope, but it is recorded here as a
  **required decision point** for the dependency-introduction phase (§4)
  rather than left implicit.
- **Source distributions:** the current sdist include list
  (`src/pcae`, `README.md`, `LICENSE`, `pyproject.toml`) **also does not
  include `schemas/`** — the same gap as above applies to sdists.
- **Runtime package lookup:** pending the wheel/sdist decision above, this
  plan's default recommendation (not a binding decision, since it touches
  `pyproject.toml`) is repository-root-relative lookup for
  development/editable/test contexts (matching existing precedent) plus
  an explicit `force-include`/package-data inclusion for wheel/sdist
  contexts if and when this package is ever expected to run from a
  non-editable, non-checkout install — deferred to the dependency-
  introduction phase to decide with full context on how urgently a
  packaged (non-editable) distribution path is actually needed.
- **Tests:** `tests/` already has `pythonpath = ["src"]` configured; test
  fixtures under `tests/fixtures/cltr_cutover/**` are planned to be
  ordinary repository files, located the same way `schemas/
  repository_intelligence/**`'s existing consumer tests locate their own
  fixtures — no change to `pyproject.toml`'s `testpaths`/`pythonpath`
  needed for tests to see the new fixture tree.
- **Repository checkouts:** unaffected — every file this plan schedules
  is an ordinary, version-controlled repository file, visible in any
  checkout regardless of the wheel/sdist packaging question above.

**Planned tests ensuring installed-package availability:** a future test
(scheduled alongside whichever implementation group first needs
non-editable-install schema access, likely no earlier than Group 1) that
builds a wheel (`python -m build` or `hatch build`), installs it into a
throwaway virtual environment, and confirms `schemas/cltr_cutover/**` is
actually present and loadable from that installed package — proving the
wheel-inclusion decision above was correctly implemented, not merely
declared. **No packaging change is made in 136E.**

---

## 26. Supported-environment plan

- **Supported Python versions:** `>=3.9` (this repository's existing
  `requires-python`, unchanged by this plan) — the selected validation
  engine (`jsonschema`, §3) is compatible with this floor as of this
  plan's writing; the dependency-introduction phase (§4) must re-confirm
  against the exact pinned version at that time.
- **macOS:** no macOS-specific behavior is introduced by this plan — pure
  Python + a small Rust-extension transitive dependency (`rpds-py`) with
  published macOS wheels for both Intel and Apple Silicon; no
  macOS-specific test skip is anticipated.
- **Linux:** same reasoning; `rpds-py` publishes manylinux wheels.
- **Offline operation:** the entire schema-validation subsystem this plan
  describes (Groups 1–6, the registry, the validation API) is designed to
  require zero network access at any point — proven, not merely asserted,
  by the no-network tests scheduled in §4/§23/§24.
- **Unsupported network filesystems:** not a distinguishing concern for
  this subsystem — it reads only small, local, version-controlled JSON
  files; no large-file or network-filesystem-specific behavior is
  planned.
- **Locale independence:** every `pattern` in this package is ASCII-
  anchored (§10 of 136C) and every digest/timestamp/identifier comparison
  is a plain byte/codepoint comparison, never a locale-aware string
  comparison or locale-aware number/date parsing — no test is expected to
  behave differently under a non-`C`/non-`en_US` locale, and this plan
  schedules at least one test explicitly run under a non-default locale
  (e.g. `LC_ALL=de_DE.UTF-8` or a CI-available equivalent) to confirm this
  claim rather than merely assert it.
- **Path independence:** the planned registry (§17) computes paths
  relative to a detected repository root (or an explicitly passed base
  path), never a hard-coded absolute path — consistent with this
  repository's existing conventions for locating `schemas/
  repository_intelligence/**`.
- **Deterministic output:** every planned test (§23) and the registry's
  own load order (§17) are deterministic by construction (sorted
  traversal, content-addressed digesting, no wall-clock or randomness in
  any planned code path).
- **CI and local verification:** this plan schedules the new test suite
  to run under this repository's existing `fast_green`/`quick`/
  `governance`/`full` pytest-marker tiers (§23) with no new CI
  configuration required beyond what already runs `pytest -m fast_green`
  (or equivalent) today — no new CI job type is planned.

---

## 27. Performance and limits plan

| Limit | Planned value | Rationale |
|---|---|---|
| Input bytes (per document) | 1 MiB | Generous relative to any single companion record's actual field list (flat-ish objects of scalar/reference fields, no bulk-data field); bounds worst-case parse/validate time and memory for a corrupted or adversarial input before any other check runs |
| Nesting depth | 32 levels | Generous relative to this contract's actual deepest nesting (envelope → embedded `cas_expectation`/conditional object → scalar fields, a handful of levels); closes the resource-exhaustion vector §5 identifies |
| List length (per array field, e.g. `limitations`, `evidence_references`, `entry_point_evidence`) | `limitations`: 32 entries (§15); reference-array fields (`evidence_references`, `actors`, `requests`): 256 entries, generous relative to any realistic evidence/actor/request set for a single cutover attempt | Bounds worst-case validation and downstream canonicalization/digest-computation time |
| Evidence-reference counts | covered by the list-length limit above (`evidence_references`, `verifier_evidence`) | same rationale |
| Free-text lengths | per §15's per-field table (500–4,000 characters depending on field) | resolves the 136D non-blocking unbounded-free-text finding |
| Validation time | no hard per-call timeout is planned at the schema-validation layer itself (a Draft-2020-12 validation of a document this small, against a schema this size, is expected to complete in low-single-digit milliseconds on ordinary hardware — not a resource concern at this scale); a soft advisory ceiling (log a warning if any single `validate_record_shape()` call exceeds, e.g., 100ms) is planned as a diagnostic aid, not a hard limit, since imposing a hard timeout on a CPU-bound, non-network validation call risks false-positive failures on a loaded CI runner |
| Schema-cache size | bounded implicitly — the registry (§17) loads a fixed, small (24-file) schema set once per process; no unbounded cache growth is possible, since the set of loadable schemas is closed and version-controlled, not dynamically discovered from untrusted input |

**No premature optimization:** this plan does not schedule caching
layers, lazy-loading strategies, or performance-tuning work beyond the
limits above — the entire schema set is small (24 files, none large) and
the validation workload (validating individual, small JSON documents) is
not expected to be a performance bottleneck at any realistic Stage 3
record-creation rate; the limits above exist to bound *adversarial/
malformed* input cost, not to optimize the *ordinary* case, which needs
no optimization.

---

## 28. Security plan

| Threat | Planned defense | Owning layer |
|---|---|---|
| Remote `$ref` | `Registry` constructed with no retrieval function, ever (§4, §9, §17) — structurally impossible, not merely forbidden by convention | Layer 2 (registry construction) |
| Schema poisoning (a malicious/corrupted schema file substituted for a real one) | manifest `file_digest` verification at registry-load time (§16, §17) — any schema file whose bytes don't match its manifest entry is rejected before it can validate anything | Layer 2 (registry) |
| Registry substitution (a caller pointed at a different, attacker-controlled schema tree) | the registry's base path is planned to be explicitly passed or repository-root-detected via a trusted, code-reviewed mechanism, never taken from an untrusted runtime input (e.g. never from an environment variable an untrusted process could set, consistent with 135W/135Y's existing "no environment-variable authorization" precedent extended here to schema-tree selection) | Layer 2 (registry construction) |
| Manifest substitution | the manifest itself is an ordinary version-controlled repository file, subject to the same code-review process as every other file in this plan's inventory — no runtime mechanism is planned to load an alternate, unreviewed manifest | Layer 2 (registry) |
| Oversized inputs | §27's input-byte limit, enforced pre-parse (§5) | Layer 1 |
| Catastrophic regex | every `pattern` in this package is planned to be a simple, anchored, non-backtracking-prone character-class regex (no nested quantifiers, no alternation-heavy lookahead — none of this contract's identifier/digest/timestamp patterns require anything beyond fixed-length or simple-repetition character classes); this plan schedules an explicit ReDoS review (each `pattern` checked against a standard catastrophic-backtracking test corpus) as part of Group 1's own independent verification (§24), not deferred | Layer 2 (schema authoring) |
| Traversal IDs | `pattern` forbids `..` and leading `/` on every identifier/locator field (§10, §12 of 136C) | Layer 2 |
| Locator escape | `storage_locator` restricted to exactly 3 binding families, namespace-relative pattern only (§12 of 136C) | Layer 2 |
| Secret persistence | no field in this package is typed to hold a reusable credential; `replay_binding`/`proof_reference` are opaque references only (§10, §14's secret-fixture category) | Layer 2 (schema authoring) + documentation/convention (136D §23's honest disclosure that shape alone cannot always detect an embedded secret) |
| Error-message secret leakage | §19's error model caps message length and is planned to never echo full field *values* into an error message — only the JSON Pointer *location* and the failing *keyword*, never the offending value itself, specifically to avoid a validation-error log accidentally persisting a secret-shaped value that was rejected | Layer 2 (validation API, §18) |
| Version downgrade | major-version-mismatch rejection (§15 of 136C, §8 of this plan); no silent coercion | Layer 2 |
| Unknown-field smuggling | two-tier `additionalProperties` policy (§12, §14) | Layer 2 |

**Independent security verification is scheduled before typed models
consume these schemas** — per §35's typed-model eligibility gate, no
typed-model implementation phase may begin until every group above has
passed its own independent verification (§24), which includes the
security-focused adversarial fixtures listed in this section and §24.

---

## 29. No-authority proof plan

Planned tests proving, for every one of the 16 standalone schemas:

- schema validation does not resolve authority — no planned code path in
  `validate_record_shape()` (§18) reads any file under
  `.pcae/cltr-authority/**`; a test asserts this by running validation in
  a temporary directory with no such namespace present at all and
  confirming no error occurs (proving no implicit dependency exists);
- schema validity does not authorize cutover — a test that constructs a
  fully schema-valid `Certification`/`PublicationAttempt` fixture and
  confirms no planned function call, anywhere in this plan's API surface,
  has any side effect beyond returning a `ShapeValidationResult`;
- no current-authority pointer is read — same reasoning as the first
  bullet, specifically re-tested against the pointer path convention
  (`current-authority-state`, 135Z §37/§38.2) to confirm no planned code
  path ever opens that specific file;
- no authority namespace is created — a test confirms
  `.pcae/cltr-authority/` does not exist after running the full planned
  test suite in a clean temporary directory;
- no production artifact is mutated — a test snapshot of
  `.pcae/finalization-transactions/`, `.pcae/phase-reports/`, and the
  legacy lifecycle's own state directories, taken before and after
  running the full planned schema/fixture/registry test suite, must be
  byte-identical;
- no notification is dispatched — no planned code path imports or calls
  anything from `pcae.core.phase_reports`' notification dispatch
  functions or PFN-001's `certify_notification_transition()`;
- no marker or receipt is created — same reasoning, re-tested against the
  specific marker/receipt file paths;
- no authority epoch changes — `ProductionAuthority.LEGACY` (`src/pcae/
  cltr/migration/enums.py`) is re-read before and after the full planned
  test suite and confirmed unchanged;
- no runtime state changes — `pcae runtime inspect`'s own reported state
  (`Observed`/`observe`/`unavailable`) is re-confirmed unchanged before
  and after running the full planned test suite as part of that suite's
  own setup/teardown.

---

## 30. CLI plan

**Disposition: deferred. No CLI is added merely for convenience; library
tests are sufficient initially.**

A possible future command, `pcae cltr schema validate --schema-id <ID>
<FILE>`, is named here as the shape a future CLI would take **if** one is
ever added — read-only and offline by construction (it would only ever
call `validate_record_shape()`, §18, never a write path).

**Why deferred:** at the point this plan is written, there is no
production consumer of Stage 3 companion schemas at all (Stage 3 is
unimplemented; no cutover request, readiness package, or any other
companion record is ever created by any current code path) — a CLI
command exists to serve an operator or another program's *interactive or
scripted* need, and no such need exists yet. Every planned consumer of
`validate_record_shape()` in the scope this plan covers (Groups 1–6's own
tests, a future semantic-validator phase) is planned to call the Python
API directly, not shell out to a CLI. Adding a CLI command now would be
speculative surface area with no current caller, contrary to this
repository's own stated preference (echoed throughout the 135/136 phase
chain) against building mechanism ahead of demonstrated need. **No CLI
implementation in 136E.** If a genuine operator-facing need for ad hoc
schema validation emerges once Stage 3 implementation is further along,
that need is expected to motivate its own small, focused future phase.

---

## 31. Documentation plan

Planned future documentation, generated where possible rather than
manually duplicated:

- **Schema catalog:** a generated table (schema_id, family, version,
  implementation group) derivable directly from the manifest (§16) —
  planned to avoid a second, hand-maintained catalog that could drift
  from the manifest.
- **Field descriptions:** already required to live in each schema file's
  own `description` keywords (per this plan's own conventions throughout,
  e.g. §7.4's absent-vs-null classification requirement) — the
  documentation catalog is planned to be generated by walking each
  schema's own `description` fields, not hand-copied into a separate
  document.
- **Enum catalog:** generated from `shared/enums.schema.json` and each
  family's own local enum `$defs` (§11) — again avoiding a second,
  driftable hand-maintained list.
- **Reference graph:** generated from the manifest's own `dependencies`
  column (§16) plus the `record_reference` cross-family table (§9.2 of
  this plan, which itself restates 136B §13's cross-reference table) —
  a future documentation-generation step is planned to render this as a
  diagram or table directly from data, not hand-maintain a second copy.
- **Fixture catalog:** generated by walking `tests/fixtures/cltr_cutover/
  **` and cross-referencing against the manifest — proving fixture
  completeness (§14) is also a documentation artifact, not just a test
  assertion.
- **Validation-layer disclosure:** the Layer 1–6 boundary (§1 of 136C,
  §22 of this plan) is planned to remain a hand-maintained narrative
  document (this kind of cross-cutting architectural explanation is not
  mechanically derivable from schema files themselves) — the one
  documentation category this plan does **not** schedule for generation.
- **Compatibility matrix:** the major/minor versioning rule (§15 of 136C)
  applied across actual schema-file version history — planned as
  generated once real version history exists (i.e., not meaningful before
  any schema has ever been revised), so scheduled as a later-phase
  concern, not part of the initial Group 1–6 implementation.
- **Error catalog:** generated directly from §19's closed reason-code
  enumeration (a Python `Enum` or equivalent, once implemented) — the
  documentation is planned to be derived from the same single
  source-of-truth enum the validation API (§18) itself uses, avoiding a
  third, independently-drifting copy of the same list.

**Duplicate manually maintained sources are avoided** throughout: every
catalog above is planned to be generated from a single authoritative
source (the manifest, the schema files' own `description` fields, or the
error-reason-code enum) rather than hand-copied prose that could silently
diverge from the actual schema content.

---

## 32. Implementation commit strategy

Planned bounded commits per implementation group (illustrative; each
future implementation phase's own governed-phase commit sequence is
determined by that phase, not fixed in advance by this plan beyond the
following shape):

1. **Dependency/tooling prerequisite** (§4's own phase) — one commit
   adding the dependency + smoke/offline/no-network tests, one commit
   finalizing that phase's canonical report.
2. **Shared definitions and manifest** (Group 1) — one commit per shared
   `$defs` file family (or one combined commit for all 7, decided by the
   implementing phase based on reviewability), one commit for the
   manifest + `README.md`, one commit for Group 1's own fixtures/tests,
   one commit finalizing the phase's canonical report.
3. **Record-group schemas and fixtures** (Groups 2–6, each its own
   governed phase pair — implementation + independent verification, per
   §33's roadmap) — each implementation phase follows the same shape:
   one commit per schema file or small cluster of related schema files,
   one commit for that group's fixtures, one commit for that group's
   tests, one commit finalizing the phase's canonical report.
4. **Registry/shape-validation code** (a later phase, after Groups 1–6
   are complete and independently verified, §17/§18) — one commit for the
   registry module, one commit for the validation API module, one commit
   for their own dedicated tests, one commit finalizing the phase's
   canonical report.
5. **Tests and documentation** — largely folded into each group's own
   phase above rather than deferred to one giant end-of-sequence phase;
   any remaining cross-cutting documentation (§31's generated catalogs)
   is its own small, later phase.
6. **Governed completion** — every phase in this sequence ends with its
   own canonical phase-completion report and metadata, per this
   repository's existing PFR-001-governed lifecycle, exactly as 136A
   through 136E themselves have.

**No exact commit count is mandated** — bounded phases are already
separated at the group level (§13, §33), which is the load-bearing
boundary; how many commits a single governed phase uses internally is
left to that phase's own judgment, consistent with this plan's
instruction not to over-specify what a future phase can reasonably decide
for itself. **Explicit phase ownership remains required**: every commit
in every future phase must be attributable to exactly one named governed
phase (matching this repository's existing `git log` convention of
prefixing every commit message with `Phase <ID>: ...`).

---

## 33. Exact phase roadmap

Derived from this plan's own dependency analysis (§4's separate-
prerequisite-phase decision, §13's six implementation groups each needing
their own independent verification, §17/§18's registry/API work needing
all six groups complete first):

```
136E — Stage 3 Companion Executable Schema Implementation Plan (this phase)
136F — Draft 2020-12 Validation Engine and Strict JSON Parsing Prerequisite
136G — Validation Engine and Parsing Independent Verification
136H — Companion Executable Schema Group 1 (Core Profiles and Shared Definitions) Implementation
136I — Group 1 Independent Verification
136J — Companion Executable Schema Group 2 (Authority Core) Implementation
136K — Group 2 Independent Verification
136L — Companion Executable Schema Group 3 (Request and Readiness) Implementation
136M — Group 3 Independent Verification
136N — Companion Executable Schema Group 4 (Authorization and Candidate) Implementation
136O — Group 4 Independent Verification
136P — Companion Executable Schema Group 5 (CAS, Publication, Recovery, Quarantine) Implementation
136Q — Group 5 Independent Verification
136R — Companion Executable Schema Group 6 (Terminal Bindings and Compatibility) Implementation
136S — Group 6 Independent Verification — Final Schema Package Complete
136T — Schema Registry and Shape Validation API Implementation
136U — Schema Registry and Shape Validation API Independent Verification
```

Beyond 136U, this plan explicitly does **not** name further phases (a
future semantic-validator architecture phase, a future typed-model
architecture phase, a future packaging-decision phase per §25) — naming
them now would exceed this plan's own planning-only scope into planning
work that itself depends on 136U's own, not-yet-existing, outcome.

**Phase-proliferation avoided:** six implementation groups, not sixteen
(one per schema file) — grouping by dependency/blast-radius (§13) keeps
each implementation phase reviewable as a bounded unit while avoiding
sixteen separate implementation-plus-verification phase pairs for what
is, in several cases (e.g. Group 1's seven shared files), a tightly
coupled unit that must be reviewed together to make sense at all.
**Unverified authority-relevant groups are never combined**: Groups 2–5,
each touching an authority-adjacent family (`AuthorityEpoch`/
`AuthorityState`, `CutoverRequest`/`ReadinessEvidencePackage`,
`HumanAuthorization`/`CutoverCandidate`/`Certification`,
`PublicationAttempt`/`PublicationEvidence`/`ConcurrencyConflict`/
`RecoveryJournalEntry`/`QuarantineRecord`), each get their own dedicated
implementation-then-verification phase pair, never bundled with another
group's own unverified content.

---

## 34. Dependency graph

```
136F (validation engine + strict parser)
    │
    ▼
136G (independent verification of 136F)
    │
    ▼
136H (Group 1: shared defs + manifest)
    │
    ▼
136I (independent verification of Group 1)
    │
    ├──────────────┬──────────────┐
    ▼              ▼              ▼
136J (Group 2)  136L (Group 3, authored sequentially after
    │               Group 2 per §13's own choice, though the
    ▼               $ref graph would technically allow parallel
136K (verify        authoring — this plan schedules sequential
  Group 2)           anyway, per its own no-parallel-unverified-
    │                authority-work preference)
    ▼
136L → 136M → 136N → 136O → 136P → 136Q → 136R → 136S
  (Groups 3, 4, 5, 6 and their own verifications, in sequence)
    │
    ▼
136S (Group 6 verified — full 16-schema package complete and verified)
    │
    ▼
136T (registry + shape-validation API implementation)
    │
    ▼
136U (registry + API independent verification)
    │
    ▼
Semantic-validator architecture phase (not named by this plan, §33)
    │
    ▼
Typed-model architecture phase (not named by this plan; gated per §35)
```

**No typed-model phase may depend on unverified schemas** — the diagram's
own structure enforces this: every arrow into a typed-model phase (were
one drawn) would have to originate at or after 136U, never at an
unverified intermediate group.

---

## 35. Typed-model eligibility

The gate for beginning typed runtime model architecture, restated as a
binding planning constraint (not merely descriptive):

- all 16 standalone executable schemas implemented (Groups 1–6, 136H
  through 136S complete);
- registry implemented (136T);
- shape validation implemented (136T);
- independent schema-package verification complete for every group
  (136I, 136K, 136M, 136O, 136Q, 136S) **and** for the registry/API
  (136U);
- no unresolved Blocking schema findings outstanding at the time typed-
  model work is proposed (any Blocking finding raised during 136F–136U
  must be repaired and re-verified before this gate is considered met);
- canonicalization handoff frozen (§21 — already frozen by this plan,
  reusing existing `pcae.cltr.canonicalization`/`digest.py` unchanged;
  this condition is about confirming no drift occurred during 136F–136U,
  not about producing new canonicalization work);
- semantic-validator boundary confirmed (§22's handoff table, and its
  own future semantic-validator architecture phase's own independent
  confirmation that Layer 2's actual implemented behavior matches this
  plan's Layer 2/Layer 4 boundary).

**Exception, narrowly scoped:** shared enum code (the Python `Enum`
classes mirroring §11's 7 shared + 14 local wire-value enums) **may** be
considered for earlier implementation than the full gate above **only
if** it cannot create divergent wire values — i.e., only if the Python
enum's own values are generated from, or mechanically cross-checked
against, the same `shared/enums.schema.json`/family-local-enum `$defs`
this plan's Groups 1–6 will freeze, so that no second, independently-
typed hand-copy of the same 21 enum vocabularies can ever drift from the
schema-frozen source of truth. This plan does not schedule this exception
being exercised — it is stated only because the task brief requires
defining it, not because an early enum-implementation phase is currently
planned.

---

## 36. Acceptance criteria

This implementation plan is complete because:

- ✅ validator engine selected (§3.2 — `jsonschema`);
- ✅ version strategy defined (§3.3 — `jsonschema>=4.18,<5`);
- ✅ dependency phase scheduled (§4 — 136F, separate bounded phase);
- ✅ strict parsing planned (§5);
- ✅ exact file inventory listed (§7 — 24 files, full table);
- ✅ `$id` and `$ref` strategy defined (§8, §9);
- ✅ schema groups defined (§13 — six groups, dependency-ordered);
- ✅ fixtures complete (§14 — full category list per family);
- ✅ free-text bounds planned (§15 — full per-field table);
- ✅ manifest decision made (§16 — required, scheduled in Group 1);
- ✅ registry planned (§17);
- ✅ validation API planned (§18);
- ✅ errors planned (§19);
- ✅ packaging planned (§25 — including a newly surfaced wheel/sdist gap
  explicitly flagged as a required decision point for 136F, not silently
  left open);
- ✅ tests planned (§23);
- ✅ security planned (§28);
- ✅ independent verification scheduled (§24, and one phase per group in
  §33's roadmap);
- ✅ typed-model gate defined (§35);
- ✅ no unresolved Blocking planning ambiguity remains (§37 confirms no
  no-go condition is currently true).

---

## 37. No-go criteria

Implementation must **not** begin (i.e., 136F must not proceed) if any of
the following becomes true before it starts — **none of these conditions
is true as of this plan**, each is re-stated here as a gate 136F's own
governed-phase-startup inspection must re-check, not assumed permanently
satisfied by this plan alone:

- no conformant validator is selected — **false**, §3.2 selects
  `jsonschema`;
- dependency policy is unresolved — **false**, §3.3/§4 define the version
  constraint and the bounded-phase approach; if this repository's own
  dependency-acceptance norms have changed materially between this plan
  and 136F's own start, 136F must re-confirm, not assume;
- remote schema resolution remains possible — **false by design**, §4's
  no-network test and §9/§17's registry-construction discipline
  structurally prevent it, pending 136F's own execution actually
  implementing it as planned;
- strict duplicate-key parsing is absent from the plan — **false**, §5;
- schema inventory is incomplete — **false**, §7's 24-file table
  reconciles the full 20-family classification;
- `$id` collisions are possible — **false by design**, §8's registry-
  level uniqueness check, pending actual implementation;
- `$ref` graph has unresolved cycles — **false**, §9 confirms acyclicity,
  independently re-derived from 136D's own confirmation;
- unknown-field behavior is ambiguous — **false**, §12's `allOf`-without-
  `unevaluatedProperties` mechanism is fully specified;
- semantic responsibilities are unowned — **false**, §22's handoff table;
- free-text limits remain unspecified — **false**, §15's full per-field
  table (this plan itself resolves the 136D non-blocking gap, at the
  planning level — actual schema-file `pattern`/`maxLength` enforcement
  remains for 136H+ to implement);
- manifest/registry integrity is unresolved — **false**, §16, §17;
- packaging is unresolved — **partially open, explicitly flagged, not
  silently left ambiguous**: §25 identifies a real wheel/sdist inclusion
  gap and schedules its resolution as a required decision point for 136F,
  rather than either resolving it here (out of scope — would require
  touching `pyproject.toml`) or ignoring it; 136F must not proceed past
  its own packaging-decision step without explicitly recording that
  decision;
- independent verification phases are absent — **false**, §24, §33 (one
  per group, plus registry/API);
- historical lifecycle conflicts are being used as readiness evidence —
  **false**, §0 explicitly disclaims using the 136A/136B historical
  reconciliation discrepancies as any form of Stage 3 or executable-
  schema readiness evidence.

Because every hard no-go condition above currently evaluates **false**,
and the one **partially open** item (packaging) is explicitly scheduled
for resolution as a decision point within the very next phase rather than
silently deferred indefinitely, this plan's own verdict (§39) is
**COMPLETE WITH OPEN PREREQUISITES**, not **NOT COMPLETE**.

---

## 38. Risk register

| Risk | Likelihood | Impact | Prevention | Detection | Mitigation | Owner phase | Latest closure point |
|---|---|---|---|---|---|---|---|
| Validator dependency incompatibility (a future `jsonschema` release drops Python 3.9 support before this repository raises its own floor) | Low | Medium — would block installation on the oldest supported Python version | Pin `<5` (§3.3); re-verify Python-version compatibility explicitly at 136F start, not assumed from this plan | 136F's own compatibility test (§4) | Pin a narrower `jsonschema` version range if needed, or raise this repository's own `requires-python` floor in a separate, deliberate phase | 136F | before 136F's own commit |
| Unsupported Draft 2020-12 features (a schema author reaches for a keyword `jsonschema` doesn't fully support) | Low | Medium — would surface as an unexpected validation failure/pass during Group 1–6 authoring | `jsonschema` is the reference-grade implementation with broad 2020-12 coverage (§3.1); Group 1's own meta-schema self-validity tests (§23) catch this early | any group's own implementation-phase test suite | fall back to an equivalent, better-supported keyword combination for the specific construct affected | whichever group first uses the affected keyword | before that group's independent verification closes |
| Remote reference fetching (an accidental network-shaped `$ref` slips into a schema file) | Low | High — would violate this contract's absolute offline requirement | No retrieval function ever configured (§4, §9, §17) — structural, not conventions-based prevention | §4/§23/§24's dedicated no-network tests | reject the offending `$ref` at registry-construction time (already the planned behavior — "detection" and "mitigation" are effectively the same structural mechanism here) | 136F (mechanism) / every group (content) | Group 1 independent verification (136I), and re-checked every subsequent group |
| Duplicate-key acceptance (a hand-authored fixture or, worse, a future real record silently drops a duplicate key without rejection) | Low | High — would violate 136C §2's Layer 1 guarantee this contract depends on | `object_pairs_hook`-based strict parser (§5), planned and tested before any schema validation is exercised | 136F's own strict-parsing test suite | fix the parsing hook; this is a Layer 1 concern entirely separate from schema content, so no schema-level mitigation is needed | 136F | 136G |
| Registry substitution (§28) | Low | High | trusted, code-reviewed base-path resolution only (§28) | code review + §24's adversarial registry-substitution test | reject any untrusted base-path override mechanism if one is ever proposed | 136T | 136U |
| Schema manifest drift (a schema file edited without updating the manifest's `file_digest`) | Medium (a real risk of ordinary human error during iterative authoring) | Medium — caught before it reaches production use, not a silent hazard | manifest-vs-filesystem completeness/integrity test (§16, §23), planned to run in every group's own test suite from Group 1 onward | any group's own CI run | regenerate the manifest entry and re-verify; this plan schedules the manifest-generation step to be either fully automated (a small script) or clearly documented as a required manual step so drift is caught immediately, not accumulated | every implementation group (136H, 136J, 136L, 136N, 136P, 136R) | each group's own independent verification |
| `$id` collision | Low | Medium — caught at registry-construction time, not silently accepted | §8's registry-level uniqueness check | §17's `DuplicateSchemaIdError`, exercised by §24's adversarial tests | fix the colliding `$id` before that group's phase can close | every implementation group | each group's own independent verification |
| Composition weakening unknown-field rules (an `allOf` misuse reopens a Tier 1 file's closure) | Low | High — would silently weaken this contract's strongest security property | §12's explicit no-`unevaluatedProperties`, single-`additionalProperties`-level design | §23's nested-unknown-field test category, §24's independent re-test | redesign the offending file's `properties`/`allOf` composition to restore single-level closure | every implementation group | each group's own independent verification |
| Overly broad shared definitions (a future convenience `$def` becomes too permissive and silently weakens a family-specific constraint) | Low | Medium | §10's explicit narrow-`$def` discipline, matching 136B §8's own precedent | code review during each group's implementation phase | narrow the offending `$def` or split it into family-specific variants | every implementation group | each group's own independent verification |
| Semantic overclaiming (a schema `description` or a future validation-API caller implies a Layer 4+ guarantee Layer 2 does not provide) | Medium (an easy mistake to make in prose, even when the schema-shape itself is correct) | High — could mislead a future implementer or operator into trusting an unverified property | §1/§22's explicit boundary language, required in every schema file's relevant `description` fields (§18's "no semantic claims" API-design constraint) | §24's semantic-boundary-honesty adversarial check | correct the offending `description`/documentation text; this is a documentation, not schema-shape, fix | every implementation group + documentation phase (§31) | each group's own independent verification |
| Fixture incompleteness (a required fixture category from §14 is skipped for one family) | Medium | Medium | §14's explicit per-family category checklist; §23's fixture-catalog-vs-manifest completeness test | §24's independent, freshly-authored adversarial fixtures (not relying solely on the implementation phase's own fixture set) | add the missing fixture category before that group's phase can close | every implementation group | each group's own independent verification |
| Secret leakage (a fixture or error message accidentally embeds a real-looking or real secret) | Low | High | §14's synthetic-only fixture discipline; §28's error-message-never-echoes-raw-values rule | code review; a planned secret-shaped-string-scanning check over the fixture tree, analogous to standard pre-commit secret scanners, as part of each group's own test suite | remove/replace the offending fixture or error-message content immediately; treat as a Blocking finding in that group's independent verification | every implementation group | each group's own independent verification |
| Package-data omission (the wheel/sdist gap identified in §25 is never actually resolved) | Medium (a real, currently-open gap, not hypothetical) | Medium — only matters once a non-editable, non-checkout install needs runtime schema access, which no current code path requires | §25's explicit "required decision point for 136F" framing, not left implicit | §25's planned wheel-build-and-install test | resolve via `pyproject.toml` `force-include`/package-data addition in 136F (or an explicitly later, named phase if 136F's own scope review defers it — but the decision itself, deferred-or-not, must be recorded, not silently skipped) | 136F | before any phase that assumes non-editable-install schema availability |
| Divergent canonicalization (a future implementer accidentally writes a second canonicalization/digest function instead of reusing the existing one) | Low | High — would break this contract's single-canonicalization-implementation guarantee | §21's explicit "no new canonicalization or digest function" constraint, restated as binding | code review; a planned static check (e.g. a simple grep-based CI check for a second `canonical_json`/digest-computation definition outside `pcae.cltr.canonicalization`/`digest.py`) could be added by a future phase if this risk is judged to need more than code review alone | any phase touching canonicalization/digest integration | the phase that first implements Layer 3 integration (beyond this plan's own scope) |
| Implementation drift from the 62-item matrix (a future group's actual schema content silently diverges from its own `CSCH-EXEC-REQ` rows) | Low | High — would undermine the entire traceability discipline this contract chain has built | §24's "re-derive requirements... rather than accepting the implementation phase's own self-reported completion" instruction, applied per group | each group's own independent-verification phase's own matrix-subset re-extraction | repair the schema content (or, if the matrix row itself was wrong, repair the row — following the same documentation-only-repair discipline 136D itself modeled) before that group's phase can close | every implementation group | each group's own independent verification |

---

## 39. Planning verdict

**IMPLEMENTATION PLAN COMPLETE WITH OPEN PREREQUISITES — READY FOR
VALIDATION-ENGINE PREREQUISITE**

Chosen over the other two options because: the plan is not "not
complete" — every required section (§1–§38) has a concrete, re-derived
(not assumed) answer, and §37's no-go checklist shows every hard
condition is currently false. It is not simply "ready" without
qualification either, because §25 surfaces one genuinely open,
previously-undisclosed packaging decision point (wheel/sdist schema
inclusion) that must be explicitly resolved, not silently assumed, as
part of the very next phase (136F) before implementation can be
considered unblocked in full. "Ready for the validation-engine
prerequisite" does **not** mean ready to create executable schemas —
136F (dependency introduction) and its own independent verification
(136G) must complete first, per §4's explicit separate-bounded-phase
decision.

---

## Findings

| ID | Title | Source | Affected implementation group | Dependency impact | Security impact | Authority-boundary impact | Required phase | Verification phase | Latest acceptable resolution point |
|---|---|---|---|---|---|---|---|---|---|
| PREREQUISITE-136D-1 | No Draft 2020-12-conformant validator exists in the repository | 136D §3, restated and disposed by this plan §3–§4 | all (blocks any programmatic Group 1–6 validation) | High — blocks all schema-content independent verification that needs to run a real validator | None directly (a tooling gap, not a vulnerability) | None | 136F | 136G | before 136H begins |
| CONFIRMED-136E-1 | `jsonschema>=4.18,<5` is the correct, sole validation-engine selection for this contract | this plan §3.1–§3.3, independently derived comparison | all | resolves PREREQUISITE-136D-1's engine-selection half | Positive — MIT license, small footprint, no network dependency by construction | None | 136F | 136G | 136F |
| PREREQUISITE-136E-1 | The current wheel/sdist packaging scope (`packages = ["src/pcae"]`, sdist include list) does not include `schemas/`, including the not-yet-existing `schemas/cltr_cutover/` | independently discovered by this plan, §25 | none directly (no current code path needs non-editable-install schema access) | Low today; would become Medium if a non-editable-install consumer is ever added | None | None | 136F (decision point) | 136G (or a later, explicitly named phase if 136F defers) | before any phase assumes non-editable-install schema availability |
| NON-BLOCKING-136D-1 | Family row-order presentation cosmetic mismatch in 136C's own §4 table (carried forward, not repaired by this plan — out of scope, no schema content affected) | 136D §5 | none | None | None | None | (future documentation-hygiene pass, unscheduled) | n/a | not time-boxed by this plan |
| DEFERRED-136E-1 | 136B/136C's own historical reconciliation discrepancy (136B reported `reconciled` by 136C at freeze time, `not_delivered` by both 136D and this phase's own re-check) | this plan §0, restating the 136E phase brief's own instruction | none — explicitly not used as readiness evidence | None | None | None (bookkeeping, not authority) | (future documentation-hygiene phase, unscheduled) | n/a | not time-boxed by this plan; not repaired here per explicit instruction |
| DEFERRED-136E-2 | 136A's `reconciliation_status: conflict` (unchanged across every phase from 136A through this plan) | 136B §0.1, 136C §0.6, 136D §1 (implicitly, via unchanged reconciliation), this plan §0 | none | None | None | None (disclosed historical evidence only) | (future documentation-hygiene phase, unscheduled) | n/a | not time-boxed by this plan; not repaired here per explicit instruction — 136A is not mutated or redispatched |

---

## No-implementation proof

Confirmed for this phase's own diff:

- **No dependency was added.** `pyproject.toml` is unmodified by this
  phase (not in this task's `Allowed Files`; not touched).
- **No packaging file changed.** No `pyproject.toml`, lock file, or
  `MANIFEST.in`-equivalent was modified.
- **No production source changed.** No file under `src/` was modified.
- **No test source changed.** No file under `tests/` was modified.
- **No executable schema or fixture was added.** `schemas/cltr_cutover/`
  does not exist after this phase, exactly as before it. No file under
  `tests/fixtures/cltr_cutover/` was created.
- **No parser, loader, registry, or validator was implemented.** No
  Python module implementing any part of §5, §17, or §18 was created.
- **No typed model was implemented.** No Python `Enum`, `dataclass`, or
  equivalent for any Stage 3 companion-record family was created.
- **No authority resolver or authority-state persistence was
  implemented.** No file under `.pcae/cltr-authority/` was created; no
  `AuthorityResolver`/`resolve_authority` symbol was added anywhere in
  `src/`.
- **No authority pointer was implemented or changed.** The existing
  legacy pointer/production-authority mechanism is untouched.
- **No cutover record was created.** No `CutoverRequest`,
  `ReadinessEvidencePackage`, `HumanAuthorization`, `CutoverCandidate`,
  `Certification`, `PublicationAttempt`, `PublicationEvidence`,
  `ConcurrencyConflict`, or `RecoveryJournalEntry` instance (schema,
  fixture, or persisted record) was created anywhere.
- **No authority epoch changed.** `ProductionAuthority.LEGACY` remains
  the value read from `src/pcae/cltr/migration/enums.py`.
- **No CLTR authority was created.** No production pointer switch
  occurred.
- **No legacy authority was demoted.** No legacy authority was retired.
- **No production behavior changed.** Every `pcae` command's observable
  behavior (`health`, `check`, `status coherence`, `runtime inspect`,
  etc.) is unaffected by this phase's diff beyond the ordinary
  task/report/status/changelog bookkeeping this repository's governed
  lifecycle always produces.
- **No execution capability was introduced.**

Runtime remains **Observed**, maximum capability remains **observe**,
execution availability remains **unavailable**, independently re-
confirmed by this phase's own `pcae runtime inspect` run (§"Required
validation" below).

---

## Legacy lifecycle remains the sole production authority.
## CLTR remains derivative.

136E produced an executable-schema implementation plan only. No
validation dependency was added. No executable schema or fixture was
created. No strict parser, schema loader, registry, shape validator,
semantic validator, or typed model was implemented. No authority
resolver, authority state, or authority pointer was implemented or
changed. No cutover request, readiness package, authorization,
candidate, certification, publication attempt, conflict record, or
recovery journal was created. No authority epoch changed. No CLTR
authority was created. No legacy authority was demoted. No legacy
authority was retired. No production behavior changed. No execution
capability was introduced. Runtime remains Observed, maximum capability
remains observe, and execution availability remains unavailable.

---

## Recommended next phase

**136F — Draft 2020-12 Validation Engine and Strict JSON Parsing
Prerequisite.**

This phase does not add the dependency or parser in 136E. 136F is the
governed phase scoped to do so, per §4's bounded-prerequisite-phase
decision, followed by its own independent verification (136G) before any
schema-content implementation (136H, Group 1) begins.
