# Phase 147Q — Authority Evaluation Persistence Boundary Hardening Independent Verification

**Phase ID:** 147Q
**Mode:** Independent Implementation Verification
**Repair baseline:** Phase 147P (`017301e3`)
**Normative baseline:** AESIC-001 v1.3
**Certification baseline:** Phase 147O.3

---

## 1. Executive Summary

**Verdict: AUTHORITY EVALUATION PERSISTENCE BOUNDARY HARDENING INDEPENDENTLY VERIFIED.**

Both findings Phase 147P claimed to close were independently reconstructed
against the actual pre-repair source (commit `d0c1008a`, Phase 147M),
reproduced live, and then independently re-attacked against the current
(repaired) implementation with fresh, differently-constructed adversarial
scenarios beyond Phase 147P's own suite:

- **AESIC-N-01** (canonical-pointer cross-key confusion): independently
  reproduced pre-repair — `read_canonical("pkg-A")` returned `pkg-B`'s AER
  silently, no exception. Independently confirmed closed post-repair: every
  cross-key construction attempted (11 distinct shapes, including a
  three-namespace relay, a record_id-collision variant, and a real
  case-insensitive-filesystem aliasing case reproduced live on this
  development machine) fails closed with `CanonicalPointerCorruptError`.
- **147O.2-F-1** (`package_id` single-level path containment):
  independently reproduced pre-repair — `package_id=".."` resolved one
  directory level above `records/<package_id>/`. Independently confirmed
  closed post-repair: every identifier attempted (traversal, absolute
  paths, repeated/alternate/Unicode-lookalike separators, percent-encoded
  strings, NUL bytes, embedded newlines) is rejected before any filesystem
  access, or — where not literally rejected (Unicode lookalikes) —
  neutralized by the pre-existing `_safe_name` substitution and still
  contained.

One new, independently-discovered finding is reported: **147Q-F-1**
(Minor/Informational, §21) — a real, reproducible TOCTOU window between
`_ensure_within_root`'s resolve-based validation and the later filesystem
write, requiring the same local, same-privilege filesystem write access
the persistence layer's whole trust boundary already assumes. It does not
block this verdict (§30 criteria).

No Blocking or Major finding was identified. No AESIC-001 amendment is
required (§17). Architecture ownership and runtime capability are
unaffected (§18/§19). `fast_green` and the Authority Evaluation chapter
suite both match their inherited baselines exactly (§27).

---

## 2. Scope

Verification-only, per this phase's No-Go Boundary (§28 of the phase
prompt). No file under `src/pcae/**` was modified — confirmed by `git
status`/`git diff` before and after this phase's work. Phase 147P's own
tests (`tests/test_phase_147p_authority_evaluation_persistence_boundary_hardening.py`)
were not modified. Added: one independent test module
(`tests/test_phase_147q_authority_evaluation_persistence_boundary_independent_verification.py`,
34 tests) and this document.

Not in scope: repairing any newly-discovered defect (147Q-F-1 is
documented and deferred, not repaired), contract/schema/architecture-policy
amendment, CLI changes, runtime-capability changes.

---

## 3. Independent Method

Followed the discipline in the phase authorization's §2, in order:

1. Re-read the AESIC-N-01 finding as characterized in
   `docs/verification/PHASE_147N_AUTHORITY_EVALUATION_INTEGRATION_INDEPENDENT_IMPLEMENTATION_VERIFICATION.md`
   §15/§29.
2. Re-read the `147O.2-F-1` finding as characterized in
   `docs/verification/PHASE_147O2_AUTHORITY_EVALUATION_PRODUCTION_WIRING_INDEPENDENT_VERIFICATION.md`
   §10/§27/§29.
3. Read Phase 147O.3's final disposition (both carried forward as
   contained-but-open, chapter-certification recommended a bundled repair
   phase — this is exactly what Phase 147P executed).
4. Extracted the exact pre-repair `src/pcae/aesic/storage.py` from git
   history (`git show d0c1008a:src/pcae/aesic/storage.py`, the commit
   immediately preceding Phase 147P's repair commit `017301e3`) and loaded
   it as an isolated module (`importlib.util.spec_from_file_location`),
   deliberately *not* the current, repaired module.
5. Reproduced both original defects live against that isolated pre-repair
   module, before reading Phase 147P's own test assertions in detail.
6. Inspected the current (`src/pcae/aesic/storage.py`, `errors.py`,
   `diagnostics.py`) production source directly, and diffed it against the
   pre-repair extraction (`git diff d0c1008a 017301e3 -- src/pcae/aesic/`)
   to see the exact, minimal repair shape rather than trusting the
   implementation report's prose summary.
7. Authored 34 fresh, independent tests: some are pre-repair
   reconstructions (§4/§7 below), most are new adversarial constructions
   distinct in shape from Phase 147P's own 50 tests (different attack
   topologies: three-namespace relay, TOCTOU symlink-swap, case-fold
   aliasing reproduced live, Unicode-lookalike separators, percent-encoded
   strings, AST-based production-call-site verification, `git diff`-scoped
   architecture-preservation checks).
