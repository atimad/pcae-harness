# Phase 145H.2 — Post-Consumption Readiness Uniqueness Implementation Repair

**Status:** Complete (implementation-only phase; no contract or
architecture revision; no runtime-capability change).
**Mode:** Governed implementation-repair phase, per this phase's own
governing prompt: implement IWPC-001 v1.4 §35's already-frozen contract
exactly, with no re-derivation of the contract text itself.
**Governing authority (consulted, this phase's own basis):** IWPC-001
v1.4 §35 (IWPC-REQ-197-209), `docs/PHASE_145H_INTERACTIVE_WORKFLOW_CHAPTER_INDEPENDENT_CERTIFICATION.md`,
`docs/PHASE_145H1_POST_CONSUMPTION_READINESS_UNIQUENESS_CONTRACT_CLARIFICATION.md`,
PROJECT_STATUS.md.
**Runtime:** Observed / observe / unavailable, confirmed unchanged before
and after this phase (`pcae runtime inspect`).
**Repair authority exercised:** Implementation only, against exactly the
engineering surface IWPC-001 v1.4 §35.12/§35.14 (IWPC-REQ-209) named as
the expected future implementation owner. No contract file was modified.

---

## 1. Root-cause confirmation

Before writing any code, this phase independently re-verified the root
cause Phase 145H first reproduced live and Phase 145H.1 independently
re-derived from primary contract text: `FilesystemPendingReadinessStore.
find_by_session_id` (`src/pcae/interactive_workflow/persistence/filesystem_pending_readiness_store.py`,
pre-repair lines 505-518) iterated only `list_package_ids()` — the
pending-only enumeration — and therefore could never return a `consumed/`
record for a session-keyed lookup. This was the sole idempotency-by-key
gate both `PublicationApplicationService.ensure_readiness_package` and
`.persist_readiness_package` relied on
(`src/pcae/interactive_workflow/application/publication_service.py`,
pre-repair lines 122-124, 158-185): once a package moved to `consumed/`,
a second `readiness` call fell through to genuine reconstruction,
minting a second `package_id`, which `governance-record publish` then
turned into a second CHGR. Confirmed unchanged from Phase 145H.1's own
description; no drift in the two phases since.

## 2. Implementation

### 2.1 `FilesystemPendingReadinessStore.find_by_session_id` (IWPC-REQ-198/199/204)

Rewritten (now at lines 505-534) to:

1. Collect every match from `list_package_ids()` (pending, unchanged
   enumeration — never includes a package already moved to `consumed/`,
   by that method's own pre-existing exclusion logic).
2. Collect every match from a new private helper, `_list_consumed_package_ids`
   (lines 575-604), which mirrors `list_package_ids`'s own enumeration
   discipline (filename-shape filtering only, no full-content load merely
   to enumerate) against the `consumed/` location.
3. If more than one record matches the given `session_id` across the two
   locations combined, raise `PendingReadinessStoreCorruptError` (maps to
   `persistence_corrupt` through the existing, unmodified error chain:
   `PendingReadinessStoreCorruptError` ->
   `ReadinessStoreCorruptApplicationError` -> `persistence_corrupt`) —
   IWPC-REQ-204's historical-inconsistency fail-closed rule. No existing
   error type, exit code, or transport shape was added; this reuses the
   pre-existing `persistence_corrupt` path unchanged.
4. Otherwise return the single match, or `None` if there is none.

No new store method was added beyond the one private enumeration helper;
`load`, `create`, `list_package_ids`, `exists`, and
`record_publication_attempt` are byte-for-byte unchanged. The atomic
create/consume mechanics, digest verification, and symlink/path-traversal
guards this method depends on (via `load`) are untouched, per IWPC-REQ-205's
confirmation that this is a lookup-scope correction only, never a
persisted-format change.

### 2.2 `PublicationApplicationService` (IWPC-REQ-197)

No behavioral change was required. `ensure_readiness_package`,
`persist_readiness_package`, and `find_readiness_package_for_session`
already delegated their idempotent-by-key check to
`FilesystemPendingReadinessStore.find_by_session_id` unconditionally —
once that method could see a `consumed/` record, the existing "return the
existing record unchanged" branch in each of the three methods correctly
started covering the consumed case for free. This independently confirms
IWPC-REQ-200's own prediction (no new transport/application-layer surface
is needed) on direct inspection of the call graph, not merely by
assertion. Docstrings on all three methods were updated to state the
lifecycle-wide guarantee explicitly, since the pre-repair text described
"pending package" only and would otherwise now read as stale/misleading.

### 2.3 `decision-session` CLI (`readiness`, `status`) (IWPC-REQ-200)

No behavioral change. Both handlers already read `disposition` and
`record_id` off the returned record and already had `"consumed"` as a
documented, reachable output value (`readiness_package_status` for
`status`; `disposition`/`record_id` for `readiness`) — the value was
simply never reached pre-repair because the store never returned a
consumed record to look at. Two stale comment blocks that described the
pre-repair limitation as permanent, disclosed behavior
(`decision_session.py`, the `status` handler's inline comment and the
`readiness` handler's module-level comment) were corrected to describe
the repaired behavior instead; no code line inside either handler
changed.

### 2.4 Files changed

- `src/pcae/interactive_workflow/persistence/filesystem_pending_readiness_store.py`
  — `find_by_session_id` rewritten; `_list_consumed_package_ids` added.
- `src/pcae/interactive_workflow/application/publication_service.py` —
  docstrings only (no executable-line change).
- `src/pcae/commands/decision_session.py` — comments only (no executable-
  line change).
- `tests/test_phase_145e_pending_readiness_store_filesystem_implementation.py`,
  `tests/test_phase_145f_application_service_boundary.py`,
  `tests/test_phase_145g_decision_session_cli.py` — new/updated tests
  (§3).
- `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DECISIONS.md`,
  `tasks/TODO.md` — governance bookkeeping.
- `docs/PHASE_145H2_POST_CONSUMPTION_READINESS_UNIQUENESS_IMPLEMENTATION_REPAIR.md`
  — this report.

No file under `docs/contracts/` was touched. No file outside the
Interactive Workflow / Publication CLI chapter was touched.

## 3. Test coverage added

### 3.1 Store level (`test_phase_145e_...py`)

- `test_consumed_package_excluded_from_list_but_still_found_by_session` —
  replaces the prior `test_consumed_package_excluded_from_list_and_find`,
  which asserted the pre-repair (buggy) behavior (`find_by_session_id`
  returning `None` after consumption); now asserts `list_package_ids()`
  stays pending-only while `find_by_session_id` reaches the consumed
  record with its `disposition`/`record_id` intact.
- `test_find_by_session_id_does_not_construct_or_mutate_consumed_record`
  — the lookup is read-only; repeated calls never change the persisted
  record or move it back to pending.
- `test_find_by_session_id_repeated_after_consumption_returns_same_identity`
  — the exact H-1 sequence's store-level core: two repeated lookups after
  consumption both return the same `package_id`.
- `test_find_by_session_id_fails_closed_on_duplicate_historical_records`
  and `..._across_pending_and_consumed` — IWPC-REQ-204: two distinct
  `package_id`s bound to one `session_id` (pending+pending, and
  pending+consumed) both raise `PendingReadinessStoreCorruptError` rather
  than silently picking one.
- `test_find_by_session_id_fails_closed_on_corrupted_consumed_record` —
  a tampered `consumed/` record's digest mismatch surfaces through the
  session-keyed lookup, not just the `package_id`-keyed `load`.

### 3.2 Application-service level (`test_phase_145f_...py`)

- `test_find_readiness_package_for_session_returns_consumed_after_publish`
  — the record returned after a real `hand_off` includes the true
  `record_id`.
- `test_persist_readiness_package_after_consumption_never_mints_second_package_id`
  — IWPC-REQ-197 invariant 5, exercised directly: presenting a second,
  freshly-built package for an already-consumed session returns the
  original identity; the second candidate `package_id` is never
  persisted (`get_readiness_package` on it raises not-found).
- `test_find_readiness_package_for_session_fails_closed_on_duplicate_historical_records`
  — IWPC-REQ-204 propagated through the application-service error
  mapping (`ReadinessStoreCorruptApplicationError`).

### 3.3 CLI level (`test_phase_145g_...py`)

- `test_status_reports_pending_readiness_then_consumed_after_publication`
  — replaces the prior test that asserted and explained away the H-1
  defect (`"none"` after consumption); now asserts `"consumed"`.
- `test_readiness_before_publication_is_idempotent` /
  `test_readiness_after_publication_repeated_reports_same_consumed_identity`
  — the two "repeated readiness requests" cases the governing prompt
  required distinguished.
- `test_original_h1_defect_no_longer_reproducible` — a direct
  CLI-transport-level reproduction of Phase 145H's own original live
  sequence (`readiness` -> `publish` -> `readiness` again -> `publish`
  again), asserting: the second `readiness` call returns the same
  `package_id`; exactly one CHGR record file exists on disk
  (`.pcae/publication-execution/records/*.json`) both before and after
  the second `readiness` call; the second `publish` is rejected as
  `publication_already_completed` referencing the original `record_id`;
  the CHGR count is still exactly one afterward.
- `test_readiness_persists_consumed_identity_across_restart` — each
  `_run` call constructs a brand-new `ApplicationContext` (fresh store/
  repository instances reading from disk), exercising restart-equivalent
  persistence without needing a real subprocess.
- `test_readiness_after_failed_publication_remains_pending` — a failed
  `publish` attempt leaves the real package's own `readiness` output
  unaffected (`disposition: "pending"`, `record_id: None`).
- `test_readiness_fails_closed_on_duplicate_historical_records` —
  IWPC-REQ-204 propagated all the way to the CLI's `error_type`
  (`persistence_corrupt`).

Interrupted-publication idempotent recovery (`resume_publication` retried
after a simulated mid-execution failure) and hand-off failure-path
readiness-state correctness were already covered, unmodified, by
`test_resume_publication_retries_after_interrupted_failure` and
`test_hand_off_maps_coordinator_exceptions` in
`tests/test_phase_145f_application_service_boundary.py` (pre-existing;
independently reconfirmed still passing and still exercising these paths
against the repaired store).

## 4. Verification

- `pcae session bootstrap --agent-id claude-local` (rehydrated the
  existing lock) confirmed healthy status and `Recommended next phase:
  145H.2` at the start of this phase.
- `pcae task transition` closed the post-145H.1 idle placeholder task and
  opened this phase's own task contract (`implementation` mode), scoped
  to exactly the files listed in §2.4.
- Targeted regression: `tests/test_phase_145e_pending_readiness_store_filesystem_implementation.py`
  (79 passed), `tests/test_phase_145f_application_service_boundary.py`
  (48 passed), `tests/test_phase_145g_decision_session_cli.py` (43
  passed) — 170 total, 0 failed, run together and individually.
- `fast_green -n auto`: 4391 passed, 0 failed — identical count to Phase
  145H.1's own last recorded baseline; this phase's new tests are not
  `fast_green`-marked, and no `fast_green`-marked test's behavior
  changed.
- Full repository suite (`-n auto`): 26,626 passed / 81 failed / 10
  skipped. Every failing test file was independently reconfirmed
  pre-existing by running it against unmodified `main` (via `git stash`)
  before attributing it: 54 of the 81 fail with `ModuleNotFoundError: No
  module named 'build'` (a missing optional packaging dependency in this
  environment, spanning `test_chgr_packaging.py`,
  `test_schema_runtime_packaging.py`, and the `test_cltr_authority_136a*`/
  `test_cltr_cutover_136*` wheel/sdist-content families); 3
  (`test_bootstrap_todo_consistency.py`) reproduce `tasks/TODO.md`'s
  already-documented 137T staleness against `PROJECT_STATUS.md`,
  unrelated to this phase's diff and unaffected by it (the "Current
  Roadmap" table this test reads is out of this phase's scope); the
  `test_scope_preflight*.py`/`test_backend_preflight_review.py`/
  `test_mutation_preflight_review.py` family and
  `test_advisory_runtime_architecture.py`/`test_rendering_134e5.py`
  reproduce identically on unmodified `main`. No failing test touches
  `interactive_workflow`, `publication_service`,
  `filesystem_pending_readiness_store`, or `decision_session.py` — the
  only overlap by name is `test_cltr_authority_136ad_request_readiness.py`/
  `test_cltr_authority_136a{h,i}_publication*.py`, an unrelated Typed
  Authority Model chapter's own "readiness package"/"publication" record
  concept (`src/pcae/cltr/authority/request_readiness.py`), independently
  confirmed to share no code path with this phase's changes and to fail
  identically on unmodified `main`.
- `pcae check`: passed. `pcae health`: healthy. `pcae doctor task-memory`:
  clean. `pcae runtime inspect`: Observed / observe / unavailable,
  unchanged before and after. Telegram sink: loaded, configured, enabled
  (unaffected — no report/notification code path touched by this phase's
  production diff).

## 5. No-Go confirmations

No architectural redesign was performed. No contract
(`docs/contracts/INTERACTIVE_WORKFLOW_PUBLICATION_CLI_TRANSPORT_CONTRACT.md`,
`INTERACTIVE_WORKFLOW_CONTRACT.md`, `PUBLICATION_EXECUTION_CONTRACT.md`,
`CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`) was modified — IWPC-001,
IWC-001, PEC-001, and CHGR-001 are all byte-for-byte unchanged from Phase
145H.1's own v1.4 state. No authority ownership changed:
`PublicationCoordinator` remains the sole authorizing/executing boundary;
`readiness` remains read/idempotent-construction only and never publishes
(IWPC-REQ-010/012, unaffected). No historical repository was migrated and
no historical duplicate record was repaired (IWPC-REQ-204 is a fail-
closed detection rule only, per its own text; no migration tooling exists
in this repository, before or after this phase). No bypass, force, or
`--assume-authorized`-style flag was introduced. No execution capability
was created; runtime remains Observed / observe / unavailable, confirmed
via `pcae runtime inspect` before and after. Identity-validation ordering
is unchanged: `require_bound_identity` still runs before every idempotent/
cache-hit branch in `ensure_readiness_package`, including the
newly-reachable consumed-package branch, since the call order inside that
method was not touched. Fail-closed behavior is preserved and extended
(a genuinely new failure mode, IWPC-REQ-204, was added exactly where the
contract requires it — a duplicate historical record now fails closed
instead of silently resolving, which the pre-repair code could not even
reach). This phase does not begin, and does not authorize, 145H.3, 145H.4,
145I, or Phase 146.

## 6. Recommended next phase

**145H.3 — Post-Consumption Readiness Uniqueness Independent
Verification.** This recommendation does not authorize 145H.3. Per this
phase's own governing prompt: stop here.
