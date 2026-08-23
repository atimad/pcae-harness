# Phase 149O.20L.7O.2S.4 — FGSC-001 Staleness Carve-Out / Attribution Completeness Narrow Repair

## Verdict

**REPAIRED — INDEPENDENT VERIFICATION PENDING**

The Blocking finding from 149O.20L.7O.2S.3 (structured Fast Green
Self-Certification Lifecycle Implementation Independent Verification) is
repaired by this phase. No other FGSC-001 semantics, bucket arithmetic,
scalar Fast Green behavior, or Stage B mechanism was changed. Real
S22.1/S22.2 self-hosting acceptance remains not authorized until an
independent verification phase (149O.20L.7O.2S.5, recommended below)
closes this finding.

## 1. True phase-entry commit

- HEAD at phase entry: `b9b83c28653d8068440e345aca796809a0429ecb`
  (`Phase 149O.20L.7O.2S.3: sync origin_main_head to final post-push
  literal value`).
- `origin/main`: identical (confirmed via `git fetch origin main` before
  starting).

## 2. Vulnerable pre-repair checkpoint

`b9b83c28` (phase-entry HEAD, above) is itself the vulnerable checkpoint —
the defect was present in the 149O.20L.7O.2S.2 implementation commit
`d911ebb9` and remained unrepaired through all of 2S.3 (a verification-only
phase; no production source changed).

## 3. Exact Blocking finding (from 2S.3)

`validate_structured_fast_green()`
(`src/pcae/core/fast_green_attribution.py`) computed the freshness
(staleness) check **before** independently recomputing
`attributable_failures` and the conservation/bucket-membership checks, and
contained an internal `if issues: return issues` guard between the
`expected_phase_artifacts` loop and the "Conservation" section. That guard
fired as soon as *any* issue had accumulated — including the staleness
issue itself, appended earlier in the function. Since routine
post-checkpoint finalization commits (PROJECT_STATUS.md, CHANGELOG.md,
`.pcae/phase-completion-*` updates — the entire premise FGSC-001 exists to
forgive) always produce staleness, the function could return a "staleness
only" issue list to `validate_derived_correctness()` (`phase_reports.py`)
*before* attribution/conservation had ever executed. FGSC-001's carve-out
(`phase_reports.py`, `validate_derived_correctness()`) trusts a
"staleness only" result as proof nothing else is wrong; an artifact
combining an allowed finalization delta with a genuine, unclassified
regression could therefore reach `FINALIZATION_VERIFIED` undetected.

## 4. Independent pre-repair reproduction

