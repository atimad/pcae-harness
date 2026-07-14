# Phase 135O — Shared Transition Input and Dual-Derivation Implementation

## 1. Implementation summary

135O implements Stage 1 ("Dual Derivation, Legacy Authority") of the
verified 135M migration contract, as repaired and confirmed by 135N. It
adds a new production package, `src/pcae/cltr/migration/`, containing:
one shared, immutable transition-input package with staged assembly
matching field availability (135M §8.4); a design-B independent
`transition_id`; a dual-derivation coordinator that runs the existing
legacy finalization path and the existing production CLTR package
against the *same* shared input, then compares them; migration-evidence
persistence in a dedicated, non-authoritative namespace; and two
read-only CLI surfaces (`pcae cltr migration status` /
`pcae cltr migration reconcile --phase-id`). It integrates through the
one shared `run_finalization_transaction()` boundary all four production
entry points (`phase_complete`, `task_finish`, `phase_report_create`,
`notify_send_report`) already funnel through, at two capture points.

Legacy lifecycle remains the sole production authority throughout. CLTR
remains derivative. Dual derivation is evidence generation, not
authority cutover. Stage 1 is disabled by default and, when enabled,
never runs unless `PCAE_CLTR_MIGRATION_STAGE=dual_derivation_legacy_authority`
and a non-empty `PCAE_CLTR_MIGRATION_EPOCH` are also set.

## 2. Stage 1 authority boundary

`pcae.cltr.migration.enums.ProductionAuthority` has two members
(`LEGACY`, `CLTR`); every `MigrationConfiguration`, `SharedTransitionInputPackage`,
and `MigrationEvidenceRecord` this phase's code can construct sets
`production_authority=LEGACY` — there is no code path, flag, or flag
combination that resolves to `CLTR`. The coordinator (`coordinator.py`)
never calls report promotion, certification, checkpoint creation,
notification dispatch, marker creation, or receipt finalization; it only
*reads* values legacy's own already-completed finalization sequence
already produced. `cltr_derivation.py` constructs a `ProductionCltrRecord`
but never calls `pcae.cltr.persistence.publish_generation` — the CLTR
derivation is migration evidence only, never a production or even a
shadow "current" generation.

## 3. Migration configuration

Two new environment variables, named per the phase brief's own suggested
naming (135M §42 left everything except `PCAE_CLTR_SHADOW_ENABLED`
unnamed — confirmed by grep during required source inspection):

- `PCAE_CLTR_DUAL_DERIVATION_ENABLED` — Stage 1 master switch. Default: unset/false.
- `PCAE_CLTR_MIGRATION_STAGE` — required when the above is true; must equal
  `dual_derivation_legacy_authority` or configuration load fails closed
  (`MigrationConfigurationError`). Any other `MigrationStage` value
  (including `shadow_observation` or a later-stage placeholder) is
  rejected, never silently downgraded.
- `PCAE_CLTR_MIGRATION_EPOCH` — required, non-empty, ASCII, no whitespace,
  when Stage 1 is enabled.

Disabled-by-default: `load_configuration()` never raises for the
disabled case even if the stage/epoch env vars are malformed — a
malformed value while disabled is recorded as inert (`effectively_active`
is `False` regardless), never fatal, since it cannot reach production.
`PCAE_CLTR_SHADOW_ENABLED` (135K) is compatible with dual derivation in
either combination; see §30.

## 4. Migration epoch

