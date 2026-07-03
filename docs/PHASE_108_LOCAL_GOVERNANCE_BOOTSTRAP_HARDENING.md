# Phase 108E — Local Governance Bootstrap & Pre-Push Hardening

## Purpose

Strengthen PCAE's local governance bootstrap so contributors and AI agents
automatically receive local governance protections on a fresh clone,
before any future Permission Broker command-path integration. This phase
follows the read-only repository protection inspection performed after
108D, which identified the largest remaining local governance gap:
hooks required a separate manual `pcae hooks install` step, no pre-push
hook existed, and a fresh clone could be worked in without any local
governance at all.

## Scope

Local governance bootstrap hardening only. No runtime execution, no
Permission Broker command-path integration, no shell mediation, no
subprocess mediation, no backend invocation, no adapter invocation, no
Telegram inbound, no execution enablement, no execution capability, no
audit persistence, no rollback execution, no emergency stop, no CI
required-status-check enforcement, no GitHub branch-protection changes,
no Permission Broker enforcement, no automatic execution, no command
execution, no automatic apply.

## Bootstrap Lifecycle

Before this phase, the documented path was:

```
Fresh clone -> pcae init -> pcae hooks install (separate, easy to skip)
    -> pcae inspect/health/check -> Ready to contribute
```

After this phase:

```
Fresh clone -> pcae init (creates scaffold AND auto-installs hooks)
    -> pcae inspect/health/check/hooks status -> Ready to contribute
```

`pcae hooks install` remains available and fully idempotent, for the two
cases where auto-install doesn't apply: (1) `pcae init` was run before
`git init` (no repository to configure hooks against yet — `pcae init`
detects this and prints an explicit skip message rather than failing
silently), and (2) an existing PCAE-scaffolded repository predating this
phase, whose `.githooks/` directory doesn't yet contain a `pre-push` file
(`pcae init --force` regenerates it, then `pcae hooks install`
re-registers `core.hooksPath`).

## Governance Bootstrap Flow

`pcae init` (the `run_init` CLI handler) now performs two steps in
sequence, non-dry-run only:

1. Write PCAE's template scaffold (unchanged behavior — idempotent,
   never overwrites non-PCAE files, `--force` regenerates PCAE-managed
   templates).
2. If the current directory is inside a Git repository
   (`pcae.core.hooks.is_git_repo`), call `install_hooks()` — which sets
   `core.hooksPath` to `.githooks` — and print its result message. If
   not inside a Git repository, print an explicit skip notice naming the
   exact remediation (`git init`, then `pcae hooks install`) instead of
   silently doing nothing.

`--dry-run` mode is unaffected: it previews what template files would be
created and never touches `core.hooksPath` or any other git config,
consistent with "dry run must never mutate state."

## Hook Lifecycle

Two hook files are now part of PCAE's managed scaffold:
`.githooks/pre-commit` (unchanged — runs `pcae check`) and
`.githooks/pre-push` (new — runs the four governance checks below).
Both are registered in `INIT_TEMPLATES` and `FORCE_MANAGED_TEMPLATES`, so
`pcae init --force` regenerates both to pick up future updates, and both
are made executable automatically by `make_executable_when_needed`
(extended this phase to recognize `pre-push` alongside `pre-commit` and
any `.sh` file).

Because `core.hooksPath` points directly at the tracked `.githooks/`
directory rather than the default `.git/hooks/`, there is no separate
"installed copy" that can go stale — whatever is checked out in
`.githooks/` is exactly what Git runs. This means "outdated" hooks can
only mean one thing: the expected hook file doesn't exist in the
checkout yet (an older clone predating this phase). `diagnose_hooks()`
(new, `pcae.core.hooks`) reports this and every other relevant state:

| Status | Meaning |
|---|---|
| `installed` | `core.hooksPath` correct, all expected hook files present and executable. Healthy. |
| `not_a_git_repo` | Command run outside a Git repository. |
| `hooks_path_missing` | `core.hooksPath` was never configured. |
| `hooks_path_incorrect` | `core.hooksPath` points somewhere other than `.githooks`. |
| `hook_files_missing` | `core.hooksPath` correct, but one or more expected files (e.g. `pre-push`) don't exist. |
| `hook_files_not_executable` | Hook files exist but lack the executable bit. |

Every non-`installed` state carries a `recommended_remediation` tuple
naming the exact command to run — never a vague "fix your hooks"
message.

`pcae hooks status` (new subcommand) and `pcae doctor hooks` (new,
alongside the existing `execution-chain`/`task-memory`/`git-lock`/
`test-run` diagnostic family) both call `diagnose_hooks()` and report
identical information — one for discoverability under the `hooks`
command group, one for discoverability under the `doctor` diagnostic
family. Both are strictly read-only: `diagnose_hooks()` performs no
writes, no git config changes, and no file mutation, verified directly
by a test that snapshots the filesystem before and after a diagnosis
call and asserts no change.

## Pre-Push Hook

`.githooks/pre-push` runs exactly:

```sh
pcae health
pcae check
pcae doctor task-memory
pcae push check
```

under `set -eu`, so the first non-zero exit aborts the push. All four
commands are pre-existing, already-read-only PCAE commands (unchanged by
this phase) — the hook adds no new checking logic, it only wires
existing checks into the push path. Verified directly: the hook's source
contains none of `subprocess`-mediated code execution, no
`permission-broker`/`permission_broker` reference, and none of
`commit`/`git push`/`task new`/`task finish`/`--fix`/`--force` (no
mutating subcommand). A dedicated test runs the real hook script against
an ungoverned scratch repository and confirms it exits non-zero,
proving it actually blocks rather than merely reporting.

