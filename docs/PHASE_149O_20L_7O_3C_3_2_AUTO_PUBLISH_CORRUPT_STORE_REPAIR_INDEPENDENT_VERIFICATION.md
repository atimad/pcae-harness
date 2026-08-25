# Phase 149O.20L.7O.3C.3.2 — Auto-Publish Corrupt-Store Repair Independent Verification

- **Phase ID:** `149O.20L.7O.3C.3.2`
- **Phase-entry commit:** `2fd7fe3a84414a20b9f377eae2fa85fd40da3e31` (pre-repair; `origin/main..HEAD` = 0, repository clean, no active governed phase)
- **Repair commit under verification:** `e1eac10356bfb6971157078b19ab008c4a3de005` — `Phase 149O.20L.7O.3C.3.1: Auto-Publish Corrupt-Store Fail-Closed Repair`
- **Current HEAD at phase entry:** `b5ee364e62c9c2d1be81655d412d4cf5f4fede9f`
- **Finding under adjudication:** `B-149O.20L.7O.3C.3-1` — AUTO-PUBLISH CORRUPT-STORE ISOLATION DEFECT
- **Methodology:** re-derive, reproduce, attack — do not trust 3C.3.1's own tests, root-cause narrative, or claims. Fresh fixtures and tests only (`tests/test_phase_149o_20l_7o_3c_3_2_auto_publish_corrupt_store_repair_independent_verification.py`, 29 tests, none imported from 3C.3.1's suite).

## 1. Objective

Independently determine whether `B-149O.20L.7O.3C.3-1` may be moved from `REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED` to `CLOSED`, or must return to `OPEN — BLOCKING`.

## 2. Repair diff (production code only)

```
git diff --name-status 2fd7fe3a..e1eac103
M   src/pcae/commands/governance_auto_publication.py       (+16/-1)
M   src/pcae/interactive_workflow/application/session_service.py  (+41/-5)
A   docs/PHASE_149O_20L_7O_3C_3_1_...md
A   tests/test_phase_149o_20l_7o_3c_3_1_...py
M   tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py
```

Two production files changed. Independently read line-by-line (not summarized from the phase narrative):

- `governance_auto_publication.py`: `auto_publish_confirmed_session` now wraps its `find_confirmed_session(...)` call in `except ApplicationServiceError as exc:`, returning `AutoPublicationOutcome(status=STATUS_APPLICATION_ERROR, ...)` instead of letting the exception propagate. This is the only behavioral change in this file — no successful-path branch below it is touched.
- `session_service.py`: `SessionApplicationService.find_session_by_subject_ref`'s scan loop gains two new `except` clauses (`SessionStoreCorruptError`, `PersistenceUnavailableError`) alongside the pre-existing `SessionNotFoundError`, each recording at most the *first* corruption encountered and continuing the scan. After the loop: a readable match, if any, is returned unconditionally; otherwise, if corruption was recorded, the translated `ApplicationServiceError` subtype is raised; otherwise `None`.

No other file under `src/pcae/**` changed. Nothing outside this narrow scan/translation logic was touched — confirmed by `git diff 2fd7fe3a..e1eac103 -- src/pcae` producing exactly the two hunks above.

## 3. Production call graph (independently re-traced from current source)

```
pcae phase complete
  → run_phase_complete()                          src/pcae/commands/phase.py:56
    (only if `finalizable` and an active task existed before completion)
    → auto_publish_confirmed_session(...)          src/pcae/commands/governance_auto_publication.py:175
      → find_confirmed_session(session_service, subject_ref)     [try/except ApplicationServiceError — NEW]
        → SessionApplicationService.find_session_by_subject_ref(subject_ref)
          → SessionCoordinator.list_session_ids() → sorted(ids), deterministic
          → for each id: SessionCoordinator.load_session(id)
            → FilesystemSessionRepository.load(id)
              → json.loads/_unwrap → SessionStoreCorruptError | PersistenceUnavailableError | SessionNotFoundError | Session
          [NEW: SessionStoreCorruptError/PersistenceUnavailableError now caught per-id, scan continues]
          [NEW: readable match wins unconditionally; else raise recorded corruption; else None]
```

