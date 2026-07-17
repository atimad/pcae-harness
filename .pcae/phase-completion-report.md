# Phase 136AA Complete — Stage 3 Typed Authority Model Shared Core Independent Verification

## Phase identity

- Phase ID: `136AA`
- Status: completed
- Classification: independent verification (no implementation; no shared-core source file modified)
- Report completeness: complete

## Scope

Independently verify the complete Typed Model Implementation Group 1
shared core (`src/pcae/cltr/authority/`) introduced by Phase 136Z, without
trusting 136Z's implementation prose, its own tests, fixtures, helper
functions, inventory, no-go assertions, packaging claims, or finding
classifications. Re-derive the required shared-core contract from the
frozen Stage 3 contract and the executable schemas directly. No
`AuthorityEpoch`, `AuthorityState`, or any other record-family model
implemented; no semantic validator, repository, persistence, resolver, or
runtime integration implemented.

## Summary

Read the frozen contract
(`docs/PHASE_135_STAGE_3_COMPANION_SCHEMAS_AND_TYPED_AUTHORITY_MODEL_CONTRACT_FREEZE.md`
§3/§11/§24/§25/§27/§44), the 136Y implementation plan
(`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_IMPLEMENTATION_PLAN.md`
§5/§12/§13/§16/§23), and every relevant executable schema under
`src/pcae/schema_resources/cltr_cutover/shared/` directly, independently
re-deriving the expected shared-core inventory (enum member lists,
identifier/digest regex patterns, envelope/`CasExpectation` field
inventories, `Limitations`/`AuthorityDisclosure` bounds) rather than
trusting 136Z's own counts or claims. Confirmed byte-for-byte agreement
between the executable schemas and the implementation for: all 9 shared
enums (`shared/enums.schema.json`, `shared/failures.schema.json`) and 2
embedded-local enums (`shared/references.schema.json#/$defs/cas_expectation`);
all 6 identifier regex patterns (`shared/identity.schema.json`); the
`sha256_hex` digest pattern (`shared/digest.schema.json`); the 7-field
`companion_envelope` and the `timestamp` pattern
(`shared/envelope.schema.json`); the 11-field, all-required
`cas_expectation` component (`shared/references.schema.json`, including
its self-documented divergence from the older Phase-135 §11.1 prose via
`NON-BLOCKING-136N-2`/`NON-BLOCKING-136N-3`); and the `limitations_array`/
`limitation_entry`/`disclosure_text`/`authority_disclosure` bounds and
`is_authoritative` const (`shared/limitations.schema.json`).

Wrote a new independent test module,
`tests/test_cltr_authority_136aa_shared_core_independent.py` (215 tests),
that constructs every expectation directly from the schema/contract data
above and imports nothing from 136Z's own test module
(`tests/test_cltr_authority_136z_shared_core.py`). Coverage includes:
exact public-API surface and `from ... import *` wildcard behavior;
subprocess-instrumented import-time side-effect probing (socket,
subprocess, filesystem writes); AST-based (not merely grep-based)
absence-of-record-family-model proof; `ABSENT` singleton identity across
copy/deepcopy/pickle/reimport, falsy-distinctness, identity-only
equality; `OpaqueJsonValue` exact round trips for every JSON-representable
shape plus rejection of bytes/bytearray/set/frozenset/arbitrary
object/function/`Path`/non-string keys/NaN/Infinity; recursive
immutability with proof that mutating a caller's original input after
construction has no effect, and that `to_json()`/`to_dict()` return fresh
independent copies each call; `ExtensionMapping` order/Unicode/explicit-null
preservation, reserved-key collision rejection, `maxProperties=32`
enforcement, unhashability; all 11 shared/embedded-local enums matched
member-for-member against schema-derived lists with fail-closed variant
testing (uppercase/title-case/whitespace/unknown/`None`/int); all 6
identifier and 6 digest wrapper regex boundaries independently probed
against the schema's own compiled pattern, plus `hashlib.sha256`
instrumentation proving zero digest wrappers compute a digest;
`RecordReference`/`EpochReference`/`GenerationReference`/`require_family`
non-dereferencing behavior; `CasExpectation`'s exact 11-field inventory,
all-fields-mandatory proof, family-restricted-reference enforcement, and
`builtins.open` instrumentation proving zero state reads during
construction; `Limitations`/`AuthorityDisclosure` bounds, control-character/
newline rejection, and the `is_authoritative` const-`false` pin (including
an override-attempt rejection test); `RecordEnvelope`/`Timestamp` exact
wire-string preservation across every permitted fractional-second-digit
count, `contract_version` const enforcement, and non-normalization of the
`Z` suffix; the 15-class error hierarchy's exact inheritance and safe,
non-leaking messages; the shared serialization primitives (`ABSENT`
omission, explicit-null preservation, `SerializationError` on bare
`ABSENT`/unsupported objects); an adversarial round-trip matrix across all
15 shared component kinds; and packaging file-inventory/dependency checks.

