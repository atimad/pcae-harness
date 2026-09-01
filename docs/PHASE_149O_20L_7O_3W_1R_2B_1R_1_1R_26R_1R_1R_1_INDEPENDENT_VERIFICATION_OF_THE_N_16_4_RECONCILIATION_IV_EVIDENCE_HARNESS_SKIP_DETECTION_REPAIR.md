# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R.1R.1

## Independent Verification of the N-16-4 Reconciliation IV Evidence-Harness Skip-Detection Repair

**Verdict: `.1R.26R.1R.1R` SKIP-DETECTION REPAIR — VERIFIED.**

`.1R.26R.1R.1` remains historically BLOCKED, but its skip-detection blocker is
closed by the separately governed and now independently verified successor.
N-16-4 remains IMPLEMENTED / NOT CLOSED pending a fresh product-level IV.

## Immutable identity

| Identity | SHA |
|---|---|
| A — pre-`.1R.26` baseline | `28b8b2b70dcd4642dc45d4a3961a5218402c3c7c` |
| B — finalized `.1R.26` | `9d28f7efc3923bfca5e18b98e0a203881b256b7e` |
| R — finalized `.1R.26R` | `e52d2f8e9175015a2b344a547bea0c11058a92c8` |
| V — finalized `.1R.26R.1` BLOCKED head | `7d60eda674ec31dd2f7efafdbbfd168c358caca6` |
| H — substantive first AST repair | `5f894e72fb37429b221c122bfad4943be88287bd` |
| J — finalized `.1R.26R.1R.1` BLOCKED head | `d334c74e4c987640c612f77d64a4dba6ae160692` |
| K2 — substantive skip repair | `e512f96e0a8ad179b2e71506cb7ab8a0ed59ee6b` |
| K / I — finalized repair head and this IV entry | `eeb31757098cb5b02ace9f4f0fabe14370bd40c4` |

## Primary sources and invariant reconstruction

Inspected directly: `PROJECT_STATUS.md`; the `.1R.25`, `.1R.26`, `.1R.27`,
`.1R.26R`, `.1R.26R.1`, `.1R.26R.1R`, `.1R.26R.1R.1`, and
`.1R.26R.1R.1R` artifacts and immutable completion metadata; V, H, J, and K
scanner source; every repair test; `.1R.19R.1` / `.1R.22R` scanner precedents;
the two substantive reconciliation guards; production Gate 7, permission,
Gate 8/9/10 sources; and REPRC-001, RDGO-001, and
HPAC-AUTHORITY-CONSUMPTION/2.1 as read-only evidence.

V's exact predicate rejected an added line containing either
`@pytest.mark.skip` or `xfail`. Thus qualified skip and skipif marks plus xfail
marks/calls were historically intended to fail. Direct `pytest.skip(...)` was
not literally covered by V, but `.1R.26R.1R.1R` was explicitly authorized to
complete the skip-to-pass model. Qualified pytest syntax is canonical in the
corpus; module-level `pytestmark`, class marks, pytest aliases, and direct
imports occur or are supported by the repaired import resolver. There is no
pytest `skipif` callable convention separate from `pytest.mark.skipif`.

## Historical false negative and repaired detector

At J the exact executable adversary

```python
import pytest
@pytest.mark.skip(reason="proof")
def test_example():
    pass
```

returns no finding from `_executable_xfail_uses`; this reproduces the BLOCKED
IV without self-text involvement. At K the unified
`_executable_test_weakening_uses` returns `("skip-mark", 2)`. A direct
`pytest.skip("reason")` similarly changes from missed at J to detected at K.

The scanner uses `ast.parse`, resolves `import pytest as ...`, direct pytest
imports, `mark` aliases, attribute chains, calls, decorators, class marks, and
module-level mark expressions. `SequenceMatcher` restricts the live guard to
inserted/replaced new-source lines. Invalid Python raises `SyntaxError` and
fails safely. Comments, docstrings, inert strings, and adversarial snippets
stored as data do not produce executable AST findings.

## Independent adversarial results

