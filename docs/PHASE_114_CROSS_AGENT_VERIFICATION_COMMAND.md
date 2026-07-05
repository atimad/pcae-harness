# Phase 114D — Cross-Agent Verification Command

## Status

Completed.

## Purpose

`pcae agent verify-handoff` is a model-agnostic, read-only command that
answers one question: **is it safe for another model, agent, automation,
or human to continue in this repository right now?** A model may propose
changes, but PCAE must be able to verify repository state before another
model or human continues from it -- this command is that verification
point.

This is containment infrastructure, not execution infrastructure. It does
not implement execution, authorization, Permission Broker enforcement,
Telegram inbound, REST, Web UI, Dashboard, or plugins. It reads existing
state and existing read-only helpers (114C's push-state reconciler among
them) and reports a verdict.

## Command

```
pcae agent verify-handoff [--json]
```

The command is strictly read-only: it does not modify files, does not
commit, does not push, does not send a notification, and does not run any
finalization logic. `verify_handoff(root)` in
`src/pcae/core/handoff_verification.py` is the reusable core function;
`run_agent_verify_handoff(...)` in `src/pcae/commands/agent.py` is the
thin CLI wrapper.

## Checks Performed

Twenty-three checks across seven categories:

**Git state** — working tree clean/dirty, current branch, whether
`origin/main` is resolvable, `origin/main..HEAD` count, `HEAD..origin/main`
count, live pushed status.

**Task state** — active task presence (idle is a valid, passing state),
`tasks/DONE.md` presence, `tasks/TODO.md` presence, task-memory doctor
state (via `diagnose_task_memory(...)`).

**Phase/report state** — canonical report (`latest.json`) exists and
parses, declared metadata `phase_id` agrees with the canonical report,
report trust/completeness, `latest.md`/`latest.json` agreement (the
markdown references the same `phase_id` the JSON declares), and whether
at least one of the report's recorded commits appears in recent git
history.

**Push-state reconciliation** — reuses `reconcile_push_state(...)` (Phase
114C) directly; flags a warning whenever declared metadata disagrees with
live git state, always naming both values.

**Notification state** — Telegram configured/enabled (read-only, via
`TelegramSink()`, never sending), and whether the latest completed phase
has a dispatch marker (`phase_already_notified(...)`).

**Architecture status** — `architecture_status` present on the canonical
report, `completed_phase_ids` structured evidence present, and a simple
check that the planned next phase doesn't already appear in
`completed_phase_ids` (an obvious duplicate/overclaim).

**Runtime invariants** — `EXECUTION_AVAILABILITY == "unavailable"`,
`CURRENT_RUNTIME_STATE == "Observed"`,
`CURRENT_MAXIMUM_PLUGIN_CAPABILITY == "observe"`, read directly from
`pcae.core.runtime_context` -- the same constants every other phase in
this arc has verified unchanged.

## Pass / Warning / Fail Semantics

Each individual check reports `pass`, `warning`, or `fail`. The overall
result is the worst severity among all checks (`fail` > `warning` >
`pass`). A missing notification marker is deliberately a `warning`, never
a `fail` -- dispatch is opt-in and push-state gated (Phase 114B), so its
absence is not itself unsafe, only visibility-reducing. A dirty working
tree, an unresolved phase-identity mismatch, a missing canonical report,
or execution becoming available are all `fail` -- each represents a state
where continuing could silently build on the wrong foundation.

## JSON Schema

```json
{
  "status": "pass | warning | fail",
  "checks": [
    {"name": "git_working_tree", "status": "pass", "detail": "working tree is clean"}
  ],
  "warnings": ["..."],
  "failures": ["..."],
  "recommended_next_action": "proceed | review warnings before proceeding | resolve failures before continuing",
  "latest_completed_phase": "Phase 114C — ... (completed).",
  "recommended_next_phase": "114D — Cross-Agent Verification Command",
  "pushed_status": "pushed | not_pushed | \"\"",
  "execution_availability": "unavailable"
}
```

