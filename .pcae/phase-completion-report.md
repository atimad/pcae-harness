# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1 — Fresh Independent Reverification of Privileged Helper + Durable Replay Foundation

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1`
- Alias: **N16-5-F-5-TB-HELPER-IV-R** (operator readability only; the full canonical CPIPC id is authoritative)
- Status: **COMPLETE**
- Predecessor: **N16-5-F-5-TB-REPLAY-REPAIR** (COMPLETE), entry HEAD == `origin/main` == `578c0455`
- CPIPC: valid direct `.1` successor of the predecessor — independently re-derived via `pcae.core.phase_id` (`is_valid` True; `normalize(id) == id`; same series `149`; same branch `O`; exactly one appended `.1` segment, 59 vs 58; `compare` = less; exact canonical text; unique against `git log --all` and `git grep` across the working tree; no conflicting active governed phase); alias display-only, no discrepancy

## Summary

Fresh, restart-from-scratch independent reverification of the privileged
helper protocol foundation and the just-completed replay-durability repair.
Neither predecessor phase's test suite or conclusions were trusted as
inherited PASS. A bounded delegated worker (no commit/push/task-close/
phase-complete authority) reconstructed all four helper/replay modules
(`hpac_pawa_helper_protocol.py` / `_operations.py` / `_os.py` /
`_replay_state.py`) from source and authored a fresh 1467-line, 137-test
adversarial suite (`tests/test_n16_5_f_5_tb_helper_iv_r.py`) plus a findings
document (`docs/PHASE_N16_5_F_5_TB_HELPER_IV_R.md`). The primary operator
independently re-read the full diff and both new files in full, independently
re-ran the new suite (137 passed), both existing regression suites
(120 passed / 1 skipped / 0 failed, confirmed byte-unchanged via `git diff`),
`fast_green` baseline-vs-candidate, and re-verified the contract-trio sha256
values, before accepting the work and proceeding to finalization.

**Core security question verified:** ordinary PCAE interpreter authority !=
protected helper authority (no import-graph path from any of the four
helper modules to `hpac_protected_admin_writer`, AST-verified; independently
grepped for `inspect`/`sys.modules`/`__module__`/`__name__`/frame-global/
ambient-identity trust patterns across all four modules — none found).
Helper authority dies with the process; only a durable, negative,
no-authority-export fact persists across restarts, fuzzed against every
`FORBIDDEN_AUTHORITY_TOKENS` member on both honest and tampered records.

**Generation-rotation resurrection (§15, CRITICAL) — no resurrection path
found.** A request consumed under generation G, replayed verbatim against a
store rotated to G+1, is denied `CONFLICTING`, never resurrected `FRESH`;
G's own consumed history is untouched. A distinct, legitimately G+1-signed
request correctly gets its own fresh keyspace slot (documented
partitioning, not a defect) — this conflation was caught and corrected in
the delegated worker's own first test draft.

**macOS classification:** same-file-object exec path — FAIL-CLOSED / NOT
IMPLEMENTED (security-complete, completeness-absent, verified via a
forced-platform test; not implemented this phase, per mandate). Peer
credentials — implemented and security-complete, genuinely exercised via a
real `AF_UNIX` socketpair + `getpeereid` on this host. Linux same-file-object
execution and `SO_PEERCRED` could not be genuinely exercised as Linux on
this macOS development host (no `/proc`) — reasoned about from source only,
flagged honestly as partial coverage rather than claimed as executed.

**One documented, non-blocking, low-severity finding (not repaired, per
this phase's IV-only mandate):** `DurableReplayStore._read()` opens a
candidate record with a blocking `O_RDONLY | O_NOFOLLOW` (no `O_NONBLOCK`)
before its `S_ISREG` check; a FIFO planted at a record slot (requires write
access already inside the `0700`, deployment-owner-only namespace) causes
the read to hang instead of failing closed quickly. Availability/DoS
exposure only — no confidentiality or integrity impact, and it does not
affect the CRITICAL generation-rotation property. Suggested smallest repair
(not applied): add `O_NONBLOCK` to that one `os.open()` call.

Closed operation/role/mutation/read-record vocabularies independently
confirmed source-derived (not merely duplicated constants) and
near-miss-rejecting. State machine (both in-process and durable) rejects
every tested skip-ahead/regression shape; no-auto-retry and evidence
staging correctly integrated under fault injection. Deterministic-vs-real
separation confirmed: `ReplayLedger.__init__`'s signature has no flag/env-var
path to fake durability. Filesystem provenance/atomicity/namespace safety
independently re-verified: digest mismatch, slot-binding mismatch, 8
malformed-record variants, truncated JSON, symlinked slot/namespace
component, group/other-writable slot/directory all fail closed; replay-key
namespace collision/traversal-safe against hostile inputs; retention never
prunes unresolved records. Real separate-OS-process tests confirm
restart-dead-authority with persistent, correctly-scoped history (clean
restart, response-loss retries, `SIGKILL` after commit, `SIGKILL` before the
boundary) and a real 8-process concurrent race yields exactly one winner.

Regression: both existing suites unmodified (`git diff` empty), 120 passed /
1 skipped / 0 failed. `fast_green` attribution performed via the governed
`pcae phase fast-green-attribution` tool (isolated-worktree baseline-vs-
candidate comparison): baseline commit `578c0455` (355 raw failed / 9
errors); candidate commit `a5c8202b` (356 raw failed / 9 errors).
`attributable_failures: []` (empty). The sole new candidate node,
`tests/test_phase_149o_20l_7n_1_dell_redeployment_proposition_independent_verification.py::TestCandidateCurrentness::test_head_equals_origin_main`,
was correctly classified by the tool itself as an `expected_phase_artifact`
(the known pre-push HEAD==origin/main scope-fence guard, expected given
`pushed_status=local_only` at attribution time; it resolves once this
phase is actually pushed). Tool status: **PASS**. An earlier, informal
spot-check by the primary operator (real file move, `-n auto`, non-isolated)
had independently surfaced a single different, flaky, unrelated node
(`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_2_1_pawa_writer_capability_integrity_repair.py::test_17_concurrent_use_permits_at_most_one_success`,
confirmed to reference no helper/replay module and to pass in 3 consecutive
standalone re-runs) which did not reproduce in the tool's own isolated-worktree
run — both independent checks agree on zero attributable security/replay/
semantic regressions from this phase's changes. Contract trio byte-unchanged
throughout (sha256 independently reconfirmed by the primary operator both
before delegation and after accepting the work). No schema or dependency
change. 0 live protected-host writes; 0 real ceremony; no FIDO2/YubiKey; no
production principal. Runtime `Observed` / `observe` / `unavailable`; 0
plugins / 0 capabilities; first governed runtime external effect **ABSENT /
UNREACHABLE**.

**Verdict: N16-5-F-5-TB-HELPER-IV-R COMPLETE / INDEPENDENTLY VERIFIED**
(with the one documented, non-blocking, low-severity finding above).
Replay-after-restart repair: **INDEPENDENTLY VERIFIED**. Protected helper +
HPAC-PAWA-HELPER/1.0 foundation: **INDEPENDENTLY VERIFIED**. Linux helper
platform profile: reasoned/not empirically re-exercised on real Linux this
phase (host limitation). macOS helper platform profile: **FAIL-CLOSED / NOT
IMPLEMENTED** (truthfully reported, not silently proceeded past).
F-5-B2 **BLOCKED PENDING REMAINING PLATFORM / CALLER MIGRATION / PACKAGING
SLICES**; F-5 **CERTIFICATION BLOCKED**; **N-16-5 NOT CLOSED**; N-16-6 /
N-16-7 **OPEN / UNTOUCHED** (N-16-7 strictly last). This phase begins
neither a narrow FIFO-hardening successor, nor any caller/client
integration, legacy in-process-path removal, packaging/install, real
certification, macOS same-file-object implementation, N-16-6, or N-16-7.

Full section-58 pass-criteria checklist, primary-operator independent
verification detail, and the 20-section adversarial test-suite breakdown:
`docs/PHASE_N16_5_F_5_TB_HELPER_IV_R.md`.

## Contract Baseline

| Contract | File | sha256 |
|---|---|---|
| HPAC-PAWA-001 v2.0 | `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` | `b8809e5119a9955863a8b947301e781f25a26c9a4107a9a917f0de083336323e` |
| HPAC-PAWA-HELPER-001 v1.0 | `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` | `e7b30daeb1f6967fe985cf7394834e76a81acefb538a0038672aa026a5b58815` |
| HPAC-PPA-001 v2.0 | `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` | `27acaabcde8d1ac1793946f5858a391f1cd18deb9f20cbaeee2121db29cc9cd2` |

Byte-unchanged before and after this phase's work (independently reconfirmed
by the primary operator).

## No Production Repair

The single finding (FIFO-at-slot blocking-open availability exposure) was
documented, not repaired, per this IV phase's bounded mandate. `git diff`
against `origin/main` for `src/`, `docs/contracts/`, `schemas/` is empty for
the entire duration of this phase.

## Recommended Next

A narrow, one-line governed hardening successor
(e.g. `N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN`) adding `O_NONBLOCK` to
`DurableReplayStore._read()`'s open call — **NOT begun**. Beyond that, per
the absolute stop boundary: no caller/client integration, no legacy
in-process-path removal, no packaging/install, no real certification, no
macOS same-file-object implementation, no N-16-6, no N-16-7 without fresh
explicit human authorization for each.