`MigrationConfiguration.migration_epoch` is read once from
`PCAE_CLTR_MIGRATION_EPOCH`, never generated, never inferred from time,
git, or titles. It is bound into every `SharedTransitionInputPackage`
(via `compute_package_id`), every `transition_id` registry key
(`transition_identity.resolve_transition_id`'s logical key), and every
`MigrationEvidenceRecord`. Evidence is persisted under
`.pcae/cltr-migration/epochs/<migration_epoch>/...`, so evidence from a
different epoch is structurally never aggregated with another epoch's
evidence (separate directory subtrees).

## 5. Authority epoch

`_authority_epoch()` (coordinator.py) computes a deterministic string
binding `production_authority` (`"legacy"`), `migration_stage`,
`migration_epoch`, and the current CLTR schema id/version
(`CLTR-SCHEMA-001`/`1.0.1`) — e.g.
`legacy|dual_derivation_legacy_authority|epoch-1|CLTR-SCHEMA-001|1.0.1`.
It is computed from configuration, never from a single boolean, and
appears on every `SharedTransitionInputPackage` and
`MigrationEvidenceRecord`. No code path transitions it to a CLTR-authority
value during Stage 1.

## 6. Transition-ID design B implementation

`pcae/cltr/migration/transition_identity.py` reproduces 135M §8.3's
resolution verbatim in its module docstring and implements it exactly:
an independently generated UUID4 `transition_id`, decoupled from
`phase_id`, with retry stability provided by a durable
per-`(phase_id, entry_point)` registry entry keyed on a logical-key
digest of `(phase_id, entry_point, migration_epoch, source_revision)` —
not the rejected design (a)'s attempt-sequence counter. An unchanged
logical key on replay returns the same `transition_id`
(`TransitionIdentity.replay=True`); a changed `source_revision` (a
genuinely new attempt) produces a new `transition_id` explicitly linked
via `predecessor_transition_id`, never an overwrite of the prior id's
own evidence. Tests: `tests/test_cltr_migration_transition_identity.py`
(11 tests) — stability, distinctness across phase/entry-point, predecessor
linkage, no-collision across five distinct attempts, UUID well-formedness,
no title/git/subprocess dependency (`monkeypatch`-enforced), missing-field
rejection, replay stability across repeated calls.

## 7. Staged input-assembly model

135O implements 135M §8.4 exactly as repaired by 135N, which itself
binds the assembler to run at **exactly two** capture points — not the
phase brief's illustrative four-way Stage A/B/C/D split, which §8.4 does
not require and which the current legacy finalization pipeline does not
expose as four independently observable points (`promote_and_dispatch()`
returns report/promotion/checkpoint/marker/receipt/notification data as
one atomic block). This mapping is a disclosed implementation decision,
documented in `pcae/cltr/migration/enums.py`'s `InputStage` docstring:

- Stage A (pre-finalization identity) → `InputStage.PRE_TRANSACTION` —
  assembled once, before either derivation path begins, at
  `finalization_transaction.run_finalization_transaction()` right after
  identity/Architecture-Status validation passes (before checkpoint
  resume lookup).
- Stage B/C/D (certified/promoted/terminal enrichment) → collapsed into
  the single `InputStage.LEGACY_COMPLETION` capture, at the same point
  `_observe_shadow_cltr` already occupies (after `promote_and_dispatch()`
  has returned).

`assembly.py` enforces this at construction time: `assemble_pre_transaction`
rejects any of `LEGACY_COMPLETION_FIELDS` if present (premature-field
rejection) and requires `PRE_TRANSACTION_FIELDS`'s mandatory subset;
`enrich_legacy_completion` rejects any field not in
`LEGACY_COMPLETION_FIELDS` and refuses to enrich a package whose latest
revision isn't still `PRE_TRANSACTION`.

## 8. Shared-input schema

`SharedTransitionInputPackage` (shared_input.py): `package_id`,
`migration_epoch`, `authority_epoch`, `phase_id`, `entry_point`,
`transition_id`, `predecessor_transition_id`, and an ordered tuple of
`SharedInputRevision`s. `package_id` is a digest of
`(migration_epoch, authority_epoch, phase_id, transition_id, entry_point,
predecessor_transition_id)` and is stable across all of a package's
revisions (`test_stable_package_identity_across_revisions`).

## 9. Revision model

`SharedInputRevision`: `package_id`, `stage` (`InputStage`), `revision`
(int, increments 1→2), `predecessor_digest` (the prior revision's own
digest, or `None` for revision 1), `fields` (deep-frozen mapping),
`provenance` (per-field `FieldProvenance`), `newly_available_fields`,
`created_reason`, `limitations`, `revision_digest`. Enrichment never
mutates a prior revision — `enrich_legacy_completion` returns a *new*
`SharedTransitionInputPackage` with an additional revision appended;
the original object and its first revision are untouched
(`test_prior_revision_untouched_after_enrichment`).

## 10. Deep immutability

`shared_input._deep_freeze` mirrors `pcae.cltr.models._deep_freeze`
exactly (dict → sorted `MappingProxyType`, list/tuple → tuple,
set/frozenset → frozenset), applied recursively to `fields` on
construction (`SharedInputRevision.__post_init__`). `SharedInputRevision`
and `SharedTransitionInputPackage` are frozen dataclasses.
`tests/test_cltr_migration_shared_input.py::TestDeepImmutability`
actively attempts nested-dict mutation (`TypeError`), nested-list
"mutation" (tuples have no `.append`, `AttributeError`), top-level
mapping mutation (`TypeError`), frozen-dataclass field reassignment, and
digest stability after a caught mutation attempt; a dedicated alias test
mutates the caller's *original* source dict after construction and
confirms the frozen copy and its digest are unaffected.

## 11. Canonicalization and digest

Reuses `pcae.cltr.digest.compute_dict_digest` /
`pcae.cltr.canonicalization.canonicalize_dict` unchanged (SHA-256 over
deterministic, sorted-key, NFC-normalized JSON) for revision digests,
package ids, transition-identity registry entries, and evidence digests
— no new digest algorithm was introduced. `SharedInputRevision.
digestible_payload()` excludes `revision_digest`/`provenance` itself from
the digested payload (self-exclusion, matching 135I §15.2-§15.4's
pattern for `record_digest`).

## 12. Field provenance

`FieldProvenance` (source_component, source_authority, observation_stage,
verification_state, source_artifact_identity, source_field, limitations)
is recorded per field, per revision, in `assembly.py`. Pre-transaction
fields declare `source_component="finalization_transaction.
run_finalization_transaction"`; legacy-completion fields declare
`source_component="finalization_transaction._observe_shadow_cltr"`. Both
declare `source_authority="legacy"` and `verification_state="explicit"`
— no field is ever marked verified without an explicit caller-supplied
value.

## 13. Validation

`assembly.SharedInputValidationError` is raised (never silently
repaired) for: missing mandatory Stage-A fields, premature
legacy-completion fields present before legacy's path has run, unknown
fields at enrichment time, double enrichment of an already-enriched
package. `configuration.MigrationConfigurationError` is raised for
missing/unsupported stage, missing/malformed epoch, and disallowed
stage/flag combinations. Neither ever "repairs" a missing value from
narrative or mutable files.

## 14. Legacy derivation

`legacy_derivation.derive_legacy` normalizes a package's already-known
fields into a `LegacyDerivationResult` (transition_id, input_revision_digest,
fields, authority_role="legacy", limitations, derivation_digest). It
performs no I/O and imports nothing from `pcae.core.phase_reports` or
`pcae.core.notifications` (`test_no_second_report_or_promotion_no_op_by_construction`
asserts this structurally). Deterministic: two calls against the same
package produce identical `derivation_digest`.

## 15. CLTR derivation

`cltr_derivation.derive_cltr` reuses the existing production CLTR
package unchanged: `ProductionCltrRecord` construction,
`validate_record` (CLTR-SCHEMA-001 v1.0.1), `evaluate_all` (all 37
invariants, `InvariantContext()`), and `run_all_adapters` (all 15
representation kinds). It never calls `publish_generation` — the record
is migration evidence only (§2 above). It consumes the *same* shared
input revision the legacy derivation consumes, deriving independently
from the shared package rather than from the legacy derivation's own
output (`derive_cltr(package)` takes the package directly, never a
`LegacyDerivationResult`).

## 16. Coordinator

`coordinator.py`'s `capture_pre_transaction` / `complete` (plus
best-effort wrappers `run_stage1_best_effort_pre_transaction` /
`run_stage1_best_effort_completion`, mirroring `shadow.py`'s naming) is
the one shared object. `complete()` runs: enrichment → persist revision →
legacy derivation → CLTR derivation → comparison → evidence → persist
evidence, each stage tracked in a `stage` variable so a failure at any
point is recorded with the exact failing stage name and never propagates
(`except Exception` at the top, containing the whole sequence). It never
calls certification, promotion, dispatch, marker/receipt, or task-state
functions — verified structurally (`test_no_notification_dispatch_module_referenced`)
and via full-cycle no-go tests (subprocess/socket patched to raise;
§37/§27 below).

## 17. Four-entry-point integration

All four entry points (`phase.py:run_phase_complete`,
`task.py:run_task_finish`, `phase_reports.py:run_phase_report_create`,
`notifications.py:run_notify_send_report`) already funnel through the
one shared `finalization_transaction.run_finalization_transaction()`,
parametrized by `entry_point`. 135O adds exactly two call sites inside
that shared function — `_capture_stage1_migration_pre_transaction` (new,
after identity validation) and `_complete_stage1_migration` (new,
alongside the existing `_observe_shadow_cltr` call) — both
entry-point-agnostic (parametrized by the caller's `entry_point` string,
no `if entry_point == ...` branch selecting different migration logic;
verified by `test_four_entry_points_share_the_same_coordinator_call_site`).
No entry-point file itself was modified.

## 18. Invocation timing

Matches 135M §8.4/§9 exactly: pre-transaction capture happens once,
before the checkpoint-resume early-return, so a resumed transaction
(content already promoted) never re-triggers Stage-1 completion — the
same idempotency property the shadow observer already has. Completion
enrichment happens once, after `promote_and_dispatch()` has returned,
alongside `_observe_shadow_cltr`. Both are best-effort and idempotent
(§24 below).

## 19. Comparison field inventory

`comparison.py` compares 20 fields where both derivations expose an
accessor (`_CLTR_FIELD_ACCESSORS`): phase/task/transition/predecessor
identity, transition_type, lifecycle_state, source/staged-final revision,
report id/digest, metadata id, phase_commit_ownership, promotion id,
checkpoint id, notification ids/state/suppressed, marker id, receipt id.
`intended_transition` and `recovery_classification` are deliberately
excluded from direct comparison — see the documented rationale in
`comparison.py`'s module docstring (they draw from genuinely distinct
vocabularies that were never meant to be byte-equal; comparing them
would manufacture a spurious `authority_relevant_mismatch`). This
exclusion is itself a disclosed limitation, not a silent gap — see §37.

