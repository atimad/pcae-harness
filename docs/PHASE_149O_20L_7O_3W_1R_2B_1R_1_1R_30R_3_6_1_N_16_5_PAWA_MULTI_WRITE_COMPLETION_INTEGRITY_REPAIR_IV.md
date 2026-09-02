# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.6.1 — Independent Verification of the N-16-5 PAWA Multi-Write Completion One-Operation Integrity Repair

**Status: INDEPENDENTLY VERIFIED. N-16-5: NOT CLOSED.**

The sole blocker identified by historical `.1R.30R.3.5` and repaired by
`.1R.30R.3.6` is independently verified. Historical `.1R.30R.3.5` remains
**BLOCKED and immutable**; the current merged RHAMP registration/authentication
mechanism is independently verified through the combined `.3.5` + `.3.6` +
`.3.6.1` evidence. Protected presentation, Gate real-assurance consumption,
and mandatory real-CTAP2-hardware certification remain unimplemented or
unperformed, so N-16-5 remains **NOT CLOSED**.

## 1. Immutable boundaries

- **A** — finalized `.1R.30R.3.4` implementation head:
  `c9cf99d5150200c426ba708d87fbdb62e73d8e18`.
- **B** — finalized `.1R.30R.3.5` BLOCKED IV head:
  `3968814ce1746299f4785462aa1e2e7c8e74af3b`.
- **R** — finalized `.1R.30R.3.6` repair head:
  `e0f79220539c80eebfc52cc169a82a37f14b8f91`.
- **V** — `.1R.30R.3.6.1` phase-entry SHA:
  `e0f79220539c80eebfc52cc169a82a37f14b8f91` (V == R).

All four were independently derived from Git subject history and `rev-parse`.
At entry the tree was clean, `origin/main..HEAD = 0`, `.3.6` was the latest
complete phase, no governed phase was active, and runtime was
`Observed / observe / unavailable` with zero plugins/capabilities.

## 2. Independent historical/current contrast

A disposable detached worktree at immutable A reproduced both defects without
relying on report prose:

1. first completion succeeds and a second completion also succeeds;
2. eight racing completion calls all report success (`8/8`).

The identical cases against R produce:

1. first completion succeeds and canonical state becomes `CONSUMED`;
2. the second call raises the existing stale result,
   `HPACAuthorityError("writer capability is spent (one-operation lifetime exhausted)")`;
3. exactly one of eight racing callers succeeds and all seven losers return
   that same stale result.

This is the intentional A-fails/R-passes security delta.

## 3. Root cause and repaired lifecycle

Historical A's `complete_multi_write` performed a separate registry lookup,
then unconditionally marked the object spent and the registry consumed. It had
no canonical `ACTIVE` precondition, no completion-time canonical scope/class
validation, and no single synchronization boundary around check-and-consume.

R routes completion through the existing `_mark_capability_consumed` helper's
`require_multi_write=True` branch. Under `_ISSUANCE_REGISTRY_LOCK`, that branch
requires:

- a canonical issuance record and exact capability-object identity;
- registry role/subject equal to the capability's current completion scope;
- the expected authority class;
- `_single_use` and `_multi_write` eligibility;
- canonical lifecycle `ACTIVE` and object-local `_spent == False`.

It then calls `_mark_spent` and performs `ACTIVE → CONSUMED` before releasing
the same lock. There is no lock gap and no GIL-based security assumption.

Canonical registry state is authoritative. Resetting `_spent` after canonical
consumption cannot restore authority. The inverse inconsistency — object says
spent while registry says ACTIVE — also fails closed and leaves registry state
unchanged. A reconstructed shell with copied fields/seal is absent from the
registry and fails closed.

## 4. Scope and lifecycle challenges

Fresh independent tests verify:

- non-issued/reconstructed capability: rejected;
- fixture capability at a production authority: rejected;
- ordinary non-multi-write capability: rejected by completion and left ACTIVE;
- wrong principal/transaction/role/mutation class: rejected without consuming
  the valid issuance;
- correcting an invalid object-local scope mutation restores only the original
  canonical scope, after which one legitimate completion succeeds;
- multiple bounded component writes remain possible while ACTIVE;
- completion is the sole terminal transition for the multi-write transaction;
- post-completion component writes and completion calls reject;
- an enrollment failure before protected writes does not call completion;
- ordinary one-write `record_write` semantics remain unchanged.

The method docstring's “exactly once”, second-call, and fail-closed claims now
match implementation. PAWA continues to use the frozen `capability_stale`
semantic; PAWA remains 21 codes and RHAMP remains 41 terminal codes.

## 5. Product and regression evidence

### Fresh IV suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_6_1_multi_write_completion_integrity_repair_iv.py`
contains 46 independent tests. Result: **46 passed**.

### Governing suites

The fresh IV, `.3.6` repair, `.3.5` IV, `.3.4` product, `.3.2.1` repair,
`.3.2.1.1` IV, and Slice-1 PAWA suites ran deterministically with `-n 0`:
**386 passed, 0 failed, 0 skipped, 0 errors**.

