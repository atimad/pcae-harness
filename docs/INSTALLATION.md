# PCAE Installation Guide

This guide explains how to install and initialize PCAE into a Git repository so that AI agent activity in that repository is governed, auditable, and human-authoritative from the first session.

---

## What "installing PCAE into a repo" means

PCAE is not an application you install once globally. It is a governance harness you install _into each repository_ where you want AI agents to operate under its control.

When you install PCAE into a repository, two things happen:

1. **The `pcae` CLI is made available** in that repository's Python environment, so you can run governance commands from its root.
2. **PCAE initializes its memory files** — a small set of structured documents, policy files, and directories under `.pcae/` — that record tasks, sessions, architecture decisions, and execution artifacts for that repository.

Every governance command (`pcae check`, `pcae health`, `pcae task new`, etc.) reads from and writes to that repository's `.pcae/` directory. Different repositories have independent, isolated PCAE state.

---

## Requirements

| Requirement | Version | Notes |
|---|---|---|
| Python | ≥ 3.9 | Check with `python3 --version` |
| Git | Any modern version | Required for hooks and session governance |
| pip | ≥ 21 | Included with Python ≥ 3.9 |

PCAE has no runtime dependencies beyond the Python standard library. The only optional dependencies are `pytest` and `pytest-xdist`, used for running the test suite.

## Current release posture (v0.3.0-rc1)

PCAE is positioned as a governed, non-executing AI coding lifecycle
harness. Installing it (editable or non-editable) gives you the `pcae`
console script and governed lifecycle commands: task contracts,
commit/push governance, report-trust validation, runtime introspection,
repository transition validation, evidence/advisory architecture,
outbound notification support, and, as of `v0.3.0-rc1`, a generic
external-agent intake path (`pcae intake create/show/list`) that
connects a real proposed change to PCAE's existing governed review/
promotion/rollback chain — see the
[v0.3 Quickstart](QUICKSTART_V0_3.md) for a 5-minute walkthrough. It
does not install or enable code-execution, backend-invocation,
autonomous agent execution, or shell mediation.

The runtime posture is intentionally observe-only: `pcae runtime inspect
--json` reports runtime state `Observed`, execution capability
`unavailable`, maximum plugin capability `observe`, and zero registered
runtime plugins. Advisory evidence and dry-run output are context for
human review; they do not authorize execution.

Outbound Telegram notification (`~/.config/pcae/telegram.env`) is
optional — every command works with it unset; see `pcae notify status`
for current configuration state. For the `v0.3.0-rc1` release summary,
see [docs/RELEASE_NOTES_V0_3_0_RC1.md](RELEASE_NOTES_V0_3_0_RC1.md);
for the prior `v0.2.0` full-release summary, see
[docs/RELEASE_NOTES_V0_2_0.md](RELEASE_NOTES_V0_2_0.md).

Historical v0.1 notes remain available in the v0.1 release-scope and
handoff documents. Telegram configuration was optional there as well;
the current v0.2 path preserves that optional notification posture.

---

## Scenario 1 — Brand-new repository

Use this path when starting a new project from scratch.

### Step 1 — Create the repository

```zsh
mkdir my-project
cd my-project
git init
git commit --allow-empty -m "Initial commit"
```

### Step 2 — Create and activate a virtual environment

```zsh
python3 -m venv .venv
source .venv/bin/activate
```

Your shell prompt should now show `(.venv)`.

### Step 3 — Install the pcae-harness package

Clone or copy the `pcae-harness` source into a location of your choice, then install it in editable mode from your project directory:

```zsh
pip install -e /path/to/pcae-harness
```

If you are working inside the `pcae-harness` repository itself (the canonical development case), run this from the repo root instead:

```zsh
pip install -e ".[dev]"
```

The `[dev]` extra adds `pytest` and `pytest-xdist`. Omit it if you do not need the test suite.

Verify the CLI is available:

```zsh
pcae --version 2>&1 || pcae health
```

### Step 4 — Initialize PCAE memory files and local governance hooks

Run `pcae init` from the repository root. This creates PCAE's required directories and template files without overwriting anything that already exists — **and, as of Phase 108E, automatically configures local Git hook governance in the same step** (no separate hook-installation step required):

```zsh
pcae init
```

The last line of output confirms hook installation:

```
Installed PCAE Git hooks: core.hooksPath is .githooks
```

