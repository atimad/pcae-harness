# Done

## Completed

- Created Phase 1 package structure.
- Added minimal CLI skeleton.
- Implemented `pcae init`.
- Added init tests.
- Implemented read-only `pcae inspect`.
- Added manifest-driven inspection and reporting tests.
- Added command-level coverage that `pcae init` creates `.githooks/pre-commit`.
- Implemented `pcae task new` for structured Markdown task contracts.
- Implemented advisory `pcae check` validation for required files, active task scope, forbidden files, and documentation updates.
- Implemented explicit `pcae hooks install` for configuring Git `core.hooksPath`.
- Improved `pcae check` active task discovery and violation diagnostics.
- Added wildcard and directory matching for task allowed-file scopes.
- Added forbidden-file enforcement with exact, wildcard, and directory task scopes.
