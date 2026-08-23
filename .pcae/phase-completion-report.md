# Phase 149O.20L.7O.2S.5 Complete — FGSC-001 Staleness Carve-Out Attribution Completeness Repair Independent Verification

Independently verified the 149O.20L.7O.2S.4 repair of the 149O.20L.7O.2S.3
Blocking finding in `validate_structured_fast_green()`
(`src/pcae/core/fast_green_attribution.py`).

**Independent reproduction**: built a disposable script and ran it against
a real `git worktree` checkout of the pre-repair checkpoint (`b9b83c28`,
with `PYTHONPATH` pointed at its own `src/`). The old code returns a
staleness-only issue list despite an injected, unclassified regression —
the exact 2S.3 defect, reproduced independently, not via the fixed 2S.4
tests. Running the identical reconstruction against current HEAD instead
returns the `attributable_failures` mismatch issue.

**Root-cause re-derivation**: full early-return audit of
`validate_structured_fast_green()` at current HEAD identifies two
`if issues: return issues` checkpoints that strictly precede the
relocated freshness check — proving structurally (not only against the
2S.3 fixture) that a returned issue list of "staleness only" now requires
every non-freshness structured-evidence check to have already run to
completion and passed.

**Non-blocking finding (carried forward, not repaired)**: the FGSC-001
caller (`validate_derived_correctness()`, `phase_reports.py`) recognizes
carve-out eligibility via a `startswith` prefix match rather than exact
issue identity. A static source scan confirms exactly one issue-message
template currently shares that prefix, so it is not overbroad in
practice — but it is fragile against a future near-matching message.

**Test evidence**: a fresh, independently-constructed 13-test suite
(`tests/test_phase_149o_20l_7o_2s_5_fgsc_001_staleness_carveout_
independent_verification.py`) covers sole-staleness acceptance and ten
independent staleness-plus-one-other-defect rejection cases. 228 existing
directly-relevant tests (2S.1–2S.4, 2R, 2R.1, 88N.5 scalar,
finalization-transaction, push) re-run unmodified. 241 tests total, zero
regressions.

**Verdict**: 2S.3 Blocking finding **INDEPENDENTLY CONFIRMED CLOSED**.
FGSC-001 repair **INDEPENDENTLY VERIFIED**. Real S22.1/S22.2 self-hosting
acceptance may now proceed. Phase 149O.20L.7O.2P remains
quarantined/untouched — no reconciliation performed or authorized by this
phase.

Full text:
`docs/PHASE_149O_20L_7O_2S_5_FGSC_001_STALENESS_CARVEOUT_ATTRIBUTION_
COMPLETENESS_REPAIR_INDEPENDENT_VERIFICATION.md`.

Recommended next: a dedicated real FGSC S22 self-hosting acceptance phase
(S22.1 positive, S22.2 negative). Only after both pass should
149O.20L.7O.2P reconciliation be considered.
