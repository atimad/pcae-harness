# Phase Report — N16-5-F-5-B2R-IV

**Canonical Phase ID:**
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1`

**Display alias:** N16-5-F-5-B2R-IV

**Predecessor canonical Phase ID:**
`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R`
(alias N16-5-F-5-B2R-IMPL)

**CPIPC validation result:** Valid direct `.1` successor of
N16-5-F-5-B2R-IMPL. Same series (149) and branch (`O`), strict successor
ordering (`pcae.core.phase_id.compare(candidate, predecessor) == "greater"`),
unique against full git history (`git log --all` — zero matches for the
candidate token before this phase's own commits), no conflicting active
phase (agent lock `claude-local`, no other active governed phase).
Independently re-derived via `pcae.core.phase_id` (`parse` / `format` /
`same_series` / `same_branch` / `compare`), not precomputed from the
operator prompt's displayed alias.

**Predecessor HEAD/commit identity:** `94e00a0405b82c0a0b2a9844ca489b08e9ce5215`
(= `origin/main` at phase entry, clean working tree, no divergence).

## Title

Fresh Independent Verification of Privileged Production Factory
Consumer-Authenticity Repair

## Independence discipline

The predecessor implementation phase's report was treated only as a
hypothesis inventory. All claims below were independently re-derived from
primary source (`src/pcae/core/hpac_protected_admin_writer.py`, read in
full) and fresh, independently authored test execution — not by rerunning
the predecessor's own 23-test suite.

## Files changed

- `tests/test_phase_n16_5_f5b2r_iv_independent_verification.py` (new, 3
  tests) — this phase's independent adversarial suite.
- `docs/PHASE_N16_5_F5B2R_IV.md` (this report, new).
- `PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json`,
  `.pcae/phase-completion-report.md` — governance artifacts.
- Task lifecycle: closed the stale idle placeholder task, opened and will
  close the N16-5-F-5-B2R-IV task.

**Production source changes: none.** No file under `src/pcae/` was
modified. This is a verification-only phase; the disclosed defect below is
documented, not repaired, per the phase's own scope boundary (Section 2 /
Section 35 of the authorizing prompt).

**Contract byte-identity result:** `HPAC-PAWA-001` and all other
docs/schemas contract files confirmed byte-unchanged since the predecessor
implementation phase's own commit (`git diff --stat -- docs/ schemas/
pyproject.toml` between the predecessor's HEAD and this phase's entry HEAD
is empty for contract files; no contract file appears in this phase's own
diff either).

## Reconstructed trust mechanism

Independently read in full from `src/pcae/core/hpac_protected_admin_writer.py`
(lines 490–716 for the mechanism itself; entry points at lines 1143
`production_writer`, 1820 `mint_protected_presentation_evidence_writer`,
2112 `certification_writer`, 2546 `recognized_certification_read_authority`
— all four confirmed, by direct source read, to call `_detect_caller_module`
then funnel through `_run_recognition_sequence`; no alternate/legacy
recognition path exists for any of them).

`_detect_caller_module` walks `inspect.stack()`, finds the first frame not
belonging to this module's own `<locals>`/`contextlib` wrapper, and reads
its `f_globals["__name__"]`. If that name is one of the four factories'
enumerated production-consumer names (`AUTHORIZED_FACTORY_CONSUMERS`,
`CERTIFICATION_FACTORY_CONSUMERS`, `READ_AUTHORITY_CONSUMERS` (=
`CERTIFICATION_FACTORY_CONSUMERS`), `PROTECTED_PRESENTATION_LAUNCHER_CONSUMERS`),
it is **not** trusted on the `__name__` key alone; it is passed to
`_verified_production_caller_name(candidate, frame)`, which requires:

1. **First-verified-use fast path** (if `candidate` already has a pin):
   `frame.f_globals is pinned_module.__dict__` (object identity) AND
   `id(frame.f_code) in pinned_codes` (frozenset of code-object ids
   snapshotted at first pin).
2. **First-observation path** (no pin yet): `sys.modules[candidate]` must
   exist, `frame.f_globals is module.__dict__` (object identity, defeats
   `sys.modules` poisoning by an object whose `__dict__` the caller does
   not actually share), `_module_has_verified_provenance` must be true
   (the module's `__spec__.loader` must be a real
   `importlib.machinery.SourceFileLoader` whose `__spec__.origin` resolves
   to the exact on-disk path a genuine import of that dotted name into the
   installed `pcae` package layout requires — derived from the
   already-imported `pcae` package's own `__file__`, never from
   `sys.path`/`cwd`/caller input), and `id(frame.f_code)` must already be
   one of the module's own currently-defined function/method code objects
   (collected via `_collect_module_code_objects`). On first success, the
   module and the frozenset of its current code-object ids are pinned into
   module-level dicts `_PINNED_TRUSTED_MODULES` / `_PINNED_CODE_OBJECTS`
   (kept alive via `_CODE_OBJECT_KEEPALIVE` to prevent CPython `id()`
   reuse after garbage collection).

A forged claim returns `None` from `_verified_production_caller_name`,
converted to the sentinel `"<unverified-caller>"` by
`_detect_caller_module` — never re-attributed to an outer frame, never a
substitute name.

### Predicate table

| Predicate | Source symbol | Input source | Caller-controllable? | Stateful? | Process-local? | Fail-open/closed? | Independently tested? |
|---|---|---|---|---|---|---|---|
| Candidate name matches enumerated consumer set | `_detect_caller_module` | `frame.f_globals["__name__"]` | Yes (ordinary dict key) | No | No | closed (falls through to non-privileged path otherwise) | Yes |
| Pin fast-path: `f_globals is pinned_module.__dict__` | `_verified_production_caller_name` | live frame | No, if pin was legitimately seeded | Yes | Yes | closed | Yes |
| Pin fast-path: `id(f_code) in pinned_codes` | `_verified_production_caller_name` | live frame | No, if pin was legitimately seeded | Yes | Yes | closed | Yes |
| First-observation: module import provenance (`SourceFileLoader` + origin path match) | `_module_has_verified_provenance` | `sys.modules[name].__spec__` | No (real import machinery only) | No | No | closed | Yes |
| First-observation: `f_globals is module.__dict__` | `_verified_production_caller_name` | live frame | No (genuine identity required) | No | No | closed | Yes |
| First-observation: `id(f_code)` in module's own collected code objects | `_verified_production_caller_name` / `_collect_module_code_objects` | `vars(module)` at first-use time | No, if module genuinely unmodified pre-first-use | No (snapshotted once) | No | closed | Yes |
| **`_PINNED_CODE_OBJECTS` / `_PINNED_TRUSTED_MODULES` / `_CODE_OBJECT_KEEPALIVE` dict identity/contents** | module globals | ordinary Python attribute access | **Yes — no encapsulation, only underscore convention** | Yes | Yes | **fails open once overwritten** | **Yes — BLOCKING FINDING** |

The final row is the load-bearing defect: every other predicate correctly
resists forgery, but the pin *state itself* is an ordinary, writable
module-level object with no access control distinguishing "the recognition
function's own writes" from "any other in-process code's writes."

## Four-factory atomicity result

**PASS.** All four factories (`production_writer`, `certification_writer`,
`recognized_certification_read_authority`,
`mint_protected_presentation_evidence_writer`) call `_detect_caller_module`
then `_run_recognition_sequence`; no factory has a fallback, alternate
overload, compatibility path, test seam, or direct-writer-constructor
bypass (confirmed by reading each factory's full body and grepping for
alternate mint paths — see "Generic writer / second trust root result"
below). The BLOCKING finding is not scoped to one factory: it is proven
end-to-end against `production_writer` and the identical primitive is
shared verbatim by the other three (confirmed by source read, not
independently re-proven against all four given the shared code path and
time budget — see "Unresolved / not independently re-run" below).

## Legitimate-consumer result

**PASS** (independently re-confirmed): `test_forged_name_via_exec_globals_still_denied`
and `test_sys_modules_poisoning_still_denied` both exercise real,
successful `production_writer` calls elsewhere in this phase's fixture
setup path (`provision_protected_root`, itself a legitimate in-module
call), and the predecessor's own 23-test suite (independently spot-read,
not blindly trusted) demonstrates the same for all four factories via
genuine imports. Not fully independently re-run end-to-end for all four
factories in this phase given the decisive blocking finding already
established — see "Unresolved" below.

## Ordinary-caller denial result

**PASS.** An ordinary caller with no forged metadata and no state
tampering cannot claim a privileged name (confirmed by direct source read:
`_detect_caller_module` returns the caller's real `__name__` verbatim when
it is not in the enumerated consumer sets, which is rejected downstream by
`_run_recognition_sequence`'s `unauthorized_factory_consumer` check).

## Caller-controlled metadata (forged `__name__`) denial result

**PASS (denied), independently re-tested.**
`test_forged_name_via_exec_globals_still_denied` independently reconstructs
the predecessor's exact `exec()`-crafted-`__name__`-via-hand-built-globals
technique against `production_writer` and confirms
`PawaError(code="unauthorized_factory_consumer")` is raised. This is the
exact historical regression class from N16-5-F-5-B2-IV; it remains denied.

## `sys.modules` poisoning result

**PASS (denied), independently re-tested.**
`test_sys_modules_poisoning_still_denied` independently constructs a
`types.ModuleType` decoy inserted into `sys.modules` under the authorized
name `pcae.core.hpac_rhamp_enrollment` (no genuine `SourceFileLoader`
origin), executes a call from inside that decoy's own `__dict__`, and
confirms denial with `unauthorized_factory_consumer`.

## Decoy/lookalike, loader/spec/origin, package-layout/path result

**Not independently re-tested with fresh adversarial code beyond the two
tests above** given time budget and the decisive blocking finding already
established (see "Unresolved" below); independently read the
`_module_has_verified_provenance` implementation and confirm by inspection
that it correctly requires both a real `SourceFileLoader` instance and an
exact resolved-path match against the only location a genuine import of
that dotted name could occupy in the installed package layout — no
path-resemblance-alone or loader-kind-alone acceptance was found in the
source.

## Code-object identity result

Independently read: the pin binds to `id(frame.f_code)` against a snapshot
of `vars(module)` taken once, at first-verified-use, one level into any
class the module defines (`_collect_module_code_objects`). A code object
`exec()` freshly compiles, or one an attacker only adds to the module's
namespace *after* the snapshot, is correctly excluded from the trusted set
by construction. Not independently tested against wrapper/decorator call
shapes or recompiled-equivalent-source scenarios — see "Unresolved" below.

## First-verified-use pin result

Independently read: the pin is populated only inside the "first
observation" branch of `_verified_production_caller_name`, and only after
all three first-observation checks (module exists, `f_globals` identity,
verified provenance, and code-object membership) succeed — a failed
verification attempt returns `None` before reaching the pin-write
statements, so a failed unauthorized attempt cannot seed or poison the
pin (confirmed by source read of lines 638–662; no test path in this
function writes to `_PINNED_CODE_OBJECTS` / `_PINNED_TRUSTED_MODULES`
except the three lines immediately following a successful verification).
This part of the design holds.

## Mutable state / monkey-patch resistance result — **BLOCKING FINDING**

**FAIL.** `_PINNED_CODE_OBJECTS`, `_PINNED_TRUSTED_MODULES`, and
`_CODE_OBJECT_KEEPALIVE` are ordinary module-level `dict`/`dict`/`dict`
objects with no property, descriptor, closure-only scoping, or any other
mechanism preventing direct external mutation. The leading underscore is
the *only* nominal protection, and Python does not enforce it.

`test_BLOCKING_ordinary_code_can_overwrite_pin_state_to_impersonate_authorized_consumer`
(new, independently authored, in
`tests/test_phase_n16_5_f5b2r_iv_independent_verification.py`) proves a
full end-to-end bypass:

1. An ordinary test module (on no consumer allowlist) imports
   `pcae.core.hpac_protected_admin_writer as w` and the real target module
   `pcae.core.hpac_rhamp_enrollment as real_mod` — both ordinary,
   unprivileged imports.
2. It compiles one small code object of its own choosing (`attacker_code`).
3. It directly writes:
   `w._PINNED_CODE_OBJECTS["pcae.core.hpac_rhamp_enrollment"] = frozenset([id(attacker_code)])`
   and the matching `_PINNED_TRUSTED_MODULES` / `_CODE_OBJECT_KEEPALIVE`
   entries. This is a plain dict assignment; nothing rejects it.
4. It executes `attacker_code` via `exec(attacker_code, real_mod.__dict__)`
   — `real_mod.__dict__` is itself an ordinary, caller-obtainable object
   (reachable as `sys.modules["pcae.core.hpac_rhamp_enrollment"].__dict__`
   by any code that has imported that module), so the resulting frame's
   `f_globals is real_mod.__dict__` is genuinely true, and
   `id(frame.f_code)` genuinely matches the forged pin entry from step 3.
5. Inside that `exec()`, the attacker's code calls
   `w.production_writer(PawaOperation.ENROLL_PRINCIPAL, ...)` and receives
   back a genuine, live `ProductionWriterHandle` — real production
   authority, minted through the fully repaired recognition sequence,
   obtained with **no forged `__name__`, no `sys.modules` poisoning, and
   no import-provenance spoof.**

Verified by running the test: `1 passed` (the test's own assertion is that
the bypass succeeds, i.e. it documents current vulnerable behavior; a
future repair should invert it into a regression lock once the gap is
closed, per the test's own docstring). Full command output:

```
tests/test_phase_n16_5_f5b2r_iv_independent_verification.py::test_forged_name_via_exec_globals_still_denied PASSED
tests/test_phase_n16_5_f5b2r_iv_independent_verification.py::test_sys_modules_poisoning_still_denied PASSED
tests/test_phase_n16_5_f5b2r_iv_independent_verification.py::test_BLOCKING_ordinary_code_can_overwrite_pin_state_to_impersonate_authorized_consumer PASSED
3 passed in 0.10s
```

This directly falsifies the primary IV question's negative-authenticity
half (an ordinary caller must not obtain privileged authority "by
manipulating caller-controlled metadata, Python import state, module
naming, load order, object identity, package layout resemblance, **or
process-local mutable state**") and IV pass criterion #17. The repair
closed the two disclosed forgery classes (metadata forgery,
`sys.modules` poisoning) but did not close the pin state itself against
direct manipulation — the trust anchor is real for what it checks, but the
checked state is not itself protected.

## Five-role closure, generic writer, second trust root results

**Not independently re-tested in this phase** given time budget and the
decisive blocking finding already established (see "Unresolved" below).
Independently spot-read `CERTIFICATION_FACTORY_CONSUMERS = frozenset({"pcae.core.hpac_certification_coordinator"})`
and the exact-set (no wildcard/prefix) equality check at line 2164
(`certification_writer`) and line 2592 (`recognized_certification_read_authority`);
consistent with the predecessor's claimed exact five-role closure.
`__all__` reviewed (lines 82–110): no new public factory symbol was added
by the predecessor's repair.

## Clean-installed wheel boundary, sdist, broader regression adjudication

**Not independently re-run in this phase.** Given the decisive blocking
finding already established from primary-source reconstruction and direct
adversarial testing (a valid early-stop condition under Section 35 of the
authorizing prompt — "critical product defect found"), this phase did not
proceed to rebuild/reinstall the wheel or re-run the full `fast_green`
suite. The predecessor's reported 91-passed/1-failed wheel-boundary result
and its 0-attributable-regression fast_green comparison are **not
independently adjudicated by this phase** and should not be relied upon as
independently confirmed; a successor phase (the repair phase, or a
follow-up IV after the repair) should re-run both.

## Unresolved / not independently re-run in this phase

Given the decisive, disqualifying blocking finding, this phase did not
exhaustively complete every adversarial sub-test enumerated in the
authorizing prompt's Sections 9–16 (e.g. alternate dotted paths, alias
imports, symlinked install paths, wrapper/decorator call-shape variance,
copied-source-under-real-name for all four factories individually,
ambient-environment sweep, full five-role negative sweep, exhaustive
generic-writer symbolic grep, clean-installed-wheel rebuild, sdist
boundary, full `fast_green` rerun). These remain legitimately open and
should be completed by whichever phase re-verifies the eventual repair —
they are independent of, and do not change, the BLOCKED verdict below,
since a single confirmed critical bypass is already sufficient to fail the
IV.

## Deterministic vs. real assurance wall

Preserved. This phase's tests exercise deterministic Python-level
mechanism verification only; no test constitutes or claims human
presence, human verification, informed approval, real FIDO2 authentication,
or a PRODUCTION `AuthenticatedHumanPrincipal`. Consumer authenticity
remains understood as one infrastructure authority boundary, not human
authentication.

## Live production state / real ceremony

**No live protected-host writes.** No `PrincipalRecord`, `CredentialRecord`,
RHAMP counter-state, PPA/protected-root, or generation-1 deployment state
was mutated. All test fixtures use disposable `tmp_path`-provisioned
protected roots. **No real certification ceremony was performed.** No
FIDO2/YubiKey hardware interaction (`getAssertion`, `makeCredential`, PIN,
touch) occurred. No PRODUCTION principal was issued. No final Gate5
assurance ceremony occurred.

## Runtime / effect wall

Unchanged: Observed / observe / unavailable; 0 plugins; 0 capabilities;
first governed runtime external effect remains ABSENT / UNREACHABLE.
`DispatchEnvelope` reachability, adapter dispatch, and Gate10 effect
reachability were not touched. No N16-6 or N16-7 work was performed.

## Governance checks

- `pcae_health`: healthy (confirmed at session bootstrap).
- `pcae_check`: passed (confirmed at session bootstrap).
- `pcae_push_check`: to be confirmed at finalization.
- `pcae_doctor_task_memory`: not run this phase (consistent with
  predecessor's own non-blocking treatment; no lifecycle-tooling change in
  this phase).
- `notification`: to be dispatched by `pcae phase complete` per current
  policy.
- `origin/main..HEAD`: 0 at phase entry; to be re-confirmed as 0 after
  push.

## Final verdicts

**N16-5-F-5-B2R-IV: COMPLETE — NOT VERIFIED / BLOCKED.**
**F-5-B2: BLOCKED** (the process-local mutable-state gap disclosed above).
**F-5: CERTIFICATION BLOCKED.**
**N-16-5: NOT CLOSED.**
**N-16-6: OPEN / UNTOUCHED.**
**N-16-7: OPEN / UNTOUCHED — strictly last.**

**Recommended next: a fresh governed repair phase** closing the
process-local mutable-state gap (real encapsulation of the pin state, not
merely underscore-prefixed module attributes) — **NOT BEGUN.** This IV
does not authorize that repair; it requires its own fresh human
authorization.

Real ceremony: **NOT PERFORMED.**