8. Ran the new suite alone, then combined with the full Authority
   Evaluation chapter, then the full `fast_green` gate (§27).
9. Only after all of the above did this document finalize its conclusions
   and cross-reference Phase 147P's own implementation report
   (`docs/implementation/PHASE_147P_AUTHORITY_EVALUATION_PERSISTENCE_BOUNDARY_HARDENING.md`).

---

## 4. AESIC-N-01 Reconstruction

**Pre-repair control flow** (`d0c1008a:src/pcae/aesic/storage.py`,
`read_canonical`):

```python
def read_canonical(self, package_id):
    pointer = self.read_pointer(package_id)   # 1. pointer lookup under the REQUESTED key
    if pointer is None:
        return None
    record = self.read_record(pointer.package_id, pointer.evaluation_id)  # 2. uses the POINTER's OWN embedded key, not the requested one
    ...
    return aer_from_payload(payload)           # 3. returned with no requested-vs-embedded key check anywhere
```

The requested-key authority is lost at step 2: `pointer.package_id` (the
pointer's own, self-reported field) — not the caller's `package_id`
argument — is what determines which AER directory is read. Nothing
compares the two. A pointer file physically stored at
`pointers/<A>.json` whose own JSON content carries `"package_id": "B"`
causes `read_canonical("A")` to read and return `B`'s AER.

**Independent live reproduction** (against the isolated pre-repair
module, `tests/test_phase_147q_...py::TestHistoricalPreRepairReconstruction::test_aesic_n01_pre_repair_pointer_redirects_across_keys`):

1. Commit a genuine, correctly-keyed AER for `pkg-B` (`evaluation_id=ev-b`,
   `record_id=rec-b`).
2. Construct a self-consistent, correctly-digested pointer whose content
   names `(pkg-B, ev-b, rec-b, <real digest>)`.
3. Physically write that pointer's bytes at `pointers/pkg-A.json` (never
   through `write_pointer`, which always keeps location and content in
   agreement — this step simulates a filesystem-level relocation, backup/
   restore mistake, or tamper).
4. Call `store.read_canonical("pkg-A")` against the pre-repair module.

**Result:** returns (does not raise) an `AuthorityEvaluationRecord` with
`package_id="pkg-B"`, `record_id="rec-b"` — confirmed identical in kind to
the AESIC-N-01 finding as documented in Phase 147N §15.

---

## 5. Cross-Key Binding Verification

Current `read_canonical` (`src/pcae/aesic/storage.py:226-275`) inserts,
before any AER is read, in order:

1. `pointer.package_id != package_id` → `CanonicalPointerCorruptError`
   (the requested-key check that was entirely absent pre-repair).
2. `record.package_id != package_id` → `CanonicalPointerCorruptError`
   (a second, independent binding check on the *AER's own* embedded key,
   not just the pointer's).
3. `record.record_id != pointer.record_id` → `CanonicalPointerCorruptError`.
4. Recomputed AER digest `!= pointer.record_digest` →
   `CanonicalPointerCorruptError`.

Independently confirmed check #2 is not redundant with #1: constructed a
scenario (`TestMaliciousPersistedState::test_record_copied_into_another_key_directory_caught_via_canonical_read`)
where the pointer's embedded key matches the query (`pkg-A`) but the
*referenced AER's own* embedded `package_id` says `pkg-B` (a raw file copy
into the wrong directory, content untouched, so its digest still
verifies). `read_record("pkg-A", ...)` alone returns this record without
error — digest verification has nothing to say about it — confirming
check #2 is the one load-bearing guard for this specific attack shape, not
dead code.

Eleven distinct cross-key constructions were exercised in total (7 in
Phase 147P's own suite plus 4 fresh ones in this phase: a
reversed-chronology record_id collision, a three-namespace A→C relay, a
percent-encoded/Unicode-lookalike identifier check, and a case-fold
aliasing test — §6). All fail closed with `CanonicalPointerCorruptError`.

---

## 6. Same-Key Regression

Independently verified, in fresh constructions distinct from Phase 147P's
own regression tests:

- A 5-generation supersession history under one key, each generation's
  `read_canonical` result checked individually (not just the final state).
- 10 independent packages written through one store instance, then read
  back through a **second, freshly-constructed** store instance
  (`AuthorityEvaluationRecordStore(root=tmp_path)` again — simulating
  process restart) — every key resolves to its own, correct AER.
- 8 packages read concurrently from 8 real OS threads
  (`threading.Thread`, not `unittest.mock` concurrency) — no
  cross-thread key bleed, no exception, every thread's result matches its
  own package.

No valid, same-key operation was found rejected or altered in behavior by
the hardening.

---

## 7. 147O.2-F-1 Reconstruction

**Pre-repair control flow** (`d0c1008a:src/pcae/aesic/storage.py`):