PCAE ships two governed hooks: a pre-commit hook that runs `pcae check` before every commit (blocking commits that violate task scope or documentation requirements), and a pre-push hook that runs `pcae health`, `pcae check`, `pcae doctor task-memory`, and `pcae push check` before every push (blocking a push if any of those report an ungoverned or unhealthy state). Neither hook executes repository code, invokes the Permission Broker, or mutates repository state — both are pure governance checks.

`pcae init` only auto-installs hooks when run inside a Git repository (`git init` first if you have not already). If you are not yet inside a Git repository, `pcae init` prints a note and skips hook installation; run `git init` and then `pcae hooks install` (see below) once you are.

To preview what will be created without writing anything (this does not install hooks either — dry runs never mutate state):

```zsh
pcae init --dry-run
```

If you ever need to (re-)install hooks explicitly — for example, after cloning a repository that already has PCAE scaffolding but no local hook configuration yet — `pcae hooks install` remains available and is idempotent:

```zsh
pcae hooks install
```

### Step 5 — Verify local governance is active

```zsh
pcae inspect        # confirm all required files are present
pcae health          # confirm governance state is healthy
pcae check           # confirm policy checks pass
pcae hooks status    # confirm local Git hooks are installed and healthy
```

A healthy installation produces:

```
PCAE health
Overall status: healthy
Required PCAE files: all present
Policy validation: valid (repo config)
...
```

and:

```
PCAE Git hook status
  Status: installed
  Git repository: True
  core.hooksPath configured: '.githooks'
  core.hooksPath expected: '.githooks'
  Healthy: True
```

