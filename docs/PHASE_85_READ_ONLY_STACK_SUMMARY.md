# Phase 85 Read-Only Stack Summary

## 1. Purpose

Document the completed Phase 86 read-only project-intelligence stack, its
commands, safety guarantees, non-authorizing boundary, test coverage,
limitations, and recommended next phase.

## 2. Scope

Summary only. This artifact describes the implemented stack. It does not add
new features, modify source code, create storage, or invoke backends.

## 3. Completed Phase 86 Sequence

| Phase | Deliverable | Tests |
|-------|-------------|-------|
| 86A | Implementation roadmap | 0 (planning) |
| 86B | Data model and storage design | 0 (design) |
| 86C | `pcae artifact-index --json` | 14 |
| 86D | `pcae memory-snapshot --json` | 16 |
| 86E | `pcae governance-timeline --json` | 22 |
| 86F | `pcae decision-log --json` | 28 |
| 86G | `pcae risk-register --json` | 31 |
| 86H | `pcae project-state --json` | 34 |
| 86I | Phase 85 integration tests | 38 |
| 86J | Documentation update | 0 (docs only) |

Total tests added in 86C–86I: 183.
Total test count after 86I: 7122.

## 4. Available Commands

| Command | Purpose |
|---------|---------|
| `pcae artifact-index --json` | Lists governance artifacts with type, path, status, freshness, and commit refs |
| `pcae memory-snapshot --json` | Reports current project memory state: phase, lifecycle, roadmap, sync status |
| `pcae governance-timeline --json` | Extracts ordered governance events from commits, artifacts, and task contracts |
| `pcae decision-log --json` | Extracts decision records with scope, status, and explicit authorization flags |
| `pcae risk-register --json` | Extracts risk records: active, accepted, deferred, stale, must-never-repeat |
| `pcae project-state --json` | Integrates all five layers into a single project-state answer surface |

All commands also support a human-readable text mode when `--json` is omitted.

## 5. Command Output Layers

```
pcae project-state
  |
  +-- pcae artifact-index    (evidence: what exists, where, freshness)
  +-- pcae memory-snapshot    (state: phase, lifecycle, roadmap, sync)
  +-- pcae governance-timeline (history: what happened, when, causality)
  +-- pcae decision-log       (decisions: what was approved/recorded)
  +-- pcae risk-register      (risks: active, accepted, deferred, stale)
```

`pcae project-state` aggregates the lower five layers into an integrated
answer. Layer summary counts are cross-validated by integration tests.

## 6. Read-Only Guarantees

These commands report observed governance state from committed evidence.
They do not grant permission, authorize execution, invoke agents, approve
adoption, permit commits, or permit pushes.

Specifically:

- All commands emit JSON to stdout only
- No files are written during command execution
- No cache files are created
- No `.pcae` storage is created or modified
- No repository files are modified
- Exit 0 on success, nonzero on actual command failure

## 7. Non-Authorizing Boundary

| Guarantee | Enforced |
|-----------|----------|
| Does not authorize execution | yes |
| Does not authorize backend invocation | yes |
| Does not authorize adoption | yes |
| Does not authorize commit or push | yes |
| Does not convert recommendations into authorizations | yes |
| Does not infer authority from output presence | yes |
| Accepted risk is not treated as mitigation | yes |
| Mitigated risk is not invented | yes |
| Next safe actions are recommendations only | yes |

Every command includes explicit safety notes in its JSON output confirming
these boundaries.

## 8. Storage/Cache/.pcae Policy

The Phase 86 read-only stack emits JSON to stdout only. It does not create
generated cache files, committed machine-readable state, or `.pcae` persistent
storage.

Storage, cache, and committed machine-readable state require a future explicit
implementation phase with its own governance gate.

## 9. Test Coverage Summary

Phase 86I added 38 integration tests in `tests/test_phase85_integration.py`.

Full test suite result: `python -m pytest -n auto` — 7122 passed, 0 failures.

Integration tests cover:
- All six commands exit successfully and emit valid JSON
- Common envelope fields (schema_version, source_command, repository_root)
- Cross-layer consistency (project-state counts match lower-layer counts)
- Evidence artifact paths match artifact index
- Active/accepted/stale risk IDs match risk register
- No-write behavior (no cache/state/.pcae created, no repo mutation)
- No authority inference across all commands
- Accepted-risk separation from active risk
- Stale-signal visibility
- Must-never-repeat visibility
- Next-safe-actions are recommendations only
- High-risk authorization booleans false
- Deterministic counts across runs

## 10. Integration Guarantees

| Check | Verified |
|-------|----------|
| project-state artifact_index record_count matches | yes |
| project-state timeline event_count matches | yes |
| project-state decision_log decision_count matches | yes |
| project-state risk_register risk_count matches | yes |
| project-state evidence_artifacts = artifact-index current paths | yes |
| project-state active_risks = risk-register active risk IDs | yes |
| project-state accepted_risks = risk-register accepted risk IDs | yes |
| project-state stale_signals = risk-register stale_signal risk IDs | yes |

## 11. What PCAE Can Now Answer

From committed evidence, using the read-only stack:

- **What phase are we in?** — `pcae project-state` or `pcae memory-snapshot`
- **What was approved or recorded?** — `pcae decision-log`
- **What is blocked?** — `pcae project-state` (active_blockers)
- **What is deferred?** — `pcae project-state` (active_deferred_items) or `pcae risk-register`
- **What was rejected?** — `pcae project-state` (active_rejected_items)
- **What risk was accepted?** — `pcae risk-register` or `pcae project-state` (accepted_risks)
- **What can be safely done next?** — `pcae project-state` (next_safe_actions, recommendation only)
- **What actions remain forbidden?** — `pcae project-state` (forbidden_actions)
- **What must never be repeated?** — `pcae risk-register` or `pcae project-state` (must_never_repeat_controls)
- **What evidence supports the answer?** — `pcae artifact-index` or `pcae project-state` (evidence_artifacts)

## 12. What PCAE Still Cannot Do

- **Execute commands on behalf of agents.** The read-only stack reports state; it does not perform actions.
- **Act as a permission broker.** Permission broker / shell gate is future direction, not implemented.
- **Create persistent storage.** No committed machine-readable state, no .pcae storage, no generated cache.
- **Replace human approval.** Human review remains required for execution, adoption, commit, and push.
- **Replace lifecycle gates.** The read-only stack does not perform lifecycle gate execution.
- **Guarantee real-time accuracy.** Output reflects committed state at generation time; it may be stale.

## 13. Known Limitations

- Project-state health/check/doctor/push fields are `"unknown"` (not run inline)
- Timeline event extraction uses regex on git commit messages
- Decision log extracts boundary decisions, not fine-grained prose decisions
- Risk register uses a standing catalog, not dynamic artifact-prose extraction
- Integration tests run via subprocess, adding runtime overhead
- Cross-layer checks validate count/ID equality, not deep field consistency

## 14. Recommended Next Phase

**86K — Phase 86 Read-Only Stack Final Verification.**

Before moving into Phase 87 or permission/storage work, run one final
verification phase to confirm docs, commands, integration tests, health,
push status, and no storage/cache artifacts.

---

read_only_stack_summary_name=phase_85_read_only_stack_summary
read_only_stack_summary_version=0.1
read_only_stack_summary_status=documented
commands_implemented=6
total_tests=7122
integration_tests=38
phases_completed=86A_through_86J
read_only=true
storage_created=false
cache_created=false
pcae_storage_created=false
authorization_inference=false
backend_invocation_performed=false
phase_85_implementation_complete=true
