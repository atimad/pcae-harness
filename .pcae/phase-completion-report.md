# Phase 136I Complete — Companion Executable Schema Shared Core Independent Verification

## Phase identity

- Phase ID: `136I`
- Status: completed
- Classification: verification (Stage 3 Companion Executable Schema, Implementation Group 1: independent verification of the shared core)
- Report completeness: complete

## Summary

Phase 136I independently re-derives, reproduces, mutates, and
adversarially attacks Phase 136H's Stage 3 Companion Executable Schema
shared core (`src/pcae/schema_resources/cltr_cutover`), trusting none of
136H's own 157 tests or report prose. Full detail in
`docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_INDEPENDENT_VERIFICATION.md`.

Before verification work, ran the two required read-only
reconciliations: `pcae phase-report reconcile --phase-id 136H`
(`delivery_recorded_bookkeeping_incomplete`, `already_dispatched`,
receipt absent, mutation: none -- a notification-delivery bookkeeping
gap, not a schema-content defect, recorded as `NON-BLOCKING-136I-3`) and
`--phase-id 136G` (`not_delivered`, `not_dispatched`, mutation: none, the
same pre-existing, unrelated historical fact already disclosed by 136H).
Neither command mutated state; neither phase was redispatched.

A fresh, independently authored adversarial test module
(`tests/test_cltr_cutover_136i_shared_core_independent_verification.py`,
221 test cases) independently re-derives the exact Group 1 inventory (7
shared files, 33 exported `$defs`, 8 shared enums, 24 reason codes, 7
manifest entries -- all confirmed exact, zero mismatch) directly from the
on-disk schemas and the frozen contract (`CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001
v1.0` Sec.4/6/8/10-16/46, the 136E implementation plan Sec.7/13), never
from 136H's own report tables. Every identifier/digest/timestamp/version/
enum/reason-code/reference/limitation definition was attacked with
independently authored boundary and adversarial values not present in
136H's own fixtures.

Manifest and registry integrity was independently attacked by mutating
temporary copies: digest substitution, path substitution, path
traversal, absolute path, duplicate entry, missing file, unindexed extra
file, and wrong `implementation_group` all fail closed. The
`_materialize_plain` Mapping-contract repair (`PREREQUISITE-136G-1`) was
independently re-attacked with a second, independently authored hostile
`Mapping` (never invoked, empty call log) plus tuples, subclassed
dict/list, direct self-reference cycles, non-`str` nested keys, and
5000-deep nesting -- all fail closed, while a shared substructure
appearing twice and dict-insertion-order independence are correctly not
misclassified as cyclic.

A fresh wheel and sdist were independently built via `python -m build`;
both contain exactly the 7 shared schemas plus manifest/manifest-schema/
README (10 entries), no `records/`/`bindings/`/`views/` content. The
built wheel was installed into an isolated venv **outside the
repository** and, with `cwd=/tmp`, registry construction (8 schema ids)
and manifest load/verify (7 entries) both succeeded -- genuine
installed-wheel operation, not source-tree fallback. Determinism was
independently reconfirmed across `PYTHONHASHSEED=0/1/42` fresh
subprocesses. No-network, no-authority, and no-execution boundaries were
independently re-verified via fresh socket monkeypatches and AST-based
source scans (not substring search, which produced one false positive
during authoring, corrected).

Combined `tests/test_schema_runtime_*.py` + `test_cltr_cutover_136h_shared_core.py`
+ the new 136I module: **515 passed, 0 failed** (294 + 221, no
cross-contamination). Fast Green: **4391 passed**, identical to the 136H
baseline, zero regressions. Full unmarked suite freshly run: **20573
passed, 19 failed, 20592 total, 1182.26s** -- all 19 failures
independently diffed line-by-line and confirmed byte-for-byte identical
to 136H's own already-classified pre-existing failure set. A 20th failure
on the first run was this phase's own new test's parallel-execution
false positive (a whole-`.pcae/`-tree non-mutation assertion that
false-failed only under `-n auto` due to unrelated concurrently running
tests legitimately writing elsewhere under `.pcae/`); corrected to scope
the assertion to `.pcae/cltr-authority/` specifically (the actual
boundary this package must never touch) and re-verified clean -- not a
product regression.

Found 4 new `NON-BLOCKING` findings (bounded enum-value overlap across
dimensions; manifest schema permits `status: "draft"` though documented
as forbidden when committed; the 136H notification-bookkeeping
reconciliation gap noted above; a `validate_record_shape`-misuse-footgun
observation about calling it with a shared `$defs`-only file's own `$id`
as `schema_id`). Zero `BLOCKING` findings. No repair was required or
made -- 136H's shared core and the carried-forward
`PREREQUISITE-136G-1` Mapping-contract repair both withstood independent
adversarial attack unchanged.

