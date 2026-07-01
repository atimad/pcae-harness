# PCAE v0.1 — Golden Workflow

## Purpose

Turn the v0.1 release scope (`docs/RELEASE_SCOPE_V0_1.md`) into a concrete,
repeatable, command-oriented operator workflow — the single sequence of
governed PCAE commands an operator runs to do real phase work, close it out
trustworthily, and have the completion reported outbound, without ever
executing code or invoking a real AI backend through PCAE itself.

## Scope

Defines: the exact commands for start-of-phase, implementation, pre-
finalization, finalization, and post-completion verification; which
commands are required vs. optional diagnostics; which flows are
explicitly unsupported in v0.1; and how the workflow preserves the
non-execution boundary, report-trust hard-fail behavior, and outbound-only
Telegram reporting. Documentation and test-verification only — no new
commands or product behavior are added in this phase.

## Prerequisites

- A local clone of this repository with `pcae` installed (editable
  install; `python -m pcae` or `pcae` on `PATH`).
- Git configured with a remote (`origin`) for `pcae push`/`push check`.
- Optional: `~/.config/pcae/telegram.env` for outbound Telegram reporting
  (`PCAE_TELEGRAM_BOT_TOKEN`, `PCAE_TELEGRAM_CHAT_ID`,
  `PCAE_TELEGRAM_ENABLED`, `PCAE_NOTIFY_ENABLED`, `PCAE_NOTIFY_SINKS`).
  Telegram is entirely optional — every step below works with it unset.

Clean-install validation from a fresh checkout was performed in Phase
106D (editable install, non-editable install, and built sdist/wheel, all
in throwaway virtual environments) — see
`docs/PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md` and
`docs/V0_1_CLEAN_SMOKE_TEST.md` for the exact commands and results. Two
packaging defects found during that validation are fixed as of 106D:
`pcae health`/`pcae check` now fail cleanly (not with a crash) outside a
git repository, and the built sdist no longer includes local `.claude`/
`.pcae` state.

## Environment Setup

```
source ~/.config/pcae/telegram.env   # optional — skip if not using Telegram
```

### Optional: agent/session bootstrap

`pcae session bootstrap --agent-id <id>` (or `--compact` for a read-only,
lock-free variant) composes health, active-task, provenance, push-readiness,
and Telegram-runtime status into a single call — useful as an agent's
start-of-session command, in addition to (not instead of) the
start-of-phase checks in step 1 below. Not required for the golden
workflow, but supported and tested (`tests/test_session.py`); see `pcae
session bootstrap --help` and `pcae session continuity-check --help` for
the full flag set. (Identified in Phase 106G's post-RC audit as real,
tested infrastructure previously missing from this document.)

## Supported Golden Workflow

### 1. Start-of-session / start-of-phase

```
source ~/.config/pcae/telegram.env      # optional
pcae health
pcae check
pcae doctor task-memory
pcae notify status                       # only meaningful if Telegram configured
pcae phase-report show --latest --trust
pcae phase-report trust --json
git status --short
git rev-list --count origin/main..HEAD
```

Confirms the repo is idle/healthy, task-memory is clean, the previous
phase's report was trust-complete, and there is nothing unexpectedly
unpushed before starting new work.

### 2. Task/phase setup

```
pcae task new "<title>" --goal "<goal>" --mode <mode> \
  --allowed-file <path> [--allowed-file <path> ...] \
  --allowed-zone <zone> [--allowed-zone <zone> ...] \
  --enforcement-mode advisory
```

This is the actual, verified `pcae task new` syntax (`pcae task new --help`),
used to create every task contract in this project's own history,
including this phase's. Other `pcae task` subcommands
(`show`, `update`, `pause`, `resume`, `list`) exist and are supported for
inspecting/adjusting an active contract; their exact flags are documented
via `pcae task <subcommand> --help` and are not repeated here.

### 3. During implementation

- Inspect the active task contract (`pcae task show`) and stay within its
  declared allowed files/zones.
- Do the actual work (writing code, docs, tests — performed by the
  human/agent through normal editing tools; PCAE does not perform this
  step).
- Run focused tests for the area under change.
- Update `PROJECT_STATUS.md` / `CHANGELOG.md` / `tasks/DONE.md` as the
  task contract requires.
- **Do not** run raw `git commit` / `git push` — use the governed commands
  in step 4/5 below.
- Preserve the no-go boundary throughout (no shell mediation, no real
  backend invocation, no automatic apply — see "No-Execution Boundary"
  below).

