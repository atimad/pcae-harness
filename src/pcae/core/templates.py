from __future__ import annotations

from pathlib import Path

INIT_TEMPLATES: dict[Path, str] = {
    Path("AGENTS.md"): """# AGENTS.md

## Operating Principle

The repo must remember the project. The agent must work inside explicit task boundaries.

## Agent Rules

- Read `PROJECT_STATUS.md` before starting work.
- Start from a task in `tasks/TODO.md`.
- Record meaningful decisions in `tasks/DECISIONS.md`.
- Move completed work into `tasks/DONE.md`.
- Update `CHANGELOG.md` for user-visible or workflow-visible changes.
- Run project checks before ending a session.
""",
    Path("PROJECT_STATUS.md"): """# Project Status

## Current Phase

Phase 1: CLI package skeleton and `pcae init`.

## Current State

PCAE Harness is being initialized as a Python CLI project.

## Next

- Implement `pcae inspect`.
- Implement `pcae task new`.
- Implement `pcae check`.
- Implement `pcae end`.
""",
    Path("CHANGELOG.md"): """# Changelog

## Unreleased

- Started PCAE Harness project.
- Added Phase 1 `pcae init` scaffold.
""",
    Path("tasks/TODO.md"): """# TODO

## Pending

- Implement `pcae inspect`.
- Implement `pcae task new`.
- Implement `pcae check`.
- Implement `pcae end`.
""",
    Path("tasks/DONE.md"): """# Done

## Completed

- Created Phase 1 package structure.
- Added minimal CLI skeleton.
- Implemented `pcae init`.
- Added init tests.
""",
    Path("tasks/DECISIONS.md"): """# Decisions

## Accepted

- Use Python and `pathlib` for cross-platform filesystem behavior.
- Use Markdown files as the only persistence mechanism for the MVP.
- Defer databases, LLM calls, and vector search.
- Keep commands modular under `src/pcae/commands`.
""",
    Path(".agent-prompts/end-session.md"): """# End Session Protocol

Before ending a session:

1. Update `PROJECT_STATUS.md`.
2. Update `CHANGELOG.md` if behavior changed.
3. Move completed task notes from `tasks/TODO.md` to `tasks/DONE.md`.
4. Record durable decisions in `tasks/DECISIONS.md`.
5. Run available checks.
""",
    Path(".githooks/pre-commit"): """#!/usr/bin/env sh
set -eu

if [ -x scripts/check-docs-updated.sh ]; then
  scripts/check-docs-updated.sh
fi
""",
    Path("scripts/check-docs-updated.sh"): """#!/usr/bin/env sh
set -eu

required_files="AGENTS.md PROJECT_STATUS.md CHANGELOG.md tasks/TODO.md tasks/DONE.md tasks/DECISIONS.md"

for file in $required_files; do
  if [ ! -f "$file" ]; then
    echo "Missing required PCAE file: $file" >&2
    exit 1
  fi
done
""",
    Path("scripts/check-docs-updated.ps1"): """$ErrorActionPreference = "Stop"

$RequiredFiles = @(
    "AGENTS.md",
    "PROJECT_STATUS.md",
    "CHANGELOG.md",
    "tasks/TODO.md",
    "tasks/DONE.md",
    "tasks/DECISIONS.md"
)

foreach ($File in $RequiredFiles) {
    if (-not (Test-Path -Path $File -PathType Leaf)) {
        Write-Error "Missing required PCAE file: $File"
        exit 1
    }
}
""",
}