## 20. Result classes and mismatch policy

`enums.ComparisonResultClass` implements all 18 classes 135M §12 names
(`exact_match` through `recovery_classification_mismatch`), with exact
wire identifiers. `COMPARISON_RESULT_PRECEDENCE` defines deterministic
precedence (identity → transition → state → digest → commit-ownership →
notification → marker → receipt → temporal-order → recovery-classification
→ generic authority-relevant → non-authority → missing → unverifiable →
representation-difference → semantic → exact); `compare()`'s overall
class is the highest-precedence class actually present. `AUTHORITY_RELEVANT_CLASSES`
gates progression eligibility (§21). At Stage 1, every mismatch is
persisted in the evidence record's `comparison_field_results`
(`field`, `result_class`, `legacy_value`, `cltr_value`, `detail`) — none
are silently dropped.

## 21. Migration evidence schema

`evidence.MigrationEvidenceRecord`: `evidence_schema_id`
(`CLTR-MIGRATION-EVIDENCE-001`), `evidence_schema_version` (`1.0.0`),
`migration_stage`, `migration_epoch`, `authority_epoch`,
`production_authority`, `package_id`, `transition_id`, `entry_point`,
`input_revision_digests`, `legacy_derivation_digest`,
`cltr_derivation_digest`, `comparison_overall_class`,
`comparison_field_results`, `recovery_classification`,
`production_completion_continued`, `migration_progression_eligible`,
`limitations`, `created_at`, `evidence_digest`. `determine_progression_eligibility`
is `False` on any authority-relevant mismatch, any unverifiable field,
migration failure, or a non-progressable recovery classification (135H.1
escape prevention). Progression eligibility is advisory evidence only —
no code path uses it to change migration stage or production behavior.

