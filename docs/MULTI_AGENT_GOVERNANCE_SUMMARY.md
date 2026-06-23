# Multi-Agent Governance Design Summary

## Overview

PCAE's multi-agent governance design stream (Phases 82A–84K) defines how PCAE should govern AI-assisted work involving multiple agents. The design covers agent discovery, identity verification, prompt approval, backend invocation guards, output capture, intake classification, adoption review, and deferred item tracking — all under explicit human authorization at every step.

This is governance design documentation only. No multi-agent runtime execution, schema parsing, or CLI automation has been implemented from these designs. All designs carry `implementation_status=not_started`.

## Completed Design Stream

### Foundation (82A–82F)

Six foundation artifacts established agent identity, capability probing, subagent discovery, safety profiles, routing dry-run, and task splitting:

| Phase | Artifact | Purpose |
|-------|----------|---------|
| 82A | Agent Capability Registry Design | Structured model for representing AI agents |
| 82B | Agent Identity Capability Probe | Bounded identity and availability probes |
| 82C | Subagent Discovery Contract | How PCAE discovers and governs subagents |
| 82D | Subagent Safety Profile | Risk classification and permission boundaries |
| 82E | Agent Routing Dry-Run | Simulated routing decisions for task types |
| 82F | Multi-Agent Task Split Dry-Run | Simulated task decomposition across agents |

### First Governed Lifecycle (83A–83L)

Twelve phases proved end-to-end governed multi-agent execution with zero governance violations:

- Contract → Route → Package → Approve → Send/Capture → Intake → Review → Approve → Execute → Verify → Close
- 2 agents invoked (claude-local, claude-deepseek), 4 agents blocked (claude-kimi, codex, subagents, unknown)
- 3 adoption candidates executed (4 lines across 2 files), 4 deferred, 4 rejected
- No source/test/README changes from backend output

### Design Documentation (84A–84K)

Ten design phases formalized the lifecycle into machine-readable schemas, a state machine, command surface, guards, storage policy, and deferred item tracker:

| Phase | Design | Key Metrics |
|-------|--------|------------|
| 84A | Lifecycle Lessons / Roadmap | 10 proven capabilities, 5 risks, 10-phase roadmap |
| 84B | Prompt Package Schema | 24 validation rules, role/agent binding, hash verification |
| 84C | Capture Metadata Schema | 26 validation rules, mutation guard, storage policy fields |
| 84D | Output Intake Schema | 30 validation rules, 40 required checks across 4 categories |
| 84E | Adoption Candidate Schema | 32 validation rules, 10 candidate types, 8 status values |
| 84F | Lifecycle State Machine | 15 states, 17 transitions, 35 validation rules |
| 84G | Lifecycle Command Dry-Run | 8 commands, 27 validation rules, JSON conventions |
| 84H | Backend Invocation Guard | 20 pre-checks, 40 validation rules, 5 decision types |
| 84I | Capture Storage Policy | 12 entities, 35 validation rules, retention/redaction |
| 84J | Deferred Item Tracker | 12 categories, 35 validation rules, 8 tracked examples |

## Key Safety Boundaries

1. **No backend invocation without explicit approval.** The guard (84H) blocks invocation unless all 20 pre-checks pass.
2. **Prompt hash verification.** SHA256 of the sent prompt must match the approved hash; mismatch blocks invocation.
3. **Capture before intake.** Every invocation must produce captured output with hashes before classification.
4. **Intake before adoption.** Captured output must pass prompt adherence, safety, contract fit, and cross-output checks.
5. **Adoption approval before execution.** Three-step pipeline: review → approve → execute, each requiring human sign-off.
6. **Governed commit and push.** All commits and pushes use governed PCAE paths (`pcae push`), never raw git.
7. **Raw output not adopted by default.** Backend output is evidence, not approved content, until explicit review.
8. **Blocked agents remain blocked.** Only a governed verification phase can change agent status.
9. **Deferred is not approved.** Tracking an item does not authorize its implementation.
10. **No auto-routing, auto-sending, auto-adopting, auto-committing, or auto-pushing.** Human authority required at every boundary.

## Deferred Implementation Areas

All 84-series designs are `implementation_status=not_started`. Future implementation phases should cover:

- Schema parsers and validators (84B–84E designs)
- Lifecycle state machine engine (84F design)
- Multi-agent lifecycle commands (84G design)
- Backend invocation guard validators (84H design)
- PCAE-managed capture storage directories (84I design)
- Deferred item tracker storage (84J design)

## Future Tests

Phases 84A–84K did not add tests because they were documentation-only. Future implementation phases must add tests for schema parsing, guard decision validation, lifecycle state transitions, capture integrity, and tracker operations.

## Roadmap Reconciliation

The original persistent memory/project intelligence roadmap candidates (lifecycle memory model, artifact index, governance event timeline, decision log integration, risk register, project state snapshot) were deferred — not dropped — during the 84-series multi-agent governance design stream. The recommended next phase (84L) should reconcile these into a Phase 85 plan:

| Proposed | Name |
|----------|------|
| 85A | Persistent Lifecycle Memory Model |
| 85B | Artifact Index |
| 85C | Governance Event Timeline |
| 85D | Decision Log Integration |
| 85E | Risk Register |
| 85F | Project State Snapshot |

This reconciliation has not been performed. Phase 84L should formalize it.
