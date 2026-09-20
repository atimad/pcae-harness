# Phase 150C — PCAE-LIFECYCLE-FILENAME-LENGTH-HARDENING-R

## Phase ID

`150C` (alias **PCAE-LIFECYCLE-FILENAME-LENGTH-HARDENING-R**), a fresh short top-level CPIPC number (`pcae.core.phase_id` `is_valid` True, no collision against `git log --all`), sibling to `150A` (blocked) and `150B` (completed). This is a fresh governed phase with its own identity, entry baseline, implementation commits, tests, Fast Green attribution, and completion lifecycle -- it does not reinterpret or retroactively verify the original blocked 150A attempt.

## Topology / worktree proof

Rooted at `origin/main` == `2be6fe01` (the commit that landed Phase 150B) in an isolated worktree/branch (`n16-5-f-5-tb-pcae-lifecycle-filename-length-hardening-r`). Verified absent from this branch's ancestry, both before mutation and before push:

- held source-conformance IV: `6c7f5cf4`, `2b8ad2aa` — absent
- blocked original 150A attempt: `72cdba16`, `d0b2a75a` — absent

Neither is touched, cherry-picked, merged, rebased, or published by this phase. The old 150A branch (`recovery/pcae-lifecycle-filename-length-hardening`) was read-only reference material (`git show 72cdba16:...`), never merged.

## Defect reproduced (independently, against current origin/main)

`write_quarantined_report()` in `src/pcae/core/phase_reports.py` embeds a phase ID directly into a filename component. For 150B's own real rejected `.1`-extended candidate identity (one `.1` longer than 150B's actual `150B` alias), the resulting `.blocked.md`/`.blocked.json` basenames are 258/260 UTF-8 bytes -- over the 255-byte portable filesystem component limit -- reproducing:

```
OSError: [Errno 63] File name too long
```

live, on current `origin/main`, before any source change. `write_phase_report()`'s promoted-artifact path did not trip for this specific ID (223-byte payload leaves enough headroom under its shorter suffix), but is patched by the same shared primitive since it uses the identical unbounded-embedding pattern and a longer ID would trip it too (proven directly in the self-hosting acceptance test with a synthetic ID longer than the real one).

`create_task_contract()` in `src/pcae/core/tasks.py` has the identical defect: `relative_path = Path("tasks") / "active" / f"{task_id}.md"` embeds the full task ID (timestamp + slugified title) with no bound.

## Writer/reader symmetry audit (full call-site inventory)

Every phase-report reader (`read_latest_report`, `phase_report_identity` resolution, notification dispatch) reads via the **returned path** from the writer or via the fixed short `latest.md`/`latest.json` names -- never by reconstructing a phase-id-derived filename independently. Bounding only the writer is therefore sufficient; no reader needed a matching change.

Task lifecycle: `close_active_task()` (used by `pcae task close`, `pcae task complete`, `pcae task finish`) renames `active_task.path` -- the **actual discovered file**, found via `find_latest_active_task()`'s `glob("*.md")`, never reconstructed from `task_id` -- to `tasks/done/<same-basename>`. This is naturally symmetric with a bounded write and required no reader change.

**Known, narrower, pre-existing gap (documented, not fixed here, per this phase's own narrow scope):** the diagnostic `pcae doctor task-memory --repair` helpers (`_repair_active_status_in_done_folder`, `_repair_done_status_in_active`, `_repair_path_for_finding`) reconstruct `tasks/{active,done}/{task_id}.md` directly from a task ID extracted from a diagnostic message, rather than from a discovered file. For an overlong task ID whose file was written under a bounded (shortened) name, these reconstructed paths would not resolve. This is a distinct, secondary self-repair code path (not the primary create/close/finish lifecycle this phase's mandate covers), pre-existing before this phase, unaffected by it, and out of this phase's narrow scope (§8 of the phase authorization: "do not broaden beyond the naming lifecycle without evidence" is read here as "without evidence that the *primary* lifecycle requires it" -- the primary lifecycle does not). Flagged for a future phase if ever exercised against an overlong task ID.

## Design (Model: bounded deterministic UTF-8-safe suffix)

`src/pcae/core/filename_safety.py` (new): `bounded_filename_component(raw, *, extension, max_bytes=255)`.

