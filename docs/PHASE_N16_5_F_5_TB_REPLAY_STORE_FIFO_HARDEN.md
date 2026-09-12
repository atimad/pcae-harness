# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1 (N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN)

**Durable Replay Store FIFO-at-Slot Nonblocking Hardening.**

## 0. Governance / phase identity

- Predecessor: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1`
  (alias `N16-5-F-5-TB-HELPER-IV-R`), COMPLETE / INDEPENDENTLY VERIFIED,
  commit `a5c8202b` (pushed as of `3eff8b80`). Confirmed via
  `PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json`
  (`status: completed`), the canonical Phase Report, and governed task
  state, all agreeing.
- CPIPC validation, independently re-derived via `pcae.core.phase_id`
  (`parse`/`is_valid`/`normalize`/`same_series`/`same_branch`/`compare`),
  not trusted from the authorization prompt's precomputed successor text:
  the successor is the predecessor with exactly one appended `.1` segment
  (58 → 59 subphase segments), `is_valid` True, `normalize(id) == id`,
  same series `149` / branch `O`, `compare` = less (strict forward
  ordering), unique against `git log --all -F --grep` at entry, no
  conflicting active governed phase.
- Entry state: branch `main`, HEAD == `origin/main` == `3eff8b80`,
  `origin/main..HEAD` = 0, tree clean.
- The FIFO-at-slot finding was reconfirmed present in current source
  (`DurableReplayStore._read()`, `hpac_pawa_helper_replay_state.py`) before
  any mutation, and reproduced independently (see §2) — not assumed from
  the predecessor's own report.

## 1. Purpose

Close exactly one documented availability finding:
`DurableReplayStore._read()` must not indefinitely block if a
filesystem object at a replay-record slot is a FIFO. Smallest safe
repair: add `O_NONBLOCK` to the read-path open call, preserving the
existing opened-object `S_ISREG` validation.

## 2. Pre-repair reproduction

A disposable temporary protected root was used to place a `mkfifo` at
the exact content-addressed slot `DurableReplayStore._read()` expects,
with no writer connected. `DurableReplayStore.check_and_reserve()` was
invoked in a genuinely separate OS process (Python `multiprocessing`,
bounded by a 5-second `.join(timeout=...)` from the parent) against
unmodified HEAD (`3eff8b80`). The child process did not return within
the bound — the open() call was still blocked — confirming the finding
reproduces exactly as N16-5-F-5-TB-HELPER-IV-R documented it, before any
source change.

## 3. Security classification (reconfirmed)

Re-inspected `_read()`'s exact control flow: the opened file descriptor
is `fstat`'d and its `S_ISREG` bit is checked **before** any `os.read()`
call is reached. This holds both before and after the repair. A FIFO
substituted at the slot — with or without a writer connected — is
therefore rejected before any byte is read from it: it cannot inject
replay bytes, cause malformed data to be accepted, bypass provenance
binding, turn an absent record into `FRESH`, alter replay identity,
bypass generation binding, leak protected data, or grant a writable
capability. The defect remains **availability-only** (a blocking
`open()`, nothing more); reclassification to a confidentiality,
integrity, replay, or authority defect was not found.

## 4. Production change

One file, one call site: `src/pcae/core/hpac_pawa_helper_replay_state.py`,
`DurableReplayStore._read()`. The open flags changed from
`os.O_RDONLY | O_NOFOLLOW` to `os.O_RDONLY | os.O_NONBLOCK | O_NOFOLLOW`.
No other production line changed. `O_NONBLOCK` was used (not an
alternative nonblocking-open technique) — it has no effect on regular-file
opens/reads on this platform, and makes a FIFO/socket open return
immediately regardless of whether a writer/peer is connected.

## 5. Regular-file validation / TOCTOU discipline

Unchanged: the `fstat(fd)` validation (`S_ISREG`, owner uid, group/other
writability) still runs against the descriptor `open()` actually
returned — never a separate `stat(path)` result — so the anti-TOCTOU
property this module already had is preserved exactly. `O_NONBLOCK`
changes only whether the initial `open()` call can block; it does not
touch the validation path at all.

## 6. Post-repair behavior verified

- FIFO, no writer: `_read()` returns promptly (bounded subprocess,
  5s timeout) and raises `ReplayStateCorruption("... not a regular
  file")` — never hangs, never treated as absent/fresh.
- FIFO, writer connected (a background process holding the write side
  open): still rejected as non-regular before any bytes are read as
  replay JSON.
- FIFO substituted over a previously-valid record: fails closed
  identically to the directory-substitution case.
- FIFO under a noncanonical namespace path (not the canonical slot):
  no effect on an ordinary, unrelated reservation (`FRESH` as normal).
- Symlink pointed at a FIFO: refused as a symlink by the existing
  `O_NOFOLLOW` policy (`ELOOP`), never traversed to reach the FIFO.
- Directory at the slot: already covered by the existing
  `test_unexpected_file_type_in_record_slot_refused`; unaffected by
  this change.
- UNIX domain socket at the slot: rejected identically (non-regular).
- Ordinary regular replay record: unaffected — opens, reads, and
  validates exactly as before; `check_and_reserve` and `_read` produce
  the same outcome as pre-repair.
- Missing-record (`ENOENT`) semantics: unchanged — `FileNotFoundError`
  handling is untouched, orthogonal to `O_NONBLOCK`.
- Malformed-record semantics (8 variants: not-JSON, wrong schema
  version, digest mismatch, etc.): unchanged, parser untouched.

## 7. Focused test suite

7 new tests added to `tests/test_n16_5_f_5_tb_replay_repair.py`:
`test_fifo_at_record_slot_without_writer_fails_closed_promptly`,
`test_fifo_at_record_slot_with_writer_still_rejected`,
`test_fifo_replacing_previously_valid_record_fails_closed`,
`test_fifo_under_noncanonical_namespace_has_no_effect_on_canonical_read`,
`test_symlink_to_fifo_record_slot_refused`,
`test_unix_socket_at_record_slot_refused`,
`test_regular_replay_record_unaffected_by_nonblocking_open`. All bounded
via a real subprocess with a hard `timeout=`, never a bare in-process
call and never `multiprocessing` fork (which deadlocks post-fork under
pytest's own capture machinery on this macOS/CPython 3.14 host — observed
directly during this phase, not theoretical) — a regression that
reintroduces blocking fails the suite promptly instead of hanging it.

The predecessor's own documented-finding test,
`test_record_slot_fifo_blocks_open_instead_of_failing_closed_fast` in
`tests/test_n16_5_f_5_tb_helper_iv_r.py`, was renamed to
`test_record_slot_fifo_fails_closed_fast_not_blocking_open` and its
assertion inverted to expect prompt fail-closed behavior instead of a
hang, per that test's own embedded instruction: "if this assertion ever
fails it means the finding was independently repaired ... and this test
should be updated."

## 8. Regression tallies (independently run)

- Focused replay-repair suite (`tests/test_n16_5_f_5_tb_replay_repair.py`,
  now including the 7 new FIFO tests): **76 passed, 0 failed** (69
  predecessor tests + 7 new).
- IV-R suite (`tests/test_n16_5_f_5_tb_helper_iv_r.py`, one test updated
  per §7): **137 passed, 0 failed** (unchanged tally from predecessor;
  the updated test's assertion direction changed, its count did not).
- Helper foundation suite
  (`tests/test_hpac_pawa_helper_protocol_foundation.py`, unmodified):
  **51 passed, 0 failed, 1 skipped** — identical to the predecessor's
  tally.
- All 3 of the security-regression-lock scenarios required by this
  phase's mandate (clean restart, response loss, crash/indeterminate,
  concurrent duplicate, conflicting replay, generation rotation, ordinary
  reset denial, restart-dead-authority-vs-persistent-history) are part
  of the 76-test replay-repair suite above and all passed unchanged.
- `fast_green` attribution: see §9 (embedded structured evidence in
  `.pcae/phase-completion-metadata.json` / canonical report).

## 9. Fast Green attribution

See the structured `test_results.fast_green` evidence embedded in the
canonical Phase Report and `.pcae/phase-completion-metadata.json`,
produced by the governed `pcae phase fast-green-attribution` tool
(isolated-worktree baseline-vs-candidate comparison against this
phase's own commit history, not a hand-typed summary).

## 10. Scope discipline confirmed

0 contract files changed (`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`,
`HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`,
`HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` untouched). 0 schema
files changed. 0 `pawa_failure_code` / RHAMP `terminal_reason_code`
values added. 0 dependency changes (`pyproject.toml` untouched). 0 live
protected-host writes (every test uses a disposable `tmp_path` protected
root). 0 real ceremony (no FIDO2/YubiKey, no PIN/touch, no
makeCredential/getAssertion, no APPROVE/REJECT, no production principal).
Runtime unchanged: `Observed` / `observe` / `unavailable`; 0 plugins / 0
capabilities; first governed runtime external effect **ABSENT /
UNREACHABLE**.

## 11. Disposition

- FIFO-at-slot blocking-open finding: **CLOSED / HARDENED**.
- Durable replay store: **HARDENED** (this one finding; no other change).
- Replay-after-restart (N16-5-F-5-TB-REPLAY-REPAIR): **REMAINS CLOSED**.
- Helper foundation (N16-5-F-5-TB-HELPER-IV-R): **REMAINS INDEPENDENTLY
  VERIFIED**, subject to this narrow change, which this phase's own
  focused evidence (§7-§8) covers.
- macOS same-file-object execution: **FAIL-CLOSED / NOT IMPLEMENTED**
  (untouched by this phase).
- F-5-B2: **BLOCKED PENDING REMAINING PLATFORM / CALLER MIGRATION /
  PACKAGING SLICES**.
- F-5: **CERTIFICATION BLOCKED**.
- N-16-5: **NOT CLOSED**.
- N-16-6 / N-16-7: **OPEN / UNTOUCHED** (N-16-7 strictly last).

## 12. Next-slice dependency analysis (recommended, NOT begun)

This phase closed the one narrow finding it was authorized to close. It
does not automatically follow that macOS same-file-object execution is
the next slice: per this phase's own governance mandate (§27 of the
authorization), that must be an explicit, independently-reasoned choice,
not an assumption.

Direct repository evidence considered:
- The macOS same-file-object exec path is FAIL-CLOSED / NOT IMPLEMENTED
  by design (verified via a forced-platform test in the IV-R suite); the
  genuine Linux same-file-object exec path has never been exercised as
  Linux on this macOS development host (no `/proc`).
- No caller (certification coordinator, HPAC admin caller, presentation
  caller) has yet been migrated to `DurableReplayStore` / the new helper
  execution path; all such callers remain on the legacy in-process
  authority path, per the absolute stop boundary preserved through every
  phase in this chain so far.
- Caller/client integration is architecturally independent of macOS
  helper execution: a caller can be migrated to call through the
  documented helper-invocation surface using a deterministic/Linux (or
  platform-abstracted) execution path in tests, while macOS execution
  stays explicitly unsupported/fail-closed, exactly as this phase's own
  regression suite already exercises the Linux-only real-exec path via
  `skipif`.

**Recommended next phase: caller/client integration architecture
slice** (Option B of the authorization's §26 menu) — begin designing how
an existing caller (e.g. the certification coordinator) is migrated to
invoke the durable helper/replay path, without requiring macOS
same-file-object execution as a prerequisite, and without beginning the
migration itself. Not begun in this phase; requires fresh explicit human
authorization.