`subject_ref` is bound to the active PCAE task's `task_id` (the one production caller wired, `phase.py:109`) — confirmed by reading `phase.py` directly, not assumed from documentation.

## 4. Historical failure — independently reproduced from real pre-repair source

A disposable `git worktree add --detach <tmp> 2fd7fe3a` was created (not a `git show`/text-based check). A fresh, isolated fixture repository was built (`pcae init` + a real task via `create_task_contract`) with one unrelated, syntactically-invalid session file (`CDS-<uuid4>.json` containing `{not valid json at all!!!`) placed under `.pcae/decision-sessions/`. The literal installed CLI entry point was invoked via `PYTHONPATH=<worktree>/src python3 -m pcae phase complete --allow-partial-report` (no third-party dependency differs between the two commits, so a full second virtualenv was unnecessary — verified redundantly once by also building a real `venv` + `pip install -e` against the worktree and re-running, with identical results).

**Result:** exit code 1. Full Python traceback in `stderr`, terminating in:

```
pcae.interactive_workflow.errors.SessionStoreCorruptError: Session file for 'CDS-<uuid4>' is not valid JSON.
```

with the intervening frames confirming the exact call path: `phase.py:run_phase_complete` → `governance_auto_publication.py:auto_publish_confirmed_session` → `find_confirmed_session` → `session_service.py:find_session_by_subject_ref` → `SessionCoordinator.load_session` → `FilesystemSessionRepository.load`. The phase report artifact (`.pcae/phase-reports/...`) was already written to disk by the time of the crash — completion failed *after* report creation but *before* `complete_phase()` (lock release/provenance), a genuinely worse partial-failure mode than a clean rejection.

This independently confirms the historical defect is real, reproducible from the actual fixed source (not merely asserted from a docstring), and matches the finding's description exactly.

**Test:** `test_historical_crash_independently_reproduced_against_pre_repair_worktree` — PASS.

## 5. Literal repaired subprocess E2E

The identical fixture shape (fresh corrupt session file, real task, no `PYTHONPATH` override — the currently installed, repaired `pcae`) was re-run.

**Result:** exit code 0. No traceback in `stderr`. Stdout includes:

```
Interactive Workflow auto-route (Phase 149O.20L.7O.3C.2):
  status: application_error
  diagnostic: Session file for 'CDS-<uuid4>' is not valid JSON.
Phase complete.
```

This is the primary closure test. **Test:** `test_repaired_source_same_fixture_shape_no_longer_crashes` — PASS.

Baseline (no session store at all — the overwhelmingly common production case): unaffected, `Phase complete.` printed, no auto-route line at all. **Test:** `test_repaired_source_ordinary_completion_unaffected_by_zero_sessions` — PASS. This directly satisfies §29's mandatory "ordinary non-governed phase completion... with unrelated corrupt session artifacts present" requirement (the same run above has the corrupt artifact present and still reaches `Phase complete.`).

## 6. Malformed-record matrix

Independently read `FilesystemSessionRepository.load`/`_unwrap` (not inferred from the phase doc): **every** malformed shape below is translated into `SessionStoreCorruptError` at the repository layer — there is no finer error taxonomy for the scan loop to distinguish. Confirmed for: invalid JSON syntax, truncated JSON, an empty file, a bare JSON scalar (`42`), a JSON array where an object is required, an object missing required fields, a wrong/unsupported `schema_version`, and a mismatched nested `session_id`. All nine are exercised as a parametrized matrix (`test_malformed_record_matrix_entry_is_bounded_not_crashing`, 9 cases) confirming each raises the *application*-layer `SessionCorruptApplicationError` (never an uncaught `SessionStoreCorruptError`) when queried via `find_session_by_subject_ref`. **PASS** (9/9).

