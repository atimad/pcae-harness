# Changelog

## Unreleased

- Started PCAE Harness project.
- Added Phase 1 `pcae init` scaffold.
- Added read-only `pcae inspect` with manifest-driven required path reporting.
- Added `pcae task new` for creating active Markdown task contracts.
- Added advisory `pcae check` validation for required files, task scope, forbidden files, and documentation updates.
- Added explicit `pcae hooks install` to configure Git to use `.githooks`.
- Added `.pcae/policy.toml` for repo-level protected-file configuration.
- Added policy status reporting to `pcae inspect`.
- Added validation diagnostics for invalid `.pcae/policy.toml` files.
- Extended `pcae task close` to close a specific active task by ID or filename.
- Added `pcae task list` for active and done task visibility.
- Added `pcae session write` for `.pcae/session.json` handoff snapshots.
- Added `pcae session read` for `.pcae/session.json` handoff summaries.
- Added `pcae session update` for `.pcae/session.json` handoff metadata.
- Added session continuity checks to `pcae check`.
