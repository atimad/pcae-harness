# Task Contract

## Task ID

20260627-88v1-secret-redaction-and-deny-mapping-repair

## Title

88V.1 — Secret Redaction and Deny Mapping Repair

## Status

active

## Mode

implementation

## Goal

Repair the four enforcement-readiness blockers identified in 88U and formalized in 88V:

1. GAP-1: VAR=val secret redaction gap
2. GAP-2: env|grep / printenv secret exposure gap
3. GAP-3: broker.requested_command raw secret retention gap
4. GAP-4: dormant deny hard-block mapping inconsistency

This is an enforcement-readiness repair phase. It must not implement enforcement, shell interception, shell wrappers, shell configuration modifications, classified command execution, backend invocation, prompt sending, output capture, intake/adoption, real execution authorization, hard block overrides, or persistent broker/shell-gate state/cache writes.

## Allowed Files

- src/pcae/core/shell_gate.py
- src/pcae/core/permission_broker.py
- src/pcae/commands/permission_broker.py (only if CLI JSON output redaction requires it)
- tests/test_broker_shell_gate_integration.py
- tests/test_broker_shell_gate_edge_cases.py
- tests/test_shell_gate_matrix.py
- tests/test_permission_broker.py (only if broker output/redaction tests fit there better)
- docs/PHASE_88_SECRET_REDACTION_AND_DENY_MAPPING_REPAIR.md
- PROJECT_STATUS.md
- CHANGELOG.md
- pyproject.toml (only if marker/test metadata requires it)
- tasks/active/**
- tasks/DONE.md

## Forbidden Files

- shell wrapper files
- shell config files
- .githooks/**
- backend invocation implementation files
- prompt/capture/intake/adoption implementation files
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- README.md (unless a tiny command reference is absolutely required)
- generated persistent broker/shell-gate storage/cache
- Phase 88W task contract
- any phase beyond 88V.1

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

- Must not implement enforcement
- Must not implement shell interception
- Must not install shell wrappers
- Must not modify shell configuration
- Must not execute classified command text
- Must not invoke backends
- Must not send prompts
- Must not capture outputs
- Must not perform intake/adoption
- Must not grant real execution authorization
- Must not override hard blocks
- Must not replace human review
- Must not write persistent broker/shell-gate state or cache
- Must not raw git commit
- Must not raw git push
- Must not force push

## Acceptance Criteria

- GAP-1 repaired: secret-like VAR=value command prefixes detected/redacted
- GAP-2 repaired: env/printenv secret exposure detected
- GAP-3 repaired: broker.requested_command does not leak raw secret-access commands
- GAP-4 repaired: deny maps to broker hard block or proven unreachable and documented
- Nested shell-gate evidence does not leak raw secret-access commands
- Serialized CLI JSON does not leak raw secret-access commands
- Unmapped shell-gate decisions fail closed
- Read-only non-secret commands not over-redacted unnecessarily
- No authority expansion, shell execution, shell interception, shell wrappers
- No backend invocation, prompts, capture, intake, adoption
- Authorization/performed flags remain false
- Existing broker, shell-gate, and integration tests pass
- Fast-green, quick tier, and full suite pass
- Documentation artifact exists
- PROJECT_STATUS.md and CHANGELOG.md updated

## Acceptance Checks

- python -m pytest tests/test_permission_broker.py -q
- python -m pytest tests -k "shell_gate" -q
- python -m pytest tests/test_broker_shell_gate_integration.py -q
- python -m pytest -m "fast_green" -n auto -ra --durations=50
- python -m pytest -m "not slow and not phase_closure" -n auto
- python -m pytest -n auto -ra --durations=150 (full suite)
- pcae health
- pcae check
- pcae doctor task-memory
- pcae doctor test-run --json
- pcae push check

## Documentation Requirements

- Create docs/PHASE_88_SECRET_REDACTION_AND_DENY_MAPPING_REPAIR.md
- Update PROJECT_STATUS.md
- Update CHANGELOG.md
- Update tasks/DONE.md

## Created Timestamp

2026-06-27T03:00:00.000000+02:00