The two exact historical blocking nodes were separately rerun unchanged:
**2 passed**. The `.3.4` product surface includes the permanent
`test_99_multi_write_completion_is_single_success_per_canonical_issuance`;
concurrency remains permanently covered by `.3.5`, `.3.6`, and this IV.

Targeted RHAMP registration/bootstrap, rpIdHash, getAssertion, full real
assertion sequence, signature rejection, UP rejection, counter update,
deterministic isolation, plus the full `test_hpac_verifier.py` suite:
**35 passed**.

## 6. Fixed-SHA attribution and broad sweep

Forty common affected test files were independently selected from immutable A
and R by direct references to HPAC foundation/writer/RHAMP/PAWA symbols and run
in clean detached worktrees:

| Tree | Nodes | Passed | Failed | Skipped | Errors |
|---|---:|---:|---:|---:|---:|
| A | 1,826 | 1,776 | 47 | 3 | 0 |
| R | 1,827 | 1,777 | 47 | 3 | 0 |

All 47 failures are common historical/baseline guard or deliberately failing
old-IV debt. R adds one passing permanent regression node. A-only failures: 0.
R-only failures: 0. R-only unexplained functional regressions: **0**.

The direct fixed-SHA behavioral contrast separately records the intended
difference: A permits the sequential replay and 8/8 concurrent successes; R
rejects replay and permits exactly 1/8 concurrent successes.

## 7. No-test-weakening and exact repair scope

For B→R:

- zero existing `def test_` removed or renamed;
- zero `skip`, `skipif`, `pytest.skip`, or `xfail` added;
- zero wildcard/fnmatch broadening;
- zero source/consumer guard weakening.

The only existing `.3.5` assertion adjustment preserves the original security
expectation while naming the sidecar store's canonical wrapper exception.

`git diff --name-status B R -- src/pcae scripts pyproject.toml` is exactly:

```text
M  src/pcae/core/hpac_foundation.py
```

No other production source changed. `HPACWriterCapability.__slots__` remains
the seven-slot form ending in `_multi_write`; `_CapabilityIssuanceRecord` and
the single process-local issuance registry retain their existing shape.

## 8. Byte identity and no-go proof

B→R byte identity holds for:

- all normative contracts, including RHAMP-001 v1.0, HPAC-PAWA-001 v1.1,
  and HPAC-001 v2.1;
- `CredentialRecord` and `_CREDENTIAL_ALLOWED_FIELDS`;
- RHAMP enrollment, sidecar, counter-state, CTAP2, client-context, assertion
  verification, and terminal-reason modules;
- `FIDO2HumanAuthenticator` and `hpac_verifier`;
- deterministic CI provider selection;
- approval presentation, Gate 5, Gate 9;
- permission/runtime/effect surfaces.

There is no `pcae-protected-local-presentation/1.0` production acceptance, no
`require_real_assurance` Gate wiring, no N-16-6/N-16-7/Slice-C change, no
first external effect, and no execution enablement. Runtime remains
`Observed / observe / unavailable`, zero plugins/capabilities. N-23-1 remains
INFO and N-23-2 remains INFO / DEFERRED.

## 9. Independent verdicts

```text
complete_multi_write canonical lifecycle:          VERIFIED
ACTIVE→CONSUMED atomicity:                          VERIFIED
sequential re-entry rejection:                     VERIFIED
concurrent completion one-success bound:           VERIFIED
registry-state dominance:                          VERIFIED
PAWA non-bearer preservation:                      VERIFIED
ordinary one-write preservation:                   VERIFIED
RHAMP enrollment regression:                       VERIFIED
repair scope:                                      VERIFIED
```

The specific blocker preventing `.3.5` from closing is repaired and
independently verified. Historical `.3.5` remains BLOCKED / immutable.
Current merged RHAMP registration/authentication is **IMPLEMENTED +
INDEPENDENTLY VERIFIED** through the combined evidence of `.3.5` (all other
surfaces), `.3.6` (repair), and `.3.6.1` (sole-blocker IV).

N-16-5 remains **NOT CLOSED** because protected presentation, Gate
real-assurance consumption, and mandatory real-CTAP2-hardware certification
remain outstanding.

## 10. Successor

The exact next phase is:

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4` — N-16-5 Protected Human-Approval
Presentation and Real-Assurance Consumption Implementation.**

It may implement the protected local presentation helper,
`pcae-protected-local-presentation/1.0`, informed-intent presentation,
trusted verifier/consumer integration, and frozen Gate 5/Gate 9
`require_real_assurance` consumption. It may not begin N-16-6, N-16-7,
Slice C, a first external effect, or execution enablement. It is recommended,
not begun, and requires its own explicit human authorization.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` is preserved. No
delegated worker was used. This primary human-authorized operator session
alone performs this phase's governed lifecycle.
