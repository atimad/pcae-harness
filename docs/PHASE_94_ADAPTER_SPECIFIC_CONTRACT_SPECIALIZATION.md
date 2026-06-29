# Phase 94V — Adapter-Specific Contract Specialization

```
phase_name    = phase_94v_adapter_specific_contract_specialization
phase_version = 1.0
phase_status  = completed
implementation_status = completed
recommended_next_phase = 94W — Real Adapter Preflight Hardening
```

## 1. Purpose

Specialize backend adapter contracts with explicit factory functions, backend-specific safety profiles, required env key declarations, no-go condition lists, and failure classification mappings.

## 2. Factory Functions

- `create_mock_adapter_contract()` — mock_only, no secrets, no approval
- `create_claude_cli_adapter_contract()` — preflight_only, bypass detection, ANTHROPIC_API_KEY
- `create_claude_deepseek_cli_adapter_contract()` — preflight_only, bypass detection, DEEPSEEK_API_KEY
- `create_codex_adapter_contract()` — preflight_only, OPENAI_API_KEY
- `create_qwen_adapter_contract()` — preflight_only, QWEN_API_KEY
- `create_custom_adapter_contract()` — disabled by default

## 3. No-Go Conditions

`get_adapter_no_go_conditions()` returns backend-specific lists. Mock excludes env/bypass/real-unsafe. Real adapters include all 12 conditions.

## 4. Failure Mapping

`get_adapter_failure_mapping()` returns standard 12-category mapping.

## 5. Files Changed

- `src/pcae/core/backend_invocations.py` — 6 factories, no-go builder, failure mapper, updated registry
- `tests/test_backend_invocations.py` — 19 tests (5 classes)

## 6. Test Coverage (19 tests)

- Test94VSpecializedContracts (9): mock, claude, deepseek, codex, qwen, custom, all non-executable, all audit, all timeout
- Test94VNoGoConditions (3): mock excludes env/bypass, claude includes both, common set
- Test94VFailureMapping (2): all categories, readable keys
- Test94VRegistry (2): uses factories, all preflight/mock
- Test94VNoExecution (3): no subprocess, no secrets, multi-part IDs

---
*Phase 94V implements adapter specialization only. No real backend invocation.*
