# Phase 147P — Authority Evaluation Persistence Boundary Hardening

**Phase ID:** 147P
**Mode:** Bounded Implementation Repair
**Primary findings repaired:** AESIC-N-01, 147O.2-F-1
**Normative baseline:** AESIC-001 v1.3
**Implementation baseline:** Phase 147M + Phase 147O.1
**Certification baseline:** Phase 147O.3 ("AUTHORITY EVALUATION INTEGRATION
CHAPTER CERTIFIED WITH OBSERVATIONS")

---

## 1. Executive Summary

Phase 147O.3 certified the Authority Evaluation chapter (147A-147O.2) with
two carried-forward, contained findings left open: AESIC-N-01 (canonical
pointer cross-key confusion) and 147O.2-F-1 (`package_id='..'` breaking
single-level path containment). Both were assessed as Major/Minor but
*contained* — neither is reachable through any production write path,
only through defense-in-depth read/diagnostic surfaces — and 147O.3
recommended repairing both together as a narrowly scoped persistence-
boundary hardening phase. This phase does exactly that, entirely within
`src/pcae/aesic/storage.py`, `src/pcae/aesic/diagnostics.py`, and
`src/pcae/aesic/errors.py`.

**Verdict: AUTHORITY EVALUATION PERSISTENCE BOUNDARY HARDENED.**

Both findings are closed:

- `AuthorityEvaluationRecordStore.read_canonical()` now treats the
  *requested* `package_id` as authoritative over the pointer's own
  embedded `package_id`, failing closed (`CanonicalPointerCorruptError`)
  on any disagreement, with no fallback lookup under the embedded key.
- `package_id`/`evaluation_id` values are validated as a single,
  traversal-free filesystem path component *before* any filesystem
  access, rejecting invalid values (`AuthorityEvaluationStorageIdentifierError`)
  rather than silently rewriting them, plus a defense-in-depth resolved-
  path root-containment check.

No AESIC-001 amendment was required. No architecture-policy change was
required (all changes stay inside the pre-existing `aesic` zone). Runtime
remains `Observed / observe / unavailable`, unchanged. The inherited
4391-test `fast_green` baseline and 344-test Authority Evaluation chapter
suite both pass unchanged; 50 new Phase 147P tests were added (394 total
in the chapter suite).

## 2. Scope

Repaired, and only, the two persistence-boundary defects named in the
authorizing prompt:

- **Finding A (AESIC-N-01):** canonical-pointer lookup must enforce the
  requested compound-key/package boundary independently of pointer-
  internal content.
- **Finding B (147O.2-F-1):** all storage path components derived from
  identifiers must remain confined to exactly one intended storage
  component; `.`, `..`, and separator-bearing values must never alter
  directory-traversal semantics.

No AES architectural redesign, no Stage 1/Stage 2 redesign, no Registry/
Decision Template redesign, no gating change, no runtime-capability
change, no unrelated filesystem refactoring. See §19 for one directly-
coupled defect (the diagnostics surface's unprotected call to
`list_evaluation_ids`) that had to be closed alongside Finding B to avoid
reintroducing an uncaught exception in a read-only diagnostic path.

## 3. Source Reconstruction

Re-read, independently, before any production code was touched:

- The Phase 147N finding text for AESIC-N-01
  (`tests/test_phase_147n_authority_evaluation_integration_independent_verification.py`,
  `TestCanonicalPointerIntegrity.test_CROSS_KEY_RELOCATION_pointer_content_disagrees_with_query_key_not_rejected`,
  pre-repair form): a pointer file physically located at
  `pointers/pkg-B.json` whose own *content* validly (self-consistent
  digest) named `pkg-A` caused `read_canonical("pkg-B")` to silently
  return package A's AER as canonical for package B, with no exception.
- The Phase 147O.2 finding for 147O.2-F-1
  (`tests/test_phase_147o2_authority_evaluation_production_wiring_independent_verification.py`,
  `TestAesicN01IndependentContainment.test_package_id_dotdot_breaks_single_level_path_containment_read_only`,
  pre-repair form): `package_id=".."` was not rejected by `_safe_name`
  (`.` is in the allowed-character set) and, used as a bare directory
  component, resolved `records/../` — one level above the intended
  per-package directory, still inside the AES storage root.
- Phase 147O.3's final disposition (`PROJECT_STATUS.md` §"Current Phase",
  `docs/certification/PHASE_147O3_...md`): both findings reconfirmed
  Major/Minor, contained, not production-write-reachable, recommended for
  147P's bundled repair.
