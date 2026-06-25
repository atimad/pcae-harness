# PCAE Testing Strategy

## Problem

The full test suite (7,407 tests) takes 15–18 minutes with `python -m pytest -n auto`.
This is appropriate for phase closure validation but too slow for normal development
feedback loops.

## Test Tier Model

| Tier | Command | Tests | Purpose |
|------|---------|-------|---------|
| **quick** | `python -m pytest -m "not slow and not phase_closure" -n auto` | ~7,000 | Fast development feedback |
| **governance** | `python -m pytest -m "integration or slow" -n auto` | ~400 | CLI integration and governance validation |
| **full** | `python -m pytest -n auto` | all | Phase closure, pre-push, final validation |

## When to Run Each Tier

### Quick (during development)

Run after making code changes to verify unit-level correctness. Excludes
subprocess-heavy CLI integration tests and phase-closure validation.
Expected time: 2–4 minutes.

```
python -m pytest -m "not slow and not phase_closure" -n auto
```

### Governance (before committing)

Run when changes affect CLI commands, gate evaluation, preflight behavior,
or governance integration. Includes all subprocess-based CLI tests.
Expected time: 8–12 minutes.

```
python -m pytest -m "integration or slow" -n auto
```

### Full (before phase closure and push)

Run before `pcae push`, phase completion commits, and major phase boundaries.
This is the authoritative validation suite. All tests must pass.
Expected time: 15–18 minutes.

```
python -m pytest -n auto
```

## Markers

| Marker | Meaning |
|--------|---------|
| `slow` | Test spawns subprocesses or takes >1s each |
| `integration` | Test spawns pcae CLI subprocesses |
| `phase_closure` | Heavyweight phase-closure validation test |

Markers are registered in `pyproject.toml` under `[tool.pytest.ini_options]`.

## Bottleneck Analysis

The primary bottleneck is subprocess-heavy CLI integration tests. Each test in
files like `test_scope_preflight.py`, `test_gate_dry_run.py`, and
`test_phase85_integration.py` spawns a full `python -m pcae` subprocess.
Each subprocess takes 0.3–10s depending on the command complexity (gate-dry-run
evaluates 15 gates with full intelligence layer = ~10s per call).

### Marked files

| File | Tests | Markers |
|------|-------|---------|
| `test_scope_preflight.py` | 66 | slow, integration |
| `test_scope_preflight_review.py` | 63 | slow, integration |
| `test_scope_gate.py` | 22 | slow, integration |
| `test_gate_dry_run.py` | 29 | slow, integration |
| `test_backend_gate.py` | 23 | slow, integration |
| `test_adoption_mutation_gate.py` | 27 | slow, integration |
| `test_commit_push_gate.py` | 26 | slow, integration |
| `test_push.py` | 34 | slow, integration |
| `test_staged_file_aware_push.py` | 12 | slow, integration |
| `test_staged_file_aware_commit.py` | 8 | slow, integration |
| `test_staged_file_aware_task_finish.py` | 9 | slow, integration |
| `test_phase85_integration.py` | 38 | slow, integration, phase_closure |
| `test_phase87_integration.py` | 29 | slow, integration, phase_closure |
| `test_lifecycle_regression.py` | 23 | slow, integration, phase_closure |

## Future Optimization Candidates

1. **Direct function calls**: Replace subprocess CLI calls with direct
   `build_scope_preflight()` / `build_gate_dry_run()` calls in unit tests.
   Keep subprocess tests as a smaller integration verification set.
2. **Fixture caching**: Cache expensive project-state/risk-register builds
   across tests that share the same repo state.
3. **Selective xdist**: Use `-n auto` only for the quick tier; run slow
   integration tests sequentially (they may contend on git state).
4. **Test file splitting**: Split the 4,236-test `test_agent.py` into
   per-phase test files for faster selective runs.

## Full Suite Remains Required

The full suite (`python -m pytest -n auto`) is the final authority for
phase closure and governed push. Quick and governance tiers are development
conveniences — they do not replace full validation.
