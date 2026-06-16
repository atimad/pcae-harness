# Task Contract

## Task ID

20260615-1913-69l-execution-sandboxing-architecture

## Title

69L Execution Sandboxing Architecture

## Status

done

## Mode

implementation

## Goal

Introduce workspace isolation for `invoke_readonly_execution`. The subprocess runs inside
a git-worktree sandbox (sandbox_dir) rather than directly in root. Post-state for ECR is
captured from sandbox_dir before destruction. Sandbox creation failure blocks as Condition 13.
ERR schema expands sandbox_mode to "workspace_isolation". Six SLR entries document
forward-compatibility constraints for Phase 69M Write Execution Governance.

## Design Resolutions Applied

- GOV-B-001: sandbox_mode enum expanded via _EGA_VALID_SANDBOX_MODES (Option B)
- GOV-B-002: _easi_create_automatic_ecr accepts post_state param; capture at call site
- GOV-B-003: Condition 13 mirrors Condition 12; execution_allowed=False in all blocked paths
- Decision A: git worktree add --detach + rsync overlay as canonical sandbox strategy
- Decision B: tempfile.mkdtemp(prefix="pcae_sandbox_") for collision-free temp dirs
- Decision C: _ESB_PRODUCTION_READINESS_CRITERIA with 8 formal criteria (ESB-C-001..008)
- Decision D: workspace_isolation only; os_isolation deferred as SLR-69L-002

## Forward-Compatibility Disclosures (69L→69M Review)

### Containment Scope

69L workspace isolation is behavioral containment, not OS containment. The subprocess
runs with cwd=sandbox_dir. Absolute path writes and external symlink write-through are
not prevented by filesystem enforcement. These constraints are documented in
_ESB_GOVERNANCE_BOUNDARIES and in SLR-69L-005.

### Governance Boundaries Added for Forward-Compatibility

The following _ESB_GOVERNANCE_BOUNDARIES entries are required disclosures — they prevent
69M from inheriting unqualified isolation claims from 69L:

- containment_assumes_read_only_subprocess=True
- write_execution_invalidates_isolation_claim=True
- governance_boundaries_scope="read_only_execution"
- write_execution_requires_independent_boundary_review=True
- git_worktree_shares_object_store_with_root=True
- git_commits_from_sandbox_land_in_shared_object_store=True
- external_symlinks_copied_as_live_symlinks=True
- ecr_blind_to_external_symlink_write_targets=True
- sandbox_destruction_is_not_lifecycle_aware=True
- rollback_candidate_semantics_assume_root_execution=True

### Overclaiming Prohibition

Do NOT use: root_working_tree_unmodified_by_subprocess=True
Use precise alternatives:
- root_not_used_as_execution_cwd=True
- relative_workspace_changes_isolated_to_sandbox=True
- absolute_path_access_not_contained_by_workspace_isolation=True

### SLR Entries Required at 69L Commit Boundary

SLR-69L-001: sandbox_provider fixed to "git_worktree"; container providers deferred.
SLR-69L-002: os_isolation deferred; workspace_isolation is development containment only.
SLR-69L-003: sandbox_dir is ephemeral; forensic artifact copy deferred.
SLR-69L-004: Promotion payload gap — ECR captures paths not content; ECP class required in 69M.
SLR-69L-005: Workspace isolation is behavioral not OS containment; absolute path writes uncontained.
SLR-69L-006: git worktree shares object store with root; git commits in sandbox persist in shared store.

## New Constants Prefix

_ESB_*

## Allowed Files

- .pcae/session.json
- .pcae/strategic-lineage.json
- .pcae/provenance-history.json
- tasks/active/**
- tasks/done/**
- tasks/TODO.md
- tasks/DONE.md
- tasks/DECISIONS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- docs/COMMANDS.md
- docs/CAPABILITY_INVENTORY.md
- docs/ROADMAP_REGISTRY.md
- src/pcae/cli.py
- src/pcae/commands/agent.py
- src/pcae/core/agent.py
- src/pcae/core/docs.py
- tests/test_agent.py
- tests/test_strategic_lineage.py

## Forbidden Files

- src/pcae/core/strategic_lineage.py

## Allowed Zones

- core
- commands
- cli
- tests
- docs
- tasks
- session
- config

## Enforcement Mode

advisory

## Forbidden Changes

- No runtime invocation (tests mock subprocess only)
- No prompt execution
- No execution authorization
- No commit
- No push
- No automatic rollback
- No os_isolation sandbox type (deferred: SLR-69L-002)
- No network isolation
- No process isolation
- No Docker dependency
- No sandbox-exec dependency
- No production_containment_ready=True assertion from constant alone
- No write execution
- No promotion payloads
- No ECP artifact class (deferred: SLR-69L-004)
- No redesign of execution chain beyond approved sandbox integration

## Acceptance Checks

- pcae status coherence passes
- pcae health passes
- pcae check passes
- python -m pytest -n auto passes
- sandbox_mode="workspace_isolation" accepted by _ega_validate
- invalid sandbox_mode rejected by _ega_validate
- cwd passed correctly in _ega_run_subprocess
- Condition 13 blocks before subprocess (execution_allowed=False, stored=False)
- post_state captured from sandbox before destroy
- _easi_create_automatic_ecr uses provided post_state when present
- ERR stores sandbox_mode, sandbox_id, sandbox_provider, sandbox_dir, sandbox_created
- production_containment_ready=False enforced
- all six SLR-69L entries present in _ESB_GOVERNANCE_BOUNDARIES or advisory
- all ten forward-compatibility boundaries present in _ESB_GOVERNANCE_BOUNDARIES
- no rollback, no write execution, no git reset/revert/commit/push in ESB functions

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.
- Update _EGA_SANDBOX_LIMITATIONS to reflect 69L workspace isolation
- Update EASI_ADVISORY / add ESB_ADVISORY strings

## Created Timestamp

2026-06-15T19:13:47.274037+02:00
