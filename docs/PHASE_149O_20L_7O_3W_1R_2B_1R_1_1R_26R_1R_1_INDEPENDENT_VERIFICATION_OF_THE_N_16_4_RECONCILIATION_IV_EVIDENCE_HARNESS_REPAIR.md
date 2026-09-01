# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R.1

## Independent Verification of the N-16-4 Reconciliation IV Evidence-Harness Repair

**Verdict: BLOCKED — `.1R.26R.1R` NOT VERIFIED.**

## Immutable identity

| Identity | SHA |
|---|---|
| A — pre-`.1R.26` | `28b8b2b70dcd4642dc45d4a3961a5218402c3c7c` |
| B — finalized `.1R.26` | `9d28f7efc3923bfca5e18b98e0a203881b256b7e` |
| R — finalized `.1R.26R` | `e52d2f8e9175015a2b344a547bea0c11058a92c8` |
| V — finalized `.1R.26R.1` BLOCKED head | `7d60eda674ec31dd2f7efafdbbfd168c358caca6` |
| H — substantive `.1R.26R.1R` repair | `5f894e72fb37429b221c122bfad4943be88287bd` |
| I — this IV entry / finalized `.1R.26R.1R` lifecycle head | `ee473b94f2411b6d7776a15e6585e834f82008a4` |

The distinction between H and I is intentional: H owns the scanner changes;
I is the immutable pushed/finalized phase head containing later documentation
and lifecycle records.

## Primary sources inspected

`PROJECT_STATUS.md`; the `.1R.25`, `.1R.26`, `.1R.27`, `.1R.26R`,
`.1R.26R.1`, and `.1R.26R.1R` canonical records; the V and H forms of
`tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py`; the
`.1R.26R.1` IV and `.1R.26R.1R` repair suites; the `.1R.19R.1` and `.1R.22R`
self-reference precedents; phase-identity rules; both substantive
reconciliation guards; production Gate 7/permission/Gate 8/Gate 9/Gate 10
sources and the frozen N-16-4 contracts as read-only evidence.

## V to H attribution

The three previously reported concrete nodes reproduce exactly: V has three
failures and H has three passes.

| Node | V | H | Root class / mechanism |
|---|---:|---:|---|
| `.1R.26R.1::test_01_sha_chain_is_reconstructed_from_git` | FAIL | PASS | temporal self-reference: moving `HEAD == R` replaced by immutable V ancestry |
| `.1R.26R::test_14_no_test_weakening_in_the_r26r_diff` | FAIL | PASS | raw self-text expected-failure scan replaced by AST inspection |
| `.1R.26R::test_15_no_wildcard_or_fnmatch_introduced_in_the_r26r_diff` | FAIL | PASS | raw self-text fnmatch scan replaced by AST inspection |

Thus the two broad defect families are harness self-reference/currentness
(the SHA node and test 14) and raw wildcard/fnmatch self-text (test 15). The
third concrete node is non-product temporal harness debt, not a third product
or reconciliation defect.

## Blocking independent finding

V's test 14 enforced both sides of this exact predicate at line 206:

```python
assert not any("@pytest.mark.skip" in line or "xfail" in line for line in added)
```

H replaces it with `_executable_xfail_uses(new) == []`. That AST helper
recognizes executable `pytest.mark.xfail` decorators and `pytest.xfail(...)`
calls, including its supported aliases, and ignores inert strings/comments/
docstrings. It has no skip node, alias, attribute, decorator, or call rule.

Fresh independent executable fixtures established:

| Challenge | Result at H |
|---|---|
| real `@pytest.mark.xfail(...)` | detected |
| real `pytest.xfail(...)` | detected |
| inert xfail strings/comments/docstrings | ignored as intended |
| real `@pytest.mark.skip(...)` | **not detected** |
| real `pytest.skip(...)` | **not detected** |
| inject real skip decorator through `_changed_test_sources`, then execute test 14 | **guard passes — false negative** |

This is not merely a missing repair-suite assertion. It is a material
weakening of the predecessor no-test-weakening invariant: a future changed
test can be converted to skip-to-pass without test 14 detecting it. The
`.1R.26R.1R` report says the original security assertions remain executable
and green and that no skip-to-pass was added, but its 22-test repair suite
contains no executable skip adversary. Its security-strength claim is
therefore incomplete.

The affected artifact is
`tests/test_runtime_dispatch_1r26r_scope_fence_reconciliation.py`, helper
`_executable_xfail_uses`, consumed by
`test_14_no_test_weakening_in_the_r26r_diff`. Classification:
**verification-harness security-guarantee regression attributable to
`.1R.26R.1R`; not reconciliation, production, or contract debt.** Repair is
required, and this IV is not authorized to perform it.

## Preserved evidence and early-stop disposition

- The xfail and wildcard/fnmatch self-match repairs work for their advertised
  direct cases; the repaired and repair suites passed 32/32 alongside this
  BLOCKED evidence suite.
- The two substantive `.1R.26R` guards are byte-identical R to H; current
  SHA-256 values remain `733c6b7286cdde3060c81751b03d9e2191e131c790ad7d1516393398cdbd391d`
  and `441b24cbf3b524f6a98817963a1e71060a390137e5ecc42e4d2c2c604197ece8`.
- V to H production diff and normative-contract diff are empty. R to H does
  not change either substantive guard.
- The `.1R.26R.1` canonical verdict remains `BLOCKED`; its successor
  annotation does not convert that outcome.
- Historical fixed-SHA result 42, repaired A to R zero-attributable result,
  and the unrelated Gate6-to-Gate10 stale historical guard remain carried
  exactly as prior independently established evidence. They were not
  re-adjudicated after the valid early stop.
- The Gate6/Gate10 finding remains pre-H, intentional fail-closed dependency
  plus stale historical guard; this repair neither hides nor fixes it.
- Runtime remains Observed / observe / unavailable, plugins 0, capabilities
  0. First external effect remains ABSENT; no Slice C or effect-capable path.
- N-16-5, N-16-6, and N-16-7 remain OPEN and untouched. N-23-2 remains INFO /
  DEFERRED NORMALIZATION DEBT.

The mandatory broad sweep, historical A/B reruns, and successful-phase
adjudication sequence were not continued after this explicit early-stop
condition. Doing so cannot establish the required no-weakening property and
would not cure the blocker.

## Adjudication

- `.1R.26R.1R` EVIDENCE-HARNESS REPAIR: **NOT VERIFIED**.
- `.1R.26R.1` EVIDENCE-HARNESS BLOCKER: **NOT CLOSED**; `.1R.26R.1` remains
  historically BLOCKED.
- N-16-4: **IMPLEMENTED — FRESH SUCCESSOR INDEPENDENT VERIFICATION REQUIRED**;
  not CLOSED.
- Production diff: empty. Contract diff: empty. Runtime/effect drift: none.
- Candidate-only attribution beyond the discovered harness false negative:
  not run after authorized early stop; no product regression was observed.

Required next phase, following the repository's append-`R` repair precedent
and unique-phase-ID rule:

`149O.20L.7O.3W.1R.2B.1R.1.1R.26R.1R.1R` — N-16-4 Reconciliation IV
Evidence-Harness Skip-Detection Repair.

It must add syntax-aware executable skip decorator/call detection (and
supported aliases consistent with repository conventions) without restoring
raw self-text matching, then receive its own independent verification. Do not
begin `.1R.27R`, N-16-5/6/7, Slice C, or execution work first.

DELEGATED `.3` FINALIZATION / COMMIT / PUSH:
UNAUTHORIZED

