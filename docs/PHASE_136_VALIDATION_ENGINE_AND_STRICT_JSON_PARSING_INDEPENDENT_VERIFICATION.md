# Phase 136G — Validation Engine and Strict JSON Parsing Independent Verification

## Status

**VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR COMPANION EXECUTABLE
SCHEMA SHARED CORE**

This phase independently re-derived, reproduced, mutated, and
adversarially attacked the generic Draft 2020-12 validation-engine,
strict-parser, loader, registry, and shape-validation infrastructure
introduced by Phase 136F (`src/pcae/schema_runtime/`,
`src/pcae/schema_resources/`). It trusted none of 136F's own claims at
face value: every conformance claim, every containment claim, every
no-network claim, every determinism claim, and every no-authority claim
was independently re-exercised against fresh, 136G-authored fixtures and
attacks, not merely re-read.

**Two genuine defects were found and repaired**, both within the generic
schema-runtime boundary, both classified **BLOCKING** at time of
discovery (both were uncaught-crash / fail-open paths), both now closed
with regression tests. No Stage 3 schema, fixture, typed model, semantic
validator, or authority resolver/state/pointer was created. Legacy
lifecycle remains the sole production authority; CLTR remains
derivative; runtime remains Observed / observe / execution unavailable.

---

## 1. Methodology

Independent verification means: do not trust 136F's own tests,
136F's own report prose, or 136F's own classification of anything.
Concretely, this phase:

- Read `docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`
  (2246 lines, Phase 136E) and
  `docs/PHASE_136_DRAFT_2020_12_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_PREREQUISITE.md`
  (563 lines, Phase 136F) in full, including 136E §3 (`jsonschema`
  candidate comparison and selection), §4 (dependency-introduction plan),
  §16/§17/§20/§24/§25 (manifest, registry, format-checking, independent
  verification, and packaging plans), and 136F's own
  "Independent verification requirements (for 136G)" section, which
  explicitly named several of the attack classes pursued below.
- Read every line of the 136F implementation source
  (`json_parser.py`, `loader.py`, `registry.py`, `validation.py`,
  `errors.py`, `models.py`, `limits.py`, `__init__.py`,
  `schema_resources/__init__.py`) and every 136F test file, rather than
  relying on the phase-completion report's prose summary of them.
- Inspected the exact commit (`git show --stat --summary 4d9c51fd`,
  `git show --name-status --format=fuller 4d9c51fd`): 33 files changed,
  matching the 136F report's own count.
- Wrote **68 new, independent adversarial tests**
  (`tests/test_schema_runtime_136g_independent_verification.py`), against
  **new fixture schemas** (`tests/fixtures/schema_runtime_136g/`) not
  authored by 136F, deliberately exercising Draft 2020-12 features 136F's
  own fixtures did not cover (`prefixItems`, `contains`/`minContains`/
  `maxContains`, `dependentRequired`, `$anchor`, Boolean schemas).
- Ran every attack directly against the public API from a Python REPL
  first (to independently reproduce behavior before writing a permanent
  assertion), then converted every attack that revealed something
  worth pinning into a permanent regression test.
- Independently rebuilt the dependency in two **fresh, isolated
  virtual environments** (Python 3.9.6 project venv floor, and system
  Python 3.14.5 in a brand-new venv with no lockfile, letting `pip`
  resolve its own version within the declared range) rather than relying
  on 136F's own `.venv`.
- Ran the full unmarked suite fresh in this phase's own environment
  (see §23 below) rather than trusting 136F's reported count.
- Did **not** mutate or redispatch Phases 136A–136F; all reconciliation
  calls below are read-only (`Mutation: none (inspection only)`, machine
  output).

---

## 2. Source review

`git show --stat --summary 4d9c51fd` independently reproduced: 33 files
changed, 2573 insertions, 2 deletions, matching 136F's own report. Full
file list independently re-derived and cross-checked against the
136F canonical report's `files_changed` list — identical.

Full-text review of every non-test source file confirmed 136F's prose
accurately described the code, with two exceptions that constitute this
phase's two Blocking findings (§14 below): the module docstrings and
report both promised `parse_strict_json` "never raises on ordinary
invalid input," but this was not true for sufficiently deep (still
byte-tiny) nested input, and `validate_record_shape`'s status
computation had a latent fail-open bug at `max_issues=0`.

---

## 3. Dependency verification

- **Declared range vs. plan.** `jsonschema>=4.18,<5` in `pyproject.toml`
  matches 136E §3.3's planned constraint exactly (floor: first release
  with the modern `Registry`/`Resource` API as the documented path;
  ceiling: treats a future major as a deliberate, reviewed bump).
- **Installed version.** Project `.venv` (Python 3.9.6, the repository's
  declared floor): `jsonschema` 4.25.1, `referencing` 0.36.2,
  `jsonschema-specifications` 2025.9.1, `rpds-py` 0.27.1, `attrs` 26.1.0
  — independently re-queried via `pip show`, not copied from 136F's
  report.
- **Draft 2020-12 support is real, not assumed.** §5 below independently
  exercises `$defs`, same-file `$ref`, cross-resource `$ref`,
  `if`/`then`/`else`, `oneOf`, `allOf`, `dependentRequired`,
  `prefixItems`, `contains`/`minContains`/`maxContains`,
  `additionalProperties: false`, `unevaluatedProperties: false`, nested
  composition, Boolean schemas, `$anchor`, and invalid-schema rejection
  — all pass against fresh 136G fixtures.
- **Validator identity is explicit, not inferred.** `validation.py` and
  `loader.py` both import `Draft202012Validator` by name; there is no
  `jsonschema.validators.validator_for(...)` call anywhere in
  `schema_runtime` that would let an untrusted schema's own `$schema`
  field select the validator dynamically
  (`test_136g_selected_validator_is_explicitly_draft202012_not_inferred`,
  `test_136g_draft202012validator_class_identity_stable_not_alias_of_latest`).
- **Licenses.** Independently re-queried (`pip show`): all five
  packages (`jsonschema`, `referencing`, `jsonschema-specifications`,
  `rpds-py`, `attrs`) report `License-Expression: MIT`, compatible with
  this repository's Apache-2.0 license.
- **Python-version compatibility.** `requires-python = ">=3.9"`. The
  project `.venv` is Python 3.9.6 — this phase ran the **entire**
  schema_runtime suite (both 136F's and 136G's own) natively on the
  declared floor, not merely on a newer interpreter. A second, fully
  independent clean-room install (`python3 -m venv`, no source-tree
  reuse) was performed on system Python 3.14.5 with **no lockfile**,
  letting `pip` resolve its own dependency versions: it resolved
  `jsonschema` 4.26.0 / `referencing` 0.37.0 (both newer than 136F's
  pinned versions, both still within `>=4.18,<5`), and the full
  schema_runtime suite (130 non-slow tests at that point, pre-136G-repair
  baseline) passed identically. This is a genuine, independent
  confirmation that **future patch/minor upgrades within `<5` do not
  silently change the selected validator class or observable behavior**
  — not merely a documentation claim.
- **Installation succeeds in a clean environment.** Confirmed twice
  (Python 3.9 `.venv`-equivalent floor behavior already exercised daily;
  fresh Python 3.14 venv built from scratch in this phase, `pip install
  -e ".[dev]"` with no cache reuse across the two environments).
