# Phase 149O.20L.7O.2W Complete — Generic Producer Intake Helper and Session Provenance Integration

**Verdict: completed — GENERIC PRODUCER INTAKE HELPER IMPLEMENTED.**
0 blocking findings. Post-`v0.3.0` development; the published `v0.3.0`
tag/release/package version are untouched.

Consolidated the duplicated Claude-labelled reference-adapter logic in
`scripts/claude_code_intake_adapter.py` into a shared, producer-neutral
helper in `src/pcae/core/intake.py` (`build_intake_candidate_from_files`,
`derive_producer_provenance`) and a new `pcae intake from-files` CLI
command. Producer provenance (`producer.kind`) is derived from the
active PCAE governance agent lock (`.pcae/agent-lock.json`, read via
`agent_core.read_agent_lock`) when one exists, falling back to a
required explicit `--producer` when it does not — preserving v0.3's
external/unbootstrapped compatibility path. Mapped, without unifying,
the three distinct agent-identity vocabularies (capability registry /
governance agent lock / backend session lock), confirming the
`codex-local` vs `codex` mismatch named in the handoff is real.

Proved Codex and an arbitrary custom agent identity work through the
identical generic helper with no dedicated adapter, and that producer
identity never influences `execution_allowed`, `promotion_executed`,
task-scope, or repo/base/hash validation — including when the
`producer` object itself carries injected authority-looking keys.
Proved the governance lock's own `active_task`/`git_branch` snapshot
fields are never substituted for canonical task-scope or base-commit
authority. Reduced `scripts/claude_code_intake_adapter.py` to a thin
subprocess wrapper around `pcae intake from-files` with zero
intake-contract logic of its own.

24 new focused tests
(`tests/test_phase_149o_20l_7o_2w_producer_provenance_integration.py`);
3 updated 2U.2 tests and 3 updated 2U.3 tests (retired script internals
moved to the shared helper's call surface; one grep allowlist extended
for the new, reviewed `git rev-parse` call).

Targeted regression (`test_agent.py`, `test_session.py`,
2U.1-2U.3, 2W): 4549 passed, 2 failed. Both failures confirmed
non-attributable via `git stash -u` A/B against clean `HEAD`
(`f25922f1`): `test_no_intake_cli_command_implemented_yet` fails
identically on clean `HEAD` (pre-existing since Phase 2U.2);
`test_no_production_code_modified_this_phase` passes on clean `HEAD`
and only fails while this phase's own changes were uncommitted (resolves
automatically once committed). Deselected clean re-run: **4549 passed,
0 failed.**

Full text:
`docs/PHASE_149O_20L_7O_2W_GENERIC_PRODUCER_INTAKE_HELPER_AND_SESSION_PROVENANCE_INTEGRATION.md`.

Recommended next phase: 149O.20L.7O.2W.1 — Generic Producer Intake
Helper and Session Provenance Integration Independent Verification.
