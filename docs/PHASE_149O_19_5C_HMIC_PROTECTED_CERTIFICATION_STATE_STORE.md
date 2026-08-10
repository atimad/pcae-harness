# Phase 149O.19.5C — HMIC Protected Certification State Store

**Status:** IMPLEMENTED — READY FOR NEXT BOUNDED HMIC IMPLEMENTATION WAVE
**Wave:** C of 5 (149O.19.5A–E) under HMIC-001 v1.0
**Selected source of ownership:** `docs/PHASE_149O_19_4_HATP_MANDATORY_
INDEPENDENT_VERIFICATION_CERTIFICATION_IMPLEMENTATION_PLAN.md` §9.3

---

## 1. Baseline

- Latest completed phase: 149O.19.5B (HMIC Implementation + Contract
  Identity Derivation), commits `34eae705`/`8d270ad9`/`786246c4`,
  pushed, `origin/main..HEAD` = 0.
- HMIC-001 v1.0: VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS. 144
  requirements, 12 CIVC invariants, 32 attack scenarios; frozen
  implementation subject 22 exact production files.
- Wave A/B production result: one module,
  `src/pcae/core/hatp_mandatory_certification.py` (data models, strict
  parsing, canonical serialization, closed status vocabulary,
  implementation/contract identity derivation, `certification_id`
  derivation). No protected storage, no validator, no writer, no
  readiness integration existed before this phase.
- `mandatory_consumption_implementation_independently_verified = False`
  (`hatp_mandatory_cutover.py`): unchanged by this phase.
- Initial inspection confirmed: repo clean, `origin/main..HEAD = 0`,
  `pcae health` healthy, `pcae check` passed, `pcae status coherence`
  coherent, `pcae doctor task-memory` pre-existing warnings only (stale
  `tasks/active/`/`tasks/done/` entries predating this phase, outside
  its allowed-file scope, not remediated here), `pcae push check`
  clean, `pcae runtime inspect` Observed/observe/unavailable, `pcae
  notify status` Telegram configured/enabled/ready, `pcae phase-report
  show --latest` and `pcae phase-report reconcile --phase-id 149O.19.5B`
  both confirmed 149O.19.5B completed/complete with no mutation.

## 2. Stop Condition W-1 (Restated, Not Crossed)

149O.19.4 §10.3 froze a hard sequencing gate: the future HMIC validator
module must eventually join HMIC-001's frozen 22-file implementation-
identity set via a dedicated v1.1 contract amendment (independently
verified) before Wave F may wire it into the readiness ceiling. This
phase (Wave C) builds only protected storage/locking primitives — no
validator, no admin ceremony, no wiring; `hatp_mandatory_cutover.py` is
byte-unchanged and never imports the new module; `hatp_mandatory_
certification.py` remains outside the v1.0 22-file frozen subject. W-1
is preserved unconditionally — see §11 (No-Go Confirmations).

## 3. Scope Wall Preserved: Stored ≠ Active-Valid ≠ Verified ≠ Ready ≠ Activation

This wave answers only: does artifact ID X exist? what bytes/model are
stored for X? which explicit certification ID is currently bound? is
certification ID X explicitly recorded as revoked? It never answers: is
X a valid certification? is X correctly bound to current
implementation? may activation proceed? Those remain Wave D
(`validate_active_hatp_mandatory_independent_verification_
certification`, not implemented here) and Wave F (readiness wiring, not
implemented here).

## 4. Wave-C Requirement/CIVC/Attack Traceability (Restated From 149O.19.4 §6/§7/§8)

