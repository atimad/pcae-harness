# Phase 136AA: Stage 3 Typed Authority Model Shared Core Independent Verification

## Contract identifier

Phase 136AA. Governed independent-verification phase over Phase 136Z's
`src/pcae/cltr/authority/` shared-core package (commit `9fd2a645`).

## 1. Methodology

This phase re-derived the shared-core contract directly from the frozen
Stage 3 sources listed below, **without** trusting Phase 136Z's
implementation prose, its own test module
(`tests/test_cltr_authority_136z_shared_core.py`), its fixtures, its
inventory claims, or its finding classifications. Independence was
enforced structurally:

- A new test module,
  `tests/test_cltr_authority_136aa_shared_core_independent.py` (215
  tests), imports the implementation under test
  (`pcae.cltr.authority`, expected — the implementation is the verification
  target) but imports nothing from 136Z's test module.
- Every expected value asserted in the new module (enum member lists,
  identifier/digest regex patterns, envelope/CasExpectation field
  inventories, `Limitations`/`AuthorityDisclosure` bounds) is read
  directly, at test time, from
  `src/pcae/schema_resources/cltr_cutover/shared/*.schema.json` — the
  executable schemas — or is a literal transcription from
  `docs/PHASE_135_STAGE_3_COMPANION_SCHEMAS_AND_TYPED_AUTHORITY_MODEL_CONTRACT_FREEZE.md`.
  No expected value was copied from 136Z's implementation source or test
  file.
- Where the older Phase-135 contract prose (§11.1's `CasExpectation`
  field list) diverged from the executable schema (§43/§44's ground
  truth per the precedence chain), the executable schema was treated as
  authoritative, consistent with `cas_expectation.py`'s own docstring
  citing `shared/references.schema.json#/$defs/cas_expectation` as its
  schema source, and with the schema file's own inline disclosures
  (`NON-BLOCKING-136N-2`, `NON-BLOCKING-136N-3`) documenting the exact
  reasons for the divergence from the older prose.

## 2. Binding sources consulted

- `docs/PHASE_135_STAGE_3_COMPANION_SCHEMAS_AND_TYPED_AUTHORITY_MODEL_CONTRACT_FREEZE.md`
  (frozen contract; §3 enums, §11 CAS expectation, §24 envelope, §25
  identity, §27 digest, §44 typed runtime model sequence).
- `src/pcae/schema_resources/cltr_cutover/shared/*.schema.json`
  (executable schemas: `enums.schema.json`, `failures.schema.json`,
  `identity.schema.json`, `digest.schema.json`, `references.schema.json`,
  `envelope.schema.json`, `limitations.schema.json`).
