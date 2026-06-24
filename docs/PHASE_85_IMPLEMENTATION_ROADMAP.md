# Phase 85 Implementation Roadmap

## 1. Purpose

Plan the governed implementation of the Phase 85 persistent memory and project intelligence
design sequence (85A–85F) into working PCAE functionality. This roadmap defines implementation
order, minimum viable scope, storage strategy, CLI surfaces, test strategy, governance gates,
safety boundaries, and risks.

## 2. Scope

Implementation planning only. This artifact defines what should be built, in what order, with
what safeguards. It does not implement any functionality, create storage, modify source code,
or add tests.

## 3. Non-Goals

- Implementing any Phase 85 design.
- Creating storage directories, machine-readable files, or CLI commands.
- Modifying source code, tests, README, or existing design artifacts.
- Backend invocation, prompt sending, capture, intake, or adoption.

## 4. Phase 85 Design Sequence Summary

| Phase | Layer | Key Metrics | Status |
|-------|-------|-------------|--------|
| 85A | Persistent Lifecycle Memory Model | 18 entities, 21 fields, 38 validation rules | draft_documented |
| 85B | Artifact Index | 24 categories, 19 fields, 38 validation rules | draft_documented |
| 85C | Governance Event Timeline | 33 event types, 19 fields, 42 validation rules | draft_documented |
| 85D | Decision Log Integration | 13 decision types, 25 fields, 42 validation rules | draft_documented |
| 85E | Risk Register | 22 risk types, 32 fields, 42 validation rules | draft_documented |
| 85F | Project State Snapshot | 26 sections, 41 fields, 44 validation rules | draft_documented |

All six layers are designed. All have `implementation_status=not_started`. Together they
define a complete project-intelligence stack: what to remember, where evidence lives, when
events happened, what was decided, what risks exist, and how to produce a project-state answer.

---

## 5. Implementation Principles

1. **Read-only first.** Every layer starts as a read-only query against committed artifacts.
   No write-back, no mutable state, no cache-as-authority.
2. **No execution authorization from memory.** Memory reports state; it does not grant permission.
3. **No adoption authorization from memory.** Adoption requires its own lifecycle, not a memory query.
4. **No commit/push authorization from memory.** Commit/push require governed `pcae push`.
5. **Repo artifacts remain source of truth.** Machine-readable outputs are derived, not authoritative.
6. **Implementation must be test-backed.** Every implementation phase adds tests.
7. **Small vertical slice before broad implementation.** Prove one layer end-to-end before parallelizing.
8. **Snapshot is generated from lower layers, not hand-written.** The snapshot command composes
   outputs from memory, index, timeline, decisions, and risks.
9. **Permission broker remains future direction** unless the operator explicitly scopes it into
   a governed implementation phase.
10. **Backward compatibility required.** Existing PCAE commands must not break.

## 6. Implementation Threat Model

| # | Threat | Impact | Mitigation |
|---|--------|--------|------------|
| IT-1 | Memory treated as authority | Execution bypasses governance gates | Read-only-first; no authorization flags set by memory |
| IT-2 | Snapshot suggests unsafe next action | Agent takes forbidden action | Forbidden-action list must accompany next-safe-action list |
| IT-3 | Artifact index misses authoritative artifact | Evidence gap in snapshot | Index must discover from filesystem, not hardcoded list |
| IT-4 | Timeline order wrong | Causal analysis incorrect | Ordering tests required; commit timestamps as anchor |
| IT-5 | Decision log loses rejection | Rejected item re-enters pipeline | Rejection preservation test required |
| IT-6 | Accepted risk treated as mitigated | Risk assumed resolved | Separate status values; test distinction |
| IT-7 | Stale handoff-state-refresh signal misclassified | Progress blocked or risk dismissed | Classification must be explicit with evidence |
| IT-8 | Generated cache becomes source of truth | Repo artifacts bypassed | Cache must be regenerable; never committed as authoritative |
| IT-9 | Tests skipped for implementation | Implementation unverified | Gate: no merge without tests |
| IT-10 | Permission broker implemented too early | Scope creep into enforcement before design is validated | Future-direction gate; operator must explicitly authorize |

---

## 7. Implementation Dependency Order

The recommended implementation order follows layer dependencies:

```
86B — Data Model and Storage Design
  ↓
86C — Read-Only Artifact Index Prototype
  ↓
86D — Persistent Memory Snapshot Prototype
  ↓ (can parallel with 86E–86G after 86C)
86E — Governance Event Timeline Extraction
  ↓
86F — Decision Log Extraction
  ↓
86G — Risk Register Extraction
  ↓
86H — Project State Snapshot CLI
  ↓
86I — Phase 85 Integration Tests
```

### Rationale

1. **86B first**: Defines shared data models and storage conventions before any layer is implemented.
2. **86C next**: Artifact index is foundational — all other layers reference artifacts by ID and path.
3. **86D after 86C**: Memory snapshot depends on artifact index for evidence lookup.
4. **86E–86G can partially parallel**: Timeline, decision log, and risk register each depend on
   the artifact index (86C) and data model (86B), but have limited cross-dependencies.
5. **86H after 86E–86G**: Project state snapshot composes all lower layers.
6. **86I last**: Integration tests verify cross-layer consistency after all layers exist.

### Alternative: Narrower MVP First

If the operator prefers a faster first deliverable, an alternative sequence is:

```
86B — Data Model (narrow: artifact record only)
86C — Artifact Index CLI (pcae artifact-index --json)
86D — Snapshot MVP (pcae project-state --json, artifact-index-only)
86E+ — Expand with timeline/decisions/risks
```

This produces a useful `pcae project-state` command sooner but with fewer answer capabilities.

## 8. Minimum Viable Implementation Scope

The smallest useful vertical slice:

| Component | MVP Scope |
|-----------|-----------|
| Artifact index | Discover docs/ artifacts, classify by type, report freshness |
| Memory snapshot | Read latest phase from task contracts, read health from PCAE commands |
| Project state | Compose artifact index + memory snapshot into JSON output |
| CLI | `pcae project-state --json` (read-only) |
| Tests | Artifact classification, field completeness, forbidden-action output |

**Not in MVP:**
- Timeline extraction (requires commit-log parsing)
- Decision log extraction (requires artifact content parsing)
- Risk register extraction (requires decision + artifact cross-referencing)
- Write-back or mutable cache
- Permission broker

## 9. Storage Strategy

### Options Evaluated

| Option | Pros | Cons |
|--------|------|------|
| Docs-only derived model | No new storage; human-readable | Not machine-queryable |
| `.pcae` generated cache | Fast queries; regenerable | New storage directory; cache staleness risk |
| Committed machine-readable artifact | Versioned; diffable | Grows repo; merge conflicts |
| Hybrid: committed docs + generated read-only cache | Best of both | More complexity |

### Recommendation

**Start with read-only command output (no persisted storage).** The first implementation
should generate project-state answers on-the-fly by scanning committed artifacts and PCAE
command outputs. No `.pcae` cache, no committed JSON state.

If performance becomes an issue (unlikely for a documentation-heavy project), a regenerable
`.pcae/cache/` directory can be introduced in a later phase with explicit storage authorization.

**Do not create storage in 86A.** Storage decisions are deferred to 86B.

## 10. Read-Only-First Strategy

Every implementation phase must start read-only:

| Phase | Read-Only Scope | Write Scope |
|-------|-----------------|-------------|
| 86C | Scan docs/, classify artifacts | None |
| 86D | Read task contracts, PCAE commands | None |
| 86E | Parse commit log for events | None |
| 86F | Parse decision artifacts for decisions | None |
| 86G | Parse risk-relevant artifacts for risks | None |
| 86H | Compose all layers into snapshot | None |

Write capabilities (if ever needed) would require separate governed phases with explicit
authorization, test coverage, and human approval.

## 11. CLI Surface Roadmap

Proposed future commands (not implemented in 86A):

| Command | Layer | Output | Phase |
|---------|-------|--------|-------|
| `pcae artifact-index [--json]` | 85B | Artifact list with type, status, freshness | 86C |
| `pcae memory-snapshot [--json]` | 85A | Memory entity state | 86D |
| `pcae timeline [--json]` | 85C | Chronological event list | 86E |
| `pcae decision-log [--json]` | 85D | Decision list with status | 86F |
| `pcae risk-register [--json]` | 85E | Risk list with status/severity | 86G |
| `pcae project-state [--json]` | 85F | Full project state snapshot | 86H |
| `pcae project-state explain` | 85F | Human-readable project state | 86H |

