# Phase 136Z Complete — Stage 3 Typed Authority Model Shared Core Implementation

## Phase identity

- Phase ID: `136Z`
- Status: completed
- Classification: implementation (Typed Model Implementation Group 1 — shared core primitives only; no record-family model)
- Report completeness: complete

## Scope

Implement only the shared typed foundations required by all later Stage 3
typed authority models (Group 1 of the 136Y implementation plan), providing
lossless, immutable, offline, schema-aligned primitives without
implementing any of the sixteen record-family models. No record-family
model, semantic validator, repository, persistence, resolver, or runtime
authority behavior was implemented.

## Summary

Implemented `src/pcae/cltr/authority/` (sibling to, not inside, the
existing `src/pcae/cltr/` package): the `ABSENT` sentinel distinguishing
field-absent from explicit-`null`; `OpaqueJsonValue` and recursive
immutable JSON containers (`MappingProxyType`/`tuple`, factored into a
shared `immutable.py` module used by both `opaque.py` and
`extensions.py`); `ExtensionMapping` for `_extensions` preservation
(`maxProperties: 32`, canonical-field-collision rejection, unhashable by
design); nine shared wire enums (`AuthorityKind`, `AuthorityRole`,
`MigrationStage`, `GenerationRole`, `PublicationState`, `RecoveryState`,
`CompatibilityMode`, `RecordFamily`, `ReasonCode`) plus two
embedded-component-local enums (`LegacyLifecycleStateWire`,
`JournalLockState`); six identifier wrapper types
(`RecordId`, `GenerationId`, `MigrationEpochToken`, `PhaseIdentity`,
`TransitionId`, `PrincipalIdentifier`) and six digest wrapper types
(`Sha256Digest`, `RecordDigest`, `ReferencedRecordDigest`,
`GenerationDigest`, `PointerDigest`, `JournalEntryDigest`) — each family
kept distinct even where shapes coincide, so one kind can never
masquerade as another; `RecordReference`/`EpochReference`/
`GenerationReference` plus a fail-closed `require_family()` helper
(mirrors the executable schema's `allOf`+`const` restriction without
three separate classes); the embedded `CasExpectation` value object (all
eleven fields unconditionally required, wrong-family rejection on its
three restricted reference fields); `Limitations`/`AuthorityDisclosure`
(the latter's `is_authoritative` hard-pinned `False`, never settable, even
when `authority_role` is itself `AUTHORITATIVE`); `RecordEnvelope`/
`Timestamp`/`SchemaVersionString` (original wire timestamp string
preserved verbatim, never normalized; `contract_version` pinned const
`"1.0"`); a fourteen-class typed-model error hierarchy rooted at
`TypedModelError`; and shared `to_dict`/`from_dict` serialization
primitives (`field_from_payload`, `serialize_value`, `to_dict_fields`,
`to_canonical_bytes`) — canonical-byte production delegates unchanged to
the existing `pcae.cltr.canonicalization` module, never a reimplementation.
Zero new production dependency: frozen stdlib `dataclasses`, continuing
the `src/pcae/cltr/models.py` precedent (Pydantic/attrs rejected, per the
136Y plan's own technology decision). No record-family model was
implemented.

226 new focused tests
(`tests/test_cltr_authority_136z_shared_core.py`: 223 non-slow + 3
`@pytest.mark.slow` wheel/sdist/installed-wheel packaging tests), all
passing, covering: exact module inventory and package boundary;
no-record-family-model source scan; `ABSENT` (identity, falsy-distinctness,
copy/deepcopy/pickle, no-truth-value, non-JSON-serializability,
omission-vs-null); `OpaqueJsonValue` (every JSON primitive shape, rejected
Python types, NaN/Infinity rejection, structural equality, current
`{}`-only shape); recursive immutable containers at nesting depths
1/2/5/10; `ExtensionMapping` (round-trip, key order, collision rejection,
`maxProperties` boundary, unhashability); every shared enum's fail-closed
rejection (unknown value, case mismatch, whitespace, boolean coercion),
plus a regression test for the enum-before-`str` serialization-ordering
detail this phase discovered (a `str`-mixin Enum member is itself a `str`
instance, so the serializer must check `isinstance(value, enum.Enum)`
before the generic scalar branch or it emits the Enum instance instead of
the wire string); identifiers/digests (fixtures per type, type-
distinctness, no-lookup); references (`require_family` accept/reject,
absent-vs-null on `EpochReference`); `CasExpectation` (all-required-fields
proof, wrong-family rejection); `Limitations`/`AuthorityDisclosure`
(array-not-object serialization, `is_authoritative` pin); `Timestamp`/
`RecordEnvelope` (exact wire preservation, malformed rejection,
`contract_version` const pin); the serialization pipeline; the error
hierarchy; runtime isolation (both directions, AST-walk); no-authority
proof (export/attribute/AST scan); no-side-effect proof
(network/subprocess/filesystem-write monkeypatch instrumentation;
environment-variable isolation proven statically after monkeypatching
`os.environ` was found to break pytest's own runtime); schema-inventory
sanity; and packaging (wheel/sdist contents, isolated installed-wheel
construction from an unrelated working directory).

One pre-existing test required a bounded, disclosed repair:
`tests/test_cltr_cutover_136m_request_and_readiness_independent_verification.py
::test_136m_no_typed_authority_model_module_exists` asserted the total
absence of `src/pcae/cltr/authority/` — correct at Phase 136M's own time,
now superseded by this phase's authorized creation of that package. The
assertion was narrowed to its original intent (no *record-family* model
class exists in the package), matching the precedent 136U set repairing
stale scope-guard lists in 136N/136R.

## Precondition: 136Y terminal Telegram notification state

Investigated (read-only) before starting this phase, per the operator
prompt's precondition. `.pcae/phase-completion-metadata.json` (136Y's own,
prior to this phase's update) disclosed
`"notification_dispatch_result": "pending (dispatched by pcae phase
complete)"` and `"report_notification_status": "pending"` — 136Y never
claimed confirmed delivery. `pcae phase-report reconcile --phase-id 136Y`
(read-only) reported `Marker: already_dispatched`, but the underlying
`.last-notified.json` marker and `.pcae/delivery-receipts/` artifacts are
local self-attestation only (the one receipt found is explicitly tagged
`is_synthetic: true`, `represents_external_delivery: false` by its own
owning module). No `.pcae/notifications/*.json` event exists for phase
136Y. **Classification: State C** — unresolved, explicitly recorded, no
lifecycle inconsistency. No resend was performed; no second 136Y
completion was created. Carried forward as `NON-BLOCKING-136Z-1`.

## Evidence and validation

- `tests/test_cltr_authority_136z_shared_core.py` (fresh, this phase,
  repository `.venv`, Python 3.9.6): 223 passed (non-slow) + 3 passed
  (`-m slow`, wheel/sdist/installed-wheel) = 226 passed, 0 failed.
- Complete `cltr_cutover` + `schema_runtime` filtered suite (fresh,
  `-k cltr_cutover -n auto`): 1925 passed, 8 skipped, 0 failed.
- Fast Green (fresh, `-m fast_green -n auto`): 4391 passed — unchanged
  baseline, zero regressions.
- Fresh wheel build (`python -m build --wheel`): contains all 14 new
  module files (`__init__.py` + 13 submodules); no record-group module
  name present. Fresh sdist build: same inclusion confirmed.
- Isolated installed-wheel smoke test: wheel installed into a fresh
  `venv` outside the repository checkout; a probe script run from an
  unrelated working directory imported `pcae.cltr.authority`, constructed
  a `RecordEnvelope`, serialized and canonicalized it, and exercised
  `ABSENT`/enum fail-closed behavior — all succeeded.
- Runtime-isolation AST-walk: zero import edges from
  `src/pcae/commands`, `src/pcae/core`, `src/pcae/cltr` (excluding
  `authority/`), or `src/pcae/runtime` into `pcae.cltr.authority`; zero
  imports from `pcae.cltr.authority` into any production
  lifecycle/notification/report module.
- No-authority proof: none of `resolve_authority`, `current_authority`,
  `activate_epoch`, `demote_legacy`, `retire_legacy`, `authorize_cutover`,
  `evaluate_readiness`, `certify_candidate`, `publish`, `recover`,
  `quarantine`, `release`, `execute` is exported by or defined anywhere in
  the new package (attribute check + AST scan).
- No-side-effect proof: instrumented `socket.socket`/
  `socket.create_connection`/`subprocess.run`/`subprocess.Popen`/write-mode
  `open()` monkeypatches around construction/serialization of one fixture
  per shared component — zero side effects. Environment-variable isolation
  proven statically (no `os.environ`/`os.getenv` token anywhere in package
  source).
- No new production dependency: `pyproject.toml` `dependencies`/`dev`
  lists unchanged (`jsonschema>=4.18,<5`; `pytest`/`pytest-xdist`); grep
  for `pydantic`/`attrs` across `src/pcae` — zero hits.
- Schema inventory unchanged: 7 shared resources, 16 record schemas —
  re-confirmed by direct inspection; no production schema file touched.
- Full unmarked suite: attempted fresh (`pytest -n auto`, 15 workers,
  22374 items collected) under a 240-second bound (monitored, then
  terminated at the bound); reached approximately 79% of collected items
  before the bound closed — the sixth independently observed
  stall/incompleteness across 136W (x3), 136X (x1), 136Y (x1), and this
  phase. 65 pre-existing `F` markers were observed within the partial
  run, outside both of this phase's own authoritative regression gates
  (the `cltr_cutover`/`schema_runtime` filtered suite and Fast Green, both
  100% clean). Not claimed as a completed or passed run; not investigated
  further per the operator prompt's explicit boundary.
- `pcae health`: healthy. `pcae check`: passed. `pcae status coherence`:
  coherent. `pcae doctor task-memory`: clean. `pcae push check`: clean.
  `pcae runtime inspect`: Observed / observe / unavailable (unchanged).
  `pcae notify status`: Telegram configured/enabled; dispatch not
  attempted this phase (`PCAE_NOTIFY_ENABLED` unset in this session).

## Findings

- `NON-BLOCKING-136Z-1`: 136Y's terminal Telegram notification state is
  unresolved/unverified (Section "Precondition" above) — a pre-existing
  gap in the Telegram sink's own delivery-evidence design (a successful
  API response is parsed but never persisted anywhere), disclosed, not
  repaired this phase (out of shared-core scope).
- `NON-BLOCKING-136Z-2`: one pre-existing stale scope-guard test
  (`test_136m_no_typed_authority_model_module_exists`) required narrowing
  to its original intent; repaired in place, re-verified passing.
- `NON-BLOCKING-136Z-3` (re-confirms `NON-BLOCKING-136W-3`): full-suite
  stall recurrence — inherited, pre-existing; no 136Z-authored test
  implicated.
- `NON-BLOCKING-136Z-4`: 65 pre-existing `F` markers observed within the
  partial full-suite run — inherited, outside both of this phase's
  authoritative gates; unrelated to shared-core changes.
- `NON-BLOCKING-136Z-5`: `build_architecture_status`'s post-completion
  "projected recommended next phase" regex
  (`src/pcae/core/phase_reports.py`) captures only a single trailing
  letter after the phase-series digits, so a two-letter phase-ID suffix
  such as `136AA` (the convention 136Y's own plan established as this
  repository's first use of a multi-letter suffix) is mis-truncated to
  `136A`, a phase completed long ago — producing a false
  already-completed conflict during phase-report finalization. Out of
  this shared-core-only phase's scope to repair (a production
  governance-tooling source change); worked around this phase by phrasing
  the recommended-next-phase field so the phase ID is not the leading
  token, avoiding the buggy prefix match without altering any production
  source. Recommended for repair in a future, separately governed
  infrastructure phase.

No `BLOCKING` finding exists. No loss of absent-versus-null distinction;
no mutable nested opaque value; no lossy round-trip; no enum coercion; no
timestamp normalization; no identifier-family collapse; no automatic
digest computation; no automatic reference lookup/dereference; no
production runtime import of the new package; no network/filesystem/
subprocess/environment side effect; no authority-like behavior; no
record-family model implemented; no new dependency; no package omission
from wheel/sdist; no installed-wheel failure.

## Safety and no-go confirmation

- Legacy lifecycle remains the sole production authority.
- CLTR remains derivative.
- No typed record model, dataclass, Pydantic model, or attrs model beyond
  the authorized shared-core primitives was implemented.
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
- Runtime remains Observed, maximum capability remains observe, and
  execution availability remains unavailable.

## Final verdict

**SHARED CORE IMPLEMENTATION COMPLETE WITH NON-BLOCKING FINDINGS — READY
FOR INDEPENDENT VERIFICATION.** Exact shared inventory implemented; no
record-family model exists; `ABSENT` is correct and stable; opaque JSON is
lossless; nested values are immutable; `_extensions` can be preserved;
enum behavior is strict; identifiers preserve family distinctions;
digests remain descriptive; references do not resolve; timestamps
preserve original wire strings; shared limitations and authority
disclosure match the contract; serialization is deterministic and
lossless; no coercion occurs; no authority behavior exists; no side
effects exist; no runtime production module imports the package; package
is included in wheel and sdist; isolated installed-wheel use passes;
focused and regression suites pass; runtime remains Observed / observe /
unavailable.

## Recommended next phase

**Stage 3 Typed Authority Model Shared Core Independent Verification
(phase 136AA).** Not started by this phase. Full rationale, design
detail, and no-go boundaries in
`docs/PHASE_136_STAGE_3_TYPED_AUTHORITY_MODEL_SHARED_CORE_IMPLEMENTATION.md`.
