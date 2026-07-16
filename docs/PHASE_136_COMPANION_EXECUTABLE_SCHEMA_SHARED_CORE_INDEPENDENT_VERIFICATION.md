# Phase 136I: Companion Executable Schema Shared Core Independent Verification

## Status

Complete. Independent verification phase (not implementation).

## Summary

Phase 136I independently re-derives, reproduces, mutates, and adversarially
attacks Phase 136H's Stage 3 Companion Executable Schema shared core
(`src/pcae/schema_resources/cltr_cutover`), trusting none of 136H's own
157 tests or report prose as verification evidence. A fresh, independently
authored adversarial test module
(`tests/test_cltr_cutover_136i_shared_core_independent_verification.py`,
221 test functions/cases) re-derives every frozen count from the contract
and the on-disk files directly, attacks every identifier/digest/timestamp/
version/enum/reason-code/reference/limitation definition with boundary and
adversarial values not present in 136H's own fixtures, mutates temporary
manifest/schema copies to prove fail-closed tamper detection, attacks the
`_materialize_plain` Mapping-contract repair with a second, independently
authored hostile `Mapping`, independently builds and inspects a fresh
wheel/sdist and proves installed-wheel operation from outside the
repository, and independently re-verifies no-network/no-authority/
no-execution/non-mutation boundaries.

**Verdict: VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR AUTHORITY AND
REQUEST SCHEMA IMPLEMENTATION.**

**Legacy lifecycle remains the sole production authority. CLTR remains
derivative.** No `records/`, `bindings/`, or `views/` directory exists. No
authority-bearing record schema, typed model, semantic validator, or
authority resolver/state/pointer was created or changed by this phase.

## Methodology

Per the phase's explicit instruction, this phase did not begin from 136H's
claimed inventory. The independent derivation order was:

1. Read the frozen contract (`PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`
   Sec.4, Sec.6, Sec.8, Sec.10-16, Sec.46) and the implementation plan
   (`PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`
   Sec.7, Sec.13) to independently establish the target Group 1 inventory
   and shape contracts, before reading 136H's own implementation doc.
2. Read every on-disk shared-core file
   (`src/pcae/schema_resources/cltr_cutover/**`) directly and independently
   recomputed file counts, `$defs` counts, enum counts, reason-code counts,
   and manifest-entry counts from the JSON documents themselves, never from
   136H's report tables.
3. Read `git show --stat --summary 1547c14b` /
   `git show --name-status --format=fuller 1547c14b` to confirm the exact
   phase-owned file set.
4. Read `src/pcae/schema_runtime/{loader,registry,manifest,validation}.py`
   in full to understand the actual verification/containment/materialization
   mechanisms being attacked, independent of 136H's own prose description.
5. Authored 221 fresh adversarial test cases attacking every category listed
   in the phase brief, iterated until every test passed (nine of the
   initially authored 221 cases had incorrect *assumptions* about the code
   under test, not defects in the code; each was corrected during this
   phase and is disclosed below as either a test-authoring correction or a
   genuine finding, never silently dropped).
6. Independently built wheel/sdist, installed the wheel into an isolated
   venv outside the repository, and exercised registry/manifest loading
   from that installation with `cwd=/tmp`.
7. Re-ran the full regression matrix (136H's own 157, the combined
   `test_schema_runtime_*.py` suite, this phase's 221, packaging tests,
   Fast Green, and the full unmarked suite).

