# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5.2 Complete — AuthenticatedHumanPrincipal Trusted-Construction and Provenance Blocking Repair

Status: completed.

Phase-entry commit (HEAD at start): `befd7a5a0b2e7dff037e973f9df7bdb5f5d7533f`.

Canonical hand-authored phase doc:
`docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_5_2_AUTHENTICATEDHUMANPRINCIPAL_TRUSTED_CONSTRUCTION_AND_PROVENANCE_BLOCKING_REPAIR.md`.

## Technical verdict

**F1 REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**

Repairs `.1R.5.1`'s BLOCKING finding: `AuthenticatedHumanPrincipal`'s
`HPAC-REQ-056` trusted-construction seal was enforced only inside
`__init__`, so `object.__new__` bypassed it entirely, producing an
`isinstance`-true, `PRODUCTION`-assurance forged instance without any
verification ever running.

## Why blocking `object.__new__` itself is not the fix

Independently confirmed: `object.__new__(AuthenticatedHumanPrincipal)`
is a call to a different, unrelated method than any subclass `__new__`
override — it bypasses the subclass's method-resolution order entirely,
so overriding `AuthenticatedHumanPrincipal.__new__` has zero effect on
this exact attack. No field, sentinel, or digest stored on the instance
survives being copied by a caller who reproduces the object's
`__slots__` state via `object.__new__` + `setattr`. Object shape,
constructor path, and non-serializability are therefore not sufficient
proof of provenance.

## Repair architecture

A new verifier-owned, identity-keyed provenance boundary:

```python
def is_verifier_authenticated_principal(candidate: object) -> bool:
    return (
        isinstance(candidate, AuthenticatedHumanPrincipal)
        and candidate in _AUTHENTIC_PRINCIPAL_REGISTRY
    )
```

`_AUTHENTIC_PRINCIPAL_REGISTRY` is a module-private set populated **only**
by `verify_human_authentication`'s own return path. Membership is keyed
by Python object identity (the class's `__hash__`/`__eq__` were already
identity-only, independently confirmed sound by `.1R.5.1`). A
caller-manufactured lookalike — direct construction (even with the real
module-private seal), `object.__new__`, a subclass attempt (now refused
at class-definition time via `__init_subclass__`), `copy`/`deepcopy`/
`pickle` (still `TypeError` via `__reduce__`, unchanged), manual
`__slots__` state copying, or reflection — is a different Python object
and can never be a registry member, regardless of field values.
`is_real_runtime_eligible` and every other field remain plain data, not
authority; every future consumer of a verification result must call
`is_verifier_authenticated_principal` first (this module still has zero
production consumers today, so no call site exists to update yet). The
`__init__` seal check is retained as defense-in-depth for the ordinary
direct-construction mistake, documented as not itself the trust
boundary.

**Design trade-off, documented:** the registry is a plain (strong-
reference) `set`, not a `weakref.WeakSet`, because adding `"__weakref__"`
to `__slots__` would break `.1R.5.1`'s preserved historical evidence test
(`test_verifier_result_attribute_copy_produces_a_distinguishable_object`,
which iterates the literal `__slots__` tuple and `setattr`s every entry —
`__weakref__` has no attribute setter). Verified results therefore
remain referenced by the module for the process lifetime; still never
persisted, still non-serializable, still lost on restart. Accepted given
zero production consumers exist today; flagged for revisit if/when a
real production consumer is wired.

## F1–F4 disposition

- **F1 — REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED.**
- **F2, F3 — unchanged, deferred.** Not technically coupled to F1's
  result-object provenance defect.
- **F4 — not self-closed.** The existing overclaiming test
  (`tests/test_hpac_verifier.py::test_caller_constructed_verifier_result_rejected`)
  is preserved unmodified; this phase's new tests instead use accurately
  scoped names for each path they cover, so the overclaiming pattern is
  not repeated in new evidence.

## Historical F1 test handling

`tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py` is
preserved **unmodified**. Two of its tests remain failing, permanently,
by design:

- `test_object_dunder_new_bypasses_trusted_construction_seal` asserts
  `not isinstance(forged, AuthenticatedHumanPrincipal)` — not achievable
  in Python without a metaclass `__instancecheck__` override, which was
  judged far more invasive than this phase's scope, and not attempted.
