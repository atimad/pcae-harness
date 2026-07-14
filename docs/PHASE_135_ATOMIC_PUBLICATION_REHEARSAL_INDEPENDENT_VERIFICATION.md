# Phase 135T — Atomic Publication Rehearsal Independent Verification

## 1. Verification philosophy

Re-derive, reproduce, attack, do not trust. Nothing in the 135S canonical report, 135S's own documentation, 135S's own test names, or 135S's own assertions was accepted as proof. Every claim checked in this phase was independently re-derived from the frozen contract (135M–135R, CLTR-001, CLTR-SCHEMA-001 v1.0.1) and from direct inspection of source, tests, and live filesystem/CLI behavior, or from a fresh reproduction in an isolated worktree.

## 2. Source-of-truth hierarchy

1. CLTR-001, CLTR-SCHEMA-001 v1.0.1 (frozen semantic/wire contracts).
2. 135M/135N (six-stage migration contract, repaired), 135O/135P (Stage 1 implementation and its independent verification).
3. 135Q (Stage 2 contract and implementation plan) — read directly, section by section, not through 135S's paraphrase.
4. 135R (Stage 2 contract verification — F-135R-1..4 read directly from its own text).
5. Actual 135S source (`src/pcae/cltr/migration/rehearsal/`, `src/pcae/core/finalization_transaction.py`, `src/pcae/cltr/migration/cltr_derivation.py`, `src/pcae/cltr/migration/disclosure.py`, `src/pcae/commands/cltr_migration.py`) and actual 135S tests, read in full.
6. Live filesystem behavior, live CLI behavior, and a live isolated-worktree baseline reproduction — never assumed from prose.

135S's own canonical report and its own implementation document were treated as claims to verify, not as evidence.

## 3. Repository and commit baseline

- Working tree clean at session start; `origin/main..HEAD` = 0.
- 135S phase-owned commits, verified by direct inspection (`git show --stat`), not inferred from recent history: `bfb943a9` (Atomic Publication Rehearsal Implementation, 34 files, 3279 insertions/92 deletions) and `ec846dc0` (task-contract cleanup, 1 file).
- `pcae phase-report reconcile --phase-id 135S` (read-only): reconciled, 1 promoted generation, marker `already_dispatched`, checkpoint `completed`, receipt `finalized`, mutation: none.
- Pre-135S baseline commit used for isolated reproduction: `bfb943a9^` = `7fb4dbc1` (Phase 135R closure commit). Reproduced in a separate `git worktree` (`baseline-135r`), never mutating the primary repository; worktree removed after use.

## 4. 135S change inventory (independently read, not summarized from 135S's own text)

New package `src/pcae/cltr/migration/rehearsal/` (16 modules, ~1,911 lines): `enums.py`, `models.py`, `identity.py`, `digest.py`, `configuration.py`, `comparison.py`, `candidates.py`, `manifest.py`, `persistence.py`, `pointer.py`, `evidence.py`, `recovery.py`, `reconciliation.py`, `status.py`, `coordinator.py`, `__init__.py`. Modified: `src/pcae/cli.py`, `src/pcae/cltr/migration/cltr_derivation.py` (F-135P-3 fix), `coordinator.py`/`disclosure.py`/`evidence.py`/`persistence.py`/`reconciliation.py`/`status.py` (F-135P-4 fix, shared `disclosure.py` constant), `src/pcae/commands/cltr_migration.py` (new read-only CLI subcommands), `src/pcae/core/finalization_transaction.py` (F-135P-1 fix, single Stage 2 integration call site `_run_stage2_atomic_rehearsal`).

## 5. Import/dependency proof

Direct grep of `src/pcae/cltr/migration/rehearsal/` for `subprocess|socket|urllib|http.client|requests\.|os\.system|os\.exec`: zero matches. Direct grep for `telegram`: exactly one match, a string literal `"intended_channel": "telegram"` inside the notification-intent candidate content (a channel-type label, never an import or a call). No import of `cltr_prototype`. Digest/canonicalization logic is imported from `pcae.cltr.digest`/`pcae.cltr.canonicalization` (never reimplemented). Containment primitives (`is_safe_segment`, `safe_join`, `write_atomic`) are imported from Stage 1's `pcae.cltr.migration.persistence`, not duplicated. **Confirmed** (see §8 for the one exception found, and its repair).

## 6. Stage 2 authority-boundary verification

Re-read 135Q §5's authority matrix directly. `production_authority` is a fixed `ProductionAuthority.LEGACY` literal (`identity.py: PRODUCTION_AUTHORITY_DISCLOSURE = "legacy"`), never read from a mutable flag. No code path in `rehearsal/` opens a production path (`.pcae/phase-reports/`, production checkpoint/marker/receipt paths) for writing — confirmed by grep of the entire package for `phase-reports` and by direct read of every module. **Confirmed.**

## 7. Configuration verification

`configuration.py` re-read directly. Disabled by default (`_env_bool` returns `False` on unset). Deterministic boolean parsing (`"1"|"true"|"yes"`, case-insensitive). Every invalid-configuration case in 135Q §46 is checked, in order, with a specific diagnostic: rehearsal enabled without Stage 1 dual-derivation; wrong `migration_stage`; missing epoch; non-legacy `production_authority`; a Stage-3-reserved flag present. All independently exercised by both 135S's own `TestConfiguration` tests and (for the reserved-flag and missing-epoch cases) already covered; no gap found. `RehearsalConfiguration.effectively_active` requires both the Stage 2 flag and Stage 1's own `effectively_active`, so Stage 2 can never be active while Stage 1 is inactive. No flag or flag combination touches `production_authority`, which is hardcoded in a separate module (`identity.py`) never read by `configuration.py`. **Confirmed.**

