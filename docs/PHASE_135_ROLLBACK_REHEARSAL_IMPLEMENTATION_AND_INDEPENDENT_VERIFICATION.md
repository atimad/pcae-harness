# Phase 135U — Rollback Rehearsal Implementation and Independent Verification

**Phase classification:** implementation, independent verification (combined, single governed phase).
**Not:** Stage 3 authority cutover, legacy demotion, legacy retirement, roll-forward automation, production pointer/rollback of any kind.

**Binding semantic authority:** CLTR-001 v1.0 (frozen 135B; verified 135C/135D/135G).
**Production wire contract:** CLTR-SCHEMA-001 v1.0.1 (frozen 135I; amended 135J).
**Rollback-rehearsal contract source:** 135Q §33 (evidence shape) / §36 (rollback-rehearsal scope) / §37 (roll-forward preference) / §38 (split-brain prevention), independently re-derived and confirmed in 135R §36 ("Rollback-rehearsal verification") and §37/§38.
**Verified Stage 2 implementation:** 135S, independently verified and repaired by 135T (VERIFIED WITH NON-BLOCKING FINDINGS; commits `8670312e`, `e0484051`). 135T's F-135R-4 disposition explicitly confirmed rollback rehearsal was **not implemented** in 135S — `rehearsal/` had no rollback module — and recommended 135U to close that gap.

## 1. Source contract and derivation

Before writing any code, this phase re-read 135M, 135N, 135O, 135P, 135Q, 135R, 135S, 135T in full and located the frozen rollback-rehearsal text directly (rather than trusting any prior summary):

