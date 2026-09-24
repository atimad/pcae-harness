# Phase 150H — Phase 150G Report Identity Reconciliation

Canonical Phase ID: `150H`

Alias: **PCAE-LIFECYCLE-PHASE-150G-REPORT-IDENTITY-RECONCILIATION**

Status: **COMPLETE — NOT RECONCILED / BLOCKED**

This was a narrow lifecycle/evidence phase. It did not modify Phase 150G's
technical result, production source, normative contracts, runtime posture, or
N-16 disposition. `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`.

## 1. Preflight and identity

At entry, `main`, `HEAD`, and `origin/main` were all
`a6d475ef474514533e0144952d4f2f89374c3d2e`; the worktree was clean and
`origin/main..HEAD == 0`. The active task was the expected idle post-150G
placeholder. The held/recovery commits `6c7f5cf4`, `2b8ad2aa`, `72cdba16`,
and `d0b2a75a` were absent from ancestry.

`150H` was independently derived from `150G` using
`pcae.core.phase_id`: valid, ordered after `150G`, same series, unequal, and
collision-free against Git history and repository records. Phase 150H was
then activated through the governed task transition and agent-lock path.

The preflight conflict reproduced exactly:

- `pcae phase-report trust`: complete/trusted;
- `pcae phase-report consistency`: consistent;
- `pcae phase-report reconcile --phase-id 150G`: `conflict`;
- blocker: notification marker payload conflicts with promoted report;
- blocker: checkpoint identity conflicts with promoted report;
- promoted generation count: 2.

## 2. Phase 150G generation inventory

The report directory is intentionally ignored by Git (`.pcae/.gitignore`),
so creation chronology comes from the immutable generation filenames,
embedded timestamps/content, filesystem timestamps, checkpoint/receipt
timestamps, and the tracked lifecycle commits/metadata that bracket each
generation. Neither generation was deleted or rewritten.

| Field | Generation A | Generation B |
|---|---|---|
| Path | `.pcae/phase-reports/20260922-203915-150G.json` | `.pcae/phase-reports/20260922-210046-150G.json` |
| Created | `2026-09-22T20:39:15.634476+00:00` | `2026-09-22T21:00:46.220209+00:00` |
| JSON file SHA-256 | `5509cb71fab2ad6bc0f6474fda3bb08bea2ead17a8c2ddd2d8c96ff25a5a3c12` | `deafa34cd8d4c7802def8445308b502c9c93603fdc622e1b28bae79a5ed5651d` |
| Stored Markdown SHA-256 | `da5a678cbf6e88eb6d37a8bad3fead8217aa92dd30709fab52edabbe5c308551` | `5b95481652526975ca6190b3a15a439b8aaefa8bfb4bd685abca7185536366b1` |
| JSON-rehydrated report digest | `bd234de06c10721dd85ffe296b806884f388896b03a59c5f426eb1a2e69faa87` | `59dda6c6f0ab09ed465a021a80eaf101c60254c872a4c39cd07d375213b2775f` |
| Snapshot from persisted JSON | `e847581a476f7640a542f5dcb048675626be2abbe30166f77a50803363fd5238` | `232104b62f1c78b24732735cf1185f62790e0b0555a141d6d348d70fe5c078e8` |
| Completeness | `pending_push` | `complete` |
| Pushed state | `not_pushed`; `origin/main..HEAD == 3` | `pushed`; `origin/main..HEAD == 0` |
| Source revision | `4b56c18f...` | `2969be8e...` |
| Commits | `31ebe985`, `40efd807`, `4b56c18f` | prior three plus `3300cd81`, `2969be8e` |
| Completion metadata | tracked in `3300cd81`; SHA-256 `390e274f2b30ac7a145d2467f20f170de8638db5a7060842d211a3e22ef46f3d` | final tracked form in `a6d475ef`; SHA-256 `dd2b3d58908e58d2a23ffa3da2054353e53d4da6c93de030e11661202742ada3` |
| Checkpoint linkage | none (pending generation is deliberately not finalized/notified) | checkpoint binds stored Markdown digest `5b954816...` and snapshot `232104b6...` |
| Notification linkage | none; notification explicitly skipped pending push | marker binds stored Markdown digest `5b954816...` and snapshot `232104b6...` |
| Promotion role | non-authoritative push-gate generation | terminal complete generation; `latest.*` target at investigation time |

