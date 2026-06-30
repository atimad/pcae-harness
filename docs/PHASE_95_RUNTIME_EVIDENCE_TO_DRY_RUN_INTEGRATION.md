# Phase 95E — Runtime Evidence to Dry-Run Integration
```
phase_name = phase_95e_runtime_evidence_to_dry_run_integration
phase_status = completed | implementation_status = completed
recommended_next_phase = 95F — Stat-Only Runtime Detector Prototype
```

## 1. Purpose
Extended ArtifactOnlyRealInvocationDryRunAssessment with 10 runtime evidence binding fields. evaluate() now requires runtime evidence for real adapter plans. Cross-binding checks: backend/adapter mismatch, timeout/audit/quarantine path mismatch. CLI --runtime-evidence flag. 6 tests (556 model total).

## 2. Files
backend_invocations.py, backend.py, cli.py, tests, docs, PROJECT_STATUS, CHANGELOG, tasks/DONE
