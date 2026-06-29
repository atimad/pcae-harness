# Phase 94T.1 — Phase Completion Metadata Freshness Guard

```
phase_name    = phase_94t1_phase_completion_metadata_freshness_guard
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 94U — Real Backend Adapter Preflight Artifacts
```

## 1. Purpose

Fix a recurring bug where `pcae phase complete` silently reuses stale data from `.pcae/phase-completion-metadata.json` written during a previous phase, producing Telegram reports with contradictory governance, test, and next-phase data.

## 2. Root Cause

`_finalize_report_and_notify()` in `phase.py` reads `.pcae/phase-completion-metadata.json` via `_load_completion_metadata()` with no validation. If the file contains `phase_id: "94Q"` from a prior phase, all governance results, test results, and recommended_next_phase are loaded verbatim — even when the completing phase is 94T. The `phase_id` field in metadata was never compared against the actual completing phase.

## 3. Freshness Guard

### Phase ID Validation (phase.py)

After loading metadata, `phase_id` is compared:

```python
meta_phase_id = meta.get("phase_id", "")
if meta_phase_id and meta_phase_id != phase_id:
    print(f"Warning: metadata phase_id mismatch; discarding stale metadata.")
    meta = {}
```

If metadata's `phase_id` differs from the completing phase, all metadata is discarded and git-derived values are used instead.

### Backward Next-Phase Detection (phase.py)

If `recommended_next_phase` points to a phase equal to or before the current phase, the field is cleared from metadata.

### Summary-to-Structured Next-Phase Check (phase_reports.py)

`_check_canonical_metadata_consistency()` now compares the next phase extracted from the summary text with the structured `recommended_next_phase`. Mismatch → trust warning + partial downgrade.

### Self-Referential Next-Phase Check (phase_reports.py)

If `recommended_next_phase` points to the same phase_id as the current report, it's flagged as a mismatch.

## 4. Files Changed

- `src/pcae/commands/phase.py` — metadata freshness guard in `_finalize_report_and_notify()`
- `src/pcae/core/phase_reports.py` — summary-to-structured next-phase check, backward next-phase check
- `tests/test_phase_reports.py` — 10 tests (2 classes)
- `docs/PHASE_94T1_PHASE_COMPLETION_METADATA_FRESHNESS_GUARD.md` — this doc

## 5. Test Coverage (10 tests)

- `Test94T1MetadataFreshness` (5): complete with fresh metadata, stale phase_id downgrade, backward next phase, summary/structured mismatch, no secrets
- `Test94T1ConsistencyValidation` (5): missing governance, missing tests, missing commits, missing next (not fatal), no Telegram inbound

## 6. No-Go Confirmations

No real backend invocation, adapter execution, subprocess, network, shell interception, Telegram inbound, enforcement, or apply execution.

---
*Phase 94T.1 is a corrective reporting substrate fix. No backend behavior was changed.*