If `pcae hooks status` reports anything other than `installed`/`Healthy: True`, it prints the exact remediation command to run — see [Hook troubleshooting](#hook-troubleshooting) below. `pcae doctor hooks` reports the same diagnosis and is also available under the `pcae doctor` diagnostic family.

---

## Scenario 2 — Existing cloned repository (no existing code)

Use this path when you have cloned a repository that does not yet have any source code or project structure beyond the initial checkout.

### Step 1 — Enter the repository

```zsh
cd my-cloned-repo
```

### Step 2 — Create and activate a virtual environment

```zsh
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install pcae-harness

```zsh
pip install -e /path/to/pcae-harness
```

Or, if contributing to the pcae-harness repo itself:

```zsh
pip install -e ".[dev]"
```

### Step 4 — Initialize PCAE and local governance hooks

```zsh
pcae init
```

This creates PCAE's template files and, since Phase 108E, automatically installs the local Git hooks (pre-commit and pre-push) in the same step — no separate hook-install step is required for a fresh clone.

### Step 5 — Verify

```zsh
pcae inspect
pcae health
pcae check
pcae hooks status
```

If `pcae hooks status` does not report `Healthy: True` (for example, because `pcae init` was skipped or run outside a Git repository), run `pcae hooks install` to install hooks explicitly — it is idempotent and safe to re-run.

---

## Scenario 3 — Existing repository already containing code

Use this path when adding PCAE governance to a project that is already in active development.

The key difference from Scenario 1: `pcae init` will not overwrite any files that already exist. Review what it plans to create before running it:

```zsh
pcae init --dry-run
```

Inspect the dry-run output. Files listed as `Would skip` already exist and will not be touched. Files listed as `Would create` are net-new PCAE files.

If you want to regenerate PCAE-managed template files (such as `.githooks/pre-commit` and `.githooks/pre-push`) to pick up a newer version — for example, a repository whose PCAE scaffold predates Phase 108E and therefore has no pre-push hook yet:

```zsh
pcae init --force
```

`--force` overwrites PCAE-managed template files but never overwrites your project's own source code or non-PCAE files.

After reviewing the dry-run output:

```zsh
pcae init
pcae inspect
pcae health
pcae check
pcae hooks status
```

`pcae init` re-installs (or, for an outdated repo, freshly installs) local Git hooks every time it runs — this is always safe to repeat.

---

## What PCAE creates

`pcae init` creates the following structure. Everything under `.pcae/` and `.githooks/` is PCAE-owned. Everything else is yours to extend.

```
your-repo/
├── AGENTS.md                    # Instructions for AI agents working in this repo
├── PROJECT_STATUS.md            # Current phase and roadmap status
├── CHANGELOG.md                 # Contribution history
├── tasks/
│   ├── TODO.md                  # Active task contracts
│   ├── DONE.md                  # Completed task history
│   └── DECISIONS.md             # Architectural decision log
├── .agent-prompts/
│   └── end-session.md           # Agent session close prompt template
├── .githooks/
│   ├── pre-commit               # Runs `pcae check` before every commit
│   └── pre-push                 # Runs health/check/doctor/push-check before every push
├── scripts/
│   ├── check-docs-updated.sh    # Documentation check script (macOS/Linux)
│   └── check-docs-updated.ps1   # Documentation check script (Windows)
└── .pcae/
    ├── policy.toml              # Architecture zones, protected patterns, agent config
    ├── session.json             # Active session state (runtime, not committed)
    ├── agent-lock.json          # Agent lease lock (runtime, not committed)
    ├── exports/                 # Governance bundle exports
    ├── approvals/               # APA — Approved Prompt Artifacts
    ├── authorizations/          # ARA — Authorization Records
    ├── audit/                   # EAR — Execution Audit Records
    ├── results/                 # ERR — Execution Result Records
    ├── execution-packages/      # ECP — Execution Change Packages
    ├── promotion-reviews/       # EPR — Execution Promotion Reviews
    ├── promotion-executions/    # PER — Promotion Execution Records
    ├── rollback-executions/     # RER — Rollback Execution Records
    └── skills/                  # Governed skill packages
```

The `.pcae/` directories for execution artifacts (`approvals/`, `audit/`, `results/`, etc.) are created on demand when their respective commands are first used — they do not exist after a fresh `pcae init`.

---

## What to commit after initialization

Commit the PCAE scaffold files. These are the durable, shared governance state for your repository:

```zsh
git add AGENTS.md PROJECT_STATUS.md CHANGELOG.md
git add tasks/
git add .agent-prompts/
git add .githooks/
git add scripts/
git add .pcae/policy.toml
git add .pcae/exports/.gitignore
git commit -m "Add PCAE governance scaffold"
```

---

## What not to commit

| Path | Reason |
|---|---|
| `.venv/` | Local Python environment — must not be shared |
| `.pcae/session.json` | Runtime session state — changes every session |
| `.pcae/agent-lock.json` | Agent lease lock — runtime state, not project state |
| `.pcae/approvals/` | Execution artifacts — excluded in `.gitignore` by default |
| `.pcae/continuity-packs/` | Large binary-adjacent exports — excluded by default |
| `__pycache__/`, `*.pyc` | Python bytecode — always excluded |

The root `.gitignore` and `.pcae/exports/.gitignore` already exclude the correct runtime paths when you run `pcae init`. Do not remove those exclusions.

---

## Starting the first governed task

PCAE's governance model requires an active task contract before any work begins. A task contract declares the session goal, which files may be modified, and which operations are forbidden.

Create a task before writing any code or running agents:

```zsh
pcae task new "My first governed task"
```

To restrict the task to specific architecture zones (recommended):

```zsh
pcae task new "Add user authentication" --allowed-zone src --allowed-zone tests
```

To verify the task was created:

```zsh
pcae task show
```

To check that governance is coherent before starting:

```zsh
pcae check
```

When the task is complete:

```zsh
pcae task complete
```

---

## Checking health, status, and coherence

Run these commands to inspect the governance state of your installation at any time:

| Command | What it checks |
|---|---|
| `pcae health` | Overall governance health: required files, policy, active task, session continuity |
| `pcae inspect` | Detailed structural inspection: every required file, zone patterns, hook status |
| `pcae check` | Policy validation: source changes against task scope, documentation requirements |
| `pcae status coherence` | PROJECT_STATUS.md coherence against roadmap registry |
| `pcae session bootstrap --agent-id <id>` | Full session context pack for AI agents starting a new session |
| `pcae runtime inspect --json` | Machine-readable runtime posture, including execution unavailability |

For machine-readable output (useful in CI):

```zsh
pcae health --json
pcae check --json
pcae inspect --json
pcae runtime inspect --json
```

---

## Common installation problems

### `pcae: command not found`

The virtual environment is not activated, or the package was not installed into the active environment.

```zsh
source .venv/bin/activate
pip install -e /path/to/pcae-harness
pcae health
```

### `pcae check` fails: "No active task"

PCAE requires an active task contract before commits are allowed. Create one:

```zsh
pcae task new "Describe what you are working on"
```

### `pcae check` fails: "Documentation not updated"

The pre-commit hook detected that source files changed but no documentation was updated. Update the relevant documentation file (`README.md`, `docs/ARCHITECTURE.md`, etc.) and re-stage:

```zsh
git add docs/
git commit
```

### `pcae health` reports: "Agent lock: stale"

A previous agent session did not release its lock. This is not an error — it resolves automatically when a new session starts:

```zsh
pcae session bootstrap --agent-id my-agent
```

Or clear it manually if no agent is actively running:

```zsh
pcae agent release --agent-id my-agent --force-stale
```

### `pcae init` skips a file I want to regenerate

Use `--force` to overwrite PCAE-managed template files:

```zsh
pcae init --force
```

This will not overwrite your project's own source files or non-PCAE files.

### Hook troubleshooting

`pcae hooks status` (or `pcae doctor hooks`, which reports the same diagnosis) always names the exact remediation command for whatever state it finds:

| `pcae hooks status` reports | Meaning | Fix |
|---|---|---|
| `Status: installed`, `Healthy: True` | Fully governed. Nothing to do. | — |
| `Status: not_a_git_repo` | Not inside a Git repository. | `git init`, then `pcae hooks install` |
| `Status: hooks_path_missing` | `core.hooksPath` was never set — the most common state right after a fresh clone, before running `pcae init`. | `pcae init` (auto-installs) or `pcae hooks install` |
| `Status: hooks_path_incorrect` | `core.hooksPath` points somewhere other than `.githooks`. | `git config core.hooksPath .githooks` |
| `Status: hook_files_missing` | `core.hooksPath` is correct, but one or more expected hook files (e.g. `pre-push`) don't exist yet — typically a repository whose PCAE scaffold predates Phase 108E. | `pcae init --force`, then `pcae hooks install` |
| `Status: hook_files_not_executable` | Hook files exist but lost their executable bit (can happen after some file-transfer or archive workflows). | `chmod +x .githooks/pre-commit .githooks/pre-push` |

`pcae hooks install` reporting "already configured" / re-printing its success message is expected and harmless — installation is idempotent; re-running it never breaks anything.

### The pre-commit hook fails on the first commit

The hook runs `pcae check`, which requires an active task. Create one before committing:

```zsh
pcae task new "Initial project setup"
git commit -m "Add PCAE governance scaffold"
```

### The pre-push hook blocks my push

The pre-push hook runs `pcae health`, `pcae check`, `pcae doctor task-memory`, and `pcae push check` — the same four commands you should run before every push per [Step 5](#step-5--verify-local-governance-is-active) above. Run them individually to see which one is failing and follow its own remediation guidance; the hook is intentionally strict and never bypasses a real governance failure.

### `python -m pytest` fails after install

If you installed without `[dev]`:

```zsh
pip install -e ".[dev]"
python -m pytest -n auto
```

### Policy file is missing or invalid

If `.pcae/policy.toml` is missing or corrupt, re-run init with `--force`:

```zsh
pcae init --force
pcae inspect
```

---

## Read-only project intelligence commands (Phase 86)

After installation, six read-only commands are available:

```
pcae artifact-index --json     # Governance artifact catalog
pcae memory-snapshot --json    # Phase, lifecycle, roadmap state
pcae governance-timeline --json # Ordered governance events
pcae decision-log --json       # Recorded governance decisions
pcae risk-register --json      # Active, accepted, stale risks
pcae project-state --json      # All layers composed
```

These commands emit JSON to stdout. They do not write files, create storage,
or authorize actions. All output is read-only and non-authorizing.

## Gate dry-run commands (Phase 87)

A dry-run gate evaluator reports hypothetical action decisions:

```
pcae gate-dry-run --json
pcae gate-dry-run --json --requested-action source_mutation --requested-file src/example.py
pcae gate-dry-run --json --requested-action backend_invocation --requested-backend claude
pcae gate-dry-run --json --requested-action commit --commit-message-present
pcae gate-dry-run --json --requested-action push --push-target origin/main
```

Gate dry-run output is **not authorization**. No gate produces `allow`.
`authorization_granted=false` for every gate. The permission broker and shell
gate described in Phase 87 architecture documents are **not yet implemented**.

## Next steps

After a successful installation, see:

- [docs/ARCHITECTURE.md](ARCHITECTURE.md) — governance model, artifact chain, execution and promotion lifecycles
- [docs/COMMANDS.md](COMMANDS.md) — full command reference
- [docs/DEMO_SCRIPT.md](DEMO_SCRIPT.md) — guided demo walkthrough
- [docs/GOVERNANCE_LIFECYCLE_DIAGRAM.md](GOVERNANCE_LIFECYCLE_DIAGRAM.md) — lifecycle flow diagrams
- [docs/governance/GOVERNANCE_HANDBOOK.md](governance/GOVERNANCE_HANDBOOK.md) — governance policies and enforcement rules
- [CONTRIBUTING.md](../CONTRIBUTING.md) — contribution workflow and testing requirements
- [AGENTS.md](../AGENTS.md) — instructions for AI agents operating in this repository
