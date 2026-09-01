# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R

## N-16-4 Reconciliation IV Evidence-Harness Repair

**Verdict: REPAIRED — INDEPENDENT VERIFICATION PENDING `.1R.26R.1R.1`.**

## Identity and primary sources

- A, pre-`.1R.26`: `28b8b2b7`
- B, finalized `.1R.26`: `9d28f7ef`
- R, finalized `.1R.26R`: `e52d2f8e`
- V, finalized `.1R.26R.1` BLOCKED head: `7d60eda674ec31dd2f7efafdbbfd168c358caca6`
- E, this phase entry: `7d60eda674ec31dd2f7efafdbbfd168c358caca6`
- H, substantive harness-repair head: `5f894e72fb37429b221c122bfad4943be88287bd`

Inspected from primary source: `PROJECT_STATUS.md`; the complete `.1R.26R.1`
BLOCKED artifact and tracked completion metadata; `.1R.26R`, `.1R.27`,
`.1R.26`, and `.1R.25` canonical evidence; the full `.1R.26R.1` IV suite;
the full `.1R.26R` reconciliation suite that physically owns the two scanner
nodes; and `.1R.19R.1` / `.1R.22R` self-reference precedents.

## Exact defects and independent reproduction

Both nodes live in
`tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py`; they are
harness/meta-guards, not either substantive `.1R.26R` reconciliation guard.

1. `test_14_no_test_weakening_in_the_r26r_diff` failed at V because it scanned
   raw added lines for the substring `xfail`. The `.1R.26R` suite's own
   docstring/assertion literals satisfied that substring predicate. AST
   inspection of the same source found no executable expected-failure
   decorator or call.
2. `test_15_no_wildcard_or_fnmatch_introduced_in_the_r26r_diff` failed at V
   because it scanned raw added lines for the substring `fnmatch`. Its own
   explanatory text and assertions satisfied that predicate. AST inspection
   found no executable `fnmatch` call and no wildcard entry in a live
   allowlist/scope assignment.

Sanitized external source fixtures reproduced the distinction: prose,
comments, docstrings, and string data are ignored; executable constructs are
detected.

## Syntax-aware repair

The expected-failure scanner now parses Python AST and resolves:

- `@pytest.mark.xfail` and called decorator forms;
- `pytest.xfail(...)`;
- `import pytest as alias`;
- direct `from pytest import xfail as alias` calls;
- direct `from pytest import mark as alias` decorators.

Strings, comments, docstrings, and fixture descriptions are never executable
AST uses and are ignored. The scanner also compares AST-discovered test
function identities across touched files, preserving the no-removal/no-rename
property.

The wildcard scanner now parses AST and detects:

- `fnmatch.fnmatch(...)`, module aliases, and directly imported aliases;
- glob metacharacters in literal values assigned to live names containing
  `AUTHORIZED`, `ALLOWLIST`, `ALLOWED`, `EXPECTED`, `SCOPE`, `IMPORTER`,
  `CONSUMER`, or `PERMITTED`.

Explanatory strings and adversarial source fixtures remain inert data.

An additional finalized-harness defect was found and repaired within the same
narrow scope: `.1R.26R.1::test_01_sha_chain_is_reconstructed_from_git` equated
moving `HEAD` with R, so it failed after `.1R.26R.1`'s lifecycle commits. It
now reconstructs finalized V and proves `merge-base(V, HEAD) == V`.

## Adversarial and regression evidence

Fresh suite
`tests/test_runtime_dispatch_1r26r1_harness_repair_3w1r2b1r1_1r26r1r.py`
contains 22 tests and proves:

- real decorator, direct call, pytest alias, and imported alias detected;
- expected-failure strings/comments/docstrings ignored;
- qualified and imported `fnmatch` calls detected;
- `{"src/pcae/*"}` in a live authorized set detected;
- an exact single-path set accepted;
- wildcard/fnmatch fixture strings/comments/docstrings ignored;
- V reproduces both historical failures;
- substantive guard hashes, historical BLOCKED record, 42-node count,
  Gate6/Gate10 disposition, source/contract/runtime/effect/status boundaries
  preserved.

