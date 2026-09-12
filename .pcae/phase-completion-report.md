# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1 — Durable Replay Store FIFO-at-Slot Nonblocking Hardening

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
- Alias: **N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN** (operator readability only; the full canonical CPIPC id is authoritative)
- Status: **COMPLETE**
- Predecessor: **N16-5-F-5-TB-HELPER-IV-R** (COMPLETE / INDEPENDENTLY VERIFIED), entry HEAD == `origin/main` == `3eff8b80`
- CPIPC: valid direct `.1` successor of the predecessor — independently re-derived via `pcae.core.phase_id` (`is_valid` True; `normalize(id) == id`; same series `149`; same branch `O`; exactly one appended `.1` segment, 59 vs 58; `compare` = less; exact canonical text; unique against `git log --all` and `git grep` across the working tree; no conflicting active governed phase); alias display-only, no discrepancy

## Summary

Closed exactly the one documented, non-blocking, availability-only finding
N16-5-F-5-TB-HELPER-IV-R left unrepaired: `DurableReplayStore._read()`
(`hpac_pawa_helper_replay_state.py`) opened a candidate replay record with a
blocking `O_RDONLY | O_NOFOLLOW` (no `O_NONBLOCK`) before its `S_ISREG`
check, so a FIFO planted at a record slot hung the read indefinitely
instead of failing closed quickly.

Before any change, the hang was independently reproduced against unmodified
HEAD (`3eff8b80`) in a genuinely separate OS process (`multiprocessing.Process`),
bounded by a 5-second `.join(timeout=...)` — the child process did not
return within the bound. The security classification was reconfirmed
availability-only by re-reading `_read()`'s exact control flow: the opened
descriptor's `S_ISREG` check runs before any `os.read()` call, both before
and after the repair, so a FIFO (with or without a writer connected) can
never have its bytes interpreted as replay content, and cannot bypass
provenance binding, generation binding, or turn an absent record into
`FRESH`.

**Production change:** exactly one call site — added `os.O_NONBLOCK` to the
open flags in `DurableReplayStore._read()`. No other production line,
contract, schema, or dependency changed.

**7 new focused tests** added to `tests/test_n16_5_f_5_tb_replay_repair.py`:
FIFO at the slot with no writer (fails closed promptly, not a hang), FIFO
with a background writer connected (still rejected as non-regular before
any byte is read), FIFO substituted over a previously-valid record (fails
closed), FIFO under a noncanonical namespace path (no effect on an
unrelated canonical reservation), symlink pointed at a FIFO (refused as a
symlink by the existing `O_NOFOLLOW` policy, never traversed to reach the
FIFO), a UNIX domain socket at the slot (rejected identically), and an
ordinary regular replay record proven unaffected by the nonblocking open.
Every FIFO/timing-sensitive test is bounded via a real subprocess with a
hard `timeout=` (never a bare in-process assertion, and never
`multiprocessing` fork, which was independently observed during this phase
to deadlock post-fork under pytest's own capture machinery on this
macOS/CPython 3.14 host) so a regression that reintroduces blocking fails
the suite promptly instead of hanging it.

The predecessor's own documented-finding test in
`tests/test_n16_5_f_5_tb_helper_iv_r.py` (renamed
`test_record_slot_fifo_blocks_open_instead_of_failing_closed_fast` →
`test_record_slot_fifo_fails_closed_fast_not_blocking_open`) was updated to
assert the now-repaired prompt fail-closed behavior instead of a hang, per
that test's own embedded instruction for exactly this case.

**Regression (independently re-run by the primary operator):** focused
replay-repair suite (now 76 tests: 69 predecessor + 7 new) — **76 passed, 0
failed**; IV-R suite (one test updated, tally unchanged) — **137 passed, 0
failed**; helper foundation suite (unmodified, `git diff` empty) — **51
passed, 0 failed, 1 skipped**, identical to the predecessor's tally. All of
the required replay-security-regression-lock scenarios (clean restart,
response loss, crash/indeterminate, concurrent duplicate, conflicting
replay, generation rotation, ordinary reset denial,
restart-dead-authority-vs-persistent-history) are part of the 76-test
replay-repair suite and all passed unchanged.