Reproduced directly (not from 2S.3's prose) via the pre-existing 2S.3
regression tests
(`tests/test_phase_149o_20l_7o_2s_3_fgsc_001_lifecycle_independent_verification.py::TestStalenessCarveOutSoundness`),
run unmodified against phase-entry HEAD before any repair:

- `test_validate_structured_fast_green_skips_attribution_recompute_once_stale`:
  confirmed the injected regression (`raw_failed` extended with an
  unclassified node) is caught by `validate_structured_fast_green()` when
  the evidence is fresh, but silently disappears from the returned issue
  list once one ordinary finalization commit makes the evidence stale.
- `test_carve_out_certifies_finalization_verified_despite_hidden_regression`:
  confirmed the same tampered evidence reaches
  `validate_derived_correctness()` (the real `pcae phase complete` gate)
  with `issues == []` and `report.metadata["fgsc_lifecycle_state"] ==
  "FINALIZATION_VERIFIED"`, at phase-entry HEAD.

Both tests asserted the *buggy* (accepting) behavior before this phase's
repair and now assert the *corrected* (rejecting) behavior — flipped as
part of this repair, per their own embedded "promote to a plain
correctness assertion" instruction.

## 5. Root cause

Ordering only. `validate_structured_fast_green()`'s freshness check ran
early in the function body and merely appended to the shared `issues`
list rather than returning immediately — but a later, unrelated
early-return guard (`if issues: return issues`, immediately before the
Conservation section) treated *any* non-empty `issues` list, including one
containing only the harmless staleness entry, as cause to stop before
computing `attributable_computed` and the final nonzero-attributable
check. No arithmetic, bucket definition, or trust boundary was wrong —
only the sequencing of when the freshness issue was allowed to be visible
relative to the rest of the function's own control flow.

## 6. Repair strategy chosen

**Option A** (of the two identified in the handoff): keep one authoritative
validator (`validate_structured_fast_green()`), and reorder its internal
checks so independent attribution/conservation recomputation always
executes before the freshness check is even evaluated. Concretely: the
freshness block (`current_head()` call, `candidate_commit` equality check,
staleness issue append) was moved from immediately after the
provenance/digest checks to immediately before the function's final
`return issues` — i.e., strictly after the nonzero-`attributable_failures`
check. No other line changed; no new function, no new module.

### Rejected alternative — Option B

Option B (keep `validate_structured_fast_green()` unchanged; make the
FGSC-001 caller in `phase_reports.py` independently re-invoke the
attributable/conservation recomputation itself before trusting "sole
staleness") was rejected: it would duplicate security-critical attribution
arithmetic in a second location (`phase_reports.py`), directly
contradicting the "avoids duplicated security-critical arithmetic" and
"preserves one authoritative validation implementation" preferences in the
handoff, for no benefit — Option A achieves the identical guarantee with a
strictly smaller, single-file diff and zero new call-site coupling.

## 7. Exact production diff

`src/pcae/core/fast_green_attribution.py` — one contiguous block (the
freshness check, ~13 lines including its `try`/`except`) relocated within
`validate_structured_fast_green()`. Removed from directly after the
provenance/digest/inline-field checks (previously immediately before the
"Baseline authority" comment); re-inserted directly before the function's
final `return issues`, after the nonzero-`attributable_failures` check,
with an expanded comment explaining why the ordering is now
security-relevant. No other function, no other file's production source,
changed.

```diff
--- a/src/pcae/core/fast_green_attribution.py
+++ b/src/pcae/core/fast_green_attribution.py
@@ evidence = persisted section @@
     evidence = persisted

-    # Freshness (2Q.1 §10).
-    try:
-        actual_head = current_head(repo_root)
-    except AttributionError as exc:
-        issues.append(f"could not determine current HEAD to check freshness: {exc}")
-        return issues
-    if evidence.get("candidate_commit") != actual_head:
-        issues.append(
-            f"structured fast_green evidence is stale — candidate_commit "
-            f"{evidence.get('candidate_commit')!r} != current HEAD {actual_head!r}"
-        )
-
     # Baseline authority (2Q.1 §9).
@@ end of function, after the nonzero-attributable_failures check @@
     if attributable_computed:
         issues.append(
             "structured fast_green has nonzero attributable_failures — "
             f"{attributable_computed!r} — cannot certify complete"
         )

+    # Freshness (2Q.1 §10) — deliberately checked *last* ... [explanatory
+    # comment; see live source]
+    try:
+        actual_head = current_head(repo_root)
+    except AttributionError as exc:
+        issues.append(f"could not determine current HEAD to check freshness: {exc}")
+        return issues
+    if evidence.get("candidate_commit") != actual_head:
+        issues.append(
+            f"structured fast_green evidence is stale — candidate_commit "
+            f"{evidence.get('candidate_commit')!r} != current HEAD {actual_head!r}"
+        )
+
     return issues
```

## 8. Early-return audit

Every early return (`return issues`) inside `validate_structured_fast_green()`
was inspected and classified against whether it can occur before
attribution/conservation recomputation:

| Location | Trigger | Before attribution recompute? | Filtered by FGSC carve-out? | Action |
|---|---|---|---|---|
| Missing required keys | malformed input | yes | no (message doesn't match `"...is stale"` prefix) | left as-is — always blocks unconditionally regardless of ordering |
| Provenance not an object / missing path+digest | malformed input | yes | no | left as-is |
| Artifact path escapes repo root | malformed input | yes | no | left as-is |
| Artifact file missing / unreadable | malformed input | yes | no | left as-is |
| Digest mismatch | tamper detected | yes | no | left as-is |
| Inline field diverges from artifact | tamper detected | yes | no | left as-is |
| Could not derive baseline (git failure) | fatal | yes | no | left as-is |
| baseline/errors not lists | malformed input | yes | no | left as-is |
| raw_failed/errors not lists | malformed input | yes | no | left as-is |
| preexisting_claimed not a list | malformed input | yes | no | left as-is |
| environment_claimed not a list | malformed input | yes | no | left as-is |
| expected_claimed not a list | malformed input | yes | no | left as-is |
| `if issues: return issues` (post-bucket-loops, pre-Conservation) | any accumulated issue (baseline mismatch, command mismatch, duplicate node, malformed bucket entry, etc.) | yes, by construction | **no** — none of these messages start with `"structured fast_green evidence is stale"` | left as-is — safe because the carve-out only special-cases the exact staleness-prefixed message; any other issue text always propagates to `other_issues` and blocks unconditionally, independent of when it was computed |
| attributable_claimed not a list | malformed input | n/a (attributable_computed already computed by this point) | no | left as-is |
| `if issues: return issues` (post-conservation) | bucket overlap / attributable mismatch / unknown node | no — occurs *after* attribution/conservation | no | left as-is |
| ~~Freshness — could not determine HEAD (git failure)~~ **relocated** | fatal | **now occurs last, after** attribution/conservation | message doesn't match the stale-prefix filter (different text) so never carve-out-eligible anyway, but ordering fixed for consistency with the rest of this audit | **fixed by this repair** |
| ~~Freshness — staleness detected~~ **relocated** | staleness | **now occurs last, after** attribution/conservation | **yes** — this is the exact issue the carve-out inspects | **fixed by this repair** (this was the Blocking defect) |

**Conclusion**: only the freshness check itself needed to move. Every
other early return either (a) produces an issue message the carve-out
never treats as staleness-only-eligible, so its *timing* relative to
attribution recomputation was never security-relevant, or (b) already
occurs after attribution/conservation. The general ordering did not need
to be rewritten — the single relocation in §7 is sufficient and complete.

## 9. Validation ordering after repair

1. Required-key presence.
2. Provenance object shape.
3. Artifact path safety + existence.
4. Artifact digest recomputation and match.
5. Inline-field-vs-artifact equality.
6. Baseline authority (git-derived `derive_phase_entry_baseline()` match).
7. Command equivalence.
8. Baseline/raw result-set shape + duplicate/overlap checks.
9. Independent preexisting recomputation (`raw_set & baseline_set`) vs.
   claimed bucket.
10. Environment-exclusion bucket validation (shape, bound, per-entry
    fields).
11. Expected-artifact bucket validation (shape, closed test identity,
    pushed_status consistency).
12. Conservation: bucket-membership disjointness.
13. Independent attributable recomputation
    (`raw_set - all_classified`) vs. claimed bucket.
14. Unknown-node-in-buckets check.
15. Nonzero-attributable-failures check (unconditional block).
16. **Freshness (candidate_commit vs. current HEAD).**
17. Return complete issue set.

This differs from the handoff's suggested reference ordering (§7 of the
handoff) only in that conservation/attributable recomputation (steps
12-14) here necessarily follow the bucket-shape validations (9-11) they
depend on, and freshness is last rather than 7th — both deviations required
by data dependencies and by the completeness property this repair
establishes, respectively. Fail-fast behavior for genuinely fatal/malformed
input (steps 1-8) is unchanged and still short-circuits immediately.

## 10. Issue-completeness semantics

Before this repair, callers could not assume `validate_structured_fast_green()`
returns *all* relevant issues — only "enough to reject" in the common case,
except when staleness was the first-computed issue, in which case even
that weaker guarantee failed for the FGSC-001 caller's specific purpose.
After this repair: whenever the returned issue list's only entry is the
staleness message, that is now sound proof every other check ran to
completion and passed. This repair does not claim a stronger blanket
"always returns literally every issue" guarantee for every possible input
combination (e.g., malformed-input early returns in §8's table still
short-circuit before some checks) — it only strengthens the one guarantee
FGSC-001's carve-out actually depends on. No new API was introduced (per
the handoff's item 8, only if it "improves correctness and avoids
duplicating trust logic" — it does not here; the existing function already
suffices once correctly ordered).

## 11. Carve-out precondition (frozen)

The FGSC-001 staleness carve-out in `validate_derived_correctness()` is
eligible iff `validate_structured_fast_green()` returns an issue list whose
**only** entry starts with `"structured fast_green evidence is stale"`.
After this repair, reaching that state requires (in order, all of):
required keys present; provenance/digest/inline-field integrity intact;
baseline authority match; command equivalence; well-formed raw/baseline
result sets with no internal duplicates/overlap; independently recomputed
`excluded_preexisting_failures` exactly matching the claimed bucket;
well-formed, bound-respecting `excluded_environment_failures`; well-formed,
identity-restricted `expected_phase_artifacts`; zero bucket-membership
overlap; independently recomputed `attributable_failures` exactly matching
the claimed bucket and containing zero entries; and no unknown node IDs in
any bucket. Only then is staleness itself evaluated. This is exactly
condition 1 of the handoff's item 9, expressed as code ordering rather than
a second boolean flag — no `filter(issue != stale)` pattern exists
anywhere in the implementation (there never was one to begin with; the
defect was purely about *when* the staleness issue could appear, not about
filtering it out incorrectly).

## 12. Original vulnerable-case post-repair result

`TestStalenessCarveOutSoundness::test_validate_structured_fast_green_skips_attribution_recompute_once_stale`
and `::test_carve_out_certifies_finalization_verified_despite_hidden_regression`
(`tests/test_phase_149o_20l_7o_2s_3_..._verification.py`), flipped from
documented-defect assertions to correctness assertions in this phase:

- Low-level validator: the injected regression now remains visible
  (`attributable_failures does not match the recomputed default set`)
  even once the evidence is also stale.
- Real gate (`validate_derived_correctness`): `issues` now contains the
  attribution-mismatch message; `report.metadata["fgsc_lifecycle_state"]`
  is never set to `FINALIZATION_VERIFIED`.

Both **REJECTED**, as required.

## 13. Valid sole-staleness result

`test_phase_149o_20l_7o_2s_2_fgsc_001_lifecycle_implementation.py::TestLifecycleFreshnessIntegration::test_finalization_delta_after_checkpoint_accepted`
(pre-existing, unmodified) still passes: a genuinely otherwise-valid
artifact whose only issue is candidate/current-HEAD mismatch, with an
allowed Class-B finalization delta, still reaches
`FINALIZATION_VERIFIED`. **PASS**, as required — the repair does not
disable FGSC-001's purpose.

## 14. Valid raw-nonzero case

New test
(`tests/test_phase_149o_20l_7o_2s_4_fgsc_001_staleness_carveout_repair.py::TestValidStalenessCasesStillPass::test_nonzero_raw_fully_preexisting_and_stale_still_passes`):
nonzero raw failures, all genuinely pre-existing (present in both baseline
and candidate raw sets, correctly excluded), zero independently
recomputed attributable failures, staleness present only via an allowed
finalization delta. **PASS / FINALIZATION_VERIFIED**, as required.

## 15. Staleness + attributable regression result

Covered by §12 above (the original 2S.3 finding) — **REJECTED**.

## 16. Staleness + omitted-node result

New test `test_staleness_plus_omitted_node_rejected`: one correctly
excluded pre-existing node plus one raw failure omitted from every
bucket (falsely absent from `attributable_failures`). **REJECTED**
(`attributable_failures does not match the recomputed default set`).

## 17. Staleness + duplicate result

New test `test_staleness_plus_cross_bucket_duplicate_rejected`: the same
node ID claimed in both `excluded_preexisting_failures` and
`excluded_environment_failures`. **REJECTED**
(`bucket membership overlaps`).

## 18. Staleness + forged-preexisting result

New test `test_staleness_plus_forged_preexisting_label_rejected`: a
genuine candidate-only failure (absent from `baseline_raw_failed`) falsely
labeled `excluded_preexisting_failures`. **REJECTED**
(`excluded_preexisting_failures does not match the recomputed
baseline∩candidate node-ID set`) — independent recomputation, not the
claimed label, governs.

## 19. Staleness + environment-abuse result

New test `test_staleness_plus_environment_bound_abuse_rejected`: four
`excluded_environment_failures` entries (exceeding the frozen
`ENVIRONMENT_EXCLUSION_BOUND=3`, unaltered by this phase). **REJECTED**
(`exceeds the bounded policy`). A single, structurally well-formed forged
environment-rerun entry is a pre-existing, carried, Non-Blocking trust
concern (2R.1 "environment-timeout exclusion weakness", §28 below) that
this narrow repair does not claim to close and does not touch; this test
exercises the bound the handoff explicitly required left unaltered, and
confirms it is not weakened by staleness.

## 20. Staleness + expected-artifact-abuse result

New test `test_staleness_plus_expected_artifact_abuse_rejected`: an
arbitrary failing node (not the closed `test_head_equals_origin_main`
identity) falsely labeled `expected_phase_artifacts`. **REJECTED**
(`does not match the closed test identity`).

## 21. Scalar compatibility

No line in `_fast_green_failure_signal()` or its call site in
`validate_derived_correctness()` was touched. `tests/test_88n5_fast_green_validation.py`
(scalar-path suite) passes unmodified, byte-for-byte identical assertions.

## 22. Structured non-FGSC strictness

`test_phase_149o_20l_7o_2s_2_..._implementation.py::TestLifecycleFreshnessIntegration::test_forbidden_change_after_checkpoint_still_blocks_completion`
and `test_stage_b_failure_blocks_completion_even_with_clean_delta`
(pre-existing, unmodified) still pass: a stale candidate combined with a
forbidden (Class A) post-checkpoint change, or a Stage B focused-check
failure, still blocks completion unconditionally — staleness never
becomes a global "ignore freshness" switch.

## 23. FGSC path (Class A/B) regression

All of `tests/test_phase_149o_20l_7o_2s_2_..._implementation.py`'s
`TestPathClassification` and `TestDiffAuthority` classes (path
classification, mode-based forcing, merge-commit rejection, rename
handling) pass unmodified — `classify_finalization_path()` and
`diff_authority_issues()` were not touched by this repair.

## 24. Stage B behavior

`run_stage_b_focused_checks()` was not touched. Its three pre-existing
tests (`TestStageBFocusedChecks`) pass unmodified.

## 25. Stage B recursion safety

`TestPushTrustBoundaryAndRecursionSafety` (2S.3 suite, unmodified) still
passes: `pcae.commands.push` carries no `fast_green_attribution`/`fgsc`
reference; `pcae.core.check`/`status`/`tasks` carry no
`validate_derived_correctness`/`finalization_transaction` reference. No
validator → Stage B → validator cycle was introduced (no code path in
this repair calls into Stage B or vice versa; the relocated block only
calls `current_head()`, already called elsewhere in the same function).

## 26. Report consistency behavior

No diagnostic outside `validate_derived_correctness()`'s own FGSC-001
branch invokes the carve-out or `validate_structured_fast_green()`
directly; `pcae phase-report consistency`'s own checks are unrelated to
this code path (confirmed by grep — no reference to
`fast_green_attribution` or `validate_structured_fast_green` outside
`phase_reports.py` and its own test files).

## 27. Finalization trust path

Traced: `validate_derived_correctness()` is the only caller of
`validate_structured_fast_green()` in the FGSC-001 lifecycle path, and it
is the function `pcae phase complete` invokes (transitively, via the
transition validator) before writing `fgsc_lifecycle_state` into
`report.metadata`. §12's repaired-rejection result at that exact call site
proves the vulnerable artifact can no longer reach canonical promotion.

## 28. Push trust boundary

Unchanged. `pcae.commands.push` (`push.py`) still carries no reference to
`fast_green_attribution` or FGSC by name (confirmed, §25). No structured
Fast Green logic was added to push.py.

## 29. Carried findings

Unchanged, not repaired in this phase: N1 (overbroad `docs/contracts/**`
digest-binding citation), N2 ("class C" naming inconsistency), N3
(push-correction-loop termination bound empirically rather than
structurally), 2R.1 raw-content artifact trust boundary, 2R.1
environment-timeout exclusion weakness, 2R.1 commit-message-based baseline
authority, 2R.1 artifact retention observation.

## 30. 2S.3 finding disposition

Blocking staleness-carve-out / incomplete-validation finding:

**REPAIRED — INDEPENDENT VERIFICATION PENDING.**

Not marked independently closed in this repair phase, per instruction.

## 31. HMIC / trust-scope result

Only one production file changed (`src/pcae/core/fast_green_attribution.py`),
already within the trusted/HMIC source set established by 2Q/2Q.1/2R/2S.2.
No new module or file was introduced into any authority-bearing scope.

## 32. Focused tests

New file: `tests/test_phase_149o_20l_7o_2s_4_fgsc_001_staleness_carveout_repair.py`
(6 tests: 1 valid-nonzero-raw-pass case, 5 staleness-plus-other-defect
rejection cases). All pass.

## 33. Existing suite regressions

Full run of the directly relevant suites after the repair:

```
tests/test_phase_149o_20l_7o_2s_4_fgsc_001_staleness_carveout_repair.py   6 passed
tests/test_phase_149o_20l_7o_2s_3_fgsc_001_lifecycle_independent_verification.py   9 passed (2 flipped, documented above)
tests/test_phase_149o_20l_7o_2s_2_fgsc_001_lifecycle_implementation.py   passed
tests/test_phase_149o_20l_7o_2s_1_independent_verification.py   passed (1 line-citation test updated — see below)
tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py   passed
tests/test_88n5_fast_green_validation.py   passed
118 passed total, 0 failed
```

Also run, unaffected: `tests/test_architecture_status_generation_repair_134e8.py`,
`tests/test_completed_phase_architecture_transition_134e10_1v_1.py`,
`tests/test_phase_149o_20l_7o_2r_1_independent_verification.py`,
`tests/test_phase_reports.py`, `tests/test_report_consistency_derived_correctness_134e9.py`
— all pass.

`tests/test_phase_id_repository_wide_conformance.py` has 2 pre-existing
failures, reproduced identically via `git stash` against unmodified
phase-entry HEAD (confirmed before attributing anything to this repair) —
unrelated to `fast_green_attribution.py`/`phase_reports.py`, not touched
or claimed fixed by this phase.

One pre-existing test required updating because this repair directly moved
the code it cites by line number:
`tests/test_phase_149o_20l_7o_2s_1_independent_verification.py::test_freshness_check_line_citation_matches_live_source`
hardcoded the freshness check's line span (586-589); updated to its new
location (789-796) with an explanatory docstring update. This is not a
weakening of the test's assertions — it still requires `candidate_commit`,
`actual_head`, and `stale` to co-occur in the cited block of live source.

## 34. Controlled Fast Green result

A single controlled baseline-vs-candidate comparison was used for this
phase's own completion evidence (see `.pcae/fast-green-attribution/` and
`.pcae/phase-completion-metadata.json`); no exploratory repeated loops were
run for literal green. Raw candidate, baseline, and attributable results
are reported separately in the metadata/report per convention — see
`.pcae/phase-completion-metadata.json`'s `validation_results` for this
phase's exact figures.