## 22. Persistence

`.pcae/cltr-migration/epochs/<epoch>/transitions/<transition_id>/{inputs,derivations,comparisons,evidence,failures}/`
plus `.pcae/cltr-migration/transition-ids/<phase_id>__<entry_point>.json`
(the design-B identity registry) and `.pcae/cltr-migration/status/current-evidence`
(an atomic status pointer). `persistence.py` mirrors `pcae.cltr.persistence`'s
containment discipline: `safe_join` resolves and containment-checks every
path segment, rejects unsafe segments (`..`, path separators, leading
dot), and refuses to follow a symlink at any component
(`test_traversal_rejected`, `test_symlink_escape_rejected`).
`write_immutable` writes only if the target is absent or byte-identical;
a genuine content conflict raises `ValueError` rather than silently
overwriting (`test_immutable_evidence_never_silently_overwritten`,
`test_conflicting_replay_raises_on_content_mismatch`). Nothing is
written under `.pcae/cltr-shadow/` or any authoritative report/checkpoint/marker/receipt
path.

## 23. Four-entry-point integration — see §17.

## 24. Idempotency

Duplicate `capture_pre_transaction` calls for the same logical key return
the same `transition_id`/`package_id` (`test_idempotent_duplicate_pre_transaction_invocation`).
Duplicate `complete()` calls for the same package and identical
completion fields produce byte-identical evidence
(`test_idempotent_duplicate_completion_invocation_no_immutable_overwrite_error`).
A duplicate `complete()` call with *different* completion fields for the
same transition is a disclosed `status="failed"`/`stage_failed=
"input_assembly"` conflict, never a silent overwrite
(`test_conflicting_replay_raises_on_content_mismatch`).