Both generations have the same Phase 150G identity and substantive technical
conclusion. Generation A is explicitly the non-authoritative pending-push
artifact required by the current lifecycle. Generation B is unambiguously the
terminal generation: it is complete, pushed, has zero outgoing commits, names
the post-task-close source revision, contains the final five-commit list, and
is the generation actually delivered and checkpointed.

## 3. Actual chronology

1. `31ebe985` opened Phase 150G's task.
2. `40efd807` implemented the recognition-core extraction.
3. `4b56c18f` recorded the in-scope stale-test repair.
4. The first report was generated as `pending_push` at 20:39:15 UTC.
5. `3300cd81` committed pending-push completion metadata/report evidence.
6. `2969be8e` closed the Phase 150G task and opened the idle placeholder.
7. After push, metadata and Fast Green were recomputed against pushed state.
8. The second report was generated at 21:00:46 UTC and notification,
   checkpoint, and synthetic delivery receipt completed at 21:00:48 UTC.
9. `a6d475ef` committed the final post-push metadata/Fast Green/task update.

There was no duplicate terminal finalization. Pending then terminal generation
is explicitly implemented behavior: `finalize_phase_report()` writes
`COMPLETENESS_PENDING_PUSH`, suppresses notification, and documents that a
normal post-push re-finalization promotes a complete report.

## 4. Root cause

Primary classification: **CLASS B — MULTI-GENERATION EXPECTED, RECONCILER
DEFECT**.

The terminal checkpoint and notification marker are not stale. Both record
`report_digest = 5b954816...`, which independently equals the SHA-256 of the
actual terminal Markdown generation and `latest.md` as observed at entry.
Both also record `finalization_snapshot_id = 232104b6...`, which independently
matches the terminal JSON's semantic snapshot.

The reconciler does not hash the stored terminal Markdown. It loads the JSON
with `PhaseReport(**data)` and calls `compute_report_digest(report)`, which
re-renders Markdown. That JSON round trip is lossy:

- the original in-memory report contained `canonical_report_content`;
- that content caused the certified Markdown to include the `Report
  Consistency` section and `Canonical report: present`;
- `PhaseReport.to_dict()` does not persist `canonical_report_content`;
- the persisted JSON says `canonical_report_used: false`;
- rehydrating the JSON therefore omits the six-line consistency section;
- the resulting recomputed digest is `59dda6c6...`, not the certified/stored
  Markdown digest `5b954816...`.

This is why `reconcile` falsely labels the correct checkpoint and marker as
conflicting. The two-generation count is not the cause and is not itself a
blocker.

A second read-only inspection defect was also reproduced: calling
`validate_derived_correctness()` during `phase-report consistency` mutates the
rehydrated report's metadata by adding `fgsc_verification_checkpoint_commit`,
`fgsc_final_phase_head`, and `fgsc_lifecycle_state`. Consequently that command
prints snapshot `b78955e8...`, while the unmutated persisted terminal JSON and
checkpoint correctly agree on `232104b6...`. The mutation is process-local;
the artifact is not changed, but the displayed identity is not a pure read of
the persisted report.

## 5. Checkpoint, marker, receipt, and canonical adjudication

The completed checkpoint was written by the finalization transaction from
21:00:46–21:00:48 UTC. It records the terminal report's actual Markdown digest,
the matching semantic snapshot, completed promotion/dispatch steps, and a
finalized receipt. The notification marker records exactly the same pair. The
receipt is finalized and records synthetic delivery only; it is evidence, not
authority.

