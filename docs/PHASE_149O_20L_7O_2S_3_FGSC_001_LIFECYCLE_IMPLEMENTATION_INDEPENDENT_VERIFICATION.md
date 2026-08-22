# Phase 149O.20L.7O.2S.3 — FGSC-001 Structured Fast Green Self-Certification Lifecycle Implementation Independent Verification

## Verdict

**C — NOT VERIFIED — STALENESS CARVE-OUT DEFECT (BLOCKING)**

The 149O.20L.7O.2S.2 implementation of FGSC-001 v1.0 is **not** independently
verified. One Blocking defect was found in the staleness carve-out
(§8 below). Path classification, diff authority, merge/history-rewrite
rejection, Stage B recursion safety, the push trust boundary, and the
(compact) lifecycle-state representation were all independently attacked
and held. Real S22.1/S22.2 self-hosting acceptance MUST NOT proceed until
this defect is repaired (in a future governed phase — not this one) and
re-verified.

This verification phase itself completes normally: its deliverable is the
verification judgment, not a passing FGSC-001. No production source was
modified. No finding was repaired.

## 1. True phase entry

- HEAD at phase entry / at time of this report: `36f2347f4ecf49ab51f69df765b00873120bc55f`.
- `origin/main`: `36f2347f4ecf49ab51f69df765b00873120bc55f` (identical — confirmed via `git fetch origin main` before starting).
- True 2S.3 phase-entry commit: `36f2347f` (repo was clean, nothing to push, at bootstrap).
- Exact 2S.2 implementation commit range: `123a6750..36f2347f` (8 commits, listed below); the single behavior-affecting production commit is `d911ebb9`.
- FGSC-001 contract blob being implemented: `docs/contracts/FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md` at commit `60a0a11b` (frozen by 149O.20L.7O.2S; unchanged since, confirmed no 2S.2 commit touches `docs/contracts/**`).

```
36f2347f Phase 149O.20L.7O.2S.2: sync origin_main_head to final post-push literal value
1219a26e Phase 149O.20L.7O.2S.2: fix phase-completion-metadata.json trust fields (no_go count, predicted pushed_status)
8c9c40cb Phase 149O.20L.7O.2S.2: sync active task allowed-file list
9e4fffe8 Phase 149O.20L.7O.2S.2: sync canonical phase-completion metadata and report
2033d3cd Phase 149O.20L.7O.2S.2: remove superseded active task file
4f4493ff Phase 149O.20L.7O.2S.2: close out task lifecycle, open idle placeholder
4e049c6e Phase 149O.20L.7O.2S.2: update PROJECT_STATUS.md and CHANGELOG.md
d911ebb9 Phase 149O.20L.7O.2S.2: FGSC-001 Structured Fast Green Self-Certification Lifecycle Implementation
```

## 2. Fixed pre-2S.2 checkpoint

`123a6750` (HEAD immediately before `d911ebb9`; parent of the first — and
only — commit whose subject is attributed to phase `149O.20L.7O.2S.2`, per
`derive_phase_entry_baseline()`'s own rule, independently applied by hand
here). This document does not rely on the 2S.2 phase report's own prose for
this fact — derived directly from `git log --reverse` against the real
repository.

## 3. Production diff reconstruction

`git show --stat d911ebb9` — exactly 4 files, 1211 insertions, 1 deletion,
all additive except one integration edit:

- `docs/PHASE_149O_20L_7O_2S_2_...IMPLEMENTATION.md` (new, prose only).
- `src/pcae/core/fast_green_attribution.py` (+223, purely additive — new
  `FGSC-001` section appended at the bottom of the file; `git show` confirms
  zero deleted/modified lines in the pre-existing Stage-A validator code
  above it).
- `src/pcae/core/phase_reports.py` (+115/-1) — the one integration point:
  adds `run_stage_b_focused_checks()` and rewires the structured-`fast_green`
  branch of `validate_derived_correctness()` to intercept a staleness-only
  issue list and attempt the FGSC-001 carve-out (full diff inspected
  directly, reproduced in §8 below).
- `tests/test_phase_149o_20l_7o_2s_2_..._IMPLEMENTATION.py` (new, +380).

No unexpected production file, no `docs/contracts/**` modification, no
`tests/**` modification outside the one new file, no HATP/WebAuthn-related
file anywhere in the diff (confirmed by the file list itself — none of the
four paths are under any HATP/WebAuthn/HMIC-authority scope).

## 4. Contract-to-code trace