## 25. Recovery

`MigrationRecoveryClassification` (enums.py) — 12 explicit values
matching the phase brief's §26 taxonomy — is supplied by the caller
(currently, `finalization_transaction.py` maps `entry_point` to
`phase_complete_finalization` / `task_finish_finalization`, defaulting
to `ordinary_finalization` for the other two entry points; see §38
Limitations — a richer, caller-supplied recovery classification wired
through the entry points themselves is deferred). It is never inferred
from titles, latest files, or git history.

## 26. 135H.1 escape prevention

`NON_PROGRESSABLE_RECOVERY_CLASSIFICATIONS` (`REJECTED_CANDIDATE`,
`PARTIAL_CANDIDATE`, `STALE_METADATA_CONFLICT`, `UNCERTAIN_PROMOTION`,
`RECONCILIATION_ONLY`) always force `migration_progression_eligible=False`
regardless of comparison outcome (`determine_progression_eligibility`).
`test_rejected_candidate_never_gets_progression_credit` proves a
`REJECTED_CANDIDATE`-classified transition completes evidence generation
but is never progression-eligible. Migration code never calls
`write_phase_report()`, promotion, notification, marker, or receipt
functions for any classification — verified structurally (§16) and by
the full no-go suite (§37).

## 27. Status command

`pcae cltr migration status [--json]` (`commands/cltr_migration.py` →
`pcae.cltr.migration.status.migration_status`): dual_derivation_enabled,
migration_stage, production_authority (always `"legacy"`), migration_epoch,
authority_epoch, shadow_enabled, transition_evidence_count,
comparison_counts_by_class, authority_relevant_mismatch_count,
unverifiable_count, migration_progression_eligible_count, blockers,
limitations, `mutation: "none"`. Strictly read-only — aggregates
persisted evidence files, never writes.

## 28. Reconciliation command

`pcae cltr migration reconcile --phase-id <ID> [--json]`
(`reconciliation.reconcile`): scans persisted evidence for transitions
whose first revision's `phase_id` field matches, reports per-transition
`transition_id`, epochs, `production_authority`, `comparison_overall_class`,
`migration_progression_eligible`, `evidence_digest`, and failure count.
`test_reconcile_never_mutates_filesystem` hashes the entire
`.pcae/cltr-migration/` tree before and after a reconcile + status call
and asserts byte-for-byte equality.

## 29. Observability

Every migration artifact (revision, derivation result, comparison,
evidence record, failure record, status/reconciliation payload) carries
an explicit non-authority disclosure (`production_authority`,
`migration_evidence_only`/`authoritative`/`authority_cutover`/
`mutation`/`runtime_boundary` as applicable). This phase does not add a
separate structured-logging framework beyond the persisted, inspectable
evidence/failure JSON artifacts themselves, which already serve as the
durable observation record (see §38 Limitations for what a dedicated
log-line-level observability layer would add).