## 8. Precondition verification (independently attacked)

135Q §21's precondition list re-derived directly from the contract text (not from `coordinator.py`'s own docstring). `_precondition_failures` in `coordinator.py` checks: rehearsal effectively active; `LEGACY_COMPLETION`-stage revision present; Stage 1 status `completed`; no Stage 1 authority-relevant mismatch; non-empty `migration_epoch`/`authority_epoch`. Confirmed each failure independently: constructing a package missing a `LEGACY_COMPLETION` revision, or with `stage1_status != "completed"`, or with an authority-relevant Stage 1 mismatch, each produces `REJECTED_PRECONDITION` with no candidate directory created (verified: `candidates_dir` is never touched before the precondition check — reconfirmed by reading the exact statement ordering in `run_stage2_rehearsal`, `step = "candidate_directory_creation"` occurs strictly after the precondition-failure early return). **Confirmed.**

## 9. Deterministic identity verification

Re-derived the identity formula directly from 135Q §6 and independently from `identity.py`'s implementation (not accepted as matching by inspection alone). New adversarial tests added in this phase (`TestIdentityDeterminism`, `tests/test_cltr_rehearsal_135t_independent_verification.py`):

- Repeated computation in the same process is stable.
- **Stable across a fresh, separate Python subprocess** — the identity is recomputed in a brand-new interpreter with no shared global state and matches the parent process's value exactly.
- Each of six independently bound fields (`migration_epoch`, `authority_epoch`, `transition_id`, `shared_input_package_id`, `final_input_revision_digest`, `phase_id`), plus `task_id` and `schema_versions`, independently changes the identity when varied one at a time, holding all others constant.

No wall-clock, random-UUID, filename-discovery, or title-derived input is read anywhere in `identity.py` — confirmed by direct reading of the module (43 lines total, no `time`/`uuid`/`random`/`Path.glob` import). **Confirmed.**

## 10. Exact 23-item candidate inventory verification

Independently re-derived 135Q §9's table (23 items) directly from the contract text (reproduced in full in this phase's own working notes, not copied from `enums.py`'s docstring). 135S's `CandidateKind` enum implements **10 file-producing items** (1–10 of the 23), consistent with 135Q §9's own item roles: items 11 (Git attribution view, V-role, observational) and 14 (Reconciliation view, V-role, observational) are non-blocking by 135Q §22's own policy; items 12–13 (compatibility/legacy-format view, diagnostic envelope) are marked **optional** directly in 135Q §9's table. Items 15–23 are reference/computed/constant fields (shared-input reference, Stage 1 evidence reference, comparison results, manifest, per-artifact digests, generation digest, epochs, limitations, non-authority disclosure) that 135Q §18 itself describes as manifest-bound rather than file-producing, and are in fact present as manifest/evidence-record fields (`shared_input_package_id`, `final_input_revision_digest`, `comparison_results`, `generation_digest`, `migration_epoch`/`authority_epoch`, `limitations`, `non_authority_disclosure`), independently confirmed by reading `models.py`'s `RehearsalManifest` dataclass field-by-field against 135Q §18's bullet list.

135S's own scoping decision to fold items 11–14 into other artifacts / the read-only reconcile command rather than emit them as separate files is **honestly disclosed**, not hidden: `manifest.py`'s `build_manifest` appends an explicit `limitations` entry naming items 11–14 and stating they are "not emitted as separate files in this implementation." This phase added a fresh test (`test_manifest_discloses_folded_items_11_through_14`) asserting this disclosure text is actually present in a real, end-to-end-produced manifest (not merely present in source as an unreached string), and a second test (`test_every_inventory_artifact_file_actually_exists_on_disk`) asserting every one of the 10 file-backed inventory entries' path actually exists on disk with a digest that independently recomputes to the manifest's recorded value. **Confirmed**: exactly 10 required file-producing items, no missing item, no duplicate logical item, no unauthorized extra item silently presented as required, deterministic ordering (`CANDIDATE_ORDER = tuple(CandidateKind)`, fixed enum declaration order), honest disclosure of the 4 folded/optional items.

## 11. Candidate honesty verification

Re-read every candidate builder in `candidates.py` directly:

- **Report candidate**: `report_id` is `f"rehearsal:{rehearsal_generation_id}:{report_id or 'unresolved'}"` — namespaced, never equal to the authoritative `report_id`. Never written to a production path.
- **Metadata candidate**: `metadata_id` is rehearsal-namespaced; `notification_delivery_timestamp` explicitly `{"value": None, "reason": "external_effect_not_occurred"}`, never fabricated.
- **Architecture Status candidate**: `artifact_role = PROJECTED`; `recommended_next_phase` is read directly from the shared input package field, never parsed from prose or inferred from Git history.
- **Checkpoint candidate**: rehearsal-scoped `state` field; no code path writes to a production checkpoint namespace (grep-confirmed).
- **Notification-intent candidate**: `delivery_attempted: False`, `intended_channel: "telegram"` (label only), `idempotency_key` rehearsal-namespaced so it can never collide with a real PFN-001 key.
- **Marker candidate**: `state = "rehearsal_candidate_dispatched_simulated"` — a distinct literal from production's `already_dispatched`/`NOTIFIED`/`NOTIFIED_UNCONFIRMED` states, so no rehearsal marker can be mistaken for, or claim, real dispatch.
- **Receipt candidate**: `delivery_confirmed: False`, `state = "rehearsal_recorded"` — a distinct literal from production's `finalized`, `delivery_timestamp` explicitly null with reason `rehearsal_no_external_effect`.

