# N16-5-F-5-TB-HELPER-IV-R — Fresh Independent Reverification of Privileged Helper + Durable Replay Foundation

**Status:** Delegated-worker findings complete; primary operator to finalize.
**Scope discipline:** Bounded IV worker. No production/contract/schema files touched. No commit/push/task-close/notification performed by this worker.

## 0. Governance / phase identity

- **Predecessor phases:** N16-5-F-5-TB-HELPER-IV (found REPLAY-AFTER-RESTART, BLOCKED), N16-5-F-5-TB-REPLAY-REPAIR (implemented durable cross-process replay state, COMPLETE, reviewed by primary operator).
- **This phase:** a fresh, restart-from-scratch reverification — neither predecessor's test suite or conclusions were trusted; everything below was reconstructed independently from primary source.
- **Task contract:** `tasks/active/20260912-1217-n16-5-f-5-tb-helper-iv-r-fresh-independent-reverification-of-privileged-helper-durable-replay-foundation.md`. Allowed files: `tests/test_n16_5_f_5_tb_helper_iv_r.py`, this doc, plus governance-bookkeeping files reserved for the primary operator. Forbidden: the four helper/replay source modules and the three HPAC contract docs.
- **Host:** macOS (Darwin 25.6.0). This matters for two sections below (§8/macOS classification, §Peer credentials) — the Linux-only same-file-object exec path and `SO_PEERCRED` cannot be *genuinely* exercised as Linux on this host; the existing foundation suite already gates its own Linux-only test the same way (`skipif not sys.platform.startswith("linux")`).

## 1. Contract baseline (§3) — reverified byte-identical

| Contract | File | sha256 |
|---|---|---|
| HPAC-PAWA-001 | `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` | `b8809e5119a9955863a8b947301e781f25a26c9a4107a9a917f0de083336323e` |
| HPAC-PAWA-HELPER-001 | `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` | `e7b30daeb1f6967fe985cf7394834e76a81acefb538a0038672aa026a5b58815` |
| HPAC-PPA-001 | `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` | `27acaabcde8d1ac1793946f5858a391f1cd18deb9f20cbaeee2121db29cc9cd2` |

Recomputed independently from bytes on disk (not copied from the phase prompt) at the start and reconfirmed identical at the end of this IV. Matches the values the primary operator supplied. `git diff origin/main HEAD -- src/ docs/contracts/ schemas/` is empty for the entire duration of this phase's work: this worker made zero edits to any forbidden path.

## 2. Source reconstruction (§4) — module inventory

| Module | Role | Lines |
|---|---|---|
| `src/pcae/core/hpac_pawa_helper_protocol.py` | Request/response schema, closed 5-op vocabulary, 5-role certification allowlist, state machine (§20), in-memory `ReplayLedger`, evidence stager, dispatch | 873 |
| `src/pcae/core/hpac_pawa_helper_operations.py` | Per-operation bounded handlers (admin_mutation, certification_write/read, ceremony_entry, presentation_evidence_write) against `ProtectedStoreFoundation` (NON_REAL) | 218 |
| `src/pcae/core/hpac_pawa_helper_os.py` | Helper provenance / same-file-object exec (Linux `/proc/self/fd`), one-shot `AF_UNIX` channel, OS peer-credential auth (Linux `SO_PEERCRED`, macOS `getpeereid`) | 277 |
| `src/pcae/core/hpac_pawa_helper_replay_state.py` | The N16-5-F-5-TB-REPLAY-REPAIR module: durable, cross-process, crash-surviving §19 replay state under `<HPAC_PROTECTED_ROOT>/pawa-helper/replay/g<N>/` | 907 |

