# Task Contract

## Task ID

20260627-88x-advisory-mode-prototype

## Title

88X — Advisory Mode Prototype

## Status

done

## Mode

implementation

## Goal

Implement the first advisory mode prototype that presents broker + shell gate decisions as non-authorizing advisory output. Add `pcae advisory check`, `pcae advisory explain`, and `pcae advisory status` commands. Advisory mode must never execute commands, block commands, intercept shell execution, install wrappers, invoke backends, or grant authorization.

## Allowed Files

- src/pcae/core/advisory.py
- src/pcae/commands/advisory.py
- src/pcae/cli.py
- tests/test_advisory_mode.py
- docs/PHASE_88_ADVISORY_MODE_PROTOTYPE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- pyproject.toml (only if required for test marker metadata)
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
- README.md (unless tiny command reference absolutely required)
- generated persistent advisory/broker/shell-gate storage/cache
- Phase 88Y task contract
- any phase beyond 88X

## Acceptance Criteria

- Advisory check command works (JSON + human-readable)
- Advisory explain command works (or deferral documented)
- Advisory status command works (or deferral documented)
- JSON envelope with all required fields
- Advisory decision mapping from broker decisions
- Secret redaction preserved (88V.1 rules)
- Hard blocks preserved
- No command execution, shell interception, shell wrappers
- No backend invocation, prompts, capture, intake, adoption
- No real authorization
- Authorization/performed flags false
- Existing tests pass (broker, shell gate, integration)
- New advisory tests pass
- Fast-green, quick tier, full suite green
- Documentation artifact created

## Acceptance Checks

- python -m pytest tests -k "advisory" -q
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

- Create docs/PHASE_88_ADVISORY_MODE_PROTOTYPE.md
- Update PROJECT_STATUS.md
- Update CHANGELOG.md
- Update tasks/DONE.md

## Created Timestamp

2026-06-27T05:00:00.000000+02:00
