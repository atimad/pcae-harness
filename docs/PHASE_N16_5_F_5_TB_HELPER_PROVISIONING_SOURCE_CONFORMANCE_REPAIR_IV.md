# Phase 150D — N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR-IV

## Phase ID

`150D` (alias **N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR-IV**), a fresh short top-level CPIPC number (`pcae.core.phase_id` `is_valid` True, no collision against `git log --all`), sibling to `150A`/`150B`/`150C`. This is a fresh, independent governed phase with its own identity, entry baseline, tests, Fast Green attribution, and completion lifecycle — it does not reuse the held IV's evidence or reinterpret its conclusions as current.

## Topology / worktree proof

Rooted at `origin/main` == `caa155b6` (Phase 150C's own final pushed commit) in an isolated worktree/branch (`n16-5-f-5-tb-helper-provisioning-source-conformance-repair-iv`, at `/Users/atilamadai/repos/pcae-harness-150d`), not on local `main` (which carries 2 unpublished commits ahead of `origin/main`). Verified absent from this branch's ancestry, both before mutation and before push:

- held source-conformance IV commits: `6c7f5cf4`, `2b8ad2aa` — confirmed absent (`git merge-base --is-ancestor` returns false for both against this branch's HEAD).

Neither held commit is touched, cherry-picked, merged, rebased, or published by this phase. They were consulted only as read-only historical reference (`git -C ~/repos/pcae-harness show <sha>:<path>`) for test-idea reconciliation (§14 below); the fresh suite here is independently authored against current source, not copied.

## Mission

Independently re-verify — against current `origin/main` after Phases 150B and 150C — the previously completed provisioning source-conformance repair (removal of `configure_privileged_helper` and `configure_presentation_mechanism` from the helper's privileged mutation dispatch surface), which had never been independently re-verified after that removal (its own predecessor IV was blocked, and the held IV that attempted this re-verification was itself blocked pre-150C by an unrelated filename-length lifecycle defect and never completed/pushed).

This phase makes **no claim** of: helper admission repaired, foundation boundary repaired, N-16-5 closed, certification complete, real external effect enabled, or PB/runtime capability enabled.

## Contract state (read directly from `docs/contracts/`, not inferred from prose)

- **HPAC-PAWA-001 v4.0** — Status: FROZEN. §98 (REQ-345-352) requires `configure_privileged_helper` be dispatched only by a standalone deployment-owner script, never through the helper's `admin_mutation` boundary; REQ-352 records that a fresh independent IV (this phase) is expected to precede any such standalone script's implementation.
- **HPAC-PAWA-HELPER-001 v5.0** — Status: REPAIRED / FROZEN — PENDING INDEPENDENT RE-VERIFICATION (this phase resolves that pending status for the source-conformance property only). §30E (REQ-184-188) narrows the closed `admin_mutation` operation-params vocabulary by removing both forbidden operations.
- **HPAC-PPA-001 v2.1** — Status: FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING (for `configure_presentation_mechanism`'s own standalone path, which is unaffected by and outside this phase's scope). Byte-unchanged before/after this phase.

No drift found between these and the versions cited by prior phases' `PROJECT_STATUS.md` history. No contract file touched by this phase.

## Source-conformance verification (current source, independently reconstructed)

`src/pcae/core/hpac_pawa_helper_protocol.py`:
- `CLOSED_ADMIN_MUTATIONS` = exactly `{enroll_principal, revoke_principal, enroll_credential, revoke_credential, initialize_credential_sidecar_state}`. Both forbidden operations absent.
- `CLOSED_OPERATIONS` (helper operation vocabulary) = exactly 5 (`admin_mutation`, `certification_write`, `certification_read`, `ceremony_entry`, `presentation_evidence_write`), enforced by a module-level `assert len(CLOSED_OPERATIONS) == 5` and an exact-membership check in `dispatch()` before any authority is consulted.

`src/pcae/core/hpac_pawa_helper_store_adapter.py`:
- `perform_recognized_admin_mutation`'s dispatch chain has no branch for either forbidden operation; an unrecognized/excluded mutation falls through to `operation_scope_invalid`.

`src/pcae/core/hpac_pawa_helper_operations.py`:
- `handle_admin_mutation` rejects any mutation absent from `CLOSED_ADMIN_MUTATIONS` with `operation_scope_invalid` before authority evaluation.
- `mint_and_perform_admin_mutation` (the Model E facade) independently re-checks membership in `CLOSED_ADMIN_MUTATIONS` — a third, redundant fail-closed gate.

All three occurrences of the forbidden operation names inside these three files are comments/docstrings only, describing the exclusion — no executable reference.

### Tree-wide occurrence inventory

Every occurrence of `configure_privileged_helper` / `configure_presentation_mechanism` in the repository (128 grep hits) classifies into exactly three buckets, with **zero unexpected helper-reachable occurrences**:

1. Comment/docstring references inside the three helper-conformance files above, describing the exclusion.
2. The legitimate standalone path: `src/pcae/core/hpac_protected_presentation_admin.py`, `src/pcae/core/hpac_protected_admin_writer.py`, `src/pcae/core/protected_presentation_installation.py`, `scripts/hpac_protected_presentation_admin.py` — `configure_presentation_mechanism`'s real, standalone, PAWA/PPA-admin-only dispatch, untouched by this repair.
3. Test files (historical IV/contract/writer-authority suites plus this phase's own fresh suite) referencing the names as test literals.

No file outside these three buckets references either name.

## Standalone provisioning path

- `configure_presentation_mechanism`: fully implemented, live, standalone, contractually correct — untouched by this repair or this IV.
- `configure_privileged_helper`: **no standalone dispatch implementation exists yet.** `scripts/hpac_pawa_helper_admin.py` does not exist; `ProtectedPresentationInstallationStore.register_helper_metadata` (the nearest related write method) has zero production callers. This is the exact, disclosed, contractually-expected state per HPAC-PAWA-001 §98 REQ-352 ("fresh independent IV precedes implementation") — not an accidental capability deletion. Confirming the capability's absence outside the helper is correct; confirming it wasn't deleted from a legitimate location it never existed in is vacuously true and disclosed as such.

## Model E non-regression

Three sealed, `__slots__`-only authority classes (`HelperAdminMutationAuthority`, `HelperCertificationWriteAuthority`, `HelperPresentationEvidenceAuthority`) each require a private module-level seal object to construct; recognition uses `type(x) is ExactClass`, never `isinstance`, so no subclass or duck-typed forgery is accepted. No shared recognizable base class. No authority object is persisted or observed crossing an IPC boundary — each is constructed and consumed within a single call. Executable tests (in the fresh suite below) prove: exact forbidden operation, case/whitespace/null-byte variants, missing/unrecognized operation field, nested-parameter smuggling, unrecognized top-level fields, a forged duck-typed authority object of the wrong exact type, and cross-family (off-diagonal) dispatch all fail closed. The `CLOSED_OPERATIONS`/`CLOSED_ADMIN_MUTATIONS` exact-membership checks make reflection/dynamic-dispatch-table tampering unreachable through the public API surface exercised by tests.

## Foundation boundary non-regression

`src/pcae/core/hpac_foundation.py` and `_validate_production_boundary` are not among the three files this repair touched — zero diff overlap with the historical foundation defect (`N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL`'s still-open `hpac_foundation.py` configured-agent-vs-live-process write-boundary gap, which remains open and unaffected, and is **not** repaired or claimed repaired by this phase).

## Helper admission — exact current state (disclosed, not claimed repaired)

A genuine, pre-existing, disclosed gap was found and independently confirmed by direct source inspection (not merely by the delegated worker's report): `hpac_pawa_helper_os.authenticate_peer`'s `configured_agent` parameter defaults to Python `None` — despite its own docstring's claim that it "defaults to a live resolution via `resolve_configured_agent_identity`," the default is a literal `None`, and when `None`, the peer-uid-≠-configured-agent conjunct (`if agent_identity is not None and credential.uid == agent_identity.uid`) is silently skipped rather than resolved or failed closed. The sole production caller, `hpac_pawa_helper_launcher.py:141`, never supplies `configured_agent`, so this conjunct is not enforced in production today.

This gap is **unrelated to the provisioning source-conformance property under verification** — it does not touch `CLOSED_ADMIN_MUTATIONS`, dispatch of either forbidden operation, or Model E authority recognition — and per §12 of this phase's authorization, an unrelated admission defect does not invalidate this narrower repair unless it makes the source-conformance claim itself false. It does not. Helper admission is **not** claimed repaired by this or any prior phase in this chain; this finding is recorded here rather than fixed, and is a candidate for a future dedicated repair phase.

## Held-IV test reconciliation

The held commits (`6c7f5cf4`/`2b8ad2aa`, local-only on the primary operator's `main`, never on `origin/main`) were inspected read-only (`git show <sha>:<path>`, no checkout/merge/cherry-pick). Their suite's central assertions were written against the *pre-repair* defect state and are not directly reusable verbatim against current (post-repair) source. Equivalent and broader coverage was independently re-derived from current source and current contracts into the fresh suite below rather than reused literally.

## Fresh dedicated IV test suite

`tests/test_n16_5_f_5_tb_helper_provisioning_source_conformance_repair_iv.py` — 34 tests, independently authored against current source. Standalone run: **34 passed, 0 failed, 0 skipped.** Covers: central exclusion from `CLOSED_ADMIN_MUTATIONS`/`CLOSED_OPERATIONS`, the full occurrence inventory as an executable assertion, dispatch fail-closed behavior through `handle_admin_mutation`/`perform_recognized_admin_mutation`/`mint_and_perform_admin_mutation`, alias/case/whitespace/null-byte/nested-parameter attack variants, Model E cross-family (off-diagonal) rejection and exact-type (non-`isinstance`) recognition, standalone-path existence and exclusivity for `configure_presentation_mechanism`, foundation-file non-overlap, the helper-admission `configured_agent=None` gap (disclosed, not fixed), and a correctly historically-pinned (not current-HEAD-bound) contract-byte-identity check.

## Regression sweep

Combined keyword sweep (`provisioning|prov_repair|helper_iv|helper_writer_authority|helper_installation_identity|hpac_pawa_helper|n16_5_f5_tb_prov`): 44 failed / 944 passed with this phase's new test file present, vs. 42 failed / 912 passed without it (`git stash push -u` isolation). The only 2 new failures — both instances of `test_real_host_class_b_conformance_is_non_compliant_and_host_unchanged` — are a pre-commit-only test-isolation artifact: that test asserts `git status --short` shows only its own two hardcoded paths, and this phase's still-untracked new test file trips that narrow allowlist before being committed. Independently confirmed by reading the test body (`tests/test_phase_149o_20l_5_class_b_real_host_provisioning_authorization_and_planning.py`): the allowlist already covers `tasks/`, `.pcae/`, `PROJECT_STATUS.md`, `CHANGELOG.md` prefixes, so once this phase's own files are committed, `git status --short` returns clean and both instances pass again — reconfirmed post-commit below. Classification: environment-specific/test-isolation artifact, not candidate-attributable to the repair or to this phase's source content. The remaining 42 failures are identical by name to the pre-existing baseline (present with zero new files added) — stale current-HEAD-bound/version-pin assumptions unrelated to this repair, matching the disease class already documented and partially repaired by Phases 150B/150C elsewhere; out of this narrow IV's scope.

## Post-commit regression re-check

Post-commit (`fb1f0174`), the two `test_real_host_class_b_conformance_is_non_compliant_and_host_unchanged` instances flagged above as a pre-commit-only artifact were re-run standalone and both pass (`tests/test_phase_149o_20l_5_class_b_real_host_provisioning_authorization_and_planning.py`: 12/12 passed). The fresh IV suite was also re-run standalone post-commit: 34/34 passed. `git status --short` is clean at this point (before the task-scope-widening and commit-message-amend bookkeeping below).

## Fast Green

`pcae phase fast-green-attribution --phase-id 150D`, method `parent_of_oldest_phase_attributed_commit` (correctly derived from this phase's own commit subject, not caller-supplied): baseline `caa155b6` (== `origin/main`, Phase 150C's final pushed commit), candidate `fb1f0174` (this phase's own implementation commit, after amending its subject to the `Phase 150D: ...` format required for programmatic attribution — the amend was performed before push, on this phase's own single unpublished commit only). **`attributable_failures: []`.** 362 raw failures on the candidate vs. 361 on the baseline (the delta being this phase's own fresh 34-test file's collection, all passing, contributing zero failures); 370 failures excluded as preexisting. One `expected_phase_artifacts` prediction (`test_head_equals_origin_main`, predicted `local_only`) is expected and will resolve after this phase pushes. Artifact: `.pcae/fast-green-attribution/8a1428feef40ac0d9c47082ffe7c272789f227d2d859914d0fb105d1dd32bb29.json`.

Note on process: an earlier invocation of this command produced a degenerate, vacuous result (baseline collapsed to candidate HEAD, trivially yielding zero attributable failures) because the phase's first commit message did not match the tool's required `"Phase <ID>: ..."` subject pattern (the alias parenthetical was placed before the colon). That result was discarded and never treated as evidence; the commit subject was corrected and this section reflects the re-run against the correctly-derived baseline only.

## Production / contract delta

Zero `src/pcae/**` changes. Zero `docs/contracts/**` changes. Confirmed by `git diff --stat` against this phase's entry commit (`caa155b6`, `origin/main`) restricted to those paths.

## Runtime posture

Observed / observe / unavailable — unchanged throughout.

## N-16 state

N-16-5 remains **NOT CLOSED**: helper admission (documented gap above) and the separate, still-open foundation configured-agent-vs-live-process write-boundary gap (`N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL`) remain unresolved. This phase verifies only the narrower provisioning source-conformance property. N-16-6 and N-16-7: untouched.

## Held-commit final disposition

**A. HISTORICAL / SUPERSEDED.** The held commits' useful verification intent was freshly and independently reconstructed in this phase from current source and current contracts; the held commits themselves remain unpublished, are not merged/cherry-picked/rebased, and may be deleted later through a separate housekeeping decision the primary operator does not make here.

## Disposition

**COMPLETE — INDEPENDENTLY VERIFIED** (source-conformance property only; see explicit non-claims above).

Recommended next phase (not begun by this phase): a narrowly-scoped repair addressing the disclosed `hpac_pawa_helper_os.authenticate_peer` `configured_agent=None` admission gap (its docstring claims a live-resolution default that the code does not perform, and the sole production caller never supplies the parameter), independently derived as the most immediate remaining N-16-5 blocker from current source — not a guess at an exact CPIPC ID in advance. N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 untouched.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved as a durable governance rule for this phase: one delegated fork performed bounded inspection, executable dispatch/adversarial testing, and fresh-test-suite authorship only (§4-16 of this phase's authorization); it ran no `git commit`, `git push`, or `pcae task`/`pcae phase` lifecycle command. All lifecycle mutation, finalization, commit, and push in this phase were performed directly by the primary operator, who also independently re-verified the delegated worker's central claims (contract text, `CLOSED_ADMIN_MUTATIONS` contents, occurrence inventory, admission-gap source lines, and the fresh suite's pytest output) before relying on them.