- **135Q §36 ("Rollback rehearsal")** freezes exactly what rollback rehearsal *may* do (retain the prior pointer as a no-op; switch the pointer to a prior verified generation via the same §23 atomic-replace pointer contract; record a `rollback_rehearsal` evidence record, "§33-shaped," noting the prior and new targets; invalidate progression eligibility for the generation rolled back from; reconcile the epoch explicitly if the rollback crosses an epoch boundary; preserve all generations and evidence) and what it **must not** do (change production pointers; roll back the production report; undo external delivery — there is none to undo, per §17's structural no-dispatch guarantee; alter the production marker or receipt; rewrite append-only history).
- **135Q §37 ("Roll-forward preference")** freezes a *preference*, not a distinct roll-forward command: prefer reconciliation/roll-forward over pointer rollback whenever production has already achieved an irreversible state (the normal case, per 135N's F-135N-1 repair) — and forbids any rollback evidence or CLI output from implying a production effect was undone.
- **135Q §38 ("Split-brain prevention")** lists nine structural cross-reference checks, all enforced at manifest-verification time; 135R's independent re-derivation additionally flagged (as a disclosed, Non-Blocking completeness note, F-135R-4) that a concurrent-rollback-vs-ordinary-publication race is covered by the underlying atomic-replace mechanism but was not, at 135R's time, named as its own test case, since rollback rehearsal did not exist yet to test.
- **135Q §33** is the general Stage 2 evidence-record contract (fields, non-authority disclosure, standalone-auditability) that §36 explicitly says the rollback evidence record must follow ("§33-shaped").
- **No section of 135Q, 135R, 135S, or 135T specifies**: an exact rollback-request field list, an exact rollback-identity formula, an exact rollback CLI surface beyond the general future-command pattern established in §34/§35 (`pcae cltr migration rehearsal status`/`reconcile`), or an exact roll-forward *mechanism* (only the §37 *preference*). These are the areas 135U had to design, within the frozen scope boundaries above, rather than invent freely. Every design choice below is explicitly justified against the frozen "may"/"must not" lists.

**Missing-contract disclosure (required by the phase brief):** 135Q does not specify whether rollback to "no current rehearsal" (an empty pointer) is permitted. 135U does **not** implement this — every rollback request in this implementation requires an explicit, existing, verified `target_rehearsal_generation_id`; there is no code path that publishes an empty/absent pointer as a rollback outcome. This is a disclosed limitation, not a silent assumption.

## 2. Phase scope

Implemented in this phase, all under `src/pcae/cltr/migration/rehearsal/`:

- `rollback.py` (new) — the rollback-rehearsal request model, deterministic identity, target validation, the 11-step atomic rollback sequence, evidence construction/persistence, idempotency/conflict handling, and read-only rollback-status aggregation.
- `identity.py` — added `compute_rollback_request_id` (deterministic, pure function of bound fields).
- `models.py` — added `RollbackRequest` and `RollbackEvidenceRecord` dataclasses.
- `enums.py` — added `RollbackOutcome` (ten terminal states, matching the phase brief's required vocabulary exactly).
- `persistence.py` — added `rollbacks_dir`/`rollback_request_path`/`rollback_conflicts_dir`, nested under the existing per-transition rehearsal namespace (no new top-level directory).
- `pointer.py` — refactored `validate_publication_target` into a shared `validate_generation_target` helper and added `publish_generation` (targets an existing finalized generation by ID/digest rather than a freshly-built manifest object), so rollback publication is held to the *identical* containment/verification rules as ordinary forward publication — no duplicated, potentially-divergent logic.
- `reconciliation.py` — extended to surface `rollback_history` per transition (read-only; a genuine gap was found and fixed here — see §14, Finding F-135U-1).
- `src/pcae/commands/cltr_migration.py` / `src/pcae/cli.py` — added the `pcae cltr migration rehearsal rollback` (mutating) and `rollback-status` (read-only) CLI subcommands.

Not touched: `coordinator.py` (forward rehearsal is unchanged), `candidates.py`, `manifest.py`, `digest.py`, `configuration.py`, `comparison.py`, `evidence.py`, `status.py`, `recovery.py` (rollback reuses these read-only, unmodified).

## 3. Authority boundary

Unchanged and re-confirmed throughout this phase: legacy lifecycle is the sole production authority; CLTR is derivative; Stage 1 evidence is derivative; the Stage 2 rehearsal generation and pointer are non-authoritative; rollback rehearsal and rollback evidence are non-authoritative. `PRODUCTION_AUTHORITY_DISCLOSURE = "legacy"` (from `identity.py`, unchanged, reused by rollback evidence) and `NON_AUTHORITY_DISCLOSURE` (unchanged, reused on every rollback artifact) are the only two disclosure constants involved; rollback introduces no third disclosure constant and no authority-adjacent flag. `RehearsalConfiguration`'s existing fail-closed rejection of any Stage 3 flag (`_RESERVED_STAGE3_ENV_VARS`) is unmodified and still governs whether rollback rehearsal can even run (it requires `atomic_rehearsal_enabled`, which itself requires legacy-authoritative Stage 1).

## 4. Rollback request model

`RollbackRequest` (`models.py`) binds: `rollback_request_id`, `phase_id`, `transition_id`, `migration_epoch`, `authority_epoch`, `current_rehearsal_generation_id` (source, read from the live pointer at build time), `target_rehearsal_generation_id`, `source_result_evidence_digest` (the source pointer's `generation_digest`), `expected_pointer_generation_id` (identical to `current_rehearsal_generation_id`, the optimistic-concurrency anchor), `reason`, `non_authority_disclosure`.

`build_rollback_request()` reads the *live* pointer at call time — never a title, filename, timestamp, or Git-history heuristic — and binds exactly what it observed. If the live pointer moves between request construction and `execute_rollback()`, the request's own `expected_pointer_generation_id` will no longer match, and execution fails closed (§9).

## 5. Deterministic rollback identity

`compute_rollback_request_id()` (`identity.py`) is a pure function of `{phase_id, transition_id, migration_epoch, authority_epoch, source_rehearsal_generation_id, target_rehearsal_generation_id, reason}` plus two fixed constants (`rollback_stage`, `production_authority_disclosure`), hashed via the same `compute_dict_digest` (canonical JSON + SHA-256) every other Stage 1/Stage 2 identity in this codebase uses. No `uuid`, no wall-clock read, no process/hash-seed/locale/working-directory/temp-root dependence — independently confirmed in `tests/test_cltr_rehearsal_135u_independent_verification.py::TestIndependentIdentityDeterminism`, including a **fresh subprocess** re-derivation (`test_identity_stable_across_fresh_subprocess`) and a per-field mutation sweep over all six bound fields (`test_identity_changes_when_any_bound_field_changes`) confirming every one independently changes the identity.

## 6. Source and target validation

Before any pointer mutation, `execute_rollback()` (§9) re-verifies the **current** pointer's own generation against its recorded digest (tamper-detects a corrupted "before" state, not just the target), then `validate_rollback_target()` verifies the target:

- Safe-segment check on the target ID itself (rejects `/`, `\`, `..`, absolute-looking, or leading-dot segments) — enforced *twice*: once eagerly at `build_rollback_request()` time (fails closed before any request object even exists) and again structurally by `safe_join()` inside every path-construction call, so a single removed check cannot silently reopen the escape.
- `authority_epoch` must literally start with `legacy` (the `|`-delimited prefix), not merely *contain* the substring "legacy" — an initial substring-based check (`"legacy" in authority_epoch.lower()`) was written, then independently attacked and found bypassable by a value like `"cltr|not-legacy"`; repaired to a strict prefix check before this scope's tests were run for the first time (Finding F-135U-2, §14).
- Not quarantined (`quarantine_dir(.../target)/quarantine_record.json` must not exist).
- Manifest schema ID/version must match this package's own `MANIFEST_SCHEMA_ID`/`MANIFEST_SCHEMA_VERSION` (unsupported-schema rejection).
- `migration_epoch`/`transition_id` recorded in the target's own on-disk manifest must match the request's — rejects a target belonging to another epoch or another transition even if an attacker somehow supplied a syntactically valid ID from elsewhere in the same rehearsal tree.
- Every artifact's digest is **recomputed from bytes read fresh off disk** (never trusted from a cached value) and compared against the manifest's recorded digest, per artifact; the generation digest is independently recomputed from the freshly-recomputed artifact digests and compared against the manifest's own `generation_digest` — this is `verify_manifest()`'s exact tamper-detection discipline, re-implemented for the rollback-target path against on-disk state rather than in-memory `CandidateArtifact` objects, since a rollback target was finalized in a *prior* process, possibly a prior run entirely.
- Every artifact's own embedded `rehearsal_generation_id`/`transition_id` must agree with the target it's being read from (the same split-brain check `verify_manifest()` performs for forward rehearsal, §38).
- `verification_status` must be `"verified"` and `candidate_or_authoritative_role` must be `"rehearsal_candidate_generation"` — rejects a target whose manifest was somehow marked unverifiable or mislabeled.
- Every generation directory and every artifact file is checked with `.is_symlink()` before being read or treated as authoritative — a pre-existing symlink at either position is rejected, never silently followed (mirroring 135T's F-135T-1 repair for the candidate-write path, applied here to the rollback-*read* path).

## 7. Namespace

Rollback state lives entirely inside the existing per-transition rehearsal namespace, never a new top-level directory:

```
.pcae/cltr-migration/epochs/<epoch>/rehearsals/<transition-id>/
  candidates/... generations/... failures/... quarantine/...   # unchanged, Stage 2 (135S)
  current-rehearsal                                            # unchanged, Stage 2 (135S)
  rollbacks/<rollback-request-id>.json                         # 135U — immutable request-identity record
  rollbacks/<rollback-request-id>.evidence.json                # 135U — evolving evidence record
  rollback-conflicts/<rollback-request-id>-<timestamp>.json    # 135U — conflicting-replay quarantine
```

## 8. Immutable history

Rollback never deletes, renames, or rewrites a `generations/` or `failures/` entry. `tests/test_cltr_rehearsal_rollback.py::TestAtomicRollback::test_both_generations_remain_after_rollback` and `test_generation_bytes_unchanged_by_rollback` confirm, byte-for-byte, that the generation rolled back *from* is untouched after a rollback (its manifest is read before and after and compared for exact equality). Rollback evidence itself is append-only per request identity: the request-identity record is written via `write_immutable` (byte-identical writes are no-ops; differing content raises, routed to `rollback-conflicts/`, never overwriting).

## 9. Atomic pointer rollback (the 11-step sequence)

`execute_rollback()` implements, in order: (1) load the current pointer explicitly; (2) register the request identity (`write_immutable`) — doubles as both the durable-intent seam and the conflicting-replay detector; (3) idempotency short-circuit (an already-`PUBLISHED`/`VERIFIED` identical request whose target is already live current pointer returns `IDEMPOTENT_REPLAY`, no mutation); (4) a **crash-recovery completion path** (§11) for a request that was durably registered before but never got as far as recording final evidence, even though its own pointer replace already succeeded; (5) stale-current-pointer-expectation check (fails closed if the live pointer no longer matches what this request expected); (6) re-verification of the *current* generation's own digest; (7) target validation (§6); (8) the no-op-retain case (target already current at the time this specific request was built); (9) durable pre-mutation intent evidence write; (10) the atomic pointer replace itself, via `pointer.publish_generation()` — the same `os.replace`-backed, tmp-write-then-rename primitive `write_atomic`/`write_pointer_atomic` already use everywhere else in this package, so no new atomicity primitive was introduced; (11) pointer readback, target re-verification, and final evidence recording.

`pointer.publish_generation()` reuses `validate_generation_target()` — the *exact same* function `publish()` (ordinary forward publication) calls — so a rollback target is rejected by precisely the same dangling/quarantined/digest-mismatched/wrong-epoch/wrong-transition rules as an ordinary rehearsal-generation publication, by construction, not by parallel reimplementation.

## 10. Rollback evidence

`RollbackEvidenceRecord` (§33-shaped, per 135Q §36) binds: `evidence_id`, `schema_version`, `migration_stage` (`"stage_2_rollback_rehearsal"`), `migration_epoch`, `authority_epoch`, `production_authority` (`"legacy"`), `transition_id`, `phase_id`, `rollback_request_id`, `source_rehearsal_generation_id`, `target_rehearsal_generation_id`, `pointer_state_before`, `pointer_state_after`, `target_manifest_digest`/`target_generation_digest`, `outcome` (one of the ten `RollbackOutcome` values), `verification_result`, `publication_result`, `limitations`, `non_authority_disclosure`, `created_at`, self-excluding `record_digest`. `RollbackOutcome` distinguishes exactly the ten states the phase brief specifies: `rollback_requested`, `rollback_rejected`, `rollback_verified`, `rollback_published`, `rollback_publication_uncertain`, `rollback_idempotent_replay`, `rollback_conflict`, `rollback_recovery_required`, `rollback_reconciled`, `rollback_quarantined`.

No rollback evidence record or CLI output anywhere in this implementation claims a production effect was undone — independently checked (`tests/test_cltr_rehearsal_135u_independent_verification.py::TestIndependentProductionIsolation`) and structurally true by construction: `rollback.py` never imports, calls, or references `finalization_transaction`, `run_finalization_transaction`, or any production promotion/notification/marker/receipt code path.

## 11. Idempotency, conflicting replay, crash matrix, recovery, uncertainty

**Idempotency:** a byte-identical replay of a request whose target is already the live current pointer, with a prior `PUBLISHED`/`VERIFIED` evidence record for that exact identity, returns `IDEMPOTENT_REPLAY` and performs zero writes (`tests/test_cltr_rehearsal_rollback.py::TestIdempotencyAndConflict::test_idempotent_replay_does_not_duplicate_evidence`).

**Conflicting replay:** the same `rollback_request_id` reused with different bound content (any of target, source, epoch, transition, reason) is detected by `write_immutable` raising on the identity file, routed to `rollback-conflicts/`, and returns `CONFLICT` — the pointer is left completely untouched (`test_same_id_different_target_is_conflict`, `test_conflicting_replay_never_becomes_current_and_is_auditable`).

**Crash matrix:** fault injection was exercised at every named boundary from the phase brief (`load_current_pointer`, `request_identity_conflict_check`, `idempotency_check`, `verify_current_generation`, `validate_target`, `write_intent_evidence`, `before_pointer_replace`, `after_pointer_replace`, `pointer_readback`, `verify_target_generation_post_write`, `before_final_evidence`, `after_final_evidence`). For every fault injected **before** the atomic replace, the pointer is confirmed byte-for-byte unchanged after the crash (`TestCrashInjection::test_fault_before_pointer_replace_leaves_pointer_unchanged`, parametrized over 7 pre-replace boundaries). For a fault injected **after** the replace, the pointer is confirmed to already, correctly, durably reflect the new target — production is untouched either way, and the already-successful replace is never silently rolled back by the crash-handling path itself (`test_fault_after_pointer_replace_records_published_pointer_intact`).

**Recovery / uncertainty:** a crash between a successful atomic replace and final-evidence recording leaves a durably-registered request identity with no terminal evidence — this exact state is recognized on replay (§9 step 4) and completed (evidence recorded as `PUBLISHED`, pointer left untouched since it was already correct) rather than either being silently re-replayed as a fresh mutation or incorrectly rejected as "stale" (`test_recovery_after_crash_can_complete_via_replay`). A pointer-readback that does not confirm the target is recorded as `PUBLICATION_UNCERTAIN`, never silently retried and never reported as a clean success.

## 12. Quarantine

A target whose generation carries a `quarantine_record.json` is rejected outright, before any digest/manifest verification is even attempted (`TestTargetValidation::test_rejects_quarantined_target`). Rollback never removes or alters a quarantine record; quarantine history is preserved exactly as Stage 2 (135S) already established.

## 13. Progression eligibility, roll-forward, split-brain

**Progression eligibility:** rollback evidence has no `progression_eligibility` field at all (unlike forward-rehearsal evidence) — independently confirmed absent (`TestIndependentProgressionEligibility::test_rollback_never_sets_progression_eligibility_true_via_side_channel`). Rollback never mutates the rolled-back-from generation's own already-persisted forward-rehearsal evidence record; 135Q §36's "invalidate progression for the generation rolled back from" is satisfied structurally — that generation is simply no longer `current-rehearsal`, and every consumer of progression eligibility (`reconciliation.reconcile`) reads the evidence tied to whatever *is* current, which after a rollback is the target's own (unmodified, already-recorded) evidence.

**Roll-forward:** deliberately **not** implemented as a distinct mechanism, per the phase brief's instruction to implement only what the contract explicitly freezes. 135Q §37 freezes a *preference* (prefer reconciliation over rollback in specific scenarios), not a command or state machine. "Rolling forward" in this implementation is simply issuing a new, distinct rollback request whose target is the newer generation — verified end-to-end (`TestIndependentRollForwardDeferral::test_rolling_forward_again_requires_a_new_explicit_request`) and confirmed absent as a dedicated function (`test_no_dedicated_roll_forward_function_exists`).

**Split-brain:** every one of 135Q §38's structural cross-reference checks that applies to a finalized generation (epoch/transition binding, artifact-level `rehearsal_generation_id`/`transition_id` agreement) is re-run against the rollback *target* independently of forward publication, since a rollback target was verified by a possibly-earlier process invocation. The concurrent-rollback-vs-forward race F-135R-4 disclosed as correctly-deferred-until-implementation is resolved identically to how ordinary forward publication resolves it: both mutation paths target the same single `current-rehearsal` file via the same atomic `os.replace`, so whichever call's `os.replace` executes second determines the outcome, and both request-identity records remain on disk, auditable, regardless of which one "won."

## 14. Findings

### F-135U-1 (CONFIRMED, repaired) — post-rollback reconcile/status lose the requesting phase_id

**Description:** `reconciliation._find_rehearsal_transitions_for_phase()` (inherited from Stage 1/135O, reused unmodified by Stage 2's `reconcile`/`status`) resolves a `phase_id` to a transition by reading the *current* generation's own embedded `repository_transition_candidate.phase_id`. After a rollback moves the pointer to a generation finalized under a **different** `phase_id** than the one that requested the rollback, a subsequent `pcae cltr migration rehearsal reconcile --phase-id <original-requesting-phase>` (or `rollback-status`) silently returned `found: false` for a transition that, in fact, had just been the target of a real, successful rollback requested by exactly that phase.
**Contract source:** 135Q §35 (read-only reconciliation), extended by 135U's rollback contract.
**Reproduction:** independently found by `tests/test_cltr_rehearsal_135u_independent_verification.py::TestIndependentNoExecutionAndReadOnly::test_reconcile_reflects_rollback_without_mutating`, which built two generations under distinct `phase_id`s on the same transition, rolled back, then called `reconcile()` with the rollback-*requesting* phase_id and got `KeyError: 'transitions'`.
**Affected code:** `src/pcae/cltr/migration/rehearsal/reconciliation.py`.
**Authority impact:** none (read-only correctness gap, not a containment escape).
**Pointer impact:** none.
**Recovery impact:** would have made rollback evidence effectively invisible to `reconcile`/`rollback-status` for the phase that actually performed the rollback — a real operational blind spot for anyone auditing their own rollback via the phase_id they used to request it.
**Production-side-effect impact:** none.
**Exactly-once impact:** none.
**Test evidence:** `test_reconcile_reflects_rollback_without_mutating` (now passing after repair).
**Repair:** `_find_rehearsal_transitions_for_phase()` now also matches a transition whenever any of its own persisted `rollback_history` evidence records carry the queried `phase_id`, in addition to the existing current-generation check.
**Residual risk:** none identified; the fix is additive (widens matching, never narrows it) and does not change forward-rehearsal (non-rollback) behavior, confirmed by the full existing Stage 1/Stage 2 regression suite passing unchanged.
**Future-stage disposition:** none required; this is a Stage 2 read-only correctness fix, not a Stage 3 concern.

### F-135U-2 (CONFIRMED, repaired) — authority-epoch check used substring match, not prefix match

**Description:** the first implementation of the "authority_epoch remains legacy" rollback-target check used `"legacy" not in request.authority_epoch.lower()`, which a value like `"cltr|not-legacy"` satisfies (the substring `"legacy"` appears inside `"not-legacy"`), incorrectly passing validation for an authority-epoch string that does not actually start with the required `legacy` prefix used everywhere else in this codebase (`"legacy|<epoch>"`).
**Contract source:** 135U phase brief's target-validation list ("authority epoch remains legacy"); 135Q's `PRODUCTION_AUTHORITY_DISCLOSURE = "legacy"` convention.
**Reproduction:** independently found and reproduced by `tests/test_cltr_rehearsal_135u_independent_verification.py::TestIndependentTargetValidation::test_wrong_authority_epoch_rejected`, constructed with `authority_epoch="cltr|not-legacy"` before this fix; the rollback published successfully instead of being rejected.
**Affected code:** `src/pcae/cltr/migration/rehearsal/rollback.py`, `validate_rollback_target()`.
**Authority impact:** low in practice today (nothing in the current codebase can actually construct a live pointer or a real rollback request with a non-legacy authority_epoch, since `RehearsalConfiguration` fails closed on any Stage 3 flag), but the check itself was a genuine, independently-reproduced logic defect in an authority-adjacent guard, not merely a style nit.
**Pointer impact:** would have allowed a rollback whose request carried a spoofed-but-substring-matching authority_epoch to proceed to the atomic pointer replace.
**Recovery impact:** none beyond the above.
**Production-side-effect impact:** none (still confined to the rehearsal-only pointer even in the unrepaired case).
**Exactly-once impact:** none.
**Test evidence:** `test_wrong_authority_epoch_rejected` (now passing after repair).
**Repair:** changed to `request.authority_epoch.split("|", 1)[0].lower() != "legacy"` — an exact prefix check, matching every other `"legacy|<epoch>"`-shaped value in this codebase.
**Residual risk:** none identified.
**Future-stage disposition:** Stage 3 (authority cutover) will need its own, freshly-derived authority-epoch validation; this fix does not pre-empt that design.

No other Blocking or Non-Blocking defect was found. All findings above were fixed within this same governed phase before regression suites were (re-)run and before finalization.

## 15. Independent verification methodology

Two separate test modules exist by design: `tests/test_cltr_rehearsal_rollback.py` (primary implementation tests, written alongside the implementation, asserting the behavior as designed) and `tests/test_cltr_rehearsal_135u_independent_verification.py` (adversarial verification, written to re-derive expectations directly from 135Q §33/§36/§37/§38's frozen text and the 135U phase brief's own "at minimum verify" lists — e.g. it hardcodes its own copy of forbidden-term checks rather than importing `rollback.py`'s internal helper functions as ground truth, and it independently re-derives the identity formula's per-field sensitivity rather than trusting `rollback.py`'s own digest output for anything other than the actual assertion under test). The two genuine findings above (F-135U-1, F-135U-2) were both caught by the *independent* module, not the implementation module — confirming the separation was substantively useful, not just organizational.

## 16. Fresh regression results (this phase, freshly run)

| Suite | Command | Result |
|---|---|---|
| Rollback focused implementation tests | `pytest tests/test_cltr_rehearsal_rollback.py -q` | 43/43 passed |
| Rollback independent adversarial tests | `pytest tests/test_cltr_rehearsal_135u_independent_verification.py -q` | 26/26 passed |
| Stage 2 focused (existing, unmodified except `pointer.py` refactor) | `pytest tests/test_cltr_rehearsal_coordinator.py tests/test_cltr_rehearsal_135t_independent_verification.py -q` | 44/44 passed |
| Combined migration suite | `pytest tests/test_cltr_migration_*.py tests/test_cltr_135o_integration.py tests/test_cltr_rehearsal_coordinator.py tests/test_cltr_rehearsal_135t_independent_verification.py tests/test_cltr_rehearsal_rollback.py tests/test_cltr_rehearsal_135u_independent_verification.py -q` | 214/214 passed |
| Production CLTR combined regression | `pytest tests/test_cltr_*.py -q` | 499/499 passed |
| Affected finalization regression (exact 135S/135T node set) | `pytest tests/test_finalization_transaction_134e10.py tests/test_finalization_gate_enforcement.py tests/test_finalization_notification_guarantee.py tests/test_finalization_configuration_identity_cross_agent_134b3.py tests/test_phase_113v_n_notification_finalization_repair.py -q` | 117/117 passed |
| Notification/marker/receipt/report/Architecture-Status regression | `pytest tests/ -k "finalization or notification or marker or receipt or phase_report or architecture_status" -q` | 1185/1185 passed |
| Fast Green | `pytest -m fast_green -n auto` | 4391/4391 passed (unchanged from 135T — new 135U test modules are not fast_green-marked, matching 135T's own precedent of not marking its new adversarial module fast_green) |

No inherited failure was found anywhere in this phase; every suite above passed cleanly on first fresh run after the two repairs in §14, so no baseline-reproduction worktree exercise was required (unlike 135T, which had to disprove a false "pre-existing" claim — 135U made no such claim to begin with).

## 17. CLI

```
pcae cltr migration rehearsal rollback --phase-id <PHASE_ID> --target-generation <GENERATION_ID> [--reason <TEXT>] [--json]
pcae cltr migration rehearsal rollback-status --phase-id <PHASE_ID> [--json]
```

`rollback` is the sole mutating rollback entry point; it resolves `transition_id`/`migration_epoch`/`authority_epoch` from the same explicit, verified evidence `rollback-status`/`reconcile` already use (never inferred from file order or timestamps), and refuses to proceed if the `phase_id` resolves to zero or more than one rehearsal transition (`TestCLI::test_rollback_cli_ambiguous_phase_rejected`). `rollback-status` is strictly read-only, confirmed via before/after filesystem snapshot equality (`TestCLI::test_rollback_status_read_only`). No generic "repair" command was added (`test_no_generic_repair_command_exists`); `status`/`reconcile` never call `execute_rollback` (`test_status_and_reconcile_never_trigger_rollback`). Rollback rehearsal is **operator-command-only** in this phase — 135Q does not require rollback to be wired into any of the four production finalization entry points or any recovery path, and this implementation does not wire it into any of them; `rollback.py` never imports `finalization_transaction` (independently confirmed, §10/§11).

## 18. Production isolation, notification isolation, no-execution

Independently re-verified via live filesystem-snapshot equality before/after every rollback outcome (success, rejection, conflict, no-op-retain): no `.pcae/phase-reports/`, `.pcae/phase-completion-metadata.json`, architecture-status, checkpoint, notification, marker, or receipt path is created, modified, or even touched by any rollback code path (`TestIndependentProductionIsolation::test_no_production_namespace_exists_before_or_after_rollback`). `rollback.py` contains no `subprocess`, `socket`, `urllib`, `requests`, `telegram`, `smtp`, or literal URL scheme reference (`test_rollback_module_never_uses_subprocess_or_network`, `test_rollback_source_never_references_telegram_or_network_terms`). Runtime state re-confirmed `Observed` / `observe` / execution `unavailable` both before and after importing the new module (`test_runtime_remains_observed_and_execution_unavailable`, `test_runtime_capability_unchanged_by_rollback_module_import`).

## 19. Limitations

- Rollback to "no current rehearsal" (empty pointer) is not implemented — disclosed in §1, not silently assumed either way.
- Roll-forward is not a distinct mechanism, only an ordinary new rollback request targeting a newer generation — disclosed in §13.
- Cross-epoch rollback ("reconciling the epoch explicitly," per 135Q §36) is rejected outright rather than implemented — this phase treats any epoch mismatch between the rollback request and the target as a hard rejection, not an attempted reconciliation, since 135Q does not freeze the exact reconciliation mechanics and inventing one was out of this phase's bounded scope. A future phase must design that mechanism explicitly if cross-epoch rollback rehearsal is ever required.
- The concurrent-rollback-vs-forward race (F-135R-4) is resolved by construction (shared atomic-replace target file) but still has no dedicated concurrency stress test in this phase (matching 135R's own disclosed, Non-Blocking deferral of the equivalent forward-publication race) — a plausible, small, Stage 2 follow-on item, not required for 135U's own scope.

## 20. Stage 3 deferrals

No Stage 3 (authority cutover) implementation, design, or investigation occurred in this phase. No authority flag, authority-epoch semantics beyond "must remain legacy," or cutover mechanism was touched. `RehearsalConfiguration`'s existing fail-closed rejection of any Stage 3 flag is unmodified.

## 21. Final verdict

**VERIFIED WITH NON-BLOCKING FINDINGS.** Two CONFIRMED, Non-Blocking findings (F-135U-1, F-135U-2) were found by this phase's own independent adversarial test module and repaired within this same governed phase, before any regression suite was (re-)run for the record and before finalization. No Blocking defect survived to finalization: no production pointer/report/checkpoint/metadata/marker/receipt mutation, no notification dispatch, no rollback to an unverified or quarantined generation, no containment escape, no pointer split-brain, no silent uncertain replay, no accepted conflicting replay, no immutable-history rewrite, no authority leakage, no execution capability introduced, and no new regression was caused by this phase's changes (confirmed by the full regression table in §16, all passing at 100% on first fresh run).

**Explicit confirmations:**

- Legacy lifecycle remains the sole production authority. **Confirmed.**
- CLTR remains derivative. **Confirmed.**
- Rollback rehearsal affected only the non-authoritative rehearsal namespace. **Confirmed** (§7, §18).
- Rollback rehearsal did not roll back production lifecycle state. **Confirmed** (§10, §18 — no rollback evidence or CLI output claims a production effect was undone).
- No production phase report changed because of rollback rehearsal. **Confirmed.**
- No production completion metadata changed because of rollback rehearsal. **Confirmed.**
- No production Architecture Status changed because of rollback rehearsal. **Confirmed.**
- No production checkpoint changed because of rollback rehearsal. **Confirmed.**
- No production pointer changed because of rollback rehearsal. **Confirmed** (only the rehearsal-only `current-rehearsal` file is ever written by `publish_generation`).
- No external notification originated from rollback rehearsal. **Confirmed** (§18).
- No production marker changed because of rollback rehearsal. **Confirmed.**
- No production receipt changed because of rollback rehearsal. **Confirmed.**
- No immutable rehearsal generation was rewritten or deleted. **Confirmed** (§8).
- No Stage 3 implementation occurred. **Confirmed** (§20).
- No authority cutover occurred. **Confirmed.**
- No legacy authority was demoted. **Confirmed.**
- No legacy authority was retired. **Confirmed.**
- No execution capability was introduced. **Confirmed** (§18).
- Runtime remains Observed, maximum capability remains observe, execution availability remains unavailable. **Confirmed** (§18).

## 22. Recommended next phase

135Q/135R's own deferrals and this phase's own limitations (§19) point to two candidate next steps, neither of which this phase asserts as final: (a) a small, bounded follow-on closing the disclosed cross-epoch-rollback and concurrent-rollback-vs-forward-race gaps (§19), or (b) beginning the Stage 3 authority-cutover *readiness architecture* the prior track has been building toward since 135M — e.g. **135V — Stage 3 Authority-Cutover Readiness Architecture**. This is a design judgment for the next contract/planning phase to confirm against the full remaining 135M migration plan, not a scope this phase asserts as final.
