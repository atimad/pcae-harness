# Task Contract

## Task ID

20260704-1349-phase-113x-2-canonical-phase-identity-source-repair

## Title

Phase 113X.2: Canonical Phase Identity Source Repair

## Status

done

## Mode

implementation

## Goal

Close the one remaining 113X forensic divergence gap: in pcae phase complete, a mismatch between the CLI/summary-derived phase_id and the metadata file's declared phase_id was silently resolved (metadata discarded, warning printed, finalization proceeded on git-derived fallback data) without ever becoming a gate blocker. Add a single canonical identity-resolution helper and feed a genuine conflict into validate_finalization_gate() as a hard blocker, reusing the existing 113X.1 quarantine enforcement rather than duplicating it.

## Allowed Files

- src/pcae/core/phase_reports.py
- src/pcae/commands/phase.py
- tests/test_canonical_phase_identity_repair.py
- docs/PHASE_113X2_CANONICAL_PHASE_IDENTITY_SOURCE_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/**

## Forbidden Files

- TBD


## Allowed Zones

- TBD

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

TBD

## Forbidden Changes

- TBD

## Acceptance Criteria

- Matching CLI/metadata phase identities finalize normally (unchanged behavior)
- Mismatched CLI/metadata phase identity fails closed (gate blocker, non-zero exit)
- Mismatched identity never overwrites latest.md/latest.json
- Mismatched identity evidence (both conflicting IDs) is preserved in the quarantined artifact
- 113X.1 blocked-finalization behavior (files_changed=0 etc.) remains intact
- No execution capability, Advisory Runtime, Runtime Snapshot, Telegram inbound, REST/web UI/plugin changes

## Acceptance Checks

- python -m pytest tests/test_canonical_phase_identity_repair.py -n auto -q
- python -m pytest tests/test_finalization_gate_enforcement.py tests/test_phase_reports.py tests/test_phase_identity.py -n auto -q
- pcae check

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-07-04T13:49:26.867903+02:00