## 35. Reporting push-state consistency result

This phase's own canonical report and metadata are written to be
internally consistent at each stage (staged-pending-push vs. promoted)
per `project_phase_completion_procedure.md`'s exact-literal-string
discipline; no "Pushed: pushed" / "push itself deferred" prose mismatch of
the kind flagged in 2S.3 is introduced here. The 2S.3 report's own
mismatch was not rewritten (no governance requirement to do so found; it
is stale prose carried into an already-promoted historical report, not
reproducible from current canonical/history state, and rewriting a
promoted historical report for cosmetic cleanup is out of this phase's
narrow scope).

## 36. Proof no S22

No S22.1/S22.2 test, fixture, or self-hosting acceptance scenario was
created or run in this phase. `grep -ri "s22"` across this phase's changed
files returns no hits outside this document's own prose.

## 37. Proof 2P untouched

`git log` shows no commit in this phase referencing or touching Phase
149O.20L.7O.2P's commits, metadata, or reconciliation state. No file under
any 2P-specific path was read, written, or reasoned about beyond the
handoff's own instruction not to.

## 38. Runtime unchanged

No file under `src/pcae/runtime/**`, `src/pcae/orchestration/**`, or any
HATP/WebAuthn module was touched.

## 39. Commits / pushed / origin comparison

Recorded at phase completion time — see `.pcae/phase-completion-metadata.json`
`phase_commits` and this document's final revision for the exact commit
hash(es), `pushed_status`, and `origin/main..HEAD` count.

## 40. Recommended next phase

**149O.20L.7O.2S.5 — FGSC-001 Staleness Carve-Out Attribution Completeness
Repair Independent Verification.**

Only after 2S.5 independently closes the Blocking finding may a real
S22.1/S22.2 self-hosting acceptance phase be scheduled. Phase
149O.20L.7O.2P reconciliation remains gated behind that outcome,
unchanged from the 2S.3 handoff's own instruction.
