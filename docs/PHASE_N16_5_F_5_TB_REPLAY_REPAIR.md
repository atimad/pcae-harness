# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1

**Alias:** N16-5-F-5-TB-REPLAY-REPAIR
**Title:** Privileged Helper Replay-Durability Repair — Cross-Process Spent-Request Preservation
**Status:** COMPLETE

## 0. Governance / phase identity

- **Predecessor alias:** N16-5-F-5-TB-HELPER-IV
- **Predecessor canonical Phase ID:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1`
- **Predecessor terminal result confirmed:** COMPLETE — NOT VERIFIED / BLOCKED, via `PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json` (`status: completed`), and the canonical predecessor Phase Report. Matches this phase's own authorization prompt exactly (no identity-mismatch finding this time, unlike the predecessor's own entry check against its authorization prompt).
- **Blocking finding confirmed:** REPLAY-AFTER-RESTART — a mutating `(request_id, nonce)` consumed by one helper process reads as `FRESH` in a new helper process, because `ReplayLedger` was process-local/in-memory with no durable-location constructor argument.
- **CPIPC validation:** `pcae.core.phase_id.parse/is_valid/normalize/same_series/same_branch/compare`, run directly against the actual module. Successor = predecessor + exactly one appended `.1` segment (57 → 58 segments). `is_valid(successor) == True`; `normalize(successor) == successor`; `same_series == True` (`149`); `same_branch == True` (`O`); `compare(predecessor, successor) == less`. Uniqueness: zero hits from `git log --all -F --grep` and `git grep -F` at entry.
- **Entry repository state:** branch `main`, HEAD == `origin/main` == `319bac5d`, `origin/main..HEAD` = 0, tree clean, no conflicting active governed phase.

## 1. Contract baseline (verified byte-unchanged)

| Contract | File | sha256 (entry = exit) |
|---|---|---|
| HPAC-PAWA-001 v2.0 | `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` | `b8809e5119a9955863a8b947301e781f25a26c9a4107a9a917f0de083336323e` |
| HPAC-PAWA-HELPER-001 v1.0 | `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` | `e7b30daeb1f6967fe985cf7394834e76a81acefb538a0038672aa026a5b58815` |
| HPAC-PPA-001 v2.0 | `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md` | `27acaabcde8d1ac1793946f5858a391f1cd18deb9f20cbaeee2121db29cc9cd2` |

Independently reconfirmed identical before and after implementation. No schema, `pawa_failure_code`, or RHAMP `terminal_reason_code` change.

## 2. Original replay reproduction (inherited from predecessor, not re-derived)

Predecessor N16-5-F-5-TB-HELPER-IV reproduced REPLAY-AFTER-RESTART via two genuinely separate OS subprocesses (not two objects in one process) under three framings (clean-consume, response-loss, crash-before-terminal-disposition), and structurally confirmed via `inspect.getsource` that `ReplayLedger`/`ProtectedStoreFoundation` perform no filesystem/network I/O and take no durable-location constructor argument. This phase did not need to re-reproduce the defect; it inherits the confirmed root cause and repairs it directly.

## 3. Evidence table (reconstructed from source this phase, before any edit)

| Symbol | Current storage | Lifetime | Mutation point | Durable? | Contract requirement | Repair need |
|---|---|---|---|---|---|---|
| `ReplayLedger._entries` | `dict[(request_id,nonce)]` in heap | one process | `check_and_mark_in_flight`, `mark_consumed` | No | REQ-076/077, PAWAH-INV-10 | Yes — the defect |
| `ReplayOutcome` | enum, 5 members | n/a | n/a | n/a | §19 table | Reused unchanged |
| `_LedgerEntry.in_flight/consumed` | two bools | process | `mark_consumed` | No | §20 durable transitions | Replaced by 7-state durable model |
| `check_and_mark_in_flight` | — | call | reserve | No | "at most one helper process may admit" | Yes — cross-process |
| `mark_consumed` | — | call | spend at boundary | No | REQ-077 | Yes — durable before mutation |
| `release_in_flight_without_consuming` | `del` from dict | call | pre-boundary release | No | REQ-083 | Guards added (spent + owner) |
| `EvidenceStager.records` | `dict[ref]` in heap | process | `stage`/`finalize` | No | §22 "durably writes under protected root" | Out of scope; bound by ref into replay record |
| `HelperStateMachine` | `_index` int | process | `advance_to` | No | §20 | Mirrored into durable record |
| `request_id`/`nonce` binding | request fields | request | — | n/a | §19 identity | Folded into durable replay key |
| `expiry` | RFC3339 string | request | `strptime`, silent fallback | n/a | REQ-074 | Hardened: unparseable ⇒ EXPIRED |
| read-vs-mutation | `operation != certification_read` | — | `validate_and_admit` | n/a | REQ-078 | Preserved exactly |
| `ReplayLedger()` call sites | only tests + `HelperContext` | — | — | — | — | No production caller existed to break |
| protected-root abstraction | none in helper modules | — | — | — | HPAC-PAWA-REQ-326/336 `pawa-helper/` | Reused, not invented |

## 4. Repair architecture

**One authoritative durable record** per `(installation_id, generation, request_id, nonce)`, as sibling records under the already-contracted `<HPAC_PROTECTED_ROOT>/pawa-helper/replay/g<N>/` namespace. No new trust root; no second independent datastore.

**Rejected alternative:** extending the staged evidence record itself as the reservation. Rejected because reservation must happen at *admission* (before staging occurs inside the handler) — using the staged record as the reservation would either move staging before admission (violating the existing ordering) or leave the admission race unprotected. Instead, the evidence ref is bound into the one durable replay record (`evidence_ref`, `committed_digest`), preserving a single source of truth.

## 5. Durable replay key and bindings

`sha256(domain ‖ installation_id ‖ generation ‖ request_id ‖ nonce)`, each part length-prefixed to prevent concatenation-collision. Caller-supplied `request_id`/`nonce` are always hashed, never used as filesystem path fragments — on-disk names are always 64 lowercase hex characters (tested with `../../../../etc/passwd` as `request_id`). Conflicting-replay detection additionally compares `operation`, `session_id`, `subject` (principal/credential/proof id), and the full `request_digest`.

## 6. Durable state model

`DurableReplayState`: `REQUEST_RECEIVED` (reservation, not yet spent) → `MUTATION_ATTEMPT_STARTED` → `MUTATION_COMMITTED` → `EVIDENCE_WRITTEN` → `RESPONSE_EMITTED`; `RECONCILIATION_REQUIRED` reachable from `MUTATION_ATTEMPT_STARTED` or `MUTATION_COMMITTED`; `RESULT_EMITTED` reachable directly from `REQUEST_RECEIVED` for non-mutating one-shot `ceremony_entry`. A forward-only legal-transition table rejects any transition not explicitly listed, failing closed rather than rewriting durable history.

## 7. Atomic reservation mechanism and crash-safety guarantee

Complete record written to a private temp name in the same directory, `fsync`'d, then published via `link()` (POSIX-atomic `EEXIST` on collision — exactly one racer wins, every other racer observes the slot already taken). State transitions use temp + `os.replace()`. All filesystem operations are performed through an `O_NOFOLLOW|O_DIRECTORY` `dir_fd` descriptor chain with no path re-resolution between check and use.

**A bare `O_CREAT|O_EXCL` on the final name was the first implementation attempt, and the concurrency test caught it failing**: it publishes the *name* before the *content*, letting a racing reader observe an empty file. `link()`-publishing makes the slot atomic in content as well as existence.

**Precise claim:** atomic against concurrent helper processes; durable across process death (verified with real `SIGKILL`). **Explicitly not claimed:** power-loss durability — `fsync` success only means the kernel accepted the write; directory `fsync` here is best-effort.

## 8. Outcomes for every disposition

- **Fresh:** new `(installation_id, generation, request_id, nonce)`, valid expiry, no existing record.
- **Consumed:** existing record in any spent state, same binding conjuncts.
- **Duplicate in-flight:** existing record in `REQUEST_RECEIVED`, same binding conjuncts, different/concurrent caller.
- **Expired:** unparseable or past-deadline `expiry`, checked before store consultation.
- **Conflicting:** same `(request_id, nonce)` with a different `installation_id`/`generation` binding, or same key but different operation/session/subject/payload digest. Original record left byte-unchanged.

## 9. Attempt-started / committed / indeterminate-reconciliation persistence

`mark_consumed` durably transitions to `MUTATION_ATTEMPT_STARTED` **before** `mutation_fn()` runs — a crash at or after the boundary always leaves the request spent. `MUTATION_COMMITTED` is recorded immediately after commit. If evidence finalization then fails, the record durably transitions to `RECONCILIATION_REQUIRED` (not "REJECTED", not silently retried) — the same exception path the foundation already used, now with a durable trace. `RECONCILIATION_REQUIRED` records are never pruned by retention.

## 10. Clean restart / response-loss / crash-restart / concurrent-duplicate / conflicting-replay results

All results below are from `tests/test_n16_5_f_5_tb_replay_repair.py`, using real subprocess separation (not two Python objects in one process) and real `SIGKILL` where a crash is exercised:

- **Clean restart:** helper A admits + consumes R, exits; fresh helper B receives identical R; B is denied (not FRESH); no second mutation. Repeated ×5.
- **Response loss after commit:** R admitted, mutation committed, response dropped, process destroyed; fresh helper resubmitting R is denied; durable state shows `RESPONSE_EMITTED` plus the committed digest.
- **Crash after `MUTATION_ATTEMPT_STARTED`:** real `SIGKILL` (exit code −9) before terminal disposition; fresh helper is not FRESH, no retry is attempted; disposition is `RECONCILIATION_REQUIRED`-observable via reconciliation read.
- **Crash before the attempt boundary:** fails closed conservatively (reservation not reclaimed within this phase's scope) rather than risking a duplicate mutation; a genuinely fresh `(request_id, nonce)` still works normally.
- **Concurrent duplicate race:** 8 and 6 real subprocesses submitting the identical request concurrently, released via a barrier; exactly one obtains FRESH/admission, the effect is counted exactly once via a shared effect directory, every other process fails closed.
- **Conflicting replay:** the same replay identity resubmitted with a changed operation, subject, session, role, or payload digest independently fails as `CONFLICTING`; the original durable record is verified byte-unchanged after each attempt.

## 11. Read-repeatability result

`certification_read` is idempotent by design and produces **zero** durable replay records — repeating a valid read across a fresh helper process succeeds every time, verified directly. The other four operation types (`admin_mutation`, `certification_write`, `ceremony_entry`, `presentation_evidence_write`) are durably one-shot; none of the five roles (`hpac_challenge_coordinator`, `hpac_assertion_recorder`, `human_authentication_proof_verifier`, `hpac_gate5_binder`, `hpac_rhamp_counter_state_verifier`) can be replayed across restart.

## 12. Generation/rotation result

A request bound to generation `G` presented to a store opened at generation `G+1` is not silently treated as fresh: cross-checked `installation_id`/`generation` produce `CONFLICTING`, not `FRESH`. **This closes a real gap the tests found during implementation** — the first cut only namespaced by current generation and would have resurrected a `G`-bound spent request under `G+1`.

## 13. Retention policy

Conservative: `prune_expired(retention=...)` removes only records whose `expiry + retention` window has fully elapsed, and never removes a `RECONCILIATION_REQUIRED` record regardless of age. Pruning is unreachable from any of the five closed operations — no request field or dispatch handler calls it; it is an explicit out-of-band deployment-owner maintenance call.

## 14. Malformed-record result

13 variants tested, all fail closed via `ReplayStateCorruption` (carrying the existing `internal_fail_closed` code, no new vocabulary): truncated file, malformed JSON, non-JSON-object, missing/unknown field, wrong schema version, invalid `durable_state` value, `record_digest` mismatch (tamper), state-only tamper, record relocated to the wrong slot, duplicate/conflicting record, symlinked record slot, symlinked namespace component, non-regular file, world-writable file or directory. None of these are ever treated as "absent" (which would itself reopen the replay hole) or as "fresh".

## 15. Ordinary-reset-denial result

No API exists for reset/mark-fresh/delete/clear-consumed. Tested directly: hostile `operation_params` cannot remove a record, alter its nonce/operation binding, or flip consumed→fresh or indeterminate→fresh; a spent record is never released by `release_reservation`; a reservation owned by a different `owner_pid` cannot be released by another process.

## 16. Replay-record provenance result

A record is only trusted after five independent conjuncts hold: valid JSON object with the exact closed field set; exact frozen schema-version literal; `durable_state` a member of the closed enum; `record_digest` recomputes over its own canonical bytes; and its own bound fields re-derive the `replay_key` naming the slot it was found in (detects relocation/forgery). Any single failing conjunct is corruption, not a weaker-but-usable record.

## 17. No-authority-export result

`record_exports_no_authority()` scans every field name and string value of a durable record against the existing `FORBIDDEN_AUTHORITY_TOKENS` vocabulary; used both as production defense-in-depth and as the test proof. No capability, `_seal`, protected path handle, writable ledger object, or reset token is ever present in a durable record.

## 18. Restart-dead-authority-vs-persistent-history result

Explicitly tested as two simultaneous facts: (A) no privileged Python object or authority token is persisted anywhere in a durable record or its raw on-disk bytes — the fd-based `VerifiedExecutable` authority from a dead process cannot be reconstructed from durable state; (B) the spent-request history nonetheless remains effective — a fresh helper process consulting the same durable store still denies the spent request. History persists; authority does not.

## 19. Regression tallies

- **Focused replay-durability suite (new):** 69 passed, 0 failed.
- **Helper foundation suite (unmodified, `git diff` empty):** 51 passed, 0 failed, 1 skipped — identical to the predecessor's own tally. (Skip is the Linux-only same-file-object exec test, skipped on this macOS host — unchanged, macOS profile left FAIL-CLOSED / NOT IMPLEMENTED per scope.)
- **Combined, independently re-run 3 consecutive times by the primary operator:** 120 passed / 1 skipped, stable.
- **fast_green (`-m fast_green -n auto`), independently re-run by the primary operator:**
  - Candidate tree: 373 failed / 9646 passed / 5 skipped / 9 errors.
  - Entry baseline (`git stash push -u` / `pop`, restoration verified via `git status`): 355 failed / 9664 passed / 5 skipped / 9 errors.
  - `diff` of the two sorted `FAILED` node-id lists: 18 nodes present only in the candidate run. Every one independently spot-checked (one shown in full below) to be a pre-existing, unrelated "no uncommitted `src/pcae`/contract change" scope-fence guard from a past phase, asserting `git status`/`git diff` against the working tree is empty — these fire for *any* uncommitted production change and clear once this phase's commit lands. None reference `hpac_pawa_helper*` or replay/security semantics.
  - Example (`tests/test_phase_149o_20l_7d_10_independent_verification.py::test_no_authority_relevant_source_mutated_by_this_phase`): failure text is `assert status == ""` where `status` lists exactly this phase's own three not-yet-committed files.
  - **Attributable regressions: 0. Security/replay regressions: 0.**

## 20. Baseline / commit

- Entry SHA (origin/main HEAD at entry): `319bac5d`.
- Files changed this phase (production + tests only): `src/pcae/core/hpac_pawa_helper_protocol.py` (+69 lines), `src/pcae/core/hpac_pawa_helper_operations.py` (+24 lines), new `src/pcae/core/hpac_pawa_helper_replay_state.py` (907 lines), new `tests/test_n16_5_f_5_tb_replay_repair.py` (1,349 lines, 69 tests). `hpac_pawa_helper_os.py` unchanged (not needed).
- Contracts changed: **NONE**. Schemas changed: **NONE**. Dependencies changed: **NONE**.
- macOS profile: unchanged, FAIL-CLOSED / NOT IMPLEMENTED.
- Live protected-host writes: **0**. Real ceremony: **NOT PERFORMED**. No FIDO2/YubiKey, no PIN request, no production principal, no counter-state mutation.
- Runtime: `Observed` / `observe` / `unavailable`. Plugins / capabilities: **0 / 0**. First governed runtime external effect: **ABSENT / UNREACHABLE**.

## 21. Governance results

- `pcae check`: passed.
- `pcae health`: healthy.
- `pcae push` / origin sync: `origin/main..HEAD` confirmed 0 pre-finalization; will be re-confirmed 0 post-push.
- Doctor / task-memory: no new errors introduced.
- Governed completion notification: dispatched via `pcae phase complete` / `pcae push`.

## 22. Status summary

- **Replay repair status:** COMPLETE. Replay-after-restart: REPAIRED / IV PENDING. Durable spent-request semantics: IMPLEMENTED.
- **Helper foundation status:** REPAIRED / FRESH IV REQUIRED.
- **F-5-B2:** BLOCKED PENDING FRESH HELPER IV + REMAINING MIGRATION SLICES.
- **F-5:** CERTIFICATION BLOCKED.
- **N-16-5:** NOT CLOSED.
- **N-16-6 / N-16-7:** OPEN / UNTOUCHED (N-16-7 strictly last).
- **Fresh helper-IV retry:** recommended under alias N16-5-F-5-TB-HELPER-IV-R (or repository-conformant equivalent successor identity). **Explicitly NOT begun** — this phase performs no caller/client integration, no legacy in-process-path removal, no packaging/install, no real certification, no N-16-6, no N-16-7, and does not itself begin the fresh helper-IV retry.

## 23. Delegated worker disclosure

Source reconstruction, architecture design, implementation, and test authorship were performed by a delegated worker under this phase's bounded scope (no commit/push/finalization authority). The primary operator independently: validated Section 0 governance and CPIPC identity before delegation; reviewed the full diff and the new module in full; re-ran the new suite, the foundation suite, and fast_green (both candidate and stashed baseline) directly; re-verified the contract-trio sha256 values; and performed all task-lifecycle, documentation, commit, push, and notification steps. `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` is preserved as the standing rule — no delegated worker performed any commit, push, or task/phase closure this phase.
