# Task Contract
## Task ID
20260627-88y1-cli-subprocess-runtime-reduction
## Title
88Y.1 — CLI Subprocess Runtime Reduction
## Status
done
## Mode
implementation
## Goal
Reduce full-suite runtime by targeting subprocess-heavy CLI tests without weakening coverage. Convert repeated CLI subprocess calls to direct function-call tests where appropriate, use shared fixtures, and preserve CLI smoke coverage.
## Allowed Files
- tests/test_phase87_integration.py
- tests/test_scope_preflight.py
- tests/conftest.py if shared fixture justified
- docs/PHASE_88_CLI_SUBPROCESS_RUNTIME_REDUCTION.md
- PROJECT_STATUS.md, CHANGELOG.md, tasks/active/**, tasks/DONE.md
## Forbidden Files
- Production source behavior files (unless narrow testability helper justified), advisory expansion, shell/system config, Phase 88Z contract
## Acceptance Criteria
- Fast-green ≤30s, quick tier ≤3min, full suite runtime reduced or bottleneck documented
- No tests deleted/skipped/xfailed; assertions not weakened; production unchanged
- Documentation artifact created; all tiers green
