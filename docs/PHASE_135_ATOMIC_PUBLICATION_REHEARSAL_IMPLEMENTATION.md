# Phase 135S — Atomic Publication Rehearsal Implementation

**Phase classification:** implementation. **Not:** contract design, contract verification, CLTR authority cutover, legacy demotion, legacy retirement, Stage 3 design, execution-capability introduction.

**Verified Stage 2 contract:** `docs/PHASE_135_ATOMIC_PUBLICATION_REHEARSAL_CONTRACT_AND_IMPLEMENTATION_PLAN.md` (135Q, commit `16d065e4`), independently verified by `docs/PHASE_135_ATOMIC_PUBLICATION_REHEARSAL_CONTRACT_VERIFICATION.md` (135R, commit `0d5b2013`, verdict VERIFIED WITH NON-BLOCKING FINDINGS).

**Binding semantic authority (unchanged):** CLTR-001 v1.0. **Production wire contract (unchanged):** CLTR-SCHEMA-001 v1.0.1. **Notification contract (unchanged):** PFN-001. **Report contract (unchanged):** PFR-001.

---

## 1. Implementation summary

135S implements Stage 2 — Atomic Publication Rehearsal, Legacy Authority — under `src/pcae/cltr/migration/rehearsal/`. Legacy lifecycle remains the sole production authority throughout. Every artifact this package produces (the CLTR record it re-derives, all rehearsal candidates, the manifest, the rehearsal pointer, and the evidence record) is disclosed as non-authoritative. Stage 2 is invoked, gated behind `PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED` (disabled by default), from a single shared coordinator called identically from all four production finalization entry points (`phase_complete`, `task_finish`, `phase_report_create`, `notify_send_report`), strictly after Stage 1 dual-derivation has already completed for the transition.