Two NON-BLOCKING findings were discovered and disclosed (full detail in
`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_SHARED_CORE_INDEPENDENT_VERIFICATION.md`
§7-§8): (1) `RecordReference` and other composite dataclasses have no
`__post_init__` re-validating that an enum/wrapper-typed field actually
holds an instance of that type, so direct construction with a raw string
bypasses `RecordFamily`'s own fail-closed check — expected given the 136Y
plan's construction-pipeline design (§16), which places that
re-validation inside each future record model's own not-yet-implemented
`from_dict`, not inside the shared-core dataclasses themselves; (2)
`Timestamp.to_datetime()` raises `ValueError` on schema-valid wire strings
with 1, 2, 4, or 5 fractional digits under the project's declared Python
floor (`>=3.9`) because `datetime.fromisoformat` on Python 3.9/3.10
requires exactly 3 or 6 fractional digits — wire fidelity, construction,
and serialization are unaffected (grep-confirmed: `to_datetime` is never
called anywhere else in the package).

A third finding was surfaced but explicitly not repaired, as it falls
outside this task's allowed-file scope: the pre-existing Phase 136U scope
guard
(`tests/test_cltr_cutover_136u_notification_marker_receipt_binding_independent_verification.py::test_136u_no_runtime_code_references_group10_families_outside_schema_resources`)
fails on `main` independently of any 136AA change, because it flags
136Z's `src/pcae/cltr/authority/enums.py` for containing the literal
string `receipt_authority_binding` — which is an authorized,
schema-matching member of the contract-frozen 16-value `RecordFamily`
enum (independently re-confirmed against
`shared/enums.schema.json#/$defs/record_family` in this phase), not an
implementation of that record family. The 136U guard predates the
shared-core `RecordFamily` enum and needs a narrow update in a future
phase; not fixed here to keep this phase bounded to the authority package
and its own verification/documentation artifacts.

## Evidence and validation

- `tests/test_cltr_authority_136aa_shared_core_independent.py` (fresh,
  this phase): 215 passed, 0 failed.