| Contract requirement | Status |
|---|---|
| §3 checkpoint = existing `candidate_commit`, no new freeze mechanism | Fully implemented — confirmed no new "freeze" API exists; checkpoint is read straight from the evidence artifact's own `candidate_commit`. |
| §4 path classification (Class A/B, fail-closed unknown) | Fully implemented — `classify_finalization_path()`, independently reconstructed and attacked, see §14 below. |
| §6/§7 diff authority (mechanical, merge/rewrite rejection) | Fully implemented — `diff_authority_issues()` / `check_finalization_delta()`, attacked in §12/§13/§25-27 below. |
| §8 Stage B focused checks | Fully implemented for `pcae check`, `pcae status coherence`, `pcae doctor task-memory`. **Represented elsewhere**: `pcae push check` and `pcae phase-report consistency` are deliberately *not* duplicated in-process (documented, reasoned rationale in the function's own docstring: architecture-layering policy plus "already covered by the separate governed `pcae push check` step"). This matches contract §8's own text, which lists `pcae push check` as a MUST but the implementation's docstring explains why the operator-facing step suffices; not flagged Blocking, but noted as a literal-text gap between contract and code (see §57 Findings). |
| §9 eight-state lifecycle | **Partially implemented / represented elsewhere** — see §32 below. |
| §10 return-to-work / invalidation | Fully implemented — any Class-A path in the delta produces `other_issues`, which unconditionally blocks (no carve-out), and no field is ever written to `report.metadata` on that path (confirmed in §12). |
| §12 push-state correction loop | Not separately implemented (no new code); relies on the pre-existing, unmodified convention documented in `project_phase_completion_procedure.md`. Consistent with contract text ("existing PCAE convention... carried forward unchanged"). |
| §13 `final_phase_head` = HEAD at promotion | Fully implemented — `current_head(repo_root)` is called fresh inside `validate_derived_correctness()` at whatever moment it runs, which is every time `finalization_transaction.py`'s pre-promotion certification runs (both `--stage-pending-report` and the promoting call), confirmed via `grep` call-site trace (§39/§42 below). |
| §14 five-condition freshness | Conditions 1-2 delegate unchanged to the pre-existing `validate_structured_fast_green()`; conditions 3-5 are new (`check_finalization_delta` + `run_stage_b_focused_checks`). **Condition 5's soundness is compromised by the Blocking defect (§8 below) under exactly the circumstance where conditions 1-2 fail (staleness).** |
| §16 scalar backward compatibility | Fully implemented — the entire carve-out is gated behind `is_structured_fast_green(raw_fast_green)`; scalar path body is untouched (confirmed by diff: zero lines changed in the `else:` scalar branch). |
| §17 push trust-boundary preservation | Fully implemented — see §41. |
| §18 report semantics (checkpoint != final_head, not implied equal) | Fully implemented — `fgsc_verification_checkpoint_commit` and `fgsc_final_phase_head` are recorded as two distinct fields; no code path asserts or requires equality. |
| §21 acceptance test list (1-13, excludes 14-16 self-hosting) | Substantially covered by the 2S.2 suite (57 tests, all independently re-run and passed, §47 below) — **except item 7, "finalization-delta count/set integrity: every changed path... none silently ignored," which the 2S.2 suite does not test end-to-end together with a co-occurring attribution defect.** That gap is exactly where this phase's Blocking finding lives. |

## 5. Verification checkpoint implementation assessment

The checkpoint is mechanically equal to `evidence["candidate_commit"]`,
itself set by `current_head(repo_root)` at the moment `build_attribution_evidence()`
ran (`fast_green_attribution.py:367`). It is never caller-arbitrary: no code
path in `phase_reports.py` accepts a checkpoint value from any source other
than the persisted, digest-verified evidence artifact
(`raw_fast_green.get("candidate_commit")`, `phase_reports.py:1750`, read only
*after* `validate_structured_fast_green()` has already confirmed the inline
value matches the artifact byte-for-byte). Checkpoint substitution attack:
attempted supplying a `candidate_commit` that does not match the artifact's
own persisted content — caught by the pre-existing digest/divergence check
(§652 confirmed via direct call, "field 'baseline_commit' diverges from the
persisted evidence artifact" reproduced for an analogous field in this
phase's own adversarial testing, §8 below).

## 6. Baseline / checkpoint separation

Verified structurally distinct: `baseline_commit` (used for the
preexisting-failure diff) and `verification_checkpoint_commit` /
`candidate_commit` (used for the finalization-delta diff) are different
fields, computed by different functions (`derive_phase_entry_baseline()` vs.
`current_head()`), and never interchanged in any code path read. No fallback
to an attacker-chosen value for either exists — both are always either
recomputed from Git (`derive_phase_entry_baseline`, `current_head`) or read
from the digest-verified artifact.

## 7. Checkpoint authority source

Derives exclusively from: (a) the digest-verified persisted evidence
artifact's own `candidate_commit` field, which was itself written by
`current_head(repo_root)` — i.e., Git — at capture time. Caller-supplied
report metadata alone is never sufficient: `report.test_results["fast_green"]`
is the caller's *only* input, and every field in it is validated against
the persisted artifact (digest match) before any of it is trusted, and the
artifact's own freshness/baseline/command fields are independently
recomputed against live Git state, not merely re-read.

## 8. Staleness carve-out — BLOCKING DEFECT

**Exact validator issue produced:** `validate_structured_fast_green()`
appends `"structured fast_green evidence is stale — candidate_commit ... !=
current HEAD ..."` when `evidence.get("candidate_commit") != actual_head`
(`fast_green_attribution.py:586-590`), **without returning** at that point —
execution is intended to continue through the remaining checks (baseline,
command, preexisting/environment/expected-artifact bucket verification,
conservation, attributable-failures rejection).

**Exact caller that receives it:** `validate_derived_correctness()`
(`phase_reports.py:1650-1793`), which partitions the returned
`structured_issues` list into `stale_issues` (matching the literal prefix
`"structured fast_green evidence is stale"`) and `other_issues` (everything
else), and proceeds to the carve-out (`check_finalization_delta` +
`run_stage_b_focused_checks`, then writes `fgsc_lifecycle_state =
"FINALIZATION_VERIFIED"` into `report.metadata`) whenever `stale_issues`
is non-empty and `other_issues` is empty.

**The defect:** `validate_structured_fast_green()` contains a second,
unconditional early-return guard —

```python
    if issues:
        return issues

    # Conservation (2Q.1 §7): disjointness + exact coverage.
    all_classified = preexisting_computed | environment_ids | expected_ids
    ...
    attributable_computed = sorted(raw_set - all_classified)
    attributable_claimed = evidence.get("attributable_failures")
    ...
    if sorted(set(attributable_claimed)) != attributable_computed:
        issues.append(...)
    ...
    if attributable_computed:
        issues.append("... has nonzero attributable_failures ...")
```

— positioned immediately *after* the freshness/baseline/command/bucket
checks and *before* the conservation/attributable-failures computation.
Because the freshness check appends its issue without returning, `issues`
is already non-empty by the time this guard is reached whenever the
evidence is stale — so the function returns **before ever computing or
checking `attributable_failures`**, the single check 2Q.1 designed
specifically so that "no human/agent judgment call [is] permitted" and the
artifact's own bucket labels are never trusted.

**Consequence:** `structured_issues` in the caller is `[staleness_issue]`
and nothing else — not because nothing else is wrong, but because nothing
else was ever checked. `other_issues` is therefore empty, the carve-out's
precondition ("only staleness is wrong") is satisfied on a false premise,
and the carve-out proceeds. Since routine, contract-permitted finalization
commits (Class B) *always* produce staleness — that is the entire reason
FGSC-001 exists — this is not an edge case: it is the **normal operating
condition** of every structured-mode phase that reaches finalization.

**Proof (mechanically tested, not asserted):**
`tests/test_phase_149o_20l_7o_2s_3_fgsc_001_lifecycle_independent_verification.py::TestStalenessCarveOutSoundness`
(new, independent test file, this phase):

1. `test_validate_structured_fast_green_skips_attribution_recompute_once_stale`
   — captures real structured evidence via `build_attribution_evidence()`,
   injects one additional unclassified failing node ID directly into the
   persisted artifact (re-signing its digest so the artifact stays
   internally self-consistent — modeling either a `build_attribution_evidence`
   defect or the filesystem-tampering actor the module's own docstring
   already names as a residual risk). **Sanity-checked**: calling
   `validate_structured_fast_green()` against this tampered evidence while
   the checkpoint still equals current HEAD (no staleness) correctly flags
   `attributable_failures does not match the recomputed default set`. Then,
   after one ordinary Class-B finalization commit moves HEAD forward
   (introducing staleness, nothing else), the same tampered evidence
   produces **only** the staleness issue — the attribution defect vanishes
   from the returned list entirely.
2. `test_carve_out_certifies_finalization_verified_despite_hidden_regression`
   — same setup, driven through the real `validate_derived_correctness()`
   gate (the function `finalization_transaction.py` actually calls at both
   `--stage-pending-report` and promotion time). Result: `issues == []` and
   `report.metadata["fgsc_lifecycle_state"] == "FINALIZATION_VERIFIED"` —
   the report is certified lifecycle-verified with a real, unclassified test
   regression sitting undetected in its own evidence.

Both tests pass against the unmodified 2S.2 implementation (run this phase,
`9 passed` for the full new file, `57 passed` for the pre-existing 2S.2/2R
suites unaffected — no regression, no production change).

**Why this is Blocking, not merely a carried-forward finding:** this is
exactly the failure mode Phase 149O.20L.7O.2S.3's own brief (§9) names as
Blocking — "any broad issue filtering" that could suppress "attributable
failures... merely because FGSC mode is active" — and exactly the Blocking
example in §57: "carve-out suppresses non-staleness issue." The suppression
here is not a logic bug in the carve-out's own filtering predicate (the
`stale_issues`/`other_issues` partition itself is correct given its input);
it is that the partition's *input* — `validate_structured_fast_green()`'s
returned issue list — is not the complete set of problems with the
evidence once staleness is present, because of a pre-existing (2R-era,
unmodified by 2S.2) early-return that was harmless before 2S.2 (because
*any* non-empty issue list blocked completion outright, regardless of
which checks it did or didn't reach) and became load-bearing and
exploitable the moment 2S.2 introduced the first code path that treats a
short issue list as meaningfully different from a long one.

**Attribution:** the specific `if issues: return issues` guard is
pre-existing code, unmodified by commit `d911ebb9` (confirmed: the 2S.2
diff to `fast_green_attribution.py` is purely additive, appended after this
guard's line number; `git blame` on this guard predates 149O.20L.7O.2S).
2S.2 did not introduce a new bug into `validate_structured_fast_green()`
itself — it introduced the first caller that makes this pre-existing
control-flow quirk security-relevant.

## 9. No generic issue filtering (attempted, partially failed)

Every generic-suppression scenario the brief asks to attack was tried:
digest mismatch, baseline mismatch, missing/malformed bucket entries,
duplicate bucket membership, malformed evidence shape, wrong schema, and
environment-policy-violation entries were all confirmed to *still* block
unconditionally when tested **without** co-occurring staleness (§8's sanity
check, and direct reproduction of the pre-existing divergence/malformed-key
early returns for `baseline_commit`). **The one exception is exactly §8's
finding**: any of these defects, when it happens to co-occur with staleness
(the routine case), is invisible to the carve-out because
`validate_structured_fast_green()` never reaches the checks that would
detect several of them (specifically: conservation / attributable-failures
recomputation; not all of the malformed-entry checks are unreachable —
those in the preexisting/environment/expected-artifact loops run *before*
the fatal `if issues: return issues` guard and were independently confirmed
still reachable and still blocking even under staleness).

## 10. Sole-staleness condition (A/B construction)

**A — only the permitted mismatch:** `TestLifecycleFreshnessIntegration::
test_finalization_delta_after_checkpoint_accepted` (2S.2 suite, re-run this
phase, passes) demonstrates clean evidence + one Class-B finalization
commit proceeds to `FINALIZATION_VERIFIED`. Confirmed correct.

**B — permitted mismatch + one unrelated validation issue:** attempted with
a tampered `baseline_commit` field (inline-vs-artifact divergence) —
correctly rejected (this divergence check runs *before* the freshness
check and returns early on its own, so it is unaffected by §8's defect).
Attempted with an injected unclassified `raw_failed` entry (§8) —
**incorrectly accepted**. B is not uniformly "must fail" as the brief
assumes; it depends on *which* class of unrelated issue, because of §8's
early-return ordering. This refines rather than contradicts the brief's
expectation: most classes of B correctly fail; the conservation/
attribution class does not.

## 11. Five-condition freshness

Extracted directly from contract §14 and cross-checked against code:

1. `candidate_commit == verification_checkpoint_commit` — `evidence.get("candidate_commit") != actual_head` check, unmodified. Broken via HEAD-advance test (2S.2 suite) — correctly rejected when *not* carved out; correctly tolerated (by design) when carved out.
2. `baseline_commit` remains authoritative — `derive_phase_entry_baseline()` recomputation, unmodified. Broken via tampered `baseline_commit` (§10) — correctly rejected, and this rejection path is unaffected by §8's defect (fires before the freshness check's issue accumulates, since baseline mismatch is checked immediately after freshness but the mismatch itself is what gets returned as `other_issues`, so `stale_issues and not other_issues` is false and the carve-out never activates — verified in §10's B case).
3. Checkpoint is ancestor of `final_phase_head` — `git merge-base --is-ancestor`, `diff_authority_issues()`. Broken via orphan-branch test (2S.2 suite, `test_rewritten_or_unrelated_ancestry_rejected`) — correctly rejected.
4. Every post-checkpoint commit single-parent + Class B — `check_finalization_delta()`. Broken multiple ways this phase (§12-14, §20-24 below) — correctly rejected in every case tested.
5. Stage B focused checks pass — `run_stage_b_focused_checks()`. Broken via monkeypatched failure (2S.2 suite, `test_stage_b_failure_blocks_completion_even_with_clean_delta`) — correctly rejected.

No condition is implied by prose alone; all five have direct code
correspondence, independently located (not via the phase report).

## 12. Final HEAD != checkpoint (synthetic disposable repo)

Constructed directly (§8/§10/§12 test infrastructure in the new
independent-verification suite, and ad hoc during investigation): checkpoint
X, one or more Class-B finalization commits producing Y, `final_phase_head
== Y`. Structured evidence for X remains valid only through the
finalization-delta check — confirmed the delta check is always
re-evaluated against the *current* `final_phase_head` at call time (never
cached), by re-running `validate_derived_correctness()` a second time after
an *additional* Class-B commit and confirming both `fgsc_final_phase_head`
values differ and both calls independently re-verify the full
checkpoint..head range (not just the incremental delta).

## 13. Forbidden delta

Repeated with one forbidden post-checkpoint modification in each of
`src/pcae/**`, `tests/**`, `docs/contracts/**` (2S.2 suite, all three
covered and re-confirmed passing this phase) plus, newly this phase,
`pyproject.toml` (exact-path Class A entry) and mode-only/symlink/gitlink
attacks under otherwise-open directories (§14 below) — old checkpoint
evidence becomes unusable for completion in every case; no carve-out
applies to any of these (they all surface as `other_issues`, since none of
them produce a "staleness" string, so the `stale_issues and not
other_issues` gate correctly never fires for them regardless of §8's
defect).

## 14. Path classification — independently reconstructed

Reconstructed directly from `classify_finalization_path()` source (not
inferred from tests), then checked against contract §4 text:

- `conftest.py` (any depth) and `.githooks/**` → A, unconditionally, before
  the general prefix rules — matches contract §4's "consumed during test
  collection/execution itself" and `.githooks/**` clauses.
- `_CLASS_A_EXACT_PATHS = {"pyproject.toml"}`, `_CLASS_A_PATH_PREFIXES =
  ("src/pcae/", "scripts/", "tests/", "docs/contracts/")` → A. Matches
  contract exactly.
- Everything else not in the Class-B allow-list (`_CLASS_B_EXACT_PATHS`:
  the metadata/report pair, `PROJECT_STATUS.md`, `CHANGELOG.md`;
  `_CLASS_B_PATH_PREFIXES`: the evidence-artifact directory, `tasks/`,
  `.pcae/session`) → A (fail-closed default). Matches contract §4's
  "unknown defaults to... forbidden" (contract text says "class C"; code
  has no class C — see N2 disposition, §53).
- Content-sensitivity restriction: even inside an open Class-B directory,
  mode `120000`/`160000` or executable-bit suffix, or non-`.md/.json/.txt`
  extension, forces A. Matches contract §4's final paragraph exactly.

## 15. Unknown path fail-closed

`fga.classify_finalization_path("random/never/seen.txt")` (2S.2 suite,
re-confirmed) and, this phase, a real gitlink under the otherwise-open
`tasks/active/` directory (§14 above) — both correctly fail closed to A.

## 16. Docs / contracts

`docs/contracts/**` is unconditionally Class A (prefix rule, no
distinction from ordinary docs) — confirmed by direct code read and the
2S.2 suite's `test_docs_contracts_change_after_checkpoint_rejected`. No
special-cased "ordinary documentation" carve-out exists inside
`docs/contracts/**`; the entire directory is closed. Matches contract §4.

## 17. `.pcae` paths

Enumerated allow-list: `.pcae/phase-completion-metadata.json`,
`.pcae/phase-completion-report.md` (exact paths only, not a `.pcae/**`
prefix), `.pcae/fast-green-attribution/` (prefix), `.pcae/session` (prefix,
covering `.pcae/session.json` and any `.pcae/session*` sibling). No broad
`.pcae/**` allowance exists. Attacked with `.pcae/agent-locks/latest.json`
(a real, existing, unlisted `.pcae/` path in this repository) —
confirmed Class A via direct `classify_finalization_path()` call (not in
any Class-B exact-path or prefix set, defaults to A).

## 18. Task paths

`tasks/` prefix covers `tasks/DONE.md`, `tasks/active/*`, `tasks/done/*` —
matches contract §4 and the actual lifecycle files this phase's own
`pcae task transition` produced. `tasks/active/hook.py` (2S.2 suite,
`test_class_b_directory_with_wrong_extension_is_class_a`) correctly forced
to A by the extension restriction even though it is nominally under an
open directory.

## 19. `PROJECT_STATUS.md` / `CHANGELOG.md`

Exact-path Class B entries. Neither is read by any Stage A `fast_green`
test (confirmed: no `import` of either file's path exists in
`src/pcae/**`, and neither has a `.py` extension). `run_stage_b_focused_checks()`
does not specifically inspect either file's content, but `pcae status
coherence` (one of the three in-process focused checks) does read
`PROJECT_STATUS.md` for phase-declaration coherence — so a malformed
`PROJECT_STATUS.md` edit *is* covered, via Stage B's focused-check set, not
via path classification. Consistent with contract §19's own framing.

## 20. Rename attack

Both directions constructed as real Git renames (not synthetic mode
strings), this phase:
`src/thing.py → CHANGELOG.md` (unsafe→safe) and `PROJECT_STATUS.md →
src/pcae/evil.py` (safe→unsafe) — both correctly rejected, because
`_diff_raw_entries()` evaluates *both* `old_path` and `new_path` against
their respective modes and any Class-A hit on either side rejects the
whole entry (`diff_authority_issues()`'s per-entry loop over
`("old_path", "old_mode"), ("new_path", "new_mode")`).

## 21. Symlink attack

Constructed a real Git symlink entry (`ln -s`, not a synthetic mode
string) at a Class-B-eligible name (`CHANGELOG.md → PROJECT_STATUS.md`) —
correctly rejected via the real `git diff --raw` mode field (`120000`),
independent of the 2S.2 suite's unit-level `mode="120000"` parametrized
test.

## 22. Mode change

Constructed a real `chmod +x` on an otherwise-valid Class-B file
(`PROJECT_STATUS.md`) with **no content change** — correctly rejected via
the real diff's mode field (`100644 → 100755`), confirmed end-to-end
through `check_finalization_delta()`, not just the unit-level
`classify_finalization_path(..., mode=...)` call.

## 23. Submodule / gitlink

Constructed a real gitlink entry (`git update-index --add --cacheinfo
160000,<sha>,tasks/active/embedded`) under the otherwise-open `tasks/`
directory — correctly rejected (mode `160000` forces Class A
unconditionally, confirmed end-to-end, not just via the unit-level
synthetic-mode test in the 2S.2 suite).

## 24. Binary / unknown delta

Not separately end-to-end tested this phase (redundant with the
content-sensitivity extension restriction already covered by §14/§19 and
the 2S.2 suite's `test_class_b_directory_with_wrong_extension_is_class_a`):
any file whose extension is not `.md`/`.json`/`.txt` is Class A regardless
of directory, which necessarily includes any binary file. No exemption
exists.

## 25. Full ancestry

`diff_authority_issues()` uses `git diff --raw ... checkpoint..final_head`,
which by Git semantics reflects the full tree-state delta including any
content that arrived via a merge — but §26 confirms merges are rejected
outright in-range, so no non-first-parent import path can exist in an
*accepted* delta. No misleading first-parent-only restriction was found:
the diff command used has no `--first-parent` flag.

## 26. Merge rejection

Constructed a real merge scenario (2S.2 suite, `test_merge_commit_in_range_rejected`,
re-confirmed this phase) — a merge commit anywhere in
`checkpoint..final_head` is unconditionally rejected via
`git rev-list --min-parents=2`, independent of what the merge actually
changed.

## 27. History rewrite

Constructed via an orphan branch (2S.2 suite,
`test_rewritten_or_unrelated_ancestry_rejected`) — checkpoint no longer an
ancestor of final HEAD is correctly rejected via `git merge-base
--is-ancestor`. No substitute-checkpoint fallback exists in the code (no
code path accepts an alternate checkpoint when the original fails
ancestry).

## 28. Stage A integration

`git diff d911ebb9 -- src/pcae/core/fast_green_attribution.py` (§3) confirms
byte-identical five-bucket arithmetic, baseline/candidate execution, and
`persist_evidence`/`build_attribution_evidence` logic above the new FGSC-001
section — zero lines modified. `tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py`
re-run independently this phase: pass count unchanged from the 2S.2 report's
own record (18/18).

## 29. Stage B implementation

`run_stage_b_focused_checks(repo_root)` (`phase_reports.py`): inputs —
`repo_root` only; authoritative delta — none computed here (that's
`check_finalization_delta`, a separate function called by the same
caller); calls, in-process, `pcae.core.check.run_checks`,
`pcae.core.status.check_project_status_coherence`,
`pcae.core.tasks.diagnose_task_memory`; result — a flat `list[str]` of
issues, empty means clean; fail-closed on any exception from any of the
three (caught individually, each appended as its own issue string rather
than silently swallowed). Confirmed by direct source read, not report
prose.

## 30. Stage B recursion safety

Independently traced the call graph of all three functions
`run_stage_b_focused_checks()` invokes: `grep` confirms none of
`pcae.core.check`, `pcae.core.status`, `pcae.core.tasks` references
`validate_derived_correctness` or `finalization_transaction` anywhere in
their source (`tests/test_phase_149o_20l_7o_2s_3_...py::
TestPushTrustBoundaryAndRecursionSafety::
test_stage_b_focused_check_functions_do_not_import_finalization_path`,
this phase, passes). The one cross-import found
(`pcae.core.status` imports `_match_current_phase_declaration` from
`pcae.core.phase_reports`) is a pure text-parsing helper with no call back
into validation/finalization (confirmed by reading its definition,
`phase_reports.py:2722` — a regex-based section-text matcher, no
side effects, no further imports of validation code). Call graph
terminates.

## 31. No re-entrant finalization

No mock/instrumentation needed beyond §30's static trace: since none of
the three Stage B focused-check functions import or call
`validate_derived_correctness`, `finalization_transaction`, or `pcae phase
complete`'s command-layer code, there is no code path by which Stage B
could re-enter finalization even indirectly. Confirmed via `grep`, not
inference from behavior alone.

## 32. Eight-state lifecycle representation

**Not implemented as eight explicit persisted enum values.** The only
lifecycle-state value ever written anywhere is the single string literal
`"FINALIZATION_VERIFIED"`, written to `report.metadata["fgsc_lifecycle_state"]`
only on the full-success path (all of conditions 3-5 hold). No other state
name from contract §9's list (`IMPLEMENTING`, `CANDIDATE_FROZEN`,
`BEHAVIOR_VERIFIED`, `FINALIZING`, `READY_TO_PUSH`, `PUSHED`, `COMPLETE`)
is ever persisted by this implementation.

This is a **compact representation**, not a missing one: the design is
stateless-recomputation rather than a persisted state machine — every call
to `validate_derived_correctness()` re-derives checkpoint validity,
finalization-delta authority, and Stage B cleanliness from Git and the
evidence artifact from scratch, rather than trusting a previously-persisted
state flag. This is semantically defensible (contract §9 itself frames the
states as a conceptual model, not a mandated storage schema) and has a real
advantage the contract's own §37 (crash/resume) cares about: there is no
stale/replayed state value that can be found on disk and mistakenly
trusted, because nothing is trusted from disk except Git commits and the
digest-verified evidence artifact (confirmed by
`test_crash_resume_reconstructable_from_git_and_artifact_alone`, 2S.2
suite, re-run and passing this phase).

**However**, this compact representation is exactly where §8's defect
lives: the *quality* of the recomputation on every call depends entirely on
`validate_structured_fast_green()` actually re-running every check each
time, and §8 shows it does not once staleness is present. A literal
eight-state machine would not, by itself, have prevented §8's defect
(the defect is in the Stage-A-equivalent recomputation function's own
control flow, not in state *storage*) — but it is noted here because the
compact representation's crash/resume safety guarantee is only as strong
as the underlying recomputation, and §8 shows that guarantee has a gap.

## 33. State transitions

No route from unverified to `report.metadata["fgsc_lifecycle_state"] ==
"FINALIZATION_VERIFIED"` was found that skips *both* Stage A and Stage B —
every code path writing that field is inside the single `if stale_issues
and not other_issues:` branch, which is only reached after
`validate_structured_fast_green()` has run (Stage A / conditions 1-2) and
is immediately followed by `check_finalization_delta()` (condition 3-4)
and `run_stage_b_focused_checks()` (condition 5), all three required to
return clean before the metadata write. §8's defect is not a skip of Stage
A or Stage B — both stages genuinely run — it is that Stage A's own
internal check is incomplete under staleness.

## 34. Invalidation

Confirmed (2S.2 suite, `test_forbidden_change_after_checkpoint_still_blocks_completion`,
re-run and passing) — a Class-A change after checkpoint invalidates via
`other_issues` non-empty, and no `fgsc_*` metadata field is written.

## 35. Return to work

Not separately re-tested this phase beyond §34/§13 (same mechanism):
a Class-A-affecting edit after checkpoint always produces `other_issues`,
which always blocks unconditionally regardless of staleness — old evidence
cannot survive a genuine implementation-affecting edit made after the
checkpoint. This holds even under §8's defect, because §8's defect
specifically requires the corrupting condition to be *inside the evidence
artifact itself* (a conservation/attribution mismatch), not a live
Class-A path change, which is caught by an entirely separate function
(`check_finalization_delta`, unaffected by `validate_structured_fast_green`'s
internal control flow).

## 36. Checkpoint persistence

Checkpoint is not separately persisted anywhere — it is re-read every time
from the evidence artifact's own `candidate_commit` field (content-addressed,
digest-verified). No self-reference: the checkpoint value used to validate
the artifact is read *from* the artifact, not from some other
`.pcae/`-resident pointer that itself would need independent authority.

## 37. Crash / resume

Covered by the 2S.2 suite's `test_crash_resume_reconstructable_from_git_and_artifact_alone`
(re-run, passing) — the checkpoint and finalization-delta cleanliness are
both fully reconstructable from Git history plus the persisted evidence
artifact, with no in-process-only state. See also §32's caveat.

## 38. Report schema

`fgsc_verification_checkpoint_commit`, `fgsc_final_phase_head`,
`fgsc_lifecycle_state` are added to `report.metadata`, an existing
open-ended dict field — no schema migration, no change to any existing key,
confirmed additive by direct diff read. Malformed structured evidence
(missing keys, wrong types) fails closed at the pre-existing
`_REQUIRED_EVIDENCE_KEYS` / type-check layer, unaffected by this phase's
changes. Scalar reports are provably unaffected (`test_scalar_mode_entirely_unaffected`,
2S.2 suite, re-run, `report.metadata == {}`).

## 39. Report trust / canonical promotion path

Traced: Stage A valid (via `validate_structured_fast_green` — subject to
§8's caveat) + finalization delta authorized (`check_finalization_delta`)
+ Stage B valid (`run_stage_b_focused_checks`) → eligible for
`fgsc_lifecycle_state = "FINALIZATION_VERIFIED"`, which is the only new
signal this phase adds; canonical promotion itself is gated by the
pre-existing, unmodified `validate_derived_correctness()` returning an
empty `issues` list overall (the FGSC fields are metadata annotations, not
themselves a separate gate). No single field bypasses the chain in the
absence of §8's defect; with §8's defect, the "Stage A valid" input to this
chain can itself be wrong.

## 40. Phase-report consistency

Recognizes checkpoint + authorized finalization delta correctly for the
one path exercised (structured-mode carve-out); scalar and non-FGSC
structured reports are provably untouched (§38). `pcae phase-report
consistency` itself (contract §19, a separate CLI diagnostic) was
confirmed, by direct code read, still unmodified by this phase and still
using naive `candidate_commit == current HEAD` — exactly as contract §19
already documents as a known, accepted, non-gating gap.

## 41. Push trust boundary

`grep "fast_green_attribution\|fgsc" src/pcae/commands/push.py` returns
nothing (confirmed via
`TestPushTrustBoundaryAndRecursionSafety::test_push_module_has_no_fgsc_or_attribution_awareness`,
this phase, passing). `push.py` continues to trust exclusively the
already-finalized canonical report's `compute_final_trust()` output.
Contract §17 holds.

## 42. Push circularity

Pre-push: `HEAD != origin/main` does not block `pcae phase complete
--stage-pending-report` — confirmed by direct code read of
`finalization_transaction.py`'s certification path (no push-state
precondition gates staging) and by this phase's own execution (staged
below while `origin/main == HEAD` still held from before this phase's
commits, i.e., push-state was irrelevant to staging succeeding).
Post-push: origin parity is established by the separate, unmodified `pcae
push` command; `final_phase_head` for the FGSC carve-out is defined
independently of origin-parity (contract §13), confirmed no code path in
the FGSC section reads `origin/main` at all (only `pcae push check`, run
as a separate operator step, does).

## 43. Push-correction loop / N3

Independently inspected: no FGSC-001 code path can change the checkpoint,
broaden finalization authority, skip Stage B, or silently rewrite trusted
evidence during a push-state correction iteration — a correction commit is
just another Class-B commit through the same unmodified
`check_finalization_delta`/`run_stage_b_focused_checks` pipeline; nothing
in the FGSC-001 addition special-cases "this is a correction commit."
Termination remains **empirically** bounded (unchanged from N3's original
2R.1 characterization) — this phase adds no new structural bound and finds
no new unboundedness. N3 remains Non-Blocking; not repaired, per phase
scope.

## 44. Finite execution

No automatic recursion or infinite loop exists in the FGSC-001 code path
(§30/§31). The correction loop (§43) is a human/governed retry loop, not
automatic execution — distinguished and confirmed via the same call-graph
trace.

## 45. 16 "attributable" Fast Green nodes — terminology

Independently reconstructed from `docs/PHASE_149O_20L_7O_2S_2_..._IMPLEMENTATION.md`
§34: the 16 nodes are `git status`-cleanliness guard tests (e.g.
`test_no_src_pcae_files_dirty_in_working_tree`) that fail specifically
because the phase's own uncommitted `git stash -u` A/B comparison
methodology leaves `src/pcae/**` dirty at the moment the candidate side of
the comparison runs — i.e., they are artifacts of the *comparison
methodology itself* (a working-tree-dirty state that exists for every
phase using this A/B convention, not specific to FGSC-001's functional
behavior), not of the FGSC-001 implementation's behavior. The report's own
prose (§34, immediately following the raw count) already discloses this
precisely and consistently, and separately reports the deselected-clean
figure per `project_phase_completion_procedure.md` convention. No
terminology imprecision or mischaracterization found: the report is
internally consistent and matches direct reconstruction. Not a defect.

## 46. Controlled A/B attribution

Not independently re-run in full this phase (a full `pytest -m fast_green
-n auto` baseline+candidate A/B is an ~260s, environment-heavy operation
already performed and documented in the 2S.2 report at §34, and re-running
it produces no new information relevant to this phase's Blocking finding,
which is a logic defect reproducible in milliseconds via disposable
synthetic repositories — see §8). The 2S.2 report's own accounting (16
attributable, all explained as methodology artifacts per §45, zero
regressions, zero masked fixes) was cross-checked for internal consistency
against the raw counts given (336→352 failed, 8690→8674 passed, diff of
exactly 16) and found arithmetically consistent (352-336=16,
8690-8674=16).

## 47. Existing 2R / 2R.1 suite regression check

`tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py` re-run
independently this phase: **18 passed**, matching the 2S.2 report's own
figure exactly — no regression from lifecycle integration.

## 48. Fresh independent test suite

`tests/test_phase_149o_20l_7o_2s_3_fgsc_001_lifecycle_independent_verification.py`
(new, this phase, does not import or reuse fixtures from the 2S.2 suite).
**9 tests, all passing** against the unmodified implementation:

- `TestRealDiffAttacks` (5): mode-only chmod, real symlink, real gitlink
  under an open directory, unsafe→safe rename, safe→unsafe rename — all
  via real Git operations end-to-end through `check_finalization_delta()`,
  not synthetic mode-string unit calls.
- `TestStalenessCarveOutSoundness` (2): the Blocking-finding reproduction
  (§8), at both the `fast_green_attribution` layer and the
  `validate_derived_correctness` gate layer.
- `TestPushTrustBoundaryAndRecursionSafety` (2): static confirmation of
  §41 and §30.

Combined with the 57 pre-existing 2S.2/2R tests re-run (§28/§47), this
phase directly exercised 66 tests against the FGSC-001 implementation, all
passing except that 2 of the 9 new tests *demonstrate* the Blocking defect
(they pass because they assert the defective behavior occurs, with
explicit comments marking them as documented-defect regression tests to be
revisited once repaired).

## 49-52. Carried-forward 2R.1 findings

Independently re-examined against the 2S.2 diff (§3): none of raw-content
trust, environment-exclusion-timeout classification, baseline
commit-message authority, or evidence-artifact retention are touched by
`d911ebb9` (confirmed: none of the relevant code —
`_collect_raw_result`, `_rerun_single_node`, `derive_phase_entry_baseline`,
`persist_evidence`'s artifact-directory handling — appears in the diff at
all). Not worsened. Not repaired. Out of scope, per phase brief §49-52.

## 53. N1 / N2

**N1** (overbroad `docs/contracts/**` digest-binding citation, from 2S.1):
`docs/contracts/FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md` is
unmodified by `d911ebb9` (confirmed, §3) — semantics unchanged, not
repaired.

**N2** ("class C" naming inconsistency, from 2S.1): confirmed still present
verbatim — contract §4 line 126 still reads "Unknown defaults to class C
(forbidden)" while the actual scheme (both contract text elsewhere and
code) is a two-class A/B system with unknown defaulting to A. The
implementation's `FinalizationPathClass` class defines only `A` and `B` —
no `C` constant exists anywhere in code. This is a documentation-prose
inconsistency only; the code's actual behavior (fail-closed to A) is
correct and unambiguous, independently confirmed in §14/§15. Not repaired,
per phase scope; correctly not opportunistically fixed by 2S.2.

**N3**: see §43.

## 54. Authority / HMIC scope

Every production file `d911ebb9` touches
(`src/pcae/core/fast_green_attribution.py`,
`src/pcae/core/phase_reports.py`) was checked against the repository's
HMIC/trust-scope-bearing test set: `grep` across `tests/` for any test
whose name or content binds either file by path under an HMIC/trust/
authority/frozen-scope test — **no match**. Both files are ordinary
governance-logic core modules, not claimed or expected to be
authority-bearing (no HATP/WebAuthn/signing/permission-broker/authority-
decision-record content appears in either file, confirmed by direct read,
§3/§8/§29). No authority-bearing implementation was found outside its
required trust binding. Not Blocking.

## 55. No real S22 yet

Confirmed: no `pcae phase fast-green-attribution` or self-hosting
acceptance command was run against the real `pcae-harness` checkout during
this phase. All FGSC-001 mechanism testing this phase used disposable
synthetic repositories under the session scratch directory, never the real
repository's own Git history or working tree, and never modified any real
production file.

## 56. Phase 2P

Not touched. No file under any 2P-related path was read, modified, or
referenced by this phase's commits. `git status --short` before this
phase's commits confirmed a clean working tree with zero pre-existing 2P
artifacts staged.

## 57. Findings summary

| # | Severity | Finding |
|---|---|---|
| 1 | **BLOCKING** | Staleness carve-out precondition ("only staleness is wrong") is unsound: `validate_structured_fast_green()`'s pre-existing early-return (`if issues: return issues`, positioned before the conservation/`attributable_failures` computation) means that once staleness is flagged, an independently-recomputed attribution defect can never surface, so it is silently absent from `other_issues` and the carve-out proceeds. Reproduced mechanically (§8). |
| 2 | Non-Blocking / documentation gap | Contract §8 lists `pcae push check` as a Stage-B-focused-checks MUST; the implementation deliberately does not duplicate it in-process (architecture-layering + "already covered by the separate governed step" rationale documented in the function's own docstring). Functionally reasonable, but the contract text and implementation diverge literally. |
| 3 | Non-Blocking (carried forward, unworsened) | N1 — overbroad `docs/contracts/**` digest-binding citation. |
| 4 | Non-Blocking (carried forward, unworsened) | N2 — "class C" naming inconsistency in contract prose (code correctly has only A/B). |
| 5 | Non-Blocking (carried forward, unworsened) | N3 — push-correction loop termination remains empirical, not structurally bounded. |
| 6 | Non-Blocking (carried forward, unworsened) | 2R.1's four out-of-scope findings (raw-content trust, environment-exclusion timeout, baseline commit-message authority, artifact retention). |
| 7 | Observation | Eight-state lifecycle (contract §9) is represented compactly (one terminal-success string) rather than as a persisted state machine — semantically acceptable on its own, but its crash/resume safety is only as strong as the recomputation §8 shows has a gap. |

## 58. Verdict

**C — NOT VERIFIED — STALENESS CARVE-OUT DEFECT.**

Real S22.1/S22.2 self-hosting acceptance MUST NOT proceed until Finding 1
is repaired by a future governed phase and this implementation is
re-verified. Phase 149O.20L.7O.2P reconciliation remains correctly out of
scope and untouched.

**Recommended next phase:** a narrow, targeted repair phase (not this one)
that closes the specific gap in `validate_structured_fast_green()` —
either reordering the function so the conservation/attributable-failures
check runs unconditionally before any early return, or making the
carve-out's precondition check re-invoke the independent recomputation
directly rather than relying on `validate_structured_fast_green()`'s
possibly-truncated issue list — followed by a fresh independent
verification of the repaired mechanism. Only after that repair phase
passes independent verification should real S22.1/S22.2 self-hosting
acceptance be scheduled, per contract §22's own framing ("Neither test is
executed by this contract-freezing phase... not operationally complete
until 22.1 succeeds").

## 59. Proportional Fast Green

This phase's own changes are test-file- and documentation-only (no
production source touched). Proportional verification used: the two new
fresh independent test files' own pass/fail results (§48), full re-runs of
the two most directly relevant pre-existing suites (§28/§47, 57/57
passing, matching prior recorded counts), and direct source/call-graph
inspection (§30/§41/§54) rather than a repeated full `pytest -m fast_green
-n auto` exploratory loop, per this phase's own "no repeat exploratory
Fast Green loops merely to get literal zero" instruction. Raw truth and
attribution are reported separately in each relevant section above (no
structured/scalar `fast_green` evidence is produced or claimed by this
verification-only phase itself, since it makes no production change to
certify).

## 60. No-Go confirmation

Confirmed, this phase: no production source modified (`src/pcae/**`
untouched — see `git status --short` in the completion record); FGSC-001
contract not amended (`docs/contracts/**` untouched); no carried-forward
finding repaired; attribution arithmetic unchanged; scalar Fast Green
unchanged; no real S22 phase executed; Phase 2P not reconciled or touched;
HATP/WebAuthn unchanged (no such file referenced anywhere in this phase's
diff); no runtime execution enabled; no Git history rewritten; no raw or
force push performed by this phase (repo staged, not pushed — see
completion record below).

## Commits / push state

This phase's own commits, `origin/main..HEAD` delta, and exact push state
are recorded in the governed phase-completion metadata/report and this
phase's task-transition commits, per `project_phase_completion_procedure.md`.
As of this report, the phase is staged (`--stage-pending-report`) but not
yet pushed — push requires separate explicit user confirmation before
`pcae push` is run, per this session's standing operating rules for
actions visible to the shared remote.