## 30. Shadow compatibility

`PCAE_CLTR_SHADOW_ENABLED` and `PCAE_CLTR_DUAL_DERIVATION_ENABLED` are
independent flags (`test_shadow_and_dual_derivation_can_both_be_enabled`).
Because Stage 1's CLTR derivation never publishes into
`.pcae/cltr-shadow/`'s "current" pointer (§2, §15), there is no risk of
two competing "current" shadow generations for one transition — the two
features write to disjoint namespaces (`.pcae/cltr-shadow/` vs.
`.pcae/cltr-migration/`) and can be enabled in any combination without
producing two lifecycle-completion representations racing for the same
pointer.

## 31. Progression eligibility

See §21/§26. `migration_progression_eligible` is advisory evidence,
never consulted to change migration stage, authority, or any production
behavior — no code path reads it back into a decision.

## 32. Failure policy

Every coordinator stage (`configuration`, `input_assembly`,
`legacy_derivation`, `cltr_derivation`, `comparison`, `migration_evidence`,
`persistence`) is wrapped so a failure there is recorded (failure JSON
under `.../failures/`), the exact stage name is disclosed
(`MigrationResult.stage_failed`), and production continues unaffected —
`test_migration_failure_does_not_block_production_completion` monkeypatches
the coordinator's own containment-boundary call to raise and confirms
`run_finalization_transaction()` still returns `status="completed"` with
the callback invoked exactly once.

## 33. Security and containment

Path containment (§22), no execution boundary (§37), immutable evidence
(§22/§24), and the task-scope-checked, governed-CLI-only change set (no
raw `git commit`/`push`, no `--no-verify`) together bound this phase's
blast radius to `src/pcae/cltr/migration/`, `src/pcae/commands/cltr_migration.py`,
two new call sites in `finalization_transaction.py`, one CLI subtree in
`cli.py`, and a new autouse env-isolation fixture in `tests/conftest.py`.

## 34. No-authority proof

`ProductionAuthority.LEGACY` is the only value ever set (§2, §5); no
enum comparison, flag, or code path in this package resolves to `CLTR`.
`test_no_boolean_can_grant_cltr_authority` iterates every truthy flag
value and asserts `production_authority == LEGACY` in every case.

## 35. No-execution proof

`tests/test_cltr_migration_coordinator.py::TestNoGoExecutionBoundary`
patches `subprocess.run`/`Popen`/`call` and `socket.socket` to raise
`AssertionError` and runs a full capture→complete cycle under that
patch — the cycle completes normally, proving no migration code path
ever reaches those functions. Structural checks
(`"subprocess" not in mod.__dict__`, `"socket" not in mod.__dict__`)
confirm the modules never import them at all.

## 36. Test results

- New migration-focused tests: **77 passed** across
  `tests/test_cltr_migration_config.py` (11),
  `tests/test_cltr_migration_transition_identity.py` (10),
  `tests/test_cltr_migration_shared_input.py` (16),
  `tests/test_cltr_migration_derivation.py` (12),
  `tests/test_cltr_migration_coordinator.py` (16),
  `tests/test_cltr_migration_cli.py` (7),
  `tests/test_cltr_135o_integration.py` (5) —
  run via `python -m pytest tests/test_cltr_migration_*.py tests/test_cltr_135o_integration.py -q`.
- Production CLTR regression (all existing `test_cltr_*.py` suites —
  production shadow, prototype, digest, canonicalization, validation,
  adapters, persistence, models, 135L independent verification, CLI —
  none modified by this phase): **285/285 passed**, unchanged from
  before this phase. Run together with the new migration suite as
  `python -m pytest tests/test_cltr_*.py -q` → **362/362 passed**
  (285 existing + 77 new).