No `AuthorityEpoch`, `AuthorityState`, `CutoverRequest`,
`ReadinessPackage`, `HumanAuthorization`, `CutoverCandidate`,
`Certification`, `CASExpectation`, `PublicationAttempt`,
`PublicationEvidence`, `ConcurrencyConflict`, `RecoveryJournal`,
`ReconciliationResult`, `Quarantine`, notification binding, marker
binding, receipt binding, `CompatibilityState`, or
`HistoricalAuthorityReference` schema was created. No Stage 3 typed
record model or cross-record semantic validator was implemented. No
authority resolver, authority-state persistence, or authority pointer
was implemented or changed. No production lifecycle behavior changed.
No execution capability was introduced. Legacy lifecycle remains the
sole production authority; CLTR remains derivative. Runtime remains
Observed, maximum capability observe, execution availability unavailable
throughout.

## Evidence and validation

- Governed phase commits: implementation commit and finalization
  commit(s) (hashes recorded after this report is committed, per the
  same multi-commit pattern used by 136E/136F/136G/136H).
- Governance and read-only inspection commands actually run and their
  results:
  - `pcae health`: healthy.
  - `pcae check`: passed.
  - `pcae status coherence`: coherent.
  - `pcae doctor task-memory`: clean before finalization close.
  - `pcae push check`: ready before, pushed after, `origin/main..HEAD`
    is `0`.
  - `pcae runtime inspect`: Observed / observe / execution unavailable,
    unchanged before and after this phase's changes.
  - `pcae notify status`: Telegram configured, enabled, ready for
    outbound delivery.
  - Read-only reconciliation for 136H/136G (mutation: none, inspection
    only): 136H `delivery_recorded_bookkeeping_incomplete`/
    `already_dispatched`/receipt absent (`NON-BLOCKING-136I-3`); 136G
    `not_delivered`/`not_dispatched` (pre-existing, unrelated). Neither
    redispatched.
- This phase's independent adversarial suite: **221 passed, 0 failed**
  (`tests/test_cltr_cutover_136i_shared_core_independent_verification.py`).
- 136H's own focused suite, re-run fresh, unmodified: **157 passed, 0
  failed** (`tests/test_cltr_cutover_136h_shared_core.py`).
- Combined `tests/test_schema_runtime_*.py` + 136H + 136I: **515
  passed, 0 failed**.
- Packaging tests (`tests/test_schema_runtime_packaging.py`, unmodified):
  **4 passed, 0 failed**.
- Fast Green (`python -m pytest -m fast_green -n auto`): **4391
  passed**, identical to the 136H baseline.
- Full unmarked suite (`python -m pytest -n auto`): **20573 passed, 19
  failed, 20592 total, 1182.26s (0:19:42)**. All 19 failing node IDs
  (`test_advisory_runtime_contract.py`,
  `test_advisory_runtime_architecture.py`, `test_phase_reports.py`,
  `test_rendering_134e5.py`, `test_finalization_transaction_134e10.py`
  (5), `test_cltr_migration_135p_verification.py` (4 parametrized),
  `test_bootstrap_todo_consistency.py` (2), `test_cltr_135o_integration.py`
  (4)) independently diffed line-by-line and confirmed byte-for-byte
  identical to 136H's own already-classified pre-existing failure set;
  none touch `schema_runtime`/`schema_resources`.
- Independent packaging verification: fresh wheel and sdist built via
  `python -m build`; both independently inspected to contain exactly 10
  entries (7 shared schemas + manifest.json + manifest.schema.json +
  README.md), no `records/`/`bindings/`/`views/` content; built wheel
  installed into an isolated venv outside the repository and exercised
  with `cwd=/tmp`, proving genuine installed-wheel operation.
- Independent manifest integrity proof: every packaged shared-core
  file's SHA-256 independently recomputed from raw bytes and confirmed
  byte-for-byte match against `manifest.json`'s recorded digests;
  adversarial mutation tests (digest substitution, path substitution,
  traversal, absolute path, duplicate entry, missing file, unindexed
  extra file, wrong `implementation_group`) all fail closed.
- Independent Mapping-contract attack: a second, independently authored
  hostile `Mapping` proven never invoked; tuple/dict-subclass/list-subclass/
  custom-scalar/cycle/deep-nesting attacks all fail closed; shared
  substructure and dict-order independence correctly not misclassified
  as cyclic; caller input never mutated.
- Independent no-network/no-authority/no-execution proof: fresh
  `socket.socket` monkeypatches; AST-walk of every `.py` file under
  `schema_resources/` and `schema_runtime/` for `pcae.cltr`-rooted
  imports (zero) and `subprocess`/`eval`/`exec`/`shell=True` usage
  (zero); `pcae runtime inspect` reconfirmed Observed/observe/unavailable
  after every operation this phase performed.

