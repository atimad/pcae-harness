# Phase 149O.19.5F — HMIC Activation-Readiness Integration

**Status:** IMPLEMENTED — HMIC VALID NOW SUPPLIES EXACTLY ONE HMRC
READINESS FACT — FRESH LOCK-HELD ACTIVATION RECHECK PRESERVED — NO REAL
ACTIVATION PERFORMED

**Phase type:** BOUNDED PRODUCTION INTEGRATION (Wave F, `docs/
PHASE_149O_19_4_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_
IMPLEMENTATION_PLAN.md` §9/§10), gated by that plan's own **Stop
Condition W-1** — independently confirmed closed at the contract +
implementation-identity boundary by Phase 149O.19.5E.4.

---

## 1. Baseline

- Latest completed phase entering this one: **149O.19.5E.4** (HMIC v1.1
  24-File Production Identity Alignment Independent Verification), exit
  commit `dd649271`, pushed, `origin/main..HEAD` = 0 at entry, repo
  clean.
- `pcae health`: healthy; required files present; git clean.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: warnings — pre-existing `tasks/done/`
  entries (149O.1H.3–149O.3) missing from `tasks/DONE.md`, unrelated to
  HMIC-001, not remediated here (outside this phase's allowed-file
  scope).
- `pcae push check`: clean, `nothing_to_push`.
- `pcae runtime inspect`: Runtime state Observed; execution capability
  unavailable; Permission Broker status `execution_unavailable`.
- `pcae notify status`: Telegram configured/enabled/ready.
- `pcae phase-report show --latest` / `pcae phase-report reconcile
  --phase-id 149O.19.5E.4`: 149O.19.5E.4 confirmed `completed`/`complete`,
  recommending exactly 149O.19.5F (this phase, not 149O.19.5G in
  advance).

## 2. Primary Sources Read Directly

- `docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`
  §19 (HMRC-REQ-054–056) — the exact six-item activation-prerequisite
  conjunction.