- If `raw + extension` already fits in `max_bytes` UTF-8 bytes, returns `raw` unchanged (byte-for-byte backward compatible with every existing short filename).
- Otherwise returns `<UTF-8-safe-truncated-prefix>--<16-hex-char SHA-256 digest of the full untruncated raw>`, sized so `<result> + extension` fits within `max_bytes`.
- `MAX_FILENAME_COMPONENT_BYTES = 255` is a deterministic, portable constant (not host-derived via `os.pathconf`), so a given identity produces the identical filename on every supported host -- required by this repository's reproducibility invariants.
- The digest is a locator/collision-avoidance mechanism only; it confers no authority. The filename is never the source of truth: the full canonical identity is always recorded verbatim in the artifact's own content (`report.phase_id` in JSON/Markdown; the task's own `## Task ID` content section).
- `bounded_filename_component` deliberately does **not** sanitize path-unsafe characters (`/`, `\`, `..`) -- that remains each existing call site's own responsibility (`phase_reports._safe_filename`'s regex substitution; `tasks.slugify_title`'s ASCII-only slugification), verified end-to-end in tests.

Independently reviewed against the original blocked 150A patch (`git show 72cdba16`): the algorithm is materially identical (same digest scheme, same truncation approach, same 255-byte constant, same call sites). This phase's implementation was authored fresh, not cherry-picked, and independently re-verified rather than assumed correct; the two converging on the same design is corroborating evidence the model is sound, not evidence of copying.

## Production changes

- `src/pcae/core/filename_safety.py` (new)
- `src/pcae/core/phase_reports.py`: `write_phase_report()` and `write_quarantined_report()` route their basename through the new `_bounded_report_base()` helper before appending extensions.
- `src/pcae/core/tasks.py`: `create_task_contract()` routes its file stem through `bounded_filename_component()` before writing.

No other production file touched. `docs/contracts/**`: 0 changes. HPAC helper protocol/store-adapter/operations files: 0 changes. PB/runtime/POL/deployment/packaging/release files: 0 changes.

## Fresh tests

`tests/test_n16_5_f_5_tb_pcae_lifecycle_filename_length_hardening_r.py` (30 tests, all passing) covers: short-name byte-identity, exact-limit boundary, one-byte-over boundary, the real historically-blocked ID becoming safe, a UTF-8/Unicode matrix (Serbian Latin+combining, accented Latin, Cyrillic, CJK, emoji, stacked combining marks, mixed scripts) asserted by **byte** length not character count, `_truncate_utf8` never splitting a code point, determinism, shared-prefix collision resistance, distinct-digest-suffix proof, extension preservation across all four report extensions, path-traversal-safety of the real production composition (`_safe_filename` then bound), quarantine + promoted report writer/reader round trips with full phase-ID content-fidelity, a direct reproduction that the *old* unbounded basename still overflows (proving the fix isn't vacuous), full task create→lookup→finish→done round trip with a 500+ character title, full identity/title retained in the done-file content, historical short report/task names completely unaffected, Phase 150B's two repaired stale assertions re-run and confirmed still green after this phase's own `src/pcae/**` edits, held/blocked-commit ancestry absence, and production-diff confinement to the three expected files.

## Self-hosting acceptance (§20)

Exercised directly (not merely via the test suite) with a synthetic phase identity *longer* than the real historically-blocked one (243 bytes vs. 223) and a synthetic task title built from it: task create, lookup (full title/ID recovered), close/move to done, phase-report promoted write, phase-report quarantine write -- all succeeded, zero `ENAMETOOLONG`, full canonical identity recovered from every written artifact's content. Did not touch or activate the held IV.

## Regressions

Full `report|task|bootstrap|session_reporting|transition_valid` keyword sweep: 20 failed / 2676 passed / 7 skipped, identical failure set (by name) to a `git stash -u`-isolated pre-edit baseline (20 failed / 2667 passed / 7 skipped -- the 9-test delta is exactly this phase's own new suite intersecting the keyword filter). Zero new failures, zero regressions. Targeted suite (`test_phase_reports*.py` + `test_task*.py` + both 150B stale-assertion-repair test files): 384/384 passed.

## Disposition

**COMPLETE — LIFECYCLE FILENAME-LENGTH HARDENING VERIFIED.**

Recommended next (not begun by this phase): reconcile/resume the held `N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR-IV` (commits `6c7f5cf4`, `2b8ad2aa`), now that this phase has landed on `origin/main` and the filename-length limitation that motivated holding it no longer applies to a `.1`-style successor identity. N-16-5 remains **NOT CLOSED**. N-16-6/N-16-7 untouched. Runtime remains Observed / observe / unavailable.

150A disposition preserved as historical evidence: blocked solely by the two now-repaired (Phase 150B) stale Fast Green assertions, not by any defect in its own implementation; its production diff was technically sound reference material, independently reviewed and independently re-derived (not cherry-picked) here. 150A itself is **not** retroactively marked VERIFIED by this phase's success -- this is a new, independent phase that re-establishes the same fix against the current canonical baseline.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved as historical governance evidence from a predecessor phase; not retroactively authorized, amended, erased, or normalized by this phase.