```python
def _record_path(self, package_id, evaluation_id):
    return self._root / "records" / _safe_name(package_id) / f"{_safe_name(evaluation_id)}.json"
```

`_safe_name`'s regex (`[^A-Za-z0-9._-]`) does **not** exclude `.` — so
`package_id=".."` passes through unchanged (both characters are in the
allowed class) and `Path("root/records") / ".." / "ev-1.json"` resolves
one level *above* `records/`, landing directly inside the AER store root.

**Independent live reproduction** (against the isolated pre-repair
module):

- `store._record_path("..", "ev-1")` → path whose parent, once resolved,
  equals `aer_root` itself, not `aer_root/records/<something>` — confirmed
  by comparing the resolved parent against the resolved `records/`
  directory (they differ) as well as against the resolved root (they
  match).
- `store._pointer_path("..")` → `pointers/...json` (no true directory
  traversal in this particular sub-path, since there is no intervening
  `/`, but the unsanitized `.` characters pass straight through,
  independently confirming the same character-class gap from a second
  call site).

Which helper accepted it: both `_record_path` and `_pointer_path`
(pre-repair) — neither validated the raw identifier at all, only
transliterated already-safe characters via `_safe_name`. Read-only
diagnostics (`summarize_package` → `read_canonical` → `_pointer_path`) can
reach it; no production write path can, because every production writer
supplies `package_id` internally (`f"prp-{uuid.uuid4().hex}"`,
`session_service.py:1157`) — confirmed unchanged in this phase by
re-reading that line and re-confirming (§16) no new caller passes
caller-controlled input to `package_id`.

---

## 8. Identifier Validation

Current `_validate_identifier_component` (`storage.py:54-81`), called from
`_record_path`, `_pointer_path`, and `_records_directory` before any
`_safe_name` transliteration or filesystem access, rejects (raising
`AuthorityEvaluationStorageIdentifierError`):

