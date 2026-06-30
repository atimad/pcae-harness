# Phase 95M — Artifact-Only Invocation Dry-Run Evidence Chain Fixtures

```
phase_name = phase_95m_fixtures
phase_status = completed | implementation_status = completed
recommended_next_phase = 95N — Artifact-Only Invocation Dry-Run Evidence Chain Review
```

## 1. Purpose

Created deterministic evidence-chain fixtures for the artifact-only invocation dry-run CLI. One canonical valid chain plus 23 broken variants. Model and CLI tests validate each fixture. No execution.

## 2. Fixture Location

`tests/artifact_only_invocation_fixtures.py`

## 3. Valid Chain

- phase_id: 95M, backend: mock, adapter: mock
- All 5 artifacts with matching digests
- Broker/shell-gate: allow_dry_run
- All safety flags: True
- command_mode: dry_run

## 4. Broken Variants (23)

| Variant | Expected Hard-Block |
|---------|-------------------|
| missing_prompt | prompt_artifact_path_missing |
| tampered_prompt_digest | prompt_artifact_digest_missing |
| backend_mismatch | backend_id_missing |
| adapter_mismatch | adapter_id_missing |
| runtime_evidence_digest_mismatch | runtime_evidence_digest_missing |
| approval_ineffective | approval_artifact_path_missing |
| invocation_plan_tampered | invocation_plan_digest_missing |
| broker_deny | broker_decision:deny |
| broker_hard_block | broker_decision:hard_block |
| shell_gate_deny | shell_gate_decision:deny |
| shell_gate_hard_block | shell_gate_decision:hard_block |
| missing_quarantine | output_quarantine_path_missing |
| missing_audit | audit_path_missing |
| missing_timeout | timeout_missing_or_invalid |
| execute_reserved | execute_reserved_not_supported |
| execute_requested | execute_requested=True |
| no_subprocess_false | no_subprocess=False |
| no_network_false | no_network=False |
| no_repo_mutation_false | no_repo_mutation=False |
| no_apply_false | no_apply=False |
| no_patch_parsing_false | no_patch_parsing=False |
| no_commit_push_false | no_commit_push_authorization=False |
| no_telegram_inbound_false | no_telegram_inbound=False |

## 5. Tests (29)

| Class | Tests | Location |
|-------|-------|----------|
| Test95MFixtureValidChain | 6 | test_backend_invocations.py |
| Test95MFixtureBrokenVariants | 7 | test_backend_invocations.py |
| Test95MFixtureSafety | 4 | test_backend_invocations.py |
| Test95MFixtureCLI | 11 | test_backend_cli.py |
| (existing 95L CLI tests) | 1 fix | test_backend_invocations.py |

## 6. No-Go

No real backend invocation. No adapter execution. No subprocess. No network. No execute. 95N not started.

## 7. Next

**95N — Artifact-Only Invocation Dry-Run Evidence Chain Review**
