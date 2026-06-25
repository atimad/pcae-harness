# Task: Phase 88H — Mutation/Adoption Preflight Prototype

## Objective

Implement explicit mutation/adoption preflight command. Evaluates whether a
proposed mutation or adoption has sufficient evidence. Does not mutate files
or perform adoption.

## Allowed Files

- src/pcae/core/mutation_preflight.py
- src/pcae/commands/mutation_preflight.py
- src/pcae/cli.py
- src/pcae/core/docs.py
- tests/test_mutation_preflight.py
- docs/PHASE_88_MUTATION_ADOPTION_PREFLIGHT_PROTOTYPE.md
- docs/COMMANDS.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/88h-mutation-adoption-preflight-prototype.md
- tasks/completed/88g-mutation-adoption-preflight-design.md

## Forbidden Files

- README.md
- docs/LINKEDIN_ARTICLE_DRAFT.md
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- .githooks/**

## Acceptance Criteria

- Mutation/adoption preflight command exists
- JSON output with decision/reason codes
- No mutation performed
- No adoption review/approval/execution
- authorization_granted=false always
- execution_authorized=false always
- README unchanged

## Status

- [x] Created
- [x] In Progress
- [x] Complete