Combined suites after repair: **68 passed** in 94.26 seconds:

- repaired `.1R.26R.1` IV suite: 26 tests;
- `.1R.26R` reconciliation suite: 20 tests;
- fresh `.1R.26R.1R` suite: 22 tests.

A broader 129-file deterministic V/current sweep executed 5,676 nodes per
side: V 5,355 passed / 315 failed / 6 skipped; repaired worktree 5,357 passed /
313 failed / 6 skipped. It had 309 common failures. The two named scanner
nodes were fixed. Four current-only failures were explicitly dirty-worktree /
real-host cleanliness assertions and are non-functional phase-worktree
  artifacts; three additional V-only historical artifact nodes and the corrected
  moving-HEAD SHA assertion were likewise environment/history-sensitive, not
  security behavior.

A clean committed V/H comparison over the two common IV/reconciliation suites
isolated the harness delta exactly: V **43 passed / 3 failed**; H **46 passed**;
common failures 0; fixed nodes exactly the two self-reference scanners plus the
newly discovered moving-HEAD SHA assertion; candidate-only unexplained 0;
unexplained attributable regressions 0. The prompt's two expected scanner fixes
remain exactly two; the third fixed node is the separately disclosed finalized-
SHA harness defect found by the mandatory full-suite rerun.

## Preservation and attribution

- Substantive first guard SHA-256 at E/current:
  `733c6b7286cdde3060c81751b03d9e2191e131c790ad7d1516393398cdbd391d`.
- Substantive importer guard SHA-256 at E/current:
  `441b24cbf3b524f6a98817963a1e71060a390137e5ecc42e4d2c2c604197ece8`.
- Historical `.1R.26` attributable count remains exactly **42**.
- Repaired A/R unexplained attributable failures remain **0**.
- `.1R.26R.1` remains historically **BLOCKED**; an append-only successor
  annotation was added after its original report, without changing its verdict.
- Gate6/Gate10 remains a pre-existing `.1R.17` intentional fail-closed
  dependency plus stale historical guard, unrelated and unrepaired.
- No production source change; no normative-contract change.
- Runtime remains Observed / observe / unavailable; plugins 0; capabilities 0.
- First external effect remains ABSENT; no effect-capable path or Slice C.
- N-16-5/6/7 remain OPEN. N-23-2 remains INFO / DEFERRED.

No test function was removed or renamed; no executable expected-failure or
skip-to-pass use was added; no live wildcard/fnmatch broadening or exact-set
downgrade was added.

## Adjudication and next phase

`.1R.26R.1` EVIDENCE-HARNESS DEFECT: **REPAIRED — INDEPENDENT VERIFICATION
PENDING `.1R.26R.1R.1`.** N-16-4 remains IMPLEMENTED and NOT CLOSED.
Historical `.1R.26R.1` and `.1R.27` remain BLOCKED.

Recommend exactly:
`149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R.1` — Independent Verification of the
N-16-4 Reconciliation IV Evidence-Harness Repair. Do not begin it here.

DELEGATED `.3` FINALIZATION / COMMIT / PUSH:
UNAUTHORIZED

## Successor annotation — `.1R.26R.1R.1` discovery and `.1R.26R.1R.1R` repair

The later independent verification `.1R.26R.1R.1` preserved this phase's
self-reference fixes but found that the AST replacement unintentionally
dropped the predecessor guard's executable skip-to-pass coverage.  In
particular, H accepted a real `pytest.mark.skip` decorator and a direct
`pytest.skip` call because `_executable_xfail_uses` classified xfail only.
`.1R.26R.1R.1` remains historically BLOCKED; its report was not rewritten.

The separately authorized successor `.1R.26R.1R.1R` extends the syntax-aware
scanner into a unified executable test-weakening detector.  It restores
skip/skipif/direct-skip detection, preserves xfail and wildcard/fnmatch
detection, and continues to ignore comments, docstrings, inert explanatory
strings, and adversarial snippets held only as fixture data.  This is a
verification-harness correction only: no substantive `.1R.26R` guard,
production source, or normative contract changed.  Independent verification
of this successor remains required at `.1R.26R.1R.1R.1`.