`fast_green` attribution performed via the governed
`pcae phase fast-green-attribution` tool (isolated-worktree
baseline-vs-candidate comparison), final run against the truly pushed
candidate: baseline commit `3eff8b80` (parent of this phase's own first
attributed commit; 359 raw failed / 9 errors); candidate commit
`102c91e3`, the final pushed HEAD (357 raw failed / 9 errors — 2 fewer,
both accounted for: the pre-push HEAD==origin/main scope-fence guard now
trivially passes, and one flaky unrelated node
(`tests/test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record`)
did not reproduce). `attributable_failures: []` (empty). Tool status:
**PASS**.

**Note on a self-corrected process mistake:** an earlier, local-only
attempt at this phase's implementation commit put the display alias in
parentheses before the colon (`Phase <id> (alias): ...`), which the
attribution tool's commit-subject regex does not parse — it silently
collapsed to a degenerate self-compare baseline (`baseline_commit ==
candidate_commit`, both the malformed commit itself), producing a spurious
359-failure tally and one spurious flaky attributable node
(`tests/test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record`).
This was caught by the primary operator before accepting any attribution
result, root-caused to the subject-line format, corrected by amending the
sole unpushed local commit's message (content unchanged) to the bare
`Phase <id>: <message>` form, and the tool was re-run to produce the
evidence above.

Contract trio byte-unchanged throughout this phase (sha256 independently
reconfirmed by the primary operator). No schema or dependency change. 0
live protected-host writes; 0 real ceremony; no FIDO2/YubiKey; no
production principal. Runtime `Observed` / `observe` / `unavailable`; 0
plugins / 0 capabilities; first governed runtime external effect **ABSENT
/ UNREACHABLE**.

**Verdict: N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN COMPLETE.**
FIFO-at-slot blocking-open finding: **CLOSED / HARDENED**. Durable replay
store: **HARDENED**. Replay-after-restart: **REMAINS CLOSED**. Helper
foundation: **REMAINS INDEPENDENTLY VERIFIED**, subject to this narrow
change, covered by this phase's own focused evidence. macOS same-file-object
execution: **FAIL-CLOSED / NOT IMPLEMENTED** (untouched). F-5-B2 **BLOCKED
PENDING REMAINING PLATFORM / CALLER MIGRATION / PACKAGING SLICES**; F-5
**CERTIFICATION BLOCKED**; **N-16-5 NOT CLOSED**; N-16-6 / N-16-7 **OPEN /
UNTOUCHED** (N-16-7 strictly last). This phase begins neither
caller/client integration, legacy in-process-path removal, packaging/install,
real certification, macOS same-file-object implementation, N-16-6, nor
N-16-7.

Full detail: `docs/PHASE_N16_5_F_5_TB_REPLAY_STORE_FIFO_HARDEN.md`.

## Contract Baseline

| Contract | File | sha256 |
|---|---|---|
| HPAC-PAWA-001 v2.0 | `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` | `b8809e5119a9955863a8b947301e781f25a26c9a4107a9a917f0de083336323e` |
| HPAC-PAWA-HELPER-001 v1.0 | `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` | `e7b30daeb1f6967fe985cf7394834e76a81acefb538a0038672aa026a5b58815` |
| HPAC-PPA-001 v2.0 | `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` | `27acaabcde8d1ac1793946f5858a391f1cd18deb9f20cbaeee2121db29cc9cd2` |

Byte-unchanged before and after this phase's work (independently
reconfirmed by the primary operator).

## Production Repair Performed

Exactly one call site changed: `os.O_NONBLOCK` added to
`DurableReplayStore._read()`'s open flags in
`src/pcae/core/hpac_pawa_helper_replay_state.py`. `git diff` against
`origin/main` for `docs/contracts/`, `schemas/`, `pyproject.toml` is empty
for the entire duration of this phase.

## Recommended Next

A caller/client integration architecture slice (design only, not
implementation) — **NOT begun**. Beyond that, per the absolute stop
boundary: no migration itself, no macOS same-file-object implementation,
no packaging/install, no real certification, no N-16-6, no N-16-7 without
fresh explicit human authorization for each.
