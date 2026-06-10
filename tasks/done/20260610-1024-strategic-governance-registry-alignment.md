# Task Contract

## Task ID

20260610-1024-strategic-governance-registry-alignment

## Title

Strategic Governance Registry Alignment

## Status

done

## Mode

implementation

## Goal

Reconcile _CI_KNOWN_CAPABILITIES with _CRI_KNOWN_CAPABILITIES (add 14 missing entries), populate commands fields for 65A and 65B in _CRI_KNOWN_CAPABILITIES, fix domain→objective inference mismatch in _ucd_classify_unmapped_capability, regenerate docs/COMMANDS.md and docs/CAPABILITY_INVENTORY.md. No new models, builders, CLI commands, or capability-objective mapping expansion.

## Allowed Files

- src/pcae/core/agent.py
- src/pcae/core/docs.py
- src/pcae/commands/agent.py
- src/pcae/cli.py
- tests/test_agent.py
- docs/COMMANDS.md
- docs/CAPABILITY_INVENTORY.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/DONE.md
- tasks/active/20260610-1024-strategic-governance-registry-alignment.md
- tasks/done/20260610-0706-strategic-state-summary.md
- .pcae/session.json

## Forbidden Files

- TBD

## Allowed Zones

- core
- commands
- cli
- tests
- docs
- tasks
- session
- config

## Forbidden Zones

- TBD

## Allowed Dependencies

- TBD

## Forbidden Dependencies

- TBD

## Enforcement Mode

advisory

## Forbidden Changes

- No runtime invocation
- No execution_allowed = True

## Acceptance Checks

- _CI_KNOWN_CAPABILITIES count increases to match _CRI_KNOWN_CAPABILITIES implemented count
- 65A commands field non-empty in _CRI_KNOWN_CAPABILITIES
- 65B commands field non-empty in _CRI_KNOWN_CAPABILITIES
- pcae strategic-state-summary unmapped capabilities show correct inferred objectives
- docs/COMMANDS.md includes strategic-roadmap-governance and strategic-state-summary
- docs/CAPABILITY_INVENTORY.md includes Strategic Roadmap Governance and Strategic State Summary
- All tests pass
- pcae check passes

## Documentation Requirements

- Update project memory files when workflow-visible behavior changes.

## Created Timestamp

2026-06-10T10:24:19.583739+02:00