- Current source: `src/pcae/aesic/storage.py` (both defects live here),
  every AER/pointer caller (`src/pcae/aesic/service.py`,
  `src/pcae/aesic/diagnostics.py`), the diagnostics surface
  (`src/pcae/commands/aesic_status.py`), and every existing test touching
  `_safe_name`/`_record_path`/`_pointer_path`/`read_canonical`.

Both findings were independently reproduced against current source
(pre-repair) by running the two named pre-repair tests, then via the new
storage-level reproductions in
`tests/test_phase_147p_authority_evaluation_persistence_boundary_hardening.py`,
before any repair code was written.

## 4. Canonical Pointer Storage Model

Reconstructed model (`src/pcae/aesic/storage.py`, `src/pcae/aesic/records.py`):

- **Logical compound key:** `(package_id, evaluation_id)` for an AER;
  `package_id` alone for the canonical pointer.
- **Filesystem location:** `records/<package_id>/<evaluation_id>.json`
  (AER, exclusive-create, immutable); `pointers/<package_id>.json`
  (canonical pointer, atomic-replace, mutable).
- **Pointer filename:** derived from `package_id` via `_safe_name`.
- **Embedded pointer fields:** `package_id`, `evaluation_id`, `record_id`,
  `record_digest`, `pointer_digest`, `schema_version`
  (`CanonicalPointer`, `src/pcae/aesic/records.py:228-249`).
- **`record_id`/`record_digest`:** the AER's own identity/content digest,
  echoed into the pointer for tamper detection.
- **Pointer digest:** covers the pointer's own four content fields (not
  `pointer_digest` itself), verified on every `read_pointer` (§10.4).
- **Lookup procedure (pre-repair):** `read_canonical(package_id)` calls
  `read_pointer(package_id)` (location-keyed, digest-verified), then
  calls `read_record(pointer.package_id, pointer.evaluation_id)` — using
  the pointer's own *embedded* `package_id`, not the caller's requested
  `package_id`, to select the AER's package namespace.
- **AER resolution:** `read_record(package_id, evaluation_id)` reads
  `records/<package_id>/<evaluation_id>.json`, verifies the AER's own
  digest, and returns the parsed record (including the AER's own
  self-carried `package_id` field).

