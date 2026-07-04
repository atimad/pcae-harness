# Phase 113X.2 — Canonical Phase Identity Source Repair

## Purpose

Governance repair phase, closing the one remaining finding from the
Phase 113X (Cross-Agent Governance Verification) forensic audit that
113X.1 did not address: 113X.1 repaired finalization gate *enforcement*
(a blocked report could still overwrite `latest.md`/`latest.json`).
This phase repairs identity *resolution* — a specific divergence
between two phase-identity sources feeding `pcae phase complete` that
was resolved silently, before it ever reached the gate.

No Advisory Runtime changes. No execution capability. No Runtime
Snapshot behavior changes. No Telegram inbound, REST, web UI, or
plugin changes. Governance/report-identity repair only.

## Root Cause

`pcae phase complete`'s finalization path (`_finalize_report_and_notify()`,
`src/pcae/commands/phase.py`) combines two independent phase-identity
sources: the CLI/summary-derived `phase_id` (`_derive_phase_id()`, a
regex over free-text `--summary`) and `.pcae/phase-completion-
metadata.json`'s own declared `phase_id`. Before this repair (Phase
94T.1's "metadata freshness guard"), a mismatch between the two was
handled by discarding the metadata, printing a console-only warning,
and proceeding to finalize using git-derived fallback data for every
other field — without the mismatch itself ever becoming a
`validate_finalization_gate()` blocker. If the git-derived fallbacks
happened to satisfy the gate's other checks, the finalization could
succeed silently despite the two identity sources having disagreed.
This is 113X audit Finding 3, not closed by 113X.1 (which repaired gate
*enforcement*, not this specific resolution gap).

Every other identity-divergence point named in the 113X.2 brief was
found, during inspection, to already converge on a single value by
construction, or to already feed the existing gate:

| Divergence point | Status before this phase |
|---|---|
| CLI-provided phase ID vs metadata phase ID | **Not enforced** — silently discarded (this repair) |
| Report body phase ID | Single field (`report.phase_id`), set once from whichever value the resolution above produces — no separate source |
| Canonical latest artifact identity | Derived from `report.phase_id` (`write_phase_report`) — consistent by construction |
| Quarantine artifact identity | Derived from `report.phase_id` (`write_quarantined_report`, 113X.1) — consistent by construction |
| Notification/report status identity | `phase_report_to_notification_event()` reads `report.phase_id` only — consistent by construction |
| Canonical report file vs current report | Already checked by `_check_canonical_metadata_consistency()`, which downgrades `report_completeness` to `partial` on mismatch — already a `validate_finalization_gate()` blocker via the existing "report completeness is not complete" check |
| `pcae task finish --commit`'s metadata | Single source only (no competing CLI-derived value) — no divergence possible there structurally |

## Scope

- `src/pcae/core/phase_reports.py` — new `resolve_finalization_phase_identity()`
  helper; `validate_finalization_gate()` gains an optional
  `identity_conflict:` parameter
- `src/pcae/commands/phase.py` — `_finalize_report_and_notify()` calls
  the resolver instead of the old ad-hoc freshness-guard comparison,
  and threads a genuine conflict into the gate
- `tests/test_canonical_phase_identity_repair.py` — 16 new tests
- `docs/PHASE_113X2_CANONICAL_PHASE_IDENTITY_SOURCE_REPAIR.md` — this document

## Implementation Summary

### 1. `resolve_finalization_phase_identity(derived_phase_id, metadata)`

Single canonical resolution point for the CLI/summary-derived and
metadata-declared phase_id. Returns `(metadata_phase_id, conflict)`:

- Both present and equal, or only one present → no conflict; the
  present value is returned.
- The CLI/summary side has no real phase reference (`""`/`"unknown"`)
  → the metadata's value is used (there's nothing for it to disagree
  with).
- Both present and disagreeing → `conflict` names both values;
  `metadata_phase_id` is returned empty (a conflicting metadata
  `phase_id` is never trusted for the finalization it disagrees with —
  callers fall back to git-derived data for every other field too,
  exactly as before this repair).

### 2. `validate_finalization_gate(..., identity_conflict=...)`

A non-`None` `identity_conflict` is appended to `blockers` as
`"phase identity: {conflict}"`, alongside `validate_phase_identity()`'s
own findings — the same single blockers list 113X.1's quarantine
enforcement already consumes. No new enforcement mechanism was
introduced; the existing one now receives the evidence it was missing.

### 3. `commands/phase.py` integration

Replaces the old "discard on mismatch, print warning, continue" logic
with a call to the resolver; a conflict is printed and metadata is
still discarded (its other fields remain untrustworthy), but the
conflict string is now passed to `validate_finalization_gate(identity_
conflict=...)`, making it a real blocker → 113X.1's quarantine path
writes the report to `.pcae/phase-reports/quarantine/`, with the
blocker text (naming both conflicting IDs) embedded in the quarantined
JSON's `finalization_blockers`, and `latest.md`/`latest.json` are never
touched.

