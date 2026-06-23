# Task: Phase 83G — Multi-Agent Prompt Send / Capture

## Objective

Send the exact approved planner and documentation-reviewer prompts to the
approved backends, capture stdout/stderr/return code/duration, run mutation
guard, and hold outputs for future intake. Do not adopt, apply, stage, commit,
or push backend output.

## Allowed Files

- docs/MULTI_AGENT_PROMPT_SEND_CAPTURE.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/83g-multi-agent-prompt-send-capture.md
- tasks/active/83f-multi-agent-prompt-invocation-approval.md
- tasks/completed/83f-multi-agent-prompt-invocation-approval.md

## Forbidden Files

- src/**
- tests/**
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- .githooks/**
- pyproject.toml
- README.md

## Acceptance Criteria

- Planner prompt sent to claude-local via claude --print
- Reviewer prompt sent to claude-deepseek via claude-deepseek --print
- stdout/stderr/return code/duration/hash captured
- Mutation guard before and after each invocation
- No adoption/application/staging of backend output
- Source code unchanged, tests unchanged

## Status

- [x] Created
- [ ] In Progress
- [ ] Complete
