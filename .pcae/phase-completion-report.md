# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R Complete — Privileged Production Factory Consumer-Authenticity Repair -- Caller-Controlled Module-Identity Elimination

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R`
- Alias: **N16-5-F-5-B2R-IMPL** (operator readability only; the full canonical CPIPC id is authoritative in task state, lifecycle, reports, completion metadata, evidence, and canonical project status)
- Status: **COMPLETE** — F-5-B2 CONSUMER-AUTHENTICITY REPAIR IMPLEMENTED / IV PENDING
- Predecessor: **N16-5-F-5-B2-IV** (COMPLETE — N16-5-F-5-B2 NOT VERIFIED / BLOCKED), canonical HEAD `cee7de03`

## Verdict

- **F-5-B2: CONSUMER-AUTHENTICITY REPAIR IMPLEMENTED / IV PENDING**
- **F-5: DEPLOYMENT VERIFIED — CERTIFICATION BLOCKED PENDING FRESH F-5-B2 IV**
- **N-16-5: NOT CLOSED**
- **N-16-6 / N-16-7: OPEN / UNTOUCHED (N-16-7 strictly last)**

## What was repaired

Repaired the shared `_detect_caller_module` primitive in
`src/pcae/core/hpac_protected_admin_writer.py` that N16-5-F-5-B2-IV proved forgeable
(trusting `frame.f_globals["__name__"]`, settable via `exec()` against a hand-built
globals dict). The repair (`_verified_production_caller_name`) now requires, for any of
the four factories' enumerated production-consumer names: (1) genuine import provenance
— a real `importlib.machinery.SourceFileLoader` origin resolving to the exact on-disk
path the installed `pcae` package layout requires, derived only from the already-imported
`pcae` package's own `__file__`, never caller-supplied; and (2) calling-frame code-object
identity against a process-local, first-verified-use pin of the module's own pre-existing
code objects. Check (1) alone was found insufficient during design (a real module's
`__dict__` is itself an ordinary caller-referenceable object, so
`exec(forged_code, real_module.__dict__)` would pass it) — check (2) closes that gap. A
forged claim is rejected outright via a non-matching `"<unverified-caller>"` sentinel,
never re-attributed to an outer frame. Applies atomically to all four factories
(`production_writer`, `certification_writer`, `recognized_certification_read_authority`,
`mint_protected_presentation_evidence_writer`).

## Evidence

- New focused suite: **23/23 passed** (`tests/test_phase_n16_5_f5b2r_impl_repair.py`) — legitimate consumers succeed for all four factories via genuine imports; the predecessor's exact `exec()`-crafted-`__name__` forgery denied for all four; `sys.modules` poisoning denied; decoy/lookalike/copied-source-under-real-name denied; ambient env/argv/cwd identity irrelevant; five-role closure intact.
- Combined N16-5 lineage bundle (8 files) independently rerun: **311/311 passed**.
- The predecessor IV's two finding-documentation tests (`test_A1`/`test_A2`) inverted into regression locks confirming the forgery is now denied; four other test files' positive-path tests updated to use genuine real-import call origination instead of the now-invalidated `_caller_identity_helper.py` scratch-module proxy.
- Full `fast_green`-marked suite (`-n auto`) independently run: candidate **9645 passed / 368 failed / 5 skipped / 9 errors**, vs. a git-stash-confirmed baseline of **9637 passed / 353 failed** on the unmodified predecessor HEAD `cee7de03`. **0 attributable regressions** — all 18 new failures are either the repository's well-documented fixed-commit git diff/git status self-check pattern (17 instances) or one confirmed-non-reproducing `pytest-xdist` ordering flake.
- Clean-installed-wheel boundary independently verified: built `pcae_harness-0.4.3` wheel via `python -m build`, installed into an isolated venv with no editable checkout on `sys.path`, focused adversarial suite run against that install: **91 passed / 1 failed** (test-methodology artifact, not a product defect).
- `pcae runtime inspect` independently reconfirmed: Observed / observe / unavailable / 0 plugins / 0 capabilities — unchanged from phase entry.
- No production dependency, contract, or protected-host state changed beyond the single repaired source file. No real ceremony, no live protected-root mutation, no FIDO2/YubiKey interaction anywhere in this phase.
- Full detail, per-factory adversarial matrix, and verdicts are in the canonical report:
  `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_N16_5_F5B2R_IMPL.md`.

## Required successor (derived, NOT begun)

A **fresh independent verification phase** (new CPIPC-valid child of this phase),
display alias **N16-5-F-5-B2R-IV**, that independently reconstructs this trust mechanism
from primary source and repeats the relevant adversarial boundary tests from a clean
install, with explicit attention to the disclosed trust-on-first-use residual risk. Only
after that IV passes may a fresh **N16-5-FINAL-CERT** be considered. Do not begin that
IV, N16-6, or N16-7 without their own explicit human authorization.

## Governance

- Tests run: 23 (new focused suite) + 311 (lineage bundle) + full `fast_green` suite (9645 passed / 368 failed / 5 skipped / 9 errors, 0 attributable) + clean-installed-wheel focused suite (91 passed / 1 failed, test-methodology artifact)
- Pushed: pushed
- Phase commits: `1496e343`, `8adc617f`, `df8685e3`
