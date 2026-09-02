# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.6 — N-16-5 PAWA Multi-Write Completion One-Operation Integrity Repair

**Status: REPAIRED — FRESH SUCCESSOR IV PENDING. N-16-5: NOT CLOSED.**

Historical `.1R.30R.3.5` remains **BLOCKED and immutable**. This phase repairs
only its decisive finding: `HPACStoreAuthority.complete_multi_write` did not
independently enforce canonical ACTIVE → CONSUMED lifecycle state and allowed
re-entrant/concurrent completion to report success more than once.

## 1. Immutable boundaries and SHAs

- **A** — finalized `.1R.30R.3.4` implementation head:
  `c9cf99d5150200c426ba708d87fbdb62e73d8e18`.
- **V** — finalized `.1R.30R.3.5` BLOCKED IV head:
  `3968814ce1746299f4785462aa1e2e7c8e74af3b`.
- **R0** — `.1R.30R.3.6` phase-entry SHA:
  `3968814ce1746299f4785462aa1e2e7c8e74af3b`.
- Entry state: clean `main`, `origin/main..HEAD = 0`; `.1R.30R.3.5` latest
  completed phase; runtime `Observed / observe / unavailable`; zero plugins
  and capabilities; first external effect absent/unreachable.

The SHAs were derived from `git log` and `git rev-parse`, not inherited from
phase prose.

## 2. Historical reproduction and root cause

Before editing, a disposable detached worktree at A reproduced both defects:

1. canonical multi-write capability → first `complete_multi_write` succeeds →
   second call also succeeds;
2. eight callers race on one ACTIVE issuance → all eight report success.

The two unchanged blocking nodes from `.1R.30R.3.5` reproduced the same
failure on R0. The exact cause was a lock-separated lookup followed by an
unconditional object-local `_spent` mutation and registry mutation:

- no canonical `record.state is ACTIVE` precondition;
- no canonical scope/class revalidation at completion;
- check and ACTIVE → CONSUMED transition were not one critical section.

`require_writer` already established the correct authority model: exact issued
object identity, registry-bound role/subject/class, canonical lifecycle state,
and object-local `_spent` only as defense in depth.

## 3. Narrow repair

Only `src/pcae/core/hpac_foundation.py` changes in production.

The existing canonical issuance helper `_mark_capability_consumed` now accepts
a completion-only `require_multi_write` mode. Under the existing
`_ISSUANCE_REGISTRY_LOCK`, it requires:

1. exact registry membership and exact canonical object identity;
2. registry-bound role and subject matching the object's completion scope;
3. registry authority class matching the completing authority;
4. `_single_use` and `_multi_write` enabled;
5. canonical lifecycle ACTIVE and object-local `_spent == False`.

It then marks the object spent and transitions the canonical registry record
ACTIVE → CONSUMED inside that same critical section. A racing caller therefore
observes CONSUMED and raises the existing stale-authority result:
`HPACAuthorityError("writer capability is spent (one-operation lifetime exhausted)")`.
PAWA already maps this semantic class to the frozen `capability_stale` code.

Registry state is authoritative: resetting `_spent` after completion cannot
restore authority. No Python-GIL assumption carries security meaning.

The default helper behavior used by ordinary `record_write` remains unchanged.
No new helper owns the issuance registry, preserving the independently verified
closed helper inventory.

## 4. Lifecycle conclusions

- `_multi_write` means one predeclared bounded multi-artifact enrollment
  transaction, not reusable authority (HPAC-PAWA-REQ-106/107).
- Component writes remain permitted while the issuance is ACTIVE; they do not
  spend a multi-write capability individually.
- `complete_multi_write` is the sole terminal transition for that transaction.
- After completion, all component writes and completion calls fail closed.
- Failure before completion leaves lifecycle ACTIVE under the frozen model; it
  does not fabricate completion or add replay semantics.
- Invalid scope/type/non-issued calls do not advance lifecycle and do not
  consume unrelated valid authority.
- Second completion is rejection, not idempotent success, matching the method
  docstring and the contract's one-operation rule.

## 5. Test changes and results

### Fresh repair suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_6_multi_write_completion_integrity_repair.py`
contains **46 collected tests** covering fixed-SHA reproduction, direct replay,
eight-way concurrency, exact stale result, registry-state dominance, `_spent`
reset, reconstructed/non-issued capability, production-vs-fixture authority,
ordinary non-multi-write capability, wrong principal/transaction/role/mutation
class, failure-state integrity, component writes, normal RHAMP enrollment,
contract/schema/source identity, Gate/runtime/presentation/effect fences, and
the shared-lock structural proof. Result: **46 passed**.