- `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
  §17–19, §50 (HMIC-REQ-050–063, -103–113).
- `docs/PHASE_149O_19_4_HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_IMPLEMENTATION_PLAN.md`
  §9 (`CUT` wiring rows), §10 (Self-Reference Disposition & HMIC v1.1
  Amendment Sequencing — Stop Condition W-1 and its precedent, §10.1).
- `docs/PHASE_149O_19_5D_HMIC_ACTIVE_CERTIFICATION_VALIDATION_ENGINE.md`,
  `docs/PHASE_149O_19_5E_4_HMIC_V1_1_24_FILE_PRODUCTION_IDENTITY_ALIGNMENT_INDEPENDENT_VERIFICATION.md`.
- `src/pcae/core/hatp_mandatory_cutover.py` — read in full before
  editing; the exact hardcoded-`False` location and six-check
  conjunction reconstructed directly from source (§3 below), not
  inferred from the governing prompt.
- `src/pcae/core/hatp_mandatory_certification.py` — read in full; the
  production validator entrypoint, `HMICValidationResult`,
  `CertificationStatus`, and `certification_status_satisfies_readiness`
  reconstructed directly from source (§5 below).

## 3. Readiness Model Reconstruction (Before Editing)

`_assess_hatp_mandatory_activation_readiness_at_root` appended **seven**
`HATPMandatoryActivationReadinessCheck` entries pre-Wave-F. HMRC-REQ-054
itself names exactly **six** activation-prerequisite terms; the seventh
(`repository_deployment_identity_valid`) is an identity/storage
prerequisite this module owns independently of HMRC-REQ-054's own
enumeration (confirmed against the contract's literal text, §19, which
lists exactly: Class-B deployment valid, HATP substrate operational,
HSCE signing implementation available, mandatory-consumption
implementation independently verified, production dependency provenance
valid, Protected Activation Authority mechanism available):

1. `class_b_protected_storage_available` — HMRC-REQ-054 item 1.
2. `repository_deployment_identity_valid` — module-owned, not one of the six.
3. `hatp_substrate_operational` — HMRC-REQ-054 item 2.
4. `hsce_signing_implementation_available` — HMRC-REQ-054 item 3.
5. `mandatory_consumption_implementation_independently_verified` — HMRC-REQ-054 item 4 (**the literal `False` constant this phase replaces**).
6. `production_dependency_provenance_valid` — HMRC-REQ-054 item 5.
7. `protected_activation_authority_mechanism_available` — HMRC-REQ-054 item 6.

The hardcoded literal was located at what is now (pre-edit)
`hatp_mandatory_cutover.py` inside the fifth `checks.append(...)` call,
as a bare `False` positional argument with no derivation.

## 4. Activation Flow Reconstruction (Before Editing)

`activate_hatp_mandatory(root, *, activated_by)` → resolves
`repository_instance_id`/`protected_root` internally →
`_activate_hatp_mandatory_at_root(...)` → `_write_cutover_transition(...,
readiness_check=lambda: _assess_hatp_mandatory_activation_readiness_at_root(...))`.
The transition-write function acquires an exclusive `flock` on
`.cutover-transition.lock`, re-resolves the current mode, validates the
transition, and — only for `target_mode == HATP_MANDATORY` — invokes
`readiness_check()` **exactly once, while the lock is still held**,
immediately before the Cutover Record write. This linearization point is
unchanged by this phase; Wave F only widens what feeds the readiness
callable's own fifth check.

## 5. HMIC Validator API Reconstruction (Before Editing)

`hatp_mandatory_certification.py` already exposed, unused by any
production caller:

- `validate_active_hatp_mandatory_independent_verification_certification(repository_root: Path) -> HMICValidationResult`
  — the sole production validation entrypoint (HMIC-REQ-109). Resolves
  `HATPTrustStore.production().root` internally; accepts no
  caller-suppliable root, identity, digest, or status override
  (HMIC-REQ-045/110/111/112, independently confirmed by the 149O.19.5D
  suite's own `TestNoCallerSuppliableAuthorityInput`). Read-only —
  acquires no write lock, calls no writer function. Re-runs the full
  12-step HMIC-REQ-103 algorithm fresh on every call; no cache.
- `HMICValidationResult(status: CertificationStatus, reason: str)` —
  `status` is the sole authority-bearing field; `reason` is non-blocking
  diagnostic text only.
- `CertificationStatus` — 9-member closed enum: `MISSING`, `MALFORMED`,
  `WRONG_REPOSITORY`, `WRONG_DEPLOYMENT`, `IMPLEMENTATION_MISMATCH`,
  `CONTRACT_MISMATCH`, `REVOKED`, `ACCESS_ERROR`, `VALID`.
- `certification_status_satisfies_readiness(status) -> bool` — returns
  `True` iff `status is CertificationStatus.VALID` (exact identity, no
  truthiness/string comparison); its own docstring already stated this
  function "is never wired into `hatp_mandatory_cutover.py` by this
  phase (Wave F only, gated by Stop Condition W-1)" — confirming this is
  exactly the intended Wave F wiring point.

No new validator was invented; both symbols above were imported
unchanged.

## 6. Frozen-Scope Disposition (Governing-Prompt Items 53–54)

Independently re-derived via `hmic._frozen_canonical_paths()` (fresh
call, not cached from a prior phase's claim): the current 24-file HMIC
v1.1 frozen set already contains
`src/pcae/core/hatp_mandatory_cutover.py` as one of its entries — HMIC
plan §10.1's own documented precedent ("the code enforcing a readiness
gate must itself be inside the scope that certification protects").
This phase's one production change therefore legitimately alters the
current 24-file implementation identity. This is operationally safe
because no real certification artifact exists anywhere on this host
(§11 below) — no pre-existing certification is invalidated by this
change; any *future* certification will simply certify the post-F
bytes. `hatp_mandatory_certification.py` and
`scripts/hatp_certification_admin.py` remain byte-unchanged (§9).

## 7. Implementation

**File changed:** `src/pcae/core/hatp_mandatory_cutover.py` only.

1. Added a narrow, non-wildcard import:
   `from pcae.core.hatp_mandatory_certification import
   (certification_status_satisfies_readiness,
   validate_active_hatp_mandatory_independent_verification_certification)`.
2. Threaded a new, optional, keyword-only `repository_root: Optional[Path]
   = None` parameter through
   `_assess_hatp_mandatory_activation_readiness_at_root`,
   `_activate_hatp_mandatory_at_root`, and the public wrappers
   `assess_hatp_mandatory_activation_readiness`/`activate_hatp_mandatory`
   (which now pass `root.path`). Defaulting to `None` preserves
   byte-identical call-compatibility for every pre-existing test seam
   call that omits it — those calls now observe an honestly-unmet HMIC
   check (fail-closed on a missing repository root) rather than a
   `TypeError`.
3. Replaced the fifth check's construction:

   ```python
   if repository_root is None:
       hmic_verified = False
       hmic_detail = "... no repository root was supplied ..."
   else:
       try:
           hmic_validation = validate_active_hatp_mandatory_independent_verification_certification(
               repository_root
           )
           hmic_verified = certification_status_satisfies_readiness(hmic_validation.status)
           hmic_detail = f"fresh HMIC active-certification validation: status={hmic_validation.status.value} ({hmic_validation.reason})"
       except Exception as exc:
           hmic_verified = False
           hmic_detail = f"... raised {exc.__class__.__name__}: {exc} ... fail-closed"
   checks.append(
       HATPMandatoryActivationReadinessCheck(
           "mandatory_consumption_implementation_independently_verified",
           hmic_verified,
           hmic_detail,
       )
   )
   ```

No other check's construction changed. The check's `name` string is
byte-identical to before. No seventh HMRC-REQ-054 item was introduced;
the six-item conjunction remains exactly six.

## 8. Production Diff Classification

`git diff dd649271 -- src/pcae/` touches exactly one file:
`hatp_mandatory_cutover.py`. Every added hunk classifies as:

- `HMIC_READINESS_IMPORT` — the narrow, two-symbol import (§7.1).
- `HMIC_VALIDATION_CALL` / `READINESS_FACT_MAPPING` — the fifth check's
  new construction (§7.3).
- `LOCK_HELD_RECHECK_PRESERVATION` / `TESTABILITY_ONLY` — the
  `repository_root` parameter threading through the two internal seams
  and two public wrappers (§7.2), required so the lock-held recheck
  inside `_write_cutover_transition`'s `readiness_check` callable
  reaches the same validator call with a real repository root.

`UNRELATED = 0`.

## 9. Contract and Validator/Admin Module Byte Stability

- `hatp_mandatory_certification.py`: byte-unchanged since `dd649271`
  (confirmed by direct byte comparison against `git show
  dd649271:src/pcae/core/hatp_mandatory_certification.py`).
- `scripts/hatp_certification_admin.py`: byte-unchanged since `dd649271`
  (same method).
- HMIC-001 v1.1, HMRC-001, HATP-001, HSCE-001, RAE-001, RWMPC-001,
  PBPA-001, PBPC-001: all eight bound contracts confirmed byte-unchanged
  since `dd649271` (`git diff --name-only dd649271 -- <paths>` empty).

## 10. Six-Item Conjunction Preservation

`tests/test_phase_149o_19_5f_hmic_activation_readiness_integration.py::TestSixItemConjunctionPreserved`
independently confirms: the readiness result still carries exactly seven
named checks (the six HMRC-REQ-054 items plus the module-owned identity
check); an AST walk of the seven `checks.append(...)` call sites
confirms no eighth was added; and an AST-block diff against the
pre-Wave-F source confirms every check's construction other than the
fifth is byte-for-byte AST-identical to before.

## 11. Current Real-Host Readiness Result

Read-only inspection against `HATPTrustStore.production().root` and this
repository's own working tree:

```
ready: False
class_b_protected_storage_available: False (protected root absent)
repository_deployment_identity_valid: False (no local repository_instance_id provisioned)
hatp_substrate_operational: False (protected storage unavailable)
hsce_signing_implementation_available: True
mandatory_consumption_implementation_independently_verified: False
    -> fresh HMIC active-certification validation: status=ACCESS_ERROR
       (could not derive current repository/deployment identity)