This phase also resolves the four findings 135Q/135R identified as Blocking prerequisites for Stage 2 implementation (F-135P-1, F-135P-2's `EXPECTED_REPRESENTATION_DIFFERENCE` half, F-135P-3, F-135P-4) — see §16.

## 2. Source documents used

Read directly, in full, before implementation: 135Q (1,174 lines, all 60 sections), 135R (589 lines, all 64 sections), 135O's implementation (`assembly.py`, `cltr_derivation.py`, `comparison.py`, `coordinator.py`, `evidence.py`, `legacy_derivation.py`, `persistence.py`, `reconciliation.py`, `shared_input.py`, `status.py`, `transition_identity.py`), and the current `src/pcae/core/finalization_transaction.py` (all four entry-point call sites and both Stage 1 capture points, confirmed at their cited line numbers).

## 3. Stage 2 authority boundary

`production_authority` remains a hardcoded `ProductionAuthority.LEGACY` literal (`pcae.cltr.migration.enums`), untouched by every Stage 2 flag, module, and code path. No Stage 2 module imports, calls, or references any production pointer, marker, receipt, or notification-dispatch path. The rehearsal generation and rehearsal pointer are non-authoritative by construction (namespace-separated, §7 below), never merely by policy.

## 4. Legacy-authority preservation

Confirmed by construction and by test (`tests/test_cltr_rehearsal_coordinator.py::TestIsolationAndNoExecution`, `TestDisabledByDefault`): with `PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED` unset, zero Stage 2 code executes and no `rehearsals/` namespace is created; with it enabled, the legacy path's dispatch count, receipt behavior, and `TransactionResult` are identical to the Stage-2-disabled case (`_run_stage2_atomic_rehearsal` never receives or mutates `result`).

## 5. Package architecture

```
src/pcae/cltr/migration/
  disclosure.py                 # F-135P-4 fix: one shared NON_AUTHORITY_DISCLOSURE constant
  rehearsal/
    __init__.py
    enums.py                    # CandidateKind, ArtifactRole, CheckpointState, RecoveryState, RehearsalOutcome
    models.py                   # CandidateArtifact, RehearsalManifest, RehearsalPointer, RehearsalEvidenceRecord
    identity.py                 # rehearsal_generation_id (135Q §6)
    configuration.py            # PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED + invalid-configuration matrix (135Q §45/§46)
    candidates.py                # 10 candidate-artifact builders (135Q §10-§16)
    comparison.py                 # EXPECTED_REPRESENTATION_DIFFERENCE wiring (F-135P-2 half)
    digest.py                     # per-artifact / generation digest (135Q §19)
    manifest.py                   # manifest build + verify (135Q §18/§19/§38)
    persistence.py                 # namespace, atomic writes, directory-level finalize rename (135Q §7/§24/§25)
    pointer.py                     # atomic rehearsal-only pointer (135Q §23)
    evidence.py                    # Stage 2 evidence record (135Q §33)
    coordinator.py                  # 19-step sequence orchestration, fault injection, quarantine (135Q §17/§20-§30/§39)
    recovery.py                     # state-based recovery classification (135Q §27, read-only)
    status.py                       # read-only status backing (135Q §34)
    reconciliation.py               # read-only reconcile backing (135Q §35)
```

18 modules planned by 135Q §49 were consolidated to 13 (plus the shared `disclosure.py`), following the phase brief's own allowance ("actual layout may be consolidated where repository conventions support it... do not create unnecessary one-function modules"): the eight per-representation candidate modules (`report_candidate.py`, `metadata_candidate.py`, etc.) are one-function-each and were merged into `candidates.py`; `verification.py`'s role is filled by `manifest.verify_manifest`.

Reused, never duplicated: `pcae.cltr.canonicalization.canonicalize_dict` / `pcae.cltr.digest.compute_dict_digest` (digesting), `pcae.cltr.migration.persistence.{is_safe_segment,safe_join,write_atomic,write_immutable,timestamp,new_uuid}` (containment/atomicity), `pcae.cltr.migration.{legacy_derivation.derive_legacy, cltr_derivation.derive_cltr, comparison.compare}` (Stage 1 derivation and comparison, unmodified in their core logic), `pcae.cltr.migration.shared_input.SharedTransitionInputPackage` (the same object Stage 1 already assembled — never re-assembled independently). No import from `src/pcae/cltr_prototype/`.

## 6. Configuration

`PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED` (new, disabled by default), read by `rehearsal.configuration.load_rehearsal_configuration()`. Reuses Stage 1's `PCAE_CLTR_MIGRATION_STAGE`/`PCAE_CLTR_MIGRATION_EPOCH` unchanged. Fail-closed: `RehearsalConfigurationError` for every unsafe combination, matching Stage 1's `MigrationConfigurationError` discipline exactly. With the flag disabled, production behavior is unchanged (confirmed by test).

## 7. Invalid configuration matrix (implemented and tested)

| Combination | Result |
|---|---|
| Rehearsal enabled, Stage 1 disabled | rejected |
| Rehearsal enabled, incompatible `migration_stage` | rejected |
| Rehearsal enabled, missing `migration_epoch` | rejected |
| Rehearsal enabled, non-legacy `production_authority` | rejected (structurally unreachable today, checked anyway) |
| Rehearsal enabled, a reserved Stage-3-pattern flag present | rejected |

`tests/test_cltr_rehearsal_coordinator.py::TestConfiguration` covers all five.

## 8. Preconditions

`coordinator._precondition_failures` checks, before any candidate directory is created: Stage 2 effectively active; the shared input package has bound a `LEGACY_COMPLETION`-stage revision; Stage 1's own `MigrationResult.status == "completed"`; no Stage 1 `authority_relevant_mismatch`; non-empty `migration_epoch`/`authority_epoch`. On any failure, a `REJECTED_PRECONDITION` evidence record is persisted and the sequence stops before step 11 (no candidate directory exists) — matching 135Q §21's own closing guarantee, verified by `TestPreconditionRejection`.

**Disclosed scope decision:** the full twelve-item precondition list in 135Q §21 includes several checks (schema-version compatibility, "no unresolved Stage 2 Blocking finding," cross-cutover-flag rejection) that are already covered structurally elsewhere in this implementation (schema versions are fixed constants this codebase controls; the four Blocking findings are resolved in this same phase, §16) rather than re-checked redundantly inside the precondition function itself.

## 9. Deterministic identities

`rehearsal.identity.compute_rehearsal_generation_id` implements 135Q §6's exact composite (`migration_epoch`, `authority_epoch`, `transition_id`, `shared_input_package_id`, `final_input_revision_digest`, `phase_id`, `task_id`, `schema_versions`, fixed `rehearsal_stage` literal, fixed `production_authority_disclosure` literal), hashed via the same canonical-JSON SHA-256 CLTR-SCHEMA-001 §14/§15 already define. No timestamp, UUID, title, or Git-history input anywhere in the identity.

## 10. Namespace

Implements 135Q §7 exactly: `.pcae/cltr-migration/epochs/<epoch>/rehearsals/<transition-id>/{candidates,generations,failures,quarantine,current-rehearsal}`, sibling of (never nested inside) Stage 1's `transitions/`. `rehearsal.persistence` reuses Stage 1's `safe_join`/`is_safe_segment` containment primitives unchanged (`TestContainment::test_traversal_segment_rejected`).

## 11. The 23-item candidate inventory: implemented scope

10 of 135Q §9's 23 items are emitted as separate files, matching 135Q §7's own example directory listing exactly (`cltr_record.json`, `report_candidate.json`, `metadata_candidate.json`, `architecture_status_candidate.json`, `checkpoint_candidate.json`, `notification_intent_candidate.json`, `marker_candidate.json`, `receipt_candidate.json`, `commit_attribution_candidate.json`, `repository_transition_candidate.json`).

The remaining 13 items are bound inside the manifest rather than emitted as separate files:

- Items 15-16 (shared-input package reference, Stage 1 evidence reference) — bound as `shared_input_package_id`/`final_input_revision_digest` and `stage1_evidence_digest` (in the evidence record).
- Item 17 (comparison results) — `manifest.comparison_results`.
- Items 18-20 (manifest, per-artifact digests, generation digest) — the manifest *is* item 18; items 19-20 are fields on it.
- Item 21 (migration/authority epoch) — manifest fields.
- Item 22 (limitations) — `manifest.limitations`.
- Item 23 (non-authority disclosure) — `manifest.non_authority_disclosure`.

Items 11-14 (git-attribution view, compatibility/legacy-format view [optional per 135Q's own table], diagnostic envelope [optional], reconciliation view) are **disclosed, not implemented as separate files**: git attribution is folded into the commit-attribution candidate's content; the two optional views are omitted (135Q's own table marks them optional); the reconciliation view is computed on demand by `rehearsal.reconciliation.reconcile` rather than stored as a static artifact — this mirrors how Stage 1's own `reconciliation.py` already works (a computed view, not a stored file). This disclosure is carried into every manifest's `limitations` field, never silently omitted.

## 12. Candidate honesty

Every candidate artifact carries `non_authority_disclosure` (the shared `disclosure.py` constant) and is tagged with an `artifact_role` (`copied_evidence`/`normalized_legacy`/`cltr_derived`/`external_effect_intent`/`unverifiable`/`projected`) — never `production_authoritative`. Concretely:

- **Report candidate:** `report_id` is `rehearsal:<generation-id>:<legacy-report-id-or-unresolved>`, never equal to a real `report_id`; `report_role: "rehearsal_candidate"`.
- **Metadata candidate:** its own `metadata_id`, never written to a production metadata path; fields dependent on unoccurred external effects are explicit `{"value": null, "reason": "external_effect_not_occurred"}`.
- **Architecture Status candidate:** sourced only from `phase_id`, `transition_status` (`lifecycle_state`), `transition_type`-derived booleans, and an explicit `recommended_next_phase` field bound in the shared input — never parsed from prose; `runtime_state` copied verbatim from the same constants `pcae runtime inspect` uses (`pcae.core.runtime_introspection`).
- **Checkpoint candidate:** rehearsal-scoped state vocabulary (`CheckpointState` enum), no collision with any production checkpoint state string.
- **Notification-intent candidate:** `delivery_attempted: false`, `rehearsal_only_status: true` always; `idempotency_key` is `rehearsal:`-prefixed so it can never collide with a real PFN-001 key; `intended_channel` is a channel-type string only, never a credential.
- **Marker candidate:** `state: "rehearsal_candidate_dispatched_simulated"` — never the bare production literal `"already_dispatched"` (confirmed live via this phase's own `pcae phase-report reconcile` output, which prints exactly that literal).
- **Receipt candidate:** `state: "rehearsal_recorded"` — never the bare production literal `"finalized"` (same live confirmation); `production_completion_authority: "legacy"` always; `delivery_confirmed: false` always.

`TestSuccessfulRehearsal::test_no_candidate_claims_production_authoritative_role` asserts the marker/receipt anti-confusion properties directly.

## 13. Assembly sequence (implemented)

`coordinator.run_stage2_rehearsal` implements the 19-step sequence: (1) precondition check, (2) identity computation, (3) idempotency check against an already-finalized generation, (4) candidate-directory creation, (5-6) candidate derivation (10 artifacts), (7) reuse of Stage 1's already-computed legacy/CLTR derivation as the "normalized legacy" comparison basis, (8-9) comparison summarization (`rehearsal.comparison.summarize`, extended with `EXPECTED_REPRESENTATION_DIFFERENCE` classification), (10) mismatch policy application, (11-12) candidate directory + all 10 artifacts written, (13) manifest write, (14) manifest/digest verification (fail-closed), (15) directory-level atomic finalization (`candidates/` → `generations/`), (16) atomic pointer publication, (17) post-publication readback verification, (18) evidence persistence, (19) exposure via the read-only `status`/`reconcile` commands.

Ordering is enforced by construction: verification (14) strictly precedes finalization (15), which strictly precedes pointer publication (16) — a partially-verified generation cannot become visible.

## 14. Manifest, digests, immutable persistence

`rehearsal.manifest.build_manifest`/`verify_manifest` implement 135Q §18/§19: fixed canonical artifact ordering (`CANDIDATE_ORDER`, never directory-listing order), nested digest binding (generation digest covers each artifact's own digest, not raw bytes, plus the four identity fields), `digest_algorithm: "sha256"` explicit field (fail-closed on any other value), split-brain cross-reference checks (every artifact's `rehearsal_generation_id`/`transition_id` must agree with the manifest's). `rehearsal.persistence.finalize_generation` performs the directory-level `os.replace` rename — **explicitly disclosed, per F-135R-1, as a new primitive** (POSIX-atomic, but this codebase's only prior precedent, `write_atomic`/`write_immutable` at `persistence.py:84-112`, is file-level, not directory-level); a bounded retry (3 attempts, 50ms backoff) is applied before failing closed, addressing 135R's disclosed Windows-transient-`PermissionError` caveat.

## 15. Atomic rehearsal pointer

`rehearsal.pointer.publish` validates the target generation exists, is finalized, and its recorded digest matches the on-disk manifest's digest, *before* the atomic replace (`pcae.cltr.migration.persistence.write_atomic`'s mkstemp+fsync+`os.replace` primitive, reused unchanged). Rejects (raises `PointerRejectedError`, never silently accepts): a dangling target, a digest mismatch, a quarantined target. `verify_published_target` performs the post-publication readback (135Q §20 step 17); an unconfirmed readback is classified `UNCERTAIN_PUBLICATION`, never silently treated as success. `TestContainment::test_pointer_rejects_dangling_target` and `TestFaultInjection` cover this.

## 16. F-135P finding dispositions (Blocking prerequisites for Stage 2 implementation)

### F-135P-1 — two entry points fell back to generic recovery classification

**Fixed.** `_ENTRY_POINT_RECOVERY_CLASSIFICATION` (`finalization_transaction.py`) now maps `"phase_report_create"` → `"report_create_recovery"` and `"notify_send_report"` → `"manual_governed_recovery"`, using the dedicated enum values that already existed for exactly this purpose. Regression: `tests/test_cltr_migration_135p_verification.py::TestEntryPointRecoveryClassificationWiring::test_report_create_and_manual_recovery_are_correctly_mapped`.

### F-135P-2 (`EXPECTED_REPRESENTATION_DIFFERENCE` half) — comparison-result class was declared but unreachable

**Fixed, for Stage 2's own comparison surface.** `rehearsal.comparison.classify_candidate_field` classifies a notification/marker/receipt-candidate field that depends on an unattempted external effect as `EXPECTED_REPRESENTATION_DIFFERENCE`, never as a fabricated match and never as a silently dropped mismatch. `EXPECTED_DIFFERENCE_KINDS` in `rehearsal.enums` names exactly the three representation kinds 135Q §31 specifies (notification, marker, receipt) — report/metadata/Architecture-Status/checkpoint remain ordinary content comparisons with no carve-out, matching 135R §32's independent confirmation. `TEMPORAL_ORDER_MISMATCH` (the other half of F-135P-2) remains unreachable through Stage 2, disclosed as such per 135Q/135R's own disposition — it is not required by any Stage 2 contract area.

### F-135P-3 — `derive_cltr` would crash on non-empty commit ownership

**Fixed.** `cltr_derivation._normalize_commit_ownership` converts raw commit-hash strings into typed `CommitOwnershipEntry` values (`certification_state=CertificationState.UNVERIFIABLE`), mirroring the Stage-0 shadow observer's own precedent (`finalization_transaction.py`'s `commit_ownership` construction) exactly, before constructing `ProductionCltrRecord`. This is directly exercised by the commit-attribution candidate (§9 item 9). Regression: `tests/test_cltr_migration_135p_verification.py::TestComparisonClassFieldCoverage::test_commit_ownership_no_longer_crashes_derivation` (derives successfully with a non-empty `phase_commit_ownership`, asserts `CLTR-COMMIT-2` no longer raises), plus `tests/test_cltr_rehearsal_coordinator.py`'s commit-attribution-candidate coverage.

### F-135P-4 — `NON_AUTHORITY_DISCLOSURE` hardcoded five (135R: seven) times

**Fixed for the five Stage 1 copies named in F-135P-4.** `pcae.cltr.migration.disclosure.NON_AUTHORITY_DISCLOSURE` is the one shared source of truth; `evidence.py`, `coordinator.py`, `persistence.py`, `status.py`, `reconciliation.py` now import and extend it rather than hardcoding independent copies. Every Stage 2 rehearsal module imports the same constant — no eleventh-through-sixteenth hardcoded copy was introduced. **Not fixed (correctly, per 135R's own disposition):** the two additional copies 135R's F-135R-2 disclosed in the Stage 0 `cltr/` namespace (`cltr/persistence.py`, `cltr/inspection.py`) remain untouched — Stage 0 is out of both 135P's and this phase's scope, and Stage 2 code never touches that namespace. Regression: `tests/test_cltr_migration_135p_verification.py::TestNonAuthorityDisclosureConsistency::test_five_copies_now_share_one_source_of_truth`.

## 17. All-four-entry-point integration

`finalization_transaction._run_stage2_atomic_rehearsal` is called once, from the single call site immediately after `_complete_stage1_migration` (itself called identically for all four entry points), inside `run_finalization_transaction()`. No entry-point-specific branching exists in either helper (`tests/test_cltr_rehearsal_coordinator.py::TestFourEntryPoints::test_no_entry_point_specific_branching_in_stage2_call_sites` asserts `"if entry_point =="` is absent from the Stage 2 call-site source). `TestFourEntryPoints::test_rehearsal_runs_identically_for_every_entry_point` drives all four real entry points (`task_finish`, `phase_complete`, `phase_report_create`, `notify_send_report`) through `run_finalization_transaction` end-to-end and confirms rehearsal evidence exists for each.

## 18. Ordinary and recovery paths

Stage 2 consumes Stage 1's already-truthful recovery classification (now that F-135P-1 is fixed) as part of its precondition checks; no separate recovery-path-specific Stage 2 logic exists beyond what 135Q's contract requires, since Stage 2's own precondition contract (§8 above) already fails closed on an incomplete/rejected legacy path regardless of *why* it was incomplete.

## 19. 135H.1 escape-prevention

Traced independently, per 135Q §41's nine-claim chain: a rejected/partial legacy path never binds a `LEGACY_COMPLETION`-stage shared input (or binds one whose fields are themselves incomplete) → the precondition check (§8 above) fails closed before any candidate directory is created → no candidate, no manifest, no finalized generation, no pointer, no progression credit is ever produced. `TestPreconditionRejection::test_rehearsal_disabled_is_rejected_before_any_write` and the `REJECTED_PRECONDITION` outcome path confirm no rehearsal namespace is created on precondition failure.

## 20. Exactly-once preservation

`coordinator.run_stage2_rehearsal`'s idempotency check (step 3) reads an already-finalized generation's manifest and returns `IDEMPOTENT_REPLAY` without any further write when the identity is unchanged (`TestIdempotencyAndReplay::test_identical_replay_is_idempotent_no_op`). The coordinator never calls, imports, or otherwise invokes any production completion/promotion/notification/marker/receipt code path — it only *reads* Stage 1's already-produced `LegacyDerivationResult`/`CltrDerivationResult` (both pure functions of the shared input) as comparison input.

## 21. Notification isolation

`TestIsolationAndNoExecution::test_rehearsal_package_never_imports_telegram_sink` statically parses every module under `rehearsal/` (via `ast`) and asserts no import references `telegram` in any form. `test_rehearsal_package_never_uses_subprocess_or_sockets` greps every module's source for `subprocess`/`socket`/`urllib`/`requests` and asserts none are present. The notification-intent candidate is pure data (§12 above); no dispatch, delivery confirmation, resend, or suppression code path exists anywhere in the package.

## 22. Marker/receipt isolation

Confirmed by construction (namespace separation, §10) and by the anti-confusion literals in §12: no code path in `rehearsal/` opens any production marker or receipt file for writing. `receipt_candidate`'s `production_completion_authority` field is always the literal `"legacy"`.

## 23. Read-only CLI

`pcae cltr migration rehearsal status` and `pcae cltr migration rehearsal reconcile --phase-id <ID>`, wired in `src/pcae/cli.py` under the existing `cltr migration` subparser tree, backed by `rehearsal.status.rehearsal_status`/`rehearsal.reconciliation.reconcile`. Both are strictly read-only — neither module imports `coordinator.py` or any write-capable function; both print an explicit non-authority disclosure line distinct from Stage 1's own (`_REHEARSAL_DISCLOSURE_LINE`), matching the existing `pcae cltr migration status`/`reconcile` presentation convention exactly (`--json` supported identically). `test_fault_injector_never_reachable_from_production_cli` confirms the CLI module never references the coordinator's test-only `fault_injector` parameter.

## 24. Security and containment

Path traversal and symlink-escape protection reuse Stage 1's already-verified `is_safe_segment`/`safe_join` unchanged (`TestContainment::test_traversal_segment_rejected`). Pointer/manifest/generation/artifact substitution are all detected by digest recomputation at verification time (`manifest.verify_manifest`); a dangling or quarantined pointer target is rejected explicitly (`pointer.validate_publication_target`).

**Disclosed scope decision:** 135Q §47 names fourteen security rows; this implementation directly tests path traversal, dangling-pointer rejection, and digest/manifest/generation substitution (via the shared digest-recomputation mechanism, which structurally covers every substitution row identically — a substituted artifact, manifest, or generation all fail the same `verify_manifest` check). Symlinked-directory adversarial tests (a pre-existing symlink placed at a candidate-directory or artifact-file target) are not separately exercised as their own test cases in this phase; `rehearsal.persistence.write_candidate_artifact` does check `target.is_symlink()` and refuses to write through one, but this specific check has no dedicated regression test in this phase — recorded as a limitation (§27).

## 25. No-execution proof

`TestIsolationAndNoExecution::test_rehearsal_package_never_uses_subprocess_or_sockets` and `test_rehearsal_package_never_imports_telegram_sink` (§21) together constitute the no-subprocess/no-network/no-Telegram proof for this package. `test_runtime_remains_observed_and_execution_unavailable` confirms the shared runtime-posture constants this package reads (`pcae.core.runtime_introspection`) are unchanged: `Observed` / `observe` / `unavailable`.

## 26. Production-output equivalence

Confirmed by test: with Stage 2 disabled, `TestDisabledByDefault` shows zero rehearsal namespace creation and unchanged dispatch-call counts. With Stage 2 enabled and successful, `TestSuccessfulRehearsal::test_legacy_authority_unaffected_by_rehearsal` confirms Stage 1's own reconciliation output is unaffected. With Stage 2 enabled and blocked by mismatch, the coordinator finalizes the generation as evidence but never publishes the pointer (`RehearsalOutcome.BLOCKED_BY_MISMATCH`) — production behavior is identical in every case, since `_run_stage2_atomic_rehearsal` never touches `result` (the `TransactionResult`) at all.

## 27. Limitations and disclosed scope decisions

- The 23-item candidate inventory is implemented as 10 stored file artifacts + 13 items bound into the manifest/evidence record, per the disclosed mapping in §11 — not 23 separate files. This mapping is itself disclosed inside every manifest's `limitations` field, never silently omitted.
- Comparison against "the authoritative production artifact that actually governed this transition" (135Q §31) is implemented by reusing Stage 1's own `LegacyDerivationResult` (already-normalized legacy fields) as the comparison basis, rather than independently re-parsing raw production files (`.pcae/phase-reports/*.md`, etc.) a second time. This avoids duplicating Stage 1's own normalization logic (per the phase brief's explicit instruction not to duplicate existing production/Stage-1 functionality) at the cost of not independently re-deriving the "authoritative" side of the comparison from raw files.
- Full state-based *resumption* of an interrupted candidate (135Q §27's `candidate_incomplete` → automatic resume-from-last-step) is not implemented; `recovery.classify` correctly *reports* every state 135Q §27 names (read-only), but the coordinator does not itself resume a partially-written candidate directory — a fresh `run_stage2_rehearsal` call for the same transition either reaches the same deterministic identity (and is treated as idempotent once finalized) or, if a `candidates/<id>/` directory was abandoned mid-write, that directory is left in place as inspectable evidence (matching 135Q §26's "quarantined on next inspection if abandoned" rows) rather than being automatically completed or cleaned up.
- Fault-injection coverage in this phase's test suite exercises a representative subset of 135Q §52's full per-artifact-write/manifest/verification/finalization/pointer-publication boundary list (via the `fault_injector` parameter, demonstrated for `before_manifest_write`), not every individual boundary as a separately named test case.
- Rollback rehearsal (135Q §33/§36/§37) and the full quarantine-trigger matrix (135Q §30's ten conditions) are implemented structurally (`pointer.publish` rejects a quarantined target; `coordinator` writes quarantine records on pointer-rejection and manifest-verification failure) but do not have a dedicated rollback-rehearsal CLI or evidence-record variant in this phase — recorded as deferred, non-gating detail for 135T's independent verification to assess.
- Symlinked-directory adversarial tests are not separately exercised (§24).

None of these limitations weakens the core safety properties verified in 135R's contract: legacy remains sole production authority; the rehearsal generation and pointer are non-authoritative by construction; no production pointer, marker, receipt, or notification path is touched; preconditions fail closed before any candidate directory exists; a partial or blocked candidate can never become `current-rehearsal`.

## 28. Deferred Stage 3 work

No Stage 3 design, CLTR authority activation, legacy-authority demotion, or legacy-authority retirement occurred in this phase. `PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED` cannot activate Stage 3 under any combination (§7).

## 29. Test results actually run during 135S

- **Stage 2 focused tests:** `tests/test_cltr_rehearsal_coordinator.py` — 28/28 passed.
- **Combined migration suite** (`tests/test_cltr_migration_*.py tests/test_cltr_135o_integration.py tests/test_cltr_rehearsal_coordinator.py`): 121/129 passed; 8 pre-existing failures, all independently confirmed (via `git stash`) to reproduce identically on unmodified `main` before this phase's changes — a sandbox-local defect in the post-dispatch receipt-modeling step of `run_finalization_transaction` (`completed_receipt_best_effort_incomplete`), unrelated to CLTR/migration/rehearsal code, not touched or fixed by this phase.
- **Production CLTR combined regression** (`tests/test_cltr_*.py`): 406/414 passed; same 8 pre-existing failures.
- **Affected finalization regression** (`test_finalization_transaction_134e10`, `test_finalization_gate_enforcement`, `test_finalization_notification_guarantee`, `test_finalization_configuration_identity_cross_agent_134b3`, `test_phase_113v_n_notification_finalization_repair`): 112/117 passed; 5 pre-existing failures from the same root cause, independently confirmed identical on baseline `main`.
- **Notification/marker/receipt/phase-report/Architecture-Status regression** (`-k "finalization or notification or marker or receipt or phase_report or architecture_status"`): 1173/1183 passed; 10 pre-existing failures (the above 5 + the 4 combined-migration-suite four-entry-point cases + 1 additional pre-existing `test_phase_reports.py` failure, independently confirmed identical on baseline `main` via `git stash`).
- **Fast Green** (`python -m pytest -m "fast_green" -n auto`): **4391/4391 passed**, unchanged from the inherited 135P/135Q/135R baseline.

No baseline failure is hidden inside an aggregate count above; every failing node ID was individually identified and independently confirmed pre-existing via `git stash` before being excluded from this phase's own claim of correctness.

## 30. Recommended next phase

**135T — Atomic Publication Rehearsal Independent Verification.**

135T must independently attack this implementation: re-derive the 135Q/135R contract against this implementation's actual source (not this document's summary), verify the candidate-inventory scoping decision in §11/§27 is disclosed accurately and does not hide an authority gap, verify the F-135P-1/-2/-3/-4 fixes against live source, exercise the fault-injection/crash-matrix/quarantine/idempotency contract more exhaustively than this phase's representative subset, and confirm no rehearsal artifact can be mistaken for production authority under adversarial inspection. 135T must not proceed to Stage 3 design, authority-cutover planning, CLTR authority activation, legacy-authority demotion, or legacy-authority retirement.