### 4. Pre-finalization

```
pcae check
pcae phase-report trust --json
pcae push check
```

Confirms the task's file/zone scope is still respected, the phase report
(if one exists yet) is trust-complete or the gap is understood, and the
repo would currently be push-ready.

### 5. Finalization: report, notify, commit, push

```
source ~/.config/pcae/telegram.env               # optional
pcae notify status                                # only if Telegram configured
pcae skill invoke phase-finalization <PHASE_ID>
pcae commit implementation --path <file> [--path <file> ...] --message "<message>"
pcae task finish --staged-file-aware --commit "<completion message>"
pcae push check
pcae push --staged-file-aware
```

`pcae task finish --commit` automatically finalizes and trust-validates
the phase-completion report from `.pcae/phase-completion-metadata.json`
(if present) and dispatches Telegram **only** when the report is
push-state complete — never as a partial/pre-final report (105C.1/105D).
This is expected and correct: at this point in the workflow, push has not
happened yet, so `pushed_status` is still `not_pushed` and dispatch is
deferred, not broken.

**Optional, lower-level finalization path** (not required for the golden
workflow, but available): `pcae phase complete --summary "..."` — hard-fails
by default on incomplete trust (105D); use `--allow-partial-report` to
override (still never dispatches Telegram for a partial report). Useful
for re-dispatching a corrected, complete report after `pcae push`, once
`.pcae/phase-completion-metadata.json` has been updated to reflect the
real post-push state. This is why both commands exist side by side:
`task finish --commit` is the one integrated step of the golden workflow
(runs pre-push, correctly defers dispatch), while `phase complete` is the
separate, explicit step used *after* push to send the final, corrected
report — they are not interchangeable, and neither one supersedes the
other in v0.1. (Phase 106G's post-RC audit found the two commands'
finalize logic is implemented independently rather than shared, and
recommends unifying them in a future phase — see
`docs/PHASE_106_POST_RC_SYSTEM_INSPECTION_LIFECYCLE_CONNECTIVITY_AUDIT.md`.)

### 6. Post-completion verification

```
pcae phase-report show --latest --trust
pcae phase-report trust --json
git rev-list --count origin/main..HEAD
git status --short
pcae doctor task-memory
```

`git rev-list --count origin/main..HEAD` must read `0` once `pcae push`
has succeeded — this is how the golden workflow confirms nothing was left
unpushed at phase close.

## Required vs. Optional Commands

### Required

- `pcae health`
- `pcae check`
- `pcae doctor task-memory`
- `pcae push check`
- `pcae phase-report trust`
- `pcae phase-report show --latest --trust`
- `pcae notify status` — required *when Telegram is configured*; skip
  entirely when it is not (Telegram is optional infrastructure, not a
  required part of the workflow itself)
- `pcae skill invoke phase-finalization <PHASE_ID>` — required before
  phase completion, per this project's own operating convention
- A governed commit command (`pcae commit implementation`)
- `pcae task finish --commit`

### Optional diagnostics

- `git status --short`
- `git rev-list --count origin/main..HEAD`
- Focused `pytest` runs for the area under change
- `python -m pytest -m fast_green -n auto` (full fast-green gate)
- Detailed metadata inspection (`.pcae/phase-completion-metadata.json`,
  `.pcae/phase-reports/*.json`)

## Unsupported for v0.1 Production Workflow

- Raw `git commit` / `git push` in place of the governed commands above.
- `--no-verify` on any git operation.
- Force push.
- Arbitrary shell mediation (PCAE does not intercept or mediate shell
  commands in v0.1).
- Telegram inbound / polling / remote command reception.
- `/run` or any remote-execution trigger.
- Autonomous backend execution (no code path invokes a real AI backend).
- Automatic patch application.
- Rollback execution (the `pcae rollback`/`pcae promote` evidence chain
  described in `README.md` is a separate, still evidence-only design
  track, not part of the v0.1 golden workflow).

## Expected Outputs

- `pcae health` / `pcae check`: `healthy` / `passed` when idle or when the
  active task's scope is respected.
- `pcae doctor task-memory`: `clean. No inconsistencies detected.`
- `pcae push check`: `Ready to push.` (or `Nothing to push.` when already
  synced), including a `Phase report trust: passed` line.
- `pcae phase-report trust --json`: `"complete": true` for a properly
  populated, push-state-complete report.
- `pcae task finish --commit`: prints `Report trust:`, `Repair required:`,
  `Report notification:`, and `Telegram: outbound-only` lines.
