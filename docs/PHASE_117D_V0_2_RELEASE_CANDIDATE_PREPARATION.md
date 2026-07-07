# Phase 117D - v0.2 Release Candidate Preparation

## Purpose

Phase 117D prepared PCAE for the future v0.2.0 release phase after
117C verified the quality baseline.

This was release preparation only. It did not publish a release, create
a tag, push a GitHub Release, publish to PyPI, publish packages, add
features, change runtime behavior, implement execution, modify
architecture, or change lifecycle behavior.

## Review Scope

The release-readiness review covered:

- new-user README positioning
- installation instructions
- examples and usage snippets in README/install/demo docs
- changelog
- project status
- Apache-2.0 license file
- contribution guidance
- stale TODO/temporary-note surfaces
- v0.2 messaging boundaries

## Documentation Prepared

Created `docs/RELEASE_NOTES_V0_2_0.md` as draft release notes for the
future release phase. The draft explicitly states that it is not a
published release artifact and that no tag, GitHub Release, PyPI
publication, or package publication occurred in 117D.

Updated release-facing documentation to align with the frozen v0.2
architecture and Phase 117C quality baseline:

- `README.md` now presents v0.2.0 release-candidate preparation as the
  current status and states the non-executing runtime posture.
- `docs/INSTALLATION.md` now describes v0.2 release-candidate
  installation expectations and includes `pcae runtime inspect --json`.
- `docs/DEMO_SCRIPT.md` now uses the current quality baseline and
  states the observe-only runtime boundary.
- `CHANGELOG.md`, `PROJECT_STATUS.md`, `tasks/TODO.md`,
  `tasks/DECISIONS.md`, and `tasks/DONE.md` were updated as governance
  memory.

## v0.2 Messaging Confirmation

The release-facing message is:

- PCAE is non-executing by design.
- Runtime state is `Observed`.
- Execution capability is unavailable.
- Maximum plugin capability is `observe`.
- Advisory evidence does not authorize action.
- Dry-run output does not authorize action.
- PCAE is not an autonomous coding agent.
- Human approval remains authoritative.

## Release Boundary Confirmation

117D did not:

- publish a release
- create a Git tag
- push a GitHub Release
- publish to PyPI
- publish packages
- modify package version metadata
- add features
- change runtime behavior
- implement execution
- modify architecture
- change lifecycle behavior
- change tests
- change production source code

## Review Findings

README messaging was stale: it still presented `v0.1.0-rc1` as the
current status and described v0.2 as a future target. That was corrected
for release-candidate preparation.

Installation commands remained valid. The version-specific note was
refreshed from v0.1 to v0.2 release-candidate posture. One stale
troubleshooting snippet, `pcae agent end`, was replaced with the
implemented `pcae agent release --agent-id <id> --force-stale` command.

The demo script's expected test-count note was stale. It was refreshed
to the Phase 117C baseline.

License and contribution guidance were present and adequate. The
contribution guide still mentions the v0.1 boundary in one release
context, but the governance requirements remain valid and no blocking
release defect was found.

No release-blocking temporary TODO/FIXME artifacts were found. The
remaining TODO content is explicit planning scratch space and not a
shipping blocker.

## Validation Plan

Required validation for this phase:

| Command | Expected result |
| --- | --- |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae doctor task-memory` | clean |
| `pcae push check` | clean or nothing to push |
| `pcae agent verify-handoff` | safe to continue |
| `pcae session bootstrap --compact --profile implementation` | succeeds |
| `pcae runtime inspect --json` | `Observed`, execution unavailable |
| `source ~/.config/pcae/telegram.env && pcae notify status` | Telegram configured/enabled |
| `python -m pytest -m "fast_green" -n auto -ra --durations=100` | `4390 passed` baseline expected |

## Release Readiness Recommendation

PCAE is ready for the dedicated v0.2.0 release phase after this phase's
validation and governed push complete.

Recommended next phase: 117E - v0.2.0 Release.
