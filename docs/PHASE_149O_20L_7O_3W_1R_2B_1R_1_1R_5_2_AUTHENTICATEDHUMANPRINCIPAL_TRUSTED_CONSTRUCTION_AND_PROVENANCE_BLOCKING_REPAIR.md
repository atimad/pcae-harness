# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5.2 — AuthenticatedHumanPrincipal Trusted-Construction and Provenance Blocking Repair

## 1. Identity

| Fact | Value |
|---|---|
| Phase ID | `149O.20L.7O.3W.1R.2B.1R.1.1R.5.2` |
| Title | AuthenticatedHumanPrincipal Trusted-Construction and Provenance Blocking Repair |
| Repository | `~/repos/pcae-harness` |
| Phase-entry commit | `befd7a5a0b2e7dff037e973f9df7bdb5f5d7533f` |
| Authorization | Human directly authorized this exact phase ID and scope in the governing prompt; the operator executing it is the primary operator, not a delegated worker. |
| Scope | Narrow repair of F1 only. No `.1R.5.2.1`, no B1/B7/N1/N2 repair, no PB/runtime-authority integration, no real FIDO2/UI. |

## 2. `.1R.5.1` verdict entering this phase

```text
NOT VERIFIED — AuthenticatedHumanPrincipal trusted-construction seal
bypassable via object.__new__ (BLOCKING)
```

All other major trust-bearing verifier areas were independently verified clean by `.1R.5.1`. This phase is therefore a narrow repair, not a verifier redesign.

## 3. F1–F4 exact findings (recovered verbatim from `.1R.5.1` §19)

| Finding | Severity | Class | Exact text |
|---|---|---|---|
| F1 | **BLOCKING** | authenticated-result provenance defect | "`AuthenticatedHumanPrincipal`'s trusted-construction seal (HPAC-REQ-056) is enforced only in `__init__`; `object.__new__` bypasses it entirely, producing an `isinstance`-true, `is_real_runtime_eligible=True` forged instance without any verification ever running." |
| F2 | NON-BLOCKING | verifier trust defect / implementation scope defect | HPAC-REQ-054 step 4 (independent challenge-digest recomputation from canonical challenge state) is not implemented; only a string-equality cross-check against the lifecycle genesis binding exists. Bounded by the absence of any standalone canonical Challenge store in the current foundation. |
| F3 | NON-BLOCKING | governance/tooling debt (inherited) | The `.1R.4` planning document mislabels HPAC-REQ-054 as an "eight-step algorithm" and silently omits contract step 4 — pre-existing debt from an already-closed phase, not introduced by `.1R.5`. |
| F4 | NON-BLOCKING | test-quality / evidence defect | `tests/test_hpac_verifier.py::test_caller_constructed_verifier_result_rejected` overclaims relative to what it tests (only the `__init__` path, not `object.__new__`). |

### 3.1 Disposition of each finding for this phase

- **F1 — repaired this phase** (see §5–§9 below).
- **F2 — deferred, unchanged.** Not technically coupled to F1: F1 is about the *result object's* provenance after all HPAC-REQ-054 steps run; F2 is about a specific step's incompleteness (challenge-digest recomputation), gated on a canonical Challenge store that does not exist. Fixing F1 requires no change to step 4's logic. Left exactly as `.1R.5.1` classified it: **NON-BLOCKING given current foundation state.**
- **F3 — deferred, unchanged.** Documentation/governance debt inherited from `.1R.4`; unrelated to the result-object construction boundary. Not touched.
- **F4 — inseparable from F1, addressed as a side effect, not rewritten.** `.1R.5.1`'s critique of `test_caller_constructed_verifier_result_rejected` is that its name overclaims what it tests. This phase does not rename or rewrite that existing test (it is unmodified, still passing, still testing exactly what it always tested: the `__init__`-with-wrong-seal path). Instead, this phase's own new test file adds tests with names that accurately describe what they cover (direct-constructor, `object.__new__`, subclass, copy, deepcopy, state-copy, reflection, pickle — each named for the exact path it exercises), so the overclaiming problem does not recur in the new evidence. F4 remains formally open as a description of the *existing* test's name; it is not self-closed here.