Canonical terminal generation adjudication: **Generation B**. Provenance is
the convergent pushed-state fields, source revision, five-commit inventory,
actual stored Markdown digest, matching checkpoint/marker snapshot pair,
finalized receipt, and later tracked `a6d475ef` metadata commit.

No linkage was mutated. `pcae phase-report reconcile` explicitly documents and
implements a read-only operation (`mutation_performed: false`); there is no
governed repair command that can safely update or rotate an already-completed
checkpoint/ordinary-completion marker. Manual JSON editing, digest
substitution, deletion, re-notification, or latest-pointer forgery would erase
or falsify history and was not attempted.

## 6. Verification

Fresh suite:

`pytest -q tests/test_phase_150h_pcae_lifecycle_phase_150g_report_identity_reconciliation.py`

Result: **13 passed**. It independently hashes both generations, proves the
terminal Markdown/checkpoint/marker identity agreement, reproduces the lossy
JSON re-render mismatch, proves the expected pending-to-complete lifecycle,
proves the reconciler is read-only, captures the process-local consistency
mutation, and verifies zero Phase 150H production/contract delta.

Final governed Fast Green attribution used baseline
`a6d475ef474514533e0144952d4f2f89374c3d2e` and candidate
`02d1d457f7efd26f39b82e913ab075bd73b3d152`. It passed with
`attributable_failures: []`; the 359 raw failures and 9 collection errors were
baseline-pre-existing, while the only expected phase artifact was the
not-yet-pushed HEAD/origin assertion. The independently generated artifact is
`.pcae/fast-green-attribution/c4ec91e02efbbf3f34dfef635e90143ea8158e2090b3c178b6515732cd52a31a.json`.
An intervening governed run's lone candidate-only
`test_verify_detects_tampered_record` result passed 5/5 candidate and 3/3
fixed-baseline focused reruns; the subsequent unmodified governed rerun passed.
Both the failed and final passing artifacts are preserved.

Post-completion note: `.last-notified.json` is a global latest-notification
pointer, not immutable per-phase storage. Phase 150H's own governed terminal
notification legitimately advanced it from the preflight-observed 150G payload
to 150H. The durable 150G checkpoint and promoted generations remain unchanged;
post-150H `reconcile --phase-id 150G` therefore reports the marker as
`not_dispatched` plus the same rehydration-created checkpoint conflict. No 150G
artifact was manually mutated.
This evidence phase does not reuse Phase 150G's attribution artifact.

## 7. Preserved truth and disposition

- Zero `src/pcae/**` changes.
- Zero `docs/contracts/**` changes.
- No Phase 150G report, checkpoint, marker, receipt, generation, or latest
  pointer was manually edited, deleted, overwritten, or fabricated.
- Phase 150G remains COMPLETE — shared recognition core implemented.
- Helper admission remains NOT wired; helper step 9-prime remains undefined.
- Foundation blocker unchanged.
- Runtime remains Observed / observe / unavailable.
- N-16-5 remains OPEN; N-16-6 and N-16-7 untouched.
- Phase 150H / recognition-core IV was NOT begun by this phase.

`HASH CONSISTENCY != PROVENANCE`. In this case, the stronger provenance also
shows that the stored terminal Markdown, checkpoint, and notification marker
already agree; the recomputation mechanism is what diverges.

## 8. Recommended next phase

The smallest next governed phase is a dedicated lifecycle-infrastructure
repair (suggested alias
**PCAE-LIFECYCLE-PHASE-REPORT-REHYDRATION-IDENTITY-REPAIR**) to make report
identity reproducible from persisted canonical artifacts and make consistency
inspection mutation-free. It must define backward-compatible reconciliation
for existing reports without rewriting delivered content or historical
generations. Only after that repair is independently verified and Phase 150G
reconciliation is clean should the recognition-core implementation IV be
re-authorized. No successor phase is begun here.
