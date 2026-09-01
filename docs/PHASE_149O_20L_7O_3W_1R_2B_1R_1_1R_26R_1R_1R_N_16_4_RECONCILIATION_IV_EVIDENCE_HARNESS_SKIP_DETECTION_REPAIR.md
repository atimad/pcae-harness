# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R.1R

## N-16-4 Reconciliation IV Evidence-Harness Skip-Detection Repair

**Verdict: REPAIRED — INDEPENDENT VERIFICATION PENDING `.1R.26R.1R.1R.1`.**

## Immutable identity

| Identity | SHA |
|---|---|
| A — pre-`.1R.26` baseline | `28b8b2b70dcd4642dc45d4a3961a5218402c3c7c` |
| B — finalized `.1R.26` | `9d28f7efc3923bfca5e18b98e0a203881b256b7e` |
| R — finalized `.1R.26R` | `e52d2f8e9175015a2b344a547bea0c11058a92c8` |
| V — finalized `.1R.26R.1` BLOCKED head | `7d60eda674ec31dd2f7efafdbbfd168c358caca6` |
| H — `.1R.26R.1R` substantive harness repair | `5f894e72fb37429b221c122bfad4943be88287bd` |
| J / phase entry — finalized `.1R.26R.1R.1` BLOCKED head | `d334c74e4c987640c612f77d64a4dba6ae160692` |
| K2 — substantive skip-detection repair | `e512f96e0a8ad179b2e71506cb7ab8a0ed59ee6b` |

## Primary sources and predecessor invariant

Read directly: `PROJECT_STATUS.md`; the `.1R.25`, `.1R.26`, `.1R.27`,
`.1R.26R`, `.1R.26R.1`, `.1R.26R.1R`, and `.1R.26R.1R.1` canonical
records; V/H/current versions of
`tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py`; all three
successor harness suites; the `.1R.19R.1` / `.1R.22R` precedents; and the two
substantive `.1R.26R` guard files. Production and normative contracts were
read only.

V's executable policy was reconstructed from its exact added-line predicate:

```python
assert not any("@pytest.mark.skip" in line or "xfail" in line for line in added)
```

The skip substring directly prohibited added `pytest.mark.skip` and
`pytest.mark.skipif` decorators. The xfail substring prohibited every added
xfail spelling, including executable calls and decorators, but also caused the
historical self-text false positive. It did not literally cover a direct
`pytest.skip(...)` call; this successor adds that executable form under the
prompt's explicit complete skip-to-pass requirement. Repository search found
qualified pytest syntax canonical, with a few pytest aliases and module-level
`pytestmark` conventions, so the detector resolves actual imports rather than
assuming one spelling.

## Exact blocked adversary and root cause

The `.1R.26R.1R.1` suite's exact semantic adversary at H was:

```python
import pytest
@pytest.mark.skip(reason="proof")
def test_example():
    pass
```

H's `_executable_xfail_uses` returned `[]`, and the phase guard accepted the
fixture. A direct `pytest.skip("proof")` was also missed. The root cause was
class B from the repair prompt: skip AST forms were omitted entirely; it was
not incomplete AST traversal and not a self-reference problem.

## Scanner architecture and security matrix

The repaired scanner retains `ast.parse` and introduces
`_executable_test_weakening_uses`. It resolves `import pytest as ...`, direct
imports of `mark`/`skip`/`skipif`/`xfail`, qualified attribute chains, calls,
decorators, and module-level mark expressions. Invalid Python raises
`SyntaxError` and therefore fails closed. A `difflib.SequenceMatcher` layer
maps AST findings onto inserted/replaced new-source lines, preserving the
predecessor's newly-added-code scope without flagging an unchanged historical
skip in an otherwise touched file. The compatibility xfail view remains for
the already-verified predecessor repair suite.

| Construct | V lexical intent | H AST | K2 AST | Verdict |
|---|---:|---:|---:|---|
| executable `pytest.mark.xfail` | reject | reject | reject | preserved |
| executable `pytest.xfail(...)` | reject | reject | reject | preserved |
| executable `pytest.mark.skip` | reject | missed | reject | restored |
| executable `pytest.mark.skipif(...)` | reject by prefix | missed | reject, condition not evaluated | restored |
| executable `pytest.skip(...)` | not literally covered | missed | reject | explicit complete-skip hardening |
| pytest alias/direct import forms | lexical spelling-dependent | xfail supported | skip/skipif/xfail supported | executable-context complete |
| module-level `pytestmark` skip/skipif | prefix-dependent | missed | reject | restored |
| inert strings/comments/docstrings | false-positive prone | ignored | ignored | self-reference immunity preserved |
| real fnmatch/live wildcard scope | reject | reject | reject | unchanged |
| inert fnmatch/wildcard fixture data | false-positive prone | ignored | ignored | unchanged |

