# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1 (alias N16-5-F-5-B2R2-IMPL)

**Title:** Privileged Production Factory Consumer-Authenticity Repair —
Mutable-State Elimination / Trust-Boundary Repair

**Predecessor (canonical):**
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1`
(alias N16-5-F-5-B2R-IV), predecessor HEAD `dff27851f44ee3bf0cf1900bc9b15467a0474c44`.

**CPIPC validation:** candidate = predecessor + exactly one direct `.1`
segment. Independently re-derived and confirmed via `pcae.core.phase_id`:
`parse`/`format` round-trip clean; `same_series` True (149); `same_branch`
True (O); `compare(predecessor, candidate)` == `less` (candidate is a
strict successor); unique against `git log --all` (0 prior matches); no
active conflicting governed phase at entry. Alias `N16-5-F-5-B2R2-IMPL`
display-only, no discrepancy.

**Status: N16-5-F-5-B2R2-IMPL COMPLETE — BLOCKED.**

Reason: **CURRENT SAME-PROCESS PYTHON TRUST BOUNDARY CANNOT SATISFY THE
FROZEN CONSUMER-AUTHENTICITY REQUIREMENT WITHOUT STRONGER SEPARATION.**

---

## 1. Contract baseline discrepancy (disclosed, non-blocking)

The authorizing prompt's Section 4 stated an expected baseline of
`HPAC-PAWA-001 v1.3`. Independent inspection of
`docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
found the contract already at **v1.4** (evolved by the separately-tracked
phase `N16-5-F5B1-READAUTH`, commit `1877a412`, with its own widen-not-weaken
reconciliation at `13e7263b`). `git merge-base --is-ancestor 13e7263b
dff27851` confirms `13e7263b` (the v1.4 freeze) is already an ancestor of
the immediate predecessor commit — i.e. v1.4 was legitimately frozen via its
own governed phase *before* N16-5-F-5-B2R-IV ran, not an unauthorized
change introduced by or during this phase. This is a stale expectation in
the authorizing prompt, not a contract-integrity violation. No contract
was modified by this phase; `git diff --stat` over this phase's own
changes touches no file under `docs/contracts/`.

## 2. Reconstructed trust model (from primary source, `src/pcae/core/hpac_protected_admin_writer.py`)

All four privileged factories (`production_writer` L1143,
`mint_protected_presentation_evidence_writer` L1820, `certification_writer`
L2112, `recognized_certification_read_authority` L2546) call
`_detect_caller_module` (L665) → `_verified_production_caller_name` (L622),
confirming the shared-primitive premise (Section 9) directly from source,
not from the predecessor's report.

| Trust predicate | Source symbol | Established | Caller-controlled? | Mutable? | Persistent? | Process-local? | Required for positive recognition? | Removable? |
|---|---|---|---|---|---|---|---|---|
| Frame belongs to real module's `__dict__` | `frame.f_globals is module.__dict__` (L642/L648) | per-call | No (module identity itself) | N/A (identity check) | N/A | N/A | Yes | No — irreducible |
| Module has genuine import provenance | `_module_has_verified_provenance` (L598) | per-call, first pin | No | N/A | N/A | N/A | Yes | No — irreducible |
| Code object belongs to module's own pre-existing code | `_PINNED_CODE_OBJECTS` (L522) | first verified use | **Yes** (ordinary dict write) | **Yes** | Yes (process lifetime) | Yes | Yes | This phase's assigned target |
| Pinned module reference | `_PINNED_TRUSTED_MODULES` (L521) | first verified use | **Yes** | **Yes** | Yes | Yes | Yes | This phase's assigned target |
| Code-object GC keepalive | `_CODE_OBJECT_KEEPALIVE` (L523) | first verified use | **Yes** | **Yes** | Yes | Yes | Indirectly (id-reuse prevention) | This phase's assigned target |

The first three rows are irreducible: any recognition scheme that verifies
"this frame is genuinely executing inside the real, import-verified
trusted module" must, by construction, compare against `module.__dict__`,
which is inherently the exact same object ordinary code obtains via
`sys.modules[name].__dict__`. The last three rows are the disclosed
defect's literal target.

## 3. Same-process threat-model adjudication (Section 8, required)

**Question:** Can the frozen HPAC-PAWA-001 consumer-authenticity property
be enforced against arbitrary ordinary same-process Python code, given
Python's ability to inspect/rebind/import/mutate objects?

**Answer: NO**, independently proved by three escalating, executed PoCs
(`tests/test_phase_n16_5_f5b2r2_impl.py`, 3/3 passed):

1. **`test_regression_direct_pin_mutation_bypass_unchanged`** — reconfirms
   the predecessor's disclosed direct-dict-write bypass against the actual
   `_PINNED_CODE_OBJECTS`/`_PINNED_TRUSTED_MODULES` state still mints a
   genuine `ProductionWriterHandle`. Unchanged because no production
   source was modified (see §4).

