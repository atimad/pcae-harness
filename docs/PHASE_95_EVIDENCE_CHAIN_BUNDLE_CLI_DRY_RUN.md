# Phase 95P — Evidence Chain Bundle CLI Dry-Run
phase_name = phase_95p_bundle_cli | phase_status = completed
recommended_next_phase = 95Q — Bundle End-to-End Dry-Run Demo

## 1. Purpose
Exposed 95O bundle model through dry-run CLI. No execution.

## 2. CLI Commands
pcae backend invoke artifact-only bundle dry-run --bundle <path> [--save] [--json]
pcae backend invoke artifact-only bundle show --latest [--json]
pcae backend invoke artifact-only bundle verify --latest [--json]

## 3. Tests (9)
All pass. Execute unavailable.

## 4. Next: 95Q — Bundle End-to-End Dry-Run Demo