**Exact mechanism of AESIC-N-01:** because the pre-repair `read_canonical`
used `pointer.package_id` (pointer content) rather than the `package_id`
argument (requested key, == the pointer file's own location) to select
which package namespace to read the AER from, a pointer file whose
location and content disagreed caused the *content's* namespace to win.
The only checks performed after that (AER existence, `record_id` match,
`record_digest` match) all compare the pointer against the AER *it names*
— none of them ever compares the pointer, or the resolved AER, back
against the originally *requested* key. A pointer could freely choose its
own lookup namespace.

## 5. AESIC-N-01 Repair — Cross-Key Binding

`src/pcae/aesic/storage.py`, `read_canonical()`:

```python
pointer = self.read_pointer(package_id)
if pointer is None:
    return None

if pointer.package_id != package_id:
    raise CanonicalPointerCorruptError(...)

record = self.read_record(package_id, pointer.evaluation_id)  # requested key, not pointer.package_id
...
if record.package_id != package_id:
    raise CanonicalPointerCorruptError(...)
if record.record_id != pointer.record_id:
    raise CanonicalPointerCorruptError(...)
...digest check unchanged...
```

Two invariants are now enforced, both fail-closed with
`CanonicalPointerCorruptError`, both performed before any use of pointer-
or AER-embedded key material:

1. **Pointer embedded key must equal the requested key.** Checked
   immediately after `read_pointer` succeeds — the requested `package_id`
   is the *sole* namespace `read_record` is ever called with; no fallback
   lookup under `pointer.package_id` is attempted.
2. **The resolved AER's own compound-key binding must equal the requested
   key.** A second, independent check (`record.package_id != package_id`)
   catches an AER whose own embedded `package_id` field disagrees with
   the directory it was found in (e.g. Attack scenario 6 in §6 below,
   where an AER is physically copied across package directories without
   updating its own embedded `package_id`).

`record_id` and `record_digest` checks are otherwise unchanged — this is
additive, not a replacement, of the pre-existing tamper-evidence chain.

## 6. Cross-Key Substitution Attacks

All twelve attack scenarios from the authorizing prompt reduce to two
underlying mechanisms — (a) a pointer file whose location and embedded
`package_id` disagree, or (b) an AER whose own embedded `package_id`
disagrees with its containing directory — both of which the two new
checks in §5 close. Implemented and passing in
`tests/test_phase_147p_authority_evaluation_persistence_boundary_hardening.py::TestCrossKeySubstitution`:

| # | Scenario | Test |
|---|---|---|
| 1 | Pointer physically stored under key A, embedded key = B | `test_pointer_physically_at_A_embeds_key_B_rejected` |
| 2 | Pointer under A references valid AER under B | `test_pointer_under_A_references_valid_AER_under_B` |
| 3 | Pointer under A references record ID existing under both A and B | `test_record_id_collision_across_keys_does_not_defeat_key_binding` |
| 4 | Pointer digest recomputed after malicious key substitution | `test_attacker_recomputed_valid_pointer_digest_over_forged_content_still_rejected` |
| 5 | AER under B has a valid digest | covered by every scenario above (AER always genuinely valid/digest-correct; only the *key binding* is attacked) |
| 6 | AER copied from B to A without canonical-key consistency | `test_aer_physically_copied_across_package_directories_rejected_by_record_key_check` |
| 7 | Pointer from B copied wholesale into A | `test_pointer_wholesale_copied_from_B_into_A` |
| 8 | Pointer filename/path matches A but content names B | same mechanism as #1/#7 |
| 9 | Historical superseded AER under A shares metadata with B | `test_historical_superseded_AER_shares_metadata_cross_key_rejected` |
| 10 | Cross-session key substitution | `test_cross_session_key_substitution_rejected` |
| 11 | Cross-template key substitution | `test_cross_template_key_substitution_rejected` |
| 12 | Cross-repository-copy (valid filenames, differing embedded key) | same mechanism as #6/#7 |

Every attack fails closed with `CanonicalPointerCorruptError`; every
valid same-key operation in the same tests (e.g. the legitimate `pkg-A`/
`pkg-B` reads alongside each forged attempt) continues to succeed
unaffected.

## 7. 147O.2-F-1 Root Cause

`_safe_name` (`src/pcae/aesic/storage.py`, pre-repair) was a *character*
sanitizer: `re.compile(r"[^A-Za-z0-9._-]").sub("_", value)`. It replaces
any character outside `[A-Za-z0-9._-]` with `_`, but `.` (and therefore
the two-character string `..`) is itself in the allowed set and passes
through **unchanged**. `_record_path` and `_pointer_path` built paths as
`root / "records" / _safe_name(package_id) / ...` — for
`package_id=".."`, this is `root / "records" / ".."`, which resolves one
level *above* `records/`, i.e. `root/` itself. Still inside the
configured AES storage root (so not an escape past the repository), but
not the intended per-package subdirectory boundary, and reachable only
through the read-only `pcae aesic status --package-id` diagnostic (every
production write call site generates `package_id` internally as
`prp-<uuid4hex>`, never from untrusted input). Slash-bearing values (e.g.
`"../../etc/pwned"`) were separately, and correctly, neutralized by the
same substitution (every `/` becomes `_`) — that half of the pre-repair
behavior was not a defect, only the "not rejected" handling of `.`/`..`
sequences was.

## 8. Identifier Path-Safety Repair

`src/pcae/aesic/storage.py`, `_validate_identifier_component()`: checked
against the *raw* value, before `_safe_name`'s character substitution —
an invalid identifier is now rejected, never rewritten into a safe-
looking one. Rejects (raising `AuthorityEvaluationStorageIdentifierError`):

- non-`str` or empty values,
- exactly `.` or `..`,
- any value containing `/`, `os.sep`, or `os.altsep` (covers backslash on
  platforms where it is the alternate separator),
- any value containing a NUL byte,
- any absolute path (`os.path.isabs`).

Applied to both `package_id` and `evaluation_id` (both are used as bare
path components) inside `_record_path`, `_pointer_path`, and the new
`_records_directory` helper (`list_evaluation_ids`'s own path-building,
previously duplicated inline). `_safe_name`'s character substitution is
retained *after* validation, unchanged, for genuinely-valid identifiers
containing characters that are safe from a traversal standpoint but not
filesystem-portable (spaces, unicode punctuation, etc.) — validation and
substitution are complementary, not redundant: validation rejects
traversal-relevant values outright; substitution continues to normalize
everything else, exactly as before, for values that pass validation.

## 9. `package_id` Boundary Repair

All of the authorizing prompt's example invalid values are now rejected
before any filesystem access:

| Value | Pre-147P | Post-147P |
|---|---|---|
| `..` | resolved one level above the per-package dir (147O.2-F-1) | rejected (`AuthorityEvaluationStorageIdentifierError`) |
| `.` | resolved to the per-package dir's own parent-equivalent | rejected |
| `../foo` | neutralized by `_safe_name` to `.._foo` (safe, but rewritten) | rejected |
| `foo/..` | neutralized to `foo_..` | rejected |
| `foo/bar` | neutralized to `foo_bar` (silently merged two components into one) | rejected |
| `/foo` | neutralized to `_foo` | rejected |

No state is mutated on rejection — validation runs before any
`Path.mkdir`/`open`/`exists()` call. No partial lookup is performed:
`_record_path`/`_pointer_path`/`_records_directory` raise before
returning a path to any caller. The check is identical for reads and
writes (both go through the same three path-building helpers). All
*valid* existing `package_id` values (the `prp-<uuid4hex>` shape every
production writer generates, plus any string free of `.`/`..`/separators/
NUL/absolute-path markers) are unaffected —
`test_valid_package_id_unaffected` and
`test_valid_package_id_with_previously_substituted_chars_still_works`
confirm this directly.

## 10. Root Containment

`_ensure_within_root()` (`src/pcae/aesic/storage.py`): a defense-in-depth
check, applied *in addition to* (never instead of) component validation,
after every path is built. Resolves both the storage root and the
candidate path (`Path.resolve()`, which follows symlinks in already-
existing parent directories and normalizes `.`/`..`) and rejects unless
the resolved path is the root itself or has the resolved root among its
`.parents`.

Given component validation already rejects every traversal-relevant
value, this check is unreachable through `package_id`/`evaluation_id`
alone under normal conditions; its purpose is symlink escapes, where a
*validated*, traversal-free identifier (e.g. `"pkg-evil"`) names a
directory that itself has been replaced with a symlink pointing outside
the storage root. `TestRootContainment` constructs exactly this: a
`records/pkg-evil` (or `pointers/`) symlink into a sibling directory
outside the root, and confirms `_records_directory`/`_record_path`/
`_pointer_path` all reject it. This is the platform-appropriate
containment strategy for this repository (POSIX symlinks); no Windows-
specific junction/reparse-point handling was added, since the repository
and its test suite run on POSIX today and `Path.resolve()`'s symlink-
following behavior is standard-library, cross-platform-correct for the
symlink case that exists on this platform.

## 11. Storage API Contract Preservation

No public method signature changed. `write_record`, `read_record`,
`list_evaluation_ids`, `read_canonical`, `read_pointer`, `write_pointer`
all keep their existing parameter/return shapes. AER immutability
(exclusive-create, `AuthorityEvaluationRecordConflictError` on differing-
content collision, idempotent no-op on identical-content collision),
canonical-pointer atomic-replace semantics, and deterministic
serialization are all untouched — none of those code paths were modified.
The repair is observable *only* for the previously-open invalid/corrupt
cases: an invalid `package_id`/`evaluation_id` now raises before touching
disk (previously silently rewritten or, for `.`/`..`, silently
mis-resolved); a cross-key pointer/AER now raises
`CanonicalPointerCorruptError` (previously silently resolved, per
AESIC-N-01). Every valid same-key read/write in
`TestRegressionValidOperationsUnchanged` (§17 below) demonstrates
unchanged behavior.

## 12. Recovery Compatibility

`TestRecoveryAndDiagnosticsCompatibility::test_corrupt_cross_key_pointer_fails_closed_and_does_not_redirect_recovery`
and `test_restart_new_store_instance_same_root_sees_consistent_state`
confirm:

- A corrupt cross-key pointer under a given key fails closed on read; it
  does not redirect recovery to whatever namespace the forged content
  names.
- Recovery (a fresh, legitimate AER + pointer write under the *same*
  requested key) succeeds independently and is read back correctly — the
  requested/current compound key remains authoritative throughout,
  exactly as before this repair (this was never broken; the repair adds
  a check, it does not change the write path).
- A fresh `AuthorityEvaluationRecordStore` instance against the same root
  (simulating process restart) reads back state written by an earlier
  instance identically — no persisted state format changed, so no
  restart-compatibility question arises.

Idempotent retry and supersession are exercised end-to-end (not just at
the storage layer) by the unmodified 147M/147N/147O.1/147O.2 suites,
which all continue to pass (§23).

## 13. Diagnostics Compatibility

`pcae aesic status --package-id ..` (and any other invalid identifier)
now: rejects internally at the storage layer, is caught by
`summarize_package`'s (now two, previously one) `try/except` blocks
(`src/pcae/aesic/diagnostics.py`), and is reported as
`canonical_pointer_ok: false`, `canonical_record_id: null`,
`total_attempts: 0` — never a crash, never a traceback. Diagnostics
remain strictly read-only: no diagnostic call path performs a write.
Cross-key pointers are reported the same way — `pointer_ok=False` via the
pre-existing `read_canonical` try/except, now catching
`CanonicalPointerCorruptError` for the *new* reason (key-binding failure)
in addition to the pre-existing reasons (digest mismatch, missing AER).
Corruption is not suppressed to keep diagnostics "successful" — the
underlying store still raises; only the diagnostics *wrapper* converts
that into a safe, informative summary rather than propagating a stack
trace to a CLI user running a read-only inspection command.
`test_cli_status_with_invalid_package_id_does_not_crash` and
`test_diagnostic_lookup_with_invalid_key_is_safe_read_only_no_crash`
confirm both the in-process and CLI-level surfaces.

## 14. Production Wiring Compatibility

No change to `src/pcae/commands/decision_session.py`,
`src/pcae/interactive_workflow/**`, `src/pcae/governance/publication/**`,
or any CHGR-construction code — none of those modules were touched. The
full 147O.1 production-wiring suite
(`tests/test_phase_147o1_authority_evaluation_production_wiring.py`, 72
tests, exercising `decision-session confirm` → Stage 1,
`decision-session readiness` → Stage 2 → AER → pointer → publication →
`governance-record publish` → CHGR citation-only integration) passes
unchanged. Every production `package_id` in that lifecycle is generated
internally (`prp-<uuid4hex>`, `src/pcae/interactive_workflow/`), never
externally supplied, so no production caller is affected by the stricter
validation; §6/§9's adversarial `package_id` values are only reachable by
calling `AuthorityEvaluationRecordStore`/`AuthorityEvaluationService`
directly with attacker-controlled input, exactly as the pre-existing
147N/147O.2 finding tests already established.

## 15. Error Taxonomy

One new exception, narrowly scoped, added to the existing closed taxonomy
(`src/pcae/aesic/errors.py`):

```python
class AuthorityEvaluationStorageIdentifierError(AuthorityEvaluationIntegrationError):
    """A package_id/evaluation_id supplied to AuthorityEvaluationRecordStore
    is not usable, verbatim, as a single AER/pointer storage path
    component (Phase 147P persistence-boundary hardening, 147O.2-F-1).
    Raised before any filesystem access is attempted; the identifier is
    rejected, never rewritten or normalized."""
```

No other new exception type was needed: AESIC-N-01's cross-key failure
reuses the pre-existing `CanonicalPointerCorruptError` (§13's own
docstring already covers "fail-closed; the mismatched pointer's
referenced content SHALL NOT be treated as canonical" — a cross-key
pointer is exactly this case, just detected earlier and more precisely
than the pre-existing digest/existence checks alone could catch it).
Distinctions preserved: malformed logical identifier
(`AuthorityEvaluationStorageIdentifierError`) vs. path-boundary violation
(same type, §10's symlink case) vs. canonical pointer corruption
(`CanonicalPointerCorruptError`, now covering key-binding failures too)
vs. missing AER (`CanonicalPointerCorruptError`, pre-existing) vs. digest
mismatch (`CanonicalPointerCorruptError`/`AuthorityEvaluationRecordCorruptError`,
pre-existing) vs. pointer update failure
(`CanonicalPointerUpdateFailedError`, untouched, raised by `service.py`
around `write_pointer`'s `OSError`). No generic `Exception` is raised by
any changed code path.

## 16. Security Analysis

See §6 (12 cross-key substitution scenarios) and §9 (6 path-traversal
`package_id` values) for the enumerated attack coverage; both sets are
implemented as adversarial tests in
`tests/test_phase_147p_authority_evaluation_persistence_boundary_hardening.py`
(`TestIdentifierPathSafety`, `TestRootContainment`,
`TestCrossKeySubstitution`), using real filesystem state (`tmp_path`), no
mocking of the storage layer. Symlink-boundary coverage:
`TestRootContainment::test_symlinked_records_directory_escaping_root_is_rejected`
and `test_symlinked_pointers_directory_escaping_root_is_rejected`.
Diagnostic-surface safety: `TestRecoveryAndDiagnosticsCompatibility`.
Recovery-path safety: same class,
`test_corrupt_cross_key_pointer_fails_closed_and_does_not_redirect_recovery`.

## 17. Requirement Traceability

| Requirement / Finding | Production symbol | Tests | Status |
|---|---|---|---|
| AESIC-N-01 (cross-key pointer confusion) | `AuthorityEvaluationRecordStore.read_canonical` (`storage.py:226-275`) | `TestCrossKeySubstitution` (10 tests), updated `test_CROSS_KEY_RELOCATION_pointer_content_disagreeing_with_query_key_now_rejected` (147N) | CLOSED |
| 147O.2-F-1 (`package_id` path containment) | `_validate_identifier_component`, `_ensure_within_root` (`storage.py:54-81, 135-149`) | `TestIdentifierPathSafety` (13 tests), `TestRootContainment` (3 tests), updated `test_package_id_dotdot_now_rejected_before_any_filesystem_access` (147O.2) | CLOSED |
| AESIC-REQ-119 (two-tier persistence layout) | unchanged | 147M/147N/147O.1/147O.2 suites (unmodified assertions) | UNCHANGED, PASSING |
| AESIC-REQ-126/127 (pointer digest fail-closed) | unchanged (`read_pointer`) | `test_ordinary_digest_tamper_still_caught_independently_of_key_binding` | UNCHANGED, PASSING |
| AESIC-REQ-054/082 (AER immutability) | unchanged (`write_record`) | `test_normal_commit_and_read`, 147M/147N suites | UNCHANGED, PASSING |
| AESIC-REQ-055 (AER digest verification) | unchanged (`verify_aer_digest`) | `test_ordinary_aer_digest_tamper_still_caught` | UNCHANGED, PASSING |
| AESIC-REQ-097 (read-only diagnostics) | `summarize_package`, `show_evaluations_for_package` (`diagnostics.py`) | `TestRecoveryAndDiagnosticsCompatibility` (4 tests) | HARDENED, PASSING |
| AESIC-REQ-016 (closed error taxonomy) | `AuthorityEvaluationStorageIdentifierError` (`errors.py`) | all `TestIdentifierPathSafety`/`TestRootContainment` tests | EXTENDED, PASSING |
| Persistence / restart / recovery | unchanged write path, additive read-time checks | `TestRecoveryAndDiagnosticsCompatibility` (2 tests) | UNCHANGED, PASSING |

## 18. Tests

New file:
`tests/test_phase_147p_authority_evaluation_persistence_boundary_hardening.py`
— 50 tests, organized as:

- `TestIdentifierPathSafety` (13) — invalid `package_id`/`evaluation_id`
  values rejected before filesystem access; valid values unaffected.
- `TestRootContainment` (3) — symlink-based root escapes rejected; valid
  paths remain contained.
- `TestCrossKeySubstitution` (10) — the twelve attack scenarios of §6.
- `TestRecoveryAndDiagnosticsCompatibility` (5) — corrupt-pointer
  recovery, restart, diagnostics/CLI safety under invalid input.
- `TestRegressionValidOperationsUnchanged` (9) — normal commit/read,
  same-key canonical read, no-pointer-yet, supersession, multi-package
  non-collision, ordinary digest tamper (pointer and AER), unconfigured
  package listing, diagnostics for a valid package.

Two pre-existing tests were updated in place (not deleted, not weakened —
their assertions directly encoded the pre-repair vulnerable behavior and
now assert the post-repair closed behavior, with the pre-repair
demonstration preserved in each docstring):

- `tests/test_phase_147n_authority_evaluation_integration_independent_verification.py`:
  `test_path_traversal_package_id_is_neutralized` →
  `test_path_traversal_package_id_is_rejected`;
  `test_CROSS_KEY_RELOCATION_pointer_content_disagrees_with_query_key_not_rejected`
  → `test_CROSS_KEY_RELOCATION_pointer_content_disagreeing_with_query_key_now_rejected`.
- `tests/test_phase_147o2_authority_evaluation_production_wiring_independent_verification.py`:
  `test_package_id_dotdot_breaks_single_level_path_containment_read_only`
  → `test_package_id_dotdot_now_rejected_before_any_filesystem_access`.

### Results

```
python -m pytest tests/test_phase_147g_authority_evaluation.py \
  tests/test_phase_147h_authority_evaluation_independent_verification.py \
  tests/test_phase_147m_authority_evaluation_integration.py \
  tests/test_phase_147n_authority_evaluation_integration_independent_verification.py \
  tests/test_phase_147o1_authority_evaluation_production_wiring.py \
  tests/test_phase_147o2_authority_evaluation_production_wiring_independent_verification.py \
  tests/test_phase_147p_authority_evaluation_persistence_boundary_hardening.py -q
394 passed
```

(344 inherited, unchanged, + 50 new Phase 147P tests. Inherited baseline
from §23 of the authorizing prompt: 344 passed — matches exactly.)

```
python -m pytest -m fast_green -n auto -q
4391 passed
```

(Matches the inherited baseline exactly — the `fast_green` module
allowlist, `tests/conftest.py:FAST_GREEN_MODULES`, is a fixed,
curated set of core-governance modules and does not include any
Authority Evaluation test module by design; this run is the unaffected-
baseline regression check, not additional AES coverage.)

## 19. Finding Closure Evidence

### AESIC-N-01

**Before:** a pointer file at `pointers/pkg-B.json` whose content named
`package_id="pkg-A"` (self-consistent digest, `pkg-A`'s AER genuinely
valid) caused `read_canonical("pkg-B")` to return package A's AER with
`result.package_id == "pkg-A"` and no exception — reproduced exactly by
the pre-repair form of
`test_CROSS_KEY_RELOCATION_pointer_content_disagrees_with_query_key_not_rejected`
(147N, git history).

**After:** the same construction now raises `CanonicalPointerCorruptError`
from `store.read_canonical("pkg-B")`; the legitimate `store.read_canonical("pkg-A")`
continues to return the correct AER. Reproduced by the updated
`test_CROSS_KEY_RELOCATION_pointer_content_disagreeing_with_query_key_now_rejected`
and independently by all ten `TestCrossKeySubstitution` tests in the new
147P suite.

### 147O.2-F-1

**Before:** `AuthorityEvaluationRecordStore()._record_path("..", "ev-1")`
resolved to `store._root / "ev-1.json"` — one level above the intended
`records/<package_id>/` directory, still inside the storage root but
outside the intended per-package boundary — reproduced exactly by the
pre-repair form of
`test_package_id_dotdot_breaks_single_level_path_containment_read_only`
(147O.2, git history).

**After:** the same call now raises
`AuthorityEvaluationStorageIdentifierError` before any path is returned
or any filesystem access occurs. Reproduced by the updated
`test_package_id_dotdot_now_rejected_before_any_filesystem_access` and
independently by `TestIdentifierPathSafety`'s full parametrized set
(`.`, `..`, `../foo`, `foo/..`, `foo/bar`, `/foo`, empty string, NUL-
bearing string).

## 20. Contract Compatibility

Both repairs merely enforce integrity intent AESIC-001 v1.3 already
states — §12.1's own two-tier persistence design assumes a pointer's
namespace is its physical location, and §16/AESIC-REQ-097's read-only
diagnostics were always specified never to expand write reachability or
crash. No genuine contradiction between the contract text and this
repair was found. **No AESIC-001 amendment is required.**

## 21. Architecture Policy

No new imports were added. `src/pcae/aesic/errors.py`,
`src/pcae/aesic/storage.py`, and `src/pcae/aesic/diagnostics.py` all stay
within the pre-existing `aesic` zone (`.pcae/policy.toml:42`); the one
new symbol (`AuthorityEvaluationStorageIdentifierError`) is exported from
the same module (`errors.py`) every other AES-owned exception already
lives in and is imported exactly the way the pre-existing exceptions
already are. No architecture rule was weakened or added.

## 22. Limitations

- Root containment's symlink handling covers POSIX symlinks (the
  platform this repository's test suite runs on); no Windows-specific
  junction/reparse-point handling was added, since none previously
  existed and none of AESIC-001's own text requires cross-platform
  symlink semantics beyond what `pathlib.Path.resolve()` already
  provides.
- `evaluation_id` validation is new defense-in-depth for a value every
  production writer already generates safely
  (`src/pcae/aesic/service.py:_new_evaluation_id`, uuid-derived); it
  closes the same class of defect for `evaluation_id` that Finding B
  named specifically for `package_id`, but no independent finding number
  was ever assigned to the `evaluation_id` case (it was never
  demonstrated reachable) — recorded here as a proactively-closed,
  non-blocking observation, not a new finding.
- `_safe_name`'s character-substitution behavior (non-traversal-relevant
  characters silently rewritten, e.g. spaces → `_`) is unchanged and
  intentionally retained for values that pass the new validation — this
  is pre-existing, disclosed behavior, not part of either repaired
  finding.

## 23. No-Go Confirmations

- No AESIC-001 amendment. Confirmed §20.
- No predecessor contract amendment. None touched.
- No AES/Stage 1/Stage 2/Registry/Decision Template redesign. Confirmed
  §11/§14 — no public signature or call-graph shape changed.
- No enablement/configuration behavior change.
  `pcae.aesic.composition.describe_authority_evaluation_configuration`
  untouched.
- No publication ownership change. `src/pcae/governance/publication/**`
  untouched.
- No authority/execution gating added. Non-gating semantics (Publication
  Coordinator carries zero Authority Evaluation references) untouched —
  no file in that call graph was modified.
- No runtime-capability change. Confirmed below (§24).
- No unrelated CLI command/plugin added. Only `run_aesic_status`'s
  existing, pre-wired call into `summarize_package` is exercised (no new
  CLI surface).
- No broader persistence redesign beyond the two findings. Every change
  is inside `_record_path`/`_pointer_path`/`_records_directory`/
  `read_canonical`/`summarize_package`/`show_evaluations_for_package`.
- No unrelated artifact store modified. Only `src/pcae/aesic/**` files
  changed (plus the two updated pre-existing test files and this
  deliverable).

## 24. Runtime Preservation

```
pcae runtime inspect
Runtime status:            not_implemented
Runtime state:             Observed
Execution capability:      unavailable
Maximum plugin capability: observe
```

Unchanged from every prior 147-series phase. Zero commits in this phase
touch any runtime-concept file.

## 25. Overall Verdict

**AUTHORITY EVALUATION PERSISTENCE BOUNDARY HARDENED.**

- AESIC-N-01 is closed (§5, §6, §19).
- Canonical pointer reads enforce requested-key binding (§5).
- Cross-key substitution fails closed (§6, 10/10 scenarios).
- 147O.2-F-1 is closed (§8, §9, §19).
- Unsafe path-component identifiers are rejected (§8, §9).
- Root containment is preserved, including symlink escapes (§10).
- Valid persistence behavior is unchanged (§11, §17 regression suite).
- Recovery still works (§12).
- Production wiring still works (§14, 147O.1 suite unchanged).
- Diagnostics remain safe (§13).
- No contract amendment required (§20).
- Runtime remains `Observed / observe / unavailable` (§24).
- All relevant tests pass: 394/394 Authority Evaluation chapter tests,
  4391/4391 `fast_green` baseline, both matching or extending the
  inherited baselines exactly (§18).

## 26. Recommended Next Phase

**147Q — Authority Evaluation Persistence Boundary Hardening Independent
Verification.** Should independently re-derive both defects from a
pre-147P commit, author its own adversarial suite (not import this
phase's), and confirm: requested-key authority during canonical-pointer
reads; cross-key pointer substitution resistance; record/key binding;
path-component validation; `package_id`/`evaluation_id` traversal
resistance; root containment (including the symlink case); recovery
compatibility; diagnostics safety; production-wiring regression safety;
contract compatibility; runtime preservation. Verification-only, no
production repair unless separately authorized. This recommendation is
not itself an authorization.