Adversarial fixtures attempting to inject false terminal claims were not required beyond the above, since every field that would carry such a claim is a fixed, non-configurable literal in source (not derived from any external input an attacker could influence) — confirmed by reading each builder function's full body; there is no code path by which caller-supplied data could override `state`, `delivery_confirmed`, or `delivery_attempted`. **Confirmed.**

## 12. Nineteen-step sequence verification

Re-derived 135Q §20's 19 steps directly from the contract text and traced each to `coordinator.py`'s `run_stage2_rehearsal`, step-by-step, via the function's own `step = "..."` markers (used for failure-evidence tagging, and independently useful as a trace aid): configuration load → precondition check → identity computation → idempotency short-circuit → candidate directory creation → candidate derivation → candidate write (per-artifact, in `CANDIDATE_ORDER`) → digest computation → comparison summary → manifest write → verification (`verify_manifest`, recomputes every digest) → mismatch policy → finalization (candidate → generation rename) → pointer publication (skipped if mismatch-blocked) → pointer verification (readback) → evidence recording. Ordering is enforced by Python's sequential statement order within one function (no reordering possible without editing source); illegal-reorder attacks (pointer before verification, manifest before complete inventory, finalization before digest verification) are structurally impossible here since each step's inputs are the prior step's outputs (e.g. `finalize_generation` is called with `manifest` already verified; `publish` is called with the already-finalized `generation_dir`). **Confirmed**, no missing or reordered step.

## 13. Manifest and digest verification

Re-read `manifest.py` and `digest.py` directly. `verify_manifest` independently recomputes every artifact digest and the generation digest and fails closed (`ManifestVerificationError`) on any mismatch, on an unknown artifact kind, or on a split-brain cross-reference (`rehearsal_generation_id`/`transition_id` mismatch between an artifact and the manifest). This phase added a fresh, real-world tamper test (`TestManifestTamperDetection`) that runs a full coordinator cycle, mutates one on-disk finalized artifact's content directly, and independently re-verifies via `verify_manifest` using freshly reloaded digests — confirming the mismatch is detected against real persisted bytes, not merely against an in-memory unit-test fixture. **Confirmed.**

Generation-digest coverage: independently confirmed `compute_generation_digest` covers the ordered list of already-computed per-artifact digests plus the four identity fields (`rehearsal_generation_id`, `migration_epoch`, `authority_epoch`, `transition_id`), excluding the manifest's own `generation_digest` field from its own input (the caller never passes it). **Confirmed** matches 135Q §19 exactly.

## 14. Containment, immutability, and the symlink-escape finding (CONFIRMED, BLOCKING, repaired)

135Q §7/§25/§47 require: no symlinks created; any pre-existing symlink at a target path aborts the write; same-filesystem atomic rename; fsync-before-digest. `persistence.py` defines `write_candidate_artifact`, which performs exactly the required pre-existing-symlink check (`target.is_symlink()` → `PathContainmentError`) before delegating to `write_atomic` (temp-file + fsync + `os.replace`).

**Independent inspection of `coordinator.py` (pre-repair) found this helper was never called.** Every candidate artifact was written via a bare `(candidate_dir / artifact.filename).write_text(...)`, and the manifest via a bare `(candidate_dir / "manifest.json").write_bytes(...)` — both bypassing the symlink check and the atomic-write/fsync discipline entirely. **Live reproduction** (pre-repair): a symlink pre-placed at a candidate artifact's target path, pointing to a file outside the rehearsal namespace, was silently followed by the exact write statement `coordinator.py` used, and the linked-to file's content was overwritten with rehearsal-candidate content — a genuine, working containment escape, not a theoretical one.

This is classified **CONFIRMED, BLOCKING** under 135Q §7 ("any pre-existing symlink found at a target path during candidate creation causes the attempt to abort"), §25, and §47 ("Symlink escape: blocked by §7/§25"), since the protection these sections require was present in source but structurally unreachable from the only production call site.

**Repair applied** (within the Stage 2 implementation boundary; no contract, CLTR-001, or CLTR-SCHEMA-001 change): `coordinator.py` now calls `write_candidate_artifact` for every candidate artifact write and for the manifest write, both of which now go through the pre-existing-symlink abort and the atomic temp-file/fsync/`os.replace` path. Verified: (a) the original attack, re-run against `write_candidate_artifact` directly, now raises `PathContainmentError` and leaves the outside file untouched; (b) a static-source assertion (`test_manifest_write_path_also_uses_containment_checked_helper`) confirms no bare `.write_text(`/`.write_bytes(` call remains in `run_stage2_rehearsal`; (c) the ordinary successful end-to-end path still completes after the repair. This is classified per this phase's governance rules as **independent verification plus bounded repair**.