All commands are read-only. `--json` required for machine-readable output. No write flags.
No `--execute` flags. No `--approve` flags.

## 12. Data Model Roadmap

86B should define shared Python data models:

| Model | Source Design | Key Fields |
|-------|-------------|------------|
| `ArtifactRecord` | 85B | artifact_id, type, path, status, freshness, evidence_level |
| `MemorySnapshot` | 85A | snapshot_id, current_phase, lifecycle_state, flags, next_actions |
| `GovernanceEvent` | 85C | event_id, type, status, timestamp, source_phase, causality |
| `DecisionEntry` | 85D | decision_id, type, status, scope, maker, provenance |
| `RiskEntry` | 85E | risk_id, type, status, severity, likelihood, exposure |
| `ProjectStateSnapshot` | 85F | snapshot_id, all sections, all fields |

Models should be Pydantic or dataclass-based, matching PCAE's existing patterns.

## 13. Test Strategy

Phase 86 implementation must reintroduce tests after the 84–85 documentation stream.

| Principle | Detail |
|-----------|--------|
| Default command | `python -m pytest -n auto` |
| Serial exceptions | 3 retained (release verification, debugging, compatibility) |
| First implementation phase | Must add tests — no implementation without coverage |
| Read-only before write | Tests verify read-only behavior before any write features |
| Cross-layer consistency | Tests verify memory/artifact/timeline/decision/risk/snapshot agree |
| Forbidden action verification | Tests confirm forbidden actions are never presented as allowed |

### Candidate Test Areas

| Area | Coverage |
|------|----------|
| Artifact classification | Type, status, freshness correctly assigned |
| Artifact freshness | Freshness rules applied per 85B design |
| Source-of-truth precedence | Higher-priority sources override lower |
| Memory field completeness | Required fields present |
| Event ordering | Ordering constraints enforced per 85C |
| Decision status transitions | Lifecycle rules enforced per 85D |
| Risk status transitions | Lifecycle rules enforced per 85E |
| Snapshot answer generation | Queries return correct shape per 85F |
| Stale signal handling | Structural vs substantive correctly classified |
| Dirty worktree detection | Uncommitted changes flagged |
| Origin divergence detection | Unpushed commits flagged |
| No execution authorization | Snapshot never sets execution_authorized=true |
| Idempotent generation | Same input produces same output |

## 14. Migration Strategy