| Input class | Verified |
|---|---|
| Empty string | Rejected — also rejected earlier, at `AuthorityEvaluationRecord.__post_init__`, via `MalformedDeclarationError` |
| `.` / `..` | Rejected |
| `../foo`, `foo/..`, `foo/bar`, repeated separators (`pkg//etc`) | Rejected (contains `/`) |
| `/foo`, absolute platform paths | Rejected (contains `/` and caught again by `os.path.isabs`) |
| Platform separator (`os.sep`), alt separator (`os.altsep`, e.g. `\` on Windows) | Rejected — both are added to `_PATH_SEPARATORS` at import time |
| Embedded NUL (`foo\x00bar`) | Rejected |
| Whitespace-padded traversal (`" .."`, `".. "`, `"\t.."`, `"..\n"`) | Independently tested (§ fresh tests): either rejected outright, or (where not an exact `".."` match) still resolves inside the root — no whitespace-stripping step exists anywhere in this code that could turn a padded string into effective traversal |
| Percent-encoded (`%2e%2e`) | Not decoded (no URL-decode step exists); `%` itself is outside `_safe_name`'s allowed class and is neutralized to `_`, landing as one ordinary contained directory component |
| Unicode fullwidth solidus lookalike (`pkg／escape`, U+FF0F) | Not a real separator on any supported platform (correctly not in `_PATH_SEPARATORS`), but independently confirmed neutralized by `_safe_name` before reaching the filesystem — verified exactly one path component is created, not two |
| Embedded newline | Contained (not itself a separator; neutralized/passed as literal content in one component) |
| Valid historical-shape IDs (`prp-<hex>`, IDs with spaces) | Unaffected — confirmed both by Phase 147P's own regression tests and by this phase's own use of realistic package IDs throughout |

Validation occurs **before** any filesystem access in every case: `_record_path`/`_pointer_path`/`_records_directory`
call `_validate_identifier_component` as their first statement, prior to
constructing any `Path` object that touches disk. Independently confirmed
via `test_read_record_rejects_invalid_package_id_before_touching_disk`-equivalent
checks (no directory or file created for any rejected identifier — verified
directly in this phase's own `test_diagnostics_for_invalid_identifier_is_read_only_and_creates_nothing`
by snapshotting the filesystem tree before/after).

---

## 9. Root Containment

`_ensure_within_root` (`storage.py:135-149`) resolves both the configured
root and the candidate path (`Path.resolve()`, which follows symlinks in
already-existing path components) and requires the resolved candidate to
equal the resolved root or be a descendant of it.

Independently verified beyond string-prefix containment (the phase
authorization explicitly warns against accepting naive prefix checks as
sufficient — this implementation does not use one; it uses `Path.parents`
membership over `.resolve()`'d paths):

- Ordinary valid IDs remain contained (baseline).
- A **valid, internal** symlink (`records/pkg-alias` → `records/pkg-real`,
  both inside the root) is correctly **permitted**, confirming the check
  is genuinely about the root boundary, not "reject all symlinks."
- A **two-hop** symlink chain (`records/pkg-1` → `hop1` → truly-outside
  directory) is rejected — Phase 147P's own tests only construct one-hop
  chains; this phase's construction confirms `.resolve()`'s
  fully-recursive symlink resolution, not just one level, is what's
  actually relied upon.
- The **pointer file itself** (not its parent directory) being a symlink
  to an outside file is rejected — a distinct construction from Phase
  147P's directory-symlink tests.
- Root containment holds even when the configured root itself does not
  yet exist on disk (`Path.resolve(strict=False)` semantics, the default)
  — no crash, no bypass, confirmed with a `root/nonexistent-root/deep`
  construction.

**Filesystem assumptions remaining after repair** (see §12 for the one
substantive gap found): containment is enforced correctly for the
filesystem state *at the moment of the check*; it is not enforced
atomically across the check-then-use window. See 147Q-F-1.

---

## 10. Symlink Analysis

See §9 for the containment-boundary symlink tests (all pass). Beyond
those, this phase specifically probed the **check-then-use** window,
since the phase authorization requires classifying "symlink replacement
after validation but before access where practical" as a distinct
category from static pre-existing symlinks.

**Mechanism identified:** `_ensure_within_root` computes
`path.resolve()` to *validate*, but **returns the original, unresolved**
`path` object (`storage.py:149`, `return path`) — not the resolved one.
The actual filesystem operation (`_write_exclusive_json`/
`_write_atomic_json`, called moments later by `write_record`/
`write_pointer`) re-walks that unresolved path from scratch, following
whatever symlinks exist in the filesystem *at that later moment*, not the
ones that existed when `.resolve()` ran.

**Independent live reproduction**
(`test_toctou_symlink_swap_between_validation_and_write_can_redirect_output`):

1. `store._record_path("pkg-1", "ev-1")` — validation passes; `pkg-1`'s
   records directory genuinely exists inside the root at this point.
2. Between that call and the write, `records/pkg-1` is deleted and
   replaced with a symlink to a directory genuinely outside the root
   (simulating a race with a local attacker holding the same filesystem
   write privilege the whole persistence layer already trusts).
3. The write proceeds using the now-stale `Path` object returned in step 1.

**Result:** the file is written outside the configured AER root, through
the swapped-in symlink — confirmed real, not theoretical, reproduced
deterministically (not as a flaky race) by performing the two steps
sequentially rather than via true concurrent threads.

**Bound on impact:** confirmed (`test_revalidating_on_a_fresh_call_after_swap_does_catch_it`)
that any *fresh* call to the same validation helper after the swap
correctly rejects it — the store caches no path between calls, so the
window is exactly one check-then-use pair, not a persistent bypass. The
prerequisite access (ability to delete/replace a directory under the AER
store tree between two near-simultaneous operations) is the same local,
same-uid filesystem write access an attacker would need to write
malicious AER/pointer content directly (§16 exercises exactly that, and
it already succeeds without any race). This is documented as new finding
**147Q-F-1** (§21) — Minor/Informational, not blocking.

---

## 11. Error Taxonomy

Confirmed by direct inspection of `src/pcae/aesic/errors.py` and its catch
sites:

- `AuthorityEvaluationStorageIdentifierError` (new in 147P): raised only
  for a malformed/unsafe identifier, before any filesystem access —
  distinct from every other error in the taxonomy.
- `CanonicalPointerCorruptError`: raised uniformly for cross-key
  mismatch, missing referenced AER, mismatched `record_id`, and digest
  mismatch — all four are corruption/integrity conditions, correctly
  unified under one type (callers that already handle
  `CanonicalPointerCorruptError`, e.g. `pcae aesic status`'s
  `summarize_package`, correctly handle the new cross-key case with no
  code change required — confirmed by reading `diagnostics.py`).
- `AuthorityEvaluationRecordCorruptError`: distinct type, reserved for AER
  digest failures — independently confirmed a cross-key-directory AER copy
  (content digest intact, directory wrong) does **not** raise this from
  `read_record` (digest still verifies) — only `read_canonical`'s
  higher-level key-binding check catches it, correctly, as
  `CanonicalPointerCorruptError` instead. This is the correct taxonomy
  (the AER itself isn't corrupt; its *placement* is), independently
  confirmed rather than assumed.
- All catch sites (`diagnostics.py`'s two `except Exception` blocks) are
  intentionally broad (`noqa: BLE001`, read-only diagnostics contract) —
  independently verified this does **not** collapse "corrupt" into
  "not configured": `summarize_package` returns `canonical_pointer_ok=False`
  for a cross-key-corrupt pointer versus `canonical_pointer_ok=True` (with
  `canonical_record_id=None`) for a package that has genuinely never had a
  pointer published — the two states remain distinguishable (§13).

Exception inheritance: all six relevant error types inherit from
`AuthorityEvaluationIntegrationError`, itself from `Exception` — confirmed
by reading the class hierarchy directly; no bare `Exception` is raised by
the storage layer itself (only diagnostics' own deliberately-broad `except
Exception` catches one, by design, at the read-only boundary).

---

## 12. Recovery

Independently verified beyond Phase 147P's own recovery test:

- Post-AER/pre-pointer crash recovery for one key (`pkg-1`) succeeds
  correctly **while a second, unrelated key (`pkg-corrupt`) is
  simultaneously cross-key-corrupt** — confirming the two keys' recovery
  paths are fully isolated, not just recoverable in isolation
  (`test_recovery_after_pointer_write_failure_is_not_derailed_by_a_concurrently_corrupt_sibling_key`).
- Repeated (3×) reads of a cross-key-corrupt pointer all raise identically
  (no partial "self-heal" after the first failure), followed by genuine
  recovery (publishing the requested key's own real pointer) resolving
  correctly and idempotently on repeated reads afterward.
- The requested key remains authoritative throughout recovery: no recovery
  path in this store or in `AuthorityEvaluationService.evaluate_stage_2`
  (confirmed via AST inspection, §16) can construct a pointer whose
  `package_id` differs from the key recovery is being attempted for.
- Recovery does not mutate immutable history: every test above wrote new
  AERs/pointers only under the *requested* key; no test observed or
  required rewriting an existing, already-persisted AER.

---

## 13. Diagnostics

Independently verified `summarize_package`/`pcae aesic status`:

- Valid package IDs work unchanged (Phase 147P's own regression test,
  independently re-confirmed not broken by this phase's additions).
- Invalid IDs (`../../etc`, `"..", ".", "foo/bar", "/etc/passwd"`) degrade
  safely: `canonical_pointer_ok=False`, `total_attempts=0`, no exception
  propagates to the CLI layer (confirmed at both the `summarize_package`
  and `run_aesic_status` levels).
- `..` cannot traverse: confirmed no filesystem state (file or directory)
  is created anywhere under the configured root as a side effect of a
  diagnostic lookup with an invalid identifier — snapshotted the full tree
  before and after.
- **Cross-key corrupt pointer is surfaced, distinguishably from "never
  established":** independently verified
  (`test_diagnostics_distinguishes_never_established_from_corrupt_cross_key_pointer`)
  that a cross-key-corrupt pointer yields `canonical_pointer_ok=False`,
  while a package that has genuinely never had a pointer published yields
  `canonical_pointer_ok=True` with `canonical_record_id=None` — the broad
  `except Exception` in `summarize_package` does **not** collapse these
  two materially different states into one, contrary to what a naive
  reading of the `noqa: BLE001` comment might suggest. This was
  independently earned by direct construction and observation, not
  assumed from the comment's own claim.
- No repair occurs, no AER or pointer is created by any diagnostic call —
  confirmed by filesystem snapshot, not just by reading the "read-only"
  docstring claim.

---

## 14. Production Wiring Regression

Full end-to-end CLI-subprocess production lifecycle regression
(`decision-session create → evidence → select → preview → confirm →
readiness → governance-record publish`, both configured and unconfigured
cases) is already exercised exhaustively by
`tests/test_phase_147o1_authority_evaluation_production_wiring.py` and
`tests/test_phase_147o2_authority_evaluation_production_wiring_independent_verification.py`
(11+ real-subprocess tests) — both suites were re-run in this phase (§27)
and pass unchanged against the current, 147P-repaired storage layer,
confirming the hardening introduced no regression at the CLI/subprocess
level. Re-authoring that full subprocess lifecycle a third time was judged
to add no independent verification value beyond re-running the existing
suites plus this phase's own white-box confirmation below; it was not
duplicated.

This phase adds a white-box, source-level regression check the prior
phases did not perform: static AST inspection of
`AuthorityEvaluationService.evaluate_stage_2` (`service.py`) confirming
that **every** `CanonicalPointer(...)` construction in that method
supplies `package_id=package_id` — i.e. the same parameter the method was
called with, never a value read back from a pointer or otherwise derived
— and that its `read_canonical(...)` call site passes that identical
`package_id` name as its sole argument. This is a structural guarantee,
independent of any specific test input, that the production write path is
incapable of constructing a cross-key pointer by construction, not merely
"never observed to."

---

## 15. Supersession and Idempotency

Independently verified via a fresh 5-generation supersession history
(§6) that:

- Each generation's write and pointer-advance remains individually
  key-bound (`package_id` checked at every step, not just the final one).
- 10 independently-written packages, read back through a second store
  instance (restart simulation), each resolve to their own correct,
  most-recent generation.
- Cross-key validation introduces no interference with supersession
  history: no test constructed here or in Phase 147P's own suite found a
  legitimate supersession sequence rejected by the new checks.

---

## 16. Malicious Persisted State

Independently constructed four persisted-artifact-tampering scenarios
bypassing all public write APIs (`write_record`/`write_pointer` never
called for the malicious artifact):

1. **AER with internally mismatched `package_id`, physically placed under
   the correct directory, referenced by a same-key pointer** — caught by
   `read_canonical`'s `record.package_id != package_id` check
   (`CanonicalPointerCorruptError`).
2. **A fully self-consistent forged AER + forged pointer pair**, where the
   pointer's `pointer_digest` is correctly recomputed over the forged
   content (confirming digest verification alone was never the intended
   defense against this attack shape) — caught by the requested-key check.
3. **An AER copied verbatim (content and filename) into a different
   package's records directory** — independently confirmed `read_record`
   alone (digest-only) does **not** catch this (the digest is untouched,
   so the AER "verifies" under the wrong directory); only
   `read_canonical`'s own `record.package_id != package_id` check closes
   it, confirming that check is load-bearing, not redundant with the
   pointer-level check.
4. All of the above canonical reads, recovery, and diagnostics exercises
   in §12/§13 build on planted malicious state, not just synthetic
   in-memory objects.

All four fail closed without redirecting outside the requested namespace,
without mutation, and without automatic repair.

---

## 17. Contract Compatibility

Independently determined Phase 147P enforces AESIC-001 v1.3's existing
intent rather than altering normative semantics:

- **Pointer integrity (AESIC-REQ-126/127):** unchanged in kind — digest
  verification still runs exactly as before; the new checks are
  *additional* preconditions before a digest-verified record is trusted,
  not a replacement for digest verification.
- **Compound-key binding (adjacent to AESIC-REQ-119):** the contract's own
  "canonical pointer, package_id-keyed" design already implies the
  requested key is the authoritative lookup key — Phase 147P makes that
  implication an enforced invariant rather than introducing a new one.
- **AER integrity:** unaffected — `verify_aer_digest`/`AuthorityEvaluationRecord`
  (`records.py`) were not touched by Phase 147P (confirmed by `git diff`,
  §18).
- **Persistence/corruption/replay/restart:** all pre-existing recovery and
  restart guarantees (§12) continue to hold, independently re-verified.
- **Diagnostics:** the read-only, never-mutating, never-fabricating
  contract (AESIC-REQ-095/097) is unaffected — confirmed no diagnostic
  call creates filesystem state (§13).

No AESIC-001 amendment is required. No semantic change was discovered
beyond the intended hardening itself.

---

## 18. Architecture Preservation

Confirmed via `git diff` scoped to Phase 147P's **own** commit
(`017301e3^..017301e3`, not the full 147M..147P range, which would
over-count five intervening verification/certification phases):

```
src/pcae/aesic/diagnostics.py
src/pcae/aesic/errors.py
src/pcae/aesic/storage.py
```

— exactly the three files this phase's own independent read of the source
identified as touched (§4/§7/§11). No other `src/pcae/**` file was
modified by Phase 147P's own commit. In particular, confirmed untouched:
`src/pcae/authority_evaluation/evaluation.py` (the evaluator),
`src/pcae/authority_evaluation/registry.py`, `registry_filesystem.py`,
`template_store.py` (Registry/Decision Template Resolution), and
`src/pcae/governance/publication/coordinator.py` (Publication
Coordinator) — none appear in the diff.

AES remains the sole orchestrator (unchanged import graph: `service.py`'s
own imports were not touched); Interactive Workflow/CHGR semantics are
unaffected (neither package appears in the 147P diff at all). Only the
persistence-boundary validation logic changed, exactly as authorized.

---

## 19. Runtime Preservation

Confirmed by both the bootstrap-time `pcae runtime inspect` output (§1 of
this phase's execution, matching the authorization's required confirmation)
and independently by static import inspection of `storage.py`: no import
of any `pcae.runtime.*`/plugin-registry module exists anywhere in the
touched files. Runtime remains `Observed`, maximum capability `observe`,
execution `unavailable`. No plugin was added, removed, or modified.

---

## 20. Independent Security Analysis

Beyond Phase 147P's own tests, this phase specifically attacked:

| Vector | Result |
|---|---|
| Unicode fullwidth solidus lookalike (U+FF0F) | Not treated as a separator (correctly, per platform semantics); neutralized by pre-existing `_safe_name` before reaching disk — no bypass |
| Percent-encoded traversal (`%2e%2e`) | No decode step exists; `%` itself falls outside `_safe_name`'s allowed class and is neutralized — no bypass |
| Repeated separators (`pkg//etc`) | Rejected outright (contains `/`) |
| Whitespace-surrounded traversal (`" .."`, `"..\n"`, etc.) | Either rejected outright, or (not an exact `".."` match) still filesystem-contained — no bypass |
| Case-folding collision | **Real on this development platform's filesystem** — reproduced live: two differently-cased `package_id`s alias to the same physical file, yet the requested-key/embedded-key binding check still fails closed rather than silently serving the aliased content. Not a vulnerability; documented as informational (147Q-F-2, §21) since it is a genuine, environment-dependent behavior worth disclosing even though it fails safe. |
| Symlink substitution (static, pre-existing) | Rejected, including two-hop chains and pointer-file-itself symlinks (§9/§10) |
| Cross-root store copying | Not independently re-tested beyond what §16 already covers (copying content across package directories *within* one root); no production input can direct two distinct `AuthorityEvaluationRecordStore` instances at overlapping roots (confirmed unchanged from Phase 147O.2's own finding, §7 of that document — no CLI flag/env var/config accepts a root override) |
| Malicious pointer digest recomputation | Attempted and caught by the requested-key check, not digest verification (§16 item 2) — confirms digest verification was never the intended defense for this class |
| Stale pointer rollback | Not independently reachable: `write_pointer` always advances forward under `write_record`'s idempotency/supersession discipline (AESIC-REQ-023), unchanged by Phase 147P; not re-attacked here since Phase 147N already assessed this class (AESIC-N-02) as informational and it is orthogonal to the two findings this phase verifies |
| Cross-key history grafting | Covered by §16's AER-copy scenarios |
| Malformed JSON producing alternate parse forms | Not independently re-attacked; `json.loads` failure is already handled uniformly as `CanonicalPointerCorruptError`/`AuthorityEvaluationRecordCorruptError` via the existing `except (OSError, json.JSONDecodeError)` clauses in `read_pointer`/`_read_record_payload`, unchanged by Phase 147P and not part of this phase's repair-verification mandate |
| **TOCTOU check-then-use window** | **Real, reproduced deterministically (§10) — new finding 147Q-F-1** |

No fabricated severity: the TOCTOU finding is classified Minor, not
Blocking or Major, because its prerequisite (local, same-uid filesystem
write-race access to the AER store tree) already grants the attacker the
ability to write malicious content directly, without any race, as §16
demonstrates unconditionally.

---

## 21. Findings

### 147Q-F-1 — Minor / Informational

- **Severity:** Minor.
- **Affected component:** `AuthorityEvaluationRecordStore._ensure_within_root`
  and its callers (`_record_path`, `_pointer_path`, `_records_directory`),
  `src/pcae/aesic/storage.py`.
- **Reproduction:** `store._record_path("pkg-1", "ev-1")` validates
  containment via `.resolve()` and returns the *unresolved* `Path`. If the
  filesystem is mutated (a directory in the path replaced with a symlink
  to outside the configured root) between that call and the later write
  (`_write_exclusive_json`/`_write_atomic_json`, which re-walks the
  unresolved path), the write follows the swapped-in symlink and lands
  outside the configured AER root. Reproduced deterministically in
  `tests/test_phase_147q_...py::TestRootContainmentAndSymlinkAnalysis::test_toctou_symlink_swap_between_validation_and_write_can_redirect_output`.
- **Expected behavior:** containment holds atomically across validation
  and use.
- **Actual behavior:** containment is checked once, at validation time;
  a filesystem mutation in the intervening window is not re-checked.
- **Operational impact:** requires local, same-privilege filesystem write
  access to the AER store tree (`.pcae/authority-evaluation/records/**`)
  timed precisely around a legitimate store operation. An attacker with
  that prerequisite access can already write arbitrary malicious AER/
  pointer content directly, with no race required (§16) — the marginal
  capability this gap adds is redirecting a specific write's *target
  location* outside the configured root, not gaining write access it
  didn't already have.
- **Containment:** every *fresh* call to the same validation logic (i.e.
  not reusing a `Path` object obtained before the race) correctly
  re-resolves and rejects the swapped symlink — the window is exactly one
  check-then-use pair per operation, not a persistent bypass.
- **Repair scope (if pursued):** resolve the path once, validate the
  resolved form, and perform the actual filesystem operation against that
  same resolved path (or reopen using `O_NOFOLLOW`-equivalent discipline
  on the final path component) — a narrow, storage-layer-only change.
- **Certification impact:** none — does not affect this phase's verdict
  (§30 criteria are unaffected; this is a new, narrower, lower-severity
  observation, not a reopening of either verified finding).
- **Recommendation:** document as accepted residual risk or address in a
  narrowly-scoped future repair phase; not blocking.

### 147Q-F-2 — Informational

- **Severity:** Informational.
- **Affected component:** `AuthorityEvaluationRecordStore` on
  case-insensitive-but-case-preserving filesystems (default APFS on
  macOS, default NTFS on Windows).
- **Reproduction:** two `package_id`s differing only in case (`"Pkg-A"`
  vs. `"pkg-a"`) physically alias to the same on-disk pointer/record file.
  Reproduced live on this development machine
  (`tests/test_phase_147q_...py::TestFreshCrossKeyAndIdentifierAttacks::test_case_folding_alias_on_case_insensitive_filesystem_still_fails_closed`).
- **Expected/actual behavior:** the requested-key/embedded-key binding
  check (§5) correctly fails closed (`CanonicalPointerCorruptError`) when
  the aliased file's embedded content disagrees with the differently-cased
  query — this is *not* a vulnerability, the hardening's own fail-closed
  design absorbs it without a dedicated case-insensitivity check.
- **Operational impact:** none identified — not reachable in production
  (`package_id`s are always `f"prp-{uuid.uuid4().hex}"`, generated
  lowercase-hex and never operator-supplied), and even if two callers
  somehow chose differently-cased IDs, the result is a safe, loud failure,
  never silent cross-key content substitution.
- **Recommendation:** no action required; disclosed for completeness per
  this phase's mandate to identify real (not theoretical) filesystem
  behavior encountered during verification.

No Blocking or Major finding was identified.

---

## 22. Finding Closure Matrix

### AESIC-N-01

| Aspect | Detail |
|---|---|
| Original reproduction | §4 of this document — pre-repair `read_canonical("pkg-A")` returned `pkg-B`'s AER silently |
| Repaired symbol | `AuthorityEvaluationRecordStore.read_canonical`, `src/pcae/aesic/storage.py:226-275` |
| Independent post-repair test | `TestHistoricalPreRepairReconstruction::test_current_code_closes_aesic_n01_for_the_identical_forged_state` plus 10 further independent cross-key constructions (§5) |
| Result | **Closed** — every construction fails closed with `CanonicalPointerCorruptError` |
| Residual risk | None identified beyond 147Q-F-1/F-2 (neither reopens this finding — both are orthogonal, lower-severity observations) |

### 147O.2-F-1

| Aspect | Detail |
|---|---|
| Original reproduction | §7 of this document — pre-repair `_record_path("..", "ev-1")` resolved one level above `records/` |
| Repaired symbol | `_validate_identifier_component` + `_ensure_within_root`, `src/pcae/aesic/storage.py:54-165` |
| Independent post-repair test | `TestHistoricalPreRepairReconstruction::test_current_code_closes_147o2_f1_for_the_identical_input` plus the full identifier/root-containment/symlink matrix (§8-§10) |
| Result | **Closed** — every identifier attempted is rejected before filesystem access, or contained after `_safe_name` neutralization |
| Residual risk | 147Q-F-1 (TOCTOU, §21) — a narrower, check-then-use gap in the *containment* mechanism itself, not a reopening of the `".."`/traversal defect this finding named |

### New findings

| ID | Severity | Summary |
|---|---|---|
| 147Q-F-1 | Minor | Check-then-use (TOCTOU) window between root-containment validation and the later filesystem write |
| 147Q-F-2 | Informational | Case-insensitive-filesystem `package_id` aliasing; fails closed, not a vulnerability |

---

## 23. Overall Verdict

**AUTHORITY EVALUATION PERSISTENCE BOUNDARY HARDENING INDEPENDENTLY VERIFIED**

All success criteria from the phase authorization are met:

- AESIC-N-01 independently reproduced pre-repair and confirmed closed (§4, §22).
- Requested storage key remains authoritative (§5).
- Cross-key substitution fails closed in every construction attempted, 11
  distinct shapes total (§5, §16).
- 147O.2-F-1 independently reproduced pre-repair and confirmed closed
  (§7, §22).
- Unsafe identifiers fail before filesystem traversal (§8).
- Root containment holds (§9), including against two-hop symlink chains
  and pointer-file-level symlinks not tested by Phase 147P.
- Symlink containment is adequate for the supported same-machine,
  same-privilege trust assumption; the one real limitation found (147Q-F-1)
  is disclosed, bounded, and non-blocking (§10, §21).
- Same-key behavior remains unchanged (§6).
- Recovery remains correct, including under concurrent unrelated-key
  corruption (§12).
- Diagnostics remain safe and — independently confirmed, not assumed —
  distinguish corruption from absence (§13).
- Production wiring remains functional (§14, plus the full re-run of both
  prior production-wiring suites at §27).
- No contract amendment is required (§17).
- Runtime remains `Observed / observe / unavailable` (§19).
- No unresolved Blocking or Major defect remains (§21).

---

## 24. Recommended Next Phase

**147R — Authority Evaluation Chapter Certification Closure**

Per the phase authorization's §31: this phase found no repairable
Blocking or Major defect, so the narrowest-repair-phase alternative does
not apply. 147R should:

- Recheck the final limitations register against this document.
- Confirm AESIC-N-01 is closed (§22 — done here; 147R should ratify).
- Confirm 147O.2-F-1 is closed (§22 — done here; 147R should ratify).
- Determine whether Phase 147O.3's certification observations can now be
  retired, given both findings this phase names as their remaining open
  items are closed.
- Record the two new informational/minor observations (147Q-F-1, 147Q-F-2)
  as accepted residual technical debt, or schedule 147Q-F-1's narrow
  storage-layer repair, at the certifying phase's discretion.
- Recommend the next strategic phase — if no material certification
  observation remains, **148A — Next Strategic Capability Architecture**
  per the phase authorization's own fallback guidance.

This recommendation is not authorization.