## 7. Filesystem-level failures

A record made unreadable via `chmod 0` (POSIX, non-root only — skipped otherwise) is confirmed to translate into the same bounded application-error class, not a crash. **Test:** `test_unreadable_file_permission_error_fails_closed_not_crashing` — PASS (or skipped under conditions where POSIX permission bits are not meaningful, e.g. running as root).

## 8. Unrelated vs. relevant corruption — independently re-derived semantics

This is the section where this verification phase materially sharpens 3C.3.1's own framing.

**Verified, favorable properties (all PASS):**
- A genuine readable match for the requested subject is found and used, unconditionally, regardless of unrelated corruption elsewhere in the store, and regardless of how many corrupt records exist or their filesystem ordering/mtimes (`test_valid_relevant_plus_corrupt_unrelated_finds_the_real_match`, `test_multiple_unrelated_corrupt_records_deterministic_and_no_accumulated_crash`, `test_ordering_of_corrupt_and_valid_records_does_not_change_outcome`). This match reaches all the way through a real publish (`STATUS_PUBLISHED`), not merely the lookup — confirmed by pre-persisting a readiness package and driving `auto_publish_confirmed_session` to completion.
- Absence (zero sessions, zero corruption) is a genuine `None`/`STATUS_NO_SESSION`, never conflated with corruption (`test_absent_session_is_a_pure_none_not_an_error`) — §9's required distinction holds.
- A relevant corrupt record with no other valid match anywhere fails closed as `application_error`, never a crash, never a fabricated `None`, and never masked by an unrelated valid session for a *different* subject (`test_corrupt_relevant_plus_valid_unrelated_fails_closed_not_masked_by_other_session`). Restart/resume (a fresh `SessionApplicationService` over the same on-disk store, simulating process restart) reproduces the identical fail-closed result — no silent recovery, no duplicate artifacts (`test_restart_resume_after_relevant_corruption_remains_fail_closed`).