- `tests/test_cltr_authority_136z_shared_core.py` (136Z's own suite,
  rerun fresh this phase, unmodified, repository `.venv` Python 3.9.6):
  230 passed, 0 failed (includes the 3 wheel/sdist/installed-wheel
  packaging tests — the system `python3` 3.14.5 lacked the `build`
  package; `.venv`'s Python 3.9.6, the declared floor, has it).
- Both suites together: 445 passed.
- `pytest -m "fast_green" -n auto`: 4391 passed (unchanged baseline).
- Bounded sweep `-k "cltr or canonicaliz or schema_runtime or manifest or
  registry"` (~134s): 3992 passed, 9 failed, 8 skipped, 18584 deselected.
  All 9 failures independently confirmed unrelated to `cltr.authority`: 1
  is the pre-existing 136U scope-guard gap discussed above; 8 are in
  `tests/test_cltr_135o_integration.py`/
  `tests/test_cltr_migration_135p_verification.py`, reproduced in
  isolation (still fail when run alone) and grep-confirmed to contain zero
  references to `cltr.authority` anywhere — inherited, pre-existing
  environmental instability (a completion-status mismatch
  `completed_receipt_best_effort_incomplete` vs. `completed`), not a
  shared-core contribution.
- Full unmarked suite: not re-attempted unbounded this phase. Consistent
  with the documented six-phase-running stall (136W-136Z) and this
  phase's explicit instruction not to become a broad
  infrastructure-repair phase; the bounded, targeted sweep above is this
  phase's regression evidence basis instead. No new shared-core-induced
  stall was observed in any run performed.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
  coherent. `pcae doctor task-memory`: clean. `pcae runtime inspect`:
  Observed / observe / unavailable (unchanged).
- `pcae notify status`: Telegram configured/enabled and ready for
  outbound delivery if `PCAE_NOTIFY_ENABLED=1` is exported. Confirmed
  (safely, presence-only, no secret values printed) that sourcing
  `~/.config/pcae/telegram.env` in this session's shell does export
  `PCAE_NOTIFY_ENABLED`/`PCAE_TELEGRAM_BOT_TOKEN`/`PCAE_TELEGRAM_CHAT_ID`.
  The operator was explicitly asked whether to enable dispatch for this
  phase's finalization and chose to keep it disabled, matching the
  136Y/136Z precedent, rather than send a live external message.
  `PCAE_NOTIFY_ENABLED` was therefore deliberately left unset for the
  `pcae phase complete` invocation that finalizes this phase — dispatch
  was not attempted.

## Findings

- `NON-BLOCKING-136AA-1`: `RecordReference`/composite shared-core
  dataclasses do not re-validate enum/wrapper membership on direct
  construction with raw values — expected per the 136Y plan's
  construction-pipeline design; disclosed as a requirement for future
  `from_dict` implementations (Group 2+) to always construct
  enum/wrapper-typed fields via their own type before passing them into a
  composite constructor.
- `NON-BLOCKING-136AA-2`: `Timestamp.to_datetime()` raises `ValueError` on
  schema-valid 1/2/4/5-fractional-digit wire strings under the Python
  3.9/3.10 floor; wire fidelity unaffected; method unused internally;
  not repaired this phase (narrow, non-Blocking, out of this phase's
  bounded scope).
- `NON-BLOCKING-136AA-3`: pre-existing Phase 136U scope guard incorrectly
  flags 136Z's frozen `RecordFamily` enum member
  `receipt_authority_binding`; a genuine, reproducible regression 136Z's
  otherwise-correct, contract-required enum caused in an existing
  verified test, but out of this phase's allowed-file scope to repair;
  flagged prominently for a future narrow follow-up.
- `NON-BLOCKING-136AA-4`: 8 pre-existing failures in
  `test_cltr_135o_integration.py`/`test_cltr_migration_135p_verification.py`,
  confirmed unrelated to `cltr.authority` by isolated rerun and grep —
  inherited, pre-existing instability, not a shared-core contribution.

No `BLOCKING` finding exists. No loss of absent-versus-null distinction;
no mutable nested opaque value; no lossy round-trip; no non-standard JSON
acceptance; no enum coercion; no identifier-family collapse; no automatic
digest computation or normalization; no automatic reference lookup or
dereference; no timestamp wire-string normalization; no competing
canonicalization implementation; no production runtime import of the
authority package; no network/filesystem-write/subprocess/environment
side effect; no authority-like behavior; no record-family model
implemented; no package omission from wheel/sdist; no installed-wheel
failure.

## Safety and no-go confirmation

- Legacy lifecycle remains the sole production authority.
- CLTR remains derivative.
- No typed record model, dataclass, Pydantic model, or attrs model beyond
  the already-authorized shared-core primitives was implemented or
  modified.
- No record-family model (`AuthorityEpoch`, `AuthorityState`,
  `CutoverRequest`, `ReadinessPackage`, `HumanAuthorization`,
  `CutoverCandidate`, `Certification`, `PublicationAttempt`,
  `PublicationEvidence`, `ConcurrencyConflict`, `RecoveryJournalEntry`,
  `NotificationAuthorityBinding`, `MarkerAuthorityBinding`,
  `FinalizationReceiptAuthorityBinding`, `CompatibilityState`,
  `QuarantineRecord`) was implemented.
- No semantic validator, cross-record repository, persistence, or derived
  view was implemented.
- No authority resolver, current-authority lookup, or historical-authority
  lookup was implemented.
- No cryptographic verification, runtime execution, or lifecycle mutation
  occurred.
- No authority epoch changed; no legacy authority was demoted or retired;
  no CLTR authority was created.
- No production schema file was changed.
- No new production dependency was introduced — `pyproject.toml`
  unchanged.
- No production runtime module imports `pcae.cltr.authority`.
- No execution capability was introduced.
- No shared-core implementation source file was modified this phase (no
  Blocking defect was reproduced, so the bounded-repair authorization was
  not exercised).
- Runtime remains Observed, maximum capability remains observe, and
  execution availability remains unavailable.

## Final verdict

**SHARED CORE VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR AUTHORITY
CORE MODEL IMPLEMENTATION.** Required shared inventory independently
re-derived and matched exactly; no unauthorized component found; absence
and null remain distinct; opaque JSON round trips exactly; nested data is
recursively immutable; extension values are preserved; enums are strict;
identifiers retain family distinction; digests remain descriptive, never
computed; references remain unresolved; timestamps preserve exact wire
strings; errors are safe and bounded; serialization is lossless;
canonicalization remains single-source; no record-family model exists; no
production runtime import exists; no authority behavior exists; no side
effect exists; package installation works outside the checkout; focused
and regression suites pass, with two unrelated inherited failure clusters
explicitly disclosed, not hidden; no unresolved Blocking finding remains;
runtime remains Observed / observe / unavailable.

## Recommended next phase

**136AB — Stage 3 Typed Authority Model Authority Core Implementation.**
Implementing only `AuthorityEpoch` and `AuthorityState` (Typed Model
Implementation Group 2), per the 136Y plan's grouping table. Not started
by this phase. Full rationale, design detail, and no-go boundaries in
`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_SHARED_CORE_INDEPENDENT_VERIFICATION.md`.