`latest_completed_phase`/`recommended_next_phase` in the JSON carry the
full `PROJECT_STATUS.md` sentence (consistent with how every other
read-only context command in this codebase already surfaces them, e.g.
`build_context_pack(...)`'s `roadmap_summary`); the human-readable default
output extracts just the phase ID (e.g. `114C`) for a concise, one-line
summary.

## Exit Codes

- `0` — pass (safe to continue) or warning (visible warnings printed, not
  blocking)
- `1` — fail (unsafe to continue without resolving the listed failures)

Warnings do not use a distinct exit code: no existing PCAE command in
this codebase uses `2` for a "warning, not blocking" semantic, so
`verify-handoff` follows the brief's own documented fallback and keeps
warnings at exit `0` with the warnings printed and included in JSON
output.

## Model-Agnostic Design

`verify_handoff(root)` takes exactly one parameter -- a repository root --
and returns an identical result regardless of caller. No model identity,
agent identity, or backend identity field exists anywhere on
`HandoffCheck` or `HandoffVerificationResult`, mirroring the Repository
Transition Validator's own frozen constraint (113T Non-Goals; 113S
Section 9) and Repository Events' model-independence rule (114B.1). The
CLI wrapper (`run_agent_verify_handoff`) does not accept or forward any
agent identifier either -- the same command, invoked by any model or
human, sees the same repository and gets the same verdict.

## How This Supports Containment

Phase 113U/113Y/113Z's Repository Transition Validator prevents an
invalid transition from becoming canonical. Phase 114A ensures only
certified artifacts are promoted. Phase 114B/114C ensure notifications and
push-state checks reflect reality rather than stale declarations. None of
that infrastructure, however, gives an *incoming* agent or human a single
place to ask "is what I'm about to build on actually trustworthy?" without
re-deriving every one of those checks by hand. `pcae agent verify-handoff`
is that single place -- containment is only as good as the next agent's
ability to verify it held.

## Limitations

- Read-only by design: it reports state, it does not repair it (unlike
  `pcae doctor task-memory --fix` or `pcae governance repair`).
- The "report commits match git" check only looks at the last 100 git log
  entries -- a report referencing a much older commit could produce a
  false warning (never a failure) in a very long-lived branch.
- The "no obvious duplicate/overclaim" architecture check is a simple
  membership check, not a semantic diff -- it catches the most obvious
  case (`planned` already listed in `completed_phase_ids`), not every
  possible inconsistency.
- Push-state derivation depends on the process's current working
  directory (Phase 114C's own `compute_live_push_state()` contract,
  unchanged here) -- the CLI command always calls it with
  `HarnessPath.cwd()`, so this is not a practical limitation for real
  usage, but a direct caller passing a different root than the process
  cwd would get push-state results scoped to the process cwd, not the
  passed root.
- Does not itself call `pcae push check` as a subprocess (to stay
  dependency-light and fast); it derives the equivalent live push signal
  directly via the same 114C reconciler `pcae push check` itself doesn't
  currently consume end-to-end.

## Compatibility Boundaries

This phase does not modify:

- the Repository Transition Validator
- Notification Certification
- Canonical Artifact Promotion
- `push_state_reconciliation.py` (114C) -- only imported and reused
- `pcae push` / `pcae push check`
- notification sinks or dispatch
- Permission Broker
- execution runtime, authorization, plugins
- Telegram inbound, REST, Web UI, Dashboard

Execution capability remains unavailable. Runtime state remains Observed.
Maximum plugin capability remains `observe`.

## Validation

Validation completed:

- focused handoff verification tests: see final report
- phase/report/push-state tests: see final report
- governance/autonomy tests: see final report
- release/lifecycle regression: see final report
- fast_green: see final report
- `pcae health`: healthy
- `pcae check`: passed
- `pcae doctor task-memory`: clean
- `pcae push check`: see final report
- `pcae session bootstrap --compact --profile implementation`: completed
- `pcae runtime inspect --json`: execution availability `unavailable`, runtime state `Observed`, maximum plugin capability `observe`
- `pcae notify status`: checked before and after sourcing Telegram env
- `pcae skill invoke phase-finalization 114D`: resolved, target status completed

## Recommended Next Phase

114E — Model Containment Drill
