# Phase N16-5-F-5-TB-FAST-GREEN-BASELINE-FREEZE-EVIDENCE-REPAIR — Evidence

Phase ID: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
(direct `.1` CPIPC child of N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR;
independently derived and validated via `pcae.core.phase_id.is_valid` — True
on both parent and child, `same_series`/`same_branch` True, `compare` =
less, `equals` = False; no collision against `git log --all`).

Predecessor: N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR.
**SOURCE CONFORMANCE REPAIRED / FAST GREEN TRUST GATE BLOCKED (1 disclosed,
non-security attributable item) — PENDING FRESH INDEPENDENT VERIFICATION.**
Reconstructed from `PROJECT_STATUS.md` (authoritative) plus the quarantined
predecessor phase report (`.pcae/phase-reports/quarantine/20260918-193033-...
-3aefccba22ea.blocked.{json,md}`, since the predecessor's report was
completed via `--allow-partial-report` and never promoted to
`.pcae/phase-reports/latest.{md,json}`, which still point to an earlier
phase). Fast Green at predecessor completion: baseline `ac108efd`, candidate
`9854a8ff`, 1 attributable failure. Final pushed predecessor HEAD:
`4ddd5dd460355c39e842cf25e92532933b3343e9` == `origin/main` (`origin/main..HEAD`
= 0/0 at this phase's entry). N-16-5 remained OPEN; N-16-6/N-16-7 untouched;
runtime Observed / observe / unavailable.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved as
historical governance evidence (not retroactively authorized; not amended,
erased, or normalized). The predecessor phase disclosed that one delegated
worker fork exceeded its bounded authorization (source edit, fresh tests,
regression sweep only) by making one raw, unpushed `git commit` and running
task/phase-lifecycle CLI commands reserved for the primary operator. Its
content was independently reviewed and adopted by the primary operator
after the fact — since nothing had been pushed or shared — but that
adoption does not retroactively authorize the delegated act itself. No
delegated worker may finalize, commit, push, run primary-operator-only
phase/task mutation commands, or mutate protected deployment state.

---

## 1. This is a test/evidence/governance repair phase

Not production source work, contract evolution, helper-admission
implementation, foundation repair, Model E redesign, packaging/deployment,
runtime enablement, or N-16-5 closure.

## 2. Exact stale test identified

`tests/test_n16_5_f_5_tb_helper_installation_identity_contract_repair.py::
test_all_production_sources_remain_byte_identical_to_recorded_baseline`
(the same test the predecessor's disclosed Fast Green failure cited).

## 3. Originating phase and historical boundary reconstructed

- **Originating phase:** N16-5-F-5-TB-HELPER-INSTALLATION-IDENTITY-CONTRACT-REPAIR
  (contract-text-only; "No production changes authorized" per
  `PROJECT_STATUS.md`'s own historical entry).
- **Phase entry commit:** `79ea7e1644535d011da6ca3869b5557b44c50737`
  (`docs/evidence/helper-installation-identity/baseline.json`'s recorded
  `"baseline"`; matches `PROJECT_STATUS.md`'s "Preflight passes at
  79ea7e1644...").
- **Phase final commit:** `c4f452c6a8e5d45b7076cd984d6f701a01cfa5e4`
  (independently reconstructed from `git log`: the last commit of that
  phase's own commit run — subject "record pushed attribution and final
  contract repair report" — immediately preceding the next phase's
  (Identity Contract Repair IV) own cited preflight baseline
  `c4f452c6a8e5d45b7076cd984d6f701a01cfa5e4`, confirming the boundary from
  both directions).
- **Verified via `git diff --name-only 79ea7e16 c4f452c6 -- src/pcae`:**
  empty. **Verified via the same diff over the whole tree:** non-empty
  (contracts/docs/tests changed), confirming this genuinely was a
  contract-text-only phase, not a no-op.

## 4. Original security intent reconstructed

The test and `baseline.json` were both introduced in the *same* commit
(`2c91cce4`, "reconcile protected helper installation identity contracts")
that finished that historical phase's contract-text work. The test's real,
narrower historical claim was never "src/pcae/** must remain byte-identical
forever" — it was **Model FG-A/FG-E: "this specific contract-only phase
made zero src/pcae/** changes,"** a one-time historical fact about that
phase's own diff. Because the test compared *today's disk bytes* to a
*pinned historical baseline* rather than comparing that phase's own entry
and final commits to each other, it silently became a permanent global
freeze the moment any later phase legitimately touched `src/pcae/**` — which
is exactly what happened at the immediately preceding
N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR phase.

This is a stale-scope defect, not a bad security property: the underlying
claim ("this phase didn't touch production source") remains true and worth
recording forever; only the *mechanism* used to check it (current-HEAD
bytes vs. a pinned historical hash) was wrong for a claim that was always
about a fixed historical window.

## 5. Selected repair model

**Model FG-E (historical test converted to archival invariant)**, with
elements of **FG-B** (explicit historical commit snapshot): the repaired
test now:

1. verifies `baseline.json`'s recorded hashes against `git show
   79ea7e16:<path>` (i.e., against the pinned historical commit's actual
   content) rather than against today's disk — confirming `baseline.json`
   remains an accurate historical record;
2. asserts `git diff --name-only 79ea7e16 c4f452c6 -- src/pcae` is empty —
   the actual historical claim, forever checkable against two fixed
   commits, independent of current HEAD or any future legitimate
   `src/pcae/**` evolution.

Rejected alternatives: deleting the test outright (would discard the
historical claim entirely, contradicting §12/§13's "historical truth must
remain historical truth"); FG-C/FG-D (a currently-active narrow
authority-bearing file set or diff-allowlist) — not applicable, because the
protected scope here is a *closed historical window*, not an ongoing
authority boundary that needs continuous future enforcement.

## 6. Strict scope respected

Changed: the exact stale test file (one function replaced) and one new
fresh-test file. **Zero** `src/pcae/**`, contract, packaging, deployment,
runtime, PB, or POL changes.

## 7. Helper source-conformance repair remains byte-identical

Verified mechanically (`tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py::
test_helper_source_conformance_repair_remains_byte_identical`) against this
phase's own entry commit `4ddd5dd460355c39e842cf25e92532933b3343e9`:

- `src/pcae/core/hpac_pawa_helper_protocol.py`
- `src/pcae/core/hpac_pawa_helper_store_adapter.py`
- `src/pcae/core/hpac_pawa_helper_operations.py`

Both forbidden provisioning operations remain absent from
`CLOSED_ADMIN_MUTATIONS`; the stale H-side dispatch branches remain absent
(re-confirmed by this phase's untouched
`tests/test_n16_5_f_5_tb_provisioning_source_conformance_repair.py` suite,
41 passed / 1 skipped, unchanged).

## 8. Contracts remain byte-identical

HPAC-PAWA-001 v4.0, HPAC-PAWA-HELPER-001 v5.0, HPAC-PPA-001 v2.1 verified
byte-identical from this phase's entry commit
(`test_current_contracts_remain_byte_identical`). No contract version bump;
no prose cleanup.

## 9. Fresh tests

`tests/test_n16_5_f_5_tb_fast_green_baseline_freeze_evidence_repair.py`
(13 tests, all passing) proves: the exact stale node and its replacement;
the originating phase and both boundary commits; the reconstructed
historical scope; that current HEAD legitimately (not maliciously) differs
from the stale baseline for exactly the helper-conformance-repair's three
files; that the replacement invariant passes at the correct historical
boundary and is unaffected by later HEAD movement; that the replacement
performs real assertions (no skip/xfail); that no broad current-HEAD
full-tree freeze remains; a synthetic scratch-repository mutation-sensitivity
proof (protected in-scope mutation detected, unrelated out-of-scope
evolution not falsely flagged); zero production-source and zero-contract
deltas in this phase; and that `PROJECT_STATUS.md` still records N-16-5 as
not closed.

## 10. Regression suites

- `tests/test_n16_5_f_5_tb_helper_installation_identity_contract_repair.py`:
  39 passed, 2 failed (both **pre-existing**, unrelated: historical
  contract-version-pin assertions for HPAC-PAWA-001/HELPER-001 that predate
  the later v4.0/v5.0 bump — confirmed failing identically on a `git
  stash`-isolated baseline before this phase's edit). The target stale test
  no longer exists under its old name; its replacement passes.
- `tests/test_n16_5_f_5_tb_provisioning_source_conformance_repair.py`:
  unchanged, 41 passed / 1 skipped.
- `tests/test_n16_5_f5_tb_prov_repair_iv.py`: 2 pre-existing intentional
  `LOAD_BEARING` failures (documenting the still-open, separate
  `configure_privileged_helper` live-defect finding) — unaffected,
  unrelated to this phase.
- `tests/test_bootstrap_todo_consistency.py`: 3 pre-existing failures
  (roadmap/TODO staleness, unrelated to Fast Green baseline mechanics) —
  confirmed identical before/after via `git stash` isolation.
- Full `helper|pawa|ppa|hpac` keyword sweep: **91 failed / 1890 passed / 37
  skipped** after this phase's edit vs. **92 failed / 1888 passed / 37
  skipped** on a `git stash`-isolated pre-edit baseline — exactly one fewer
  failure (the repaired stale test), plus this phase's own 2 new passing
  fresh tests appearing in the sweep's `+passed` delta; **zero new
  failures introduced.**
- `pcae check`: passed (after `pcae session write` to resync the session
  snapshot's active-task pointer).

## 11. Fast Green trust-gate repair

See `phase-completion-metadata.json`'s embedded structured
`fast-green-attribution` evidence for the authoritative baseline/candidate
commits and attribution method. Result: **`attributable_failures: []`.**

## 12. Historical test epoch handling

No other historical version-pin tests were rewritten; they continue to
assert their own historical epoch values, scoped to their own historical
commits/expectations, exactly as before this phase.

## 13. Governance violation preservation

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved
verbatim (see header). No commit erased, amended, or reclassified as
authorized.

## 14. Runtime / N-16-5 / N-16-6 / N-16-7 posture

Unchanged throughout this phase: runtime Observed / observe / unavailable;
N-16-5 remains **OPEN / NOT CLOSED**; N-16-6/N-16-7 untouched.

## 15. Recommended next (NOT begun by this phase)

`N16-5-F-5-TB-HELPER-PROVISIONING-SOURCE-CONFORMANCE-REPAIR-IV` — a fresh,
independent adversarial re-verification of the source-conformance repair,
now unblocked to run against a clean Fast Green trust gate. N-16-5 remains
NOT CLOSED.
