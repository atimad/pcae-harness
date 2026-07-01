# Phase 106D — Packaging / Installation / Clean-Smoke Test

## Purpose

Validate PCAE v0.1 release readiness from an installation and
clean-smoke-test perspective: can PCAE actually be installed as a release
artifact (editable, non-editable, and built sdist/wheel), does the `pcae`
console script resolve correctly, do the required v0.1 commands exist and
behave sanely outside the development checkout, and does the golden
workflow (106C) hold up in a genuinely clean environment.

## Scope

Packaging metadata inspection, editable/non-editable install testing in
temporary virtual environments, `python -m build` sdist/wheel validation,
CLI command/help availability checks, golden-workflow smoke checks against
a fresh git clone, and Telegram-optional behavior verification. Two small,
release-critical defects found during this testing were fixed (see "Repair
Decisions"); no broad packaging redesign was performed.

## Non-goals

106D does not implement runtime enforcement, autonomous execution, real
backend invocation, adapter execution, shell mediation, Telegram inbound,
rollback execution, or apply/commit/push authorization beyond the existing
governed lifecycle. It does not add an execution enablement flag or
toggle. It does not publish to PyPI or perform any release tagging — that
is 106E's scope. v0.1 remains non-executing by design; v0.2 remains the
autonomy target.

## Relationship to v0.1 Release Scope

Builds directly on `docs/RELEASE_SCOPE_V0_1.md` (106A) and
`docs/V0_1_GOLDEN_WORKFLOW.md` (106C): this phase is the first time either
document's claims were tested against an environment that does **not**
already have PCAE's own development checkout, dependencies, and `.pcae/`
governance state present.

## Packaging Metadata Inspection

`pyproject.toml` (before this phase's fix):

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pcae-harness"
version = "0.1.0"
description = "Persistent Constrained Agentic Engineering Harness CLI."
readme = "README.md"
requires-python = ">=3.9"
license = "Apache-2.0"
dependencies = []

[project.scripts]
pcae = "pcae.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/pcae"]
```

Findings:

- **Version**: static `0.1.0`, matches the v0.1 scope freeze — not
  dynamic. Fine for a first release; a dynamic/tag-derived version scheme
  is a reasonable future improvement, not a blocker.
- **Python requirement**: `>=3.9` — reasonable, broad.
- **Dependencies**: `[]` — the CLI is dependency-free (stdlib only), which
  simplifies installation considerably (no third-party dependency
  resolution beyond the build backend itself).
- **Console script**: `pcae = "pcae.cli:main"` — correct and, per the
  install tests below, resolves properly in every install mode tested.
- **Package discovery**: wheel target explicitly scoped to `src/pcae`
  (`[tool.hatch.build.targets.wheel] packages = ["src/pcae"]`) — correct,
  and confirmed to produce a clean wheel (only `pcae/` package files).
- **Sdist scope**: **not previously configured** — hatchling's default
  sdist behavior swept in the entire repository checkout. Fixed in this
  phase (see "Repair Decisions").
- **Build backend**: hatchling, present and functional; `python -m build`
  works once `build` is installed in the target environment (not a
  runtime dependency of PCAE itself, only needed to build a release
  artifact).
- **README/LICENSE**: both present (`README.md`, `LICENSE`) and correctly
  referenced/bundled.

## Clean Environment Strategy

All install/build testing was performed in throwaway `mktemp -d` virtual
environments and directories, outside this repository, with each temp
directory removed immediately after use. No test artifacts, build output,
or temporary venvs were left in the repository or committed.

## Editable Install Result

```
python -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/python" -m pip install --upgrade pip setuptools wheel
"$tmpdir/venv/bin/python" -m pip install -e /Users/atilamadai/repos/pcae-harness
```

**Result: succeeded.** `pcae --help` resolved correctly and listed the
full command tree. `pcae phase-report trust --help`, `phase-report show
--help`, `notify status --help`, `push check --help`, `doctor task-memory
--help`, `task finish --help`, `commit implementation --help`, `skill
invoke --help`, `health --help`, `check --help` all returned exit 0 with
correct help text.

**Defect found and fixed**: running `pcae health` / `pcae check` outside
any git repository crashed with an unhandled
`subprocess.CalledProcessError` traceback instead of a clear error
message. See "Repair Decisions" — this is now a clean, one-line error.

## Non-Editable Local Install Result

```
python -m venv "$tmpdir2/venv"
"$tmpdir2/venv/bin/python" -m pip install --upgrade pip setuptools wheel build
"$tmpdir2/venv/bin/python" -m pip install /Users/atilamadai/repos/pcae-harness
```

**Result: succeeded.** Verified the installed package is a true
site-packages copy, not a reference back to the source checkout
(`python -c "import pcae; print(pcae.__file__)"` resolved inside the
venv's `site-packages/`, not the repo). `pcae --help` and
`pcae phase-report trust --help` both worked standalone, confirming the
package is genuinely self-contained once installed.

## Build Artifact Result

```
"$tmpdir2/venv/bin/python" -m build --outdir "$builddir" /Users/atilamadai/repos/pcae-harness
```

**Result: succeeded**, both `pcae_harness-0.1.0.tar.gz` (sdist) and
`pcae_harness-0.1.0-py3-none-any.whl` (wheel) built.

**Defect found and fixed**: the sdist, before this phase's fix, contained
**44,399 files (~6.4MB)** — the entire repository checkout, including
`.claude/settings.local.json` (local-only settings) and `.pcae/session.json`
/ `.pcae/provenance-history.json` (local runtime state that should never
ship as "source"). The **wheel was already correctly scoped** (118 files,
only `pcae/` package modules) — so end users installing from a wheel (the
common case) were never affected; only a from-sdist build was bloated.
Fixed by adding an explicit `[tool.hatch.build.targets.sdist]` include
list. Rebuilt sdist: **117 files, ~1.1MB** — `src/pcae`, `README.md`,
`LICENSE`, `pyproject.toml`, plus hatchling's auto-included `PKG-INFO` and
`.gitignore`. Re-verified: installing directly from the corrected sdist
(`pip install pcae_harness-0.1.0.tar.gz`) still succeeds and produces a
working `pcae` command.

## CLI Command Availability Result

All required v0.1 golden-workflow commands (`health`, `check`,
`doctor task-memory`, `push check`, `phase-report trust`,
`phase-report show --trust`, `notify status`, `task finish`,
`commit implementation`, `skill invoke`) resolve with exit 0 for `--help`
in every install mode tested (editable, non-editable, built-wheel).

## Golden Workflow Smoke Result

Cloned this repository fresh (`git clone` into a temp directory) and ran,
using the editable-install venv's `pcae`:

- `pcae health` → `healthy (idle)` (one harmless warning: session snapshot
  missing, expected for a fresh clone — resolved by `pcae session write`,
  not required for the golden workflow's read-only diagnostics).
- `pcae check` → passed.
- `pcae doctor task-memory` → clean.
- `pcae phase-report trust --json` → `"complete": true` (correctly fell
  back to the pre-completion metadata draft, since `.pcae/phase-reports/`
  is gitignored and not present in a fresh clone — matches 105B's
  documented fallback behavior).
- `pcae push check` → `Nothing to push` / `phase_report_trust: skipped`
  (correct: no `.pcae/phase-reports/latest.json` exists in a fresh clone).

All golden-workflow diagnostic commands from `docs/V0_1_GOLDEN_WORKFLOW.md`
work correctly in a genuinely clean clone, with no execution features
reachable and no unhandled crashes.

## Telegram Optional / Disabled Behavior

With `PCAE_TELEGRAM_BOT_TOKEN` / `PCAE_TELEGRAM_CHAT_ID` /
`PCAE_TELEGRAM_ENABLED` / `PCAE_NOTIFY_ENABLED` all unset:

```
pcae notify status
```

Reports `Configured: False`, `Enabled: False`, `Token: missing`,
`Chat ID: missing`, and prints a clear hint
(`Set PCAE_NOTIFY_ENABLED=1 to enable notification dispatch.`) — no crash,
no attempted network call (`External network: Active by default: False`).
Confirms Telegram is safely, silently skippable and never required for
any golden-workflow step.

## Packaging Blockers

| Item | Status |
|---|---|
| `pcae health`/`pcae check` crash outside a git repo | **Fixed this phase** |
| Sdist bloat / local-state leakage (`.claude/`, `.pcae/session.json`) | **Fixed this phase** |
| Wheel scoping | Already correct — no blocker |
| Console script resolution | Already correct — no blocker |
| Editable install | Already correct — no blocker |
| Non-editable install | Already correct — no blocker |
| `python -m build` availability | Not a runtime dependency; documented as a release-engineering prerequisite, not a blocker |
| PyPI publication / release tagging | Out of scope for 106D — deferred to 106E |
| Version scheme (static vs. dynamic) | Not a blocker for v0.1; a future improvement |

No remaining blockers before a v0.1 release candidate, given the two
fixes above.

## Repair Decisions

1. **`pcae health`/`pcae check` crash outside a git repo.** First attempt
   introduced a new `NotAGitRepositoryError` raised from
   `core/git_status.py::read_git_changes`/`read_git_branch`, caught in
   `cli.py::main()`. This **broke 40 existing tests** (e.g.
   `tests/test_provenance.py`), because several call sites — notably
   `core/provenance.py::_safe_git_branch` — already had their own
   `except (subprocess.CalledProcessError, FileNotFoundError)` handling
   around these functions, and the new custom exception type bypassed
   those handlers entirely. **Corrected approach**: reverted
   `git_status.py` to its original behavior (raising the raw
   `subprocess.CalledProcessError`, exactly as before), and instead added
   a narrowly-scoped catch in `cli.py::main()` for
   `subprocess.CalledProcessError` where `exc.cmd[0] == "git"` — this
   only intercepts the specific "a git command failed" case at the
   top-level CLI entry point (where nothing was catching it before), and
   does not change behavior for any of the 78 existing call sites of
   `read_git_changes`/`read_git_branch` that already handle these errors
   themselves. Re-ran fast-green after the correction: 4390/4390, no
   regressions.
2. **Sdist scope.** Added `[tool.hatch.build.targets.sdist] include =
   ["src/pcae", "README.md", "LICENSE", "pyproject.toml"]` to
   `pyproject.toml`. The wheel target was already correctly scoped and is
   unchanged.

No safety checks were weakened. No product behavior beyond these two
targeted fixes was changed.

## Residual Risks

1. `python -m build` (and its `build`/isolated-venv dependencies) is not
   installed by default and is not a runtime dependency of PCAE — a
   release engineer must install it explicitly to build distribution
   artifacts. This is normal Python packaging practice, not a defect.
2. Version is static (`0.1.0`) — bumping it for future releases is a
   manual `pyproject.toml` edit, not automated from git tags. Acceptable
   for a first release; worth revisiting for v0.2+.
3. This phase validated install/build mechanics and CLI availability, not
   full functional behavior end-to-end from a built wheel (e.g. it did not
   re-run the entire test suite against a wheel-installed copy — the test
   suite runs against the source checkout via `pythonpath = ["src"]`).
   Given the wheel's package contents are identical to the source tree's
   `pcae/` package (confirmed via the wheel file listing), this is judged
   low-risk, not a blocker.

## Recommended Next Phase

106E — v0.1 Release Candidate. Prepare the v0.1 release candidate with a
final checklist, release notes, and tag-readiness review, now that
packaging/install/build have been smoke-tested and their defects fixed.