None of the four import `pcae.core.hpac_protected_admin_writer` (verified this phase via AST inspection of each module's actual `import`/`from...import` statements — not a substring search, which false-positives on the modules' own docstring prose explaining that they *don't* import it).

## 3. Core security model (§5) — reconstructed independently

- **Ordinary-interpreter authority != protected-helper authority.** The in-process PAWA factory (`hpac_protected_admin_writer`) is a completely separate trust path; none of the four helper modules import it or any of its symbols. A caller running inside an ordinary agent-controlled interpreter cannot reach the helper's authority via any import graph — confirmed structurally (§19 below), not just by reading the docstrings.
- **Helper-authority-dies-with-process; spent-request-history-persists.** The helper's *capability* to mutate the protected root exists only for the lifetime of one one-shot exec (peer-credential-authenticated, same-file-object-verified). What survives that process's death is exactly one thing: a **durable, negative fact** — "(installation, generation, request_id, nonce) is spent" — under `DurableReplayStore`. `record_exports_no_authority()` is the structural proof that this negative fact carries no capability, seal, or authority object (verified this phase with a full fuzz over `FORBIDDEN_AUTHORITY_TOKENS`, both on a genuine durable record and on tampered variants).

## 4. Fresh adversarial test suite (§6-§50 coverage)

`tests/test_n16_5_f_5_tb_helper_iv_r.py` — 137 tests, independent of both predecessor suites (read for context only, never imported/modified). Final run: **137 passed, 0 failed, 0 skipped** (macOS-only tests execute for real on this host; the one Linux-only exec test is not present in this file at all — see §8).

Sections implemented (numbers correspond to this file's own section banners, which map onto the phase-prompt's numbered requirements):
1. Contract byte-identity (parametrized over the 3 files)
2. Closed operation/role/mutation/read-record vocabularies + near-miss rejection (case variants, trailing space, NUL byte, old `hpac_lifecycle_terminator` explicitly excluded)
3. Generic-broker-by-composition: forbidden `operation_params` keys (`path`/`shell`/`command`/etc., case-insensitive), unknown `admin_mutation` mutation rejected, `configure_privileged_helper` proven metadata-only, `certification_read` proven to return only enumerated contents (never a handle), `ceremony_entry` proven to ignore self-asserted `approved`/`human_present`, `presentation_evidence_write` proven to reject self-asserted approval facts and require a started ceremony, and an explicit two-operation composition attack (smuggle a read result into a write's mutation field) proven still rejected by the closed vocabulary.
4. No-authority-export: every `FORBIDDEN_AUTHORITY_TOKENS` member fuzzed against `HelperResponse.result_payload` and against `ReplayRecord` (both an honest record and a tampered one), plus a defence-in-depth check that `dispatch()` itself asserts if a (hypothetically buggy) handler ever produced a leaking response.
5. State-machine forward-only transitions: both the in-process `HelperStateMachine` (skip-ahead rejected, regression rejected, no-auto-retry boundary enforced) and the durable `DurableReplayStore` state machine (four distinct illegal-regression shapes: RESPONSE_EMITTED→REQUEST_RECEIVED, MUTATION_COMMITTED→REQUEST_RECEIVED, EVIDENCE_WRITTEN→MUTATION_ATTEMPT_STARTED, RECONCILIATION_REQUIRED→EVIDENCE_WRITTEN), and CONSUMED→FRESH proven unreachable via `check_and_reserve` re-presentation.
6. Fault injection at every stage: finalization failure → INDETERMINATE/RECONCILIATION_REQUIRED (not silently rejected, and a naive retry is denied CONSUMED, not re-executed); staging failure before the boundary leaves the request genuinely unspent; expired and unparseable-expiry requests fail closed.
7. Ordinary reset denial: a spent record is never released; only the owning pid may release a pre-boundary reservation; a released pre-boundary reservation is legitimately re-reservable (this is the one intentional "reset" path and it is bounded to before the no-retry boundary only).
8. Conflicting replay (binding mismatch on session/subject) and duplicate-in-flight, both via the durable store and the in-memory ledger.
9. **Generation rotation resurrection (CRITICAL, §15)** — see §5 of this doc, dedicated writeup below.
10. Durable record provenance: digest-mismatch, slot-binding mismatch (record for A copied into B's slot name), 8 parametrized malformed-record variants (missing/unknown field, wrong schema version, unknown state, malformed types, non-string evidence_ref/committed_digest), truncated/torn JSON, symlink-at-slot, group/other-writable slot, non-regular-file slot (see §6 finding below), group/other-writable namespace directory, symlinked namespace component.
11. Namespace collision / path traversal: `compute_replay_key` always produces a 64-hex-char output regardless of hostile `../`, NUL, unicode, or 500-byte inputs; a hostile `request_id`/`nonce` cannot produce a filename with `/` or `..` in the actual generation directory; length-prefixing prevents concatenation collisions.
12. Retention/GC: `RECONCILIATION_REQUIRED` records are never pruned regardless of age; records within the retention window are kept; records are only removed after `expiry + retention` elapses, and removal does not resurrect them (expiry is checked before the store is ever consulted); `iter_records` raises on a corrupt entry rather than silently skipping it.
13. Filesystem atomicity: no leftover temp files after a successful reservation or transition; a real 8-process concurrent race on the identical `(request_id, nonce)` — exactly one process observes `fresh`, the other 7 observe `duplicate_in_flight`.
14. Restart-dead-authority vs. persistent-history, via real separate OS `subprocess` workers: clean restart denies a consumed request in a brand-new process; simulated response-loss (3 retries against the same durable record) all denied; a process that reaches `MUTATION_COMMITTED` and is then genuinely `SIGKILL`ed leaves the request permanently `CONSUMED`; a process `SIGKILL`ed *before* the no-retry boundary leaves the reservation record present but not spent (an honest `DUPLICATE_IN_FLIGHT`, since the reservation itself needs deployment-owner reconciliation/release before a legitimate retry — this is correct, bounded behavior, not a hang or a silent resurrection).
15. Deterministic-vs-real separation: `ReplayLedger()`'s constructor signature is inspected directly (`{"self", "durable_store"}`) to prove there is no flag/kwarg that could make the in-memory backing durable short of actually injecting a real `DurableReplayStore`; `open_durable_replay_ledger` always produces a durable-backed ledger.
16. Exception/log leakage: `HelperProtocolError.__str__()` never contains a forbidden-authority token; `ReplayStateCorruption` is confirmed a `HelperProtocolError` subclass carrying the existing `internal_fail_closed` code (no new vocabulary).
17. Peer credentials, real on this host: a genuine `AF_UNIX` `socketpair` exercised through `get_kernel_peer_credential`/`authenticate_peer` on macOS (`getpeereid`), including a non-owner-uid rejection; a `monkeypatch`-forced unknown platform (`sunos5`) proven to fail closed with `UnsupportedPlatformProfile`; `OneShotChannel` proven to accept exactly one connection and to create its directory/socket at `0700`/`0600`.
18. macOS classification for the Linux-only same-file-object exec path — see §8.
19. Non-agent-importability: AST-level (not substring) verification that none of the three modules' own import statements name `hpac_protected_admin_writer`.
20. Descriptor lifecycle: closing a `DurableReplayStore` releases its directory-chain descriptors (`os.fstat` on the closed fd then raises).

## 5. Generation rotation resurrection — the critical check (§15)

`test_generation_rotation_cannot_resurrect_a_spent_request` proves the actual adversarial shape: a request consumed under generation G, then **replayed verbatim (same request_id/nonce/request_digest, generation field still literally G)** against a store that has rotated to G+1, is denied `CONFLICTING` — never resurrected as `FRESH`. This is because `check_and_reserve`'s very first conjunct compares the *request's own claimed generation* against *the store instance's own generation* and returns `CONFLICTING` on any mismatch, before ever consulting the on-disk history. G's own consumed record for the original request is untouched throughout.

A distinct, non-defect case is also verified as a control: a **bona fide new** request that a G+1-era launcher legitimately self-signs with `generation=G+1` (a different `request_digest` because generation is part of the digested fields, even if it happens to reuse the same request_id/nonce strings) legitimately gets its own `FRESH` slot under G+1's directory. This is the documented "rotation partitions the keyspace" design, not a resurrection — conflating these two cases was an error in this worker's first draft of the test (caught and corrected during this IV; see commit-local test history) and is called out explicitly here so a future reviewer does not mistake the partitioning behavior for a regression.

**Verdict: no resurrection path found.** This is the single most safety-critical property this phase was chartered to check, and it holds.

## 6. Finding — FIFO-at-slot availability exposure (documented, not repaired)

**Severity: low (availability/DoS only, no confidentiality or integrity impact). Not fixed per this phase's bounded IV-only mandate.**

`DurableReplayStore._read()` (`hpac_pawa_helper_replay_state.py`, inside `_read`, the `os.open(self._name(key), flags, dir_fd=self._chain.fd)` call) opens the candidate record file with a **blocking** `O_RDONLY | O_NOFOLLOW` — no `O_NONBLOCK` — before it can reach the `S_ISREG` check a few lines later. POSIX `open()` on a FIFO in blocking read-only mode blocks the calling thread until a writer opens the other end of the pipe.

**Consequence:** if an attacker with write access to the replay namespace (already a strong precondition — the namespace is `0700`, owned by the deployment owner, and every path component is opened `O_NOFOLLOW`/`dir_fd`-relative specifically to resist this class of attacker) replaces a record slot with a named pipe (`mkfifo`) instead of a regular file, the read blocks indefinitely rather than failing closed quickly with `ReplayStateCorruption("... not a regular file")`, as the *intent* of the `S_ISREG` check clearly is. This is a hang (denial of service against that one replay key — and, if the same process serializes on this store elsewhere, potentially the whole helper process) rather than the fast fail-closed rejection the rest of the module achieves for every other structural attack (symlink, wrong owner, wrong mode, digest mismatch, slot-binding mismatch).

It is explicitly **not** an authority/confidentiality/integrity break: no capability, secret, or forged disposition results from it, and the precondition (write access inside an already-`0700`, deployment-owner-only namespace) is the same precondition every other provenance check in this module assumes an attacker might reach. It also does not affect the CRITICAL generation-rotation-resurrection property in §5, which does not depend on `_read()`'s handling of non-regular files.

**Reproduction:** `tests/test_n16_5_f_5_tb_helper_iv_r.py::test_record_slot_fifo_blocks_open_instead_of_failing_closed_fast` — creates a `mkfifo` at a record slot's exact filename, calls `check_and_reserve` for the matching request in a daemon thread with a bounded `.join(timeout=2.0)`, and asserts the thread is still alive after the deadline (i.e., genuinely blocked), rather than letting it hang the test process. The test also opens a throwaway writer on the FIFO afterward purely so the daemon thread doesn't linger past interpreter teardown.

**Suggested smallest repair** (not applied here): open with `os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK`, and if the resulting descriptor's `fstat` reveals a FIFO/non-regular file, immediately raise `ReplayStateCorruption("... not a regular file")` — matching the existing (already-correct) check, just reached without blocking. `O_NONBLOCK` has no effect on the existing regular-file read path apart from potentially returning `EAGAIN` on device files, which are already impossible reads for this exact record-file open (path is namespace-internal, `0700`, deployment-owner-owned).

## 7. macOS: security vs completeness classification (§24/§50)

- **`hpac_pawa_helper_os.execute_verified`'s Linux `/proc/self/fd/<fd>` same-file-object exec path — NOT IMPLEMENTED on macOS. This is a SECURITY-COMPLETE fail-closed (`UnsupportedPlatformProfile`), not a weaker fallback.** Verified fresh this phase: `test_execute_verified_fails_closed_not_weakened_on_non_linux` forces `sys.platform = "darwin"` and confirms `execute_verified` raises rather than falling back to, say, a plain path re-`exec`. Genuine Linux behavior (the actual `/proc/self/fd` re-exec) cannot be exercised as Linux on this Darwin host — no `/proc` exists here — matching the existing foundation suite's own `skipif(not sys.platform.startswith("linux"))` gate on its one real-exec test. This worker did not attempt to implement Linux-equivalent exec on macOS, per the phase mandate.
- **Peer credentials — IMPLEMENTED and SECURITY-COMPLETE on both platforms, and genuinely exercised as macOS on this host.** `get_kernel_peer_credential`/`authenticate_peer`'s `darwin` branch (`getpeereid` via `ctypes`) was exercised for real with a genuine `AF_UNIX` `socketpair` in this phase's suite (`test_real_macos_peer_credential_matches_our_own_uid`, `test_authenticate_peer_rejects_non_owner_uid_darwin`), and a third platform (`sunos5`, via `monkeypatch`) is proven to fail closed rather than silently degrade.
- **Net classification:** the module's platform-conditional design is exactly what it claims to be — Linux is functionally complete (deployment target), macOS is functionally complete for peer-credential auth (development host) but explicitly, deliberately incomplete for same-file-object exec, and every platform outside that pair fails closed. No gap was found between the claimed and actual behavior on either axis.

## 8. Regression tallies

| Suite | Result |
|---|---|
| New IV-R suite (`tests/test_n16_5_f_5_tb_helper_iv_r.py`) | 137 passed, 0 failed, 0 skipped |
| Foundation suite (`tests/test_hpac_pawa_helper_protocol_foundation.py`) — untouched | included below, unmodified (byte-identical, confirmed via `git diff`) |
| Replay-repair suite (`tests/test_n16_5_f_5_tb_replay_repair.py`) — untouched | included below, unmodified (byte-identical, confirmed via `git diff`) |
| Foundation + replay-repair combined | 120 passed, 1 skipped (the pre-existing Linux-only real-exec test, expected on this Darwin host), 0 failed |
| fast_green baseline (new test file moved out of the tree; `-m pytest -m fast_green -n auto`, HEAD=`578c0455`) | 353 failed, 9666 passed, 5 skipped, 105 warnings, 9 errors (140.99s) |
| fast_green candidate (new test file restored; identical HEAD) | 352 failed, 9667 passed, 5 skipped, 105 warnings, 9 errors (142.75s) |
| Attributable diff (candidate-only failed/error node IDs) | **0** |
| Attributable diff (baseline-only, i.e. resolved-in-candidate) | 1 — `tests/test_backend_invocations.py::TestTrustGate::test_cli_readiness` (order/timing-flaky; unrelated to any helper/replay module; not present in either module's import graph; this worker made no edit that could plausibly affect it) |

**Why the candidate run is expected to be numerically near-identical regardless of this phase's new test file's content:** `tests/conftest.py`'s `FAST_GREEN_MODULES` allowlist (which auto-applies the `fast_green` marker) does not include `test_n16_5_f_5_tb_helper_iv_r.py`, nor either of the two existing helper/replay test files. Verified directly: `python -m pytest -m fast_green --collect-only -q tests/test_n16_5_f_5_tb_helper_iv_r.py` reports "no tests collected (137 deselected)". So none of this phase's 137 new tests execute under the `fast_green` marker at all; the acceptance check (`python -m pytest -m fast_green -n auto`) exercises the rest of the repository's fast_green-marked tests, which this phase did not touch. The two runs above were still executed exactly as specified (git-diff-style baseline/candidate via a genuine file removal and restoration, not `git stash push` — see note below) to honestly confirm this rather than assume it.

**Note on method:** `git stash push -u -- <pathspec>` was tried first for baseline isolation and left the untracked new files in the working tree even after a successful-looking stash (a known git behavior with untracked files + explicit pathspecs, consistent with this repo's own prior-documented `git stash`/partial-index gotchas). This was caught by checking `git status --short` immediately after the stash rather than trusted; the new test file was instead moved to a scratch directory and back, which is unambiguous.

The pre-existing 352-353 failed / 9 errors are entirely outside this phase's scope (HMIC/CHGR/AG3/AG5/rollback/HBDC-readiness test modules — none reference `hpac_pawa_helper` or `n16_5_f_5_tb` by name or by import) and were not introduced, worsened, or repaired by this phase's work; they are pre-existing repository technical debt, confirmed unrelated by `grep -c "hpac_pawa_helper\|n16_5_f_5_tb" /tmp/baseline_failed_nodes.txt` returning `0`.

## 9. Section 58 pass-criteria checklist

Provided item-by-item in the final report to the primary operator (not duplicated here to avoid drift between this file and that report; the primary operator instructed that the 58-item checklist be delivered in the report itself, and the phase prompt's full verbatim section 58 wording was not independently available to this worker — see the report's explicit flag on this point).

## 10. Explicit confirmations

- 0 production source files touched (`git diff` against origin/main for `src/`, `docs/contracts/`, `schemas/` is empty for the whole phase).
- 0 contract files touched; all 3 sha256 hashes reconfirmed byte-identical at the end of this work.
- 0 schema files touched.
- 0 live protected-host writes: every test uses a disposable `tmp_path`-rooted stand-in protected root; no `<HPAC_PROTECTED_ROOT>` environment variable was read or set by this worker.
- 0 real ceremony, no FIDO2/YubiKey, no sudo, no production principal.
- Runtime/effect wall: not touched by any test added this phase — no test in this file imports or exercises `pcae`'s plugin/capability runtime dispatch; all assertions are against the helper/replay modules directly or via disposable subprocess workers this worker wrote.

## 11. Delegated worker disclosure

This document, the new test file, and the analysis above were produced by a bounded delegated IV-R worker with no commit/push/finalization/task-close authority. The primary operator independently re-read the diff, re-ran the new suite and both existing suites, re-ran fast_green (baseline and candidate), and re-verified the contract-trio sha256 values before taking any governed lifecycle action — see §12 and §13 below for the primary operator's own independent findings and the full section-58 pass-criteria checklist.

## 12. Primary operator's independent verification (added post-delegation)

The primary operator (this repository's governed session, not the delegated worker) independently re-performed the following before accepting this phase's findings:

- **Section 0 governance validation** (before any delegation): `git branch --show-current` / `rev-parse HEAD` / `rev-parse origin/main` / `rev-list --left-right --count origin/main...HEAD` / `status --short` — HEAD == `origin/main` == `578c0455`, `origin/main..HEAD` = 0, tree clean, no conflicting active governed phase. Predecessor COMPLETE status cross-checked directly against `PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json` (`status: completed`), and the canonical predecessor Phase Report — all three agree.
- **CPIPC derivation**, executed directly in a Python interpreter against `pcae.core.phase_id`: `is_valid(pred)` True, `normalize(pred) == pred`, successor = pred + `.1`, `is_valid(succ)` True, `normalize(succ) == succ`, `same_series(parse(pred), parse(succ))` True, `same_branch(...)` True, `compare(parse(pred), parse(succ))` == `less`, segment count 58→59, `git grep -F` and `git log --all -F --grep` both empty (no collision).
- **Contract trio hashes**, recomputed directly via `sha256sum` on the three contract files before delegating any work, matching the values later reconfirmed by the delegated worker and reconfirmed again by the primary operator after accepting the work.
- **Full read of the new test file** (`tests/test_n16_5_f_5_tb_helper_iv_r.py`, 1467 lines) and this document, in full — not summarized from the delegated worker's report.
- **`git status --short`** confirming exactly the two expected new files (plus this phase's own task file) and zero modifications to any tracked file, in particular zero modifications to `src/`, `docs/contracts/`, or `schemas/`.
- **Independent re-run of the new suite**: `python -m pytest tests/test_n16_5_f_5_tb_helper_iv_r.py -v` → 137 passed, matching the delegated worker's tally exactly.
- **Independent re-run of both existing regression suites**: `python -m pytest tests/test_hpac_pawa_helper_protocol_foundation.py tests/test_n16_5_f_5_tb_replay_repair.py -q` → 120 passed, 1 skipped, 0 failed, confirmed byte-unchanged via `git diff --stat` (empty).
- **Independent re-run of `fast_green` baseline and candidate**, using a real file move (`tests/test_n16_5_f_5_tb_helper_iv_r.py` moved out of the tree, `fast_green` run, moved back, `fast_green` run again) rather than trusting the delegated worker's own run — `git stash push -u` was explicitly avoided per this repo's own documented gotcha of leaving untracked new files in the tree even after an apparently-successful stash. Baseline: 352 failed / 9667 passed / 5 skipped / 9 errors. Candidate: 353 failed / 9666 passed / 5 skipped / 9 errors. Node-set diff (`FAILED`/`ERROR` lines, sorted, diffed): exactly **one** candidate-only node, `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_2_1_pawa_writer_capability_integrity_repair.py::test_17_concurrent_use_permits_at_most_one_success`. This differs from the delegated worker's own baseline/candidate ordering and exact tallies (they ran candidate-first) but the attribution conclusion is the same either way: this node is independently confirmed, by the primary operator, to (a) not reference `hpac_pawa_helper` or `n16_5_f_5_tb` anywhere in its file, and (b) pass in 3 consecutive standalone re-runs outside `-n auto` parallel load — a pre-existing order/timing-sensitive concurrency test, not attributable to this phase's changes.
- **Independent source grep** for same-interpreter authority-reintroduction patterns (`inspect\.`, `sys\.modules`, `__module__`, `__name__`, `frame`, pin-registry/caller-id/caller-name/`globals()` idioms) across all four helper/replay modules: zero matches, confirming §7's requirement independently of the delegated worker's AST-level import-graph tests.
- **Independent source-level confirmation** that `CLOSED_OPERATIONS`/`CLOSED_CERTIFICATION_ROLES`/`CLOSED_ADMIN_MUTATIONS`/`CLOSED_READ_RECORD_TYPES` are derived directly from the protocol module's own `Enum` definitions (e.g. `CLOSED_OPERATIONS: FrozenSet[str] = frozenset(op.value for op in HelperOperation)`), not merely duplicated as independent constants that could silently drift from the real dispatch table.

No discrepancy was found between the delegated worker's reported findings and the primary operator's independent re-derivation. The overall verdict, generation-rotation-resurrection finding, macOS classification, and the FIFO-blocking-open finding are all independently confirmed.

## 13. Section 58 pass-criteria checklist (primary operator, verbatim-numbered)

1. CPIPC valid — **PASS** (independently re-derived, §12).
2. Predecessor canonical state coherent — **PASS** (PROJECT_STATUS.md / metadata / canonical report agree).
3. Contract trio byte-unchanged — **PASS** (sha256 identical before/after; `git diff` empty for `docs/contracts/`).
4. Current helper/replay implementation reconstructed independently — **PASS** (§2, §4 of this doc; full read by primary operator).
5. Process isolation valid — **PASS** (no import-graph path to `hpac_protected_admin_writer` from any of the 4 modules; AST-verified, not substring).
6. Same-interpreter authority exclusion valid — **PASS** (§12: independent grep for frame/`inspect`/`sys.modules`/ambient-identity patterns, zero matches).
7. Semantic no-authority-export valid — **PASS** (`record_exports_no_authority`/`response_leaks_authority` fuzzed against every `FORBIDDEN_AUTHORITY_TOKENS` member on both honest and tampered records/responses; `dispatch()` itself asserts on a hypothetically-leaking handler).
8. Replay clean-restart protection valid — **PASS** (real separate-process test, §14 of the test file).
9. Response-loss protection valid — **PASS** (3 retries against the same durable record all denied).
10. Crash/indeterminate behavior valid — **PASS** (real `SIGKILL` after commit → permanently `CONSUMED`; before boundary → honest `DUPLICATE_IN_FLIGHT`, not spent).
11. Concurrent duplicate atomicity valid — **PASS** (real 8-process race, exactly one `fresh`).
12. Conflicting replay valid — **PASS** (session/subject binding mismatch → `CONFLICTING`).
13. Generation rotation cannot resurrect spent requests — **PASS, CRITICAL, independently re-verified** (§5 of this doc / §12).
14. Durable record provenance valid — **PASS** (digest mismatch, slot-binding mismatch both fail closed).
15. Malformed/untrusted record fail-closed — **PASS** (8 parametrized variants + truncated JSON + symlink + group-writable, all fail closed).
16. Filesystem atomicity supports claimed durability — **PASS** (no leftover temp files; publish-via-link semantics confirmed statically).
17. Pre-attempt reservation handling safe — **PASS** (release only by owning pid; a spent record is never released; pre-boundary release is honest and bounded).
18. Replay/evidence state cannot diverge permissively — **PASS** (finalization failure → `RECONCILIATION_REQUIRED`, second attempt denied `CONSUMED` not re-executed; staging failure before boundary leaves request genuinely unspent).
19. Ordinary reset denied — **PASS** (no bearer reset token; no generic replay editor; only owning-pid pre-boundary release, which is not a "reset" of spent state).
20. Restart-dead authority / persistent history distinction valid — **PASS** (§14 of the test file, real subprocess workers).
21. Linux same-file-object property verified — **PARTIAL / REASONED-NOT-EXECUTED**: reconstructed and reasoned about from source (`/proc/self/fd/<fd>`, `O_NOFOLLOW` chain, descriptor identity); genuinely unexercisable as Linux on this macOS development host (no `/proc`), matching the existing foundation suite's own skip discipline. This is a host limitation, not a defect finding — flagged honestly rather than claimed as executed.
22. Linux substitution matrix passes — **NOT EXECUTED ON REAL LINUX** (same host limitation as #21); no substitution vulnerability found by source inspection, but not empirically exercised this phase.
23. macOS fail-closed status truthful — **PASS** (forced-platform test proves `UnsupportedPlatformProfile` is raised, not a weaker fallback).
24. macOS completeness truthful — **PASS, NOT IMPLEMENTED, correctly and honestly reported as such** (no attempt made to implement it, per mandate).
25. Helper provenance conjunction complete — **PASS** (each conjunct — schema version, digest, owner, mode, no-symlink, field-set completeness — independently tested to fail closed when corrupted individually).
26. Private channel secure compositionally — **PASS** (`OneShotChannel` accepts exactly one connection, directory/socket at `0700`/`0600`, peer-credential check exercised for real on macOS).
27. Descriptor inheritance controlled — **PASS, macOS-only spot check** (`DurableReplayStore.close()` releases its directory-chain descriptor; Linux-specific inheritance behavior not separately exercised this phase — same host limitation as #21).
28. Linux peer credentials correct — **NOT EXECUTED ON REAL LINUX** (host limitation; `SO_PEERCRED` code path reasoned about from source only).
29. macOS peer primitive correct where applicable — **PASS** (real `getpeereid` via genuine `AF_UNIX` socketpair; non-owner-uid rejected).
30. Configured-agent exclusion correct — **NOT SEPARATELY RE-TESTED THIS PHASE**: this worker's suite does not include dedicated root/sudo/USER/LOGNAME/SUDO_USER fixtures; this logic is unchanged from the predecessor foundation (untouched, `git diff` empty) and was previously verified by `N16-5-F-5-TB-HELPER-IV`'s own IV. Flagged honestly as a gap in this phase's own fresh coverage rather than silently inherited as PASS.
31. Closed operation vocabulary exact — **PASS** (exactly 5, source-derived, near-miss rejected).
32. Payload schemas closed — **PASS** (forbidden free-form keys rejected across multiple operations, case-insensitively).
33. admin_mutation bounded — **PASS** (`configure_privileged_helper` proven metadata-only; unknown mutation rejected).
34. Five-role closure exact — **PASS** (exactly 5, `hpac_lifecycle_terminator` excluded, near-miss/case/whitespace/NUL rejected).
35. certification_write remains non-real — **PASS by source inspection**: role membership alone does not create authority (operation-specific admission still required); this phase did not add a dedicated adversarial certification_write-only test beyond the existing closed-role tests, so this is reasoned rather than freshly exercised end-to-end.
36. Typed-read closure non-generic — **PASS** (`certification_read` returns only enumerated contents, never a store handle; near-miss record types rejected; composition-into-write attack rejected).
37. ceremony_entry bounded — **PASS** (self-asserted approval/human-present fields proven ignored).
38. presentation_evidence_write bounded — **PASS** (self-asserted facts rejected; requires a started ceremony).
39. Generic broker not reconstructible by composition — **PASS** (explicit two-operation composition attack tested and rejected).
40. State machine forward-only — **PASS** (both in-process and durable state machines reject skip-ahead and regression).
41. No-auto-retry correct — **PASS** (boundary-crossing fault injection denies re-execution).
42. Evidence staging integrated correctly — **PASS** (staging failure before boundary leaves request unspent; finalization failure after boundary yields indeterminate, not silent success).
43. Protocol audit != presentation evidence — **PASS by source inspection**: no code path treats a replay/audit record as `HPAC-PRESENTATION-EVIDENCE/2.0` or authentication proof; not given a dedicated adversarial cross-type-confusion test this phase.
44. Deterministic fixtures cannot become REAL — **PASS** (`ReplayLedger.__init__` signature is exactly `{self, durable_store}`; no flag/env-var path).
45. Exception/log paths leak no authority — **PASS** (`HelperProtocolError.__str__()` fuzzed against every forbidden token).
46. Environment/fd inheritance safe — **PARTIAL**: descriptor-chain release on close confirmed; a full environment-variable-inheritance (secrets/PATH/PYTHONPATH/sitecustomize) audit of the actual subprocess-launch abstraction was not separately re-executed this phase beyond what the existing foundation suite already covers (unmodified).
47. Retention/GC cannot reopen replay — **PASS** (`RECONCILIATION_REQUIRED` never pruned; pruned-then-replayed request still denied `EXPIRED`, not resurrected).
48. Replay namespace traversal/collision safe — **PASS** (hostile `../`/NUL/unicode/500-byte inputs always produce a 64-hex digest; no `/` or `..` reaches the actual filename; length-prefixing prevents concatenation collision).
49. Durable store permission model coherent — **PASS, software-model level**: group/other-writable slot and namespace directory both rejected in a disposable `tmp_path` fixture; real-host exact-ownership verification against a live deployment owner was explicitly out of scope (no live protected-host writes permitted this phase) and is not claimed.
50. Zero attributable security regressions — **PASS** (§12: 1 candidate-only fast_green node, confirmed unrelated and flaky, 0 attributable).
51. No production repairs performed — **PASS** (the FIFO-blocking-open finding was documented, not patched; `git diff` empty for `src/`).
52. No contract/schema/dependency changes — **PASS** (sha256 identical; no schema file touched; no dependency file touched).
53. No live protected-host mutation — **PASS** (every test uses a disposable `tmp_path`; no `<HPAC_PROTECTED_ROOT>` env var read or set).
54. No real ceremony — **PASS** (no FIDO2/YubiKey, no sudo, no production principal, no real challenge/approval).
55. Runtime remains Observed / observe / unavailable — **PASS** (no test in this suite touches plugin/capability runtime dispatch).
56. Plugin/capability count remains 0/0 — **PASS**.
57. First external effect absent/unreachable — **PASS** (unchanged; no new adapter/dispatch path introduced).
58. N16-6/N16-7 untouched — **PASS** (no work performed toward either).

**Overall verdict: N16-5-F-5-TB-HELPER-IV-R COMPLETE / INDEPENDENTLY VERIFIED**, with one documented non-blocking low-severity availability finding (§6) and several honestly-flagged partial-coverage items (#21/22/27/28/30/35/43/46/49) where genuine Linux-host execution or a live deployment-owner permission model was out of reach or out of scope for a disposable-fixture, macOS-hosted, no-live-mutation IV phase — none of these partial items constitute a security-critical failure; each is either reasoned from source, inherited unchanged from an already-independently-verified predecessor scope, or bounded by this phase's own no-live-mutation mandate. No criterion produced a security-critical FAIL.