| Construct | J | K / fresh IV | Verdict |
|---|---:|---:|---|
| `@pytest.mark.xfail` | detected | detected | preserved |
| `pytest.xfail(...)` | detected | detected | preserved |
| `@pytest.mark.skip` | missed | detected | restored |
| `@pytest.mark.skipif(True, ...)` | missed | detected | restored |
| conditional `@pytest.mark.skipif(...)` | missed | detected without evaluating condition | restored |
| `pytest.skip(...)` | missed | detected | authorized complete-skip hardening |
| module-level `pytestmark` | xfail only | skip/skipif/xfail detected | complete |
| class-level marks | xfail only | skip/skipif/xfail detected | complete |
| pytest/direct-import aliases | xfail only | skip/skipif/xfail detected | complete |
| inert strings/comments/docstrings | ignored | ignored | self-reference immunity intact |
| malformed source | parse error | `SyntaxError` | fail-safe |
| executable `fnmatch.fnmatch` | detected | detected | preserved |
| live `AUTHORIZED={"src/pcae/*"}` | detected | detected | preserved |
| exact finite file set | accepted | accepted | preserved |
| inert wildcard/fnmatch text | ignored | ignored | preserved |

Mixed executable/inert source reports only the executable node. Ordinary
English “skip”, a literal `*`, phase prose, test names, and fixture labels do
not trigger. Executable `path.startswith("src/pcae/")` is not detected: V
prohibited `fnmatch` text only, and the live wildcard detector is deliberately
limited to wildcard/fnmatch scope broadening rather than claiming every
conceivable broad predicate.

## Guard identity, history, and provenance

- `.1R.22` exact-source-set guard SHA-256 at R and K:
  `733c6b7286cdde3060c81751b03d9e2191e131c790ad7d1516393398cdbd391d`.
- Gate7 importer guard SHA-256 at R and K:
  `441b24cbf3b524f6a98817963a1e71060a390137e5ecc42e4d2c2c604197ece8`.
- REPRC-001 remains SHA-256
  `c30cb30d81ab2f4080cc592fdc9e71cfb2e0224fdb1ac452d676db0d2b3226d1`.
- Historical A/B attribution remains exactly **42** nodes, independently
  exercised by the fixed-SHA `.1R.26R.1` suite rather than scanner strings.
- Repaired A/R unexplained attributable failures remain **0**; both repaired
  nodes are green.
- `.1R.27`, `.1R.26R.1`, and `.1R.26R.1R.1` remain historically BLOCKED in
  canonical reports and completion metadata. No outcome was rewritten.
- Provenance remains explicit: raw scanner → self-reference BLOCKED → first
  AST repair → skip false negative found by BLOCKED IV → successor AST repair
  → this independent verification.

The J→K harness surface comprises the scanner helper, repair-aware historical
IV test, 31-test repair suite, exact docs/status/task/lifecycle records, and no
unrelated behavioral family. No test function was removed or renamed; no live
xfail, skip, skipif, wildcard, fnmatch broadening, or exact-fence weakening was
introduced. Adversarial source snippets are inert fixture data.

## Suites, meta-guards, and repair-suite quality

Fresh suite:
`tests/test_runtime_dispatch_1r26r1_skip_detection_repair_independent_verification_3w1r2b1r1_1r26r1r1r1.py`
— **43 passed**. It covers the 43 mandated axes, including immutable history,
real/inert AST challenges, parse failure, guard identity, provenance, 42/A-R,
broad-selection derivation, runtime/effect, and successor boundaries.

Combined fresh, repair, historical IV, reconciliation, Gate7 implementation,
and narrow-eligibility suites: **273 passed**. This includes the unchanged
`.1R.26R` test 14/15 meta-guards, the repair-aware `.1R.26R.1R.1` BLOCKED-IV
suite, `.1R.26R.1R`, `.1R.26R.1`, `.1R.26R`, Gate7 importer inventory, and
the exact-source guard.