## Design Decisions

1. **One new helper, not a rearchitecture.** `validate_finalization_gate()`
   already is the single canonical enforcement point for phase-identity
   consistency (113B.2, 113X.1). This phase closes the one path that
   bypassed it, rather than introducing a competing "canonical identity"
   abstraction.
2. **A conflicting metadata `phase_id` is still fully distrusted**, not
   partially merged — the resolver returns an empty metadata phase_id
   on conflict, so downstream code keeps falling back to git-derived
   data for every field (unchanged from the prior discard behavior),
   while the conflict itself is now enforced rather than silently
   logged.
3. **An absent or `"unknown"` CLI/summary phase_id is not a conflict.**
   There is nothing for the metadata's declared phase_id to disagree
   with in that case; treating it as a conflict would regress every
   caller whose summary text doesn't happen to embed a `"Phase X"`
   substring.
4. **`pcae task finish --commit` is untouched** — its phase_id comes
   from a single source (metadata only), so this divergence class does
   not apply there.

## Safety Invariants

- No Advisory Runtime changes
- No execution capability introduced or changed
- No Runtime Snapshot behavior changes
- No Telegram inbound, REST, web UI, or plugin changes
- Runtime state remains Observed
- Maximum plugin capability remains `observe`
- Execution availability remains unavailable

## Known Pre-Existing, Out-of-Scope Issues Found During Validation

Three pre-existing test failures were found during the full `python -m
pytest` run, none caused by this phase's changes (each independently
reconfirmed via `git stash -u` against the clean pre-113X.2 baseline):

- `tests/test_rc_audit_findings_repair.py::TestAsymmetryReproduction::test_both_paths_agree_on_complete_report`
  — already documented in Phase 113X.1's own docs; `validate_phase_identity()`
  reads the real `PROJECT_STATUS.md` from the working directory rather
  than an isolated fixture.
- `tests/test_bootstrap_todo_consistency.py::test_recommended_next_phase_matches_real_project_status`
  and `::test_real_todo_not_flagged_stale_against_real_project_status`
  — both hardcode an expectation that PROJECT_STATUS.md's real,
  current recommended next phase is `"112C"` and that `tasks/TODO.md`'s
  stale "🔜 Next" marker is not flagged stale; PROJECT_STATUS.md has
  advanced far past 112C for many phases (112D onward). This is the
  same "stale TODO.md" condition PCAE's own bootstrap output already
  reports as informational-only.

All three are the same class of pre-existing fragility: a test that
hardcodes an assumption about the literal, ever-advancing content of
`PROJECT_STATUS.md`/`tasks/TODO.md` rather than using an isolated
fixture. None fall within 113X.2's scope (CLI/metadata/report/
quarantine phase-identity divergence in the finalization write path).

## Test Coverage

16 tests in `tests/test_canonical_phase_identity_repair.py`:

| Group | Tests | Focus |
|---|---|---|
| A — `resolve_finalization_phase_identity()` unit-level | 6 | Matching/mismatching/absent/unknown-derived cases |
| B — matching identities finalize normally | 1 | No regression for the common case |
| C — mismatched identity fails closed | 2 | Non-zero exit, blocker text, console warning |
| D — mismatch never overwrites latest | 2 | Prior valid `latest.json` untouched, no fresh `latest.*` created |
| E — mismatch preserved in quarantine | 1 | Both conflicting IDs present in quarantined JSON, single canonical `phase_id` on the artifact |
| F — status reflects canonical identity | 2 | Blocked artifact has one unambiguous `phase_id`; valid artifact's metadata and body agree |
| G — 113X.1 behavior intact | 2 | `files_changed=0` still quarantines; `--allow-partial-report` still bypasses (unchanged) |

## Validation

- `python -m pytest tests/test_canonical_phase_identity_repair.py -n auto -q`
- `python -m pytest tests/test_finalization_gate_enforcement.py tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_phase_identity.py tests/test_phase_report_trust_hard_fail.py tests/test_phase_report_trust_gate_cli.py tests/test_rc_audit_findings_repair.py tests/test_task_finish_report_trust_notification.py tests/test_task_finish_notification_ordering.py -n auto -q`
- `python -m pytest -n auto -q` (full suite)
- `python -m pytest -m fast_green -n auto -q`
- `pcae health && pcae check && pcae doctor task-memory && pcae push check`

## Recommended Next Phase

No new phase is proposed by this repair. The 113X forensic-audit
findings scoped for governance repair (Finding 1 in 113X.1, Finding 3
in 113X.2) are both closed. Return to normal PCAE roadmap development
(113D — Advisory Runtime Verification & Compatibility), or open a
dedicated phase for the three pre-existing test fragilities documented
above if their recurring noise in `python -m pytest` becomes a
priority.
