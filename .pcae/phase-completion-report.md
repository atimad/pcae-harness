# Phase 149O.20L.7O.2S.6 Complete — FGSC-001 Real Self-Hosting Acceptance (S22.1 Positive + S22.2 Negative)

Executed FGSC-001's real self-hosting acceptance requirements against the
actual, unmodified `src/pcae/core/fast_green_attribution.py` and
`src/pcae/core/phase_reports.py` implementation, in two isolated local
disposable git clones (origin removed — no network, no shared state with
this repository).

**S22.1 (positive)**: real non-degenerate baseline/candidate structured
evidence (`pcae phase fast-green-attribution`, real full
`pytest -m fast_green` run) — verdict PASS, 0 issues, 355 real
pre-existing failures excluded, 0 attributable. An authorized Class-B
post-checkpoint finalization delta (real governed task lifecycle,
`PROJECT_STATUS.md` edit) advanced HEAD past the checkpoint. The real
`check_finalization_delta()` and `run_stage_b_focused_checks()` (backed
by the real `pcae check`) both returned 0 issues. No scalar+deselection
fallback was used as completion authority.

**S22.2 (negative)**: a second, independently valid checkpoint, then one
deliberate forbidden post-checkpoint change to a `tests/**` path (Class A
per contract §4). The real `check_finalization_delta()` rejected it —
fail-closed, at the diff-authority path-classification boundary, before
Stage B or any trust gate — with no manual override applied or needed.

Two test-harness-only setup bugs (not production defects) were found and
fixed during this phase: the baseline-commit-subject regex stops parsing
at the first hyphen, and Stage B requires real `pcae` task governance
(not just a commit) to pass `pcae check`. Both are documented in the
phase doc.

**Regression evidence**: the four existing FGSC-001 test files (2S.2–
2S.5) re-run unmodified in this repository — 67 passed, 0 failed.

No production code (`src/pcae/**`) was modified this phase. No Blocking
defect was found. Phase 149O.20L.7O.2P remains quarantined/untouched — no
reconciliation performed or authorized by this phase.

**Verdict**: **FGSC-001 v1.0 — REAL STRUCTURED FAST GREEN SELF-HOSTING —
OPERATIONALLY CERTIFIED.** S22.1 PASS. S22.2 PASS.

Full text:
`docs/PHASE_149O_20L_7O_2S_6_FGSC_001_REAL_SELF_HOSTING_ACCEPTANCE.md`.

Recommended next: 149O.20L.7O.2T — Phase 149O.20L.7O.2P Attribution-Aware
Reconciliation and Canonical Promotion Assessment. Must first determine
whether historical 2P evidence can legitimately be re-evaluated under the
now-certified structured model before any promotion is considered — not
an automatic promotion of 2P.