Full per-section detail (independent inventory derivation, every attack
category, the nine disclosed test-authoring corrections, all four new
findings, and the final verdict) is in
`docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_INDEPENDENT_VERIFICATION.md`.

## Findings

- `NON-BLOCKING-136I-1`: four enum values (`certified`, `quarantined`,
  `legacy_retired`, `cutover_candidate`) recur across more than one of
  the 8 shared enum dimensions. Not a defect -- each value is scoped to
  its own field, never cross-validated. Pinned by a new regression test.
- `NON-BLOCKING-136I-2`: `manifest.schema.json`'s own `status` enum
  permits `"draft"` as schema-valid, though its `description` field
  documents `"draft"` as forbidden in a committed manifest; no schema or
  loader-level gate enforces that documentation-only rule. Not repaired
  within this phase's boundary; disclosed for a future hardening phase.
- `NON-BLOCKING-136I-3`: `pcae phase-report reconcile --phase-id 136H`
  reports `delivery_recorded_bookkeeping_incomplete` with an absent
  receipt -- a notification-delivery bookkeeping gap for 136H's own
  completion, not previously disclosed in 136H's own report. Outside
  this phase's schema-verification scope; disclosed for governance
  completeness.
- `NON-BLOCKING-136I-4`: `validate_record_shape` called with a
  `shared/*.schema.json` file's own `$id` as `schema_id` (rather than
  composing that file's `$defs` via `$ref` from a real record schema)
  applies no root-level shape constraint and always returns `VALID` for
  any legal plain-JSON input. Not a defect in current production usage
  (no caller does this today); recorded as a caller-footgun observation
  for whichever future group first authors a `records/*.schema.json`
  file.
- `NON-BLOCKING-136H-1`, `NON-BLOCKING-136H-2`, `NON-BLOCKING-136H-3`
  (restated, independently re-verified, not newly repaired): all three
  remain correctly disclosed and non-blocking; no new information.
- `PREREQUISITE-136G-1` (independently re-attacked, remains resolved):
  the `_materialize_plain` Mapping-contract repair withstood a second,
  independently authored hostile `Mapping` and additional adversarial
  input types without regression.

Zero unresolved Blocking findings. Zero repairs required or made.

## Safety and no-go confirmation

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. 136I independently verified only the executable-schema
shared core. No `AuthorityEpoch`, `AuthorityState`, `CutoverRequest`,
`ReadinessPackage`, `HumanAuthorization`, `CutoverCandidate`,
`Certification`, `CASExpectation`, `PublicationAttempt`,
`PublicationEvidence`, `ConcurrencyConflict`, `RecoveryJournal`,
`ReconciliationResult`, `Quarantine`, notification binding, marker
binding, receipt binding, `CompatibilityState`, `HistoricalAuthorityReference`,
or derived record-view schema was created. No Stage 3 typed record model
or cross-record semantic validator was implemented. No authority
resolver, authority-state persistence, or authority pointer was
implemented or changed. No cutover request, readiness package,
authorization, candidate, certification, publication attempt, conflict
record, or recovery journal runtime object was created. Schema validity
does not establish lifecycle authority, cutover eligibility,
authorization, publication success, or recovery truth. No authority
epoch changed. No CLTR authority was created. No legacy authority was
demoted. No legacy authority was retired. No production lifecycle
behavior changed. No execution capability was introduced. Runtime
remains Observed, maximum capability remains observe, and execution
availability remains unavailable.

No `records/`, `bindings/`, or `views/` directory exists under
`cltr_cutover`. `.pcae/cltr-authority/` does not exist. The
repository-root `schemas/cltr_cutover/` path does not exist. No
production artifact changed as a result of this phase's verification
work. No repair was made to 136H's shared-core schemas, manifest, or
`schema_runtime` code.

## Final verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR AUTHORITY AND REQUEST
SCHEMA IMPLEMENTATION.** Every attack category in the phase brief was
independently exercised; the exact Group 1 inventory, manifest
integrity, packaging, Mapping-contract repair, and no-network/no-
authority/no-execution boundaries all withstood independent adversarial
attack. Zero unresolved Blocking findings remain. "Ready for authority
and request schema implementation" applies only to the next bounded
record-schema group (136J) and does not authorize typed models, semantic
validation, authority resolution, or cutover behavior.

## Recommended next phase

**136J — Authority and Request Schema Implementation.** Group 2 per the
frozen plan: `AuthorityEpoch`, `AuthorityState`, `CutoverRequest`,
`ReadinessPackage`, plus fixtures and focused tests. Must not implement
authorization, certification, publication, recovery, terminal bindings,
typed models, semantic validation, or authority runtime behavior.