Path-traversal containment (`is_safe_segment`/`safe_join`, existing 135S test `TestContainment::test_traversal_segment_rejected`) and dangling/wrong-epoch pointer-target rejection (`TestContainment::test_pointer_rejects_dangling_target`) were independently re-read and confirmed structurally sound; no additional defect found in those paths.

## 15. Atomic pointer verification

`pointer.py` re-read directly. `publish` calls `validate_publication_target` (rejects quarantined targets, dangling targets, digest mismatch between the manifest argument and the on-disk finalized generation) strictly before `write_pointer_atomic` (which now, like candidate writes, goes through `write_atomic`'s temp-file + fsync + `os.replace`). `verify_published_target` performs the required post-publication readback and returns `False` (never a silent success) on any ambiguity, which the coordinator maps to `RehearsalOutcome.UNCERTAIN_PUBLICATION` rather than `SUCCESSFUL`. **Confirmed** no production pointer is ever opened for writing anywhere in this module (grep-confirmed for `phase-reports`, `cltr-shadow`).

## 16. Crash matrix and recovery verification

135Q §26's crash matrix re-derived directly from the contract text. Every named crash point maps to an existing `fault_injector` call site in `coordinator.py` (`before_write_<kind>`/`after_write_<kind>`, `before_manifest_write`/`after_manifest_write`, `verification`, `before_finalization`/`after_finalization`, `before_pointer_publish`/`after_pointer_publish`, `pointer_verification`, `before_evidence_persist`/`after_evidence_persist`), independently confirmed present at 135S's own fault-injection tests' exercised points plus this phase's own repair-verification pass. `recovery.py`'s `classify` function is read-only and state-based (quarantine record → manifest presence → pointer match → evidence presence → candidate completeness), never reading a title, Git history, or `tasks/DONE.md` — confirmed by direct reading of the entire 64-line module (no `subprocess`, no `git`, no title-string parsing). **Confirmed**, consistent with 135Q §27.

## 17. Idempotency, replay, and quarantine verification

`run_stage2_rehearsal`'s idempotency short-circuit (`existing_manifest is not None` → `IDEMPOTENT_REPLAY`, no new write) occurs strictly before any candidate directory is created, confirmed by statement ordering. `finalize_generation` rejects (raises, not silently overwrites) a non-empty pre-existing target directory, matching 135R §29's independently-confirmed directory-vs-file `os.replace` semantics (re-derivation independently agrees with 135R's own analysis on this point — checked directly against Python's documented `os.replace` behavior, not merely accepted from 135R's text). Quarantine (`_persist_quarantine`) is reached only via a `PointerRejectedError` from `publish`, and a quarantined generation can never become `current-rehearsal` since `validate_publication_target` rejects `is_quarantined=True` targets unconditionally, with no override parameter or flag anywhere in the call chain. **Confirmed.**

## 18. Progression eligibility

`progression_eligibility` is `False` whenever `blocked_by_mismatch` is true, and further gated by `verified` (post-pointer-verification). It is computed entirely within `run_stage2_rehearsal` and only ever consumed by read-only `status.py`/`reconciliation.py` — no CLI mutation path exists, no code path outside the coordinator ever sets this field. Confirmed advisory-only, consistent with 135Q §32 and the existing `pcae roadmap next` precedent. **Confirmed.**

## 19. All-four-entry-point verification

Independently traced (via grep, not accepted from 135Q's citation) all four production finalization entry points to their exact call sites: `run_phase_complete`, `run_task_finish`, `run_phase_report_create`, `run_notify_send_report` all funnel through `run_finalization_transaction`, which contains exactly one Stage 2 integration call site, `_run_stage2_atomic_rehearsal(migration_result=migration_result)`, called unconditionally at one place regardless of `entry_point`. `test_no_entry_point_specific_branching_in_stage2_call_sites` (135S's own test, independently re-read and re-run) confirms via `inspect.getsource` that no `if entry_point ==` branch exists in `_run_stage2_atomic_rehearsal`. **Confirmed** single shared coordinator, no entry-point-specific publication semantics.

## 20. 135H.1 escape reproduction

Traced the actual call path: a rejected/incomplete legacy candidate never reaches `LEGACY_COMPLETION` shared-input enrichment in a clean state, which `_precondition_failures` reads and rejects on (`stage1_status != "completed"`, no `LEGACY_COMPLETION` revision) before any candidate directory is created — reconfirmed by direct reading, not by mock-only assertion. A rejected candidate therefore cannot reach candidate write, manifest verification, finalization, or pointer publication; `progression_eligibility` is forced `False`; no marker/receipt/notification path is reachable regardless (§21/§22 below). **Confirmed** by real call-path tracing.

## 21. Production side-effect isolation, notification isolation, marker/receipt isolation

Filesystem-snapshot proof (this phase, live): running `pcae cltr migration rehearsal status` and `pcae cltr migration rehearsal reconcile --phase-id <missing>` against an empty temporary directory left the filesystem **byte-for-byte unchanged** (0 entries before, 0 entries after) — both commands are genuinely read-only, not merely documented as such. Import/grep proof: zero occurrences of `subprocess`, `socket`, `urllib`, `http.client`, `requests.`, `os.system`, or `os.exec` anywhere in `rehearsal/`; the sole `"telegram"` occurrence is a string label, never an import. No code path in `rehearsal/` writes to a production marker or receipt path (grep-confirmed: no reference to production marker/receipt file paths anywhere in the package). **Confirmed.**

## 22. Read-only CLI verification

`run_cltr_migration_rehearsal_status`/`run_cltr_migration_rehearsal_reconcile` (`commands/cltr_migration.py`) are thin wrappers over `rehearsal_status.rehearsal_status()`/`rehearsal_reconciliation.reconcile()`, both already confirmed read-only in §21. Tested with a missing phase ID (returns `found: False` with a truthful blocker, no exception, no mutation) and with rehearsal enabled but no prior rehearsal run (empty transitions list). **Confirmed.**

## 23. No-execution proof

Runtime introspection re-confirmed live: `pcae runtime inspect` reports `Runtime state: Observed`, `Execution capability: unavailable`, `Maximum plugin capability: observe`, `Registry status: empty`, `Plugin count: 0` — unchanged by 135S. Combined with §5/§21's import-graph proof (no subprocess/socket/execution-adapter import anywhere in the new package), this is a structural proof, not merely a passing-test coincidence: the capability class of code that could execute anything simply is not imported. **Confirmed.**

## 24. Production-output equivalence

Compared production report/metadata/Architecture-Status/checkpoint/marker/receipt/notification behavior across Stage 2 disabled, Stage 2 enabled-and-successful, and Stage 2 enabled-and-rejected (via `TestDisabledByDefault`, `TestSuccessfulRehearsal`, `TestPreconditionRejection`, independently re-run this phase): in every case `result.status`/`calls` (the production dispatch callback) are identical regardless of Stage 2's outcome, confirming Stage 2 never alters `run_finalization_transaction`'s return value or side effects (the call is `try/except Exception: pass`-contained one statement after Stage 1 completion, and its return value is discarded, never fed back into `result`). **Confirmed**, no undisclosed difference.

## 25. F-135R-1 through F-135R-4 dispositions (independently re-read from 135R directly)

- **F-135R-1** (persistence.py citation: `137-233` doesn't exist in a 140-line file; actual file-level precedent is `84-112`; directory-level rename is a new, undocumented-as-such primitive): 135R repaired this as a documentation citation fix in 135R's own document, disclosing the Windows-transient-`PermissionError` caveat. Independently confirmed the underlying claim (directory-level `os.replace` is POSIX-atomic) is correct, and confirmed 135S's `persistence.py` (`finalize_generation`) actually implements the disclosed Windows-transient-failure retry (`_RENAME_RETRY_ATTEMPTS = 3`, bounded backoff) — i.e., 135S did not merely inherit the disclosure, it implemented the mitigation 135R recommended. **Disposition: resolved in implementation, beyond what 135R required.**
- **F-135R-2** (`NON_AUTHORITY_DISCLOSURE` hardcoded 7 times repo-wide, not 5; 2 extra copies in the Stage 0 `cltr/` namespace, out of Stage 2's scope): independently re-grepped this phase (§5 above, plus direct grep of `src/pcae/cltr/persistence.py`/`src/pcae/cltr/inspection.py`) — confirms the 2 Stage-0 copies still exist, untouched, as F-135R-2 anticipated (correctly out of Stage 2's scope; Stage 2 code never touches the Stage 0 namespace). All 5 Stage-1 copies plus every Stage 2 rehearsal module now import the single `disclosure.py` constant, independently confirmed by grep (§5). **Disposition: F-135P-4's in-scope five-copy drift risk is genuinely fixed; F-135R-2's disclosed two-copy Stage-0 gap remains, correctly out of scope.**
- **F-135R-3** (risk-register missing a row for the directory-rename-vs-file-rename distinction): a documentation-only compensation in 135R's own document; no code implication. **Disposition: no action required in 135S or 135T.**
- **F-135R-4** (concurrent rollback-vs-ordinary-publication race not named as its own split-brain row or test module, disclosed and deferred to Stage 2 implementation's own test-authoring): independently confirmed 135S does not implement rollback rehearsal (§33/§36) in this phase at all — `rehearsal/` has no rollback module — so this race is not yet reachable in the current implementation; it remains correctly deferred. **Disposition: still deferred, correctly so; flagged as a Stage 2 follow-on implementation item, not a 135T gap** (135T's boundary excludes broadening migration scope).

## 26. F-135P-1 through F-135P-4 dispositions (independently re-verified against source, not accepted from 135S's claim)

- **F-135P-1** (two entry points fell back to `ordinary_finalization`): independently confirmed fixed in `finalization_transaction.py`'s `_ENTRY_POINT_RECOVERY_CLASSIFICATION` (`phase_report_create` → `report_create_recovery`, `notify_send_report` → `manual_governed_recovery`). **However, this phase found the fix's own regression test (`test_cltr_migration_135p_verification.py`) still asserted the pre-fix `ordinary_finalization` fallback as expected** — see §27 below for the resulting false regression-baseline classification and its repair. **Disposition: source fix genuinely correct; the associated test was stale and has been repaired in this phase.**
- **F-135P-2** (`EXPECTED_REPRESENTATION_DIFFERENCE` half): independently confirmed wired in `comparison.py`'s `classify_candidate_field`, reachable for the three `EXPECTED_DIFFERENCE_KINDS` (notification/marker/receipt candidates). `TEMPORAL_ORDER_MISMATCH` remains correctly unreachable through Stage 2 (135Q's own disposition permits this; not required until Stage 3 contract freeze). **Disposition: resolved for the Stage-2-facing half, as required; the deferred half remains correctly deferred.**
- **F-135P-3** (`derive_cltr` would crash on non-empty commit ownership): independently confirmed fixed via `_normalize_commit_ownership` in `cltr_derivation.py`, which normalizes bare commit-hash strings into `CommitOwnershipEntry` with `certification_state=CertificationState.UNVERIFIABLE` — independently cross-checked against the Stage-0 shadow observer's own precedent (`finalization_transaction.py:932-938`) and confirmed the pattern (including the same `branch_identity="main"` hardcoding) is faithfully reused, not a new ad hoc hack. A dedicated test (135S's own `build_commit_attribution_candidate` exercise, independently re-run) confirms non-empty ownership no longer crashes. **Disposition: resolved, faithful to existing precedent.**
- **F-135P-4** (`NON_AUTHORITY_DISCLOSURE` hardcoded 5 times): independently confirmed resolved via `disclosure.py`'s shared constant, imported by all 5 original Stage 1 consumers plus every Stage 2 module (§5/§25 above). **Disposition: resolved.**

## 27. Independent regression-baseline reproduction (mandatory section)

135S's canonical report claims: affected finalization 112/117 (5 pre-existing failures), combined migration 121/129 (8 pre-existing failures), production CLTR combined 406/414 (same 8), notification/marker/receipt/report 1173/1183 (10 pre-existing failures — the 8 plus 4 four-entry-point cases plus 1 additional `test_phase_reports.py` failure), all attributed to "a sandbox-local defect in the post-dispatch receipt-modeling step of `run_finalization_transaction` (`completed_receipt_best_effort_incomplete`)," and all claimed independently confirmed via `git stash` to reproduce identically on unmodified `main`.

**This phase did not accept that classification and independently reproduced it, per this phase's mandatory method.** Node IDs were recorded on the current (135S) tree, then the exact same test commands were run against a clean, isolated `git worktree` checked out at the exact pre-135S baseline commit (`bfb943a9^` = `7fb4dbc1`), never mutating the primary repository, using the same Python (3.14.5), same pytest (9.0.3), same test commands, same environment.

**Finding: the claimed 5/8/10 pre-existing failure counts and their attributed root cause (`completed_receipt_best_effort_incomplete` receipt-modeling defect) did not reproduce.** Running the exact commands 135S's own report specifies, on the current (135S) tree, produced exactly **2** failures, not 5, 8, or 10 — and both were the same underlying assertion, in `tests/test_cltr_migration_135p_verification.py::TestFourEntryPointsThroughRealFinalizationBoundary::test_migration_evidence_recovery_classification_for_each_entry_point`, parametrized over `phase_report_create` and `notify_send_report`. The failure content (`AssertionError: 'manual_governed_recovery' == 'ordinary_finalization'`) has nothing to do with receipt modeling; it is a **stale test assertion left over from before F-135P-1's fix landed** — the test still asserted the pre-fix `ordinary_finalization` fallback as the expected/passing value (`# F-135P-1 gap` comments in the test source), which F-135P-1's own genuine repair (§26 above) made false.

**Node-by-node baseline table:**

| Node ID | Current (135S) tree | Pre-135S baseline (`7fb4dbc1`, isolated worktree) | Classification |
|---|---|---|---|
| `test_migration_evidence_recovery_classification_for_each_entry_point[task_finish]` | PASS | PASS | unaffected |
| `test_migration_evidence_recovery_classification_for_each_entry_point[phase_complete]` | PASS | PASS | unaffected |
| `test_migration_evidence_recovery_classification_for_each_entry_point[phase_report_create]` | **FAIL** (pre-repair) | PASS | **new regression, Stage-2-relevant** — caused directly by 135S's own F-135P-1 source fix landing without the corresponding test update |
| `test_migration_evidence_recovery_classification_for_each_entry_point[notify_send_report]` | **FAIL** (pre-repair) | PASS | **new regression, Stage-2-relevant** — same cause |

No other failing node ID was found in any of the four regression-suite commands 135S's own report names, on the current tree, before or after this phase's repair. The claimed `completed_receipt_best_effort_incomplete` receipt-modeling defect was independently searched for (§ below) and found to be a real, defined fallback status in `finalization_transaction.py` (lines 828–834), but **no test in any of the four named regression-suite commands currently exercises a code path that triggers it** — it is not the cause of any observed failure in this session, contradicting 135S's attribution.

**Repair applied** (bounded, within Stage 2's test-update scope, not touching CLTR-001/CLTR-SCHEMA-001 or production source beyond §14's symlink fix): `tests/test_cltr_migration_135p_verification.py`'s two stale assertions were corrected to the genuinely-fixed classifications (`report_create_recovery`, `manual_governed_recovery`), matching `finalization_transaction.py`'s actual, correct `_ENTRY_POINT_RECOVERY_CLASSIFICATION` mapping. **Post-repair, all four regression-suite commands 135S's own report names pass at 100%**, independently re-run this phase:

| Suite | 135S claimed | This phase, pre-repair | This phase, post-repair |
|---|---|---|---|
| Stage 2 focused (`test_cltr_rehearsal_coordinator.py`) | 28/28 | 28/28 | 28/28 (+ 16 new adversarial tests, §28) |
| Affected finalization regression | 112/117 (5 failing) | 117/117 | 117/117 |
| Combined migration suite | 121/129 (8 failing) | 127/129 (2 failing) | 129/129 |
| Production CLTR combined | 406/414 (8 failing) | 412/414 (2 failing) | 414/414 |
| Notification/marker/receipt/report | 1173/1183 (10 failing) | 1181/1183 (2 failing) | 1183/1183 |
| Fast Green (`-m fast_green -n auto`) | 4391/4391 | 4391/4391 | 4391/4391 |

**This is classified as a CONFIRMED, BLOCKING finding against 135S's regression-baseline claim** (a phase report asserting a false "pre-existing, unrelated" classification for a self-caused regression is exactly the kind of claim this verification phase exists to catch), **repaired in this phase** by correcting the two stale test assertions. It does not indicate any defect in the underlying F-135P-1 source fix, which was independently confirmed correct in §26; the defect was entirely in the un-updated test file.

## 28. Fresh adversarial tests (135T's own, not copied from 135S)

Added `tests/test_cltr_rehearsal_135t_independent_verification.py`, 16 tests, all independently written and passing:

- `TestSymlinkEscapeRepaired` (3 tests): live regression test for §14's finding — pre-existing-symlink abort at a candidate-artifact path; static source-proof no bare `write_text`/`write_bytes` remains in the coordinator; full end-to-end run still succeeds after the repair.
- `TestIdentityDeterminism` (8 tests): stability within one process; **stability across a fresh subprocess**; each of 6 bound fields plus `task_id`/`schema_versions` independently changes the identity.
- `TestHonestInventoryDisclosure` (2 tests): the manifest's disclosed folding of items 11–14 is actually present in a real, end-to-end-produced manifest; every one of the 10 file-backed inventory entries' artifact file actually exists on disk with a digest that independently recomputes to the manifest's recorded value.
- `TestManifestTamperDetection` (1 test): a real, on-disk, post-finalization mutation of a candidate artifact is independently detected on re-verification via freshly reloaded digests, not merely via an in-memory fixture.

All 16 pass; `python3 -m pytest tests/test_cltr_rehearsal_135t_independent_verification.py -v` → 16 passed.

## 29. Exact test execution (fresh, this phase)

All commands run fresh in this session (no cached/claimed-only results):

| Command | Result |
|---|---|
| `pytest tests/test_cltr_rehearsal_coordinator.py tests/test_cltr_rehearsal_135t_independent_verification.py -q` | 44 passed |
| `pytest tests/test_cltr_migration_*.py tests/test_cltr_135o_integration.py tests/test_cltr_rehearsal_coordinator.py tests/test_cltr_rehearsal_135t_independent_verification.py -q` | 145 passed |
| `pytest tests/test_cltr_*.py -q` | 430 passed |
| `pytest -k "test_finalization_transaction_134e10 or test_finalization_gate_enforcement or test_finalization_notification_guarantee or test_finalization_configuration_identity_cross_agent_134b3 or test_phase_113v_n_notification_finalization_repair" -q` | 117 passed |
| `pytest -k "finalization or notification or marker or receipt or phase_report or architecture_status" -q` | 1183 passed, 18810 deselected |
| `pytest -m "fast_green" -n auto -q` | 4391 passed |
| Baseline reproduction (`git worktree` at `7fb4dbc1`), `pytest tests/test_cltr_migration_*.py tests/test_cltr_135o_integration.py -q` | 101 passed, 0 failed |
| Baseline reproduction, the 4-case parametrized test in isolation | 4 passed, 0 failed |

## 30. Governance results

`pcae health`: healthy, all required files present, git clean. `pcae check`: passed. `pcae doctor task-memory`: clean. `pcae push check`: nothing to push (prior to this phase's own commit). `pcae runtime inspect`: Observed / observe / execution unavailable, registry empty, 0 plugins — unchanged. Telegram runtime: configured, enabled, outbound-only, ready. `pcae phase-report show --latest`/`reconcile --phase-id 135S`: consistent, single canonical 135S report, single promoted generation, no duplicate terminal lifecycle. No raw `git commit`/`git push` used in this phase; no `--no-verify`; no force push.

## 31. Strict no-go confirmations

- Legacy lifecycle remains the sole production authority. **Confirmed** (§6, §24).
- CLTR remains derivative. **Confirmed.**
- The Stage 2 rehearsal generation remains non-authoritative. **Confirmed** (§11).
- The Stage 2 rehearsal pointer remains non-authoritative. **Confirmed** (§15).
- No production pointer changed because of Stage 2. **Confirmed** (§15, §21).
- No external delivery originated from Stage 2. **Confirmed** (§21, §23).
- No production marker was created or modified by Stage 2. **Confirmed** (§21).
- No production receipt was created or finalized by Stage 2. **Confirmed** (§21).
- No Stage 3 implementation occurred in this phase. **Confirmed** — this phase added no rollback/cutover/authority code; the only source change is the symlink-write repair (§14) and one stale-test repair (§27).
- No authority cutover occurred. **Confirmed.**
- No legacy authority was demoted. **Confirmed.**
- No legacy authority was retired. **Confirmed.**
- No execution capability was introduced. **Confirmed** (§23).
- Runtime remains Observed, maximum capability remains observe, execution availability remains unavailable. **Confirmed** (§23, §30).

## 32. Findings table

| ID | Title | Contract source | Verdict | Repair |
|---|---|---|---|---|
| F-135T-1 | Candidate-artifact and manifest writes bypassed the pre-existing-symlink abort (`write_candidate_artifact` defined but never called) | 135Q §7/§25/§47 | **CONFIRMED, BLOCKING** | Repaired: `coordinator.py` now calls `write_candidate_artifact` for every candidate and the manifest. Regression test added (§14, §28). |
| F-135T-2 | 135S's regression-baseline claim (5/8/10 "pre-existing, receipt-modeling, sandbox" failures) did not reproduce; the actual 2 failures were a new, Stage-2-caused regression (stale F-135P-1 test assertions) misclassified as inherited | 135S's own canonical report / phase-completion-report.md | **CONFIRMED, BLOCKING** (against the phase-report's own truthfulness requirement) | Repaired: 2 stale assertions in `test_cltr_migration_135p_verification.py` corrected to the genuinely-fixed classifications. All four named regression suites now pass 100%. |
| F-135T-3 | 135Q §9's 23-item inventory is implemented as 10 file-backed items plus manifest/evidence-record-bound fields, with items 11–14 folded/deferred | 135Q §9/§18 | NON-BLOCKING, honestly disclosed | No repair required — disclosure is genuine and independently confirmed present in a real end-to-end manifest (§10, §28). |
| F-135R-4 (inherited) | Rollback-rehearsal-vs-ordinary-publication race not yet reachable since rollback rehearsal is not implemented in 135S | 135R §38/§51 | NON-BLOCKING, correctly deferred | No repair; correctly out of 135S/135T's implemented scope. |

## 33. Final verdict

**VERIFIED WITH NON-BLOCKING FINDINGS** (independent verification plus bounded repair).

Two Blocking defects were found (F-135T-1, a real symlink-escape containment gap; F-135T-2, a false regression-baseline claim masking a genuine, small, Stage-2-caused test regression) and both are repaired within the Stage 2 implementation boundary in this phase, with the repairs re-verified: the symlink-escape attack now aborts with `PathContainmentError` and leaves the outside target untouched; all four regression suites 135S's own report names now pass at 100%; Fast Green remains 4391/4391; the Stage 2 focused suite is now 44/44 (28 inherited + 16 fresh). No unresolved Blocking finding remains. Every other verification area in §6–§26 independently confirms the Stage 2 contract's authority boundary, atomicity, containment (once repaired), crash/recovery completeness, idempotency, quarantine integrity, exactly-once preservation, notification/marker/receipt isolation, and no-execution boundary hold, by direct re-derivation and live reproduction rather than by trusting 135S's own claims.

This phase performed **independent verification plus bounded repair** (135T did not begin Stage 3, did not design authority cutover, did not grant CLTR authority, did not demote or retire legacy authority, did not change production pointer semantics, and introduced no execution capability, subprocess, shell, network, or backend invocation).

## 34. Limitations

- This phase's repair of F-135T-1 and F-135T-2 is narrowly scoped to the exact defects found; it does not constitute a full line-by-line audit of every one of the ~300 sub-requirements enumerated in the original task brief. The verification areas in §6–§26 above represent the highest-value, most load-bearing properties (authority boundary, identity, containment, atomicity, crash/recovery, exactly-once, isolation, no-execution, regression truthfulness) rather than an exhaustive mechanical checklist.
- The platform-specific Windows directory-rename `PermissionError` retry path (135R's F-135R-1 disclosure) is implemented (`_RENAME_RETRY_ATTEMPTS`) but was not exercised on actual Windows filesystem semantics in this session (macOS/Linux only available).
- Rollback rehearsal (135Q §33/§36) is not implemented in 135S; F-135R-4's disclosed race is therefore correctly unreachable, not verified as safe under load — this remains a Stage 2 follow-on implementation item, not a 135T gap, since 135T's boundary excludes broadening migration scope.
- The two additional Stage-0-namespace `NON_AUTHORITY_DISCLOSURE` copies (F-135R-2) remain unresolved, correctly out of Stage 2's scope.

## 35. Recommended next phase

135S is now genuinely verified (with the two Blocking findings repaired in this phase). Verified evidence that now exists: a working, contract-conformant Stage 2 atomic-publication-rehearsal implementation with correct authority isolation, correct exactly-once identity, correct (post-repair) containment, and a truthful (post-repair) regression baseline.

This phase does not recommend immediately beginning Stage 3 authority cutover. Deriving the next phase from the remaining 135M migration plan, 135Q/135R deferrals, 135S's own disclosed limitations (items 11–14 folding, no rollback-rehearsal implementation), and this phase's findings: the most load-bearing remaining gap before any authority-cutover *readiness* discussion is (a) implementing rollback rehearsal itself (135Q §33/§36, not yet built), and (b) closing F-135R-4's now-reachable-once-built race with its own explicit test, per 135R's own disclosed deferral. A plausible next phase is **135U — Rollback Rehearsal Implementation and Independent Verification**, but this is a design judgment for the next contract/planning phase to confirm, not a scope this phase asserts as final.
