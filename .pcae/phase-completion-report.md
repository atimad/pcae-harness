# Phase 149O.20L.7O.2S.4 Complete — FGSC-001 Staleness Carve-Out / Attribution Completeness Narrow Repair

Repairs the 149O.20L.7O.2S.3 Blocking finding. `validate_structured_fast_green()`
(`src/pcae/core/fast_green_attribution.py`) previously computed its
freshness (staleness) check before independently recomputing
`attributable_failures` and the conservation/bucket-membership checks, and
contained an internal `if issues: return issues` guard that could return a
staleness-only issue list to the FGSC-001 caller
(`validate_derived_correctness()`, `phase_reports.py`) before attribution
recomputation ever ran — letting an artifact combining an allowed
finalization delta with a genuine, unclassified regression reach
`FINALIZATION_VERIFIED` undetected.

**Repair**: relocated the freshness check to run last in
`validate_structured_fast_green()`, strictly after the
nonzero-`attributable_failures` check, so a staleness-only result is now
sound proof every other structured-evidence validity check already ran
and passed. Single-file production diff; no new module, no change to
bucket definitions, scalar Fast Green, path classification, or Stage B.

Reproduced the exact 2S.3 Blocking scenario at phase-entry HEAD via the
pre-existing 2S.3 regression tests before repairing, then flipped those
same two tests from documented-defect to correctness assertions after the
fix (both now correctly reject the vulnerable case). Added a new 6-test
focused suite covering the required attack matrix: a valid nonzero-raw/
fully-excluded case that still passes under staleness, plus five
independent staleness-plus-other-defect cases (omitted node, cross-bucket
duplicate, forged pre-existing label, environment-bound abuse,
expected-artifact-identity abuse) that all still reject.

427 tests pass across the full directly-relevant sequential suite set
(2S.1–2S.4, 2R, 2R.1, 88N.5 scalar, phase-report-trust, architecture-status,
report-consistency); zero regressions. The full repository-wide
`-m fast_green` suite proved unreliable in this sandbox for full
completion (concurrent xdist worktree interference produces a large,
order-of-magnitude-consistent failure set even on a fully clean,
unmodified HEAD, confirmed via A/B comparison; direct inspection shows
those specific failures are pre-existing "no source changed since an old,
unrelated phase's entry commit" assertions unrelated to this repair) and
was not used as completion evidence.

**Disposition of the 2S.3 Blocking finding: REPAIRED — INDEPENDENT
VERIFICATION PENDING** (not independently closed in this repair phase).

Full text: `docs/PHASE_149O_20L_7O_2S_4_FGSC_001_STALENESS_CARVEOUT_NARROW_REPAIR.md`.

**S22.1/S22.2 self-hosting acceptance remains NOT authorized** until
149O.20L.7O.2S.5 independently closes this finding. Phase 149O.20L.7O.2P
reconciliation remains gated behind that outcome and was confirmed
untouched by this phase.

Recommended next: **149O.20L.7O.2S.5 — FGSC-001 Staleness Carve-Out
Attribution Completeness Repair Independent Verification.**
