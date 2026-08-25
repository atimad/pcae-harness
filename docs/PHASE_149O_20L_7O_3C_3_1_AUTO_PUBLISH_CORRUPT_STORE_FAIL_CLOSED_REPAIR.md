# Phase 149O.20L.7O.3C.3.1 — Auto-Publish Corrupt-Store Fail-Closed Repair

- **Phase ID:** `149O.20L.7O.3C.3.1`
- **Phase-entry commit:** `2fd7fe3a` (`origin/main..HEAD` = 0, repository clean)
- **Finding repaired:** `B-149O.20L.7O.3C.3-1` — AUTO-PUBLISH CORRUPT-STORE ISOLATION DEFECT
- **Finding status after this phase:** **REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.** This phase does not close its own finding; closure requires the recommended follow-up, `149O.20L.7O.3C.3.2 — Auto-Publish Corrupt-Store Repair Independent Verification`.

## 1. Historical crash reproduction

Independently confirmed at phase entry, before any production source was touched:

- Existing suite `tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py` — already committed at phase-entry HEAD `2fd7fe3a` — reproduces the crash directly (`test_corrupted_unrelated_session_file_crashes_auto_publish`, run against unmodified source: raised `SessionStoreCorruptError` uncaught, exactly as documented).
- A fresh, literal **subprocess-level** `pcae phase complete` E2E, run against unmodified phase-entry source (`tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_corrupt_store_fail_closed_repair.py::test_subprocess_pcae_phase_complete_no_longer_crashes_on_unrelated_corrupt_session`, executed once *before* the repair as part of this phase's own reproduction step): exit code 1, `stderr` containing a full Python traceback ending in `pcae.interactive_workflow.errors.SessionStoreCorruptError: Session file for '<unrelated CDS id>' is not valid JSON.` — the real installed CLI entry point crashes for a phase completion that has nothing to do with Interactive Workflow.
- `tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_corrupt_store_fail_closed_repair.py::test_pre_repair_commit_reproduces_the_uncaught_crash` pins this reproduction against the phase-entry commit via `git show 2fd7fe3a:...` (a fixed-worktree-equivalent comparison, avoiding an extra `git worktree` checkout): confirms `find_session_by_subject_ref`'s scan loop at phase entry catches only `SessionNotFoundError`, and confirms `auto_publish_confirmed_session`'s call to `find_confirmed_session` was not wrapped in any `try`/`except` at phase entry.

## 2. Exact production call graph

```
pcae phase complete
  → run_phase_complete()                                    (src/pcae/commands/phase.py:56)
    → auto_publish_confirmed_session(...)                    (src/pcae/commands/governance_auto_publication.py)
      → find_confirmed_session(session_service, subject_ref)
        → SessionApplicationService.find_session_by_subject_ref(subject_ref)
                                     (src/pcae/interactive_workflow/application/session_service.py)
          → SessionCoordinator.list_session_ids()             (deterministic full scan, sorted ids)
          → SessionCoordinator.load_session(session_id)        (for every id, unconditionally)
            → FilesystemSessionRepository.load(session_id)
              → json.loads(raw) → raises SessionStoreCorruptError on malformed JSON
                                    (or PersistenceUnavailableError on an OSError read failure)
```

`find_session_by_subject_ref`'s loop, at phase entry, caught only `SessionNotFoundError` — a single record's corruption anywhere in the store aborted the entire scan with an uncaught `SessionStoreCorruptError`/`PersistenceUnavailableError` (`pcae.interactive_workflow.errors` — an `InteractiveWorkflowError` subclass hierarchy). `auto_publish_confirmed_session`'s own `except` clauses only ever covered `ApplicationServiceError` subclasses (`pcae.interactive_workflow.application.errors`) — a sibling, unrelated hierarchy — and only around the later `ensure_readiness_package`/`publish_with_permission_gate` calls, not around the `find_confirmed_session` call itself. The exception therefore propagated unmodified through every layer above, out of `run_phase_complete`, which wraps the auto-publish block in no `try`/`except` at all.

## 3. Error ownership

Chosen ownership point: **`SessionApplicationService.find_session_by_subject_ref`** (the exact method that owns the full-scan loop), with a second, consistent layer at **`auto_publish_confirmed_session`** (which already owns exception-to-outcome translation for every other `ApplicationServiceError` on the publish path).

Rejected alternatives:
- **Filesystem repository (`FilesystemSessionRepository.load`)**: already correctly raises typed, sanitized domain exceptions (`SessionStoreCorruptError`/`PersistenceUnavailableError`) per its own documented contract — the defect is not that this layer raises, but that a caller two layers up does not translate/contain it. Changing this layer's behavior would be the wrong ownership point and would affect every other caller of `load()` (e.g. `SessionApplicationService.load_session`, which already correctly translates this exception into `SessionCorruptApplicationError`).
- **`SessionCoordinator.load_session`**: a thin, intentionally domain-exception-preserving delegation (per its own docstring, "no ownership re-check here"); translating domain errors into application errors here would blur the coordinator/application-service boundary this codebase's existing architecture already keeps separate (`SessionApplicationService.load_session` is the one place that already does this translation, one layer up).
- **`run_phase_complete`**: a broad `try/except` at this call site would violate the brief's own "avoid broad catch-all exception handling at the wrong layer" instruction and would not distinguish relevant/unrelated corruption at all — it would simply convert every corruption into an unconditionally-swallowed no-op, printed or not, from the single highest-level entry point, with no application-error translation and no `session_id` disclosed.

## 4. Unrelated-vs-relevant corruption semantics (as implemented)

`find_session_by_subject_ref`'s scan loop now catches `SessionStoreCorruptError`/`PersistenceUnavailableError` per record (in addition to the existing `SessionNotFoundError`), continues the scan (deterministic — every id is still visited regardless of which one is corrupt, so the result never depends on filesystem iteration order), and:

- **If a genuinely readable match for `subject_ref` is found**, it is returned unconditionally — a real, live, readable match proves any corruption encountered elsewhere in the same scan is not the record governing this subject (at most one *live* governing record maps to a given `subject_ref` under this module's own convention; duplicate-`subject_ref` ambiguity is the pre-existing, disclosed, unrepaired NON-BLOCKING 3C.3 finding — see §7). This is the "unrelated corruption does not block/shadow the real match" half of the brief's required distinction.
- **If no readable match is found and at least one record could not be read**, the corruption is surfaced as a translated `SessionCorruptApplicationError`/`SessionPersistenceUnavailableApplicationError` (`interactive_workflow.application.errors` — already-existing types, no new taxonomy) *instead of* the method's own `None` ("no session bound") return. `auto_publish_confirmed_session` catches this via its existing `except ApplicationServiceError` idiom (extended to also wrap the `find_confirmed_session` call, not just the publish calls) and converts it to the existing `STATUS_APPLICATION_ERROR` outcome, with `diagnostic` carrying the sanitized message.

This is the fail-closed half required by the brief: a corrupt record that genuinely could have been the one governing the current subject is never silently laundered into "no governance state exists" (§6 of the governing brief) — it is surfaced as a disclosed, structured `application_error`, distinct from `no_session_bound`.

**Practical consequence for `pcae phase complete`'s own gating**: neither outcome (`no_session_bound` nor `application_error`) has ever gated `finalizable`/the exit code — `run_phase_complete`'s `if outcome.status != STATUS_NO_SESSION:` guard only controls whether diagnostic lines are printed; `complete_phase()` runs based solely on the pre-existing `finalizable` value (Phase 149O.20L.7O.3C.2's own documented, unmodified design). This is why converting the crash into *any* structured, non-raising outcome — `application_error` in the no-match/corruption case — is sufficient to restore the isolation property the finding required: "unrelated phase completion is not globally blocked" was never actually about the outcome status; it was about the process not crashing before reaching that point at all.

## 5. Production files changed (2)

| File | Reason |
|---|---|
| `src/pcae/interactive_workflow/application/session_service.py` | `find_session_by_subject_ref`'s scan loop now catches and translates `SessionStoreCorruptError`/`PersistenceUnavailableError` per record instead of only `SessionNotFoundError`; on no readable match with corruption present, raises the translated application error instead of returning `None`. |
| `src/pcae/commands/governance_auto_publication.py` | `auto_publish_confirmed_session` now wraps the `find_confirmed_session(...)` call in the same `except ApplicationServiceError` handling already used for the publish path, converting the (now correctly-typed) translated exception into a disclosed `STATUS_APPLICATION_ERROR` outcome instead of letting it propagate. |

No other production file was touched. `run_phase_complete` (`src/pcae/commands/phase.py`) is unchanged — `test_run_phase_complete_call_site_has_no_exception_guard_around_auto_publish_block` (3C.3's own regression guard, re-run unmodified) still passes, confirming the fix does not rely on adding a `try`/`except` at the call site.

## 6. Duplicate-`subject_ref` ambiguity — disposition

**Not repaired in this phase**, per the governing brief's own conditional-scope instruction (§11/§12). Rationale: repairing this would require deciding (a) whether "at most one live/eligible session per `subject_ref`" is a hard invariant this module must enforce, and (b) what the correct fail-closed *outcome vocabulary* for an ambiguity is (a new `AutoPublicationOutcome` status? an exception? which of the two existing candidates is "current"?) — none of which is derivable from existing frozen contracts without a separately governed decision, and the brief explicitly forbids inventing a new outcome/contract in this narrow repair phase. `tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_corrupt_store_fail_closed_repair.py::test_duplicate_subject_ref_ambiguity_unchanged_by_this_repair` confirms the pre-existing latest-`created_at` resolution is byte-for-byte unchanged by this repair. Carried forward unchanged as the same NON-BLOCKING finding 3C.3 §8 already recorded.

## 7. Tests added

`tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_corrupt_store_fail_closed_repair.py` (14 tests, all passing against repaired source):

1. `test_pre_repair_commit_reproduces_the_uncaught_crash` — fixed pre-repair-commit (`2fd7fe3a`) source comparison.
2. `test_corrupted_unrelated_session_file_no_longer_crashes_lookup` — unit-level: no longer raises the raw, untranslated domain exception.
3. `test_corrupted_unrelated_session_file_no_longer_crashes_auto_publish` — `auto_publish_confirmed_session` returns `application_error`, does not raise.
4. `test_unrelated_corruption_does_not_mask_a_real_confirmed_match` — a genuine confirmed match for the current subject is still found despite unrelated corruption elsewhere.
5. `test_unrelated_corruption_alone_yields_application_error_not_none` — no readable match + corruption present → translated application error, not `None`.
6. `test_no_session_bound_case_is_still_a_pure_none_when_store_is_clean` — ordinary clean-store case unaffected.
7. `test_multiple_unrelated_corrupt_records_deterministic` — multiple corrupt files + one real match: deterministic result.
8. `test_multiple_unrelated_corrupt_records_no_match_is_application_error` — multiple corrupt files, no match: `application_error`, not `no_session_bound`.
9. `test_no_bound_session_remains_a_pure_no_op` — regression: `no_session_bound` unaffected.
10. `test_confirmed_session_lookup_unaffected_when_store_has_no_corruption` — regression: ordinary confirmed lookup unaffected.
11. `test_duplicate_subject_ref_ambiguity_unchanged_by_this_repair` — §6's disposition, pinned.
12. `test_subprocess_pcae_phase_complete_no_longer_crashes_on_unrelated_corrupt_session` — **mandatory literal subprocess E2E** (brief §25): real `python -m pcae phase complete` in a disposable repo, unrelated corrupt session file present, exit code 0, no traceback.
13. `test_subprocess_pcae_phase_complete_still_works_with_zero_sessions` — subprocess baseline regression: no session at all.
14. `test_no_new_cross_zone_import_introduced_by_the_repair` — architecture-policy re-check: `session_service.py` gained no new `commands`/`core` import.

`tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py` (3C.3's own suite): the one test that documented the BLOCKING defect as-reproduced (`test_corrupted_unrelated_session_file_crashes_auto_publish`) has its assertions updated in place — the prior "raises uncaught `SessionStoreCorruptError`" expectation *was* the defect; the updated assertions confirm the corruption is now surfaced through the existing `ApplicationServiceError`/`AutoPublicationOutcome` vocabulary instead. No other test in this file was modified. All 22 tests pass unmodified in behavior/intent, 21 of them byte-for-byte unchanged.

## 8. Regression evidence

| Suite | Result |
|---|---|
| `tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_corrupt_store_fail_closed_repair.py` (new) | 14 passed |
| `tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py` (3C.3, updated in place) | 22 passed |
| `tests/test_phase_149o_20l_7o_3c_2_governed_capability_consumption_integration.py` (3C.2) | included below, all passed |
| `tests/test_phase_145d_session_repository_filesystem_implementation.py`, `test_phase_145e_pending_readiness_store_filesystem_implementation.py`, `test_phase_145g_decision_session_cli.py`, `test_phase_145g1_decision_session_cli_repair.py`, `test_phase_145g2_decision_selection_cli_repair.py`, `test_phase_145g3_decision_session_identity_binding.py` (session/publication lifecycle) | 284 passed total (combined with 3C.2 above) |
| `tests/test_architecture.py`, `tests/test_policy.py` (architecture/zone policy) | 180 passed |
| `tests/test_chgr_*.py` (6 files), `tests/test_permission_broker*.py` (3 files), `tests/test_phase_144c_publication_coordinator.py`, `tests/test_iwc_143o_session_coordination_publication_handoff.py`, `tests/test_task_finish_*.py` (3 files) | 585 passed, 2 failed (`test_chgr_packaging.py`'s two `python -m build` wheel-packaging tests) — **pre-existing, unrelated**: independently reproduced identical against `git stash`-clean phase-entry source (byte-for-byte same failure, a local build-environment issue unrelated to this diff, not touching any file this phase changed) |
| `tests/test_phase.py` (full file — `pcae phase complete`/`prompt-capture` etc.) | 886 passed |
| `tests/test_session.py` | 145 passed |
| `tests/test_notifications.py`, `tests/test_notifications_cli.py`, `tests/test_notification_certification_idempotency.py` | 56 passed |

## 9. Fast Green

*(recorded below once the phase-entry-baseline-vs-repaired-source Fast Green A/B run, launched in the background during this phase, completes)*

## 10. Runtime boundary

`pcae runtime inspect` before and after this phase's work: `Observed / observe / unavailable` — unchanged. No file under `src/pcae/cltr/`, HATP/HMIC/Class-B, shell-gate, or rollback-execution paths appears in this phase's diff.

## 11. Plan B+ / active-task / human-authority / CHGR-uniqueness / Permission-Broker regression re-confirmation

All re-run via the unmodified 3C.2/3C.3 suites (§8 above) plus this phase's own §7 items 4/7 (unrelated corruption does not mask or alter a real confirmed match/publish attempt) and item 9/10 (`no_session_bound` unaffected): no semantic change to Interactive Workflow auto-route, CHGR uniqueness/idempotency, Permission Broker coverage, or Publication Execution Ownership invocation conditions. Human authority preservation (no automatic positive decision for any non-`Confirmed` state) is untouched by this repair — the changed code path is only reached inside the scan loop that runs *before* any state-branch decision, and this repair adds no new branch that could fabricate a positive outcome.

## 12. Release state (unchanged)

v0.3.2 remains **NOT RELEASED**. No tag, GitHub Release, artifact upload, or PyPI publication occurred. No version was changed. The unpinned-`hatchling` reproducible-build issue remains open, carried forward unmodified. The article track remains stopped; `~/repos/pcae-deepseek-research` was not inspected, modified, or imported from.

## 13. Final verdict

```
AUTO-PUBLISH CORRUPT-STORE DEFECT:      REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED
UNRELATED CORRUPT SESSION:              NO LONGER CRASHES PCAE PHASE COMPLETE
RELEVANT CORRUPT SESSION:               FAILS CLOSED (application_error, no session fabricated)
PLAN B+ HAPPY PATH:                     PRESERVED
HUMAN AUTHORITY:                        PRESERVED
CHGR UNIQUENESS:                        PRESERVED
PERMISSION BROKER COVERAGE:             PRESERVED
RUNTIME:                                Observed / observe / unavailable
RELEASE:                                BLOCKED PENDING INDEPENDENT REPAIR VERIFICATION
```

## 14. Recommended next phase

**149O.20L.7O.3C.3.2 — Auto-Publish Corrupt-Store Repair Independent Verification.** Per the governing brief, this repair must not close its own finding; the next phase must independently reproduce the historical crash from fixed pre-repair source, derive the unrelated-vs-relevant corruption semantics on its own, attack the repaired store/service boundary, run the literal `pcae phase complete` subprocess E2E, verify no traceback, verify relevant-corruption fail-closed behavior, verify unrelated-corruption isolation, verify the duplicate-`subject_ref` disposition, rerun the Plan B+ E2E, and adjudicate finding `B-149O.20L.7O.3C.3-1`. Only after that phase independently closes the repair should release scope/version/reproducible-build hardening be reconsidered. This phase stops here — 3C.3.2 is not begun automatically.