- `test_forged_via_object_new_would_report_real_runtime_eligible` asserts
  `is_real_runtime_eligible is False` on a hand-forged instance — a
  data-shape property this phase deliberately did not entangle with the
  authority registry (see the data/authority distinction above).

Both are exactly the two tests `.1R.5.1` itself reported as the evidence
of F1's existence, and remain that record. This phase's repair is proven
by the new suite below, not by rewriting these assertions.

## Tests

```
tests/test_hpac_verifier_repair_3w1r2b1r1115a2.py
20 passed
```

Fresh suite covering direct construction (with and without the real
seal), `object.__new__`, subclass refusal, shallow/deep copy, pickle,
manual slot-state copy, reflection, forged-with-identical-fields,
non-principal inputs, cross-call non-equality, registry lifetime/
strong-reference behavior, deterministic `NON_REAL` regression, and
zero PB/runtime/Gate-9 imports / zero production consumers.

Existing and historical suites re-run unmodified:

```
tests/test_hpac_verifier.py
27 passed

tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py
27 passed, 2 failed (permanently, by design — see above)
```

## Fast Green / regression scope

Full 20-file HPAC-family test scope run as a `git stash` A/B against
phase-entry commit `befd7a5a`:

```
Baseline:   409 passed, 54 failed
Candidate:  429 passed, 54 failed
```

The 54 failures are identical (by test ID) between baseline and
candidate — all pre-existing, unrelated to `hpac_verifier.py`. The +20
are this phase's new suite. **Unexplained attributable regressions in
this scope: 0.**

Full 38,100-test repository suite: **not run this phase.** `pytest -n
auto` produces pre-existing xdist worker-collection-mismatch errors on
both baseline and candidate (confirmed identical via the same stash A/B)
— the already-carried "xdist random-UUID parametrization instability"
tooling debt, not introduced or worsened by this phase. A full serial
run was not attempted, disclosed as an explicit scope limitation
consistent with `.1R.5.1`'s own precedent (§15), and judged acceptable
because `hpac_verifier.py` has zero production consumers anywhere in
`src/pcae` — no code outside the 20-file HPAC-family scope could
possibly be affected by this phase's change.

## Consumer inventory

```
grep -rn "hpac_verifier|AuthenticatedHumanPrincipal|verify_human_authentication" src/pcae
  → one hit outside hpac_verifier.py itself: a comment in human_authenticator.py
```

Zero production consumers of `hpac_verifier.py` exist. PB, runtime
authority, and Gate 9 (`runtime_invocation_authority_consumption.py`)
remain unreferenced by the verifier (AST-checked, independently
re-confirmed by this phase's own new test).

## Governance verdict

**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED** (historical
incident, preserved, not revisited). This phase's commit/finalize/push
sequence was performed only by the primary operator the human explicitly
authorized for this exact phase ID.

## No-Go confirmation

- No B1, B7, N1, or N2 production repair.
- No Permission Broker integration.
- No Runtime Enforcement or Shell Gate activation.
- No real FIDO2, WebAuthn, CTAP, enrollment, or credential operation.
- No protected approval UI, approval CLI, or enrollment CLI.
- No provider, network, subprocess, hardware, or external runtime effect.
- No Gate-9 production wiring, Gate-10 dispatch, or PB/runtime-dispatch
  consumption.
- Only one production file modified: `src/pcae/core/hpac_verifier.py`.
  `hpac_foundation.py`, `hpac_lifecycle.py`, and the B1/B7/N1/N2 files
  untouched (task scope explicitly forbade editing them this phase).
- No normative contract modification.
- No revert, force push, history rewrite, or hook bypass.
- No `.1R.5.2.1` (independent verification) work begun.

Runtime remains `Observed / observe / unavailable`. POL-005 unchanged.

## Commit and push state

Phase commits:

- `40d742c3cf133d77ec1040c0613a27ab1360a853`
- `817cdadbb110aeb0ab8cc1f7bf771d8529b14f9f`
- `e8549d8009635c0b4d2763c00e6027a56d0412f6`

Pushed: pending (to be finalized after `pcae push`).

## Recommended next phase

**Not canonically assigned this phase** (no-invent-an-ID constraint).
Recommended: `149O.20L.7O.3W.1R.2B.1R.1.1R.5.2.1` — Independent
Verification of AuthenticatedHumanPrincipal Trusted-Construction and
Provenance Repair. **Requires separate explicit human authorization
before starting.**
