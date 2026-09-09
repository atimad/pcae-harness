# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R Complete — Independent Verification of Privileged Production Factory Consumer-Authenticity Repair

- Phase: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R`
- Alias: **N16-5-F-5-B2-IV** (operator readability only; the full canonical CPIPC id is authoritative in task state, lifecycle, reports, completion metadata, evidence, and canonical project status)
- Status: **COMPLETE** — N16-5-F-5-B2: NOT VERIFIED / BLOCKED
- Predecessor: **N16-5-F-5-B2-IMPL** (COMPLETE — F-5-B2 REPAIR IMPLEMENTED / IV PENDING), canonical HEAD `bf8505b7`

## Verdict

- **N16-5-F-5-B2: NOT VERIFIED / BLOCKED**
- **F-5: CERTIFICATION remains BLOCKED** (new `__name__`-forgery defect must be repaired and independently reverified before any retry)
- **N-16-5: NOT CLOSED**
- **N-16-6 / N-16-7: OPEN / UNTOUCHED (N-16-7 strictly last)**

## What was independently found

Independently reconstructed the N16-5-F-5-B2-IMPL repair from primary source (not from
the predecessor's report): the repaired `_detect_caller_module` in
`src/pcae/core/hpac_protected_admin_writer.py` unconditionally discards the
`explicit`/`_caller_module` keyword and instead trusts `frame.f_globals.get("__name__")`
for the first non-contextlib caller frame. This closes the originally-disclosed
keyword-argument spoof path (independently reconfirmed: predecessor's 49-test suite
still passes 49/49) but **does not** establish the build-time/import-time provenance
`HPAC-PAWA-001` §32 requires — `f_globals["__name__"]` is an ordinary mutable dict key
any in-process caller can set via `exec()` with a hand-built globals dict, with no
`sys.modules` registration required.

**Blocking finding**, independently reproduced (not merely accepted from the delegated
worker that did initial inspection): using the exact `exec()`-with-crafted-`__name__`
technique the repository's own `tests/_caller_identity_helper.py` already relies on to
simulate a legitimate caller, an ordinary in-process caller with no special privilege
forges `__name__` to an enumerated authorized-consumer string and obtains a genuine,
fully-usable capability handle from `production_writer` (`ProductionWriterHandle`) and
`certification_writer` (`CertificationWriterHandle`). The repair relocated trust from
the disclosed `_caller_module` keyword to an equally caller-controllable implicit
global, rather than eliminating caller-controlled recognition.

No `src/pcae` source and no frozen contract were modified in this IV phase, per
governed independence discipline — the defect is recorded, not repaired.

## Evidence

- New independent adversarial suite: **18/20 passed** (`tests/test_phase_n16_5_f5b2_iv_adversarial.py`) — 2 failures are intentional evidence of the SECURITY BOUNDARY FAILURE (category A: `__name__` forgery via `exec()` globals), not test-authoring bugs. Ambient-identity spoofing (USER/LOGNAME/SUDO_USER/PATH/argv/cwd), a genuinely-imported decoy module under a different dotted path, and the exact five-role closure negative sweep all correctly denied.
- Predecessor's original suite independently reconfirmed: **49/49 passed** (`tests/test_phase_n16_5_f5b2_impl_consumer_authenticity.py`) — unaffected, because it does not exercise the `__name__`-forgery vector.
- Full `fast_green`-marked suite independently run: 9635 passed, 355 failed, 5 skipped, 9 errors (677.08s). Of the 355 failures, exactly 2 are this phase's own intentional evidence; the remaining 353 failures and all 9 errors are in test files entirely unrelated to `hpac_protected_admin_writer` (HMIC/HATP trust-enrollment/signing-authority contract-identity suites, HBDC bound-contract-digest suite, hardware-provider substrate suite, shell_gate audit suite) — pre-existing/unrelated since no `src/pcae` file was modified in this phase. **0 attributable regressions.**
- `pcae runtime inspect` independently reconfirmed: `not_implemented` / Observed / observe / unavailable / 0 plugins / 0 capabilities — unchanged from phase entry.
- Not independently exercised in this phase (disclosed, not silently omitted): the `__name__`-forgery attack against `recognized_certification_read_authority`, `mint_protected_presentation_evidence_writer`, or the clean-installed wheel boundary.
- No production, contract, dependency, or protected-host state changed. No real ceremony, no live protected-root mutation, no FIDO2/YubiKey interaction anywhere in this phase.
- Full detail, per-category adversarial matrix, and verdicts are in the canonical report:
  `docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_30R_5R_2_1R_1R_2R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_1R_N16_5_F5B2_IV.md`.

## Required successor (derived, NOT begun)

A **fresh governed repair phase** (new CPIPC-valid child of this IV phase) for the
`__name__`-forgery consumer-recognition defect, covering all four factories
(`production_writer`, `certification_writer`, `recognized_certification_read_authority`,
`mint_protected_presentation_evidence_writer`) atomically since they share the
primitive, and re-verifying the clean-installed wheel boundary. Must not be split so
any one factory remains uncertified. Only after that repair is independently verified
may a retry-equivalent of this IV, and subsequently a fresh **N16-5-FINAL-CERT** (a new
CPIPC-valid id, never a reused completed/blocked one), be authorized. Do not begin the
repair phase, N16-6, or N16-7 without their own explicit human authorization.

## Governance

- Tests run: 20 (new adversarial suite) + 49 (predecessor suite reconfirmation) + full `fast_green` suite (9635 passed / 355 failed / 5 skipped / 9 errors, 2 failures attributable to this phase's own intentional evidence)
- Pushed: pushed
- Phase commits: `62374fa5`, `1efceb8e`
