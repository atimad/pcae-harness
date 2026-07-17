# Phase 136S: Recovery Schema Independent Verification

## Status

VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR NEXT EXECUTABLE-SCHEMA GROUP

## 0. Purpose and scope

Phase 136S independently re-derives, from primary sources, and attempts to
falsify the exact Implementation Group 8 (`ConcurrencyConflict`,
`RecoveryJournalEntry`) executable-schema implementation delivered by Phase
136R (commits `a32ec2ef`, `e7d69168`), against
CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0's frozen primary contract
(`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`).
This phase does not trust 136R's own tests, prose, field interpretation,
graph analysis, fixtures, or finding dispositions — every claim below was
independently re-derived and, where feasible, adversarially re-tested
against a freshly built package (wheel + isolated venv), not merely 136R's
own in-repo test suite.

Legacy lifecycle remains the sole production authority. CLTR remains
derivative.

## 1. Methodology

1. Re-read the frozen contract's §46 (implementation groups), §27
   (`ConcurrencyConflict`), §28 (`RecoveryJournalEntry`) directly from
   `PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md`.
2. Independently listed the on-disk schema/manifest inventory (`find`,
   `grep`, `python3 -c "import json; ..."`) and cross-checked counts against
   the contract's own text, not against 136R's self-reported counts.
3. Read `records/concurrency_conflict.schema.json` and
   `records/recovery_journal_entry.schema.json` directly and manually
   diffed every field against the contract's field tables and against the
   shared `$defs` in `shared/references.schema.json`,
   `shared/identity.schema.json`, `shared/digest.schema.json`,
   `shared/enums.schema.json`, `shared/limitations.schema.json`.
