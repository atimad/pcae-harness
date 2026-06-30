# Phase 95F.1 — Phase Report Skill Discovery and Authoring Protocol Design

```
phase_name    = phase_95f1_phase_report_skill_discovery_and_authoring_protocol_design
phase_version = 1.0
phase_status  = completed
implementation_status = discovery/planning_only
recommended_next_phase = 95F.2 — Phase Report Authoring Skill and Completeness Enforcement
```

## 1. Executive Conclusion

**A Phase Report Authoring Skill should be added.** It should be mandatory for phase finalization. But **a skill alone is not sufficient** — the report-completeness validator must also be strengthened to check individual governance and test result keys, not just dict presence.

**Recommendation**: Combined 95F.2 implementing both the skill AND completeness enforcement.

## 2. Current Skill Inventory

Discovered 6 skills at `.pcae/skills/`, each with a `SKILL.md` file:

| Skill ID | Type | Purpose | Mechanism | Auto? |
|----------|------|---------|-----------|-------|
| `capability-analysis` | analysis | Capability analysis | CLI invoke | Prompt-convention |
| `phase-agent` | agent | Render full agent prompt package | CLI invoke | Prompt-convention |
| `phase-implementation` | implementation | Implement one governed PCAE phase | CLI invoke | Prompt-convention |
| `phase-validation` | validation | Render validation prompt | CLI invoke | Prompt-convention |
| `roadmap-analysis` | analysis | Roadmap analysis | CLI invoke | Prompt-convention |
| `task-transition` | workflow | Task transition planning | CLI invoke | Prompt-convention |

**No skill exists for phase report authoring or finalization.**

## 3. Current Skill System Behavior

- **Location**: `.pcae/skills/<skill-id>/SKILL.md`
- **Loader**: `src/pcae/commands/agent.py` — `build_skill_system_foundation()`, `_write_skill_registry_md()`
- **Registry**: `docs/SKILL_REGISTRY.md` (generated, not hand-written)
- **Auto-discovery**: No. Claude does not auto-discover skills.
- **PCAE invocation**: `pcae skill invoke <skill-id> <phase_id>` renders a prompt
- **Prompt-convention**: Skills are used because phase prompts instruct Claude to use them. They are not auto-loaded or enforced.
- **Versioning**: Yes — `1.0.0` per skill with `skill_version` field
- **Tests**: Minimal — skill rendering is tested but skill enforcement is not

## 4. Phase Report Failure Pattern

Recurring failures across multiple phases:

| Phase | Failure |
|-------|---------|
| 94T/94T.1 | Stale metadata from 94Q reused verbatim |
| 95B | Partial — missing trust fields (files_changed, tests_run, ...) |
| 95C | Complete status despite only 2 of 5 governance results present |
| 95E | Missing regression evidence (report/notification, bootstrap, fast-green) |
| 95F | Partial — missing trust fields |

**Root causes**:
1. No mandatory protocol for writing `.pcae/phase-completion-metadata.json`
2. `assess_completeness()` checks `governance_results` dict presence but NOT individual keys
3. `assess_completeness()` checks `test_results` dict presence but NOT specific suites
4. The terminal summary is often correct but metadata JSON is hand-crafted and error-prone
5. No skill exists to guide the operator/agent through the required fields

## 5. Proposed Phase Report Authoring Skill

### Location

`.pcae/skills/phase-finalization/SKILL.md` (consistent with existing skill location pattern)

### Skill Structure

Following the existing SKILL.md format:

```markdown
# Skill

## Skill ID
phase-finalization

## Skill Name
Phase Finalization and Report Authoring

## Skill Type
workflow

## Purpose
Guide the operator through writing complete .pcae/phase-completion-metadata.json
before running pcae phase complete. Enforce all mandatory trust fields.

## Required Metadata Fields
(phase_id, phase_name, status, files_changed, tests_added_or_updated, ...)

## Required Governance Evidence
(pcae_health, pcae_check, pcae_doctor_task_memory, pcae_push_check, telegram_runtime)

## Required Test Evidence
(backend_model_tests, backend_cli_tests, report_notification_tests, 
 bootstrap_session_reporting_tests, fast_green)

## Required Output Fields
(no_go_confirmation, full no_go_confirmed dict with all 20+ items,
 notification_dispatch_result, recommended_next_phase)

## Workflow
1. Verify phase_id matches the completing phase — never reuse stale metadata
2. Run all required validation suites before writing metadata
3. Write .pcae/phase-completion-metadata.json with all mandatory fields
4. Verify governance_results dict has all 5 required keys
5. Verify test_results dict has all applicable test suites
6. Verify no_go_confirmed dict has all 20+ required confirmations
7. Verify recommended_next_phase points forward, not backward
8. Run pcae phase complete
9. Verify pcae phase-report show --latest shows complete ✅
```

## 6. Proposed Completeness Enforcement

### Current Gap

`assess_completeness()` at `phase_reports.py:122` checks:
- `governance_results` is non-empty dict → passes
- `test_results` is non-empty dict → passes
- Does NOT check individual keys within these dicts

### Minimum Change

Add `_REQUIRED_GOVERNANCE_KEYS` and `_REQUIRED_TEST_SUITE_KEYS` constants:

```python
_REQUIRED_GOVERNANCE_KEYS: frozenset[str] = frozenset({
    "pcae_health", "pcae_check", "pcae_doctor_task_memory",
    "pcae_push_check", "telegram_runtime",
})
```

In `assess_completeness()`, after checking dict presence, also check that all required governance keys exist. Missing keys → `missing_trust_fields` → `partial`.

### Report Completeness States After Fix

| State | Condition |
|-------|-----------|
| **complete** | All fatal + non-fatal fields present, all required governance keys present, all required test suite keys present |
| **partial** | Fatal fields present but governance or test keys missing |
| **incomplete** | Fatal fields missing |

## 7. Recommended Next Phase

**95F.2 — Phase Report Authoring Skill and Completeness Enforcement**

Combined phase that:
1. Creates `.pcae/skills/phase-finalization/SKILL.md`
2. Strengthens `assess_completeness()` with key-level validation
3. Adds tests for the new completeness checks
4. Verifies that a report with only `pcae_health`/`pcae_check` (missing the other 3 governance keys) is marked `partial`

Do NOT implement real backend invocation or start 95G.

---
*Phase 95F.1 is discovery/planning only. No skill was created. No code was changed.*