2. **`test_gc_based_bypass_defeats_closure_encapsulation`** — the general
   case. A trust dict held purely as a local variable inside a closure,
   **never** assigned to any module-level name, **never** returned, is
   still located and mutated by ordinary code using only
   `import gc; gc.get_objects()` — with **zero reference chain** to the
   closure. `gc.get_objects()` enumerates every GC-tracked object
   currently alive in the process, independent of what references it.
   This is a standard-library capability, not ctypes, not a C extension,
   not a debugger. It defeats every technique Section 3 lists as
   insufficient (class attribute, name-mangling, `MappingProxyType`
   wrapping a dict held elsewhere, `WeakValueDictionary`, closure) for the
   identical underlying reason: none of them remove the object from the
   GC's live-object graph, and `gc.get_objects()` does not require any
   reference chain from the caller's own held names.

3. **`test_fresh_scan_no_cache_redesign_is_also_unsafe`** — proves Section
   7's preferred alternative ("eliminate the cache, re-derive fresh from
   `vars(module)` at every call") is *also* unsafe, not merely today's
   caching implementation. An ordinary caller defines a new function
   directly inside the trusted module's own namespace via `exec()` against
   `module.__dict__` (an ordinary operation on an already-imported module
   object — no forged `__name__`, no `sys.modules` poisoning) and calls it
   normally; a fresh-every-call scan of `vars(module)` genuinely,
   correctly-by-its-own-logic includes the attacker's own code object,
   because by the time of the scan it truly is present in the module's
   namespace. The module namespace being scanned — not merely the cache —
   is itself the untrusted, ordinary, caller-writable surface.

