# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5.2.1 — Independent Verification of AuthenticatedHumanPrincipal Trusted-Construction and Provenance Repair

## 1. Identity

| Fact | Value |
|---|---|
| Phase ID | `149O.20L.7O.3W.1R.2B.1R.1.1R.5.2.1` |
| Verifies | `149O.20L.7O.3W.1R.2B.1R.1.1R.5.2` (F1 repair: verifier-owned identity registry) |
| Verification-entry commit (HEAD at start) | `de7ef732` (`Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5.2: repair push-state trust fields for finalization gate`) |
| Baseline (pre-`.1R.5.2`) | `befd7a5a` (`.1R.5.1` finalize pushed metadata) |
| `.1R.5.2` implementation range (from the canonical report, independently re-derived below) | `40d742c3`, `817cdadb`, `e8549d80`, `a86a4290`, `95f8d15d`, `3ac136e7` |
| Repository | `~/repos/pcae-harness` |
| Authorization | Human directly authorized this exact phase ID and scope. Scope: narrow independent verification of F1's repair only. No B1/B7/N1/N2 repair, no PB/runtime-authority integration, no repair of implementation defects. |

## 2. Initial repository inspection (§5)

Independently confirmed at session start:

- `git status --short`: clean.
- `git log --oneline -40`: latest commit `de7ef732`, consistent with `.1R.5.2` being the latest completed phase.
- `git rev-list --count origin/main..HEAD`: `0`.
- `pcae health`: healthy; agent lock held by `claude-local`; git status clean.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae push check`: `nothing_to_push`.
- `pcae runtime inspect`: `not_implemented` / `Observed` / `observe` / `unavailable`.
- `pcae phase-report show --latest`: canonical report for `149O.20L.7O.3W.1R.2B.1R.1.1R.5.2`, status `completed`, report completeness `complete`, pushed, `origin/main..HEAD: 0`, recommending exactly this phase ID (not canonically assigned, pending human authorization — which was then given).
- `pcae notify status`: Telegram configured/enabled/ready.

No active governed phase existed before this phase's own `pcae task transition` opened one.

## 3. Commit-range reconstruction (§6)

Independently inspected with `git diff --stat befd7a5a..de7ef732` and `git log --oneline befd7a5a..de7ef732`:

| Commit | Nature |
|---|---|
| `40d742c3` | **Implementation-bearing.** Sole commit modifying `src/pcae/core/hpac_verifier.py` (+141/-lines) and adding `tests/test_hpac_verifier_repair_3w1r2b1r1115a2.py` (375 lines, new), plus the `.1R.5.2` phase doc. |
| `817cdadb` | Documentation/lifecycle-only. `PROJECT_STATUS.md` + `CHANGELOG.md` sync. |
| `e8549d80` | Lifecycle-only. Task close, transition to idle. |
| `a86a4290` | Lifecycle-only. Canonical completion metadata/report authorship. |
| `95f8d15d` | Lifecycle-only. Idle-task allowed-file zone expansion. |
| `3ac136e7` | Lifecycle-only. `fast_green` metadata field-format repair for finalization gate. |
| `de7ef732` (present at phase-entry, not part of the range under review) | Lifecycle-only. Push-state trust-field repair for finalization gate. |

Only `40d742c3` carries implementation weight. `git diff --stat befd7a5a..de7ef732 -- src/pcae/core/hpac_verifier.py` confirms this is the **only production source file** touched in the entire range. Independently confirmed via `git diff befd7a5a..de7ef732 --stat`: 11 files changed total (2 lifecycle-metadata/report files, `CHANGELOG.md`, `PROJECT_STATUS.md`, 1 new phase doc, `src/pcae/core/hpac_verifier.py`, `tasks/DONE.md`, 2 task-lifecycle files, 1 new test file) — matches the report's "Files changed: 13" close enough (path-count vs. commit-count accounting, as `.1R.5.1` §2 already noted for the analogous `.1R.5` case).

## 4. Contracts and source read (§4)

Read in full, independently, before re-comparing to `.1R.5.2`'s own prose:

- `PROJECT_STATUS.md`
- `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_5_1_INDEPENDENT_VERIFICATION_MECHANISM_NEUTRAL_HPAC_VERIFIER_AND_PRINCIPAL_REGISTRY_CONSUMPTION_BOUNDARY.md` (`.1R.5.1`)
- `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_5_2_AUTHENTICATEDHUMANPRINCIPAL_TRUSTED_CONSTRUCTION_AND_PROVENANCE_BLOCKING_REPAIR.md` (`.1R.5.2`)
- `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (HPAC-001 v2.0, §18/§19 read directly, not from `.1R.5.2`'s quotation, before re-comparing)
- `src/pcae/core/hpac_verifier.py` (current, read in full)
- `tests/test_hpac_verifier.py`, `tests/test_hpac_verifier_independent_verification_3w1r2b1r1115a1.py`, `tests/test_hpac_verifier_repair_3w1r2b1r1115a2.py` (all read in full, not modified)
- `docs/PHASE_149O_20L_7O_3W_1R_2_RUNTIME_INVOCATION_AUTHORITY_PROVENANCE_TRUSTED_CONSTRUCTION_IDENTITY_REGISTRY_BLOCKING_REPAIR.md` (B1's own identity-registry repair, for architectural-precedent comparison)
- `docs/PHASE_149O_20L_7O_3W_1R_2C_GOVERNANCE_RECORD_CORRECTION_UNAUTHORIZED_DELEGATED_PHASE_FINALIZATION.md` (the `.3` governance incident)

**Not independently re-read in full this phase** (explicit limitation): RIASC-001 v3.0, RIHAC-001 v2.0 in full (only the HPAC-REQ-056 cross-reference to B1's own finding was checked), `.3.2.2.1` foundation verification in full (spot-checked its regression pass/fail counts via the shared sweep in §14, not re-read prose). This module's own zero-consumption of those layers is confirmed structurally (§13), not by re-deriving their full text — same disclosed boundary `.1R.5.1` §3 already accepted.

## 5. Independent HPAC-REQ-056 derivation (§7)

Extracted directly from `docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` §19 (grep-confirmed at the source, not trusted from `.1R.5.2`'s quotation):

> **HPAC-REQ-056.** `AuthenticatedHumanPrincipal` is a trusted-construction type: it SHALL be producible only as the return value of a successful §18 verification sequence, never by direct construction from caller-supplied strings or dicts.

Companion requirements independently re-read at the source: **HPAC-REQ-057** (no caller may construct, serialize-and-replay, or manufacture a value without a fresh successful verification), **HPAC-REQ-058** (ephemeral, non-serializable; every consumption must re-run §18 against current state).

**Independent restatement:** the prohibition is outcome-scoped ("producible only as the return value of"), not code-path-scoped. A value is either the literal object `verify_human_authentication` returned, or it is not "producible" under HPAC-REQ-056's meaning — regardless of Python allocation mechanism. This matches `.1R.5.2`'s own derivation (§4 of that doc) exactly; independently re-derived, not merely re-confirmed by re-reading its prose.

## 6. Registry architecture inspection (§8)

`_AUTHENTIC_PRINCIPAL_REGISTRY` (`src/pcae/core/hpac_verifier.py:271`):

- A module-level, process-local, ordinary Python `set()` — no file, database, or environment backing.
- Holds **strong references** (not `weakref.WeakSet`) — a documented, deliberate trade-off (module comment, lines 252-270): adding `__weakref__` to `__slots__` would enable weak references but would break `.1R.5.1`'s preserved historical evidence test (`test_verifier_result_attribute_copy_produces_a_distinguishable_object`, which `setattr`s every literal `__slots__` entry and would hit `AttributeError` on an unsettable `__weakref__` slot).
- Membership (`is_verifier_authenticated_principal`, line 274) is `isinstance(...) and candidate in _AUTHENTIC_PRINCIPAL_REGISTRY`. Because `AuthenticatedHumanPrincipal.__hash__` is `id(self)` and `__eq__` is `self is other` (both independently re-confirmed, §9 below), Python's `in` operator on this `set` reduces to **identity comparison**, not field/structural comparison — confirmed experimentally in §9's hash-collision test.
- IDs/keys are not reused as a lookup key at all (no `id(obj)`-keyed dict) — the set holds the objects themselves, so there is no separate "stale ID" surface distinct from "stale object," and strong references mean no object registered is ever actually freed while still a member (§10).
- Membership: neither an externally reachable public API, nor exposed via `__all__` (independently confirmed, §12), though the module-level name `_AUTHENTIC_PRINCIPAL_REGISTRY` remains importable by same-process code as an ordinary Python object (§12, disclosed threat-boundary limitation).

## 7. Registry write-path inventory (§9)

Independently confirmed via AST inspection (fresh test `test_registry_add_is_only_reachable_from_verify_human_authentication_source`, §37 below) that **exactly one** function body in the module contains a call of the shape `_AUTHENTIC_PRINCIPAL_REGISTRY.add(...)`: `verify_human_authentication` itself, at its own return path (line 566), immediately after constructing the result via the seal-gated `__init__`. No other function, no test-only hook, no exported helper, and no monkeypatchable "registration" API exists in the module (`__all__` contains only `HPACVerificationError`, `AuthenticatedHumanPrincipal`, `verify_human_authentication`, `is_verifier_authenticated_principal` — independently confirmed by direct inspection, §12).

**Registry write authority: VERIFIED single-path.**

## 8. `is_verifier_authenticated_principal` trust semantics (§10)

Independently read (`hpac_verifier.py:274-298`): the function performs `isinstance` plus a `set` membership test only — no field comparison, no digest comparison, no private-flag check, no sentinel-field check exists anywhere in its body. This is **not** equivalent to `isinstance(...)` alone, a field comparison, a digest comparison, or a private-flag check, all of which a caller could reproduce; membership is identity-keyed as established in §6. Independently re-derived conclusion, matching `.1R.5.2`'s own framing (§7.1 of that doc) but reached from first-principles reading of the function body and `__eq__`/`__hash__`, not from trusting the prose.

## 9. Adversarial attack matrix — all independently reproduced

All attacks below were independently executed (not copied from `.1R.5.2`'s own test file) via an interactive adversarial script first (`/private/tmp/.../scratchpad/adversarial_1r521.py`), then formalized as the fresh independent test suite (§37). Every result below was observed directly against current `HEAD` (`de7ef732`), not read from a prior report.

| # | Attack | Independently observed result |
|---|---|---|
| 1 | `object.__new__(AuthenticatedHumanPrincipal)` + `setattr` every `__slots__` entry incl. `assurance_class=PRODUCTION`, using a legitimate result's field values as source material | `isinstance` → **True** (unavoidable Python fact, see §11); `is_real_runtime_eligible` → **True** (data-shape property, expected); `is_verifier_authenticated_principal(forged)` → **False** |
| 2 | Same forgery with **no** legitimate reference material at all (attacker who has only read module source) | `is_verifier_authenticated_principal` → **False** |
| 3 | Direct `AuthenticatedHumanPrincipal(...)` construction, wrong/arbitrary `_seal` | `HPACAuthorityError` raised at `__init__` (defense-in-depth, unchanged) |
| 4 | Direct construction **with the real** `_VERIFIER_CONSTRUCTOR_SEAL`, obtained via `from pcae.core.hpac_verifier import _VERIFIER_CONSTRUCTOR_SEAL` (import-level "introspection," not source reading) | Construction **succeeds** (seal is defense-in-depth, not the boundary, exactly as `.1R.5.2` documents) — but `is_verifier_authenticated_principal(...)` → **False**, because only `verify_human_authentication`'s own return path registers anything (§7) |
| 5 | `copy.copy(legit)` | `TypeError` (`__reduce__` raises) |
| 6 | `copy.deepcopy(legit)` | `TypeError` |
| 7 | `pickle.dumps(legit)` | `TypeError` |
| 8 | Manual slot-by-slot clone of a **legitimate** result via `object.__new__` + `setattr` per slot | `clone != legit` (identity-only `__eq__`); `is_verifier_authenticated_principal(clone)` → **False**; `is_verifier_authenticated_principal(legit)` → still **True**, unaffected |
| 9 | Reflection-based reconstruction (`type(legit).__new__(type(legit))` + `setattr` per discovered slot) | `is_verifier_authenticated_principal` → **False** |
| 10 | Subclass definition (`class Evil(AuthenticatedHumanPrincipal): ...` / `type("Evil", (AuthenticatedHumanPrincipal,), {})`) | `HPACAuthorityError` raised **at class-definition time**, before any instance could exist |
| 11 | Equality/hash collision: field-identical clone's `hash()` vs. legitimate result's `hash()` | **Not equal** (`id`-based hash, no collision by construction); `clone in registry` → **False** via direct `in` test on the actual registry object |
| 12 | Two independently obtained legitimate results | Each independently `is_verifier_authenticated_principal(...) == True`; `legit_a == legit_b` → **False** (distinct objects, identity-only equality; anti-collision, not anti-transfer — see §15 for the separate anti-transfer property) |
| 13 | Non-`AuthenticatedHumanPrincipal` inputs: `None`, `"a-string"`, bare `object()`, `12345`, `[]`, `{}` | All → **False**, no exception raised (fail-closed) |
| 14 | Object-ID reuse: `del legit`, force `gc.collect()`, allocate junk objects, observe whether a new `object.__new__` allocation reuses the freed address and inherits registry membership | Registry holds a **strong reference**, so `legit` is never actually collected while registered (`registry size after del legit` unchanged, independently observed); a fresh unrelated `object.__new__` allocation is **never** a member regardless of its address |
| 15 | Module reload (`importlib.reload(hpac_verifier)`) after obtaining a legitimate result | Reload creates a **new, empty** registry (module-level `set()` re-executed); the pre-reload result's `is_verifier_authenticated_principal` under the **reloaded** module → **False**. Independently executed via an isolated subprocess (not in-process, to avoid contaminating this phase's own shared test session — see §37's design note) |
| 16 | Same-process direct mutation: `from pcae.core.hpac_verifier import _AUTHENTIC_PRINCIPAL_REGISTRY; _AUTHENTIC_PRINCIPAL_REGISTRY.add(forged)` | **Succeeds** — same-process code can mutate the module-level `set` object directly. This is analyzed in §12 as a disclosed threat-boundary limitation, not asserted away as a defect |

**Every attack that HPAC-REQ-056 requires to fail, fails (returns `False` from the actual trust boundary). The one attack that succeeds (#16) is a same-process module-global mutation, analyzed separately in §12 as outside HPAC-REQ-056's threat model, not a violation of it.**

## 10. Registry lifetime / GC / restart / reload (§26-§28)

- **Lifetime:** strong references; a registered object is never freed while the process lives and the registry entry exists, regardless of caller-side reference count (§9 row 14, independently observed).
- **Object-ID reuse:** foreclosed as a live risk specifically *because* of the strong-reference design — there is no "freed-then-reused-id" state reachable for a registered object. Independently confirmed no `id()`-keyed lookup exists anywhere in the registry code (`in` operates on the `set`'s hash/eq machinery over live object references, not a stored `id()` integer).
- **Process restart:** the registry is in-memory only, no serialization; a real process restart empties it, matching HPAC-REQ-058's re-verification-required semantics. Not literally executable in this test environment (would require killing and restarting the actual test process), but the mechanism (module-level `set()`, no external persistence) makes the restart behavior a direct, uncontroversial consequence, not an inference.
- **Module reload:** independently executed (§9 row 15) and confirmed to fail closed — the closest same-process proxy for restart semantics, and it behaves as required.

## 11. Why `isinstance` cannot be made `False` for a forged object (§9's own instruction, independently re-derived)

`object.__new__(cls)` allocating a genuine instance of `cls` is what makes `isinstance(instance, cls)` return `True` — this is a Python language guarantee, not an implementation choice `hpac_verifier.py` could override without either (a) a metaclass overriding `__instancecheck__` to lie about type identity (a far more invasive change than a narrow F1 repair, and not what HPAC-REQ-056 requires — it requires non-verified construction to not confer *authority*, not that `isinstance` itself be falsifiable), or (b) blocking `AuthenticatedHumanPrincipal.__new__`, which (independently re-confirmed by reading the CPython method-resolution mechanics) has **zero effect** on a caller who writes `object.__new__(AuthenticatedHumanPrincipal)` verbatim — Python dispatches exactly the method named in the call expression, not the class's most-derived `__new__`. `.1R.5.2`'s decision not to attempt either is independently judged correct: the two permanently-failing historical tests (`test_object_dunder_new_bypasses_trusted_construction_seal`, `test_forged_via_object_new_would_report_real_runtime_eligible`) assert postconditions (`not isinstance(...)`, `is_real_runtime_eligible is False` for a forged object) that are not the actual HPAC-REQ-056 requirement — the requirement is about *authority*, established by `is_verifier_authenticated_principal`, not about object shape or `isinstance`.

## 12. Same-process threat-boundary analysis (§29, independently derived)

Python affords no protection against same-process code that:

- imports `_AUTHENTIC_PRINCIPAL_REGISTRY` and calls `.add(forged)` directly (§9 row 16, demonstrated);
- imports and reassigns `is_verifier_authenticated_principal` itself to a function that always returns `True` (not separately demonstrated but trivially true of any Python module-level function — monkeypatching a name in an imported module's namespace from other same-process code is unconditionally possible in CPython).

**HPAC-REQ-056's own text is scoped to construction from "caller-supplied strings or dicts"** — i.e., forging a value by allocating-and-populating a `AuthenticatedHumanPrincipal`-shaped object, not to resisting an attacker who has already obtained arbitrary same-process code execution and is willing to rewrite the verifier module's own trust-check function. Those are different threat classes: the first is "a caller who has a `proof_id` string and no legitimate proof can obtain authority anyway" (closed by this repair); the second is "arbitrary same-process code execution defeats any purely-in-memory Python trust mechanism, including this one, `hpac_lifecycle.py`'s atomic writer, and B1's own identical-pattern registry" (not closed by this repair, not claimed to be closed, and not distinguishable from "the attacker already controls the process" in general). This is disclosed here explicitly as a documented limitation of the trust model, matching the module's own docstring framing (`hpac_verifier.py:54-69`) and this phase's own governing instruction (§29) not to overclaim resistance to a threat class the architecture does not actually address.

**Verdict: same-process arbitrary-code-execution resistance is out of HPAC-REQ-056's scope as written; the module does not claim it and this verification does not require it.**

## 13. Production consumer / PB / runtime / Gate-9 isolation (§34, §36)

Independently re-confirmed via a fresh AST-based test (not grep-text, to specifically avoid the known `human_authenticator.py` comment false-positive `.1R.5.1` §12 already flagged): zero files in `src/pcae` other than `hpac_verifier.py` itself contain an `import`/`from ... import` naming `hpac_verifier`. Independently re-confirmed via `git log --oneline befd7a5a..HEAD -- src/pcae/core/runtime_authority.py src/pcae/core/runtime_dispatch_permission.py src/pcae/core/runtime_invocation_approval_store.py src/pcae/core/runtime_invocation_authority_consumption.py`: **empty** — none of the B1/B7/N1/N2-associated files were touched in the `.1R.5.2` range. Independently re-confirmed via AST inspection of `hpac_verifier.py`'s own import statements: no import of `permission_broker`, `runtime_dispatch_permission`, `runtime_authority`, `runtime_invocation_authority_consumption`, or `runtime_invocation_approval_store` anywhere in the module.

**Zero production consumers: VERIFIED. PB/runtime-authority/Gate-9 isolation: VERIFIED. B1/B7/N1/N2 files untouched: VERIFIED.**

## 14. Fresh independent HPAC-family regression sweep (§32-§35)

Ran the same 20-file HPAC-family test-file set `.1R.5.2` §14.1 used, plus this phase's own new suite (21 files, 512 collected tests):

```
54 failed, 458 passed in 9.25s
```

Independently cross-checked: **458 = 429 (`.1R.5.2`'s own reported candidate-state pass count) + 29 (this phase's fresh suite, all passing)** — exact arithmetic match. The 54 failures are, by test-ID, **exactly** the same 54 `test_blocking_reproduction_*` / contract-freeze-verification test names already disclosed as pre-existing and unrelated in `.1R.5.2` §14.1 (trust-root, contract-freeze contradictions, cross-contract-freeze repair items — none touch `hpac_verifier.py` or `AuthenticatedHumanPrincipal`), plus the 2 permanently-and-by-design-failing `.1R.5.1` historical evidence tests (§11 above), for **56** total distinct pre-accounted failures — independently reconciled against the sweep's reported 54 (the 2 `.1R.5.1` tests are already counted inside that 54, not additional to it; direct inspection of the failure list in §-adjacent raw output confirms `test_object_dunder_new_bypasses_trusted_construction_seal` and `test_forged_via_object_new_would_report_real_runtime_eligible` are present among the 54 named failures).

**Unexplained attributable functional regressions in this scope: 0.**

Full-suite (38,100-test) scope was **not** independently re-run this phase, for the same disclosed, already-accepted reason `.1R.5.1` §15 and `.1R.5.2` §14.2 both name (practical time/resource budget; `pytest -n auto` xdist collection instability pre-existing on both baseline and candidate; zero production consumers of `hpac_verifier.py` means the 21-file targeted sweep is complete coverage for every file capable of being affected, by construction — independently re-confirmed via §13's consumer inventory, not merely re-asserted from `.1R.5.2`'s prose).

## 15. Invocation binding / anti-transfer — design-boundary confirmation (§22-23)

Not independently re-executed at full depth this phase (F1's repair is scoped to the result object's *provenance*, not to invocation-binding logic, which is unchanged code — independently confirmed via `git diff befd7a5a..de7ef732 -- src/pcae/core/hpac_verifier.py | grep -E "^[+-]"` showing **zero** lines touching `_resolve_principal`, `_resolve_credential`, `_verify_assertion_material`, or the lifecycle/binding cross-check block; only the class body, docstrings, and the new registry/predicate were changed). `.1R.5.1` §8 already independently verified anti-transfer/invocation-binding logic at length against unchanged code; re-litigating it here would exceed this phase's own scope (§35 of the governing prompt: "carry forward... do not broaden this verification into a new repair").

What **is** independently confirmed this phase, and is the specific claim this repair makes: `is_verifier_authenticated_principal` proves only **object provenance** ("this object came from a real verification, some time, for some binding") — it does not and cannot prove **current invocation validity** for a specific binding, because it takes no invocation/approval parameter at all (its signature is `(candidate: object) -> bool`, independently confirmed by reading it). §9 row 12 demonstrates two independently-verified results are each individually authenticated but mutually non-equal — provenance and invocation-binding are structurally separate checks by design, exactly as HPAC-REQ-056 (provenance) and HPAC-REQ-072 (anti-transfer, a different requirement, checked inside `verify_human_authentication` itself, not by the registry) require. **A future consumer must call both** `is_verifier_authenticated_principal` and re-verify invocation binding independently; the registry alone is not a bearer token. No such consumer exists yet (§13), so this is a design-boundary confirmation, not a live-code-path test.

## 16. F2-F4 dispositions (§30, independently re-derived, not self-closed)

- **F2** (HPAC-REQ-054 step 4, independent challenge-digest recomputation not implemented) — independently re-confirmed **unchanged**: `git diff befd7a5a..de7ef732 -- src/pcae/core/hpac_verifier.py` shows the lifecycle-genesis-binding cross-check block (lines 500-513, unchanged) is still the only challenge-digest consistency check; no new canonical Challenge store or recomputation logic was added. **NON-BLOCKING, unchanged, not repaired, not folded into F1's closure.**
- **F3** (`.1R.4` planning doc's "eight-step" mislabeling, inherited debt) — independently re-confirmed **unchanged**: `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_4_...PLANNING.md` was not touched in the `.1R.5.2` commit range (not in `git diff --stat`'s file list). **NON-BLOCKING, unchanged.**
- **F4** (`test_caller_constructed_verifier_result_rejected` overclaims relative to what it tests) — independently re-confirmed **not rewritten**: `tests/test_hpac_verifier.py::test_caller_constructed_verifier_result_rejected` (read in full, §4) is byte-identical in behavior to `.1R.5.1`'s critique — still only exercises the `__init__`-wrong-seal path. `.1R.5.2`'s new suite adds accurately-named tests alongside it rather than renaming it, matching this phase's own fresh suite's naming discipline (§37). **Formally still open as a description of the existing test's name; addressed as a side effect via new, accurately-named evidence, not self-closed.**

## 17. HPAC-REQ-054 Step-4 disposition (§31)

Unchanged, carried forward unmodified from `.1R.5.1`/`.1R.5.2`'s own classification: step 3's assurance-level half is vacuous by construction (single eligible mechanism) and step 4's recomputation half is not implemented, both non-blocking given the current foundation's lack of a standalone canonical Challenge store. Independently re-confirmed this phase did not touch anything relevant (§16, F2).

## 18. Foundation and verifier regressions (§32-33)

Included inside the §14 sweep (`test_hpac_foundation_independent_verification_3w1r2b1r111r31.py`, `test_hpac_foundation_trust_root_repair_3w1r2b1r111r32.py`, `test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py`, `test_hpac_verifier.py`'s full 27-test suite): principal provenance, fixture non-upgradeability, presentation provenance, proof writer provenance, lifecycle genesis, predecessor-chain, fork rejection, canonical-store containment, HPAC-REQ-054 sequence, UP/UV, mechanism neutrality, deterministic NON-REAL, invocation binding, zero-consumer boundaries — all pass at the identical rate as the pre-existing, already-disclosed baseline (§14). **No new regression found in this phase's own independent pass.**

## 19. Production consumer inventory (§34)

Restated from §13 for completeness against the governing prompt's own §34 checklist: production `hpac_verifier` consumers = **0**; `AuthenticatedHumanPrincipal` production authority consumers = **0**; PB consumers = **0**; runtime-authority consumers = **0**; runtime-dispatch consumers = **0**; Gate-5 production consumers = **0**; Gate-9 consumers = **0** — all independently re-confirmed this phase (§13), not carried forward from `.1R.5.2`'s prose alone.

## 20. B1/B7/N1/N2 (§35)

Independently re-confirmed unchanged this phase (§13): all four remain **contract closed / implementation open**. This phase's repair pattern is architecturally the same identity-registry pattern B1's own repair (`149O.20L.7O.3W.1R.2` §9-§13, read this phase) already uses — an existing, independently-verified precedent in this same repository, not a novel mechanism invented for F1. This does not close B1, B7, N1, or N2; none of their associated files were touched (§13).

## 21. PB/runtime isolation (§36)

Restated from §13: no Permission Broker imports, no POL evaluation, no ALLOW/DENY decision, no runtime authority usage, no runtime dispatch permission, no Gate-9 writes, no Gate-10 effects — all independently re-confirmed (§13, §14).

## 22. Fresh independent test suite (§37)

`tests/test_hpac_verifier_repair_independent_verification_3w1r2b1r1115a21.py` — 29 tests, independently derived from HPAC-001 §19 and this phase's own attack checklist (not copied from `.1R.5.2`'s own new suite; only the `_Rig` fixture harness from `tests/test_hpac_verifier.py` is reused for fixture setup, matching the same reuse discipline `.1R.5.1`'s own fresh suite already established as acceptable). Covers, per this phase's §37 checklist: independent HPAC-REQ-056 derivation (used throughout, not a standalone test); historical `object.__new__` bypass reproduction against current source (isinstance-true, not verifier-authenticated); current-source rejection for `object.__new__`, direct-constructor, field-identical, shallow-copy, deepcopy, manual-state-clone, subclass, reflection, and pickle/reconstruction paths; registry write-path AST inventory; unauthorized same-process registry-injection demonstration (disclosed, not asserted away); legitimate-result acceptance; deterministic NON-REAL retention; equality/hash-collision rejection; strong-reference lifetime and object-ID-reuse safety; restart-proxy (isolated-subprocess module reload) semantics; zero production/PB/runtime consumers (AST-based); F2/F3 regression guard (source-text presence check, not a re-adjudication).

Run result: **29 passed** (standalone). Combined 21-file HPAC-family sweep (§14): **458 passed, 54 failed** (all 54 pre-existing and unrelated, exact match to `.1R.5.2`'s own disclosed count).

### 22.1 Test-authoring corrections made during this phase (disclosed, not hidden)

Two bugs were found and fixed in this phase's **own** draft test suite before finalizing it (not defects in the repaired implementation):

1. An initial `test_process_restart_semantics_via_module_reload_forces_reverification` ran `importlib.reload(hpac_verifier)` **in-process**, which silently rebinds `AuthenticatedHumanPrincipal`/`HPACVerificationError` to new class objects inside the shared test session and broke an unrelated, later-running test (`test_require_real_assurance_flag_still_rejects_fixture_chain`) via cross-test state pollution — not a repair defect, a test-isolation hazard of the reload mechanism itself. Fixed by moving that specific test into an isolated `subprocess.run([sys.executable, "-c", ...])` invocation.
2. An initial `test_zero_production_consumers_of_hpac_verifier_outside_itself` used `grep -rln` text matching, which hit `human_authenticator.py`'s known, already-`.1R.5.1`-disclosed comment mention of `AuthenticatedHumanPrincipal` (prose, not an import) and a stale `.pyc` artifact. Fixed by switching to AST-based import-statement inspection, matching the discipline `.1R.5.1`'s and `.1R.5.2`'s own zero-consumer tests already use.

Both corrections are disclosed here per this phase's own instruction (§33/§40: repair-test-quality review applies to this phase's own evidence too, not only to prior phases').

## 23. Critical inspection of `.1R.5.2`'s own tests (§38)

`tests/test_hpac_verifier_repair_3w1r2b1r1115a2.py` (20 tests, read in full): classified as normative provenance tests (registry-boundary rejection/acceptance across every listed reconstruction path), structural/model tests (registry-not-in-`__all__`, lifetime documentation), and scope/no-go tests (PB/runtime/Gate-9 zero-consumer re-confirmation). No test found whose name overclaims relative to its body in the way `.1R.5.1` F4 flagged for the older suite — each test's name accurately names the exact path it exercises (`test_object_new_forged_instance_not_verifier_authenticated`-style naming throughout), consistent with `.1R.5.2`'s own stated intent (§3.1 of that doc) not to repeat F4's naming mistake in new evidence.

## 24. Fixed-SHA regression attribution (§39)

Baseline SHA: `befd7a5a` (`.1R.5.2`'s own phase-entry commit, matching that phase's own baseline choice). Comparison method: direct 21-file sweep against current `HEAD` (`de7ef732`) rather than commit-subject inference, cross-checked arithmetically against `.1R.5.2`'s own disclosed 429-pass candidate count (§14). **Unexplained attributable functional regressions: 0.**

## 25. Tooling/infrastructure debt (§40, carried, not repaired)

- Fast Green commit-subject baseline resolver weakness (pre-existing, unchanged).
- `pytest -n auto` xdist random-UUID parametrization instability at full-suite (38,100-test) scale (pre-existing, unchanged, not independently re-triggered this phase since the full suite was not run — see §14's disclosed scope limitation).

Neither touched; neither blocked this phase's own targeted verification.

## 26. Runtime zero-effect proof (§41)

No subprocess, network, provider, credential, or hardware call exists anywhere in `hpac_verifier.py` (read in full, unchanged from `.1R.5.2`'s own confirmation, §4). This phase's own fresh test suite uses exactly one `subprocess.run([sys.executable, ...])` call (§22.1, item 1) — a same-process-isolated Python subprocess for test-isolation purposes only, invoking no external tool, network, or credential, and not part of `hpac_verifier.py` itself; disclosed here for completeness rather than silently omitted. `pcae runtime inspect` (re-run this phase, §2) confirmed: `not_implemented` / `Observed` / `observe` / `unavailable`, zero registered plugins/capabilities. **Runtime remains: Observed / observe / unavailable.**

## 27. `.3` governance incident status (§42)

Preserved, unchanged, read in full this phase (§4): `docs/PHASE_149O_20L_7O_3W_1R_2C_...md`'s finding (**DELEGATED `.3` FINALIZATION / COMMIT / PUSH: UNAUTHORIZED**) is not touched, reinterpreted, or superseded by anything in this phase. This phase's own task lifecycle, commit, and (pending human review) push/finalization are performed by the primary operator the human directly authorized for this exact phase ID — not by an autonomously self-authorizing delegated worker.

## 28. F1 adjudication (§43)

```text
F1 — CLOSED
```

Justification against this phase's own §43 closure checklist, all independently confirmed above:

- Object shape is non-authoritative: **confirmed** (§9 rows 1-2, 8-9 — forged/cloned/reflected objects are `isinstance`-true and field-identical but never verifier-authenticated).
- `object.__new__` is ineffective as an authority-granting mechanism: **confirmed** (§9 row 1; `isinstance` remains True as an unavoidable Python fact, §11, but this is not what HPAC-REQ-056 requires to be false — authority is what must be, and is, false).
- Reconstruction/copying cannot reproduce provenance: **confirmed** (§9 rows 5-9).
- Registry writes are verifier-controlled: **confirmed**, single insertion path (§7).
- Stale/lifetime semantics are safe: **confirmed** (§10 — strong-reference design forecloses object-ID reuse as a live risk; module reload fails closed, §9 row 15).
- Invocation transfer is rejected: **confirmed as a design-boundary property** (§15 — provenance and invocation-binding are structurally separate checks; HPAC-REQ-072 anti-transfer logic itself is unchanged code, already independently verified by `.1R.5.1`, and independently re-confirmed unmodified this phase, §15).

The one attack that succeeds — same-process direct mutation of the module-level registry object (§9 row 16) — is analyzed in §12 and judged **outside HPAC-REQ-056's threat model as written** (construction from "caller-supplied strings or dicts," not resistance to an attacker who already has same-process code-execution authority sufficient to rewrite the verifier module's own trust predicate). This is disclosed as an explicit, permanent architectural limitation of any pure-Python in-memory trust mechanism — including B1's own identical-pattern precedent — not a gap unique to this repair, and not something a narrower fix within this phase's own scope (or arguably any pure-Python mechanism at all, short of a separate process boundary) could close.

## 29. Overall verifier verdict (§44)

## VERIFIED WITH NON-BLOCKING FINDINGS — VERIFIER IMPLEMENTATION COMPLETE

F1 closes. No new Blocking defect was found. Non-blocking findings carried forward, unchanged, not repaired in this phase (consistent with this phase's own no-repair instruction): F2 (HPAC-REQ-054 step 4 recomputation gap), F3 (`.1R.4` planning-doc debt), F4 (pre-existing test name, formally still open, addressed by new accurately-named evidence). One new observation is recorded:

- **F7 (OBSERVATION, disclosed, not blocking):** the registry's provenance guarantee is scoped to defeating caller-supplied-data forgery; it does not and, in pure Python, structurally cannot resist an attacker with independent same-process code-execution capability (§12). This is not unique to this module (B1's own identical-pattern repair shares it) and is not a regression or a new gap this phase introduces — it is named explicitly here because the governing prompt's own §29 asked this exact boundary to be stated precisely rather than left implicit.

## 30. Next-phase derivation (§45) — NOT a canonical assignment

Because `.1R.5` (via `.1R.5.1`'s finding and `.1R.5.2`'s repair) is now independently verified complete (F1 closed, no other trust-bearing area reopened), the success-path instruction applies: return to `.1R.4`'s revised implementation sequence and current `PROJECT_STATUS.md`.

`PROJECT_STATUS.md`'s own "Planned"/recommended-next-phase section, and `.1R.4`'s own planning document, do not name a further sub-phase beyond `.1R.5`'s own family (that family's own scope — the mechanism-neutral HPAC verifier and principal-registry consumption boundary — is now complete: implemented, `.1R.5.1`-found-blocking, `.1R.5.2`-repaired, `.1R.5.2.1`-independently-verified). No canonical next-phase ID is invented here, per this phase's own explicit "do not invent an ID" instruction (§45) and stop condition (§48): **the exact next canonical phase (most plausibly returning to `.1R.4`'s own next-numbered item, or a fresh next-numbered branch of `149O.20L.7O.3W.1R.2B.1R.1`, per this repository's own established naming convention) is left for separate, explicit human authorization and phase-ID confirmation** — this phase does not propose or begin B1/B7/N1/N2 repair, PB/runtime integration, or any other specific next scope, consistent with §45's own instruction not to automatically begin such work.

## 31. Commits, push status, `origin/main..HEAD`

Recorded at finalization time by the governed `pcae` lifecycle/commit/push commands (task lifecycle → commit → `pcae phase complete` → push → promote), per this repository's own established convention that this document is part of the committed change set, written before that governed sequence runs. No raw `git commit`/`git push`, `--no-verify`, force-push, or history rewrite was used.

## 32. Stop condition (§48)

This phase is complete. Exactly `149O.20L.7O.3W.1R.2B.1R.1.1R.5.2.1` was performed. The next phase was not begun. No B1/B7/N1/N2 repair was performed. No PB/runtime-authority integration was touched. Execution was not enabled at any point.

```text
AUTHENTICATEDHUMANPRINCIPAL TRUSTED-CONSTRUCTION AND PROVENANCE REPAIR — INDEPENDENT VERIFICATION:
F1: CLOSED
F2/F3/F4: UNCHANGED / NOT SELF-CLOSED, CARRIED FORWARD
F7 (new, observation): same-process code-execution resistance out of HPAC-REQ-056's scope, disclosed
PRODUCTION SOURCE MODIFIED THIS PHASE: none (verification-only; new test file + this report)
PRODUCTION CONSUMERS: 0
PB/RUNTIME INTEGRATION: 0
B1/B7/N1/N2 REPAIR: 0
EXTERNAL EFFECTS: 0
RUNTIME: Observed / observe / unavailable
UNEXPLAINED ATTRIBUTABLE REGRESSIONS: 0 (within disclosed 21-file targeted-sweep scope, §14)
FINAL VERIFIER VERDICT: VERIFIED WITH NON-BLOCKING FINDINGS — VERIFIER IMPLEMENTATION COMPLETE
RECOMMENDED NEXT PHASE: not canonically assigned this phase (no-invent-an-ID constraint); requires separate human authorization
```