Read in full, per the phase brief's mandatory source review:
`PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`,
`PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_IMPLEMENTATION_PLAN.md`,
`PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_IMPLEMENTATION.md`, and
the relevant sections of
`PHASE_136_VALIDATION_ENGINE_AND_STRICT_JSON_PARSING_INDEPENDENT_VERIFICATION.md`
(for the `PREREQUISITE-136G-1` finding this phase's repair resolves).
`PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_INDEPENDENT_VERIFICATION.md`
(136D) was consulted for prior verification-phase methodology precedent.

## Pre-implementation reconciliation (read-only)

```
pcae phase-report reconcile --phase-id 136H
  Status: delivery_recorded_bookkeeping_incomplete
  Promoted generations: 1
  Marker: already_dispatched
  Checkpoint: completed_receipt_best_effort_incomplete
  Receipt: absent
  Mutation: none (inspection only)

pcae phase-report reconcile --phase-id 136G
  Status: not_delivered
  Promoted generations: 1
  Marker: not_dispatched
  Checkpoint: completed
  Receipt: finalized
  Mutation: none (inspection only)
```

Both commands are notification-delivery bookkeeping reconciliations, not
schema-content reconciliations. 136G's `not_delivered` status is the same
pre-existing, unrelated historical fact 136H's own report already
disclosed and did not block 136H's startup. 136H's own reconciliation
(`delivery_recorded_bookkeeping_incomplete`, receipt absent) is a newly
observed notification-delivery bookkeeping gap for 136H's own completion,
not previously disclosed in 136H's own report. It concerns Telegram
delivery/receipt bookkeeping only — it does not indicate more than one
logical 136H completion, does not indicate any schema-content defect, and
does not block 136I's schema-verification scope. Recorded here as
**NON-BLOCKING-136I-3** (see Findings). Neither reconciliation command
mutated any state; neither phase was redispatched.

## 1. Independent inventory derivation

Independently re-derived directly from the on-disk JSON documents (not from
136H's report tables), cross-checked against the frozen contract:

| Item | Independently derived | 136H's claim | Match |
|---|---|---|---|
| Shared schema files | 7 | 7 | ✅ |
| Exported `$defs` (sum) | 33 (7+8+3+1+6+4+4) | 33 | ✅ |
| Shared enums (`enums.schema.json`) | 8 (`authority_kind`, `authority_role`, `migration_stage`, `generation_role`, `publication_state`, `recovery_state`, `compatibility_mode`, `record_family`) | 8 | ✅ |
| Reason codes | 24, no duplicates | 24 | ✅ |
| Manifest entries | 7, all `implementation_group: 1`, `family: shared`, `status: frozen` | 7 | ✅ |
| Manifest digests | all 7 independently recomputed from raw file bytes via `hashlib.sha256`, all match | — | ✅ |
| Manifest `schema_id` fields | all 7 match the entry's own file's declared `$id` exactly | — | ✅ |
| Dependency graph | acyclic, every dependency resolves to a real, distinct entry's `$id` | — | ✅ |

No mismatch found. All five headline counts (7 files / 33 `$defs` / 8 enums
/ 24 reason codes / 7 manifest entries) are independently confirmed exact,
not approximate.

## 2. Scope-boundary verification

- None of the 16 forbidden authority-bearing record-schema filenames
  (`authority_epoch.schema.json` … `compatibility_state.schema.json`)
  exists anywhere under the packaged `cltr_cutover` tree.
- No `records/`, `bindings/`, or `views/` directory exists under the
  packaged root.
- No `.pcae/cltr-authority/` or repository-root `schemas/cltr_cutover/`
  path exists on disk.
- **Repository-wide** `git ls-files` scan (not scoped to the packaged
  root) confirms none of the 16 forbidden filenames is tracked anywhere in
  the repository outside documentation/status/changelog prose.

**Result: PASS.**

## 3. Draft 2020-12 / `$id` verification

- All 8 packaged resources (7 shared + `manifest.schema.json`) declare
  `"$schema": "https://json-schema.org/draft/2020-12/schema"` exactly and
  independently pass a freshly invoked `Draft202012Validator.check_schema`.
- All 8 `$id` values are unique.
- No `$ref` target is an absolute `http://` URL; every non-fragment-only
  `$ref` target resolves under the frozen `https://pcae.local/schemas/cltr_cutover/`
  namespace.
- Registry construction was proven to perform zero network calls by
  monkeypatching `socket.socket`/`socket.create_connection` to raise, then
  building the registry successfully.
- The registry rejects a duplicate `$id` both across two independent roots
  and from a manually injected duplicate-`$id` file within one root (the
  latter surfaces as `SchemaResourceError`, not `SchemaRegistryError`, at
  the `load_schema_package` layer — both are `SchemaResourceError` in the
  MRO; this phase's test asserts on either type, correcting a test-authoring
  assumption made before reading `registry.py` closely enough).

**Result: PASS.**

## 4. Identifier attacks

Independently authored boundary/adversarial cases for `record_identity`,
`migration_epoch`, `phase_identity`, `transition_identity`, and
`principal_identifier` (empty, min-1-under, exact-min, exact-max,
max-1-over, wrong case, path separators, `..`, leading/trailing
whitespace, embedded tab/newline/control characters, Unicode confusables)
all match the frozen contract's charset/length/case rules exactly — every
attack that should be rejected is rejected, every boundary-valid case is
accepted.

**Cross-family masquerade (documented limitation, not a defect):**
`record_identity` and `generation_identity` share an identical pattern and
length family by design (`shared/identity.schema.json`'s own docstring
states this explicitly: "kept as a distinct named definition so a
generation identifier can never silently masquerade as a generic
`record_id` **in a schema that composes both**"). A bare string validated
against either `$def` in isolation cannot be shape-distinguished — this is
inherent to JSON Schema's string-pattern model, not a defect in this
package, and is only actually enforced once a future `records/*.schema.json`
file composes both fields together (Layer 4 concern, correctly out of this
phase's implemented scope). Independently confirmed and recorded.

**Result: PASS**, with the above documented (non-blocking) limitation.

## 5. Digest verification

`sha256_hex` independently attacked with uppercase hex, 63/65-character
lengths, `sha256:`-prefixed form, non-hex characters, empty string,
leading whitespace, Unicode lookalike digits, `null`, and wrong scalar
types (int/float/bool/list) — every attack rejected, the canonical
64-lowercase-hex form accepted. All six semantically distinct digest
`$defs` (`record_digest`, `referenced_record_digest`, `generation_digest`,
`manifest_digest`, `pointer_digest`, `journal_entry_digest`) confirmed to
`$ref` the single shared `sha256_hex` primitive, preserving named
semantic distinction while sharing one pattern.

**Result: PASS.**

## 6. Timestamp attack

Independently confirmed the frozen pattern's exact behavior, including two
disclosed, non-repaired pattern-only limitations restated from 136C/136H:
`2026-13-01T00:00:00Z` (invalid month) and `2026-02-30T00:00:00Z` (invalid
Feb 30) are both **pattern-valid** (calendar validity is a Layer-4/5
concern, not enforced here), and `:60` (leap second) is pattern-valid per
the frozen `\d{2}` seconds pattern (`NON-BLOCKING-136C-1`, re-verified,
not repaired — the contract's own fenced code block is authoritative over
its self-contradictory prose). Numeric offset form, missing `Z`, lowercase
`z`, missing `T` separator, 7+ fractional digits, and leading/trailing
whitespace are all correctly rejected.

**Result: PASS**, with the two inherited, previously disclosed
pattern-only limitations reconfirmed, not newly introduced.

## 7. Version / schema-identity attack

`schema_version`'s `^[0-9]+\.[0-9]+$` pattern independently confirmed to
reject a missing minor component, an extra third component, prerelease
suffixes, a leading `v`, and surrounding whitespace. **Documented
limitation, independently confirmed**: the charset itself does not forbid
leading zeros (`"01.0"` is pattern-valid) — this is inherent to the frozen
pattern text itself (restated verbatim from the contract, not a 136H
deviation) and is not exploitable as an authority or identity confusion,
since `schema_version` never participates in identity/digest computation.

**Result: PASS.**

## 8. Limitations structure attack

Independently re-verified all documented bounds: empty array permitted;
32 items permitted, 33 rejected; 2000-character entry permitted,
2001-character entry rejected; empty-string entry rejected; 8 embedded
newlines permitted, 9 rejected; NUL/ESC control characters rejected, tab
permitted; non-string array items (`int`, `object`, `null`) rejected.
**Documented, independently confirmed limitation**: duplicate limitation
entries are not locally rejected by the shared definition (by the shared
definition's own explicit design — duplicate-content review is a Layer 4/
authoring-review concern).

**Result: PASS.**

## 9. Authority-disclosure attack

`is_authoritative` independently confirmed immovably `const false` — every
attempted override (`true`, the string `"false"`, `null`, `0`) is
rejected. `authority_role` independently confirmed to accept only its
7 frozen enum values (including the structurally-permitted `"authoritative"`
value, per Sec.9's own disclosure that shape-level permission is not the
same as live authority) and reject case variants, whitespace, wrong-enum
substrings (e.g. `"cltr_authoritative"`, a `migration_stage` value), and
unknown strings. Unknown top-level fields on `authority_disclosure` are
rejected (`additionalProperties: false`); each of the three required
fields independently confirmed individually-required. A static source scan
independently confirms no `current_authority`/`authority_state`/
`authority_epoch`/`pcae.cltr` reference exists anywhere under
`src/pcae/schema_resources/`, proving a shape-valid disclosure has no
runtime authority-resolution path to reach.

**Result: PASS.**

## 10. Enum verification

All 8 shared enums independently re-derived value-for-value from the
on-disk schema (not from 136H's report table) and cross-checked; every
enum rejects unknown values, case variants, leading/trailing whitespace,
substring/near-match values, numeric types, and `null`.

**FINDING NON-BLOCKING-136I-1** (see Findings below): four string values
recur across more than one enum dimension (`certified` in both
`migration_stage` and `publication_state`; `quarantined` in both
`authority_role` and `publication_state`; `legacy_retired` in both
`migration_stage` and `compatibility_mode`; `cutover_candidate` in
`migration_stage`, `generation_role`, and `record_family`). This is safe
at the schema level — each value is scoped to its own field, never
cross-validated against another field's enum — and is now pinned by an
independent regression test so any *new*, undisclosed overlap introduced
by a future edit is caught.

Family-local enums (`RequestState`, `ReadinessState`,
`AuthorizationState`, `CandidateState`, `CertificationState`,
`GateResult`, `PublicationOutcome`, `ConflictType`, `JournalState`,
`ReconciliationState`, `QuarantineState`, `DeliveryState`, `MarkerState`,
`ReceiptState`) independently confirmed absent from `shared/enums.schema.json`
— none was accidentally centralized.

**Result: PASS**, with NON-BLOCKING-136I-1 recorded.

## 11. Reason-code verification

All 24 codes independently re-derived from the on-disk file and matched
exactly against the frozen 135Z Sec.31 vocabulary; no duplicates. Unknown,
case-variant, and hyphenated near-match values rejected. Independently
confirmed no reason code's machine name embeds an authority-outcome claim
(`authorized`, `certified_ok`, `published_ok`, `cutover_complete` substrings
all absent from the 24-value set).

**Result: PASS.**

## 12. Principal / proof-reference attack

`principal_identifier`'s ASCII charset independently confirmed to exclude
`=` and space (rejecting `"password=hunter2"` and any bearer-token form
containing a space). **Documented limitation, independently confirmed**:
shape validation cannot universally detect secret-shaped values whose
characters happen to fall inside the permitted charset (e.g. an
AWS-access-key-shaped string is charset-permitted) — this is an inherent
property of pattern-only shape validation, correctly out of this shared
core's scope (secret-shape detection is a policy/semantic-layer
responsibility, never claimed as complete here). A repository-wide scan of
every `properties`/`$defs` key name in all 8 packaged resources confirms
none contains `password`/`secret`/`bearer`/`private_key`/`api_key`/
`bot_token`/`access_token` as a substring. `proof_reference` independently
confirmed to `$ref` `record_reference`'s exact shape (never a bespoke
signature-blob shape).

**Result: PASS.**

## 13. Record-reference attack

`record_reference` independently attacked: each of the three required
fields (`record_id`, `record_digest`, `record_family`) individually
confirmed required; wrong-shape digest rejected; unknown `record_family`
enum value rejected; traversal-shaped (`../etc/passwd`), absolute-path
(`/abs/path`), and remote-URI-shaped (`https://evil.example/steal`)
`record_id` values all rejected by the identifier pattern itself; unknown
top-level field rejected (`additionalProperties: false`); an
`id`/`digest`-swapped tuple (each field given the other's shape) rejected.

**Documented limitation, independently confirmed, not a defect**: a
`record_reference` whose `record_id` is lexically shaped like one family
(e.g. `cutreq-...`) while `record_family` claims a different value (e.g.
`authority_state`) is still shape-valid — cross-field semantic family
agreement is explicitly a Layer-4 responsibility this shared core does not
and cannot enforce at the shape level (locators are hints only, never
trust anchors, per Sec.40).

**Result: PASS.**

## 14. Epoch / generation-reference verification

`epoch_reference` independently confirmed to accept its minimal required
shape (`migration_epoch` only) and its optional `epoch_digest` binding;
neither presence implies the named epoch is active (no code path in this
shared core reads or resolves epoch activation — none exists to read).
`generation_reference` independently confirmed to always require both
`generation_id` and `generation_digest` together — no bare, unpaired
generation-id field exists anywhere in this package.

**Result: PASS.**

## 15. Manifest independent verification and tampering attacks

Every manifest digest independently recomputed directly from file bytes
(never trusting the manifest's own claim) — all 7 match. Independently
authored tamper mutations against temporary copies, all fail closed:

| Mutation | Outcome |
|---|---|
| Digest substitution | `ManifestIntegrityError` |
| Path substitution (points at a different real file) | `ManifestIntegrityError` |
| Path-traversal entry (`../../../etc/passwd`) | raises (loader containment check) |
| Absolute-path entry (`/etc/passwd`) | raises (loader containment check) |
| Duplicate manifest entry (same path twice) | `ManifestIntegrityError` ("Duplicate") |
| Missing file (entry present, file deleted) | raises |
| Unindexed extra file (file present, no entry) | `ManifestIntegrityError` ("completeness") |
| Wrong `implementation_group` (99, outside 1-11) | `ManifestIntegrityError` (manifest-schema rejection) |
| Reordered entries | loads successfully; deterministic-`file_path`-sort-order contract is violated by the mutation itself, correctly detected by a separate sort-order assertion, not by `load_and_verify_manifest` (which does not itself enforce ordering — an independently confirmed, disclosed scope boundary of that function) |

**FINDING NON-BLOCKING-136I-2** (see Findings below): `manifest.schema.json`'s
own `status` enum is `["frozen", "draft"]` — a `"draft"`-status entry is
**schema-VALID** and independently proven to load and verify successfully
end-to-end. The rule that `"draft"` "must never appear in a committed
manifest" is a documentation/process convention (stated in the schema's
own `description` field), not a schema-enforced or
`load_and_verify_manifest`-enforced constraint. No CI or loader-level gate
currently rejects a committed `"draft"` entry.

**Result: PASS**, with NON-BLOCKING-136I-2 recorded.

## 16. Registry integration attack

Independently confirmed: an unresolved local `$ref` (a schema-id that
never registered) fails closed as `OutcomeStatus.INFRASTRUCTURE_FAILURE`;
a symlinked schema file is rejected by the loader's containment check
(`SchemaResourceError`, "Symlink..."); registry content (schema-id set) is
independently confirmed stable regardless of the process's current working
directory. Registry construction, manifest verification, and shape
validation of an invalid record were each independently re-proven to
perform zero network calls (fresh `socket.socket` monkeypatches, not
reusing 136H's own monkeypatch fixture).

**Result: PASS.**

## 17. Composition safety

Four fresh, independently authored test-only compositions (not 136H's own
envelope-composition test) confirm: a fully valid `allOf`-composed
document with a family-local field passes and an unknown field is
rejected; a document missing a required envelope field is rejected; an
unknown field nested inside a composed `authority_disclosure` object is
independently rejected (proving `authority_disclosure`'s own
`additionalProperties: false` closure holds under composition, not just in
isolation); a `oneOf` composition cannot be satisfied by a
reference-shape belonging to a different reference `$def`
(`epoch_reference`'s shape rejected where `record_reference` is required);
a `null` placeholder for a required digest field is rejected.

**Result: PASS.**

## 18. Mapping-contract repair verification (`_materialize_plain`)

A second, independently authored hostile `Mapping` subclass (distinct from
136H's own `_HostileMapping` fixture, with side-effecting
`__getitem__`/`__iter__`/`__len__`/`keys`/`items`/`__contains__`, each
appending to a call-log) is independently proven **never invoked** — the
call log is empty after rejection, proving `_materialize_plain` type-checks
before any dunder access, not merely before the specific dunders 136H's own
fixture happened to instrument.

Additional independent adversarial inputs, all rejected as
`INFRASTRUCTURE_FAILURE`: a bare `tuple` (unsupported container, distinct
from `list`); a `dict` subclass instance; a `list` subclass instance; a
custom object masquerading as a numeric scalar; a directly self-referential
`dict` (`d["self"] = d`); a directly self-referential `list`
(`l.append(l)`); a non-`str` key nested two levels deep (not only at the
top level, as 136H's own fixture tested); a 5000-level-deep nested `dict`
(fails closed on depth, not `RecursionError`).

**Correctly not rejected** (independently confirmed, non-cyclic legitimate
cases): the identical sub-object appearing twice in two unrelated branches
of the same tree is **not** misclassified as a cycle (proven via a second,
independently constructed shared-substructure fixture); a 20,000-key wide
(but shallow) `dict` materializes successfully with no crash — no width
guard exists in this repair (only depth), which is consistent with 136H's
own documented scope (a nesting-*depth* guard, not a breadth guard) and is
recorded here as an observation, not a defect, since an attacker-controlled
width-only payload cannot itself cause unbounded recursion (the
materialization walk is iterative, never recursive, independently
confirmed by successfully processing the 20,000-key input without a stack
overflow).

`_materialize_plain` independently reconfirmed to never mutate its input
(`deepcopy`-snapshot equality check on a fresh, independently constructed
nested structure) and to produce dict-insertion-order-independent
validation outcomes (two dicts with identical key/value pairs in reversed
insertion order produce identical validation status).

**Result: PASS.**

## 19. Resource containment and symlink attack

A symlinked schema file placed inside a temporary copy of the package is
independently confirmed rejected by `load_schema_resource`'s own
containment/symlink check (test skips gracefully on filesystems without
symlink support, e.g. some CI sandboxes, rather than false-failing).
TOCTOU (replace-after-enumeration) attacks were not separately re-proven
beyond the loader's existing `resolve(strict=True)` + `relative_to` design
proof already inspected in source review (Sec.19 above); no practical
TOCTOU exploit was identified within the supported single-process,
synchronous-load boundary this package operates in, so no additional
repair was made.

**Result: PASS.**

## 20. Packaging verification

Independently built both a wheel and an sdist via `python -m build`
(fresh `pip`/`hatchling` isolated build environment, not reusing any
136H/136F build artifact). Independently inspected archive contents:

- Wheel: `pcae/schema_resources/cltr_cutover/{README.md, manifest.json,
  manifest.schema.json, shared/{digest,enums,envelope,failures,identity,
  limitations,references}.schema.json}` — exactly 10 entries, all 7 shared
  schemas present, no `records/`/`bindings/`/`views/` content.
- Sdist: identical relative layout under `src/pcae/schema_resources/cltr_cutover/`
  — exactly 10 entries, same set.
- Independently installed the built wheel into a **fresh venv outside the
  repository** (`/tmp`, no relation to the repo's own `.venv`), then, with
  `cwd=/tmp` (independent of the repository entirely), imported
  `pcae.schema_resources.cltr_cutover_root`, built the registry (8 schema
  ids), and loaded/verified the manifest (7 entries) successfully —
  proving genuine installed-wheel operation, not source-tree fallback.

**Result: PASS.**

## 21. Determinism verification

Registry `schema_ids` ordering and every manifest entry's recomputed
digest independently confirmed stable across `PYTHONHASHSEED=0`, `1`, and
`42` fresh subprocess runs (identical tuple/digest output in all three).
Independently confirmed stable across 5 repeated in-process registry
builds and 5 repeated manifest loads within this phase's own test run.
Independently confirmed the shared core's editable-install operation is
unaffected by the calling process's current working directory.

**Result: PASS.**

## 22. Security result

Traversal/absolute-path identifiers rejected; duplicate-`$id` rejected
across roots and within one root; manifest digest/path substitution and
traversal-path entries all fail closed; no network-shaped `$ref` target
exists; no secret-shaped field name exists; the full independently
re-attacked Mapping-contract surface (Section 18 above) holds.

## 23. No-network result

Independently re-proven (fresh `socket.socket`/`socket.create_connection`
monkeypatches, not reusing 136H's fixture) across registry construction,
manifest verification, and shape validation of both a valid and an invalid
record, plus an explicit attempt to resolve an unregistered remote-looking
`$ref`, which raises rather than falling back to any network retrieval.

## 24. No-authority result

Independent AST-walk of every `.py` file under `src/pcae/schema_resources/`
and `src/pcae/schema_runtime/` confirms zero import of any `pcae.cltr`-rooted
module. Independent source-text scan confirms zero occurrence of
`current_authority`/`authority_state`/`authority_epoch`/`pcae.cltr` anywhere
under `schema_resources/`. `.pcae/cltr-authority/` confirmed absent both
before and after this phase's own repeated registry/manifest/validation
operations (non-mutation proof).

## 25. No-execution result

Independent AST-walk (not substring search, which produced a false
positive against this module's own docstring prose during authoring —
corrected) confirms zero `import subprocess`, zero `subprocess.`-rooted
call, zero bare `eval(`/`exec(`/`os.system(` call, and zero `shell=True`
occurrence anywhere in `src/pcae/schema_runtime/`. `pcae runtime inspect`,
invoked as a real subprocess from within this phase's own test suite,
independently reconfirms **Observed** / **observe** /
**unavailable** — unchanged by every operation this phase performed.

## 26. Contract traceability

Every Group 1 shared-core element independently mapped to a manifest
entry (`test_136i_every_group_1_shared_file_maps_to_a_manifest_entry`).
Independent scan confirms none of the 14 family-local enum names
(`RequestState` … `ReceiptState`) exists as a `$def` anywhere in
`shared/enums.schema.json` — no Group 2+ requirement was prematurely
implemented.

## 27. Focused / regression test results

- **This phase's independent adversarial suite**:
  `tests/test_cltr_cutover_136i_shared_core_independent_verification.py`
  — **221 passed, 0 failed** (9 of the initially authored cases required
  correction during authoring — see "Test-authoring corrections" below;
  all corrections are disclosed, none silently dropped).
- **136H's own focused suite** (re-run fresh by this phase, unmodified):
  `tests/test_cltr_cutover_136h_shared_core.py` — **157 passed, 0 failed**.
- **Combined schema-runtime + 136H + 136I suite**:
  `tests/test_schema_runtime_*.py` + `test_cltr_cutover_136h_shared_core.py`
  + `test_cltr_cutover_136i_shared_core_independent_verification.py` —
  **515 passed, 0 failed** (294 + 221, exactly the sum of the two
  independently-verified counts — no cross-contamination, no double
  counting).
- **Packaging tests**: `tests/test_schema_runtime_packaging.py` —
  **4 passed, 0 failed**.
- **Fast Green**: `python -m pytest -m fast_green -n auto` — **4391
  passed**, identical to the 136H baseline, zero regressions.
- **Full unmarked suite**: `python -m pytest -n auto` — see below.

## 28. Test-authoring corrections (disclosed, not defects in 136H's code)

Nine of this phase's initially authored 221 test cases required correction
during authoring; each correction and its root cause is disclosed here in
full, per the instruction not to silently drop failing attacks:

1. `SchemaRegistryError` vs `SchemaResourceError` — a manually injected
   duplicate `$id` within a single root surfaces as `SchemaResourceError`
   at the `load_schema_package` layer, not `SchemaRegistryError` (which
   `build_offline_registry` raises only for a duplicate detected *across*
   multiple roots). Test corrected to accept either type. Not a defect:
   both are fail-closed rejections.
2. Enum-overlap test — see `NON-BLOCKING-136I-1` above; corrected from an
   incorrect "no overlap" assumption to an exact, pinned overlap-set
   assertion.
3. Manifest `implementation_group` tamper test — initially asserted
   against an in-memory-only mutated dict without writing it to the
   temporary on-disk `manifest.json` before the first verification call;
   `load_and_verify_manifest` reads from disk, so the original assertion
   exercised the *unmutated* file. Corrected to write before verifying.
4. Manifest `"draft"` status test — see `NON-BLOCKING-136I-2` above;
   corrected from an incorrect "must be rejected" assumption to an
   accurate "schema-permitted, disclosed gap" assertion.
5–7. Three tests (`shared_substructure`, `wide_structure`,
   `plain_materialization_order`) incorrectly assumed
   `shared/digest.schema.json`, used directly as a `schema_id`, applies a
   root-level `type`/`properties` constraint. It does not: every
   `shared/*.schema.json` file is a `$defs`-only library file with no
   root-level shape constraint of its own (by design — it is never itself
   a record's `schema_id` in production use; a future `records/*.schema.json`
   file would compose its `$defs` via `$ref`, not use the shared file's own
   `$id` as a record's `schema_id`). Validating any legal plain JSON
   document directly against a shared file's own `$id` therefore always
   returns `VALID`. Corrected assertions to expect `VALID` and to test the
   materialization-safety property that actually matters (no false
   `INFRASTRUCTURE_FAILURE` misclassification), rather than an incorrect
   shape-rejection expectation. **This is itself an independently
   discovered, disclosed observation — `NON-BLOCKING-136I-4` below —** not
   merely a test bug: it clarifies that `validate_record_shape` called
   with a shared `$defs`-only file's `$id` as `schema_id` is a no-op shape
   gate, a footgun for any future caller who mistakenly does this instead
   of composing via a real record schema.
8. The "no-network for invalid record" test was corrected to validate
   against `manifest.schema.json` (which does have a real root-level
   object shape) rather than `shared/digest.schema.json`, for the same
   reason as items 5–7, so the test's `INVALID` assertion is meaningful.
9. The no-subprocess/no-eval source scan initially used a bare substring
   search, which false-positived on this module's own docstring prose
   ("performs no network, subprocess, shell, or backend invocation").
   Corrected to an AST-based check for actual `import subprocess`/
   `subprocess.`-rooted calls and `eval`/`exec`/`system` call nodes,
   matching the same AST-based rigor already used for the no-authority-
   import check.

None of these nine corrections reflects a defect in 136H's shared-core
schemas, manifest, or `schema_runtime` code — all nine were corrections to
this phase's own initial test assumptions, made before the tests were
finalized and reported. They are disclosed in full per the instruction
that "any mismatch must be explained and classified," in the interest of
transparency about this phase's own verification process.

## Findings

| ID | Title | Classification | Repair decision |
|---|---|---|---|
| `NON-BLOCKING-136I-1` | Four enum values (`certified`, `quarantined`, `legacy_retired`, `cutover_candidate`) recur across more than one of the 8 shared enum dimensions | NON-BLOCKING | Not a defect — each value is scoped to its own field, never cross-validated. Pinned by a new regression test (`test_136i_enum_dimensions_overlap_is_bounded_and_recorded`) so any *new* undisclosed overlap is caught in the future. |
| `NON-BLOCKING-136I-2` | `manifest.schema.json`'s own `status` enum permits `"draft"` as schema-valid, though its `description` field documents `"draft"` as forbidden in a committed manifest; no schema or loader-level gate enforces that documentation-only rule | NON-BLOCKING | Not repaired within this phase's boundary (would require either narrowing the manifest schema's own `status` enum to `const "frozen"`, which is itself an authoring decision belonging to a future manifest-schema revision, or adding a separate CI lint — deferred to the next phase or a dedicated hardening phase, whichever the roadmap schedules first). Independently proven and disclosed here so it is not silently rediscovered later. |
| `NON-BLOCKING-136I-3` | `pcae phase-report reconcile --phase-id 136H` reports `delivery_recorded_bookkeeping_incomplete` with an absent receipt — a notification-delivery bookkeeping gap for 136H's own completion, not previously disclosed in 136H's own report | NON-BLOCKING | Outside this phase's schema-verification scope (notification/receipt bookkeeping, not schema content). Disclosed for governance completeness; does not indicate a second logical 136H completion or any schema-content defect. Deferred to whichever phase next touches phase-completion notification bookkeeping. |
| `NON-BLOCKING-136I-4` | `validate_record_shape` called with a `shared/*.schema.json` file's own `$id` as `schema_id` (rather than composing that file's `$defs` via `$ref` from a real record schema) applies no root-level shape constraint and always returns `VALID` for any legal plain-JSON input | NON-BLOCKING (documentation gap, not a code defect) | Not a defect in current production usage (no caller does this today; no `records/*.schema.json` file exists yet to misuse this way). Recorded as a caller-footgun observation for whichever future group first authors a `records/*.schema.json` file and its own calling code — that code must use the *record's own* `schema_id`, never a shared file's `$id`, as the `schema_id` argument to `validate_record_shape`. No repair required within the 136H/136I shared-core boundary. |
| `NON-BLOCKING-136H-1` (restated, not independently repaired) | `phase_identity`/`transition_identity` implemented in `identity.schema.json` rather than `envelope.schema.json` as the contract Sec.6 summary table names them | NON-BLOCKING (confirmed correctly disclosed by 136H) | Independently confirmed: both files' contents are fully frozen elsewhere (Sec.10's identifier table), only the housing file differs from Sec.6's summary prose; all six identifier `$defs` are correctly `$ref`-reachable from `references.schema.json` and `envelope.schema.json` at their actual on-disk locations. No downstream `$ref` path assumption in this shared core depends on the file split named in Sec.6's summary table. Confirmed resolved, no action needed. |
| `NON-BLOCKING-136H-2`, `NON-BLOCKING-136H-3` (restated) | `cas_expectation` deferred; leap-second gap | NON-BLOCKING (confirmed) | Independently re-verified in Sections 1 and 6 above; both remain correctly disclosed and non-blocking, no new information. |

No `BLOCKING`, `CONFIRMED` (defect), `PREREQUISITE`, or `DEFERRED`
(requirement-scope) findings were produced by this phase's independent
attack. `PREREQUISITE-136G-1` (the Mapping-contract finding 136H resolved)
was independently re-attacked in Section 18 above and remains resolved —
no regression of that repair was found.

## Repairs

None. No `BLOCKING` or `CONFIRMED` (code-defect) finding was produced;
this phase's boundary permits repair only in that case. All findings above
are `NON-BLOCKING`, disclosed for future action rather than requiring
immediate repair.

## Limitations

- Digest, timestamp, and version patterns validate representation/shape
  only, never recomputed bytes, calendar validity, or semantic version
  ordering (restated from 136C/136H, independently re-confirmed, not
  newly discovered).
- Secret-shape detection (Section 12) is inherently incomplete at the
  shape-validation layer; this shared core never claims otherwise.
- Cross-field semantic agreement (record-family vs. record-id lexical
  shape, epoch/generation existence and activation, authority-role vs.
  live authority) is explicitly out of shape-validation scope everywhere
  in this package (Layer 4), independently reconfirmed at every relevant
  attack point above, never silently assumed to be enforced.
- TOCTOU (Section 19) was reasoned about via source inspection rather than
  exploited end-to-end; no practical exploit was identified within this
  package's supported single-process, synchronous-load boundary.

## Verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR AUTHORITY AND REQUEST
SCHEMA IMPLEMENTATION.**

This readiness applies only to the next bounded record-schema group
(136J, Group 2 — `AuthorityEpoch`, `AuthorityState`, plus, per the frozen
plan's Group 2/3 split, `CutoverRequest` and `ReadinessPackage` remain
candidates for Group 2/3 scoping at that phase's own discretion). It does
not authorize typed models, semantic validation, authority resolution, or
cutover behavior.

## No Stage 3 activation

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. 136I independently verified only the executable-schema shared
core. No `AuthorityEpoch`, `AuthorityState`, `CutoverRequest`,
`ReadinessPackage`, `HumanAuthorization`, `CutoverCandidate`,
`Certification`, `CASExpectation`, `PublicationAttempt`,
`PublicationEvidence`, `ConcurrencyConflict`, `RecoveryJournal`,
`ReconciliationResult`, `Quarantine`, notification binding, marker
binding, receipt binding, `CompatibilityState`,
`HistoricalAuthorityReference`, or derived record-view schema was
created. No Stage 3 typed record model or cross-record semantic validator
was implemented. No authority resolver, authority-state persistence, or
authority pointer was implemented or changed. No cutover request,
readiness package, authorization, candidate, certification, publication
attempt, conflict record, or recovery journal runtime object was created.
Schema validity does not establish lifecycle authority, cutover
eligibility, authorization, publication success, or recovery truth. No
authority epoch changed. No CLTR authority was created. No legacy
authority was demoted. No legacy authority was retired. No production
lifecycle behavior changed. No execution capability was introduced.
Runtime remains Observed, maximum capability remains observe, and
execution availability remains unavailable.

## Recommended next phase

**136J — Authority and Request Schema Implementation** (Group 2, per the
frozen plan): `AuthorityEpoch`, `AuthorityState`, `CutoverRequest`,
`ReadinessPackage`, plus fixtures and focused tests. Must not implement
authorization, certification, publication, recovery, terminal bindings,
typed models, semantic validation, or authority runtime behavior.