## 4. HPAC-REQ-056 independent derivation

Recovered verbatim from `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` §19:

> **HPAC-REQ-056.** `AuthenticatedHumanPrincipal` is a trusted-construction type: it SHALL be producible only as the return value of a successful §18 verification sequence, never by direct construction from caller-supplied strings or dicts. This is the identical structural discipline RIHAC-001's own family already applies elsewhere (B1's forgeable-seal finding, `149O.20L.7O.3W.1R.2` §9, names exactly this class of mistake to avoid) — HPAC-001 does not repeat it here.

Companion requirements read alongside it:

- **HPAC-REQ-057**: no caller may construct, serialize-and-replay, or otherwise manufacture a value without a fresh, successful §18 verification producing it.
- **HPAC-REQ-058**: the type is ephemeral and non-serializable; every consumption must re-run §18 against current registry state rather than trusting a cached result.

**Requirement, restated precisely:** the prohibition is stated in terms of *outcome* — "producible only as the return value of a successful verification" — not scoped to any one Python code path (`__init__`, a specific constructor, etc.). A value is either the literal object `verify_human_authentication` returned, or it is not "producible" under HPAC-REQ-056's meaning, regardless of how a caller allocated or populated it.

**Mapping the defect to the requirement:** `object.__new__(AuthenticatedHumanPrincipal)` plus attribute assignment produces a value satisfying every visible property of "the return value of a successful verification" (right type, right fields, right `is_real_runtime_eligible`) without the verification ever running. This is exactly the outcome HPAC-REQ-056 forbids, reached by a code path its `__init__`-only seal check does not cover.

No semantics beyond the contract text were invented: HPAC-REQ-056 does not specify *how* trusted construction must be implemented, only that non-verified construction must be impossible in effect. The repair (§5) implements that outcome without adding any new normative vocabulary.

## 5. Root cause

`AuthenticatedHumanPrincipal` declares `__slots__` but no `__new__` override. `object.__new__(cls)` allocates a bare instance of `cls` without invoking `cls.__init__` at all, so the `_seal is not _VERIFIER_CONSTRUCTOR_SEAL: raise` check — the only place trusted construction was enforced — is never reached. This is architecturally the same class of mistake as B1 (`149O.20L.7O.3W.1R.2` §4, "Forgeable trust seals"): a value the type system alone is trusted to protect, protected only by a check that lives in one specific constructor path, not by anything that survives an alternate allocation route.

## 6. Why "block `object.__new__`" is not the fix

This phase's own governing instructions warned against patching only `object.__new__`, and independent analysis confirms why that warning is correct, not merely cautious:

- **Overriding `AuthenticatedHumanPrincipal.__new__` does not stop the documented attack.** The exact reproduction in `.1R.5.1` §10.2 calls `object.__new__(AuthenticatedHumanPrincipal)` directly — a call to a different, unrelated method (`object`'s own `__new__`), not a call that goes through the subclass's method-resolution order at all. Overriding `AuthenticatedHumanPrincipal.__new__` changes what happens when someone calls `AuthenticatedHumanPrincipal(...)` or `AuthenticatedHumanPrincipal.__new__(AuthenticatedHumanPrincipal)`; it has zero effect on a caller who writes `object.__new__(AuthenticatedHumanPrincipal)` verbatim, because Python dispatches exactly the method named in the call expression, not the class's most-derived `__new__`.
- **No field-based check survives copying.** Any sentinel, boolean, or digest stored as an instance field can be read off a legitimate instance and copied onto a forged one via `object.__new__` + `setattr` for every slot (confirmed working in §8 below, before considering the fix). A field is data; data is exactly what "instance shape... as proof" (this phase's own framing) means, and the contract requires more than instance shape.
- **This generalizes across every listed reconstruction path** (direct constructor, `object.__new__`, subclass, `copy`, `deepcopy`, manual state/slot copying, reflection, pickle/reduce, copying a legitimate instance): every one of them is fundamentally "allocate an object of this class, then populate its fields" — the difference between them is only *how* the fields get populated, and no field-population mechanism is provable from inside the fields themselves.

## 7. Repair architecture — verifier-owned identity registry

The repaired design distinguishes, per this phase's §7 preferred direction:

- **`AuthenticatedHumanPrincipal` data** — the object itself: a `principal_id`, `credential_id`, `assurance_class`, etc. Reproducible by a caller via any of the paths in §6, and that is now treated as expected and harmless, because data alone was never meant to be authority.
- **Verifier-established authenticated-principal authority** — a fact that exists *about* an object, not *in* it: "this exact Python object, by identity, is one `verify_human_authentication` actually returned." This fact is recorded in a new, module-private, process-local set, `_AUTHENTIC_PRINCIPAL_REGISTRY`, and checked by a new function:

```python
def is_verifier_authenticated_principal(candidate: object) -> bool:
    return (
        isinstance(candidate, AuthenticatedHumanPrincipal)
        and candidate in _AUTHENTIC_PRINCIPAL_REGISTRY
    )
```

`verify_human_authentication`'s own return path is the *only* place anything is ever added to the registry:

```python
result = AuthenticatedHumanPrincipal(..., _seal=_VERIFIER_CONSTRUCTOR_SEAL)
_AUTHENTIC_PRINCIPAL_REGISTRY.add(result)
return result
```

### 7.1 Why this is the "verifier-owned identity registry" pattern (§7 option), not a new sentinel

`AuthenticatedHumanPrincipal.__hash__`/`__eq__` were already identity-only (`id(self)` / `self is other`) — a property `.1R.5.1` independently verified sound (§10.1). Registry membership therefore keys on Python object identity, not on any field or digest: a candidate is a member if and only if it is the literal object, at that memory location, that was added. A caller-manufactured lookalike is, by construction, a *different* Python object — even if every field is byte-identical — and can never collide with a real entry, no matter how it was allocated. This is exactly item 3's requirement ("do not add another copyable sentinel... choose a mechanism because the downstream trust check can independently establish verifier provenance") — the registry membership check does not compare any field at all; it is not a sentinel that could be copied, because there is nothing about the object itself to copy that would satisfy it.

### 7.2 Why `__init__`'s seal check is retained (defense-in-depth, not the boundary)

The `_seal is not _VERIFIER_CONSTRUCTOR_SEAL: raise` check inside `__init__` was not removed. It still gives an immediate, clear error for the ordinary mistake of calling `AuthenticatedHumanPrincipal(...)` directly, and it costs nothing to keep. But it is explicitly documented (module docstring, class docstring, and inline comments) as **not** the trust boundary — `is_verifier_authenticated_principal` is.

### 7.3 Subclassing closed at definition time

`__init_subclass__` now unconditionally raises `HPACAuthorityError`. A subclass could otherwise define its own `__init__` that never checks the seal at all — trivially recreating the "isinstance-true, never verified" shape this phase repairs, via the *ordinary* constructor call syntax rather than `object.__new__`. There is no legitimate reason to subclass a trusted-construction result type, so subclassing itself is refused rather than merely discouraged.

## 8. Adversarial reproduction — before and after

All reproduced independently against the repaired source, interactively, before writing the formal test suite (§10):

| Attack | Result before this phase | Result after this phase |
|---|---|---|
| `object.__new__(AuthenticatedHumanPrincipal)` + `setattr` every slot, including `assurance_class=PRODUCTION` | `isinstance` True; `is_real_runtime_eligible` True; **no downstream check existed to reject it** (zero consumers) | `isinstance` True (unavoidable, see §9); `is_real_runtime_eligible` True (data-shape only); `is_verifier_authenticated_principal(forged)` → **False** |
| Subclass definition (`class Evil(AuthenticatedHumanPrincipal): ...`) | Would succeed; a subclass `__init__` could skip the seal entirely | `HPACAuthorityError: AuthenticatedHumanPrincipal must not be subclassed`, raised at class-definition time |
| `copy.copy(legitimate_result)` | `TypeError` (via `__reduce__`) | Unchanged: `TypeError` |
| `copy.deepcopy(legitimate_result)` | `TypeError` | Unchanged: `TypeError` |
| Manual slot-by-slot state copy of a legitimate result (including the copied real `_verifier_seal` value) onto an `object.__new__` clone | Field-identical to the original; no check existed to reject it | `is_verifier_authenticated_principal(clone)` → **False**; `is_verifier_authenticated_principal(original)` → **True** |
| Reflection-based reconstruction (`type(legit).__new__(type(legit))` + `setattr` for every discovered slot) | Same as above | `is_verifier_authenticated_principal(reflected)` → **False** |
| `pickle.dumps(legitimate_result)` | `TypeError` (via `__reduce__`) | Unchanged: `TypeError` |
| Direct constructor call with the real module-private seal obtained via source/introspection access | Constructs successfully; nothing distinguished it from a "real" call | Constructs successfully (unchanged — the seal is defense-in-depth, not the boundary) but `is_verifier_authenticated_principal(...)` → **False**, because only `verify_human_authentication`'s own call site registers a result |
| Legitimate `verify_human_authentication(...)` call | Succeeded, produced a correct object | Unchanged, plus `is_verifier_authenticated_principal(result)` → **True** |

## 9. Historical F1 test handling

`tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py` (`.1R.5.1`'s fresh suite) is preserved **unmodified**, per this phase's explicit instruction not to rewrite history. Two of its tests continue to fail after this repair, and a third began failing for an unrelated reason during development of this repair (all three analyzed below):

- `test_object_dunder_new_bypasses_trusted_construction_seal` asserts `not isinstance(forged, AuthenticatedHumanPrincipal)`. **This postcondition is not achievable in Python.** `object.__new__(cls)` allocating a genuine instance of `cls` is definitionally what makes `isinstance` return `True` — there is no way to make an object *not* be an instance of the class `object.__new__` was asked to allocate one of, short of a metaclass that overrides `__instancecheck__` to lie about type identity, which would be a far more invasive and surprising change than this phase's scope calls for, and was not attempted. This test's premise, not the implementation, is what does not hold; it is expected to remain failing, permanently, as a documentation of the (unsatisfiable-as-worded) original ask. **This phase's actual fix target is the trust decision, not `isinstance`** — exactly the distinction §21 of this phase's instructions draws ("the key test is not: can I instantiate the class?").
- `test_forged_via_object_new_would_report_real_runtime_eligible` asserts `forged.is_real_runtime_eligible is False` for a hand-populated forged instance. `is_real_runtime_eligible` is a plain data-shape property (`self.assurance_class is HPACAuthorityClass.PRODUCTION`) that this phase deliberately did not entangle with the identity registry — see §7's data/authority distinction. Making every property on the object consult a global registry would blur exactly the line §7 asks to be drawn (data vs. verifier-established authority) and would not generalize (a forged object could still set any *other* field a future consumer might read). The correct, generalizing fix is that **no consumer may treat `is_real_runtime_eligible` (or any other field) as authoritative without first calling `is_verifier_authenticated_principal`**, which is what this phase's new suite tests directly. This test also remains failing, permanently, for the same reason as above — it is testing a data property, not the authority boundary.
- A third existing test in the same file, `test_verifier_result_attribute_copy_produces_a_distinguishable_object`, iterates the literal `AuthenticatedHumanPrincipal.__slots__` tuple and `setattr`s every entry from a legitimate result onto a fresh `object.__new__` clone. An early draft of this repair added `"__weakref__"` to `__slots__` (to let the registry use a `weakref.WeakSet` and avoid pinning verified results in memory forever). `__weakref__` has no attribute setter, so that historical test would have started raising `AttributeError` — an unexplained attributable regression. **This repair does not add `__weakref__` to `__slots__`** for exactly this reason; see §11 for the resulting design trade-off. With that reverted, this test passes unmodified, exactly as it did before this phase.

No historical test's assertions were edited, weakened, or reinterpreted. Both permanently-failing tests are exactly the two `.1R.5.1` itself reported as the evidence of F1's existence (§13 of that report), and remain the record that F1 existed — this phase's repair is proven by the *new* suite (§10), not by making the old, unsatisfiable-as-worded assertions pass.

## 10. New adversarial test suite

`tests/test_hpac_verifier_repair_3w1r2b1r1115a2.py` (independently written for this phase; imports `_Rig` from `tests/test_hpac_verifier.py` for fixture setup only, not for assertions). Covers, per this phase's §20/§21 checklist:

- pre-repair `object.__new__` bypass reproduced from fixed source (documents the allocation still succeeds; the fix is the trust check, not blocking allocation);
- direct constructor without the seal rejected (regression, existing behavior);
- direct constructor *with* the real module-private seal still not registered (proves the seal is defense-in-depth only, not the boundary);
- `object.__new__` forgery not verifier-authenticated;
- subclass construction refused at class-definition time;
- shallow copy / deepcopy / pickle of a legitimate result all raise `TypeError` (regression);
- manual slot-by-slot state copy of a legitimate result (including the real, copied `_verifier_seal`) not verifier-authenticated;
- reflection-based reconstruction not verifier-authenticated;
- a forged result with every public field identical to a legitimate one still rejected by the actual trust decision;
- a legitimate result **is** accepted through the provenance boundary;
- non-`AuthenticatedHumanPrincipal` inputs (`None`, a string, a bare `object()`) rejected by the boundary, fail-closed, no exception;
- two independent legitimate results are both individually authenticated but not equal to each other (identity-only equality preserved);
- registry lifetime behavior (a documented strong-reference trade-off, not a leak-free weak set — see §11) and that the registry is not part of the public API surface;
- deterministic NON-REAL assurance is unaffected by the repair;
- zero PB/runtime-authority/Gate-9 imports and zero production consumers, re-confirmed independently within this phase's own test file.

Run result: **20 passed** (`test_hpac_verifier_repair_3w1r2b1r1115a2.py` alone). Combined with the existing `test_hpac_verifier.py` (27 tests, unmodified, all passing) and the historical `test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py` (27 of 29 passing — the 2 not passing are exactly the pair discussed in §9, both permanently failing by design; the third test discussed in §9, which would have newly broken under an earlier `__slots__` draft, passes unmodified under the design actually adopted in §11): **74 passed / 2 permanently-and-by-design-failing, across the three files (76 total), with both non-passing tests fully accounted for and neither newly broken by this phase.**

## 11. Design trade-off: strong-reference registry, not a weak one

The registry is a plain `set()`, not a `weakref.WeakSet()`. The natural design would use a weak set so a verified result's registry entry disappears once every caller-held reference to it is dropped, rather than pinning it in memory for the life of the process. That requires adding `"__weakref__"` to `__slots__`, which (§9) breaks `.1R.5.1`'s preserved historical evidence test.

This is accepted as a **documented, deliberate trade-off**, not a silent gap:

- Every genuine verification result remains referenced by `_AUTHENTIC_PRINCIPAL_REGISTRY` for the remaining lifetime of the process, even after the caller that obtained it drops its own reference.
- This does **not** weaken HPAC-REQ-058: the result is still never persisted to disk, never serializable (`__reduce__` still raises), and never survives a process restart (the registry itself is an in-memory `set`, gone on restart — see §13).
- `hpac_verifier.py` has zero production consumers today (§14), so unbounded accumulation across a long-running process is not a live concern — nothing today calls `verify_human_authentication` in a loop outside test fixtures.
- **Carried forward, not repaired here:** a future phase that wires a real, long-running production consumer of this module must revisit this before that consumption path is trusted — either by accepting the `__weakref__` slot addition together with an update to the now-superseded historical test (which would require separate authorization, since it touches `.1R.5.1`'s evidence), or by adding an explicit bounded/LRU eviction policy to the registry.

## 12. HPAC-REQ-054 Step-4 disposition

Unchanged. F2/F3 (§3.1) remain exactly as `.1R.5.1` classified them: **NON-BLOCKING**, not repaired, not folded in — confirmed not inseparable from F1's provenance-boundary defect.

## 13. Process lifetime / restart semantics

`_AUTHENTIC_PRINCIPAL_REGISTRY` is an ordinary in-process Python `set`, module-level state with no file, database, or environment backing. On process restart it is empty; no serialized or cached verification result can register itself, because the only insertion point is a live call to `verify_human_authentication` completing inside that same process. This matches the ephemeral, ownership model HPAC-REQ-058 and `.1R.4` §29 already require: **restart ⇒ re-verification required**, unchanged by this phase.

## 14. Foundation and verifier regression results

### 14.1 Targeted HPAC-family regression sweep

Ran the full set of HPAC/human-principal/approval-presentation test files (20 files) before and after this phase's changes:

| | Passed | Failed |
|---|---|---|
| Baseline (`befd7a5a`, this phase's changes stashed) | 409 | 54 |
| Candidate (this phase's changes applied) | 429 | 54 |

The 54 failures are byte-for-byte identical between baseline and candidate (confirmed by diffing the failing test-ID lists) — all are pre-existing historical `test_blocking_reproduction_*` / contract-freeze-verification tests documenting *other*, already-recorded findings unrelated to this phase (trust-root, contract-freeze contradictions, cross-contract-freeze repair items) — none of them touch `hpac_verifier.py` or `AuthenticatedHumanPrincipal`. The +20 additional passing tests are exactly this phase's new suite. **Unexplained attributable regressions in this scope: 0.**

### 14.2 Full-suite scope — explicit limitation

The full repository suite currently collects **38,100 tests**. Running it under `pytest -n auto` (the acceptance-check command) produces xdist worker-collection-mismatch errors on **both** the phase-entry baseline and this phase's candidate, confirmed identical before any change in this phase was applied (`git stash` diff-test performed) — this is the pre-existing "xdist random-UUID parametrization instability" tooling debt named in this phase's own §30 instruction ("carried separately, not repaired unless directly blocking this phase"; it is not blocking). A full serial (non-`-n auto`) run of all 38,100 tests was not performed, for the same practical time/resource-budget reason `.1R.5.1` §15 disclosed for its (then-smaller, ~8,796-test) full suite: **this is disclosed as an explicit scope limitation, not silently treated as equivalent to a full regression-attribution exercise.**

This limitation is judged acceptable specifically because **`hpac_verifier.py` has zero production consumers anywhere in `src/pcae`** (independently re-confirmed, §14.3) — no other module imports it, so no code path outside the 20 test files enumerated in §14.1 could possibly be affected by this phase's change, by construction. The §14.1 sweep is therefore complete regression coverage for every file capable of being affected, not a sample of a larger unverified population.

### 14.3 Foundation trust regressions (§26 of this phase's instructions)

Re-confirmed via `tests/test_hpac_foundation_independent_verification_3w1r2b1r111r31.py`, `tests/test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py`, `tests/test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py` (§14.1's sweep already includes all three): principal provenance, fixture non-upgradeability, presentation provenance, proof writer provenance, lifecycle genesis, predecessor chain, fork rejection, and canonical-root containment tests all pass at the same rate as baseline. No regression.

### 14.4 Verifier regressions (§27)

`tests/test_hpac_verifier.py`'s full 27-test suite (HPAC-REQ-054 sequence, principal resolution, credential relationship, presentation, proof, lifecycle, UP/UV, mechanism neutrality, deterministic NON-REAL, invocation binding, fail-closed dependency errors, zero consumers) — **all 27 pass, unmodified, unchanged from baseline.**

## 15. Fixed-SHA regression attribution

Baseline SHA: `befd7a5a0b2e7dff037e973f9df7bdb5f5d7533f` (this phase's own entry commit — no intervening commits exist between baseline and candidate other than this phase's own uncommitted working-tree changes at analysis time). Comparison method: `git stash` / `git stash pop` around the identical pytest invocation, not commit-subject inference (§29 of this phase's instructions). This phase does **not** inherit `.1R.5`'s 370-node deselection set as authority — the §14.1 comparison instead directly diffs failing-test-ID sets between the two states of the same working tree. **Unexplained attributable functional regressions (within the §14.1/§14.2 scope explained above): 0.**

## 16. Tooling debt (carried, not repaired)

- Fast Green commit-subject baseline resolver issue (pre-existing).
- `pytest -n auto` xdist random-UUID parametrization instability, now affecting 14–15 of many workers across a 38,100-test collection (pre-existing, confirmed identical on baseline and candidate, §14.2).

Neither was touched; neither blocked this phase's own targeted verification.

## 17. Production consumer inventory / PB / runtime isolation

- `grep -rn "hpac_verifier\|AuthenticatedHumanPrincipal|verify_human_authentication" src/pcae` outside `hpac_verifier.py` itself: **zero matches** (re-confirmed after this phase's edits, both by direct grep and by this phase's own AST-based test, `test_repair_still_has_zero_production_consumers`).
- `hpac_verifier.py` imports: unchanged from `.1R.5` except the addition of `is_verifier_authenticated_principal` to `__all__`; no new import of `permission_broker`, `runtime_dispatch_permission`, `runtime_authority`, `runtime_invocation_authority_consumption`, or `runtime_invocation_approval_store` (re-confirmed by `test_repair_did_not_introduce_pb_or_runtime_authority_or_gate9_imports`).
- Files this phase modified: `src/pcae/core/hpac_verifier.py` only (production code). `runtime_authority.py`, `runtime_dispatch_permission.py`, `runtime_invocation_approval_store.py`, `runtime_invocation_authority_consumption.py`, `hpac_foundation.py`, `hpac_lifecycle.py` were not opened for write (all listed as forbidden files in this phase's own task contract; enforcement mode strict).

**PB isolation: VERIFIED. Runtime-authority isolation: VERIFIED. Gate-9 isolation: VERIFIED. Zero production consumers: VERIFIED (unchanged from `.1R.5.1`).**

## 18. B1/B7/N1/N2 status

Unchanged, still **OPEN** (contract closed / implementation open), per `149O.20L.7O.3W.1R.2`'s own recorded status. None of the four files associated with those findings (`runtime_authority.py`, `runtime_dispatch_permission.py`, `runtime_invocation_approval_store.py`) were touched by this phase. This phase's repair pattern (identity-based registry rather than a field-based seal) is architecturally related to, but intentionally not applied to, B1's own still-open forgeable-seal finding — B1's repair remains a separate, not-yet-authorized phase; this phase does not modify `runtime_authority.py` and creates no precedent that B1 is closed.

## 19. Runtime zero-effect proof

No subprocess, network, provider, credential, or hardware access exists anywhere in `hpac_verifier.py` (read in full both before and after this phase's edits — the module remains pure Python over in-memory/filesystem-backed store objects it already depended on). `pcae runtime inspect` was not re-run this phase (no runtime-adjacent code was touched); the last-known state (`.1R.5.1` §16) was `not_implemented` / `Observed` / `observe` / `unavailable`, zero registered plugins/capabilities, and nothing in this phase's scope could have changed that. **Runtime remains: Observed / observe / unavailable.**

## 20. `.3` governance incident status

Unchanged. `docs/PHASE_149O_20L_7O_3W_1R_2C_GOVERNANCE_RECORD_CORRECTION_UNAUTHORIZED_DELEGATED_PHASE_FINALIZATION.md`'s finding (**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED**) is not touched, reinterpreted, or superseded by anything in this phase. This phase's finalization, commit, and push (§22) are performed by the primary operator the human explicitly authorized for this exact phase ID in the governing prompt — not by an autonomously self-authorizing delegated worker — and only after the human's own review of this document, consistent with the correction that incident established.

## 21. F1 finding disposition

```text
F1: REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED
```

Not self-closed. `.1R.5.2.1` (§22) is the recommended, human-authorization-gated next phase to independently confirm this repair before F1 is marked CLOSED.

F2, F3, F4: unchanged classifications, dispositions per §3.1 (F2/F3 deferred unrepaired-but-unaffected; F4 partially addressed by new tests' accurate naming, not self-closed or rewritten).

## 22. Acceptance criteria — verified against this phase's own §34 checklist

| Criterion | Status |
|---|---|
| Provenance not based on object shape / constructor secrecy / copyable sentinel / serialized trusted flag | ✅ — identity-registry membership only |
| Caller direct construction cannot establish authority | ✅ — §10, §8 |
| `object.__new__` cannot establish authority | ✅ — §10, §8 |
| copy/deepcopy/reconstruction cannot establish authority | ✅ — §10, §8 |
| Legitimate verifier result accepted only through verifier-owned provenance boundary | ✅ — §10, §8 |
| Invocation binding preserved | ✅ — unrelated code path, unchanged, regression-confirmed §14.4 |
| Deterministic assurance remains NON-REAL | ✅ — §10, §14.4 |
| Production consumers: 0 | ✅ — §17 |
| PB/runtime integration: 0 | ✅ — §17 |
| B1/B7/N1/N2 repair: 0 | ✅ — §18 |
| External effects: 0 | ✅ — §19 |
| Runtime: Observed / observe / unavailable | ✅ — §19 |
| Unexplained attributable regressions: 0 | ✅ — §14, within the disclosed and justified scope |

## 23. Commits, push status, `origin/main..HEAD`

Recorded at finalization time by the governed `pcae` lifecycle/commit/push commands (see the phase-completion metadata/report artifacts this phase's task contract requires); this document is written before that governed commit/push sequence runs, per repository convention that the repair document itself is part of the committed change set. No raw `git commit`/`git push`, `--no-verify`, force-push, or history rewrite was used.

## 24. Recommended next phase (not begun, not a canonical assignment)

Per this phase's own §37 instruction:

> `149O.20L.7O.3W.1R.2B.1R.1.1R.5.2.1` — Independent Verification of AuthenticatedHumanPrincipal Trusted-Construction and Provenance Repair

Stated here as a recommendation for the human operator to authorize and formally assign, not as a canonically pre-assigned next phase. **Not begun.**

## 25. Stop condition

This phase is complete. Exactly `149O.20L.7O.3W.1R.2B.1R.1.1R.5.2` was performed. `.1R.5.2.1` was not begun. No B1/B7/N1/N2 repair was performed. No PB/runtime-authority integration was touched. No real FIDO2/UI work was performed. Execution was not enabled at any point.

```text
AUTHENTICATEDHUMANPRINCIPAL TRUSTED-CONSTRUCTION AND PROVENANCE REPAIR:
F1 REPAIRED — INDEPENDENT VERIFICATION PENDING — NOT CLOSED
F2/F3/F4:
UNCHANGED / NOT SELF-CLOSED
PRODUCTION SOURCE MODIFIED:
src/pcae/core/hpac_verifier.py (only)
PRODUCTION CONSUMERS:
0
PB/RUNTIME INTEGRATION:
0
B1/B7/N1/N2 REPAIR:
0
EXTERNAL EFFECTS:
0
RUNTIME:
Observed / observe / unavailable
UNEXPLAINED ATTRIBUTABLE REGRESSIONS:
0 (within disclosed full-suite scope limitation, §14.2)
RECOMMENDED NEXT PHASE:
149O.20L.7O.3W.1R.2B.1R.1.1R.5.2.1 (not begun; requires separate human authorization)
```