### Permanent product regression

The normal `.1R.30R.3.4` product suite gains one permanent regression:
one canonical multi-write issuance has at most one successful completion.
The suite now collects **125 tests** and passes **125/125**.

### Historical blocking nodes

Both `.1R.30R.3.5` blocking nodes now pass. Once the completion rejection made
the next assertion reachable, its post-completion sidecar-write expectation was
corrected from the foundation exception to the store's canonical wrapper
`RhampCredentialSidecarError`. The security expectation was not weakened: the
write must and does fail. The historical report and BLOCKED verdict are
unchanged.

### Governing affected suites

The dedicated repair suite, full `.1R.30R.3.4` product suite, full
`.1R.30R.3.5` IV suite, `.1R.30R.3.2.1` repair, `.1R.30R.3.2.1.1` IV, and
Slice-1 PAWA suite pass **340/340** with deterministic `-n 0` execution.

### Fixed-SHA attribution and broad sweep

The common 39-file HPAC/PAWA/RHAMP/FIDO2/consumer-guard set produced:

| Tree | Passed | Failed | Skipped |
|---|---:|---:|---:|
| A (`c9cf99d5`) | 1,758 | 48 | 3 |
| repair candidate, pre-commit | 1,761 | 46 | 3 |

There are zero unexplained functional candidate-only failures. Two
candidate-only nodes are working-tree/unpushed scope guards and are expected to
clear after the governed commit; four A-only historical guards were repaired by
intervening committed phases. The intentional defect attribution is A fails / R
passes for second and concurrent completion. Post-commit guard verification is
required before finalization.

No-test-weakening audit: zero existing test definitions removed or renamed;
zero new `skip`, `skipif`, `pytest.skip`, or `xfail`; zero wildcard/fnmatch
broadening; no source/consumer guard weakened.

## 6. Byte-identity and no-go proof

Against R0:

- every normative contract is byte-unchanged: RHAMP-001 v1.0,
  HPAC-PAWA-001 v1.1, HPAC-001 v2.1, and all other `docs/contracts/**`;
- `CredentialRecord` and `_CREDENTIAL_ALLOWED_FIELDS` are byte-unchanged;
- RHAMP enrollment, sidecar, counter-state, CTAP2 provider,
  `FIDO2HumanAuthenticator`, `hpac_verifier`, deterministic CI selection,
  approval presentation, Gate 5, Gate 9, runtime, and effect surfaces are
  byte-unchanged;
- `HPACWriterCapability.__slots__` remains the same seven-slot tuple;
- `_CapabilityIssuanceRecord.__slots__` and the single issuance-registry shape
  are unchanged;
- PAWA remains the closed 21-code vocabulary and RHAMP remains the closed
  41-code terminal vocabulary;
- no dependency changes.

No protected presentation or `pcae-protected-local-presentation/1.0`; no
`require_real_assurance` Gate 5/9 wiring; no N-16-6 or N-16-7; no Slice C; no
first external effect; no execution enablement.

## 7. Verdict and successor

```
HPACStoreAuthority.complete_multi_write terminal lifecycle: REPAIRED — IV PENDING
MULTI-WRITE one-operation semantics:                      REPAIRED — IV PENDING
PAWA non-bearer:                                         UNCHANGED / VERIFIED BASELINE PRESERVED
RHAMP registration:                                     UNCHANGED / VERIFIED BASELINE PRESERVED
RHAMP counter:                                          UNCHANGED / VERIFIED BASELINE PRESERVED
FIDO2 authentication mechanism:                         UNCHANGED / VERIFIED BASELINE PRESERVED
historical .1R.30R.3.5:                                 BLOCKED / PRESERVED
N-16-5:                                                 NOT CLOSED
N-16-6 / N-16-7:                                        OPEN / UNTOUCHED
N-23-1 / N-23-2:                                        INFO / INFO-DEFERRED, UNCHANGED
Runtime:                                                Observed / observe / unavailable
First external effect:                                  ABSENT / UNREACHABLE
```

The fresh CPIPC-valid successor is:

**`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.6.1` — Independent Verification of
the N-16-5 PAWA Multi-Write Completion One-Operation Integrity Repair.**

The nested `.3.6.1` form follows the established repair → nested-IV convention
used by `.3.2.1` → `.3.2.1.1`; it is recommended, not reserved, requires its
own explicit human authorization, and is not begun here.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` is preserved. No
delegated worker was used. This primary operator session alone performs the
governed commit, push, completion, and notification under explicit authority.