Fresh mixed fixtures confirm only the executable node is returned when prose,
comments, docstrings, and an actual call coexist. An unchanged pre-existing
executable mark plus an unrelated appended line produces no introduced-use
finding. No arbitrary condition evaluation is attempted for skipif: the
decorator itself is the prohibited construct.

## Adversarial and suite evidence

The new dedicated suite
`tests/test_runtime_dispatch_1r26r1_skip_detection_repair_3w1r2b1r1_1r26r1r1r.py`
contains 31 tests. It covers immutable identities, H false-negative
reproduction, the V predicate, qualified and aliased xfail/skip/skipif/call
forms, module-level marks, fail-closed parse behavior, inert and mixed
fixtures, wildcard/fnmatch preservation, substantive-guard hashes, historical
records, 42/A-R evidence, runtime/effect/status boundaries, and governance.

Combined focused evidence after repair:

- `.1R.26R.1R.1R` fresh repair suite;
- repair-aware historical `.1R.26R.1R.1` suite;
- unchanged `.1R.26R.1R` repair suite;
- repaired `.1R.26R` reconciliation suite;
- `.1R.26R.1` independent suite;
- substantive Gate7 and narrow-eligibility suites.

Result: **230 passed**. The exact H skip adversary is now detected; xfail and
wildcard/fnmatch self-text remains ignored.

## Fixed-SHA and broad attribution

The deterministic broad selection was re-derived from every test containing
an executable `git diff --name-only ... src/pcae` guard plus all runtime-
dispatch, Gate7, narrow-eligibility, and permission-observation test families.
It selected 84 current files / 4,052 current nodes and 83 common J files /
4,021 J nodes; the 31-node difference is exactly the new repair suite.

| Side | Passed | Failed | Skipped |
|---|---:|---:|---:|
| J | 3,834 | 182 | 5 |
| K2/current | 3,865 | 182 | 5 |

All 182 failures are common historical point-in-time/frozen-scope failures.
J-only failures: 0. K2/current-only failures: 0. Candidate-only unexplained:
**0**. Unexplained attributable regressions: **0**. The semantic fixed item is
the skip adversary: H/J accepts it, K2 rejects it. The historical IV test was
made repair-aware so it still proves the H miss from immutable source while
also requiring current rejection; its historical BLOCKED report remains
unchanged.

## Preservation and boundaries

- Substantive exact-source-set guard SHA-256:
  `733c6b7286cdde3060c81751b03d9e2191e131c790ad7d1516393398cdbd391d`.
- Substantive Gate7 importer guard SHA-256:
  `441b24cbf3b524f6a98817963a1e71060a390137e5ecc42e4d2c2c604197ece8`.
- Historical `.1R.26` attributable result: exactly **42**, preserved by
  fixed-SHA suite evidence independent of scanner strings.
- Repaired A/R unexplained attributable failures: **0**, preserved.
- `.1R.27`, `.1R.26R.1`, and `.1R.26R.1R.1` remain historically BLOCKED.
- The Gate6/Gate10 finding remains the pre-existing intentional fail-closed
  dependency plus stale historical guard first attributable at `302f5aba`;
  this phase neither hides nor repairs it.
- J-to-K2 production diff: empty. J-to-K2 normative-contract diff: empty.
  REPRC unchanged; N-23-2 remains INFO / DEFERRED NORMALIZATION DEBT.
- No test function removed or renamed; 31 added. No executable skip/xfail,
  live wildcard/fnmatch broadening, or exact-set weakening added to the live
  corpus. Adversarial snippets remain inert string data.
- Runtime remains Observed / observe / unavailable, plugins 0, capabilities
  0. First external effect remains ABSENT; no `adapter.dispatch()` call site,
  Slice C, effect-capable path, provider/network/credential/hardware effect,
  or execution enablement.
- N-16-5, N-16-6, and N-16-7 remain OPEN and untouched. N-16-4 remains
  IMPLEMENTED / NOT CLOSED.

## Adjudication and next phase

`.1R.26R.1R` EVIDENCE-HARNESS REPAIR: **REPAIRED / SUPERSEDED BY COMPLETE
EXECUTABLE-WEAKENING DETECTION — INDEPENDENT VERIFICATION PENDING.**

`.1R.26R.1R.1` SKIP-DETECTION BLOCKER: **REPAIRED — INDEPENDENT VERIFICATION
PENDING.** Its historical phase remains BLOCKED.

Recommend exactly:

`149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R.1R.1` — Independent Verification of
the N-16-4 Reconciliation IV Evidence-Harness Skip-Detection Repair.

Do not begin it here. Do not restart N-16-4 IV or begin N-16-5/6/7.

DELEGATED `.3` FINALIZATION / COMMIT / PUSH:
UNAUTHORIZED
