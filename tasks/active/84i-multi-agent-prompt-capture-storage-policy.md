# Task: Phase 84I — Multi-Agent Prompt Capture Storage Policy

## Objective

Design prompt/capture storage policy for governed multi-agent execution.
Documentation-only. No implementation, no backend invocation, no storage creation.

## Allowed Files

- docs/MULTI_AGENT_PROMPT_CAPTURE_STORAGE_POLICY.md
- PROJECT_STATUS.md
- CHANGELOG.md
- tasks/active/84i-multi-agent-prompt-capture-storage-policy.md
- tasks/active/84h-multi-agent-backend-invocation-guard-hardening.md
- tasks/completed/84h-multi-agent-backend-invocation-guard-hardening.md

## Forbidden Files

- src/**
- tests/**
- docs/REAL_CAPTURED_TASKS.md
- .pcae/**
- .githooks/**
- pyproject.toml
- README.md

## Acceptance Criteria

- docs/MULTI_AGENT_PROMPT_CAPTURE_STORAGE_POLICY.md exists
- Defines storage policy name multi_agent_prompt_capture_storage_policy
- Defines storage policy version 0.1
- Documents storage threat model, entity model, prompt/hash/invocation policies
- Documents stdout/stderr capture, raw output, manifest, git-vs-non-git policies
- Documents retention, redaction, adoption reference, integrity, failure/recovery policies
- At least 30 validation rules
- No implementation, no backend invocation, no storage creation
- Source code unchanged, tests unchanged

## Status

- [x] Created
- [x] In Progress
- [ ] Complete