No migration is needed for 86B–86I because:
- No existing machine-readable state is being replaced.
- New commands are additive (they don't modify existing command behavior).
- Existing PCAE commands (health, check, doctor, push, lifecycle) remain unchanged.

If future phases introduce persisted cache, migration should:
- Generate cache from committed artifacts (not migrate from old format).
- Validate generated cache against committed artifacts.
- Never treat cache as authoritative.

## 15. Backward Compatibility Rules

1. Existing PCAE commands must not change behavior.
2. Existing task contract format must not change.
3. Existing PCAE health/check/doctor/push must continue to pass.
4. New commands are additive only.
5. No existing artifact format is modified.
6. No existing test is modified or removed.
7. New tests must not break existing test count parity.

## 16. Governance Gates

| Gate | Purpose | When |
|------|---------|------|
| Design gate | Phase 85 designs reviewed and accepted | Complete (85A–85F) |
| Implementation-plan gate | This roadmap reviewed and accepted | 86A (this phase) |
| Data model gate | Shared data models reviewed before implementation | 86B |
| Read-only prototype gate | First read-only command validated | 86C |
| Cross-layer integration gate | All layers integrated and tested | 86H–86I |
| Write-capable feature gate | Not planned; requires explicit future authorization | Future |
| Permission broker gate | Not planned; requires explicit future authorization | Future |
| Human approval gate | Operator approves each implementation phase | Every phase |
| Commit/push gate | Governed `pcae push` for every implementation commit | Every phase |

## 17. Safety Boundaries

1. Implementation roadmap does not authorize implementation.
2. Implementation roadmap does not authorize source/test changes.
3. Implementation roadmap does not authorize CLI changes.
4. Implementation roadmap does not authorize storage creation.
5. Implementation roadmap does not authorize backend invocation.
6. Implementation roadmap does not authorize adoption.
7. Implementation roadmap does not authorize commit or push outside normal phase completion.
8. Each implementation phase requires its own explicit authorization.
9. Generated outputs must never be committed as authoritative state.
10. Permission broker remains future direction unless explicitly scoped.

## 18. Rollout Phases

| Phase | Deliverable | Tests | Risk Level |
|-------|-------------|-------|------------|
| 86B | Shared data models, storage design | Model validation tests | Low |
| 86C | `pcae artifact-index --json` | Artifact classification tests | Low |
| 86D | `pcae memory-snapshot --json` | Memory field tests | Low |
| 86E | `pcae timeline --json` | Event ordering tests | Medium |
| 86F | `pcae decision-log --json` | Decision status tests | Medium |
| 86G | `pcae risk-register --json` | Risk classification tests | Medium |
| 86H | `pcae project-state --json` | Snapshot composition tests | Medium |
| 86I | Integration test suite | Cross-layer consistency | Low |

Each phase is independently shippable. A failure in 86E does not block 86C or 86D from
being useful.

## 19. Risk Register for Implementation

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Memory treated as authority | high | possible | Read-only principle; no authorization flags from memory |
| Snapshot suggests unsafe action | high | possible | Forbidden-action list always accompanies safe-action list |
| Artifact index misses artifact | medium | possible | Filesystem scan, not hardcoded list |
| Timeline order wrong | medium | possible | Ordering tests with commit timestamp anchors |
| Decision log loses rejection | high | unlikely | Rejection preservation tests |
| Accepted risk treated as mitigated | medium | possible | Separate status values with tests |
| Stale signal misclassified | medium | possible | Explicit classification with evidence requirement |
| Generated cache becomes source of truth | high | unlikely | No cache in MVP; cache regenerable if added |
| Tests skipped for implementation | high | unlikely | Gate: every implementation phase adds tests |
| Permission broker implemented too early | medium | unlikely | Future-direction gate; explicit operator authorization |
| Backward compatibility broken | high | unlikely | Existing test suite must continue passing |

## 20. Open Questions

| # | Question | Decision Scope |
|---|----------|---------------|
| OQ-1 | Should 86B define all six data models or start with artifact-only? | 86B scoping |
| OQ-2 | Should timeline extraction parse git log or rely on committed phase artifacts? | 86E design |
| OQ-3 | Should the snapshot command produce markdown output in addition to JSON? | 86H design |
| OQ-4 | At what point should `.pcae/cache/` be introduced, if ever? | Post-86I evaluation |
| OQ-5 | Should permission broker design be refined before or after Phase 86? | Operator decision |

These questions are documented for future phases to address. They do not block 86A.

---

## 21. Recommended Next Phase

**86B — Phase 85 Data Model and Storage Design**

86B should:
1. Define shared Python data models for the six Phase 85 layers.
2. Decide whether to define all models at once or start with artifact-only.
3. Define storage conventions (command output only vs `.pcae/cache/`).
4. Add model validation tests.
5. Establish the test baseline for the implementation stream.

No 86B task contract is created in 86A.

---

## Roadmap Identity

| Field | Value |
|-------|-------|
| implementation_roadmap_name | phase_85_implementation_roadmap |
| implementation_roadmap_version | 0.1 |
| implementation_roadmap_status | draft_documented |
| implementation_status | not_started |

## Authorization Flags for 86A

| Flag | Value |
|------|-------|
| backend_invocation_performed | false |
| new_prompts_sent | false |
| new_capture_performed | false |
| new_intake_performed | false |
| new_adoption_review_performed | false |
| new_adoption_approval_performed | false |
| new_adoption_execution_performed | false |
| repo_mutation_authorized | true_for_implementation_roadmap_docs_status_only |
| readme_mutation_authorized | false |
| source_mutation_authorized | false |
| test_mutation_authorized | false |
| docs_real_captured_tasks_mutation_authorized | false |
| persistent_memory_implementation_authorized | false |
| artifact_index_implementation_authorized | false |
| timeline_implementation_authorized | false |
| decision_log_implementation_authorized | false |
| risk_register_implementation_authorized | false |
| project_snapshot_implementation_authorized | false |
| permission_broker_implementation_authorized | false |
| shell_gate_implementation_authorized | false |
| storage_implementation_authorized | false |
| cli_implementation_authorized | false |
| phase_86b_task_contract_authorized | false |
| commit_authorized | false |
| push_authorized | false |
| execution_authorized | false |