## Self-Repair

`pcae doctor hooks` is this phase's self-repair surface, matching the
existing `pcae doctor` family's convention (diagnose, then name the
exact fix). Every non-healthy diagnosis prints
`pcae hooks install`, `pcae init --force`, `git config core.hooksPath
.githooks`, or `chmod +x <files>` — whichever is the correct minimal fix
for that specific detected state, never a generic pointer.

## Contributor Experience

`docs/INSTALLATION.md` and `docs/CONTRIBUTOR_WORKFLOW.md` were updated to
describe the real, current bootstrap process: Scenario 1/2/3 all now show
a single `pcae init` step producing both scaffold and active hooks, with
`pcae hooks status` added to every "verify" step. A new "Hook
troubleshooting" table in `docs/INSTALLATION.md` maps every
`diagnose_hooks()` status to its exact fix. `docs/CONTRIBUTOR_WORKFLOW.md`
now states explicitly that the pre-push hook automates the four checks
contributors were already told to run manually before opening a PR.

## AI-Agent Implications

An AI agent following only the documented installation steps in a fresh
clone now ends up governed without needing separate tribal knowledge
about `pcae hooks install` — the single documented `pcae init` step is
sufficient. This narrows, but does not eliminate, the admin-bypass risk
identified in the pre-108E repository protection inspection: local hooks
protect against an agent *forgetting* to run governance checks before
committing/pushing, but they do not prevent a deliberate raw
`git commit --no-verify` / `git push` (no technical enforcement exists
for that, and this phase does not add any — see Remaining Limitations).
The pre-push hook specifically closes the gap where an agent could
previously push without ever running `pcae push check` at all, simply
because no hook existed to prompt it.

## Remaining Limitations

Explicitly not eliminated by this phase, matching its stated boundary:

- **`--no-verify` remains technically unblocked.** Nothing in this phase
  (or anywhere in the codebase) intercepts `--no-verify` at the git
  level — it remains only a simulated hard-block reason code in the
  older `permission_broker.py` prototype, never real enforcement. Local
  hooks are opt-in-by-convention, not unbypassable.
  A deliberate `git commit --no-verify` or `git push --no-verify`
  still skips both hooks entirely; this is a fundamental property of
  client-side Git hooks, not something a differently-designed hook
  could fix.
- **Admin bypass remains unchanged.** `enforce_admins: false` on GitHub
  branch protection is untouched by this phase, per its explicit
  boundary (no branch-protection changes). This phase only hardens
  *local* governance; the repository-level admin-bypass risk documented
  after 108D is unaffected.
- **No required CI status checks.** Also unchanged, also out of this
  phase's scope.
- **Existing clones from before this phase remain ungoverned for
  pre-push until they re-run `pcae init --force` (or `pcae hooks
  install` after manually adding `.githooks/pre-push`).** This phase
  cannot retroactively fix already-checked-out working directories; it
  can only ensure *future* `pcae init` runs (fresh clones, or explicit
  re-initialization) produce a governed state. `pcae doctor hooks` /
  `pcae hooks status` correctly detect and name the fix for this exact
  case (`hook_files_missing`).

None of these gaps block the target state for *new* bootstraps: a newly
cloned PCAE repository following only the documented `pcae init` step
becomes governed by default.

## Governance-By-Default Assessment

- **Can a contributor accidentally bypass local governance by following
  only the official installation guide?** No, as of this phase, for a
  fresh clone. `pcae init` alone (Step 4 in `docs/INSTALLATION.md`,
  Scenario 1) now installs both hooks; there is no longer a separate,
  skippable "Step 5" for hook installation to forget.
- **Can an AI agent accidentally bypass local governance after following
  the documented bootstrap?** No, for the same reason — the documented
  bootstrap is now a single step that leaves hooks active. An agent that
  deliberately uses `--no-verify` or raw `git` commands still bypasses
  governance, but that is a deliberate action, not an accident of
  following the docs (see Remaining Limitations).
- **Are there any remaining manual steps that are easy to forget?**
  Only for pre-existing (pre-108E) clones, which need one explicit
  `pcae init --force` to pick up the new pre-push hook — and
  `pcae hooks status`/`pcae doctor hooks` both detect and name this
  exact fix, so it is not silent.
- **Does the documentation accurately describe the real bootstrap
  process?** Yes, updated and verified against the actual current CLI
  behavior in this phase (fresh-clone tests exercise the real
  documented commands via subprocess, not just unit-level function
  calls).
- **What remaining gaps prevent PCAE from being "governed by default"?**
  `--no-verify`/raw-git bypass and the repository-level admin-bypass
  posture — both explicitly out of this phase's scope, both already
  documented from the pre-108D protection inspection, neither
  introduced or worsened by this phase.

## Fresh-Clone Validation Results

Validated via `tests/test_hooks_bootstrap_hardening.py`'s
`test_fresh_clone_bootstrap_reaches_governed_state` and
`test_fresh_clone_hooks_status_reports_healthy_after_bootstrap`: a
minimal upstream repository is created, initialized with
`init_harness()`, committed, and cloned locally (no network access).
Before any bootstrap step, `diagnose_hooks()` on the clone correctly
reports `hooks_path_missing` (hooks are tracked files, but
`core.hooksPath` is local git config, never cloned). After running the
real `python -m pcae init` subprocess against the clone (matching
exactly what a contributor would type), `diagnose_hooks()` reports
`installed`/healthy, and a real `python -m pcae hooks status --json`
subprocess against the clone confirms the same. No manual step beyond
the one documented `pcae init` command was used.

## Recommended Next Phase

**109A — Permission Broker Command-Path Integration Design.**