| HMIC-REQ | Subject | Implemented by |
|---|---|---|
| 003, 021–023 | Single Protected Root, no override, structural non-duplication | `_reject_unsafe_protected_path`, `load_certification`/`load_active_binding` (both resolve `HATPTrustStore.production().root` internally, no override parameter) |
| 012 | Agent cannot write Protected Root (OS-permission boundary, not in-process) | Module docstring restates `hatp_mandatory_cutover.py`'s precedent; no in-process authority check added |
| 022, 025 | Certification files under existing root, own files, never merged into `registry.json`/`cutover-record.json`; exactly two frozen file names | `_CERTIFICATIONS_FILE_NAME`, `_CERTIFICATION_BINDINGS_FILE_NAME` |
| 026–027 | Repository/deployment-keyed storage, multi-repository/deployment safety | `_append_certification_record`/`_write_active_binding` key by `(repository_instance_id, canonical_deployment_root)`; single shared file, keyed entries, no per-repo directory |
| 028 | Local-only, no import/export, copy ≠ certify | `_write_active_binding` never verifies the pointed record exists; storage never infers validity from placement |
| 035 | Immutable record fields except `status`/`revoked_at` | `_write_revocation` uses `dataclasses.replace` for exactly those two fields, re-validated via the strict parser |
| 083 | `mkstemp`+`fsync`+`os.replace` atomic idiom | `_atomic_write_protected_json` |
| 084, 098 | Create-once; identical-content idempotent, differing-content conflict | `_append_certification_record` (byte-for-byte canonical comparison) |
| 085–086, 090 | Active-Certification Pointer is the only "active" signal; no implicit latest; creating a record never auto-activates it | `_load_active_binding`/`_write_active_binding`; `test_no_implicit_latest_...`, `test_creating_a_record_does_not_auto_activate_it` |
| 087–089 | Recertification creates a new record; old record unmutated; replay rejected by comparison, not a special flag | `_append_certification_record`'s create-once precondition (structural — Wave D owns the actual comparison) |
| 091–094 | Revocation is field mutation, not deletion; explicit-ID only; same protected-root write access; revoked-active ⇒ readiness-relevant fact for Wave D | `_write_revocation` |
| 095–096 | Never downgrades HMRC mode | Structural — this module never imports/calls `hatp_mandatory_cutover.py` |
| 097, 101–102 | Dedicated `.certification-transition.lock`, distinct from `.cutover-transition.lock`, no read-path lock acquisition, fixed path | `_certification_transition_lock` |
| 098–100 | Deterministic creation/supersession/revocation races | `_append_certification_record`/`_write_active_binding`/`_write_revocation`, all lock-serialized; real-thread concurrency tests |
| 128 | Symlink rejection — root, parent, both files | `_reject_unsafe_protected_path` |
| 129 | No path traversal via `certification_id` — structurally eliminated | No function in this module ever builds a path from `certification_id` |

CIVC coverage this wave: CIVC-6 (exactly one authoritative cert via
explicit pointer, no implicit latest — storage side) and the
concurrency-adjacent portion of CIVC-7 (no cached/stale storage state;
every read is fresh, no memoization). Attack coverage this wave: #7
(repo-local fake cert under `.pcae/` has no effect — storage only ever
resolves `HATPTrustStore.production().root`), #19 (symlinked
certification/pointer/root/parent rejected), #21 (corrupt pointer file
→ `MALFORMED` at the storage layer), #26 (concurrent revoke/activate/
create race deterministic via the lock), #30 (certification files
copied between two Protected Roots — existence in the second root
never itself establishes a binding there).

## 5. Production Module