**Root cause, generalized beyond the three named pin dicts:** any
recognition scheme for "this frame belongs to the real, trusted module"
must ultimately compare against that module's own `__dict__`, which is
*necessarily* the same ordinary, mutable, caller-reachable object every
legitimate importer also reaches through `sys.modules[name].__dict__`.
Layering a cache on top (today's design) adds a second mutable,
caller-reachable surface without removing the first. Removing the cache
(Section 7's preference) does not remove the first surface either — it
just removes the second, leaving the module namespace itself exploitable.
No pure-Python encapsulation technique hides a live object from
`gc.get_objects()`/`gc.get_referrers()`, which requires no reference
chain and no privileged access beyond the standard library.

**Conclusion:** the required security property (Section 6) is **not
satisfiable within the current same-process Python interpreter boundary**,
for any of the four privileged factories, under any design shape
considered (cache-based, cache-free/fresh-scan, or conventional
encapsulation of either). This is a same-interpreter, standard-library
capability limitation, not a coding defect fixable by better hiding of
state.

## 4. No production source modified

Per Section 27/34's early-stop discipline: since a genuine repair honoring
the frozen contract's consumer-authenticity property does not exist within
the stated threat model, no cosmetic re-encapsulation was implemented.
`src/pcae/core/hpac_protected_admin_writer.py` is **byte-unchanged** by
this phase (`git diff` over this phase's changes touches no file under
`src/`). Building a repair that only obscures rather than removes the
defect would produce false assurance — explicitly prohibited by Section 3
and Section 27.

## 5. Four-factory atomicity

Confirmed by source read (§2 above): all four factories share the
identical `_detect_caller_module` → `_verified_production_caller_name`
primitive verbatim, so the unsatisfiability finding applies uniformly to
`production_writer`, `certification_writer`,
`recognized_certification_read_authority`, and
`mint_protected_presentation_evidence_writer` — none is repaired, none is
newly regressed (no source changed for any of them).

## 6. Focused test tally

`tests/test_phase_n16_5_f5b2r2_impl.py`: 3 new tests, 3 passed, 0 failed.
No existing test file modified.

## 7. Broader regression tally / baseline comparison

`python3 -m pytest -m "fast_green" -n auto`:
- With this phase's changes: 9667 passed, 352 failed, 5 skipped, 9 errors.
- Baseline (this phase's new test file stashed, identical commit
  otherwise): 9665 passed, 351 failed, 5 skipped, 9 errors.
- `FAILED` test-ID set comparison (`comm` diff) between the two runs:
  **0 failures unique to this phase's changes.** One failure
  (`test_fido2_library_installed_does_not_flip_substrate_operational`)
  appeared only in the baseline run and not the with-changes run — a
  pre-existing flake unrelated to `hpac_protected_admin_writer` (FIDO2
  substrate-operational detection), not attributable to this phase either
  direction.
- **Attributable regressions: 0.** The ~351-352 pre-existing failures are
  the repository's known population of fixed-commit-hash self-checks
  (`*_byte_unchanged_since_*`, `*_untouched_by_this_phase`,
  `*_no_src_contracts_or_scripts_changes_since_election`, etc.) across
  dozens of historical phases — each compares against a commit that is no
  longer HEAD as new phases land, a documented pre-existing repository
  characteristic (not introduced or worsened by this phase; verified by
  identical failure-ID sets with and without this phase's one new test
  file).

Clean-installed-wheel rebuild (Section 24) and sdist verification were
**not independently rerun this phase**: no `src/` file changed, so wheel
contents are unaffected by this phase's changes; both remain
`not_independently_rerun_this_phase`, consistent with the predecessor
phase's own precedent for a decisive early-stop finding.

## 8. Live state / ceremony / runtime — all NOT PERFORMED / unchanged

- Live protected-host writes: **NONE.**
- PrincipalRecord / CredentialRecord / RHAMP counter / PPA / protected-root
  mutation: **NONE.**
- Real certification ceremony: **NOT PERFORMED.**
- FIDO2 hardware interaction (getAssertion/makeCredential/PIN/touch):
  **NOT PERFORMED.**
- Runtime: **Observed / observe / unavailable** (unchanged).
- Plugins / capabilities: **0 / 0** (unchanged).
- First governed runtime external effect: **ABSENT / UNREACHABLE**
  (unchanged).

## 9. Predicate-by-predicate result summary

| Check | Result |
|---|---|
| Predecessor CPIPC / canonical state | Validated |
| Frozen contracts unchanged | Confirmed (HPAC-PAWA-001 v1.4 byte-unchanged; §1 discrepancy is prompt staleness, not a violation) |
| Writable trust-pin defect eliminated | **NOT eliminated** — proved unsatisfiable, not repaired |
| Ordinary in-process mutation denied | **FAIL** (by design proof, §3) |
| Pseudo-encapsulation accepted as boundary | **Not accepted** — explicitly rejected per Section 3/27 |
| Four factories atomically covered | Yes (shared primitive, unmodified) |
| Legitimate consumers still work | Yes — unchanged, no source touched |
| Forged caller metadata denied | Yes — unchanged (reconfirmed by predecessor's own suite, not rerun this phase) |
| sys.modules poisoning denied | Yes — unchanged |
| Decoy/lookalike denied | Yes — unchanged |
| Import/reload order creates no authority | Unchanged from predecessor |
| Exact five-role closure preserved | Unchanged — no source touched |
| No generic writer introduced | Confirmed — no source touched |
| No second trust root introduced | Confirmed — no source touched |
| No consumer self-enrollment introduced | Confirmed — no source touched |
| Deterministic vs. real assurance | Preserved — no ceremony performed |
| Clean-installed wheel boundary | Not independently rerun this phase (no src change) |
| Focused test tally | 3/3 passed |
| Broader raw regression tally | 9667 passed / 352 failed / 5 skipped / 9 errors |
| Attributable regressions | 0 |
| origin/main..HEAD | 0 (confirmed post-push) |

## 10. Final status

- **N16-5-F-5-B2R2-IMPL: COMPLETE — BLOCKED.**
- **F-5-B2: BLOCKED.**
- **F-5: CERTIFICATION BLOCKED.**
- **N-16-5: NOT CLOSED.**
- **N-16-6: OPEN / UNTOUCHED.**
- **N-16-7: OPEN / UNTOUCHED — STRICTLY LAST.**

## 11. Recommended successor

A fresh governed **architecture phase** defining a stronger trust boundary
than pure same-process Python — e.g. an OS-process boundary (a separate,
minimally-privileged helper process holding the authority state, invoked
only through an IPC surface that does not expose the state itself to the
importing interpreter), a C-extension-backed opaque capability not
represented as a Python heap object reachable via `gc`, or an equivalent
mechanism outside the interpreter's own object graph. This phase does
**not** design or implement that architecture. **NOT BEGUN.**

`N16-5-F-5-B2R2-IV` (fresh independent verification of a repair) is **not
applicable** — no repair was implemented to verify. The correct next
governed step is the architecture phase above, not an IV of this phase's
(non-)implementation.

## 12. Governance checks

- `pcae session bootstrap`: healthy, check passed, push clean.
- `pcae check` / `pcae health`: see finalization output below.
- Historical governance integrity preserved: `N16-5-F-5-B2` and
  `N16-5-F-5-B2R-IV` verdicts (`NOT VERIFIED / BLOCKED`) are unmodified;
  `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved
  verbatim, unchanged, un-reinterpreted.
- No delegated worker performed finalization/commit/push for this phase;
  all investigation, PoC authorship, and finalization were performed
  directly.

## Explicit confirmation

**N16-5-F-5-B2R2-IV was NOT begun. N16-5-FINAL-CERT was NOT begun. No
protected human approval, real ceremony, FIDO2 hardware interaction, live
counter mutation, or production principal issuance occurred. N16-6 and
N16-7 were not begun.**