Quality review: the 31-test repair suite uses real AST source fixtures and
does distinguish executable nodes from inert data. Its test 24 carries the
42-node result through the independently frozen node table rather than
rerunning the full A/B itself, and its test 25 checks only the two repaired
nodes; this is a non-blocking evidence-layer limitation because the combined
`.1R.26R.1` fixed-SHA suite and this IV rerun the historical attribution. It
does not overclaim prefix coverage. No repair is required.

## J/K attribution and broad sweep

The selection was independently reconstructed from all tests containing an
executable `git diff --name-only ... src/pcae` guard plus runtime-dispatch,
Gate7, narrow-eligibility, and permission-observation families.

| Side | Files | Nodes | Passed | Failed | Skipped |
|---|---:|---:|---:|---:|---:|
| J detached worktree, raw | 83 | 4,021 | 3,831 | 185 | 5 |
| K detached worktree, raw | 84 | 4,052 | 3,862 | 185 | 5 |
| current IV tree | 85 | 4,095 | 3,908 | 182 | 5 |

J and K raw failure-node sets are exactly identical: 185 common, J-only 0,
K-only 0. Three failures occur only in linked detached worktrees: two require
ignored immutable `.pcae/phase-reports` artifacts absent from linked
worktrees, and one attempts a nested worktree beneath the linked worktree's
`.git` file. Normalized functional results are therefore J 3,834/182/5, K
3,865/182/5, and current 3,908/182/5. All 182 functional failures are common
historical point-in-time/frozen-scope nodes. The 31 K-only passing nodes are
the repair suite; the additional 43 current-only passing nodes are this IV.

The expected semantic fix is exact: J accepts executable skip/skipif/direct
skip fixtures and K rejects them. No pre-existing collected test remains red
solely to encode that state transition because the historical BLOCKED-IV test
was made repair-aware: it loads J immutably and requires the current rejection.
Candidate-only unexplained failures: **0**. Unexplained repair-attributable
regressions: **0**. No xfail/fnmatch self-reference regression occurred.

## Product, contract, runtime, and unrelated finding

J→K and I→current diffs under `src/pcae` are empty. J→K and I→current diffs
under `docs/contracts` are empty. Focused N-16-4 evidence for REPRC-001, B1-B,
B2-D, Currentness B, synthetic Gate7 ALLOW, production ALLOW unreachability,
Gate8/9/10 independence, runtime unavailability, and first-effect absence is
green in the 273-test combined run.

`test_no_downstream_production_consumer_of_gate6_symbols` remains the
pre-existing stale guard over the intentional fail-closed Gate6→Gate10
dependency first introduced at `302f5aba`. J→K does not touch its production
source, hide it, or repair it. It remains separate future adjudication debt
and does not invalidate N-16-4 safety.

Runtime remains State Observed, maximum capability observe, execution
availability unavailable, plugins 0, capabilities 0. First external effect is
ABSENT: no `adapter.dispatch()` call site, Slice C, provider/network/
credential/hardware effect, or execution enablement. N-16-5, N-16-6, and
N-16-7 remain OPEN and untouched. N-23-2 remains INFO / DEFERRED NORMALIZATION
DEBT; no contract wording was normalized.

## Adjudication and successor

- `.1R.26R.1R.1R` SKIP-DETECTION REPAIR: **VERIFIED**.
- `.1R.26R.1R.1` SKIP-DETECTION BLOCKER: **CLOSED**; its phase remains
  historically BLOCKED.
- `.1R.26R.1R` EVIDENCE-HARNESS REPAIR: **SUPERSEDED BY COMPLETE VERIFIED
  DETECTION MODEL**.
- N-16-4: **IMPLEMENTED — FRESH PRODUCT-LEVEL INDEPENDENT VERIFICATION
  SUCCESSOR REQUIRED**; not CLOSED.

Repository precedent and the accepted unique-ID decision prohibit reusing the
finalized/BLOCKED `.1R.27`. Recommend exactly:

`149O.20L.7O.3W.1R.2B.1R.1.1R.27R` — Independent Verification of the N-16-4
Runtime Enforcement Gate After Reconciliation.

Do not begin it here and do not skip to N-16-5.

DELEGATED `.3` FINALIZATION / COMMIT / PUSH:
UNAUTHORIZED