`src/pcae/core/hatp_mandatory_certification.py` (extended; sole
production file touched this phase — same module Waves A/B created, per
149O.19.4 §9.3's `STORE` ownership legend). New Wave-C surface:

- **Constants:** `_CERTIFICATIONS_FILE_NAME` (`certifications.json`),
  `_CERTIFICATION_BINDINGS_FILE_NAME` (`certification-bindings.json`),
  `_CERTIFICATION_TRANSITION_LOCK_FILE_NAME`
  (`.certification-transition.lock`).
- **Errors:** `CertificationStorageSymlinkError`,
  `CertificationRecordNotFoundError`, `CertificationConflictError`,
  `CertificationIdentityMismatchError`.
- **Path safety / atomic write:** `_reject_unsafe_protected_path`,
  `_atomic_write_protected_json`.
- **Lock:** `_certification_transition_lock` (context manager,
  `fcntl.flock` exclusive).
- **Readers (tri-state OK/ABSENT/MALFORMED, never lock, never
  auto-provision):** `_read_raw_protected_file`, `_read_certifications`,
  `_read_certification_bindings`.
- **Explicit-ID load seams (internal):** `_load_certification_record`,
  `_load_active_binding`.
- **Production, agent-readable load entrypoints (public):**
  `load_certification(certification_id, root)`,
  `load_active_binding(root)` — both resolve `HATPTrustStore.
  production().root` internally, no override.
- **Internal, admin-only-caller write primitives (private, never called
  with `HATPTrustStore.production().root` anywhere in this module):**
  `_append_certification_record`, `_write_active_binding`,
  `_write_revocation`, plus the `CertificationAppendResult` return type
  and `_recompute_certification_id` self-consistency helper.

New Wave-C-authorized imports: stdlib `fcntl` (the identical POSIX
locking primitive `hatp_mandatory_cutover.py` already uses for its own
`.cutover-transition.lock`), `tempfile`, `contextlib.contextmanager`,
`dataclasses.replace`, `typing.Iterator`; `pcae.core.hatp_bootstrap.
HATPTrustStore` (read-only `.production().root` resolution, the
identical dependency `hatp_mandatory_cutover.py` already takes on).
Still never imports `hatp_mandatory_cutover.py`, the provider/hardware
modules, the Permission Broker, `rollback_approval_evidence.py`,
`agent.py`, `commands/agent.py`, or `cli.py`.

## 6. Storage Topology

Both files live directly under `HATPTrustStore.production().root` —
never a second root, never `.pcae/**`. Both are single, shared JSON
documents (not directory-per-repository); every entry is keyed by
`(repository_instance_id, canonical_deployment_root)` (already present
as `CertificationRecord`/`CertificationBinding` fields from Wave A/B).
No per-certification filesystem path is ever derived from
`certification_id` — structurally eliminating path-traversal risk from
that field rather than merely validating it defensively
(`test_certification_id_never_appears_as_a_filename_or_path_
component`). `test_storage_topology_exactly_two_files_no_per_repo_
directories` confirms exactly three on-disk entries after a full
create+bind cycle: `certifications.json`,
`certification-bindings.json`, `.certification-transition.lock`.

## 7. Certification Artifact Storage (Create-Once)

`_append_certification_record`:

1. Rejects a candidate whose `status != "active"` — a record is never
   created pre-revoked; revocation is always the separate
   `_write_revocation` operation.
2. Self-consistency check: re-derives `certification_id` from the
   candidate's own eight stated fields (Wave B's pure
   `derive_certification_id`) and refuses
   (`CertificationIdentityMismatchError`) on mismatch — a structural
   check of the candidate's own bytes only, never a comparison against
   current Git/contract state (Wave D's job).
3. Round-trips the candidate through the strict Wave-A parser before
   persisting, so every record this module ever writes passes through
   the identical validation domain the parser itself enforces.
4. Under the transition lock: reads the current document (or an empty
   default if absent), and for an existing same-ID record compares
   canonical bytes — exact match is an idempotent no-op (no write, no
   duplicate entry, no rewrite of an already-revoked record's status);
   any byte difference is `CertificationConflictError`. Never silently
   overwrites.
5. Persists via `_atomic_write_protected_json` (`mkstemp`+`fsync`+
   `os.replace`), rejecting a symlinked destination immediately before
   the replace (TOCTOU discipline).

## 8. Active-Certification Binding (No Implicit Latest)

`_write_active_binding` replaces (never compare-and-swaps — HMIC-REQ-099
specifies plain locked last-write-wins, not CAS) the binding entry for
one exact `(repository_instance_id, canonical_deployment_root)` key,
preserving every other key's entry unchanged. It never verifies the
pointed `certification_id` exists in `certifications.json` (storage
does not cross-check current implementation — that remains Wave D's
job); a binding may legitimately point at an as-yet-uncreated or
already-revoked record, and Wave C never rewrites or clears it merely
because the pointed record is later revoked
(`test_revoked_binding_storage_is_not_rewritten_or_cleared`). Missing
binding entry means explicitly "no active certification for this key" —
`_load_active_binding` returns `None`, never a scan/sort/glob fallback
(`test_no_implicit_latest_multiple_records_no_binding_selects_none`,
`test_explicit_binding_returns_named_record_even_if_another_is_newer`).

## 9. Revocation (Field Mutation, Monotonic)

`_write_revocation` mutates the existing `CertificationRecord`'s
`status`/`revoked_at` fields in place within `certifications.json` —
never a deletion, never a separate revocation-record file
(HMIC-REQ-091's exact mechanism). Monotonic: no code path in this
module ever writes `status: "active"` onto an already-`"revoked"`
record (`test_no_un_revoke_api_exists`); an identical-timestamp replay
is idempotent (no write); a differing timestamp is
`CertificationConflictError` — the first-recorded revocation always
wins. Revoking a non-active record has no binding effect
(`test_revocation_of_non_active_record_has_no_binding_effect`).

## 10. Locking, Atomicity, Concurrency

`_certification_transition_lock` acquires an exclusive `fcntl.flock` on
`.certification-transition.lock`, fixed directly under the Protected
Root — a distinct file from HMRC-001's own `.cutover-transition.lock`
(`test_lock_file_name_is_dedicated_and_distinct_from_cutover_lock`), so
certification writes never serialize against Cutover Record writes
(HMIC-REQ-101). Only writers acquire it; every reader in this module is
lock-free, and no reader ever creates the Protected Root or the lock
file (`test_lock_file_created_only_by_write_not_by_read`). Real-thread
(not mocked) concurrency tests confirm: 8 identical concurrent creates
→ exactly 1 winner + 7 idempotent no-ops, single stored record; 8
distinct concurrent creates → 8 distinct stored records, no corruption;
5 concurrent active-binding writes for the same key → exactly one
final, non-torn pointer; 8 concurrent identical revocations →
deterministic single revoked record; a revoke racing a concurrent
append of a different certification → both effects land, no half-
applied state.

## 11. No-Go Confirmations

- Only Wave-C-authorized production file was modified: `git diff
  --name-only` against the phase-entry commit for `src/pcae/` shows
  exactly `src/pcae/core/hatp_mandatory_certification.py`
  (modification, not addition — the same file Waves A/B created).
- HMIC-001, HMRC-001, HATP-001, HSCE-001, RAE-001, RWMPC-001, PBPA-001,
  and PBPC-001 all remain byte-unchanged.
- The exact 22-file certified subject remained byte-unchanged this
  phase (Wave C never reads or writes any of the 22 files).
- `hatp_mandatory_cutover.py` remains byte-unchanged; the hard-coded
  `mandatory_consumption_implementation_independently_verified = False`
  ceiling is untouched (`test_hardcoded_false_readiness_ceiling_
  unchanged`). The new module is never imported by `hatp_mandatory_
  cutover.py` or any other existing production file
  (`test_certification_module_not_imported_by_cutover_module`).
- No validation function, `is_valid`/`is_certified` boolean, or
  readiness-boolean-returning function exists anywhere in this module
  (`test_no_validation_function_exists_in_module`,
  `test_no_readiness_boolean_function_exists`).
- No admin ceremony, no `create_certification`/`activate_certification`/
  `revoke_certification`/`certify_current_implementation` function
  exists; every write primitive is private (leading underscore), never
  called with `HATPTrustStore.production().root` anywhere in this
  module (`test_load_certification_and_load_active_binding_are_read_
  only_no_write_api_exposed`).
- No ordinary `pcae` CLI change; no `commands/agent.py`/`agent.py`
  change; no admin writer script exists anywhere in the repository yet
  (Wave E, not this phase).
- No real certification artifact, active-certification binding, or
  revocation record was created anywhere on this host — every test uses
  an isolated `tmp_path` protected root; `HATPTrustStore.production().
  root` is never constructed for a write in this test suite.
- Import has no side effect: no root resolution, no directory creation,
  no Git/hardware/PB access at module import time
  (`test_import_has_no_side_effect_no_root_resolution_no_directory_
  creation`, subprocess-isolated).
- No Cutover Record or activation marker was created or modified. No
  real `HATP_MANDATORY` activation occurred. No Class-B provisioning
  occurred. No Permission Broker behavior changed. `POL-005` remained
  unchanged. No `COMP-002` capability was implemented.
- Runtime/executed-source-binding remains deferred per HMIC-REQ-063
  (Wave B's own disposition, unchanged and unrevisited this phase).
- W-1 remains mandatory before any future readiness integration (Wave
  F); this phase does not begin, and could not begin, that gate.
  `hatp_mandatory_certification.py` remains outside the v1.0 22-file
  frozen subject (Wave C enlarges the module; this does not satisfy
  W-1).

## 12. Tests

- `tests/test_phase_149o_19_5c_hmic_protected_certification_state_
  store.py` — 56 tests: no-auto-provisioning reads, storage topology
  (exactly two files + lock, no per-cert path), create-once/idempotent/
  conflict (including self-consistency-mismatch rejection), atomic
  write (no temp residue on success, cleanup on `fsync` failure),
  active-binding no-implicit-latest/explicit-pointer/replace semantics,
  revocation (field mutation, idempotent, conflict, no un-revoke,
  revoked-binding-unaffected), symlink rejection (root, parent, both
  files, write-time final-path symlink), non-regular-file rejection
  (directory, FIFO), malformed-vs-absent distinction (bad JSON,
  duplicate keys, unknown schema version), multi-repository/multi-
  deployment isolation, copy-attack (existence ≠ binding), dedicated-
  lock-file identity, real-thread concurrency (create/bind/revoke
  races), production-entrypoint read-only-surface confirmation,
  import-side-effect-free confirmation, and the phase-boundary/
  production-allowlist/contract-byte-identity/no-validation-function/
  hardcoded-False-unchanged checks mirroring the 149O.19.5A/B suites'
  own final section.
- Widened two 149O.19.5A/B-era stale scope-boundary assertions (same
  established pattern as the prior 149O.19.3-era and 149O.19.5B-era
  widenings recorded in this repository's history): `tests/
  test_phase_149o_19_5a_hmic_certification_models_canonical_parsing.
  py::TestDependencyClosure::test_no_network_call_in_module_source` now
  checks actual `import` statements via the parsed AST rather than a
  raw substring scan (Wave C legitimately introduces the word "socket"
  in a non-regular-file-rejection comment and imports `fcntl` for
  locking — neither is network-shaped; the real invariant, no
  `socket`/`requests`/`urllib` import, is unchanged and re-checked
  precisely). `tests/test_phase_149o_19_5b_hmic_identity_derivation.
  py::TestNoCertificationValidityJudgment::test_module_source_never_
  reads_certifications_json` now scopes its string-literal scan to
  Wave B's own named functions only, not the whole module (Wave C's own
  later-added section of this same file legitimately reads/writes both
  filenames — that is Wave C's entire job).
- New test module added to `tests/conftest.py`'s `FAST_GREEN_MODULES`
  (deterministic; all protected-root fixtures live entirely under
  pytest's `tmp_path`, no shared/network state, no real
  `HATPTrustStore.production()` write).

## 13. Regression

- Wave A/B/C (`tests/test_hatp_mandatory_certification_models.py`,
  `tests/test_phase_149o_19_5a_hmic_certification_models_canonical_
  parsing.py`, `tests/test_phase_149o_19_5b_hmic_identity_derivation.
  py`, `tests/test_phase_149o_19_5c_hmic_protected_certification_state_
  store.py`): 163 tests across the Wave A/B/C phase-boundary suites, all
  passing (Wave-C-local run); the underlying `test_hatp_mandatory_
  certification_models.py` module is exercised as part of the broader
  sweep below.
- 149O.19.2/149O.19.3/149O.19.3R/149O.19.3R.1/149O.19.4 contract/plan
  suites and the broad `-k "hmic or hatp or 149o"` sweep: A/B-confirmed
  via `git stash -u` against unmodified `main` — before: 60 failed /
  3374 passed; after (this phase's uncommitted diff): 69 failed / 3421
  passed. All 9 net-new failures are the same, already-recorded class of
  pre-existing test design limitation this repository's own history
  documents repeatedly (149O.19.5A/B phase docs): an ancient phase's own
  "`git diff` against my fixed historical entry commit touches no
  `src/pcae/` file" assertion, which any later phase's *first* legitimate
  touch to `src/pcae/core/hatp_mandatory_certification.py` necessarily
  trips for that phase's own old baseline, purely by virtue of time
  passing and the file changing again — not a functional regression.
- Fast Green (`-m fast_green`), true A/B baseline via `git stash -u`
  (not just an uncommitted-diff comparison): baseline 37 failed / 5853
  passed; post-implementation 39 failed / 5907 passed. Exact `diff` of
  the sorted `FAILED` line lists confirms all 37 baseline failures are
  byte-identical between runs (unrelated pre-existing issues — a flaky
  parametrized timestamp test and several already-broken ancient
  "no-production-change-since-me" assertions), and exactly 2 net-new
  failures, both the identical benign class described above:
  `test_phase_149o_14_..._test_git_diff_against_pre_phase_head_touches_
  no_src_pcae_or_contract_file` and `test_phase_149o_1g_..._test_only_
  expected_production_files_changed`. Clean, deselected run (all 39
  pre-existing/newly-tripped nodeids explicitly `--deselect`ed):
  **0 failed, 5907 passed, 2 skipped, 39 deselected**.

## 14. Implementation Verdict

```
HMIC PROTECTED CERTIFICATION STATE STORE: IMPLEMENTED
— READY FOR NEXT BOUNDED HMIC IMPLEMENTATION WAVE
```

## 15. Recommended Next Phase

149O.19.5D — HMIC Active Certification Validation Engine (Wave D):
fresh active-binding load, explicit-certification load, revocation
evaluation, repository/deployment cross-check, implementation identity
comparison, contract identity comparison, verification-record checks
owned by contract, exact closed HMIC `ValidationStatus` result. Still no
admin ceremony, no readiness integration, no hardcoded-`False`
replacement, no activation. W-1 remains mandatory. Not pre-authorized by
this phase.

## 16. Status Restatement (Unchanged By This Phase)

B-149O.19.3-1: INDEPENDENTLY CONFIRMED CLOSED (unchanged). B-149O-1..4:
INDEPENDENTLY CONFIRMED CLOSED AT SYSTEM IMPLEMENTATION/ENFORCEMENT
BOUNDARY — DEPLOYMENT/OPERATIONAL ACTIVATION DEFERRED (unchanged). HATP
production: **NOT READY**. Runtime: **Observed / observe / unavailable**.