- `git rev-list --count origin/main..HEAD`: `0` after a successful `pcae
  push`.

## Failure Handling

- If `pcae check`/`pcae health` fail mid-task: the active task contract's
  allowed files/zones likely need updating (`pcae task update`) — do not
  bypass with `--skip-checks` except as an explicit, understood override.
- If `pcae push check` fails on `Phase report trust: failed`: the latest
  phase report is content-incomplete (missing fields or disallowed
  placeholders) — run `pcae phase-report trust --json` for the exact
  missing/placeholder fields and repair the metadata, not the check.
- If `pcae task finish --commit` reports `Report notification:
  skipped_incomplete`: this is expected pre-push behavior (105C.1/105D),
  not a failure — it means push-state fields aren't final yet. Push, then
  optionally re-dispatch via `pcae phase complete` with corrected metadata
  if a final Telegram report is desired.
- If `pcae task finish --commit` fails on a commit/lock error: run
  `pcae doctor git-lock`, then `pcae task finish recover --dry-run`.

## Trust Gate Behavior

The 105A/105B report-trust validator (`pcae phase-report trust`) and the
105D hard-fail gates govern this workflow:

- `pcae phase complete` hard-fails by default (exit 1) on an incomplete/
  invalid report; `--allow-partial-report` is the explicit override
  (Telegram is still suppressed for a partial report either way).
- `pcae push check` fails if the latest phase report is content-incomplete
  (missing fields/placeholders), but does **not** require push-state
  fields to already say "pushed" — that would deadlock the normal
  task-finish-then-push sequence (105D design decision).
- `pcae task finish --commit` remains warning-only for push-state fields,
  since it structurally runs before the push it is reporting on
  (105C.1/105D).

## Telegram Outbound Behavior

Telegram delivery is entirely outbound: a short summary
(`sendMessage`) plus the full report as a document (`sendDocument`) are
sent only when `PCAE_NOTIFY_ENABLED`/sinks are configured **and** the
report is trust-complete. There is no inbound handler anywhere in
`core/notifications.py` — Telegram cannot send commands to PCAE, and the
golden workflow never relies on Telegram for anything but notification.

## No-Execution Boundary

Every command in this workflow is either: (a) a read-only governance check
(`health`, `check`, `doctor task-memory`, `phase-report trust/show`), (b) a
local git operation already gated by the existing lifecycle commands
(`commit implementation`, `task finish --commit`, `push`), or (c) an
outbound-only notification dispatch (Telegram). None of them invoke a real
AI backend, mediate an arbitrary shell command, apply a patch
automatically, or perform rollback execution. This matches
`docs/RELEASE_SCOPE_V0_1.md`'s excluded-capabilities list exactly.

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `pcae check` fails: "Source files changed without documentation file updates." | Task touched source/test files without touching a docs file | Update a doc the task contract allows, or confirm the task's `Documentation Requirements` |
| `pcae push check` shows `Phase report trust: failed` | Latest report missing required fields or contains a disallowed placeholder | `pcae phase-report trust --json` for exact fields; fix `.pcae/phase-completion-metadata.json` |
| `pcae task finish --commit` shows `Report notification: skipped_incomplete` | Normal pre-push state (push-state fields pending) | Not an error; push, then optionally re-dispatch via `pcae phase complete` |
| `pcae skill invoke phase-finalization <ID>` returns `target_type_unresolved` | The phase ID isn't in the separate roadmap registry yet (a known, pre-existing, out-of-scope gap — see 105B/105C/105C.1/105D/106A/106B phase reports) | Informational only; does not block the workflow |
| `git rev-list --count origin/main..HEAD` is nonzero after "finishing" | `pcae push` was not yet run, or failed | Run `pcae push check` then `pcae push --staged-file-aware` |

## Relationship to v0.2 Autonomy

This workflow is entirely v0.1-scoped: every command is read-only,
governed-local-git, or outbound-notification. v0.2's autonomy track
(runtime enforcement, governed backend invocation, adapter execution,
human-approval enforcement, durable audit persistence, rollback execution
governance — see `docs/RELEASE_SCOPE_V0_1.md`'s "v0.2 Full-Autonomy
Roadmap Boundary") would introduce new workflow steps of its own; none are
anticipated or reserved for in this document.

## Recommended Next Phase

106D — Packaging / Installation / Clean-Smoke Test — **complete**. See
`docs/PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md`.

106E — v0.1 Release Candidate (recommended next). Prepare the release
candidate with a final checklist, release notes, and tag-readiness review.