production_dependency_provenance_valid: True
protected_activation_authority_mechanism_available: False (protected root absent)
```

No `certifications.json`/`certification-bindings.json` exists anywhere
under this host's real protected root, before or after this
inspection — the readiness call is read-only and creates nothing.
Overall readiness remains honestly `False`; HMIC alone cannot and does
not change this.

## 12. Fresh Validation / No Cache

`TestFreshnessNoCache` confirms: two successive calls to
`_assess_hatp_mandatory_activation_readiness_at_root` against the same
isolated fixture, with a certification stored between them, observe
different results (`False` then `True`) — no memoization. A static
source check confirms no `lru_cache`/`functools.cache`/
`cached_property` decorator anywhere in the module.

## 13. Lock-Held Recheck and TOCTOU Races

`TestLockHeldRecheckAndTOCTOU` (isolated fixtures only, never the real
host):

- **Successful activation**: an isolated fixture with all six
  HMRC-REQ-054 terms genuinely satisfied (HMIC via the real validator
  against a self-consistent fixture certification; the other five via
  isolated/test seams, `hatp_substrate_operational` monkeypatched since
  a genuine Class-B hardware fixture is out of this phase's scope)
  reaches `HATP_MANDATORY` — the only place this suite writes real
  cutover state, and only in `tmp_path`.
- **Revocation between assessment and activation**: an advisory
  pre-lock assessment reports `ready=True`; the certification is then
  revoked; `_activate_hatp_mandatory_at_root` is called and raises
  `HATPMandatoryActivationReadinessError` — the Cutover Record is
  byte-identical before/after, mode remains `PREPARED`, no activation
  marker is created.
- **Binding change between assessment and activation**: same outcome,
  triggered by re-pointing the active binding at a nonexistent
  certification.
- **Implementation drift between assessment and activation**: same
  outcome, triggered by mutating a frozen fixture file after the
  pre-lock assessment.
- **Lock-held recheck instrumentation**: the real validator function is
  wrapped to record call sites; activation is proven to invoke it again
  (fresh) after the transition lock is acquired, never trusting the
  pre-lock call's result.

## 14. One-Way Cutover Preservation

`TestOneWayCutoverAfterActivation`: in an isolated fixture, activation
to `HATP_MANDATORY` followed by certification revocation leaves the
Cutover Record's mode at `HATP_MANDATORY` — readiness may now honestly
report the HMIC term unmet, but the protected cutover state itself is
never downgraded. A static check additionally confirms no
`(HATP_MANDATORY, PREPARED)`/`(HATP_MANDATORY, LEGACY_COMPATIBLE)` entry
exists in the transition graph.

## 15. Semantic Walls (Restated, Unchanged)

HMIC `VALID` supplies exactly one of six HMRC-REQ-054 terms. It is not,
and this phase does not make it: HATP production ready by itself,
activation, rollback approval, PB `ALLOW`, execution capability,
Class-B-deployed, substrate-operational, or runtime/executed-source
provenance. HMIC-REQ-063 (runtime/executed-source binding) remains
explicitly deferred — untouched by this phase.

## 16. Tests

`tests/test_phase_149o_19_5f_hmic_activation_readiness_integration.py`
(49 tests, new): frozen-scope disposition; no-caller-suppliable-input;
exact enum mapping (parametrized over all 9 `CertificationStatus`
members); real validator integration for every reachable status
(`VALID`, `MISSING`, `REVOKED`, `IMPLEMENTATION_MISMATCH`,
`CONTRACT_MISMATCH`, `WRONG_REPOSITORY`, malformed binding);
validation-exception fail-closed; six-item conjunction preservation;
override-never-bypasses-other-checks (both directions); full positive
fixture; freshness/no-cache; lock-held recheck and four TOCTOU race
scenarios; one-way cutover; current real-host readiness; production
diff classification; no-real-effects restatement.

Twelve pre-existing test modules from Phases 149O.19.3 through
149O.19.5E.4 asserted, as their own contemporaneous evidentiary claim,
that this readiness ceiling was still hardcoded `False`/unwired at the
time each of those phases concluded. Per this repository's established
"restated, not weakened" methodology (see e.g.
`test_phase_149o_19_3r_1_...py`'s own `_POST_REPAIR_ALLOWED_NEW_FILES`
precedent), each such assertion was repinned to read the file's content
*as of that phase's own pre-Wave-F historical commit* (via `git show`)
rather than weakened to accept either the old or new state — preserving
every historical claim exactly while unblocking this phase's
intentional, independently-gated change. Files touched this way (test
files only, no production/contract change):
`test_phase_149o_19_3_hmic_contract_independent_verification.py`,
`test_phase_149o_19_3r_hmic_frozen_file_set_contract_repair.py`,
`test_phase_149o_19_3r_1_hmic_frozen_identity_repair_independent_reverification.py`,
`test_phase_149o_19_5a_hmic_certification_models_canonical_parsing.py`,
`test_phase_149o_19_5c_hmic_protected_certification_state_store.py`,
`test_phase_149o_19_5d_hmic_active_certification_validation_engine.py`,
`test_phase_149o_19_5e_1_hmic_v1_1_validator_admin_identity_contract_evolution.py`,
`test_phase_149o_19_5e_2_hmic_v1_1_contract_independent_verification.py`,
`test_phase_149o_19_5e_3_hmic_v1_1_24_file_production_identity_alignment.py`,
`test_phase_149o_19_5e_4_hmic_v1_1_24_file_alignment_independent_verification.py`,
`test_phase_149o_19_5e_hmic_protected_admin_certification_revocation.py`,
`test_phase_149o_19_hmrc_mandatory_consumption_independent_verification.py`.
Four of these twelve (`test_phase_149o_19_3`, `test_phase_149o_19_5a`,
`test_phase_149o_19_5e_3`, `test_phase_149o_19_5e_4`) needed a *second*,
small repin pass after this phase's own commit landed — see §19 item 3
for why (a fixed-historical-commit-vs-`HEAD` comparison that was
dormant while this phase's change was still uncommitted).

## 17. Regressions

- Wave A–E and E.1–E.4 suites (`test_phase_149o_19_5a` through
  `test_phase_149o_19_5e_4`, plus `test_hatp_mandatory_activation_guard.py`):
  all pass after the pinning repairs in §16.
- HMIC contract regression
  (`test_phase_149o_19_2`/`_3`/`_3r`/`_3r_1` contract-freeze/repair
  suites): pass, with the one confirmed pre-existing/unrelated exception
  in §18.
- HMRC readiness/cutover regression (`test_hatp_mandatory_activation_guard.py`,
  `test_phase_149o_19_hmrc_mandatory_consumption_independent_verification.py`):
  pass.
- Broad HATP/HMRC sweep (all `test_*hatp*`/`test_*hmrc*`/`test_*hmic*`
  files, 63 files, one pre-existing `fido2` import-error file excluded —
  environment-missing optional dependency, unrelated to this phase):
  after the full repin pass (§16, including the second, post-commit
  round), only the one confirmed pre-existing/unrelated failure in §18
  remains.
- Fast Green: see §19 for the full three-stage account (uncommitted →
  committed → repinned) and final clean result.

## 18. Pre-Existing, Unrelated Finding (Not Remediated)

`test_phase_149o_19_3r_hmic_frozen_file_set_contract_repair.py::test_no_production_source_changed_by_this_repair`
fails identically with and without this phase's changes (confirmed via
`git stash -u` A/B): it compares `git diff <149O.19.3-entry-commit>
HEAD -- src/pcae/` and asserts the result is empty, but
`hatp_mandatory_certification.py` was legitimately created by a much
later phase (149O.19.5A), long after 149O.19.3R concluded — the test's
own historical-scoping constant was never updated for that later,
unrelated addition. Outside this phase's allowed-file scope; reported,
not repaired, consistent with 149O.19.5E.4's own precedent for
similarly-scoped stale findings.

## 19. Fast Green

Method: `pytest -m fast_green --ignore=tests/test_phase_149o_7_hatp_class_b_activation_independent_verification.py`
(the ignored file has a pre-existing, unrelated `fido2` optional-
dependency `ImportError` at collection time in this environment),
iterated three times as the phase's own uncommitted-vs-committed state
changed, each time comparing against a `git stash -u` A/B baseline:

1. **Baseline** (this phase's changes stashed): 24 failed, 6136 passed.
2. **With this phase's changes uncommitted**: 28 failed, 6181 passed —
   exactly 4 additional failures, all literal `git diff HEAD`/`git
   status --porcelain` (working-tree-vs-current-HEAD) checks that
   depend on nothing being committed yet.
3. **After this phase's own commit landed**: those 4 self-resolved as
   predicted, but 6 *different*, previously-latent failures surfaced —
   tests in files this phase already touches
   (`test_phase_149o_19_3`, `test_phase_149o_19_5a`,
   `test_phase_149o_19_5e_3`, `test_phase_149o_19_5e_4`) that compare a
   **fixed historical commit** against literal `HEAD` (not the working
   tree) — these were silent while `HEAD` still equaled that fixed
   commit's own later descendant `dd649271` (i.e. while this phase's
   change was uncommitted), and only became visible once `HEAD` actually
   advanced past it. All 6 repinned identically to the 12 in §16/§17
   (read via `git show <pre-Wave-F-commit>` or an explicit second
   fixed-commit upper bound, never `HEAD`) — no weakening, same
   methodology, same pre-Wave-F commit (`dd649271`).
4. **Final run, post-repin, fully committed**: 25 failed, 6184 passed —
   exactly the original 24-failure baseline plus one additional,
   confirmed-flaky node
   (`test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`,
   the identical flaky node 149O.19.5E.4's own phase report already
   documented; re-run in isolation here too: 1 passed). A line-level
   diff confirms the baseline's 24 failures are an exact subset of these
   25.
5. **Clean deselected run** (all 25 confirmed pre-existing/unrelated
   node IDs explicitly deselected): **0 failed, 6184 passed, 2 skipped**
   (363.24s).

**Reported `fast_green` field for this phase's own canonical report:**
`0 failed, 6184 passed, 2 skipped` (clean, deselected run); raw run
without deselection: `25 failed, 6184 passed, 2 skipped` (382.75s) — 24
confirmed pre-existing via the `git stash -u` A/B method (identical set,
same node IDs, older differently-scoped "no `src/pcae/**` file changed
since my phase" assertions unrelated to HMIC/HATP semantics, one flaky
Python-3.9-interpreter-version check, one AG3/AG5/PB argument-shape
check — the same subset `test_phase_149o_19_5e_4`'s own report
attributed), plus 1 additional flaky node confirmed passing in isolated
re-run.

## 20. Governance Checks (Close)

- `pcae health`: healthy.
- `pcae check`: passed.
- `pcae status coherence`: coherent.
- `pcae doctor task-memory`: pre-existing warnings only (same
  `tasks/done/` bookkeeping gap noted at baseline, §1 — unrelated,
  unremediated, outside allowed-file scope).
- `pcae push check`: run after commit, before push.
- `pcae runtime inspect`: Observed / observe / unavailable (unchanged).
- `pcae notify status`: Telegram configured/enabled/ready (unchanged).

## 21. Implementation Verdict

**HMIC ACTIVATION-READINESS INTEGRATION: IMPLEMENTED**
**— HMIC VALID NOW SUPPLIES EXACTLY ONE HMRC READINESS FACT**
**— FRESH LOCK-HELD ACTIVATION RECHECK PRESERVED**
**— NO REAL ACTIVATION PERFORMED**

**W-1: REMAINS INDEPENDENTLY CLOSED AT CONTRACT + IMPLEMENTATION-IDENTITY BOUNDARY.**

HATP production remains **NOT READY**: no real HMIC certification, no
Class-B provisioning, runtime/executed-source binding still deferred
(HMIC-REQ-063), Permission Broker and POL-005 unchanged, COMP-002 not
implemented. Runtime remains Observed / observe / unavailable.

## 22. Recommended Next Phase

**149O.19.5G — HMIC Assembled Attack Matrix / Hardening**, per
`docs/PHASE_149O_19_4_..._IMPLEMENTATION_PLAN.md`'s own naming. Expected
scope: assembled Wave A–F adversarial testing across the now-wired
readiness-integration boundary; no new capability by default; narrow
repairs only if this phase's own findings require them; no real
activation, no Class-B provisioning, no PB/POL-005/COMP-002 changes. No
phase after 149O.19.5G is pre-authorized by this document.