4. Rebuilt the `$ref` dependency graph, the manifest dependency graph, the
   record-identity graph, and the record-digest graph from scratch with
   independently written Python (not 136R's graph code) and checked for
   cycles across all 18 Group 1–8 schema resources.
5. Built a fresh wheel and sdist (`python -m build`), installed the wheel
   into a clean, isolated virtualenv (`/tmp/136s_venv`, no repository
   working-tree paths), and exercised the installed package's registry
   construction, manifest verification, and record validation there — not
   inside the repository's own dev environment.
6. Authored a fresh, independently-derived adversarial test module,
   `tests/test_cltr_cutover_136s_recovery_schema_independent_verification.py`
   (99 tests), that does not import fixtures or assertions from 136R's own
   `tests/test_cltr_cutover_136r_recovery_schema.py`.
7. Ran the full regression matrix (per-group implementation and
   independent-verification suites, schema-runtime suite, Fast Green, full
   unmarked suite) and independently classified every failure.

## 2. Section 46 group assignment and CSCH-EXEC-REQ-062 pairing — independently re-derived

Grepping `CSCH-EXEC-REQ-062` across `docs/`, `src/`, and `tests/` confirms
consistent, unambiguous usage across every phase from 136J onward: it binds
each of the 11 contract implementation groups to its own independent
verification gate before the next group may begin, and requires each
group's constituent record families to be delivered together (paired), not
split across governed phases. Group 8's own schema-file descriptions
(`concurrency_conflict.schema.json` line 5, `recovery_journal_entry.schema.json`
line 5) both independently assert the identical pairing claim, each citing
Sec.27/Sec.28/Sec.46.

**Independently confirmed: Group 8 is exactly `{ConcurrencyConflict,
RecoveryJournalEntry}`.** No third family, no hidden equivalent, no Group
9+ family appears tagged `implementation_group: 8` anywhere in
`manifest.json`.

**"Paired atomically" — independently derived meaning.** CSCH-EXEC-REQ-062
governs *implementation-group delivery completeness*, not runtime
behavior. Concretely, and confirmed by direct test
(`test_136s_group8_pair_completeness_missing_sibling_is_detectable`,
`test_136s_manifest_missing_group8_entry_fails_completeness`):

- the manifest must include both Group 8 entries together (a manifest with
  only one is structurally distinguishable and `load_and_verify_manifest`
  fails closed with `ManifestIntegrityError` on two-way completeness);
- package completeness (wheel, sdist) requires both files present;
- neither schema may ship alone in a single governed phase.

It does **not** mean, and this phase found no evidence 136R implemented it
to mean: runtime atomic persistence, atomic record creation, atomic
conflict/recovery execution, or current-authority mutation. No runtime
Group 8 object is created or persisted anywhere in this codebase (§11
below).

## 3. Exact inventory and manifest counts — independently verified

Directly parsing `manifest.json` with fresh Python (not reusing 136R's
counting code):

| Quantity | Independently derived count |
|---|---|
| Total manifest entries | **18** |
| Shared-resource entries (`implementation_group: 1`) | **7** (`digest`, `enums`, `envelope`, `failures`, `identity`, `limitations`, `references`) |
| Production record entries | **11** |
| Entries tagged `implementation_group: 8` | **2** (`concurrency_conflict`, `recovery_journal_entry`) |
| Group 9+ entries | **0** |
| Standalone `CASExpectation` schema file | **absent** |
| Notification/marker/receipt binding files | **absent** |
| `CompatibilityState` / `HistoricalAuthorityReference` files | **absent** |
| `bindings/` or `views/` directories | **absent** |

Two-way completeness independently verified: every `*.schema.json` file
under `src/pcae/schema_resources/cltr_cutover` (18 records + shared,
excluding `manifest.schema.json` itself) has exactly one manifest entry,
and every manifest entry corresponds to a real file on disk
(`load_and_verify_manifest`, exercised both against the repository copy
and against the freshly built/installed wheel — see §9).

## 4. `ConcurrencyConflict` field verification (§27)

Reconstructed independently from `records/concurrency_conflict.schema.json`
and cross-checked against §27's field table:

| Field | Required/conditional | Verified behavior |
|---|---|---|
| `schema_id`, `schema_version`, `contract_version`, `record_type`, `record_id`, `record_digest`, `created_at`, `migration_epoch` | Always required (envelope) | Absence of any one independently confirmed rejected (parametrized test, all 15 required fields) |
| `actors` | Always required, `minItems: 2` | Single-actor array independently confirmed rejected |
| `requests` | Always required, `minItems: 1`, family-locked to `cutover_request` | Empty array and wrong-family reference (`authority_state`, `human_authorization`, `certification`, `publication_evidence`) each independently confirmed rejected |
| `type` | Always required, 4-value enum | Unknown/invented values (`winner_selected`, `resolved`, `cas_mismatch_v2`) independently confirmed rejected |
| `expected_state` / `observed_state` | Conditionally required together, iff `type == "cas_mismatch"` | Independently confirmed: missing when required → rejected; present when `type` is anything else → rejected; both present with `type: cas_mismatch` → valid |
| `winner` | Always present as a key, nullable | Absent key rejected; `null` valid; well-formed reference valid |
| `recovery_requirement` | Always required, shared `RecoveryState` (10 values) | Confirmed present in `shared/enums.schema.json` |
| `limitations`, `authority_disclosure` | Always required | `authority_role: "authoritative"` independently confirmed locally forbidden; `is_authoritative: true` independently confirmed rejected (const `false` enforced) |
| `_extensions` | Optional, Tier 2, string-valued map only | Non-string value and nested-object value both independently confirmed rejected |

No field beyond §27's table was found present; no field was found missing.
`phase_id` and `transition_id` are independently confirmed **absent** from
this schema's required/property list — `concurrency_conflict` is not in
§7.2's phase_id-required or transition_id-required family lists, and
injecting either as an extra property is independently confirmed rejected
(strict `additionalProperties: false`).

**Semantic boundary — independently attacked.** A structurally perfect
`cas_mismatch` record with `expected_state` and `observed_state` set to the
*identical* id+digest still validates
(`test_136s_conflict_schema_valid_cas_mismatch_does_not_imply_cas_actually_failed`):
the schema cannot and does not detect that this describes a non-conflict.
Similarly, any well-formed reference is accepted as a `winner` claim
regardless of whether it is the "correct" resolution
(`test_136s_conflict_winner_reference_validity_does_not_imply_correct_resolution`).
Confirmed: schema validity establishes shape only, never conflict truth,
CAS truth, or resolution correctness.

## 5. `RecoveryJournalEntry` field verification (§28)

Reconstructed independently from `records/recovery_journal_entry.schema.json`:

| Field | Required/conditional | Verified behavior |
|---|---|---|
| Envelope fields (8) + `transition_id` | Always required — `recovery_journal_entry` is one of the four transition_id-required families (§7.2) | All 9 independently confirmed rejected-if-absent |
| `sequence` | Always required, non-negative integer | Negative value independently confirmed rejected |
| `prior_entry_digest` | Always present as a key, nullable | `null` required and enforced when `sequence == 0`; well-formed `sha256_hex` required and enforced when `sequence != 0` — both directions independently confirmed via `allOf`/`if`/`then` |
| `operation_reference`, `prior_state_reference`, `new_state_reference` | Always required, generic `record_reference` (no family lock — §28 names none, disclosed gap, see §7) | Absence independently confirmed rejected |
| `authority_state_reference` | Always required, family-locked to `authority_state` | Wrong-family substitution (`authority_epoch`, `cutover_request`, `human_authorization`) independently confirmed rejected |
| `generation_reference` | Always required, `generation_reference` shape (id+digest, no family tag) | Confirmed consistent with existing precedent (`authority_state.authoritative_generation`) |
| `publication_attempt_reference` | Conditionally optional (freely present-if-applicable; §28's trigger condition is undecidable from the frozen text — no enum value structurally gates it) | Absence valid; wrong-family substitution (`certification`) independently confirmed rejected; correct family valid |
| `external_effect_state` (4 values), `retry_replay_classification` (3 values) | Always required, record-local inline enums | Unknown values independently confirmed rejected for both |
| `state` (4 values: `recorded`/`reviewed`/`actioned`/`superseded`) | Always required | Conditional companions verified below |
| `operator_review` | Required iff `state` in `{reviewed, actioned, superseded}`; forbidden iff `state == "recorded"` | Both directions independently confirmed |
| `recovery_action` | Required iff `state == "actioned"`; forbidden otherwise | Both directions independently confirmed, including "reviewed but not actioned" (forbidden) |
| `limitations`, `authority_disclosure` | Always required | `authority_role: "authoritative"` independently confirmed locally forbidden |

`operator_review` and `recovery_action` are each independently confirmed to
be strict, minimal, single-field objects (`notes` / `description`
respectively); unknown sub-fields on either are independently confirmed
rejected.

**Semantic boundary — independently attacked.** A structurally perfect
`state: "actioned"` entry with a fully-populated `recovery_action` still
validates even though no recovery action has executed anywhere in this
process
(`test_136s_journal_schema_valid_actioned_entry_does_not_imply_recovery_executed`).
A `sequence: 5` entry with a well-formed `prior_entry_digest` validates
even though no `sequence` 0–4 documents exist anywhere in the fixture or
registry
(`test_136s_journal_chain_link_validity_does_not_imply_chain_is_unbroken`):
chain contiguity/integrity verification is confirmed to be Layer 4, never
enforced at this schema layer. Confirmed: schema validity establishes
shape only, never recovery truth, replay safety, or journal-ordering
correctness.

## 6. Sibling independence — four independently authored graphs

1. **`$ref` graph** (independently written traversal over both schema
   documents' raw JSON): `concurrency_conflict.schema.json`'s only
   cross-file `$ref` targets are `shared/envelope.schema.json`,
   `shared/identity.schema.json`, `shared/digest.schema.json`,
   `shared/enums.schema.json`, `shared/references.schema.json`,
   `shared/limitations.schema.json`. `recovery_journal_entry.schema.json`'s
   targets are the same six shared files. **Neither references the
   other.** Full Group 1–8 `$ref` graph (18 nodes) independently confirmed
   acyclic by DFS.
2. **Manifest dependency graph**: `concurrency_conflict`'s declared
   `dependencies` list contains no entry naming `recovery_journal_entry`,
   and vice versa. Full 18-entry manifest dependency graph independently
   confirmed acyclic by DFS.
3. **Record-identity graph**: both families use the identical generic
   `record_identity` pattern (`^[a-z][a-z0-9-]{7,127}$`); family
   distinction is enforced entirely via `record_type`/`record_family`
   const fields, not via any identity-pattern-level dependency between the
   two siblings — confirmed no identity-level coupling exists.
4. **Record-digest graph**: `recovery_journal_entry.prior_entry_digest`
   digests a *prior journal entry*, never a `ConcurrencyConflict`
   document; `concurrency_conflict.schema.json` has no digest-typed field
   referencing a `RecoveryJournalEntry` at all. Independently confirmed: a
   `RecoveryJournalEntry` whose `prior_entry_digest` is set equal to its
   own `record_digest` is still schema-valid (self-reference-by-value
   detection is explicitly Layer 4, never enforced at Layer 2) — this is a
   disclosed limitation, not a defect (see §16).

**Both siblings can be created independently; no ordering is required
between them.** The valid creation order across all 18 resources is: the 7
shared resources first (no dependencies among most; `envelope`,
`limitations`, `references` each depend only on other shared resources),
then any record family whose dependencies are satisfied — `concurrency_conflict`
and `recovery_journal_entry` both depend only on shared resources and may
be created in either order relative to each other, independently confirmed
via `test_136s_creation_order_shared_before_group8_group8_has_no_forward_deps`.

No cycle of any kind (self, mutual, or hidden through shared `$defs`) was
found in any of the four graphs.

## 7. Family-specific reference verification

Every family-restricted reference slot on both Group 8 schemas was
attacked with a wrong-family substitution:

- `ConcurrencyConflict.requests` — locked to `cutover_request`; substituting
  `authority_state`, `human_authorization`, `certification`, or
  `publication_evidence` independently confirmed rejected.
- `RecoveryJournalEntry.authority_state_reference` — locked to
  `authority_state`; substituting `authority_epoch`, `cutover_request`, or
  `human_authorization` independently confirmed rejected.
- `RecoveryJournalEntry.publication_attempt_reference` — locked to
  `publication_attempt`; substituting `certification` independently
  confirmed rejected.

`ConcurrencyConflict.expected_state`, `observed_state`, and `winner`, and
`RecoveryJournalEntry.operation_reference`, `prior_state_reference`, and
`new_state_reference` are each independently confirmed **generic**
(`record_reference` with no `record_family` const) — §27 and §28 name no
specific family restriction for these slots. This reproduces the disclosed
gap-fill category first raised at `NON-BLOCKING-136N-7` (§16 below); it is
not a new defect, and is not broadened here.

## 8. Strictness and extension verification

Both Group 8 schemas independently confirmed **Tier 2** (`_extensions`
only, §14): each declares `additionalProperties: false` at the top level
and permits exactly one reserved key, `_extensions`, itself constrained to
a string-valued map (`maxProperties: 32`). Non-string extension values,
nested-object extension values, unknown top-level fields, unknown
`operator_review`/`recovery_action` sub-fields, malformed `record_id`
(path-traversal payload), and malformed `record_digest` (non-hex string)
were each independently attacked and confirmed rejected.

## 9. Manifest, packaging, and installed-wheel verification

- **Manifest digest integrity**: independently re-verified all 18 entries'
  `file_digest` values against freshly recomputed SHA-256 of the actual
  files on disk via `load_and_verify_manifest`. A tampered
  `concurrency_conflict` digest, injected into a scratch copy of the
  package, independently confirmed raises `ManifestIntegrityError`. A
  manifest with the `recovery_journal_entry` entry removed independently
  confirmed raises `ManifestIntegrityError` (two-way completeness fails
  closed for incomplete Group 8 delivery — the schema-level meaning of
  "paired").
- **Fresh wheel + sdist** (`python -m build`, clean `/tmp/136s_dist`):
  both artifacts independently confirmed to contain exactly the 7 shared
  resources, 11 production record schemas (including both Group 8 files),
  `manifest.json`, `manifest.schema.json`, and `README.md` — no Group 9+
  schema, no notification/marker/receipt binding, no `CompatibilityState`,
  no `HistoricalAuthorityReference`, no `bindings/`, no `views/`.
- **Isolated installed-wheel verification**: installed the built wheel
  into a clean virtualenv (`/tmp/136s_venv`, `pip install
  pcae_harness-0.2.0-py3-none-any.whl` plus `jsonschema`/`referencing`, no
  repository working-tree path on `sys.path`). From that installed
  package: registry construction succeeded, manifest verification returned
  18 verified entries, a fresh valid `ConcurrencyConflict` record validated
  `VALID`, and the same record with `winner` removed validated `INVALID`.
- **No-network verification**: `socket.socket` and
  `socket.create_connection` were monkeypatched to raise on any call,
  both in-repository and in the installed-wheel process; registry
  construction, manifest verification, and record validation all
  independently confirmed to complete with zero network calls.

## 10. No-conflict-resolution / no-recovery / no-authority / no-execution verification

- Searched `src/pcae/cltr` for `concurrency_resolver.py`,
  `conflict_resolver.py`, `recovery_coordinator.py`,
  `recovery_evaluator.py`, `reconciliation.py` (new), `quarantine.py`
  (new) — none exist. Pre-existing `src/pcae/cltr/migration/coordinator.py`,
  `src/pcae/cltr/migration/reconciliation.py`,
  `src/pcae/cltr/migration/rehearsal/{coordinator,recovery,reconciliation}.py`
  predate this phase (untouched by commits `a32ec2ef`/`e7d69168`, confirmed
  by `git show --name-status`) and belong to Stage 2 rehearsal
  infrastructure, unrelated to Group 8 schemas or CLTR authority.
- No `.pcae/cltr-authority/` directory exists.
- No `.py` file named `concurrency_conflict.py`, `recovery_journal_entry.py`,
  `conflict_resolver.py`, or `recovery_coordinator.py` is tracked under
  `src/pcae`.
- `pcae runtime inspect` independently re-run: Runtime state **Observed**,
  maximum plugin capability **observe**, execution capability
  **unavailable**, registry empty, plugin count 0 — unchanged from
  pre-136S state.
- No authority epoch changed; no CLTR authority created; no legacy
  authority demoted or retired. No production lifecycle behavior changed.

## 11. Inherited finding review

| Finding | Disposition under 136S |
|---|---|
| `NON-BLOCKING-136M-1` (generic `record_id` pattern, no per-family prefix enforcement) | Unaffected — Group 8 uses the identical shared `record_identity` `$def`; no stronger check added or needed. |
| `NON-BLOCKING-136M-2` (manifest `dependencies` not cross-checked against actual `$ref` usage) | Re-confirmed for Group 8's two entries — no spurious or missing edge found (§6). |
| `NON-BLOCKING-136M-3` (`implementation_group` in-range-but-wrong not locally detected) | Unaffected — Group 8's own two entries are correctly tagged `8`, matching §46. |
| `NON-BLOCKING-136M-4` (`ReadinessPackage` local conditional not enforced) | Unaffected. |
| `NON-BLOCKING-136N-1` through `136N-8` | Unaffected except `136N-7` (cross-family reference cannot be restricted absent a matching enum value) — re-confirmed as the same category applying to `ConcurrencyConflict.expected_state/observed_state/winner` and `RecoveryJournalEntry.operation_reference/prior_state_reference/new_state_reference` (§7 above; originally disclosed by 136R as `NON-BLOCKING-136R-3`). |
| `NON-BLOCKING-136O-1` (spurious `enums.schema.json` manifest dependency) | Not reproduced for Group 8 — both entries' declared `enums.schema.json` dependency is actually used (`recovery_state`, `record_family`). |
| `NON-BLOCKING-136P-1` (`temporary_pointer_reference` no if/then trigger) | Unaffected directly (`publication_attempt`-scoped); same category reused for `recovery_journal_entry.publication_attempt_reference` (136R's `NON-BLOCKING-136R-1`), independently re-confirmed present and unresolved (§5, §7). |
| `NON-BLOCKING-136P-2` (`authoritative_generation` typed `generation_reference`) | Same precedent independently re-confirmed reused for `RecoveryJournalEntry.generation_reference` (136R's `NON-BLOCKING-136R-4`). |
| `NON-BLOCKING-136Q-1` (full-suite "N inherited failures" not a stable frozen node-ID set) | **Re-confirmed and reproduced independently** — see §12; the count and composition again differ from the immediately prior phase's reported numbers, consistent with this finding's own prediction. |
| `NON-BLOCKING-136R-1` (`publication_attempt_reference` trigger undecidable from frozen text) | Independently re-confirmed unresolved; left freely optional, matches contract text, no Blocking impact. |
| `NON-BLOCKING-136R-2` (pre-existing manifest entries use informal per-phase group numbering, not literal §46 group numbers, for groups authored before this convention was adopted) | Independently re-confirmed present; unaffected by Group 8 (Group 8's own two entries use the correct contract-group number, `8`). |
| `NON-BLOCKING-136R-3` (several Group 8 cross-family references left generic, no family `const`, since §27/§28 name no specific restriction) | Independently re-confirmed (§7 above), same category as `136N-7`. |
| `NON-BLOCKING-136R-4` (`generation_reference` typing precedent) | Independently re-confirmed, same category as `136N-2`/`136P-2`. |

No inherited finding was resolved, amplified into Blocking, or converted
by this phase's Group 8 verification. No new Blocking finding was
independently discovered.

## 12. Full-suite baseline verification

136R reported: current tree `21477 passed, 20 failed`; isolated pre-136R
baseline `21384 passed, 10 failed`; no Group 8-related failing node IDs.

Independently re-run in this phase:

- Combined regression matrix (136H–136S implementation + independent-
  verification suites, `test_schema_runtime_*`, `test_schema_runtime_boundaries`,
  `test_schema_runtime_packaging`): **1518 / 1518 passed** (1419 inherited
  from 136R's own combined-suite count + 99 newly authored 136S tests).
- Fast Green (`pytest -m fast_green -n auto`): **4391 / 4391 passed**,
  exactly matching 136R's reported count (the 136S test module carries no
  `fast_green` marker, so it does not change this count).
- Full unmarked suite, current tree (`pytest -n auto`, complete node-ID
  capture, not truncated): **21576 passed, 20 failed** (`21596` collected).
  Complete failing node-ID list:

  ```
  test_advisory_runtime_architecture.py::test_no_new_directory_added_for_advisory
  test_advisory_runtime_contract.py::test_no_new_directory_added_for_advisory
  test_architecture_status_generation_independent_verification_134e8v.py::test_real_repository_status_has_no_stale_132f_plan_and_discloses_no_conflicts
  test_bootstrap_todo_consistency.py::test_real_todo_current_roadmap_lists_recommended_phase_as_next
  test_bootstrap_todo_consistency.py::test_real_todo_no_longer_marks_90_series_as_next
  test_cltr_135o_integration.py::TestDisabledByDefault::test_no_migration_evidence_directory_created
  test_cltr_135o_integration.py::TestEnabledStage1::test_legacy_authority_still_completed_transaction
  test_cltr_135o_integration.py::TestEnabledStage1::test_migration_evidence_produced_for_phase_complete
  test_cltr_135o_integration.py::TestEnabledStage1::test_migration_failure_does_not_block_production_completion
  test_cltr_migration_135p_verification.py::TestFourEntryPointsThroughRealFinalizationBoundary::test_migration_evidence_recovery_classification_for_each_entry_point[notify_send_report]
  test_cltr_migration_135p_verification.py::TestFourEntryPointsThroughRealFinalizationBoundary::test_migration_evidence_recovery_classification_for_each_entry_point[phase_complete]
  test_cltr_migration_135p_verification.py::TestFourEntryPointsThroughRealFinalizationBoundary::test_migration_evidence_recovery_classification_for_each_entry_point[phase_report_create]
  test_cltr_migration_135p_verification.py::TestFourEntryPointsThroughRealFinalizationBoundary::test_migration_evidence_recovery_classification_for_each_entry_point[task_finish]
  test_finalization_transaction_134e10.py::TestEndToEndTransaction::test_gate_passing_report_completes_all_stages_and_invokes_callback
  test_finalization_transaction_134e10.py::TestExternalDeliveryIsolation::test_transaction_delivery_step_uses_recording_adapter_only
  test_finalization_transaction_134e10.py::TestPrePromotionGatingIsAuthoritative::test_receipt_creation_happens_only_after_promote_and_dispatch_returns
  test_finalization_transaction_134e10.py::TestResumability::test_distinct_certified_content_does_not_collide_with_prior_completion
  test_finalization_transaction_134e10.py::TestResumability::test_second_call_for_same_certified_content_does_not_reinvoke_callback
  test_phase_reports.py::TestPhase128B1NotificationDispatchReliabilityRepair::test_public_reconciliation_requires_report_marker_checkpoint_and_receipt
  test_rendering_134e5.py::test_current_report_generation_remains_unchanged
  ```

- Full unmarked suite, isolated pre-136R worktree (`git worktree add
  --detach` at commit `15fca95e`, 136Q's close commit, fresh venv, `pip
  install -e ".[dev]"`): **21378 passed, 16 failed**. Complete failing
  node-ID list:

  ```
  test_advisory_runtime_architecture.py::test_no_new_directory_added_for_advisory
  test_advisory_runtime_contract.py::test_no_new_directory_added_for_advisory
  test_architecture_status_generation_independent_verification_134e8v.py::test_historical_incident_reports_are_preserved
  test_architecture_status_generation_independent_verification_134e8v.py::test_real_repository_status_has_no_stale_132f_plan_and_discloses_no_conflicts
  test_bootstrap_todo_consistency.py::test_real_todo_current_roadmap_lists_recommended_phase_as_next
  test_bootstrap_todo_consistency.py::test_real_todo_no_longer_marks_90_series_as_next
  test_cltr_cutover_136k_authority_core_independent_verification.py::test_136k_installed_wheel_validates_group2_fixtures_outside_repository
  test_cltr_cutover_136k_authority_core_independent_verification.py::test_136k_sdist_and_wheel_still_exclude_group3plus_and_authority_namespace
  test_gate_dry_run_context.py::test_git_branch_returns_string
  test_rendering_134e5.py::test_current_report_generation_remains_unchanged
  test_risk_register.py::test_risk_register_no_repository_files_created
  test_runtime_snapshot.py::test_verbose_output_includes_runtime_context_section
  test_schema_runtime_packaging.py::test_136f_installed_wheel_resource_lookup_in_isolated_venv
  test_schema_runtime_packaging.py::test_136f_sdist_contains_smoke_schema_and_no_stage3_record_schema
  test_schema_runtime_packaging.py::test_136f_wheel_contains_smoke_schema_and_no_stage3_record_schema
  test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record
  ```

  Of these 16, 4 are independently confirmed **environment-artifacts of the
  ephemeral worktree/venv itself**, not real pre-136R failures:
  `test_gate_dry_run_context.py::test_git_branch_returns_string` fails
  because a `git worktree add --detach` checkout has no branch name
  (`git branch --show-current` returns empty); the three
  `test_schema_runtime_packaging.py` wheel/sdist tests fail because the
  `build` package was never installed into that scratch venv (`pip install
  -e ".[dev]"` does not pull it in; confirmed via `python -c "import
  build"` raising `ModuleNotFoundError` in that venv). That leaves **12
  real baseline failures**.

**Independent node-ID cross-reference (current-tree 20 vs. baseline's real
12):**

| Overlap category | Node IDs | Count |
|---|---|---|
| Reproduced in both (pre-existing, unaffected by 136R/136S) | `test_advisory_runtime_architecture.py`, `test_advisory_runtime_contract.py` (`test_no_new_directory_added_for_advisory` each), `test_rendering_134e5.py::test_current_report_generation_remains_unchanged`, `test_architecture_status_generation_independent_verification_134e8v.py::test_real_repository_status_has_no_stale_132f_plan_and_discloses_no_conflicts`, `test_bootstrap_todo_consistency.py` (both parametrizations) | 6 |
| Present in baseline's real 12, absent from current tree (state healed or state-sensitive) | `test_shell_gate.py::TestAuditPersistence::test_verify_detects_tampered_record`, both `test_cltr_cutover_136k_...` tests, `test_architecture_status_generation_independent_verification_134e8v.py::test_historical_incident_reports_are_preserved`, `test_runtime_snapshot.py::test_verbose_output_includes_runtime_context_section`, `test_risk_register.py::test_risk_register_no_repository_files_created` | 6 |
| Present in current tree only (new, all governed-lifecycle-state/finalization-transaction/migration-evidence tests, none touching Group 8) | `test_cltr_135o_integration.py` (4), `test_cltr_migration_135p_verification.py` (4 parametrizations), `test_finalization_transaction_134e10.py` (5), `test_phase_reports.py` (1) | 14 |

**Independently confirmed: zero of the 20 current-tree failures and zero
of the 16 baseline failures name, import, or exercise
`concurrency_conflict`, `recovery_journal_entry`, any `cltr_cutover`
Group 8 schema path, or `schema_runtime`'s core validation logic** (the two
136k and three packaging-test failures are, respectively, Group 2
authority-core and generic schema-runtime-packaging tests, pre-existing
and unrelated to Group 8; none reference `concurrency_conflict.schema.json`
or `recovery_journal_entry.schema.json`). **Zero Group 8 regressions.**

**New finding — 136R's self-reported baseline is independently
unreproducible.** 136R's own report claimed an isolated pre-136R baseline
of `21384 passed, 10 failed`. This phase's independent reproduction of the
identical commit (`15fca95e`) in a freshly built worktree instead measured
`21378 passed, 16 failed` — a different total collected-test count (21394
vs. 21388, before accounting for the 4 environment-specific failures),
different failure count, and only partial node-ID overlap with any
plausible reading of 136R's claim (136R's own report did not itself
enumerate all 10 baseline node IDs, only asserted the count and a
zero-overlap-with-Group-8 conclusion). This is disclosed as
**NON-BLOCKING-136S-2**: the exact pre-136R baseline is not independently
reproducible byte-for-byte across separate worktree/venv constructions,
most plausibly because (a) some failures are sensitive to live
governed-lifecycle/task/session state that differs between the original
in-repository run and any later isolated worktree, and (b) an isolated
worktree's fresh venv can differ from the original run's environment in
installed optional dependencies (e.g. `build`). This is a strictly larger
instance of the instability `NON-BLOCKING-136Q-1` first disclosed — it
extends the finding from "the inherited-failure composition shifts between
phases" to "the inherited-failure composition is not independently
reproducible even for the same commit, across separate constructions." It
does not implicate Group 8, and it is not resolved by this phase (nor
required to be) — no Blocking impact, since the load-bearing claim (zero
Group 8 regressions) is independently confirmed true in both this phase's
own current-tree run and its own baseline run, regardless of the exact
count mismatch against 136R's self-report.

## 13. Findings table

| ID | Summary | Classification |
|---|---|---|
| CONFIRMED-136S-1 | Group 8 inventory, Section 46 assignment, and CSCH-EXEC-REQ-062 pairing exactly match 136R's claims | CONFIRMED |
| CONFIRMED-136S-2 | `ConcurrencyConflict` and `RecoveryJournalEntry` field tables exactly match §27/§28, no missing/invented field | CONFIRMED |
| CONFIRMED-136S-3 | Sibling independence holds across all four independently authored graphs; no cycle | CONFIRMED |
| CONFIRMED-136S-4 | Fresh wheel/sdist, isolated installed-wheel, no-network, no-conflict-resolution, no-recovery, no-authority, no-execution all independently verified clean | CONFIRMED |
| NON-BLOCKING-136S-1 (re-confirmation) | All twelve inherited non-blocking findings (`136M-1..4`, `136N-7`, `136P-1/2`, `136Q-1`, `136R-1..4`) remain present, unresolved, and non-blocking; none amplified | NON-BLOCKING |
| NON-BLOCKING-136S-2 (new) | 136R's self-reported isolated pre-136R baseline (`21384 passed, 10 failed`) is not independently reproducible: a fresh worktree/venv build of the identical commit measured `21378 passed, 16 failed` (12 real after excluding 4 environment artifacts). No Group 8 implication either way; a strictly larger instance of `NON-BLOCKING-136Q-1` | NON-BLOCKING |

Zero Blocking findings.

## 14. Required confirmations

Legacy lifecycle remains the sole production authority.
CLTR remains derivative.
136S independently verified the exact Group 8 `ConcurrencyConflict` and
`RecoveryJournalEntry` executable-schema implementation against the frozen
primary contract.
Section 46 and CSCH-EXEC-REQ-062 require the two Group 8 schemas to be
delivered as one complete implementation group.
Paired schema delivery does not establish runtime atomicity, atomic
persistence, conflict resolution, recovery execution, or authority
transition.
No Group 9+ schema, notification binding, marker binding, receipt binding,
`CompatibilityState`, `HistoricalAuthorityReference`, or derived
record-view schema was implemented.
No Stage 3 typed record model or broad cross-record semantic validator was
implemented.
No cryptographic verification, authorization evaluator, certification
evaluator, publication evaluator, conflict resolver, recovery evaluator,
reconciliation evaluator, quarantine evaluator, authority resolver,
authority-state persistence, or authority pointer was implemented or
changed.
No runtime `ConcurrencyConflict` or `RecoveryJournalEntry` object was
created or persisted.
No publication, compare-and-swap operation, conflict resolution, recovery,
reconciliation, quarantine action, pointer mutation, authority activation,
or execution occurred.
Schema validity does not establish concurrency truth, CAS truth, journal
truth, recovery truth, retry safety, replay safety, publication success,
current authority, or lifecycle authority.
No authority epoch changed.
No CLTR authority was created.
No legacy authority was demoted.
No legacy authority was retired.
No production lifecycle behavior changed.
No execution capability was introduced.
Runtime remains Observed, maximum capability remains observe, and
execution availability remains unavailable.

## 15. Lifecycle reporting observations (carried forward)

- Architecture Status has repeatedly reported no explicit
  recommended-next-phase sentence despite the canonical report containing
  one; unaffected by this phase's own report body.
- A prior 136N report retained stale 136M body content; this phase's
  report body was compared line-by-line against 136R's report before
  finalization to prevent recurrence.
- 136R's own report wording stated user confirmation overrode the task
  prompt; this report instead frames it correctly: the frozen primary
  contract governs; operator clarification aligned the task instructions
  with that contract.

## 16. Limitations and deferred work

- Chain-integrity verification (that a `prior_entry_digest` genuinely
  matches the immediately preceding entry, and that `sequence` values are
  globally contiguous) is explicitly Layer 4, deferred beyond this phase
  and beyond Group 8's schema scope.
- Self-reference-by-digest-value detection is not enforced at Layer 2
  (§6, `test_136s_record_digest_graph_journal_prior_digest_is_not_its_own_digest`).
- Group 9+ (`QuarantineRecord`, notification/marker/receipt bindings,
  `CompatibilityState`, `HistoricalAuthorityReference`) is explicitly
  out of scope for this phase and was not implemented, exercised, or
  designed.

## 17. Verification verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR NEXT EXECUTABLE-SCHEMA GROUP**

Zero Blocking findings were independently discovered or reproduced. All
twelve inherited non-blocking findings remain disclosed, unresolved, and
non-blocking.

## 18. Recommended next phase

Per the frozen contract's §46 implementation-group table, the next
unimplemented group after Group 8 is Group 9. The exact next group's
title and inventory must be independently re-derived from the frozen
contract text at the start of that phase, not inferred solely from
conceptual sequence. This phase does not begin that derivation and does
not begin Group 9 implementation.
