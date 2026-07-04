# Phase 113B.2 — Phase Identity & Lifecycle Hardening

## Purpose

Corrective governance hardening phase. During an attempted implementation of
Phase 113C, the agent incorrectly believed it was still completing Phase
113B. This resulted in incorrect phase identity, incorrect phase report
title, incorrect architecture status, and implementation work beginning
under the wrong lifecycle context.

This phase strengthens PCAE so that future agents cannot silently drift
into the wrong phase. No Advisory Runtime changes. No execution.
Governance hardening only.

## Scope

- `src/pcae/core/phase_reports.py` — `validate_phase_identity()` function
  and integration into `validate_finalization_gate()`
- `src/pcae/core/context.py` — `_detect_phase_ambiguity()` function and
  bootstrap prompt improvements
- `tests/test_phase_identity.py` — 17 validation tests
- `docs/PHASE_113B2_PHASE_IDENTITY_HARDENING.md` — this document

## Implementation Summary

### 1. Phase Identity Validation (`validate_phase_identity`)

Added to `src/pcae/core/phase_reports.py`. Cross-references:

| Check | Source | Block on mismatch |
|---|---|---|
| Summary text describes correct phase | `report.summary` regex | Yes (hard blocker) |
| Commit messages reference correct phase | `report.commits` regex | Yes (hard blocker) |
| Sub-phase may reference parent (113B.2 → 113B) | Phase ID comparison | No (allowed) |
| Architecture Status internal consistency | `report.architecture_status` | Yes |
| Metadata execution state vs Architecture Status | `md.execution_integration_status` vs `architecture_status` | Yes |

Integrated into `validate_finalization_gate()` as hard blockers —
phase identity mismatches are never advisory.

### 2. Bootstrap Phase Ambiguity Detection

Added `_detect_phase_ambiguity()` to `src/pcae/core/context.py`:

- Compares active task phase against PROJECT_STATUS.md current phase
- Detects when PROJECT_STATUS.md current phase is marked as completed
  (no phase in progress)
- Results flow into `roadmap_summary.phase_ambiguity`
- Displayed prominently in `build_bootstrap_prompt()` with a ⚠️ banner
- Fail-closed: bootstrap says "Halt and resolve each mismatch"

### 3. Bootstrap Prompt Improvements

- `Current phase (from PROJECT_STATUS.md)` line always shown
- Phase ambiguity section with explicit mismatch details
- Clear instruction: "Do NOT infer which is correct — verify explicitly"

## Design Decisions

1. **Fail-closed** — identity mismatches are hard blockers in
   `validate_finalization_gate()`, not trust warnings
2. **Sub-phase tolerance** — sub-phases (113B.2) are legitimate
   corrective phases that may not match the current PROJECT_STATUS.md
   phase; they are NOT flagged as mismatches
3. **Parent-phase commits** — a sub-phase (113B.2) may reference its
   parent phase (113B) in commit messages without triggering identity
   errors
4. **No new module** — all changes live in existing infrastructure
   (`phase_reports.py`, `context.py`)
5. **Backward compatible** — existing trust checks continue unchanged

## Safety Invariants

- No Advisory Runtime changes
- No execution capability
- No authorization
- Runtime state remains Observed
- Maximum plugin capability remains observe
- Execution availability remains unavailable

## Test Coverage

17 tests in `tests/test_phase_identity.py`:

| Section | Tests | Focus |
|---|---|---|
| 1 — validate_phase_identity basics | 8 | Valid reports, wrong summary, wrong commits, parent-phase tolerance, sub-phase tolerance, empty inputs |
| 2 — Architecture Status consistency | 2 | Impossible combinations, runtime state mismatch |
| 3 — Finalization gate integration | 1 | Phase identity blocks finalization |
| 4 — Bootstrap ambiguity | 3 | Import, no-task state, dict return |
| 5 — Fail-closed behavior | 2 | Blockers vs warnings, valid reports not blocked |
| 6 — Recommendation chain | 1 | Self-referencing recommendation blocked |

## Recommended Next Phase

**113C — Advisory Runtime Prototype (Observation-Only)**

113C must remain completely untouched by this corrective phase.