- Affected finalization regression:
  `tests/test_finalization_transaction_134e10.py`,
  `tests/test_finalization_gate_enforcement.py`,
  `tests/test_finalization_notification_guarantee.py`,
  `tests/test_finalization_configuration_identity_cross_agent_134b3.py`,
  `tests/test_phase_113v_n_notification_finalization_repair.py` →
  **117/117 passed** (dual-derivation flags default off via the new
  `_isolate_cltr_migration_flags` autouse fixture, so these are unaffected
  by 135O's new call sites when the flags are unset).
- Fast Green: **4391/4391 passed**
  (`python -m pytest -m "fast_green" -n auto -ra --durations=100`).
  135O's own new test files are not in `FAST_GREEN_MODULES`
  (matching the existing convention that CLTR-focused suites are tracked
  separately, not folded into Fast Green — none of the pre-existing
  `test_cltr_*.py` files are in that set either). The 4391 count matches
  the pre-135O baseline exactly (verified via `--collect-only` before and
  after this phase's changes); the previously-reported 135N figure of
  4396/4396 reflects natural drift from intervening phases, not a
  regression introduced here.
- Full suite: **19,902 passed, 39 failed** on first run (before this
  phase's own task contract was opened) — investigated and found to be
  caused entirely by the *absence* of an active task contract scoping
  this phase's file changes (34 of the 39: `test_scope_preflight*`,
  `test_backend_preflight*`, `test_mutation_preflight*`), which passed
  once `tasks/active/20260714-1155-...-135o-....md` was opened with
  matching `--allowed-file` patterns. Re-running the same 10 affected
  files after opening the task contract: **680/685 passed**, with
  **5 inherited failures unrelated to 135O**, confirmed via `git status`/
  `git log` that none of the files these tests exercise were touched by
  this phase and that the failures predate 135O (`src/pcae/advisory` was
  added in Phase 124E; `tasks/TODO.md` was last modified 2026-07-13,
  before Phase 135J):
  - `tests/test_bootstrap_todo_consistency.py::test_real_todo_no_longer_marks_90_series_as_next`
  - `tests/test_bootstrap_todo_consistency.py::test_real_todo_current_roadmap_lists_recommended_phase_as_next`
  - `tests/test_advisory_runtime_contract.py::test_no_new_directory_added_for_advisory`
  - `tests/test_advisory_runtime_architecture.py::test_no_new_directory_added_for_advisory`
  - `tests/test_rendering_134e5.py::test_current_report_generation_remains_unchanged`

## 37. Inherited finding dispositions

135N's 3 Non-Blocking findings:

- **Predecessor-transition-identity gap** (135M §8.1 field list) —
  **resolved**: `predecessor_transition_id` is a first-class
  `PRE_TRANSACTION_FIELDS` entry (assembly.py) and a `SharedTransitionInputPackage`
  attribute, sourced from `transition_identity.TransitionIdentity.
  predecessor_transition_id`.
- **135M §35 Git-attribution wording overstatement** — **deferred**,
  unchanged; this is a 135M editorial-wording fix explicitly bundled for
  the already-scheduled 135S editorial-hygiene pass, not an implementation
  concern. 135O's own commit-attribution handling (via `report.commits`)
  does not change or depend on that wording.
- **transition_id design-B resolution act itself** — **implemented**
  exactly as resolved (§6 above); no residual action.

135L's 4 Non-Blocking findings (production shadow package, still live):

- **F-135L-1** (`InvariantContext` live-fact fields unpopulated) —
  **not touched by 135O**; `cltr_derivation.py` calls `evaluate_all(record,
  InvariantContext())` the same way `shadow.py` does. Still a natural
  135M-cleanup-adjacent candidate, now equally relevant to the migration
  path; not repaired here (out of Stage 1 scope; repairing invariant
  wiring is not a Stage-1 dual-derivation requirement).
- **F-135L-2** (`adapter_sources` never passed at the one shadow call
  site; `transition_id == phase_id` collision) — the **collision half is
  resolved by construction** for the migration path specifically:
  `cltr_derivation.py` uses the design-B `transition_id` (never
  `phase_id`), so the same-phase content-correction discard scenario
  F-135L-2 describes cannot recur *for migration evidence*. The
  `adapter_sources`-never-passed half is **unchanged**: `derive_cltr()`
  accepts `adapter_sources` but `_complete_stage1_migration()`
  (finalization_transaction.py) does not yet pass one, so 11/15
  representation adapters resolve `unverifiable` for migration-derived
  records too, same as the shadow path. Wiring real adapter sources
  through both paths remains future work (135P/135Q candidate).
- **F-135L-3** (re-promoted canonical report, `phase_reports.py`) — out
  of scope; 135O touches no report-promotion code.
- **F-135L-4** (`repository_identity`/`branch_identity` hardcoded to
  `phase_id`/`"main"`) — **still present**, and now also true of
  `cltr_derivation.py`'s constructed record (`repository_identity=
  package.phase_id, branch_identity="main"`), matching the existing
  shadow path exactly. No downstream Stage-1 conformance decision depends
  on these two fields' real-world accuracy (they are not in
  `comparison.py`'s compared-field set). Unchanged disposition: not
  repaired, no false pass/fail caused.

135J's 4 Non-Blocking findings — all 135I/135M citation- and
prose-precision notes with no implementation surface; **not applicable**
to 135O's Stage-1 implementation scope, no action taken.

Newly identified during this phase (Non-Blocking, none touching
authority/recovery/exactly-once safety):

- **N-135O-1**: `intended_transition` and `recovery_classification` are
  intentionally excluded from `comparison.py`'s cross-derivation field
  set (§19) because the two derivations draw them from genuinely
  different vocabularies. This is the correct Stage-1 behavior (comparing
  them would manufacture false authority-relevant mismatches), but it
  also means Stage 1's evidence currently offers no cross-check at all
  for recovery-classification agreement between legacy and CLTR. A
  richer, explicitly-namespaced recovery-classification crosswalk is
  deferred to a future phase.
- **N-135O-2**: `MigrationRecoveryClassification` is currently derived
  from `entry_point` alone inside `finalization_transaction.py`
  (`phase_complete`/`task_finish` map to their matching classification;
  `phase_report_create`/`notify_send_report` default to
  `ordinary_finalization`). The richer §25/§26-style classifications
  (`report_create_recovery`, `paused_task_handling`,
  `stale_metadata_conflict`, etc.) exist in the enum and are fully
  exercised by unit tests, but no production call site currently
  supplies them — the entry points themselves do not yet expose which
  specific recovery scenario is in play. Wiring real recovery
  classification through the entry points is deferred (135P/135Q
  candidate; tracked as a limitation, not a defect, since the current
  default is always the safe, non-progression-suppressing choice for
  ordinary completions and 135O's own tests directly exercise the
  escape-prevention behavior via explicit classification).
- **N-135O-3**: `adapter_sources` is not yet threaded from
  `finalization_transaction.py` into the migration coordinator (same gap
  as F-135L-2's second half, inherited). 11/15 CLTR representation
  adapters therefore resolve `unverifiable` for Stage-1 migration
  evidence today. This does not affect Stage-1's authority-relevant
  comparison set (§19), which does not depend on adapter results.

## 38. Limitations

- Recovery classification is entry-point-derived, not caller-supplied
  per actual recovery scenario (N-135O-2).
- Adapter sources are not wired through to the CLTR derivation
  (N-135O-3, inherited from F-135L-2).
- `intended_transition`/`recovery_classification` have no cross-derivation
  comparison at Stage 1 (N-135O-1).
- Structured, log-line-level observability (§29) is currently limited to
  the persisted evidence/failure JSON artifacts; a dedicated logging
  layer was not added.
- Stage A/B/C/D from the phase brief is implemented as the two capture
  points 135M §8.4 actually binds (§7); this is a disclosed fidelity
  decision, not a deviation from the contract text.

## 39. Deferred atomic publication

No atomic authoritative publication, Stage 2 rehearsal, or Stage 3
authority cutover was implemented. `MigrationStage` enum values beyond
`SHADOW_OBSERVATION`/`DUAL_DERIVATION_LEGACY_AUTHORITY` exist as
placeholders only and fail closed if selected (`configuration.py`).

## 40. Recommended next phase

**135P — Shared Transition Input and Dual-Derivation Independent
Verification.** 135P should independently re-derive and adversarially
verify this Stage 1 implementation — particularly the two-capture-point
simplification of 135M's Stage A/B/C/D framing (§7/§38), the
entry-point-derived recovery classification (N-135O-2), and the
unwired adapter sources (N-135O-3) — before any Stage 2 atomic-publication
rehearsal work begins. Do not begin Stage 2 or authority-cutover work
directly after 135O.
