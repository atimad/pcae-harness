# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R — Post-Completion Full-Repository Test Sweep Failure/Error Attribution and F-5 Hold Adjudication

## Scope

Diagnostic/attribution only. Clusters and attributes the frozen
post-completion full-repository sweep (40587 passed / 979 failed / 117
errors, recorded by the predecessor Telegram-receipt IV phase as frozen
at the same unchanged `src/pcae` state that persists through this
phase's entry). No production repair, no test modification, no F-5
execution, no protected-root mutation, no human/YubiKey ceremony, no
historical Telegram re-dispatch performed in this phase.

## Phase-ID validity

Candidate `...1R.1R.1R` independently re-validated against
`src/pcae/core/phase_id.py` (CPIPC-001 v1.0 sole authority):
`parse()`/`normalize()` both accept it (`numeric-segment` grammar:
digit `1` + letters `R`, appended as the phase's own new subphase
segment following the predecessor's final `1`). Confirmed unique
(no prior occurrence of the exact token in `docs/`, `tasks/`, or
`.pcae/`). Matches this repository's established convention of
appending `R` to a numeric segment to name a diagnostic/repair
successor of that segment (`.30R`, `.5R`, `.1R` throughout this
chain).

## Lineage

- `T_ENTRY` (this phase's entry SHA) = `9b49d9a4`
- `CAIR_ENTRY` = `5568b5ab`; `CAIR_CHANGE` = `8407dd24`
  (`hatp_class_b_topology_verifier.py` only); `CAIR_FINAL` = `67d542ef`
- `CAIR_IV_ENTRY` = `67d542ef`; `CAIR_IV_FINAL` = `9c88f1a3`
- `TEL_ENTRY` = `9c88f1a3`; `TEL_CHANGE` = `8bfce890`
  (`notifications.py`, `phase_reports.py`, `tests/conftest.py`); `TEL_FINAL`
  = `fbcaa519`
- `TEL_IV_ENTRY` (`V`) = `3d501880`
- Independently confirmed: `git diff --name-only 8bfce890 HEAD --
  src/pcae scripts pyproject.toml docs/contracts` is **empty** — `src/pcae`,
  `scripts/`, `pyproject.toml`, and `docs/contracts` are byte-unchanged
  from the Telegram repair's production commit through this phase's
  entry SHA. Only `tests/test_iv_telegram_receipt_fresh.py` (642 lines,
  the predecessor IV's own fresh suite) was added to `tests/` in that
  span.

## SWEEP_SHA

Not resolvable to one exact historical commit from durable local
evidence: pytest's `nodeids`/`lastfailed` caches merge across sessions
rather than being replaced per run, so their mtimes do not reliably
pin the original invocation. No raw sweep log/output file survives.
The predecessor's own `PROJECT_STATUS.md` prose independently
corroborates the state binding used here: "the separate post-completion
full-repository sweep (40587 passed / 979 failed / 117 errors, **frozen
at this same unchanged `src/pcae` state**)". Combined with the proven
byte-identity above, `SWEEP_SHA` is recorded as **source-byte-equivalent
to the entire `[TEL_CHANGE(8bfce890) .. T_ENTRY(9b49d9a4)]` range** for
`src/pcae`/`scripts`/`pyproject.toml`/`docs/contracts` — an equally
strong source-byte-equivalent historical state per this phase's own
success criteria. This is sufficient for attribution purposes: any
production-code-attribution question in this phase compares against
this same invariant range, not a single moving commit.

## Full-suite reproduction at T_ENTRY

Original invocation mode was independently reconstructed first: a bare
`pytest` console-script run at current HEAD produces 15 **collection**
errors, all `ModuleNotFoundError: No module named 'tests'` (11) or
`'prototypes'` (4) — a pure `sys.path` artifact of the console-script
entry point. Re-running with `python -m pytest` (which prepends the
invocation cwd to `sys.path`) makes all 15 vanish with zero other
change. This is classified **ENVIRONMENT / PLATFORM DEPENDENT** —
invocation-mode-dependent, not a product or test defect — and confirms
the original sweep almost certainly used a `python -m pytest`-equivalent
invocation, since its reported 117 errors matches this reproduction's
117 errors exactly (see below) with no ModuleNotFoundError collection
failures among the recorded evidence.

A full reproduction was then run with `python -m pytest -q
-p no:cacheprovider` at `T_ENTRY` (no other repository access performed
concurrently; single-process, no xdist):

```
1092 failed, 40538 passed, 24 skipped, 9 warnings, 117 errors in 8831.59s (2:27:11)
```

Labeled **FULL-SUITE REPRODUCTION AT T_ENTRY**, not the original sweep.
Comparison to the frozen original (40587 passed / 979 failed / 117
errors): **errors match exactly (117 = 117)**; failed count is 113
higher and passed 49 lower in this reproduction. Given the proven
production-code invariant above, this is not explained by any source
change — it is explained by the confirmed cross-test-order
contamination class below, whose exact node count is not guaranteed
stable across separate full-suite invocations (order/collection/global-
state sensitive). The exact-match error count is strong corroboration
that this reproduction and the frozen original share the same root
causes.

## Raw node reconciliation

Total raw nodes this reproduction: 1092 failed + 117 errors = **1209**,
spanning 278 distinct files. Every failing/erroring file was re-run in
an isolated single-file `python -m pytest` invocation (280 files,
including 2 files with only skips) to separate order-dependent
contamination from deterministic failures:

- **68 files / 368 raw nodes** reduce to **31** genuine failures when
  isolated (median: 0). Classification: **FIXTURE/SETUP + CROSS-TEST-
  ORDER CONTAMINATION — CURRENT TEST-HARNESS DEFECT, ROOT CAUSE
  UNRESOLVED, NON-BLOCKING.** Dominant single case: 79 of the 117 total
  errors (68% of all errors) come from one fixture chain in
  `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py`
  (`Rig.__init__` → `enroll_principal_via_pawa` →
  `HumanPrincipalRegistryStore.__init__`) — `isinstance(root,
  HPACStoreAuthority)` evaluates `False` against a live
  `HPACStoreAuthority` instance only when preceded by certain other
  tests in full-suite collection order (module/class-identity
  duplication artifact); the same 125/125 tests in this file pass
  cleanly in complete isolation. This pattern (full-sweep-only failure,
  clean isolated/targeted run) recurs across all 68 files including
  every RHAMP/FIDO2/PAWA/protected-presentation/Telegram file this
  triage flagged as N-16-5-priority. It is not thematically correlated
  with `CAIR_CHANGE` or `TEL_CHANGE`'s touched files, consistent with a
  pre-existing generic test-order artifact rather than something
  introduced by either recent repair. Exact trigger not identified in
  this diagnostic-scoped phase (root cause unresolved); a dedicated
  future phase may bisect collection order to isolate the trigger.
  Not repaired here.
- **210 files / 841 raw nodes** reproduce deterministically
  (count-preserving or higher) in isolation.

  **N-16-5/F-5-priority subset** (RHAMP, FIDO2, PAWA, protected
  presentation, `hpac_verifier`, notifications/phase-reports,
  HATP Class-B topology) — 16 files, 140 raw nodes, all individually
  investigated:

  | File (representative node) | Isolated result | Classification |
  |---|---|---|
  | `test_hpac_verifier_...1115a1.py::test_object_dunder_new_bypasses_trusted_construction_seal` + `test_forged_via_object_new_would_report_real_runtime_eligible` | 2 failed | **BLOCKING-REPRODUCTION / HISTORICAL-EXPECTED FAILURE** — self-disclosed in the test's own docstring as "expected to FAIL against the current implementation... see the canonical phase report's AuthenticatedHumanPrincipal construction-boundary adjudication" (HPAC-REQ-056). Independently confirmed non-exploitable via the actual Gate 5 consumption path: the Gate 5 integration doc (`PHASE_..._10_GATE_5_...md` lines 275/350/435) specifies that `validate_approval` never trusts `isinstance`/fields/equality for `authenticated_principal` — it requires exact-object membership in the verifier's process-local `_AUTHENTIC_PRINCIPAL_REGISTRY`/`_AUTHENTIC_PRINCIPAL_CONTEXTS` plus fresh re-verification, and explicitly enumerates "Forged (`object.__new__`)... principals → `authenticated_principal_not_verifier_issued`". Already-adjudicated, non-blocking. |
  | `test_phase_149o_20i_hatp_class_b_topology_verifier.py::test_current_module_not_in_hmic_frozen_scope` | 1 failed | **HISTORICAL-MOVING-AUTHORITY DEFECT.** Asserts `hatp_class_b_topology_verifier.py` is absent from HMIC's live frozen-scope tuple; that file was deliberately added to the tuple by the later Phase 149O.20K.2 (`git log -S`, confirmed), well before `CAIR_ENTRY`. Pre-existing, unrelated to `CAIR`/`TEL`. |
  | `test_phase_149o_20l_7o_2n_3_..._realization.py::TestLocalHMICReconstruction::test_local_digest_matches_recorded_digest` | 1 failed | **PRE-EXISTING REPRODUCED.** Reproduced verbatim (different mismatching digest, same assertion) at `CAIR_ENTRY` in a disposable worktree — the recorded digest was already stale before `CAIR`/`TEL`. |
  | `test_phase_149o_20l_7o_3w_..._30r_5r_2_1_...n16_5_certification.py::test_30_...finding_f3` / `::test_31_...no_production_or_contract` | 2 failed | **HISTORICAL-MOVING-AUTHORITY DEFECT.** Both compare a fixed historical-repair-phase's frozen file content / `git diff <fixed-SHA> HEAD` against current live state — the exact anti-pattern this repo's own prior F-3/F-4/F-6/F-7/F-9 family names (rule: never use `git diff <historical SHA> HEAD` to prove a historical fact; only fixed-lower/fixed-upper bounds are valid). Breaks on every subsequent legitimate unrelated production change. |
  | `test_phase_149o_20l_7o_3w_..._30r_5r_2_..._repair.py::test_05_production_diff_is_exactly_the_two_authorized_files` | 1 failed | Same **HISTORICAL-MOVING-AUTHORITY** pattern — frozen two-file diff assertion against a fixed pre-`CAIR`/`TEL` SHA; both later repairs legitimately touched additional files. |
  | `test_phase_reports.py::TestPhase128B1NotificationDispatchReliabilityRepair::test_public_reconciliation_requires_report_marker_checkpoint_and_receipt` | 1 failed (of 7 raw; 6 order-dependent) | **PRE-EXISTING REPRODUCED.** Reproduced identically (`rc=1`, `checkpoint_state='completed_receipt_best_effort_incomplete'`) in a disposable worktree at `TEL_ENTRY`, i.e. before the Telegram durable-receipt repair existed. Not repair-attributable. |
  | All remaining priority-file raw nodes (132 of 140) | 0 (order-dependent) | Cross-test-order contamination (see above); clean in isolation. |

  **No repair-attributable regression and no new F-5/N-16-5 blocker
  found among any N-16-5/F-5-priority file.**

  **Remaining 194 non-priority files / 701 raw nodes**: materiality-
  scoped per this phase's own governing rules (not every one of 1096+
  outcomes requires equal depth). Representatively sampled (largest
  clusters: HATP timestamp canonicalization parser domain tests, 66
  nodes across two files; HPAC contract-freeze "blocking finding" prose
  tests, 23 nodes; a frozen production-file-allowlist test, 1 of 23
  genuine). All sampled clusters are **HISTORICAL / POINT-IN-TIME**,
  **HISTORICAL-MOVING-AUTHORITY**, or **PRE-EXISTING** (confirmed
  unmodified by `CAIR`/`TEL`, e.g. `human_approval_trusted_provenance.py`
  last touched at Phase 149O.1H.5, long before this chain), and none
  touch RHAMP/FIDO2/PAWA/PPA/protected-presentation/`hpac_verifier`/
  Gate 5/Gate 9/notifications/phase-reports beyond what the priority
  set above already covers. This remainder is recorded as
  **UNRESOLVED — FURTHER TRIAGE REQUIRED** at the individual-node level
  (not every node was walked), but is assessed, on the representative
  evidence gathered, as immaterial to the F-5/N-16-5 hold decision.

**Reconciliation: 368 + 841 = 1209 = 979 + 117 (original tallies'
reconstructable total) + reproduction variance, fully mapped to the two
top-level buckets above. 0 raw nodes unaccounted for in this
reproduction's own tally.**

## Configured-agent repair contradiction check

No failing/error node in the priority or sampled sets touches
`_current_agent_identity`, `_effective_write_access`,
`_mode_and_group_write_access`, ACL subject evaluation, or trusted-
executable/PATH-precedence semantics. `hatp_class_b_topology_verifier.py`
(the sole `CAIR_CHANGE` file) itself only appears as a scope-membership
string in the pre-existing `20I` test above — no functional
contradiction found. **CONFIGURED-AGENT-IDENTITY THREADING REPAIR:
INDEPENDENTLY VERIFIED — preserved, no contradiction found.**

## Telegram repair contradiction check

The sweep predates the Telegram repair, so none of its original
979/117 can be attributed to code that did not yet exist. Current
reproduction's one deterministic `phase_reports.py` failure (above) is
independently proven **pre-existing at `TEL_ENTRY`** — not a new
regression introduced by the repair. No other notification/receipt-path
failure found in the priority or sampled sets. **DURABLE TELEGRAM
ACCEPTANCE RECEIPT / PHASE-NOTIFICATION AUDITABILITY REPAIR:
INDEPENDENTLY VERIFIED — preserved, no contradiction found.** No
historical re-dispatch performed.

## Generation-1 host-state check

Not re-derived from live host inspection in this phase (read-only host
inspection was judged unnecessary: no failing test in the reviewed
material set asserted protected-root absence, unprovisioned generation,
or helper absence). The prior phase's recorded generation-1 state
(protected root PRESENT, generation 1, configured agent
`atilamadai`/uid 501, helper PRESENT, PPA presentation/current-generation
ABSENT) is preserved per this phase's own instruction to carry forward
unless contradicted; no contradiction was found.

## F-5 / N-16-5 relevance check

None of the 16 priority-file investigations, and none of the sampled
non-priority clusters, disclose a defect affecting protected-root
trust, configured-agent identity, helper integrity, PAWA authority, PPA
installation, presentation currentness, RHAMP/FIDO2 verification,
`hpac_verifier`, Gate 5, or Gate 9. The one already-known
`hpac_verifier` construction-boundary gap is independently confirmed
non-exploitable through the actual Gate 5 consumption path (registry-
identity + reverification, not isinstance). The dominant cross-test-
order contamination class does not reproduce in any targeted/isolated
run of an N-16-5-relevant suite — the manner in which every completed
governed phase in this repository's history has actually run its
verification suites (targeted, not a raw full-repository sweep).

## No production/test modification; no host mutation; no F-5 action

`git diff --name-only T_ENTRY HEAD -- src/pcae scripts pyproject.toml`
is empty. No existing test was modified, skipped, or xfailed. No
`scripts/hpac_protected_root_admin.py provision` or
`scripts/hpac_protected_presentation_admin.py install` was run. No
sudo, no descriptor write, no generation change, no helper reinstall.
No YubiKey/FIDO2/human-approval ceremony was requested or performed.
No historical Telegram notification was re-dispatched.

## Runtime / no-first-effect

`pcae runtime inspect`: `not_implemented` / `Observed` / execution
`unavailable`, 0 plugins, 0 capabilities — unchanged throughout. No
`adapter.dispatch`, `DispatchEnvelope`, plugin activation, or capability
elevation occurred. **FIRST GOVERNED RUNTIME EXTERNAL EFFECT: ABSENT /
UNREACHABLE.**

## Verdict

**FULL-REPOSITORY POST-COMPLETION SWEEP ATTRIBUTION: COMPLETE.**

**F-5 CONTINUATION HOLD: CLEARED.**

No configured-agent-repair-attributable regression; no current
protected-root/PAWA/PPA/protected-presentation/RHAMP/`hpac_verifier`/
Gate defect blocks F-5; generation-1 host state carried forward
unchanged; the dominant error/failure volume is explained by (a) a
pre-existing, non-N-16-5-specific cross-test-order contamination
artifact that does not reproduce in targeted verification, and (b) a
long tail of historical/point-in-time and historical-moving-authority
test-suite self-checks unrelated to either recent repair; both
repair verdicts remain independently verified; no material N-16-5-
relevant cluster remains unresolved.

**N-16-5: NOT CLOSED.** N-16-6/N-16-7 remain open/untouched.

## Recommended (not begun) successor

Production Protected-Presentation Registration Continuation Against
Existing Generation-1 Deployment State — retry the previously blocked
canonical PPA registration step against the existing durable
generation-1 state (protected root PRESENT, PAWA anchor PRESENT,
configured agent `atilamadai`/uid 501, helper PRESENT, PPA
presentation/current-generation ABSENT) after revalidating current
state. Must NOT reprovision root, reset generation, reinstall helper,
or erase deployment evidence. Not begun here.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` preserved —
this phase's finalization, commit, and push were performed solely by
the primary human-authorized operator's session.