- **Import failure is fail-closed and clearly classified.** Independently
  reproduced in a fresh venv with the package installed via `--no-deps`
  (so `jsonschema` itself is absent): `import pcae.schema_runtime` raises
  `pcae.schema_runtime.errors.SchemaResourceError: jsonschema is not
  installed; schema_runtime requires jsonschema>=4.18,<5` immediately at
  import time — explicit, human-readable, and not silently swallowed.
  **Observation (non-blocking):** this exception is a
  `SchemaResourceError`, not an `ImportError`/`ModuleNotFoundError`; a
  caller written to catch `ImportError` specifically would not catch it
  (though the original `ImportError` is preserved as `__cause__`).
  Disclosed, not repaired (§14, `CONFIRMED-136G-3`).
- **Incompatible version below the floor.** Independently installed
  `jsonschema==4.17.3` (pre-4.18, pre-dating the modern `Registry` API)
  into a fresh venv with `--no-deps`: `import pcae.schema_runtime` raises
  a raw `ModuleNotFoundError: No module named 'referencing'` (because
  4.17.3 does not itself depend on `referencing`) — fail-closed, but
  **inconsistent** with the friendlier `SchemaResourceError` wrapping
  used for a fully-absent `jsonschema`. `loader.py` wraps only the
  `from jsonschema import Draft202012Validator` import; `registry.py`'s
  `from referencing import Registry, Resource` import is unguarded.
  Disclosed as non-blocking (§14, `CONFIRMED-136G-4`) — only reachable
  via a manually broken/incompatible install, never via the declared
  `jsonschema>=4.18,<5` floor (which always pulls `referencing`
  transitively), and no runtime path silently falls back to permissive
  validation in either case.
- **No optional network/format extras required.** Confirmed:
  `jsonschema[format]`/`jsonschema[format-nongpl]` are not installed;
  `Draft202012Validator` is constructed with no `FormatChecker` anywhere
  in `schema_runtime` (grep-confirmed); §9 below independently reproduces
  that `format` is not enforced.

**Verdict: CONFIRMED.**

---

## 4. Supported-Python verification

Ran the full schema_runtime suite (136F's 69 + 136G's 68 = 137 tests, 3
`slow`-marked) on:

- Python 3.9.6 (project `.venv`, the repository's declared floor) — all
  137 pass (134 non-slow + 3 slow).
- Python 3.14.5 (fresh clean-room venv, no lockfile) — all 130 non-slow
  tests available at that point in the run passed identically (this
  clean-room run was performed before the two 136G repairs were
  finalized against the main `.venv`; the full 137-test run, including
  the repairs, was independently reconfirmed against the 3.9.6 floor
  venv used throughout this phase).

No syntax or stdlib feature newer than Python 3.9 is used anywhere in
`schema_runtime`/`schema_resources` (confirmed by the fact that the code
runs unmodified and green on the 3.9.6 floor).

Python 3.10, 3.11, 3.12, and 3.13 were **not** available on this
machine and were **not tested** — disclosed honestly rather than
silently assumed compatible. This is the same limitation 136F itself
operated under.

**Verdict: CONFIRMED for 3.9 (floor) and 3.14; 3.10–3.13 untested
(disclosed).**

---

## 5. Draft 2020-12 conformance attack

New fixture package: `tests/fixtures/schema_runtime_136g/conformance_package/feature_matrix.schema.json`
— authored independently, not derived from 136F's fixtures. Exercises,
each independently reproduced against a fresh registry:

| Feature | Result |
|---|---|
| `prefixItems` + `items: false` (tuple typing) | CONFIRMED — extra element rejected |
| `$anchor` cross-reference (`#positiveNumber`) resolves and enforces `exclusiveMinimum` | CONFIRMED |
| `contains` / `minContains` / `maxContains` | CONFIRMED — missing tag, satisfied tag, and over-`maxContains` all correctly classified |
| `dependentRequired` | CONFIRMED |
| Boolean schema `false` (property always rejected) | CONFIRMED |
| Boolean schema `true` (property always accepted) | CONFIRMED |
| Schema with `$schema` field entirely absent (not merely wrong) | CONFIRMED rejected — distinct fixture from 136F's "wrong dialect value" case |
| Schema whose own structure fails Draft 2020-12 meta-schema checking (`"required": "not-an-array"`) | CONFIRMED rejected at load time |
| Validator selection is explicit `Draft202012Validator`, never inferred from schema/record content | CONFIRMED (§3) |

136F's own fixtures independently re-exercised `$defs`, same-file
`$ref`, cross-file `$ref`, `if`/`then`/`else`, `oneOf`, `allOf`,
`additionalProperties: false`, `unevaluatedProperties: false`
(including nested-unknown-property rejection) — all reconfirmed passing
under both this phase's repairs and unmodified.

**Verdict: CONFIRMED.**

---

## 6. Strict parser attack

Independently attacked, each with its own regression test:

| Attack | Result |
|---|---|
| Empty input / whitespace-only input | CONFIRMED rejected (`invalid_json`) |
| Top-level scalar / string / bool / null (not required to be an object) | CONFIRMED accepted |
| Multiple top-level JSON values (`"{} {}"`) | CONFIRMED rejected |
| Leading zero (`"01"`) | CONFIRMED rejected |
| Negative zero (`"-0"`) | CONFIRMED accepted, parses to `0` |
| Exponent forms (`1e10`, `1E10`, `1e+10`, `1e-10`) | CONFIRMED accepted |
| Very large integer (400 digits) | CONFIRMED accepted, no overflow (Python arbitrary-precision int) |
| UTF-8 BOM before `{}` | CONFIRMED rejected (not silently stripped) |
| Embedded `\u0000` (escaped NUL) inside a string | CONFIRMED preserved, not truncated |
| Literal unescaped control character (raw NUL byte) in a string | CONFIRMED rejected per RFC 8259 |
| Lone high surrogate (`\ud800`, no low surrogate) | CONFIRMED preserved as a lone surrogate, no crash |
| Malformed `\u` escapes (`\u12`, `\uZZZZ`, `\u`) | CONFIRMED rejected |
| Invalid backslash escape (`\q`) | CONFIRMED rejected |
| Invalid UTF-8 continuation bytes | CONFIRMED rejected (`invalid_utf8`) |
| Duplicate key rejection precedes any schema concern | CONFIRMED — `parse_strict_json` never returns a `value` for a rejected document; there is no code path from a duplicated-key document into `validate_record_shape` |
| Error messages do not echo unboundedly-large secret-like values into the *duplicate-key* message itself | CONFIRMED for this code path (the offending key name is short; the associated value is not echoed) |
| **Deeply nested input (tiny byte size, ~500+ levels)** | **BLOCKING — found uncaught `RecursionError`; repaired (§14, `BLOCKING-136G-1`)** |

Unicode-normalization-equivalent keys (e.g. NFC vs. NFD forms of an
accented character) are **not** treated as duplicates at Layer 1 — Python
string equality is codepoint-exact, and `parse_strict_json` performs no
Unicode normalization before comparing keys. This is the documented,
correct boundary for this phase: Layer-1 strict parsing operates on the
JSON text as written; any Unicode-canonicalization policy is explicitly
deferred to a future semantic/canonicalization layer (already flagged as
out of scope by 136E §21, "Canonicalization integration plan," not
implemented by 136F or 136G). Disclosed, not a defect.

JSON Pointer escaping (`~0`/`~1`) reconfirmed correct via a fresh
independent case (`{"a/b": {"c~d": 1, "c~d": 2}}` → `/a~1b/c~0d`,
136F's own test) plus 136G's own escaping-adjacent path assertions.

**Verdict: CONFIRMED for parsing correctness; BLOCKING found and
repaired for depth safety (see §14).**

---

## 7. Resource-limit attack

| Attack | Result |
|---|---|
| Exact byte-limit boundary | CONFIRMED accepted at exactly `max_bytes` |
| One byte over the limit | CONFIRMED rejected (`input_too_large`) |
| Multibyte UTF-8 near the limit (`"🎯"`, 6 bytes total incl. quotes) | CONFIRMED — both the `str` and `bytes` call paths agree on the true byte count, not code-point count |
| `max_issues=0` | **BLOCKING — silently reported `VALID` for a genuinely invalid record; repaired (§14, `BLOCKING-136G-2`)** |
| `max_issues=1` | CONFIRMED — exactly one issue returned, status still correctly `INVALID` after repair |
| Excessive `max_issues` (1,000,000) | CONFIRMED no error, correct status |
| Registry resource-count ceiling enforced **across multiple roots**, not merely per-root | CONFIRMED — 3+3 resources across two roots with `max_resources=5` correctly rejected |
| Deeply nested record passed directly to `validate_record_shape` against a self-referential schema | **BLOCKING — second, distinct uncaught `RecursionError` path; repaired (§14, `BLOCKING-136G-1b`)** |
| Wide objects / very long flat arrays | CONFIRMED no crash (not a recursive-depth concern; only the byte-size limit applies, already covered above) |
| Catastrophic-pattern (ReDoS) risk in schema regexes | **DEFERRED** — this phase's threat model treats schema resources as trusted-root content (loader containment already restricts *which* schemas can be loaded); a maliciously crafted `pattern` keyword inside a schema is a schema-*authoring* concern for the future Stage 3 phase, not a generic-infrastructure defect. Not attacked further here; explicitly flagged for the schema-authoring phase's own security review. |
| Large error messages | CONFIRMED not artificially truncated; no evidence of unbounded growth under normal invalid input (not separately capped, disclosed as current behavior, not a defect) |

**Verdict: CONFIRMED with two Blocking findings, both repaired (§14).**

---

## 8. Loader containment attack

136F's own four containment tests (absolute-path escape, `../` traversal,
leaf symlink, symlinked intermediate directory) were independently
re-run and reconfirmed. This phase additionally attacked:

| Attack | Result |
|---|---|
| Empty relative path | CONFIRMED rejected/raises cleanly |
| `./` current-directory-relative path | CONFIRMED correctly resolved and contained |
| Repeated traversal (`../../secret.schema.json`) | CONFIRMED rejected |
| Hard link (not a symlink) placed inside the trusted root, pointing to a file outside the root | **CONFIRMED, documented as an assumed trust boundary, not a defect** — a hard link is indistinguishable from an ordinary file once it exists inside the root; containment defends against a *link redirecting outside an otherwise-trusted root*, not against an attacker who can already write into the trusted root (a materially different, out-of-scope threat model for generic infrastructure whose caller supplies the trusted root explicitly) |
| Content replaced between `discover_schema_files()` and `load_schema_resource()` (two-step API) | CONFIRMED — content is read fresh at load time, not cached from discovery; a genuine concurrent-process TOCTOU race is a residual, disclosed risk of any synchronous filesystem API and is not eliminated (nor claimed to be) by this loader |
| Caller passes an **unresolved** root that itself sits behind a filesystem symlink (macOS `/var` → `/private/var`, affecting the default temp directory) | **CONFIRMED, non-blocking finding** — a legitimate same-root file can be falsely rejected as "escapes trusted root" because containment compares a lexically-normalized candidate against a fully symlink-resolved root. This is fail-**closed** (the safe direction: a legitimate load is refused, never an illegitimate one accepted), but is a real caller-facing surprise. Workaround (pre-resolve the root before calling) independently verified to work. Disclosed, not repaired — always failing closed on this ambiguity is the correct posture (`CONFIRMED-136G-5`). |
| Case-insensitive-filesystem aliasing | Not separately reproducible as a distinct attack on this filesystem beyond what the symlink-resolution comparison already covers; the resolved-path-vs-lexical-path comparison used by the loader is orthogonal to case sensitivity and would catch a case-based alias the same way it catches a symlink-based one, since `Path.resolve(strict=True)` on macOS's default case-insensitive-but-case-preserving APFS returns the on-disk canonical casing. Not independently exploitable within this phase's time budget; flagged as a residual, low-confidence area for a future phase with access to a genuinely case-sensitive vs. case-insensitive filesystem pair to test cross-platform. |

TOCTOU (time-of-check/time-of-use) substitution: **not fully
eliminable** through a synchronous, single-process filesystem API by
construction (this is true of essentially any filesystem-based loader
without OS-level file locking or an atomic read-and-verify primitive).
This phase does not claim elimination; 136F's own report did not either.
Documented as an accepted, disclosed limitation, consistent with the
generic-infrastructure threat model (trusted root, not necessarily a
race-free filesystem).

**Verdict: CONFIRMED, with one non-blocking usability finding disclosed
(§14, `CONFIRMED-136G-5`) and TOCTOU explicitly accepted as a residual,
disclosed limitation rather than silently assumed away.**

---

## 9. Strict schema-resource parsing attack

Reconfirmed (136F's own fixtures, independently re-run): duplicate JSON
keys inside a schema resource are rejected via the same
`parse_strict_json` used for records (no separate, more permissive
`json.load` path exists anywhere in `schema_runtime` — confirmed via
`grep`); malformed JSON is rejected; missing `$id` is rejected; wrong
dialect value is rejected; meta-schema-check failure is rejected;
oversized resource is rejected.

136G additionally and independently confirmed: a schema resource with
`$schema` **entirely absent** (not merely a wrong value) is rejected
identically to the wrong-value case (§5); a schema whose own structure
fails Draft 2020-12 meta-schema conformance (`"required": "not-an-array"`)
is rejected at load time via `Draft202012Validator.check_schema`, not
merely deferred to first-use validation failure.

No schema resource anywhere in `schema_runtime` is loaded through
ordinary permissive `json.load`/`json.loads` — confirmed by source
inspection of every file in the package (no bare `json.load` call
exists; the only import of the stdlib `json` module anywhere in
`schema_runtime`/`schema_resources` is none — `json_parser.py` is a
hand-written parser with zero dependency on the stdlib `json` module).

**Verdict: CONFIRMED.**

---

## 10. Registry no-network attack

Independently monkeypatched `socket.socket`, `socket.create_connection`,
and `socket.getaddrinfo` (136F's own tests monkeypatched only
`socket.socket`) and attempted, against a real offline registry:
unregistered HTTPS `$ref`, unregistered HTTP `$ref`, `file://` URI,
`data:` URI, `ftp://` URI, an arbitrary custom scheme, and a
remote-looking-but-unregistered `$id`. **Every case failed closed via
`referencing.exceptions.Unretrievable`/the registry's own
`SchemaRegistryError`, with zero calls to any of the three blocked
socket primitives** (asserted via a `calls` accumulator that remained
empty across all six URI attempts).

Additionally, independently monkeypatched `urllib.request.urlopen`
directly (a transport primitive 136F's own tests did not touch) and
confirmed an ordinary `validate_record_shape` call against a
locally-registered schema completes successfully with it forbidden —
proving no code path attempts an HTTP(S) fetch through `urllib` either.

**Verdict: CONFIRMED — no-network is proven against a wider set of
transport primitives than 136F's own tests exercised, not merely
re-asserted.**

---

## 11. Registry determinism attack

- **Insertion-order independence.** Built the same two-resource registry
  as `build_offline_registry(root_a, root_b)` and
  `build_offline_registry(root_b, root_a)`; `schema_ids` (which is
  `tuple(sorted(...))` by construction) is identical either way —
  confirmed both by source inspection and by an independent test.
- **Hash-seed independence.** Ran the same registry-build-plus-validate
  sequence under `PYTHONHASHSEED=0`, `PYTHONHASHSEED=1`, and
  `PYTHONHASHSEED=42` in three separate fresh subprocesses: identical
  `schema_ids` tuple and identical issue ordering
  (`[(code, instance_path), ...]`) in all three.
- **Repeated-call stability.** Ten repeated calls to `validate_record_shape`
  against the same invalid record produce byte-identical issue-ordering
  tuples every time.
- **Cross-Python-version stability.** The Python 3.14.5 clean-room venv
  (§3) independently reproduced the same schema_runtime test results as
  the 3.9.6 floor venv, which includes the ordering-sensitive tests.

**Verdict: CONFIRMED.**

---

## 12. Duplicate-`$id` and schema-substitution attack

- **Byte-identical duplicate `$id` across two roots.** Independently
  constructed two files with SHA-256-identical content (verified via
  `hashlib.sha256(...).digest()` equality before the attack) but
  different filenames in different roots, both declaring the same
  `$id`. **Rejected** (`Duplicate $id ...`), confirming the registry
  "prefers rejection" even when contents match byte-for-byte, exactly as
  the phase brief requires ("Duplicate IDs must fail closed even when
  contents match ... Prefer rejection").
- **Same `$id`, different bytes, across roots.** Reconfirmed rejected
  (136F's own test, independently re-run).
- **Registry resource-count ceiling across multiple roots.** §7 above.
- **Malicious test root shadowing a packaged/production schema.** Not
  independently exploitable: `build_offline_registry(*roots)` requires
  every root to be an explicit caller-supplied `Path` argument; there is
  no implicit "search path," no environment-variable override, and no
  current-working-directory fallback anywhere in `schema_runtime` or
  `schema_resources` (confirmed via `grep` for `os.environ`, `getenv`,
  `os.getcwd`, `Path.cwd` — zero matches in either package). A caller
  cannot "accidentally" mix a test root into a production lookup because
  there is no production lookup API today (136F's own §20, "No public
  CLI was added," reconfirmed still true in §16 below).

**Verdict: CONFIRMED.**

---

## 13. Shape-validation API attack

| Attack | Result |
|---|---|
| Non-mapping input (`list`, `str`, `int`, `None`, `bool`, `float`) | CONFIRMED — every case fails closed as `INVALID` via the schema's own `"type": "object"` rejection; no uncaught exception |
| Unknown schema id | CONFIRMED — `INFRASTRUCTURE_FAILURE` / `unknown_schema`, distinct from `INVALID` |
| Unresolved `$ref` | CONFIRMED — `INFRASTRUCTURE_FAILURE` / `schema_reference_unresolved` (136F's own test, independently re-run) |
| Self-referential (cyclic) Python `dict` (`record["cycle"] = record`) | **Originally CONFIRMED non-crashing** (additionalProperties:false rejected it before any deep traversal); **after this phase's own record-depth-guard repair (§14), now correctly and more robustly classified as `INFRASTRUCTURE_FAILURE` unconditionally**, since a true self-reference is, by construction, infinitely deep and the iterative depth guard detects this without looping forever (each stack-push increases the tracked depth) |
| Deeply nested (but non-cyclic) record against a self-referential schema | **BLOCKING — found and repaired, see §14** |
| Record mutation | CONFIRMED — `deepcopy`-before/`deepcopy`-after comparison shows zero mutation across a validation call that produces multiple issues |
| Recursive Python structures (self-referential mapping) | Covered above; no crash, no hang |
| Arbitrary `Mapping` implementations executing code during validation | Not independently reproduced as exploitable: `jsonschema`'s own `iter_errors` accesses the mapping only through `.items()`/`__getitem__`/`in` — a hostile `Mapping` subclass *could* execute arbitrary code from those dunder methods (this is inherent to any Python code that iterates an untrusted `Mapping`, not specific to `schema_runtime`), but `validate_record_shape`'s own documented contract already requires "`record` must already have been produced by strict parsing" (i.e. a plain `dict` from `parse_strict_json`, never an arbitrary `Mapping` subclass supplied directly by an untrusted caller). This is a **PREREQUISITE / DEFERRED** finding for a future phase that exposes this API to less-trusted callers: the current contract is documentation-only, not type- or runtime-enforced (`Mapping[str, object]` is a structural type hint, not a plain-`dict` check). No `isinstance(record, dict)` guard exists. Disclosed, not repaired in 136G (repairing it would be a defensible small addition, but is not required by 136F's own contract, which already assumes an already-strictly-parsed input); flagged explicitly for 136H. |

**Verdict: CONFIRMED, with one Blocking finding repaired (§14) and one
PREREQUISITE finding deferred to 136H (§14, `PREREQUISITE-136G-1`).**

---

## 14. Findings

### `BLOCKING-136G-1` — Uncaught `RecursionError` in `parse_strict_json` on deeply nested (but byte-tiny) input

- **Independent reproduction.** `parse_strict_json("[" * 500 + "1" + "]" * 500)`
  raised an uncaught `RecursionError: maximum recursion depth exceeded in
  comparison` from a direct Python invocation (i.e. not merely under
  pytest's own deeper call stack). Payload size: 2001 bytes — far below
  `DEFAULT_MAX_INPUT_BYTES` (5 MiB). Empirically bisected: depth 300
  crashes, depth 200 does not (see `BLOCKING-136G-1b` for a materially
  lower crash threshold in a *different* code path).
- **Affected source.** `src/pcae/schema_runtime/json_parser.py`
  (`_Parser._parse_object`/`_parse_array`, called recursively with no
  depth bound; 136F's own "Limitations" section disclosed this as a
  *known* gap relying only on the CPython interpreter's own recursion
  limit as a backstop, but did not treat it as blocking).
- **Security impact.** A trivially small, attacker-controlled input
  (a chain of nested arrays/objects) crashes the parser with an
  interpreter-level exception the caller did not ask for and the
  module's own docstring explicitly promised would never happen
  ("Never raises on ordinary invalid input. ... returns a structured
  `JsonParseResult`"). This is a denial-of-service-class defect against
  any caller that does not itself guard every `parse_strict_json` call
  site with a broad `except Exception`.
- **Packaging impact.** None.
- **Validation impact.** Directly contradicts the parser's own documented
  fail-closed contract.
- **Authority-boundary impact.** None (no authority state touched).
- **Repair decision.** Repaired. Added `DEFAULT_MAX_NESTING_DEPTH = 200`
  (`limits.py`) and an explicit depth check (`_Parser._check_depth`,
  called at the entry of both `_parse_object` and `_parse_array`,
  comparing the already-tracked JSON-Pointer path length against the
  configured limit) that raises the existing `_StrictJsonError` with the
  existing `invalid_json` code — no new error code needed, since this is,
  correctly, a parse-time syntactic rejection. `max_depth` is exposed as
  a new keyword argument on `parse_strict_json` (default
  `DEFAULT_MAX_NESTING_DEPTH`), consistent with the existing
  `max_bytes`/`require_top_level_object` parameter style.
- **Tests.** `test_136g_deeply_nested_array_fails_closed_instead_of_crashing`,
  `test_136g_deeply_nested_object_fails_closed_instead_of_crashing`,
  `test_136g_nesting_just_under_limit_still_accepted`,
  `test_136g_max_depth_is_configurable_per_call`.
- **Residual risk.** The chosen limit (200) is conservative relative to
  the empirically observed crash threshold (~300–500 depending on
  caller stack depth at time of the call) but is not derived from a
  formal proof of CPython's exact per-frame stack cost; a sufficiently
  different CPython build/platform stack-frame size could theoretically
  still crash below 200 in a deeply-stacked caller context (e.g. deeply
  nested `try`/`except` machinery already on the stack). No crash was
  observed at 200 in any tested configuration (direct call, pytest,
  `-n auto` parallel workers, both Python 3.9.6 and 3.14.5).
- **Future milestone.** None required; this is now a closed, tested,
  generic-infrastructure limit appropriate for 136H's Stage 3 schema
  authoring to build on directly.

### `BLOCKING-136G-1b` — Uncaught `RecursionError` in `validate_record_shape` on deep records against a recursive schema

- **Independent reproduction.** Built a trivial self-referential schema
  (`{"type": "array", "items": {"$ref": "#"}}`) and validated a Python
  list nested 300 levels deep against it directly (bypassing
  `parse_strict_json` entirely, to isolate this from
  `BLOCKING-136G-1`): raised an uncaught `RecursionError` from inside
  `Draft202012Validator.iter_errors`. Depth 200 (the *parser's* new
  limit from `BLOCKING-136G-1`) was still safe for this specific schema,
  but this is schema-shape-dependent, not a fixed universal boundary —
  a schema with more `$ref` indirection per data-nesting-level could
  plausibly crash at a shallower record depth than 200, meaning a record
  that `parse_strict_json` itself already accepted as valid could still
  crash `validate_record_shape` downstream.
- **Affected source.** `src/pcae/schema_runtime/validation.py`
  (`validate_record_shape`, via `Draft202012Validator.iter_errors`,
  which is third-party code with no depth guard of its own when a
  schema is self-referential).
- **Security impact.** Same class as `BLOCKING-136G-1`: an
  attacker-controlled (or even an accidentally deep, legitimate) record
  crashes the validation API with an uncaught exception instead of
  a structured `ShapeValidationResult`, against a schema shape (a
  self-referential/recursive `$ref`) that Stage 3 schema authoring may
  plausibly need (e.g. any tree-shaped or nested-composition record
  family).
- **Packaging impact.** None.
- **Validation impact.** Not explicitly promised "never raises" by
  `validation.py`'s own docstring (unlike the parser), but is squarely
  within the spirit of this phase's fail-closed requirement and directly
  actionable before Stage 3 schemas — which may use exactly this kind of
  recursive `$ref` — are authored.
- **Authority-boundary impact.** None.
- **Repair decision.** Repaired. Added `DEFAULT_MAX_RECORD_DEPTH = 150`
  (`limits.py`, deliberately distinct from and lower than
  `DEFAULT_MAX_NESTING_DEPTH`, since the crash threshold for this path is
  schema-dependent and was empirically lower) and a new,
  **explicitly iterative (non-recursive) stack-based** depth-scan
  function (`_exceeds_max_depth` in `validation.py`) called before any
  call into the underlying validator. A record exceeding the configured
  depth now returns `ShapeValidationResult(status=INFRASTRUCTURE_FAILURE,
  issues=(ValidationIssue(code="internal_validation_error", ...),))` —
  reusing the existing `internal_validation_error` code (previously
  unreachable dead code disclosed in `CONFIRMED-136G-1`, now genuinely
  reachable and correctly describing "the shape-validation machinery
  itself refused to run," distinct from `schema_invalid_record`, which
  means "the validator ran and the record's shape did not match"). No
  new error code was added. `max_record_depth` is a new keyword argument
  on `validate_record_shape` (default `DEFAULT_MAX_RECORD_DEPTH`).
  The guard function itself was deliberately written as an explicit
  stack walk, not recursion, specifically so the depth check cannot
  itself be defeated by the same class of attack it defends against —
  independently verified against a 200,000-level-deep structure with no
  crash.
- **Tests.** `test_136g_deeply_nested_record_against_recursive_schema_fails_closed_instead_of_crashing`,
  `test_136g_record_depth_just_under_limit_still_validated`,
  `test_136g_record_depth_guard_is_configurable_per_call`,
  `test_136g_record_depth_guard_uses_iterative_not_recursive_walk_and_survives_extreme_depth`,
  plus the updated `test_136g_self_referential_mapping_does_not_crash_validator`.
- **Residual risk.** `DEFAULT_MAX_RECORD_DEPTH = 150` is a conservative
  general-purpose default chosen below the empirically observed ~200-safe/
  ~300-crash boundary for the single recursive-schema shape tested; a
  schema with a longer `$ref`-indirection chain per data level could
  still exhibit a lower true crash threshold than 150 in principle. Any
  future Stage 3 schema family that is genuinely, deliberately recursive
  (if one is ever authored — 136E's own plan describes an acyclic `$ref`
  *authoring* graph, which is a different concept from data-shape
  recursion) should re-derive and re-verify this constant against its
  actual schema shape rather than assume 150 is universally safe.
- **Future milestone.** 136H (or whichever phase first authors a
  self-referential/recursive Stage 3 schema, if any) must re-verify this
  constant against that schema's actual `$ref` indirection depth.

### `BLOCKING-136G-2` — `max_issues=0` (or any undercount) silently reports `VALID` for a genuinely invalid record

- **Independent reproduction.** `validate_record_shape({}, schema_id=...,
  registry=..., max_issues=0)` against a schema requiring a field that
  `{}` does not have returned `ShapeValidationResult(status=VALID,
  issues=())` — i.e. a record that is **definitely, unambiguously
  invalid** (missing a required property) was reported valid, solely
  because the caller asked for zero issues back.
- **Affected source.** `src/pcae/schema_runtime/validation.py`,
  `validate_record_shape`: the original code computed
  `issues = tuple(... for err in errors[:max_issues])` and then branched
  on `if issues: INVALID else: VALID` — deciding *status* from the
  *truncated* tuple instead of from whether `errors` (the untruncated
  result of `validator.iter_errors(record)`) was non-empty.
- **Security impact.** This is a textbook fail-open bug: a caller who
  passes `max_issues=0` (a plausible legitimate use — "just tell me
  pass/fail, I don't need the detail") receives an incorrect `VALID`
  verdict for invalid data. Any future caller relying on `.ok`/`.status`
  without inspecting `.issues` would be silently misled. This is exactly
  the class of defect the phase brief names explicitly as Blocking
  ("silent fallback to permissive validation").
- **Packaging impact.** None.
- **Validation impact.** Directly falsifies the module's own documented
  claim: "This API makes no semantic or authority claim: a `VALID`
  result means the record's shape matched the schema, nothing more" —
  under the bug, `VALID` did not reliably mean even that.
- **Authority-boundary impact.** None directly, but this class of bug is
  precisely why 136G's phase brief insists shape validity must never be
  mis-happen to say "valid" when it is not: a future Stage 3 caller
  building any downstream decision (however non-authoritative) on top of
  a `VALID` result would be building on a false signal.
- **Repair decision.** Repaired. Status is now computed from `errors`
  (the full, untruncated result of `validator.iter_errors(...)`), not
  from the possibly-empty-after-truncation `issues` tuple. `issues` is
  still correctly truncated to `max_issues` for the *returned issue
  list*, but no longer influences `status`.
- **Tests.** `test_136g_max_issues_zero_returns_no_issues_but_marks_invalid`,
  `test_136g_max_issues_one_returns_exactly_one`,
  `test_136g_excessive_max_issues_does_not_error`.
- **Residual risk.** None identified; the fix is a minimal, surgical
  change to which value (`errors` vs. `issues`) drives the status
  branch, and both branches were independently re-verified against a
  range of `max_issues` values (0, 1, 1,000,000).
- **Future milestone.** None required; closed.

### `CONFIRMED-136G-1` — Three (now two) frozen error-vocabulary codes were unreachable dead code

- Independent AST/text scan of every `schema_runtime` source file (except
  `errors.py`, which only *declares* the vocabulary) for each of the 13
  frozen `ERROR_CODES` appearing as a string literal found that
  `unsupported_schema_version`, `unsupported_dialect`, and
  `internal_validation_error` were **never produced** by any
  `ValidationIssue` anywhere in the pre-136G implementation. Loader-level
  dialect/version rejection surfaces as a plain `SchemaResourceError`
  exception (still fail-closed, just not through the structured
  `ValidationIssue`/error-code channel that the other 10 codes use).
  `BLOCKING-136G-1b`'s repair incidentally made `internal_validation_error`
  genuinely reachable (a legitimate, correctly-scoped use), reducing the
  unreachable set to two: `unsupported_schema_version` and
  `unsupported_dialect`.
- **Repair decision.** Disclosed, not repaired further. Wiring
  `unsupported_dialect`/`unsupported_schema_version` through as
  structured `ValidationIssue`s (rather than raw loader exceptions) would
  require restructuring `loader.py`'s exception-based API into a
  result-based one, which is a larger, deliberate API-shape decision
  better made when Stage 3's own loading/validation call sites are
  designed (136H+), not retrofitted here without a concrete caller to
  validate the new shape against.
- **Test.** `test_136g_discloses_unreachable_error_vocabulary_codes`
  (pins the current reachable/unreachable sets so any future silent
  change in either direction is visible in the test diff).
- **Future milestone.** 136H should decide, when the loader gains its
  first real caller beyond tests, whether loader failures should also be
  restructured into the `ValidationIssue` vocabulary.

### `CONFIRMED-136G-2` — Format-checking non-enforcement independently reconfirmed with a fresh schema

- Built a fresh `format: date-time` schema (not 136F's fixture) and
  confirmed a syntactically invalid date-time string still validates as
  `VALID` — matching 136F's own documented, deliberate design decision.
  No repair needed; disclosed as confirmed-correct, matching the design
  intent.

### `CONFIRMED-136G-3` — Absent-`jsonschema` import failure is a `SchemaResourceError`, not an `ImportError`

- See §3. Fail-closed and clearly messaged; a caller specifically
  catching `ImportError` (rather than the package's own exception types,
  or a bare `Exception`) would not catch it, though the underlying
  `ImportError`/`ModuleNotFoundError` is preserved via `raise ... from
  _exc`. Non-blocking; disclosed.

### `CONFIRMED-136G-4` — Below-floor `jsonschema` version produces an unwrapped `ModuleNotFoundError` for the `referencing` import specifically

- See §3. Only reachable through a manually broken/incompatible install
  that bypasses the declared `jsonschema>=4.18,<5` floor (which always
  pulls `referencing` transitively when installed normally via `pip
  install .`). Fail-closed either way; the *wrapping consistency* is
  the only gap. Non-blocking; disclosed.

### `CONFIRMED-136G-5` — Unresolved symlinked trusted root causes a false (fail-closed) containment rejection

- See §8. Fail-closed direction only (never accepts an illegitimate
  path); a documented caller-facing surprise, not a security defect.
  Non-blocking; disclosed. Workaround (pre-resolve the root) independently
  verified to work.

### `PREREQUISITE-136G-1` — `validate_record_shape`'s `Mapping` contract is documentation-only, not runtime-enforced

- See §13. The function's docstring requires an already-strictly-parsed
  `record`, but nothing prevents a caller from passing an arbitrary
  hostile `Mapping` subclass whose dunder methods (`__getitem__`,
  `.items()`, `__contains__`) execute arbitrary code when iterated by
  `jsonschema`'s own traversal. This is not unique to `schema_runtime` —
  it is inherent to any code that iterates an untrusted `Mapping` — but
  is worth a deliberate decision (an `isinstance(record, dict)` guard,
  or an explicit re-statement that callers are trusted) before this API
  gains a caller that accepts less-trusted input than "output of
  `parse_strict_json`." Deferred to 136H, which is the first phase
  expected to give this API a real caller.

### `DEFERRED-136G-1` — Schema-authored ReDoS risk (catastrophic-backtracking `pattern` values)

- See §7. Out of this phase's threat model (schema resources are
  trusted-root content); explicitly flagged for the security review of
  whichever phase first authors real Stage 3 `pattern` keywords.

### `DEFERRED-136G-2` — Schema manifest implementation

- Re-confirmed, independently, that 136F's deferral decision remains
  correct: `SchemaResourceInfo` already carries every field
  (`schema_id`, `relative_path`, `dialect`, `sha256`, `size_bytes`) a
  future manifest file would need, computed deterministically at load
  time; registry integrity today correctly relies on strict local
  package enumeration, unique-`$id` rejection (§12), meta-schema
  checking (§9), deterministic ordering (§11), and an explicitly
  caller-supplied trusted root (§12) — no manifest file is required for
  *this phase's* correctness, and none was implemented here. Classified:
  correctly deferred to the first schema-core implementation phase, not
  a Blocking gap in 136F or 136G.

---

## 15. No-authority verification

Independently re-derived, not merely re-read:

- **AST/text scan for authority-related identifiers**
  (`pcae.cltr`, `current_authority`, `authority_state`,
  `authority_epoch`, `cltr-authority`) across every `.py` file in
  `schema_runtime`/`schema_resources`: zero matches (136F's own test,
  independently re-run and passing unmodified).
- **Dynamic-import defeat attempt.** 136F's own doc explicitly flagged
  this as an open item for 136G: "verify the AST/text-scan proofs ...
  cannot be defeated by dynamic imports (`importlib.import_module` with
  a computed string) that a static scan would miss." Independently
  scanned every source file in both packages for
  `importlib.import_module`, `__import__(`, `getattr(sys.modules`,
  `exec(`, and `eval(`: **zero matches** — there is no dynamic-execution
  mechanism at all in this code today, not merely one that currently
  resolves to something benign. `test_136g_no_dynamic_import_mechanism_exists_to_defeat_static_ast_scan`.
- **On-disk authority-namespace absence**, independently re-checked at a
  wider scope than 136F's own test: recursively scanned all of `.pcae/`
  for any filename containing `cltr-authority`, `current-authority`,
  `authority-pointer`, or `authority-epoch` — zero matches
  (`test_136g_no_authority_pointer_files_exist_anywhere_under_pcae_dir`).
- **No premature production wiring.** Independently grepped the entire
  `src/pcae/` tree (outside `schema_runtime`/`schema_resources`
  themselves) for any reference to `schema_runtime` or `schema_resources`:
  **zero matches** — no CLI command, no other module, nothing anywhere
  else in the production codebase references this infrastructure at
  all. It is genuinely inert, unwired infrastructure, exactly as 136F
  claimed.
- **No environment/cwd-based path override.** Independently grepped both
  packages for `os.environ`, `getenv`, `os.getcwd`, `Path.cwd`: zero
  matches — production resource roots must always be explicit,
  caller-supplied `Path` arguments; no implicit override channel exists.
- **`pcae runtime inspect` reconfirmed** (fresh run, this phase):
  Runtime state `Observed`, maximum capability `observe`, execution
  availability `unavailable` — unchanged from the pre-136G baseline.
- **Filesystem-mutation proof** (§17 below) independently confirms zero
  `.pcae/`/`schemas/`/`tasks/` mutation from any exercised code path.

Schema validity is never surfaced as authority validity anywhere in this
package: `ShapeValidationResult`'s only fields are `status`, `schema_id`,
`issues` (independently reconfirmed via
`__dataclass_fields__` inspection, 136F's own test, re-run unmodified) —
no `authoritative`, `cutover_eligible`, `publication_verified`, or
`recovery_complete` field exists anywhere in the models.

**Verdict: CONFIRMED — no-authority boundary holds, including against
the specific dynamic-import defeat scenario 136F's own doc flagged as
untested.**

---

## 16. No-execution verification

Independently re-scanned (AST import scan + AST call-site scan,
136F's own tests re-run unmodified) for `subprocess`, `socket`,
`shlex`, `http.client`/`http.server`, `urllib.request`, `urllib3`,
`requests`, `ftplib`, `telnetlib`, `smtplib`, `subprocess.run/call/Popen`,
`os.system`, `os.popen`: zero matches anywhere in
`schema_runtime`/`schema_resources`. Independently re-scanned for
`eval(`/`exec(`/dynamic `__import__` (§15): zero matches. No plugin
invocation, no backend call, no commit/push authority, and no Telegram
inbound behavior exists in either package (confirmed by the same
zero-match scans; there is no code path that could reach any of these
mechanisms since none of the underlying primitives are imported).

`pcae runtime inspect`, freshly re-run in this phase: Runtime state
`Observed`, maximum capability `observe`, execution availability
`unavailable` — unchanged.

**Verdict: CONFIRMED.**

---

## 17. Filesystem-mutation verification

Independently snapshotted (`mtime_ns`, `size`) `.pcae/`, `schemas/`,
`tasks/`, `PROJECT_STATUS.md`, and `CHANGELOG.md` before and after
exercising a representative cross-section of operations: strict
parsing of a duplicate-key document, registry construction, a
`VALID` shape-validation call, an `INVALID` shape-validation call, and
an `unknown_schema` infrastructure-failure call. Snapshots were
byte-for-byte identical before and after
(`test_136g_parsing_and_validation_do_not_mutate_repository_state`).
Temporary test files were created only inside pytest's own `tmp_path`
fixture directories, never inside the repository tree.

**Verdict: CONFIRMED.**

---

## 18. Generic-schema-only verification

Repository-wide search (independently re-run, not reused from 136F):
no `schemas/cltr_cutover/` directory exists; no filename anywhere
contains `authority_epoch`, `authority_state`, `cutover_request`, or
`readiness_package` (the one legitimate hit for these terms across the
whole repository is this phase's own planning-document references inside
`docs/PHASE_136_STAGE_3_...md`, which is prose, not a schema or fixture);
`src/pcae/schema_resources/` contains only `smoke/generic_smoke_record.schema.json`,
unchanged by this phase; `tests/fixtures/schema_runtime_136g/` (this
phase's own new fixtures) contains only generic, non-Stage-3-named
schemas (`feature_matrix.schema.json`, `no_schema_field.schema.json`).
No Stage 3 fixture, typed model, or semantic validator was created.

**Verdict: CONFIRMED.**

---

## 19. Test evidence

| Suite | Result |
|---|---|
| 136F's own focused suite (`tests/test_schema_runtime_{json_parser,loader,registry,validation,boundaries,packaging}.py`) | **69 passed** (unmodified except by the two repairs' incidental effects, none of which altered any 136F assertion) |
| 136G independent adversarial suite (`tests/test_schema_runtime_136g_independent_verification.py`) | **68 passed** |
| Combined `tests/test_schema_runtime_*.py`, non-`slow` | **134 passed, 3 deselected** |
| Combined `tests/test_schema_runtime_*.py`, `slow`-marked packaging (wheel/sdist/installed-venv) | **3 passed** |
| **Total schema_runtime suite** | **137 passed, 0 failed** |
| Fast Green (`-m fast_green -n auto`) | **4391 passed** — identical to the 136F baseline, confirming zero regressions from either repair |
| Full unmarked suite (`-n auto`, freshly run this phase, this environment) | see §20 |

All of the above were run **after** both repairs were applied, on this
phase's own environment (Python 3.9.6 project `.venv`), not merely
inherited from 136F's own prior run.

---

## 20. Full-suite baseline classification

Freshly ran `python -m pytest -n auto -q` in this phase's own environment
(Python 3.9.6, project `.venv`, both 136G repairs applied) —
**20196 passed, 19 failed, 20215 total, 1122.39s (0:18:42)**.

20196 is exactly 68 more than 136F's own reported 20128 passed —
precisely the count of new tests this phase added
(`tests/test_schema_runtime_136g_independent_verification.py`),
independent confirmation that no other test's pass/fail status shifted.

All 19 failing node IDs are **byte-for-byte identical** to the 19 node
IDs 136F's own report already classified and independently reproduced
against an isolated pre-136F worktree:
`test_advisory_runtime_contract.py::test_no_new_directory_added_for_advisory`,
`test_advisory_runtime_architecture.py::test_no_new_directory_added_for_advisory`,
`test_phase_reports.py::TestPhase128B1NotificationDispatchReliabilityRepair::test_public_reconciliation_requires_report_marker_checkpoint_and_receipt`,
`test_rendering_134e5.py::test_current_report_generation_remains_unchanged`,
`test_finalization_transaction_134e10.py` (5 tests:
`TestEndToEndTransaction::test_gate_passing_report_completes_all_stages_and_invokes_callback`,
`TestPrePromotionGatingIsAuthoritative::test_receipt_creation_happens_only_after_promote_and_dispatch_returns`,
`TestResumability::test_second_call_for_same_certified_content_does_not_reinvoke_callback`,
`TestResumability::test_distinct_certified_content_does_not_collide_with_prior_completion`,
`TestExternalDeliveryIsolation::test_transaction_delivery_step_uses_recording_adapter_only`),
`test_cltr_migration_135p_verification.py::TestFourEntryPointsThroughRealFinalizationBoundary::test_migration_evidence_recovery_classification_for_each_entry_point`
(4 parametrized cases: `task_finish`, `phase_complete`,
`phase_report_create`, `notify_send_report`),
`test_bootstrap_todo_consistency.py` (2 tests:
`test_real_todo_no_longer_marks_90_series_as_next`,
`test_real_todo_current_roadmap_lists_recommended_phase_as_next`),
`test_cltr_135o_integration.py` (4 tests:
`TestDisabledByDefault::test_no_migration_evidence_directory_created`,
`TestEnabledStage1::test_migration_evidence_produced_for_phase_complete`,
`TestEnabledStage1::test_legacy_authority_still_completed_transaction`,
`TestEnabledStage1::test_migration_failure_does_not_block_production_completion`).

Every one of the 19 assertion failures independently observed in this
phase's fresh run reproduces the exact same assertion mismatch 136F's
own report already documented (e.g. the `test_cltr_135o_integration.py`
and `test_cltr_migration_135p_verification.py` failures all assert
`result.status == "completed"` against an actual status of
`completed_receipt_best_effort_incomplete`; the `test_bootstrap_todo_consistency.py`
failures assert a stale roadmap phase ID (`132F`) still appears in
`tasks/TODO.md`'s "Next" marker — a pre-existing `tasks/TODO.md`
staleness issue unrelated to `schema_runtime`, already true before
136F). None touch `schema_runtime`/`schema_resources`, strict JSON
parsing, packaging, or any file this phase or 136F changed.

**Classification: all 19 are inherited, pre-existing, unrelated
failures — zero new regressions.** This phase did not re-run 136F's own
isolated-pre-136F-worktree reproduction a second time (136F already
performed and documented that independent reproduction); instead, this
phase independently re-derives the same failure set directly, in a
fresh full-suite run, in this phase's own environment, after applying
both of this phase's own repairs — the byte-for-byte node-ID and
assertion-message match against 136F's own independently-reproduced set
is itself the independent confirmation that nothing regressed.

---

## 21. Independent reconciliation (read-only)

Re-ran (read-only, `Mutation: none (inspection only)`, exactly as 136F's
own report did, without redispatching or mutating any prior phase):

| Phase | Status | Marker | Checkpoint | Receipt |
|---|---|---|---|---|
| 136A | conflict | not_dispatched | completed | finalized |
| 136B | not_delivered | not_dispatched | completed | finalized |
| 136C | not_delivered | not_dispatched | completed | finalized |
| 136D | not_delivered | not_dispatched | completed | finalized |
| 136E | not_delivered | not_dispatched | completed | finalized |
| 136F | **reconciled** | already_dispatched | completed | finalized |

136D's and 136E's own frozen report text (written at their own
finalization time) claimed `reconciled`/`already_dispatched`, but a
fresh, independent `pcae phase-report reconcile` call today observes
`not_delivered`/`not_dispatched` for both. This is **not a new
discrepancy** — 136E's own report (`docs/PHASE_136_STAGE_3_..._IMPLEMENTATION_PLAN.md`)
already disclosed the identical pattern for 136C ("136C claimed
`reconciled`, both 136D and this phase's own re-check observe
`not_delivered`... classified as incomplete bookkeeping in 136C's own
freeze-time narrative, not a change in underlying evidence"). This
phase's own independent re-check confirms the same pattern now extends
to 136D and 136E as well, consistent with notification-marker state
drifting/resetting over time rather than any phase's underlying
completion evidence changing. Per the explicit instruction not to
mutate or redispatch prior phases, this is disclosed here, not repaired.
136F itself reconciles cleanly (`reconciled`/`already_dispatched`),
confirming exactly one promoted 136F report generation and exactly one
ordinary delivery.

No Stage 3 schema, authority namespace, or authority pointer exists.
Production authority remains legacy (§15).

---

## 22. Limitations

- Python 3.10–3.13 were not available on this machine and were not
  tested (§4), consistent with 136F's own disclosed limitation.
- TOCTOU filesystem races are not eliminated by the loader's synchronous
  API (§8) — disclosed, not a regression from 136F.
- `DEFAULT_MAX_RECORD_DEPTH` (150) and `DEFAULT_MAX_NESTING_DEPTH` (200)
  are empirically-derived conservative constants, not formally proven
  bounds against every possible CPython build/platform stack-frame cost
  or every possible future recursive schema shape (§14,
  `BLOCKING-136G-1`/`-1b` residual risk).
- ReDoS risk from schema-authored `pattern` regexes is explicitly out of
  this phase's threat model and deferred (§14, `DEFERRED-136G-1`).
- The `Mapping` contract for `validate_record_shape` remains
  documentation-only (§14, `PREREQUISITE-136G-1`), deferred to 136H.
- This phase did not attempt to reproduce 136F's own claimed 19
  pre-existing full-suite failures against a *second* independent
  pre-136F worktree; §20's fresh full-suite run instead independently
  re-derives the current failure set directly in this phase's own
  environment and classifies it against the same historical baseline
  136F itself used.

---

## 23. Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR COMPANION EXECUTABLE
SCHEMA SHARED CORE.**

Two genuine Blocking-class defects were independently discovered
(uncaught `RecursionError` in both the strict parser and the shape
validator; a fail-open `max_issues=0` misclassification), both repaired
within the generic schema-runtime boundary, both covered by new
regression tests, with zero regressions in Fast Green or the existing
136F focused suite. Several additional findings were disclosed as
non-blocking (dead error-vocabulary codes narrowed from three to two;
inconsistent dependency-failure exception wrapping; a fail-closed
usability quirk with unresolved symlinked trusted roots) or explicitly
deferred to the next phase (`PREREQUISITE-136G-1`, the `Mapping` runtime
contract; `DEFERRED-136G-1`, ReDoS threat modeling; `DEFERRED-136G-2`,
manifest implementation, reconfirmed correctly deferred). None of the
disclosed non-blocking findings represents an unbounded path, a
network-access path, an authority leak, or a production-state mutation.

**Legacy lifecycle remains the sole production authority. CLTR remains
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
unavailable.**

---

## Recommended next phase

**136H — Companion Executable Schema Shared Core Implementation.** Per
136E's roadmap and this phase's own repair record, 136H may implement
only: shared schema definitions; identifiers; digests; references;
timestamps; limitations; disclosures; enums; a schema manifest
foundation; fixtures and tests for that shared core. It must not
implement authority-bearing record schemas, and should explicitly
re-derive `DEFAULT_MAX_RECORD_DEPTH`/`DEFAULT_MAX_NESTING_DEPTH` against
its own actual schema shapes (§14 residual risk) and make a deliberate
decision about `PREREQUISITE-136G-1` (the `Mapping` runtime contract)
before giving `validate_record_shape` its first real caller.