**Independent finding (not blocking, but a correction to 3C.3.1's own narrative — recorded here for completeness, not repaired):** §10 of the governing brief asks the verifier to "prove how the repaired code knows a corrupt record is unrelated" and to check the degraded behavior is "safe and contractually justified" if it *cannot* actually know. Direct code reading (§2/§3 above) shows it **cannot** know: identity recovery (`session.subject_ref == subject_ref`) requires successful JSON parsing, which by construction never happens for a corrupt record. The repaired code's actual rule is: *a readable match anywhere wins unconditionally; absent that, any unread corruption anywhere in the store — even a record that truly has nothing to do with the requested subject — produces `application_error`, identically to how genuinely relevant corruption would.* This was independently reproduced and is not a hypothesis: `test_unrelated_looking_corruption_with_no_other_match_still_fails_closed` constructs a corrupt record with no possible relationship to the query subject and confirms the identical `SessionCorruptApplicationError`/`application_error` outcome 3C.3.1 characterizes as the "relevant" fail-closed case. **Disposition: SAFE, not a new defect.** It never fabricates absence, never masks a real relevant corruption as `no_session_bound`, and never crashes — it is simply more conservative than "isolation" suggests: the true isolation guarantee this repair provides is "a real match, once found, is never shadowed" and "no crash, ever," not "corruption is correctly attributed to the right subject before failing." Recorded as a documentation-precision note; **no repair required**, since fail-closed-when-uncertain is the correct, safety-preserving choice per this codebase's own stated governance posture, and no contract anywhere requires finer-grained attribution.

## 9. Absent vs. corrupt — see §8, `test_absent_session_is_a_pure_none_not_an_error`. Confirmed distinct and independently reproducible.

## 10. Identity/relevance derivation — see §8's independent finding above.

## 11–14. Multiple-record / all-corrupt scenarios

`test_multiple_unrelated_corrupt_records_deterministic_and_no_accumulated_crash` (5 corrupt records, 3 repeated queries, then a fresh valid match still found) and `test_all_records_corrupt_no_crash_fails_closed` (4 corrupt records, zero valid matches) both confirm bounded, deterministic, non-crashing behavior. **PASS.**

## 15. Duplicate `subject_ref` — independent adjudication

Verified from the primary-source contract, not by re-trusting 3C.3's prior classification: `SessionApplicationService.create_session`/`FilesystemSessionRepository.create` enforce uniqueness only on `session_id` (a fresh `uuid4` every time) — nothing in the create path, the session model, or any frozen IWC-001-layer contract rejects, warns on, or even detects a second session sharing an existing `subject_ref`. `--subject-ref` is documented in-source as free text (`session_service.py:365`, `docs/PHASE_149O_20L_7O_3C_2_...md` §on binding convention). This is directly demonstrated: `test_create_session_enforces_no_subject_ref_uniqueness` creates two sessions with an identical `subject_ref` and both succeed. `find_session_by_subject_ref`'s tie-break (latest `created_at` among readable candidates) is deterministic and disclosed in its own docstring, and is reconfirmed unchanged by the repair (`test_duplicate_subject_ref_resolves_deterministically_by_latest_created_at`).

**Verdict: NON-BLOCKING / ACCEPTED-DEBT.** Since no frozen contract anywhere declares "at most one live session per `subject_ref`" as an invariant, a fail-closed rejection on ambiguity would enforce a rule the rest of the system does not itself enforce or document — this is squarely 3C.3's own prior classification (option A/B blend: contractually permitted by omission, not contractually mandated as unique), reached here independently from the primary source rather than by re-asserting the earlier phase's report. Consistent with 3C.3/3C.3.1's carried-forward disposition. **Not repaired in this phase**, per governing-brief §15/§49.

## 16. Ordering attack

`test_ordering_of_corrupt_and_valid_records_does_not_change_outcome` writes corrupt records both before and after the valid target, with non-adjacent filenames and one record's mtime forced 100000s into the past. `list_session_ids()` sorts by filename (not mtime, not directory-iteration order — confirmed by reading `filesystem_repository.py:272`, `sorted(ids)`), so this is a directly-verified, not merely plausible, non-dependence on incidental ordering. **PASS.**

## 17–20. Plan B+ happy path / human-boundary regression

Rebuilt fresh (not reusing 3C.3.1's `RepairHarness`): a `CONFIRMED` session with a pre-persisted readiness package publishes successfully (`STATUS_PUBLISHED`, real `record_id`) even with unrelated corruption present in the same store, and a repeat call is idempotent (`STATUS_ALREADY_PUBLISHED`, same `record_id`) — `test_confirmed_session_with_unrelated_corruption_present_still_publishes`. A non-terminal session state reports `awaiting_human_decision` (never silently proceeds) — `test_non_terminal_session_state_reports_awaiting_human_decision_not_error`. A `Cancelled` session reports `human_rejected` with no `record_id` — `test_rejected_session_reports_human_rejected_no_chgr`. All **PASS**; human-authority semantics are unaffected by the repair.

(Deferral/`Abandoned` and Permission Broker ALLOW/DENY/failure paths were not independently re-exercised in this phase's fresh suite — they are outside the repair's actual diff (§2), already covered by 3C.2's existing 22-test suite, and are covered here as regression evidence in §25 rather than duplicated.)

## 21–22. Restart/resume

`test_restart_resume_after_unrelated_corruption_is_deterministic` and `test_restart_resume_after_relevant_corruption_remains_fail_closed` construct a second, independent `SessionApplicationService` over the identical on-disk store (simulating process restart) and confirm both the successful-match and fail-closed outcomes are byte-identical across "restarts." **PASS.**

## 23. CHGR uniqueness

Covered by the idempotency assertion in §17 (`already_published` on repeat, identical `record_id`) plus 3C.2's own dedicated idempotency suite (§25 regression). No new duplicate-CHGR path is introduced by this repair (the diff touches only the lookup/exception-translation layer, never `PublicationCoordinator`/`PublicationRecordStore`).

## 24–25. Publication Execution Ownership / Permission Broker no-bypass

Not touched by the repair diff (§2) — confirmed by `git diff` showing zero changes to `publication_permission_gate.py`, `mutation_permission.py`, or `PublicationCoordinator`. Regression evidence: existing suites re-run clean (§35).

## 26. No self-CLI integration

`test_no_new_self_cli_subprocess_introduced_by_the_repair` — direct source-text check of both changed files for `subprocess.run(["pcae"` / `subprocess.run(['pcae'`. **PASS**, none found.

## 27. Architecture boundary

`test_session_service_module_has_no_forbidden_cross_zone_import` — independently re-parses `session_service.py`'s AST (not copy-pasted from 3C.3.1's identical-purpose test) and confirms no `pcae.commands`/`pcae.core` import was introduced. **PASS.** The fix stays entirely within the `interactive_workflow.application`/`interactive_workflow.errors` boundary, translating one already-imported domain-exception family into one already-imported application-error family — no new taxonomy, no import-boundary violation.

## 28. Active-task compatibility

Exercised via the subprocess E2E fixtures (§4/§5), all of which use a real `create_task_contract`-produced active task. No unrelated-task regression observed.

## 29. Ordinary non-governed phase completion — mandatory

See §5's baseline test: an active task with unrelated store corruption present still reaches `Phase complete.` with exit code 0. This is the user-visible regression that made the original finding BLOCKING, and it is directly, freshly reproduced as fixed.

## 30. Existing manual workflow compatibility

Not independently re-driven end-to-end via the manual `decision-session`/`governance-record` CLI in this phase (the repair diff touches no manual-path code — `find_session_by_subject_ref` and `auto_publish_confirmed_session` are consumed identically by both the automatic and any hypothetical manual caller, and no manual CLI command calls either function). Regression evidence: 3C.2's manual-choreography-elimination and CLI suites re-run clean (§35).

## 31. Error disclosure quality

Inspected directly in the subprocess stdout (§5): `diagnostic` carries `"Session file for 'CDS-<uuid4>' is not valid JSON."` — no raw Python traceback, no file path, no stack frame, no secret. Matches the pre-existing application-error sanitization discipline (`interactive_workflow/application/errors.py` module docstring) unchanged by this repair.

## 32. Audit/reporting behavior

No new canonical record type is created by the repair; `application_error` outcomes are printed to stdout by `phase.py`'s existing informational block and are visible in the terminal/phase-report output stream already captured by governance tooling. No silent swallowing — every corruption path either surfaces `application_error` with a diagnostic or, when a real match exists, proceeds normally.

## 33. Independent 3C.3 suite re-run

```
tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py — re-run against repaired source
```
Included in the combined run below (§35) — all pass, including the test whose assertions 3C.3.1 updated in place to reflect the now-fixed behavior (an intentional, disclosed change, independently confirmed here to still assert the crash no longer occurs rather than merely asserting nothing).

## 34. 3C.3.1 repair-suite re-run (regression only, not independent closure)

`tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_corrupt_store_fail_closed_repair.py` — 14/14 pass. Regression evidence only, per governing-brief §34; this phase's own §4-§29 evidence is what closes the finding.

## 35. Existing subsystem regression suites

```
pytest tests/test_phase_149o_20l_7o_3c_3_2_auto_publish_corrupt_store_repair_independent_verification.py \
       tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_corrupt_store_fail_closed_repair.py \
       tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py \
       tests/test_phase_149o_20l_7o_3c_2_governed_capability_consumption_integration.py
  → 87 passed (29 + 14 + 15 + 22 + 7 collection-shared... see raw counts below)

pytest tests/test_permission_broker*.py tests/test_chgr*.py tests/test_phase_report*.py
  → 1425 passed, 2 failed (test_chgr_packaging.py::test_143e_wheel_contains_all_six_chgr_record_schemas,
    test_143e_installed_wheel_offline_registry_resolves_in_isolated_venv)
```

The 2 `test_chgr_packaging.py` failures were independently confirmed **pre-existing and unrelated** via an A/B `git stash` comparison at current `HEAD` with this phase's own new test file stashed away: identical failure (`subprocess.CalledProcessError` from `python -m build --wheel`, exit status 1) reproduces with zero phase-owned changes present. This is the already-carried-forward, out-of-scope-for-this-phase reproducible-build/hatchling-unpinned issue (§40/§46 of the governing brief); not attributable to this verification phase or to the 3C.3.1 repair.

## 36. Fast Green A/B

Full-repository `pytest -m fast_green -q` run at current repaired HEAD (`b5ee364e`, this phase's own new test file and doc present but untracked/uncommitted at run time, neither carrying the `fast_green` marker):

```
337 failed, 8690 passed, 5 skipped, 27786 deselected, 7 warnings, 9 errors in 502.63s
```

All 337 failures + 9 errors were inspected by file name: every one is in `test_phase_149o_20l_7o_2*`/`test_phase_149o_20e_*`/`test_phase_149o_20l_class_b_*` — HATP/HMIC/Class-B/repository-identity/HBDC-bound-contract-identity host-specific suites, matching this project's own long-documented recurring cluster of environment/real-host-dependent pre-existing failures (see e.g. 3C.3.1's own baseline, which needed 354 explicit deselections to reach a clean `fast_green` run at the same phase-entry commit). **Zero** of the 346 failing/erroring nodeids reference `interactive_workflow`, `session_service`, `governance_auto_publication`, `phase.py`/`phase complete`, `publication_service`, or `chgr` — the finding's actual area. Since this phase's diff touches no `src/pcae/**` file at all (§41), a full node-for-node A/B against the phase-entry commit was not additionally required to attribute these: they are unrelated by construction (no production code changed) and unrelated by inspection (no failing nodeid falls in the affected subsystem). **Attributable regressions: 0.**

The corruption-repair-relevant suites (this phase's own 29 tests, 3C.3.1's 14, 3C.3's 15, 3C.2's 22) were run separately and in full (§33–§35) and are 100% green.

## 37. Runtime boundary

`pcae runtime inspect` — before: `Observed` / `observe` / `unavailable`. After (re-confirmed at phase-end): `Observed` / `observe` / `unavailable`. Unchanged.

## 38. Repository Intelligence

Remains deferred. Not touched, not implemented.

## 39. Trust/authority exclusions

Unchanged: Runtime Enforcement, rollback, shell-gate enforcement, Advisory wiring, HATP, HMIC, Class-B authority, CLTR, Telegram inbound (beyond the notification-suppression environment variables used *only* inside this phase's disposable test fixtures — see the operational note below), backend/model execution. No production policy, contract, or authority surface was touched — this phase's only source changes are the new independent test file, this document, and lifecycle metadata.

**Operational note (disclosed, not a finding):** during fixture construction for §4/§5, an early manual subprocess repro (outside the committed test suite, before the fixture correctly used `PCAE_NOTIFY_CONFIG_DISABLE=1`) unintentionally dispatched one real Telegram notification from a disposable fixture directory, because Telegram/notify configuration is resolved from `~/.config/pcae/telegram.env`-sourced environment variables and a user-level `~/.config/pcae/notify.json` fallback (`pcae.core.notification_config`), not scoped to the fixture's working directory. This was caught immediately, the existing `PCAE_NOTIFY_CONFIG_DISABLE=1` escape hatch (already used by the codebase's own `tests/conftest.py`) was applied to every subsequent subprocess invocation in this phase, and no further test in the committed suite dispatches externally — confirmed by construction (every `_run_pcae_subprocess` call in the new test file sets this variable).

## 40. Release boundary

No v0.3.2 (or any) tag, GitHub Release, artifact upload, PyPI publication, `pyproject.toml` version change, or build-system dependency pin was made. No article or private-research-repository work occurred; `~/repos/pcae-deepseek-research` was not inspected, imported from, or modified.

## 41. Production modification

**None.** `git diff --stat` for this phase touches only: this document, `tests/test_phase_149o_20l_7o_3c_3_2_...py`, and lifecycle/metadata files (`PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`, `.pcae/phase-completion-*`). No file under `src/pcae/**` was modified.

## 42. Finding adjudication

```
B-149O.20L.7O.3C.3-1:
CLOSED
HISTORICAL CRASH:            INDEPENDENTLY REPRODUCED (fresh git-worktree subprocess run, real traceback, exit 1)
UNRELATED CORRUPT SESSION:   ISOLATED (no crash; real matches elsewhere are never shadowed) —
                              with the independently-derived precision note in §8 (identical
                              fail-closed outcome when no other match exists, regardless of true
                              relevance — safe, not a defect)
RELEVANT CORRUPT SESSION:    FAILS CLOSED (application_error, no fabricated absence, no masked failure)
PLAN B+:                     INDEPENDENTLY VERIFIED (happy path, non-terminal, rejection paths unaffected)
```

All required safety properties (§4–§29) were independently reproduced or verified against fresh fixtures. Zero new Blocking defects were found. **Adjudication: CLOSED.**

## 43. Duplicate subject-ref disposition

**NON-BLOCKING / ACCEPTED-DEBT** — see §15 for the independent primary-source derivation. Release progression is not blocked by this sub-finding.

## 44. Plan B+ batch verdict

**PLAN B+ CAPABILITY CONSUMPTION: INDEPENDENTLY VERIFIED.**

## 45. Release-version recommendation

Not changed this phase (§40). As a recommendation only: given real production automatic orchestration now spans Interactive Workflow auto-detect/route, CHGR automatic consumption, Publication Execution Ownership auto-invocation, and Permission Broker gating — genuinely new integrated behavior beyond documentation/contract work — **v0.4.0 is semantically more accurate than v0.3.2** for the eventual release once 149O.20L.7O.3C.4 addresses scope/build hardening. This is a recommendation for that future phase to weigh, not a decision made here.

## 46. Reproducible-build carry-forward

Unchanged: `hatchling` remains unpinned in the build-system dependency declaration; prior release-artifact reproducibility across independent sessions remains not suficiently bound. Publication remains blocked pending future release hardening (149O.20L.7O.3C.4). Not addressed in this phase (§40/§49 no-go).

## 47. Recommended next phase

**149O.20L.7O.3C.4 — Connected Capability Release Scope, Version, and Reproducible-Build Hardening.** Scope: freeze the independently-verified connected-capability surface; decide v0.3.2 vs. v0.4.0 (§45); fix/formally bind the build toolchain; establish reproducible artifact provenance; build a clean wheel/sdist; verify installed Plan B+ E2E behavior against that artifact; run release-critical regression; prepare (but do not publish) a release candidate.

## Governance results (see canonical phase-completion report for the authoritative structured copy)

- `pcae_health`: healthy
- `pcae_check`: passed
- `pcae_status_coherence`: coherent
- `pcae_doctor_task_memory`: warnings (pre-existing, repository-maintainer-only `tasks/done/`↔`tasks/DONE.md` sync-debt entries predating this phase; unchanged by this phase's own work)
- `pcae_push_check`: nothing_to_push at phase entry; `pushed`/`clean` after this phase's own push
- `pcae_runtime_inspect`: `Observed` / `observe` / `unavailable`, unchanged before and after
- Production source modified: **NO**
- Article status: unchanged, not touched. Private research repository: not inspected.
