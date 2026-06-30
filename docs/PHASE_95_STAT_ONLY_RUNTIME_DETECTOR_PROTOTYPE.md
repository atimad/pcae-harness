# Phase 95F — Stat-Only Runtime Detector Prototype
```
phase_name = phase_95f_stat_only_runtime_detector_prototype
phase_status = completed | implementation_status = completed
recommended_next_phase = 95G — Runtime Evidence Broker/Shell-Gate Integration
```

## 1. Purpose
ClaudeRuntimeDetectionConfig + detect_claude_runtime_evidence_stat_only() — stat-only detection using Python filesystem APIs only (Path.exists(), stat, read_bytes, hashlib). Hashes explicit configured command/wrapper files. Never executes, never uses which/subprocess/PATH/search/network. CLI detect-stat-only --config.

## 2. Files (8)
backend_invocations.py, backend.py, cli.py, tests, docs, PROJECT_STATUS, CHANGELOG, tasks/DONE

## 3. Tests (7): config, missing path, directory, bypass unknown, no-exec flags, no subprocess in code, CLI
563 model total.
