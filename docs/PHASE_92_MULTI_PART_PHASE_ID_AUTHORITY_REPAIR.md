# Phase 92D.8.3 — Multi-Part Phase ID Authority Repair

## Root Cause

1. `_derive_phase_id()` regex `(\d+[A-Z](?:\.\d+)?)` truncated "92D.8.3" to "92D.8"
2. Consistency checker scanned all phase IDs in prose, treating "Recommended Next Phase: 93D" as a current-phase mismatch

## Fixes

- Phase ID extraction now uses canonical report title heading only
- `_derive_phase_id` regex uses `(?:\.\d+)*` for multi-part IDs
- Consistency checker ignores recommended next phase mentions
- Authoritative phase_id from metadata, validated against title heading

## Supported Forms

92D, 92D.1, 92D.8, 92D.8.1, 92D.8.2, 92D.8.3, 93D, 93D.1
