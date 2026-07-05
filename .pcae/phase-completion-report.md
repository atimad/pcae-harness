# Phase 115A Complete — Repository Decision & Explainability Framework

- **Phase ID:** `115A`
- **Status:** completed
- **Report completeness:** complete
- **Missing trust fields:** none
- **Files changed:** 9
- **Tests run:** 15
- **Commits:** 79662071, 676a8063, 6c3e72b8, 2489cba7, dd61dc3b, 2cb43bc8, f4bee1a4
- **Pushed:** pushed
- **origin/main..HEAD:** 0

## Summary

Phase 115A froze the Repository Decision & Explainability Framework. It
defines how PCAE explains why a repository transition is accepted,
rejected, quarantined, or requires human review. Repository Decision
remains a computation, not a fifth Repository State Kernel primitive.

The canonical framework is:

Repository State -> Repository Transition -> Evidence Collection ->
Decision Evaluation -> Transition Result -> Repository Artifact ->
Repository Event.

## Decision Framework

The framework distinguishes Repository State, Evidence, Decision,
Repository Artifact, and Repository Event. Evidence is evaluation-scoped:
it is a first-class architectural concept but not a kernel primitive.
Decision Evaluation remains centralized and deterministic.

## Evidence Architecture

Evidence has Source, Category, Confidence, and Freshness. Evidence must
be deterministic, reproducible, structured, and model-independent.
Evidence examples include Git, Reports, Metadata, Tasks, Architecture,
Runtime, Push State, Notification, Governance, and Tests.

## Repository Skills

Repository Skills are future evidence-only providers. They collect
evidence and never decide, vote, mutate state, authorize transitions,
promote artifacts, send notifications, bypass the validator, invoke
runtime execution, or depend on model identity.

## Explainability Model

Every Transition Result must be explainable with structured fields:
Decision, Reason, Evidence Used, Invariant(s), Severity, Suggested
Repair, and Confidence. No AI-generated prose is required.

## Decision Composition

Skills never vote and never override one another. Conflicting evidence
remains evidence and is evaluated by the centralized Decision Framework.

## Canonical Wire Diagram

The canonical Mermaid diagram is in `docs/PCAE_DECISION_FRAMEWORK.md`:
Repository State -> Evidence Providers -> Evidence -> Decision Framework
-> Transition Validator -> Transition Result -> Repository Artifact ->
Repository Event -> Notification Policy -> Consumers.

## PCAE Architecture Status

*Generated conceptually from canonical project state. Never manually
maintained as runtime state.*

### Completed

- Repository State Kernel review through Phase 114R
- Repository Decision & Explainability Framework through Phase 115A

### Planned

- 115B — Repository Evidence Framework Contract Freeze

### Current Runtime State

- **State:** Observed
- **Maximum Capability:** observe
- **Execution Availability:** unavailable

## Governance Results

- **pcae_health:** healthy
- **pcae_check:** passed
- **pcae_doctor_task_memory:** clean
- **pcae_push_check:** clean
- **pcae_session_bootstrap_compact:** completed
- **pcae_runtime_inspect:** execution unavailable, Observed, observe
- **telegram_runtime:** loaded, configured, enabled

## Test Results

- **focused_decision_explainability_documentation_tests:** 15/15 (passed)
- **report_notification_tests:** present_in_canonical_metadata (present)
- **bootstrap_session_reporting_tests:** present_in_canonical_metadata (present)
- **fast_green:** not_run_documentation_only_no_runtime_code_changed

## No-Go Confirmations

- No runtime implementation.
- No execution capability.
- No Repository Transition Validator changes.
- No Notification Policy changes.
- No lifecycle command changes.
- No Permission Broker changes.
- No plugins.
- No Telegram inbound.
- No REST.
- No Web UI.
- No Dashboard.
- No raw git commit.
- No raw git push.
- No force push.
- No tags.
- No releases.
- No package publication.

## Recommended Next Phase

115B — Repository Evidence Framework Contract Freeze

## Report Consistency

- **Canonical report:** present
- **Metadata:** present
- **Status:** consistent

---
*Report generated for PCAE Phase 115A. Schema version 1.0.*