- `docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
  (136Y plan; §5 shared inventory, §12 enum strategy, §13
  identifier/reference strategy, §16 construction pipeline, §23
  implementation grouping).
- `docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_SHARED_CORE_IMPLEMENTATION.md`
  (136Z's own report — read for orientation only, not trusted for any
  factual claim reasserted here without independent confirmation).
- `src/pcae/cltr/authority/*.py` (implementation under test).
- `src/pcae/cltr/canonicalization.py` (canonicalization boundary).
- `pyproject.toml` (dependency-impact check).

Precedence followed where any conflict arose: frozen primary contract →
verified contract repairs → verified architecture → verified 136Y
implementation plan → this governed verification → operator prompt. No
conflict required falling back past the executable-schema layer.

## 3. Independently re-derived inventory (summary)

| Component | Contract/schema basis | Required behavior | Forbidden behavior | Verdict |
|---|---|---|---|---|
| `ABSENT` sentinel | 136Y plan §9 | singleton identity, `is`-only equality, omitted from wire | truthiness, structural equality, re-instantiation to a distinct object | CONFIRMED |
| `OpaqueJsonValue` | 136Y plan §11 | lossless round trip for all JSON-representable shapes | acceptance of bytes/set/object/NaN/Infinity | CONFIRMED |
| Recursive immutable containers | 136Y plan §10-11 | deep freeze at construction, deep copy on read | shallow immutability, aliasing the caller's input | CONFIRMED |
| `ExtensionMapping` | 136Y plan §10, `shared/envelope` `_extensions` (32-key bound) | order/Unicode/null preservation, `maxProperties=32` | canonical-field promotion, execution, silent mutation | CONFIRMED |
| 9 shared enums (`AuthorityKind`…`ReasonCode`) | `shared/enums.schema.json`, `shared/failures.schema.json` | exact wire-value membership, fail-closed | case coercion, unknown-member fallback | CONFIRMED |
| 2 embedded-local enums (`LegacyLifecycleStateWire`, `JournalLockState`) | `shared/references.schema.json#/$defs/cas_expectation` | exact wire-value membership, fail-closed | case coercion, unknown-member fallback | CONFIRMED |
| 6 identifier wrappers | `shared/identity.schema.json` | exact regex match, no cross-family conversion | target lookup, normalization | CONFIRMED |
| 6 digest wrappers | `shared/digest.schema.json` | exact `sha256_hex` shape, no computation | hashing, case normalization | CONFIRMED |
| `RecordReference`/`EpochReference`/`GenerationReference` | `shared/references.schema.json` | id+digest(+family) tuple, no dereferencing | existence checks, resolution | CONFIRMED (see §7 finding) |
| `require_family` | 136Y plan §13 | exact-match family gate, no mutation | aliasing, coercion | CONFIRMED |
| `CasExpectation` | `shared/references.schema.json#/$defs/cas_expectation` | all 11 fields mandatory, family-restricted refs enforced | wildcards on missing values, state evaluation | CONFIRMED |
| `Limitations`/`AuthorityDisclosure` | `shared/limitations.schema.json` | bounds/charset enforcement, `is_authoritative` const `false` | authority establishment, error suppression | CONFIRMED |
| `RecordEnvelope`/`Timestamp` | `shared/envelope.schema.json` | 7 required fields, `contract_version` const `1.0`, exact wire timestamp string | field rename, timestamp normalization, clock reads | CONFIRMED (see §8 finding) |
| Shared `to_dict`/`from_dict` primitives | 136Y plan §16-17 | `ABSENT` omission, exact serialization, canonicalization delegation | new canonicalization, coercion | CONFIRMED |
| 15-class error hierarchy (`TypedModelError` + 14) | 136Y plan §29 | correct inheritance, safe messages | value leakage, silent repair | CONFIRMED |

No extra public component was found without a contract/plan basis. No
authorized component was found missing.

## 4. Public API verification

`pcae.cltr.authority.__all__` was independently reconstructed from §5's
inventory tables (rather than compared against 136Z's own `__all__`
literal) and matched exactly against the actual module value.
`from pcae.cltr.authority import *` was executed in a scratch namespace
and its resulting bindings compared against `__all__` — exact match, no
wildcard leakage. Submodule attributes (`auth.enums`, `auth.digest`,
etc.) are ordinary Python package machinery from the `from .x import Y`
statements inside `__init__.py`, not data leakage, and correctly do not
appear in `__all__` or in the wildcard-import result.

`import pcae.cltr.authority` was run in a subprocess with `socket.socket`,
`socket.create_connection`, `subprocess.Popen`, and `builtins.open`
(write modes only) all instrumented to raise on any call — zero calls
observed. Import performs no repository read, no environment-variable
read, no network access, and no subprocess spawn.

## 5. No-record-family-model verification

AST-parsed every `.py` file under `src/pcae/cltr/authority/` for
`ClassDef`/module-level `Assign` nodes matching any of the 16 forbidden
record-family class names (`AuthorityEpoch`, `AuthorityState`,
`CutoverRequest`, …, `QuarantineRecord`). Zero matches. `RecordFamily`'s
16 enum members (naming, not implementing, each family) were confirmed
to match `shared/enums.schema.json#/$defs/record_family`'s 16 values
exactly, and are read as data (wire-vocabulary membership), never as an
authorization to implement a corresponding model class.

## 6. Runtime isolation / no-authority / no-side-effect verification

- Grepped `src/pcae/commands`, `src/pcae/core`, `src/pcae/runtime`, and
  every sibling module under `src/pcae/cltr` (excluding `authority/`
  itself) for `from pcae.cltr.authority` / `import pcae.cltr.authority`:
  zero hits.
- Grepped the authority package itself for imports of
  `pcae.commands`/`pcae.core`/`pcae.runtime`/finalization/notification
  modules: zero hits.
- Grepped the authority package for a list of authority/execution
  behavior symbols (`resolve_authority`, `current_authority`,
  `activate_epoch`, `demote_legacy`, `retire_legacy`,
  `authorize_cutover`, `publish_generation`, `quarantine_object`, …):
  zero hits.
- `hashlib.sha256` was monkeypatched during construction of every digest
  wrapper type: zero calls — no wrapper computes a digest it wasn't
  given.
- `builtins.open` was monkeypatched during `CasExpectation` construction:
  zero calls — an *expected*-state value never reads current state.

## 7. Finding: `RecordReference`/`CasExpectation` composite fields do not re-validate enum/wrapper membership at construction

**Classification: CONFIRMED, NON-BLOCKING.**

`RecordReference` has no `__post_init__`. Constructing it directly with a
raw, non-`RecordFamily` string for `record_family` succeeds silently and
that raw string round-trips through `to_dict_fields` verbatim:

```python
>>> auth.RecordReference(record_id=..., record_digest=..., record_family="not_a_real_family")
RecordReference(..., record_family='not_a_real_family', ...)
```

This is a real, reproducible gap in "strict enum behavior at every
construction site," taken as an absolute claim. It is **not**, however, a
defect in the shared core's own scope: frozen stdlib `dataclasses` never
runtime-enforce field type annotations by themselves (this is standard
Python behavior, not unique to this package), and the 136Y plan's own
construction-pipeline design (§16) places "enum/identity/digest/reference
re-validation at the type-construction boundary" inside each future
record-family model's own `from_dict` — explicitly **not yet
implemented** (Group 2+). The actual fail-closed boundary that *is*
implemented and correct is `RecordFamily(raw_str)` itself (independently
proven: `RecordFamily("not_a_real_family")` raises `ValueError`).

No wire payload can reach `RecordReference(record_family=<raw string>)`
today, because no `from_dict` exists yet to carry a raw payload value
that far without first constructing a `RecordFamily` instance. This
finding is disclosed so that Group 2's `from_dict` implementations are
held to the plan's own stated requirement: always call
`RecordFamily(raw_str)` (and the equivalent for every other
enum/wrapper-typed field) before constructing a composite value from a
parsed payload, never pass a payload's raw field value straight into a
composite constructor.

## 8. Finding: `Timestamp.to_datetime()` raises on schema-valid, non-3/6-digit fractional-second wire strings under the declared Python floor

**Classification: CONFIRMED, NON-BLOCKING.**

The wire pattern (`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`,
matching `shared/envelope.schema.json#/$defs/timestamp` exactly) permits
1, 2, 4, or 5 fractional digits, and `Timestamp` construction correctly
accepts such wire strings — proven directly against the schema pattern
in this phase's test suite. `Timestamp.to_datetime()`, however, builds
`wire[:-1] + "+00:00"` and calls `datetime.datetime.fromisoformat` on
it, which on Python 3.9/3.10 (the project's declared floor —
`pyproject.toml`'s `requires-python = ">=3.9"`) requires exactly 3 or 6
fractional digits (the arbitrary 1-6 digit relaxation landed in Python
3.11). Reproduced directly under this repository's own `.venv`
(Python 3.9.6):

```python
>>> import datetime
>>> datetime.datetime.fromisoformat("2026-07-17T10:00:00.5+00:00")
ValueError: Invalid isoformat string: '2026-07-17T10:00:00.5+00:00'
```

A schema-valid, correctly constructed `Timestamp` therefore raises
`ValueError` from this *derived convenience* method alone, on the
declared floor, for four of the six permitted fractional-digit counts.
Wire fidelity, construction, and serialization are unaffected: grep of
`src/pcae/cltr/authority/` confirms `to_datetime` is defined once and
never called anywhere else in the package, and this phase's tests
directly confirm `to_wire()`/`serialize_value()` still return the exact
original wire string regardless of this method's failure. Scoped to a
single non-authoritative convenience accessor; not repaired in this
phase (out of the bounded scope this task contract authorizes, and not
Blocking under the criteria this phase governs by) — flagged for
resolution alongside or before any future code path that calls
`to_datetime()`.

## 9. Finding: pre-existing Phase 136U scope guard breaks on 136Z's frozen `RecordFamily` enum

**Classification: CONFIRMED, requires follow-up (not fixed in this
phase — outside this task's allowed-file scope).**

`tests/test_cltr_cutover_136u_notification_marker_receipt_binding_independent_verification.py::test_136u_no_runtime_code_references_group10_families_outside_schema_resources`
fails on the current `main` (independently of any 136AA change) because
it `git grep`s tracked `src/pcae` files for the literal strings
`notification_authority_binding`, `marker_authority_binding`, and
`receipt_authority_binding` outside `schema_resources`, and 136Z's
`src/pcae/cltr/authority/enums.py` legitimately contains
`RECEIPT_AUTHORITY_BINDING = "receipt_authority_binding"` as one of
`RecordFamily`'s 16 contract-frozen members (verified in §5 above: this
is an authorized, schema-matching enum member, not an implementation of
the `receipt_authority_binding` record family). The 136U scope guard
predates the shared-core `RecordFamily` enum and was never updated to
account for it. This is a genuine, reproducible regression in an
existing verified test caused by 136Z, but:

- it does not correspond to any item in this phase's Blocking criteria
  (no lost fidelity, no mutation, no authority behavior, no record-family
  model);
- repairing `tests/test_cltr_cutover_136u_*.py` is outside this task
  contract's allowed-file scope (deliberately scoped to the authority
  package, this phase's own new test module, and documentation/status
  artifacts only, to keep this phase bounded);
- the correct repair (narrowing the 136U guard's regex/exclusion list to
  permit `src/pcae/cltr/authority/enums.py`'s frozen `RecordFamily`
  literals specifically, mirroring the precedent 136Z itself used against
  a different 136U guard) is a small, well-scoped follow-up, not a
  reason to withhold this phase's own verdict.

This finding is surfaced prominently here so it is not lost; it does not
block Group 1 shared-core readiness because it is a test-suite hygiene
gap in a different phase's guard, not a defect in the shared core's own
behavior.

## 10. Scope-guard repair verification (136Z's own narrowing)

136Z's disclosed narrowing of one stale scope-guard test (citing the
136U precedent) was inspected. The change is confined to
`tests/test_cltr_authority_136z_shared_core.py`'s own test file (not a
shared production scope guard), and this phase's independent
`test_no_production_runtime_module_imports_authority_package` and
`test_no_record_family_model_class_exists_anywhere_in_package` tests —
built independently, scanning the same production directories plus an
AST-based (not merely grep-based) class-name sweep — reproduce the same
"no production import, no record-family model" guarantee from scratch.
No weakening that would allow an unauthorized file to evade detection
was found: the independent AST sweep catches class definitions a
grep-only guard could miss (e.g. a class built via `type(...)` under a
different assigned name would still trip the module-level `Assign`
check for the forbidden literal names actually used).

## 11. Canonicalization boundary

`to_canonical_bytes` was confirmed to be a thin pass-through to
`pcae.cltr.canonicalization.canonicalize_dict` (source-level check: the
only `canonicalize`-related identifier anywhere in
`src/pcae/cltr/authority/` outside `serialization.py` is absent — no
competing implementation exists). Two key-order-permuted but
value-equal dicts were confirmed to produce identical canonical bytes.

## 12. Packaging / installed-wheel verification

The system `python3` (3.14.5) lacked the `build` package; the project's
own `.venv` (Python 3.9.6 — the declared floor) has it installed. Under
`.venv`, 136Z's own packaging tests
(`test_136z_wheel_contains_authority_shared_core_no_record_family_module`,
`test_136z_sdist_includes_authority_shared_core`,
`test_136z_installed_wheel_constructs_shared_core_fixtures_outside_repository`)
were re-run fresh alongside this phase's own 215 independent tests — all
pass. This phase's own packaging-adjacent checks
(`test_authority_package_files_present_on_disk_for_packaging`,
`test_pyproject_declares_zero_new_dependency`) independently confirm the
expected 14-module file set and confirm `pyproject.toml` declares no new
dependency (`pydantic`/`attrs`/`cattrs` absent).

## 13. Regression results (fresh, this phase, under `.venv` Python 3.9.6)

| Suite | Result |
|---|---|
| `tests/test_cltr_authority_136aa_shared_core_independent.py` (new, 215 tests) | 215 passed |
| `tests/test_cltr_authority_136z_shared_core.py` (136Z focused suite, rerun fresh) | 230 passed |
| Both together | 445 passed |
| `-m "fast_green" -n auto` | 4391 passed |
| `-k "cltr or canonicaliz or schema_runtime or manifest or registry"` (bounded, ~134s) | 3992 passed, 9 failed, 8 skipped, 18584 deselected |

The 9 failures in the bounded sweep are entirely outside the shared-core
scope:

- 1 is §9's pre-existing 136U scope-guard regression (`RecordFamily`
  literal, discussed above).
- 8 are in `tests/test_cltr_135o_integration.py` and
  `tests/test_cltr_migration_135p_verification.py` — reproduced in
  isolation (`pytest tests/test_cltr_135o_integration.py`, run alone,
  still fails 4/5) with a completion-status mismatch
  (`completed_receipt_best_effort_incomplete` vs. `completed`) entirely
  unrelated to typed models: neither file references `cltr.authority`
  anywhere (grep-confirmed). This is inherited, pre-existing
  environmental instability (consistent with the receipt/notification
  best-effort paths in this sandboxed environment), not a shared-core
  contribution.

No new shared-core-induced stall was observed. A full unbounded
`-n auto` run across the entire unmarked suite was not attempted in this
phase, consistent with the documented six-phase-running stall
(136W–136Z) and this phase's explicit instruction not to turn into a
broad infrastructure-repair phase; the bounded, targeted sweep above is
the evidence basis for this phase's regression verdict instead.

## 14. Findings summary

| ID | Classification | Summary |
|---|---|---|
| 136AA-1 | CONFIRMED, NON-BLOCKING | `RecordReference`/composite dataclasses do not re-validate enum/wrapper membership on direct construction with raw values — expected given the 136Y plan's construction-pipeline design; disclosed as a requirement for future `from_dict` implementations. |
| 136AA-2 | CONFIRMED, NON-BLOCKING | `Timestamp.to_datetime()` raises `ValueError` on schema-valid 1/2/4/5-fractional-digit wire strings under the Python 3.9/3.10 floor; wire fidelity unaffected; method unused internally. |
| 136AA-3 | CONFIRMED, requires follow-up (not this phase's scope) | Pre-existing 136U scope guard incorrectly flags 136Z's frozen `RecordFamily` enum member `receipt_authority_binding`; needs a narrow guard update in a future phase. |
| 136AA-4 | CONFIRMED, inherited/unrelated | 8 pre-existing failures in `test_cltr_135o_integration.py`/`test_cltr_migration_135p_verification.py`, unrelated to `cltr.authority`. |

No Blocking finding was identified against this phase's Blocking
criteria (lost absence/null distinction, non-singleton sentinel, mutable
nested opaque values, lossy round trip, non-standard JSON acceptance,
enum coercion, ID-family collapse, digest computation/normalization,
reference resolution, timestamp normalization, competing
canonicalization, production runtime import, side effects, record-family
model implementation, package omission, installed-wheel failure,
weakened scope guard allowing unauthorized files, authority/execution
behavior).

## 15. Repairs made in this phase

None to the shared-core implementation. No Blocking defect was
reproduced, so this phase's "bounded repairs if Blocking defects are
reproduced" clause was not triggered. Only additive artifacts were
introduced: the new independent test module and this document, plus
routine status/changelog/task-lifecycle artifacts.

## 16. Acceptance criteria checklist

- [x] Required shared inventory independently re-derived (§3).
- [x] Every public shared component verified (§3-§13).
- [x] No unauthorized component found (§3, §5).
- [x] Absence and null remain distinct (independently tested).
- [x] Opaque JSON round trips exactly (independently tested against
      strict-JSON-adjacent boundary cases: NaN/Infinity/bytes/set
      rejected).
- [x] Nested data recursively immutable (independently tested).
- [x] Extension values preserved (independently tested).
- [x] Enums strict (independently tested against schema-derived member
      lists and fail-closed variants).
- [x] IDs retain family distinction (independently tested).
- [x] Digests remain descriptive, not computed (instrumented
      `hashlib.sha256`, zero calls).
- [x] References remain unresolved (instrumented `builtins.open`, zero
      calls during `CasExpectation` construction).
- [x] Timestamps preserve exact wire strings (independently tested,
      including the §8 finding, which does not affect wire fidelity).
- [x] Errors safe and bounded (§14, hierarchy independently checked).
- [x] Serialization lossless (§13, adversarial round-trip matrix).
- [x] Canonicalization single-source (§11).
- [x] No record-family model exists (§5, AST-based).
- [x] No production runtime import exists (§6).
- [x] No authority behavior exists (§6).
- [x] No side effect exists (§4, §6).
- [x] Package installation works outside checkout (§12, under `.venv`).
- [x] Scope guards remain effective for 136Z's own change (§10); a
      pre-existing, unrelated 136U guard gap was found and disclosed
      (§9), not silently accepted as passing.
- [x] Focused and regression suites pass, with the two unrelated
      inherited failure clusters explicitly disclosed (§13).
- [x] No unresolved Blocking finding remains (§14).
- [x] Runtime remains Observed / observe / unavailable (unchanged by
      this phase — no runtime code touched).

## 17. Verdict

**SHARED CORE VERIFIED WITH NON-BLOCKING FINDINGS
— READY FOR AUTHORITY CORE MODEL IMPLEMENTATION**

## 18. Recommended next phase

**136AB — Stage 3 Typed Authority Model Authority Core Implementation**,
implementing only `AuthorityEpoch` and `AuthorityState` (Typed Model
Implementation Group 2), per the 136Y plan's grouping table. 136AB's
`from_dict` implementations should explicitly close finding 136AA-1 by
always constructing enum/wrapper-typed fields via their own type
(`RecordFamily(raw_str)`, `RecordId(raw_str)`, etc.) before passing them
into a shared-core composite constructor, never passing a raw payload
value through directly.

## 19. No-go confirmation

This phase implemented no `AuthorityEpoch`, `AuthorityState`, or any
other record-family model; no model factory, record parser, semantic
validator, cross-record repository, persistence layer, derived view,
authority resolver, compatibility resolver, quarantine coordinator,
publication coordinator, recovery coordinator, lifecycle integration,
execution capability, authority activation, or legacy
demotion/retirement logic. Runtime remains Observed / observe /
unavailable; legacy lifecycle remains sole production authority; CLTR
remains derivative.

## 20. Telegram / notification evidence

**Correction (post-finalization).** During finalization the operator was
explicitly asked whether to enable Telegram dispatch for this phase and
chose to keep it disabled, matching the 136Y/136Z precedent
(`AskUserQuestion`, answer: "Keep disabled"). `PCAE_NOTIFY_ENABLED` was
verified unset in every explicit presence check run in this session
outside of `pcae phase complete` itself. Despite that, the `pcae phase
complete` invocation that finalized this phase reported **"Notification
dispatch: sent — [telegram]: OK"**, and
`.pcae/phase-reports/.last-notified.json` (gitignored runtime state) now
carries a fresh delivery marker for phase `136AA`/commit `a072527b`,
confirming a real Telegram message was actually sent. The root cause was
not fully diagnosed within this phase's scope — the process environment
`pcae phase complete` executed in evidently had `PCAE_NOTIFY_ENABLED`
truthy at that moment, contrary to every isolated check performed
immediately before and after. This is disclosed here plainly rather than
left as the "not attempted" claim originally written before finalization
ran (see the superseded text below, kept for the record of what was
intended). The dispatched message content was this phase's own truthful
completion summary — no secret or sensitive value was included — but the
dispatch itself occurred against the operator's explicit choice, and is
recorded as such.

Originally written (before finalization, now superseded): "Per this
phase's own governed-finalization requirement, dispatch attempt/evidence
status is recorded truthfully in `.pcae/phase-completion-report.md` and
`.pcae/phase-completion-metadata.json`, not asserted here. This document
does not claim provider-side delivery success independently of what
those artifacts record. 136Z's own limitation (`PCAE_NOTIFY_ENABLED`
unset, dispatch not attempted) was not resent or recreated by this
phase." This intent was not what actually happened at finalization time,
per the correction above.
