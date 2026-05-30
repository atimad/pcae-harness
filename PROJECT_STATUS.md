# Project Status

## Current Phase

Phase 41C: Governed Execution Reporting.

## Governance Coherence Note

Governance documents are operational artifacts. Stale roadmap references in
PROJECT_STATUS.md, tasks/TODO.md, or CHANGELOG.md create orchestration risk:
agents read them as forward-looking guidance and attempt to implement work
that has already been done. Provenance history, runtime capabilities, and
roadmap guidance must remain coherent. When they drift, run
`pcae status coherence` to surface stale references.

## Current State

PCAE can recommend the next governed roadmap phase with `pcae roadmap next`
and `pcae roadmap next --json`, can select a recommended agent for a task
type with `pcae orchestration select TASK_TYPE` and
`pcae orchestration select TASK_TYPE --json`, and can explain that selection
with `pcae orchestration explain TASK_TYPE` and
`pcae orchestration explain TASK_TYPE --json`, using current orchestration
policy and agent registry, and can expose the current governed capability
matrix with `pcae orchestration capabilities` and
`pcae orchestration capabilities --json`, while keeping recommendations
advisory and non-mutating, preview and refresh adoption with init options,
generate command,
architecture, and glossary documentation, generate, inspect, detect drift in,
preview repair for, and repair GitHub Actions governance CI workflows, inspect
repo readiness in human-readable or JSON form, report governance health and
agent lease state in human-readable or JSON form, run checks in human-readable
or JSON form with agent lease state exposed in JSON, report architecture
metrics in human-readable or JSON form, summarize governance trends and risk
in human-readable or JSON form, list available governance pipelines, run or
preview the default governance pipeline in human-readable or JSON form without
dirtying tracked operational state, preview one governance daemon monitoring
cycle, inspect daemon capability status, and preview future daemon watch
behavior with policy-driven intervals in human-readable or JSON form, acquire
and release a local agent session lease with policy-configured stale-lock
status reporting and explicit stale force release, export portable governance
bundles and fleet bundles as local ignored artifacts, preview and restore
approved governance bundle state safely with optional architecture history
merging, trial PCAE adoption against another Git repo in human-readable or
JSON form, apply PCAE onboarding to external Git repos with explicit force,
maintain a local fleet registry of governed repos, remove fleet repos safely,
inspect fleet readiness, detect fleet governance drift, orchestrate fleet-wide
governance apply in dry-run or force mode with optional JSON output, keep
managed pre-commit hooks pointed at `pcae check`, aggregate fleet health in
human-readable or JSON form, manage task lifecycle, validate task scope and
policy with CI-safe exit codes, enforce strict architecture dependency gates,
start or end governed engineering sessions with `pcae session start` and
`pcae session end`, record and read governance provenance attribution events,
automate governed phase lifecycle handoff with `pcae phase complete` and
`pcae phase start`, execute governed handoff automation with `pcae phase
handoff` including governance validation, agent lock transfer, and JSON output,
initialize a fresh governed session with `pcae session bootstrap` including
agent lock acquisition, health/check validation, active task display, current
provenance session, timeline summary, ready status, and JSON output, print
clear manual handoff steps and a copy-ready bootstrap prompt from `pcae phase
handoff` with clear guidance when `--next-agent` is omitted, display
multi-agent restart workflow examples (Claude CLI, Codex Desktop, Generic
governed agent) with a `restart_workflows` field in JSON output, check
PROJECT_STATUS.md for stale roadmap references with `pcae status coherence`
and `pcae status coherence --json`, and resume a governed session idempotently
with `pcae session bootstrap --agent-id <id>` when the same agent already
holds the lock, showing the full governance summary without duplicating
provenance events, and inspect the effective orchestration agent policy with
`pcae orchestration policy` and `pcae orchestration policy --json`, including
configurable `[orchestration]` section in `.pcae/policy.toml` with defaults
for `default_agent`, `documentation_agent`, `runtime_agent`, and
`validation_agent`, and list registered agents and their capabilities with
`pcae orchestration agents` and `pcae orchestration agents --json`, including
configurable `[agents.<id>]` sections in `.pcae/policy.toml` with `kind` and
`roles` fields, defaulting to `claude-local`, `codex-local`, and `pcae-native`
when no agent sections are configured, and recommend the best governed agent for
a work type with `pcae orchestration recommend --work-type TEXT` and
`pcae orchestration recommend --work-type TEXT --json`, matching the work type
against declared agent roles with deterministic fallback to `default_agent`,
and extended `pcae phase handoff` with `--work-type TEXT` to resolve the next
agent from orchestration policy when `--next-agent` is omitted, with
recommendation metadata in both human and JSON output, and generate
governance-aware workflow plans with `pcae orchestration plan --workflow TEXT`
and `pcae orchestration plan --workflow TEXT --json` for the built-in workflows
`documentation`, `implementation`, `validation`, and `release`, with
deterministic fallback for unknown workflows, and preview executable
orchestration workflow steps with `pcae orchestration simulate --workflow TEXT`
and `pcae orchestration simulate --workflow TEXT --json`, showing recommended
agents, work types, reasons, and governance checkpoints without executing work
or changing locks. Orchestration recommendations are advisory and
user-controlled: PCAE remains vendor-neutral and policy-guided, users may
override recommendations or prefer one agent for all work, and future agent
registries may include Claude, Codex, Kimi, DeepSeek, Perplexity, or other
models as capabilities evolve. Workflow coherence can be validated with
`pcae orchestration validate --workflow TEXT` and
`pcae orchestration validate --workflow TEXT --json`, which checks registry
membership, role coverage, deterministic ordering, fallback behavior, and
governance checkpoints without making recommendations mandatory. Phase handoff
guidance can include the same workflow validation with
`pcae phase handoff --workflow TEXT`, including JSON fields for workflow
validity, warnings, and governance checkpoints. Execution readiness can be
previewed with `pcae orchestration readiness --workflow TEXT` and
`pcae orchestration readiness --workflow TEXT --json`, combining workflow
validation, governance checkpoints, registry membership, health/check state,
and session continuity while remaining advisory and non-executing. Lightweight
governance coherence auditing is available with `pcae governance audit` and
`pcae governance audit --json`, checking phase and next-step status, stale
roadmap references, active task readability, session continuity availability,
provenance history presence, policy parsing, and agent registry presence
without mutating governance artifacts or rewriting roadmap files, and
deterministic advisory repair planning can be previewed with
`pcae governance repair --dry-run` and
`pcae governance repair --dry-run --json`, using audit results to report
detected issues, proposed repairs, safety notes, and the advisory reminder
that the user remains authoritative without modifying files, and portable
governed runtime snapshot contents can be previewed with
`pcae runtime snapshot --preview` and
`pcae runtime snapshot --preview --json`, showing active task, agent lock,
session continuity, provenance, orchestration policy, registered agents,
health/check status, and workflow metadata without exporting files, restoring
state, or mutating governance artifacts, and the same governed runtime
snapshot can be exported as portable ignored JSON with
`pcae runtime snapshot export` and `pcae runtime snapshot export --json` under
`.pcae/runtime-snapshots/`, and exported runtime snapshots can be inspected
read-only with `pcae runtime snapshot inspect PATH` and
`pcae runtime snapshot inspect PATH --json`, reporting snapshot validity,
included sections, runtime summary, portability notes, safety notes, and
advisory status without restoring runtime state or mutating files, and
snapshot restore effects can be previewed with
`pcae runtime snapshot restore PATH --dry-run` and
`pcae runtime snapshot restore PATH --dry-run --json`, showing what runtime
sections would and would not be restored while leaving agent locks,
provenance, sessions, history, and files unchanged. Runtime snapshots now
include explicit schema/version governance with `snapshot_schema_version`,
`snapshot_kind`, and `exported_by_version`; inspection and restore preview
report compatibility status and notes, warning clearly for unsupported schema
versions or unknown snapshot kinds without migrations, conversion, or snapshot
mutation. Runtime snapshot compatibility can be analyzed deterministically with
`pcae runtime snapshot compatibility PATH` and
`pcae runtime snapshot compatibility PATH --json`, reporting support level,
snapshot kind, schema version, exporter version visibility, compatibility
checks, compatibility warnings, future-version warnings, required runtime
section presence, and the advisory note that the user remains authoritative
without modifying snapshots, migrating state, or restoring runtime state, and
exported runtime snapshots can be indexed read-only with
`pcae runtime snapshot manifest` and
`pcae runtime snapshot manifest --json`, scanning `.pcae/runtime-snapshots/`
to report snapshot count, latest snapshot, deterministic manifest entries,
compatibility status, support level, compatibility summary counts, and the
advisory note that the user remains authoritative without pruning snapshots,
restoring runtime state, or writing a database, and retention actions can be
previewed with `pcae runtime snapshot retention --dry-run` and
`pcae runtime snapshot retention --dry-run --json`, using the manifest to keep
the latest five snapshots by default and mark older snapshots as prune
candidates while deleting nothing, mutating no manifest, and restoring no
runtime state, and snapshot lineage relationships can be analyzed read-only
with `pcae runtime snapshot lineage` and
`pcae runtime snapshot lineage --json`, ordering snapshots chronologically
by exported_at, grouping compatible snapshots into continuity chains with
previous-snapshot references, recording incompatible snapshots as lineage
breaks, and reporting the latest lineage head without modifying any snapshot
or manifest, and restore safety can be validated read-only with
`pcae runtime snapshot validate-restore PATH` and
`pcae runtime snapshot validate-restore PATH --json`, running nine checks
(compatibility, support level, repo cleanliness, session continuity, active
task presence, policy validity, agent lock safety, lineage continuity, and
governance health) to determine whether a snapshot is safe to restore,
reporting blocking issues that prevent restore, non-blocking warnings, and
the lineage continuity status without restoring runtime state, modifying
agent locks, or mutating provenance, session, or governance artifacts, and
a compact governed context pack for AI agents can be previewed with
`pcae context pack --preview` and `pcae context pack --preview --json`,
reporting active task, scope boundaries (allowed and forbidden files from
the active task contract), governance state (health, check, session
continuity, agent lock), orchestration state (policy summary, registered
agents, default agent, advisory recommendation semantics confirming user
authority), provenance summary (event count, latest event), roadmap summary
(current phase and next items from PROJECT_STATUS.md), fixed operational
rules including phase prompt authority and stale-context suppression,
validation commands, bootstrap and handoff notes, and a universal agent note
confirming the context pack is vendor-neutral and not tailored to any
specific AI agent or provider, without writing files, modifying runtime
state, or weakening governance constraints, and an optional `--profile`
flag selects a work-mode governed context profile (`implementation`,
`documentation`, `validation`, or `handoff`) that adjusts emphasis without
weakening governance constraints; unknown profiles fall back to the balanced
universal profile with a clear warning; JSON output includes `profile_type`
and `emphasized_sections`; profiles optimize by work mode, not by vendor or
model, and `pcae session bootstrap --compact` generates a read-only compact
governed bootstrap prompt suitable for fresh AI sessions, post-auto-compact
recovery, cross-agent handoff, and token-efficient continuity restoration,
embedding active task, governance state, operational rules, validation
commands, stale-context suppression, bootstrap/handoff guidance, and a
vendor-neutral note, with `--profile` for work-mode emphasis and `--json`
for machine-readable output including `bootstrap_prompt`, `profile_type`,
`governance_state`, `operational_rules`, `validation_commands`, and
`advisory` — advisory: "Bootstrap compression reduces token usage without
relaxing governance constraints." and `pcae context export` exports a
compact governed context pack as an ignored local artifact under
`.pcae/context-packs/` (filename `context-pack-YYYYMMDD-HHMMSS.txt`)
reusing the compact bootstrap prompt content, with `--profile` for
work-mode emphasis and `--json` output (fields: `path`, `profile_type`,
`exported_at`); exported files are Git-ignored via `context-packs/` in
`.pcae/.gitignore` and `pcae docs commands` now covers all current CLI command groups
including phase, status, governance, runtime snapshot, orchestration,
context, provenance, session bootstrap, and docs, with `docs/COMMANDS.md`
refreshed to match using `--force`, and `pcae continuity export` exports a
portable governed continuity restore pack as an ignored JSON artifact under
`.pcae/continuity-packs/` (filename `continuity-pack-YYYYMMDD-HHMMSS.json`)
combining runtime snapshot metadata, compact context pack, compact bootstrap
prompt, active task summary, governance state, orchestration state, provenance
summary, operational rules, validation commands, stale-context suppression
rules, bootstrap continuity notes, and a vendor-neutral note; supports
`--profile` for work-mode emphasis and `--json` output (fields: `path`,
`profile_type`, `exported_at`, `included_sections`, `continuity_summary`);
exported packs are Git-ignored via `continuity-packs/` in `.pcae/.gitignore`;
continuity packs are governance-complete, vendor-neutral, portable, and
read-only exports — no automatic restore, prompt injection, remote sync,
telemetry, or runtime mutation, and exported continuity packs can be
inspected read-only with `pcae continuity inspect PATH` and
`pcae continuity inspect PATH --json`, reporting pack validity, exported
timestamp, profile type, included sections, continuity summary (active task,
governance health/check, provenance event count, orchestration default agent,
compact context pack presence, compact bootstrap prompt presence,
stale-context suppression presence, vendor-neutral note presence), portability
notes, safety notes, and the advisory "Continuity pack inspection is advisory;
no runtime state is changed." without restoring runtime state, mutating
continuity packs, or modifying governance artifacts, and continuity pack
compatibility can be analyzed deterministically with
`pcae continuity compatibility PATH` and
`pcae continuity compatibility PATH --json`, running nine checks
(structure validity, required sections presence, governance state presence,
compact bootstrap presence, operational rules presence, stale-context
suppression presence, vendor-neutral note presence, runtime snapshot metadata
compatibility, and future-version warning support) to determine whether a
pack is compatible with the current PCAE runtime, reporting support level
(`supported`, `partially-supported`, or `unsupported`), compatibility checks,
warnings, governance continuity summary, portability summary, and the advisory
"Continuity compatibility analysis is advisory; no runtime state is changed."
without mutating continuity packs, restoring runtime state, or modifying
governance artifacts, and exported continuity packs can be indexed
deterministically with `pcae continuity manifest` and
`pcae continuity manifest --json`, scanning `.pcae/continuity-packs/` to
report pack count, latest pack, deterministic manifest entries (sorted
newest-first by exported_at), and compatibility summary counts; each manifest
entry includes filename, exported_at, profile_type, governance_health,
governance_check, active_task_id, compatibility_status, support_level,
vendor_neutral, stale_context_suppression_present, and compact_bootstrap_present;
the advisory "Continuity manifests are advisory; the user remains authoritative."
is included; the command does not mutate continuity packs, prune packs,
restore runtime state, or modify governance artifacts, and retention actions
for continuity packs can be previewed read-only with
`pcae continuity retention --dry-run` and
`pcae continuity retention --dry-run --json`, using the manifest to keep the
latest five continuity packs and mark older packs as prune candidates while
deleting nothing; human-readable output reports pack count, keep count, prune
candidate count, packs to keep, and prune candidates; JSON output includes
`pack_count`, `keep_count`, `prune_candidate_count`, `keep`, `prune_candidates`,
and `advisory`; the advisory "Continuity retention planning is advisory; no
continuity packs are deleted." is included; the command does not delete
continuity packs, mutate continuity packs, restore runtime state, or modify
governance artifacts, and governance artifact synchronization can be validated
read-only with `pcae governance sync-check` and
`pcae governance sync-check --json`, analyzing PROJECT_STATUS.md,
tasks/TODO.md, CHANGELOG.md, and tasks/DONE.md; stale references are split by
artifact type: operational artifacts (PROJECT_STATUS.md, tasks/TODO.md)
produce `operational_stale_references` which contribute to out-of-sync status,
while historical artifacts (CHANGELOG.md, tasks/DONE.md) produce
`preserved_historical_references` which are displayed but do NOT affect
synchronization status (historical records are preserved by design, not
actionable drift); completed TODO entries (pending items whose `pcae` commands
already appear in DONE.md or CHANGELOG.md), inconsistent roadmap entries (Next
items whose commands already appear in DONE.md), and governance audit
capability gaps are also reported; JSON output includes `synchronized`,
`operational_stale_references`, `preserved_historical_references`,
`completed_todo_entries`, `inconsistent_entries`, `governance_drift_warnings`,
and `advisory`; the advisory "Synchronization analysis is advisory; no
governance artifacts are modified." is included; the command does not mutate
artifacts, auto-repair TODO.md, rewrite PROJECT_STATUS.md, or modify
CHANGELOG.md, and `pcae governance audit` and `pcae governance audit --json`
now include an `artifact_sync_drift` check that runs sync-check analysis
internally, passing with a success message when artifacts are synchronized and
passing with an advisory message when drift issues are present (drift surfaces
as audit warnings via `find_artifact_sync_drift_warnings`, not as failures),
reporting completed TODO entries still listed as pending and inconsistent
roadmap entries as non-blocking warnings while stale references continue on
the existing path without double-counting; adding `artifact_sync_drift` to
`_GOVERNANCE_AUDIT_KNOWN_CHECKS` closes the gap that `pcae governance
sync-check` previously reported; the audit remains read-only: no artifacts
are mutated, no TODO entries are removed, and no governance files are
rewritten, and deterministic repair planning is available with
`pcae governance sync-repair --dry-run` and
`pcae governance sync-repair --dry-run --json` (preview, read-only) and safe
repairs can be applied with `pcae governance sync-repair --force` and
`pcae governance sync-repair --force --json`, which removes only completed
entries from tasks/TODO.md (operational artifacts, proposed action: remove)
while preserving all historical artifacts (CHANGELOG.md, tasks/DONE.md); if
no applicable operational repairs exist, `--force` no-ops clearly and
reports that historical references are preserved as-is; running
`pcae governance sync-repair` without `--dry-run` or `--force` fails with a
clear error directing the user to specify a flag; after `--force`, sync-check
will no longer report the removed entry as a completed TODO entry and
governance audit warnings reduce accordingly, and governance artifact
lifecycle classification is centralized in `classify_governance_artifact` and
`ArtifactClassification` with four explicit classes: operational
(PROJECT_STATUS.md, tasks/TODO.md), historical (CHANGELOG.md, tasks/DONE.md),
runtime (.pcae/provenance-history.json, .pcae/agent-lock.json,
.pcae/session.json), and generated (.pcae/runtime-snapshots/**,
.pcae/context-packs/**, .pcae/continuity-packs/**); `pcae governance
sync-check` and `pcae governance sync-repair` use the classifier for
operational vs. historical vs. runtime vs. generated semantics; runtime and
generated artifacts are explicitly ignored for source governance repair;
`SyncRepairEntry.to_dict()` now exposes `artifact_class` and `governance_role`
in JSON output; the classifier is deterministic and read-only, and the governance artifact
classification registry is exposed as a reusable read-only command with
`pcae governance artifacts` and `pcae governance artifacts --json`, listing
all 10 known governance artifacts with path, artifact_class, governance_role,
repair_policy, and source_control_role grouped by class; JSON output includes
`artifacts`, `classes`, and `advisory`; the registry reuses
`classify_governance_artifact` from Phase 35R and does not mutate artifacts
or change sync-check/sync-repair behavior, and PCAE is now aware of the
agreed high-level roadmap sequence (Option B — Architecture Memory, Option C
— Multi-Agent Collaboration, Remote Coding) and predicted phases for Option B
(36F–36M); `pcae roadmap next` and `pcae roadmap next --json` reference this
planned sequence when no pending TODO items exist, recommending the first
predicted phase (36F Architecture Decision Record model) and surfacing the
full `roadmap_sequence` and `predicted_phases` in output; when TODO items
exist, `predicted_phases` is empty and the first TODO item is recommended as
before; recommendations remain advisory, no tasks are created automatically,
and no runtime state is mutated, and governed Architecture Decision Records
(ADRs) are now a first-class PCAE model with ten fields (decision_id, title,
status, rationale, alternatives_considered, consequences, created_at,
phase_reference, author, contributors), four lifecycle statuses (proposed,
accepted, superseded, deprecated), a `create_adr()` factory that validates
all required fields and rejects unknown statuses, an `is_human_approved`
property reflecting the "accepted" status, human-authority semantics enforced
by requiring a non-empty author, and vendor-neutral contributor support via a
plain string tuple; no CLI commands, persistence, or automatic decision
generation are included in this phase, and governed Architecture Decision Records can be inspected
read-only with `pcae architecture decisions` and
`pcae architecture decisions --json`, listing all decisions with id, title,
status, and phase reference, and with `pcae architecture show DECISION_ID`
and `pcae architecture show DECISION_ID --json`, showing full decision detail
(all ten fields plus `is_human_approved`); unknown decision IDs fail with a
clear error; a deterministic in-memory sample registry provides two decisions
(ADR-0001, ADR-0002) until Phase 36H introduces human-authored persistence;
inspection is read-only and does not mutate any artifacts; the advisory
"Architecture decision inspection is advisory; the user remains authoritative."
is included in all output, and governed Architecture Decision Records can be
created with `pcae architecture add --title TEXT --rationale TEXT --author TEXT`
and persisted as JSON files under `.pcae/architecture/ADR-YYYYMMDD-HHMMSS.json`;
decision IDs are generated sequentially (ADR-0003, ADR-0004, ...) after the
sample registry (ADR-0001, ADR-0002); `--status TEXT` defaults to `accepted`;
`--alternative TEXT`, `--consequence TEXT`, and `--contributor TEXT` are
repeatable; `--phase-reference TEXT` is optional; invalid statuses fail with a
clear error; `pcae architecture decisions` and `pcae architecture show` now
include persisted ADRs; persisted ADR files are ignored by Git via
`.pcae/.gitignore`; human author is required and remains authoritative;
contributors are vendor-neutral string identifiers, and all Architecture
Decision Records (sample + persisted) can be exported as a portable ignored
artifact with `pcae architecture export` and `pcae architecture export --json`
to `.pcae/architecture-exports/architecture-decisions-YYYYMMDD-HHMMSS.json`;
the export includes `exported_at`, `decision_count`, `decisions` (all ten ADR
fields plus `is_human_approved`), `statuses` (per-status count summary), and
`advisory`; export files are Git-ignored via `.pcae/.gitignore`; the command
is read-only and does not mutate any persisted ADR, and governed Architecture
Decision Records can have their status validated with `pcae architecture
validate` and `pcae architecture validate --json`; validation checks the full
registry (sample + persisted) for status integrity issues including duplicate
decision IDs and unknown statuses; the result includes `valid` (bool),
`issues` (list of human-readable strings), `issue_count`, and `advisory`;
exit code is 0 when valid and 1 when issues are found; the command is
read-only and does not mutate any ADR or artifact, and Architecture Decision
Records are now linked to governed phase/provenance context (Phase 36K):
`ArchitectureDecisionRecord` gains two optional fields `commit_reference`
and `provenance_reference` captured at ADR creation time when available;
`add_architecture_decision` records the short HEAD commit SHA via
`git rev-parse --short HEAD` and the timestamp of the latest provenance
event; existing ADRs without these fields load with `None` and remain valid;
`pcae architecture show DECISION_ID` displays an "Architecture linkage"
section (Phase, Commit, Provenance, Contributors, Human approved) in
human-readable output and includes an `architecture_linkage` object in
`--json` output; `pcae architecture decisions --json` includes
`architecture_linkage` in each decision; `build_architecture_linkage(adr)`
returns "unavailable" for absent linkage fields; all inspection operations
remain read-only and do not mutate provenance history or ADR files, and
Architecture Memory is now integrated into compact continuity surfaces
(Phase 36L): `ContextPack` gains an `architecture_memory` field (compact
summary with decision_count, accepted_count, latest_decision, advisory)
populated from the live ADR registry; `build_bootstrap_prompt` adds a
single compact line ("Architecture memory: N decisions (M accepted), latest:
ADR-XXXX"); `ContinuityPack` includes `architecture_memory` in its JSON
export; `pcae context pack --preview` displays an "Architecture memory"
section; `--json` output includes the field; `pcae continuity export --json`
includes `architecture_memory_present` in `continuity_summary`; `pcae
continuity inspect` reports "Architecture memory present:"; a new
"architecture memory" section is added to `CONTINUITY_PACK_INCLUDED_SECTIONS`;
`pcae continuity compatibility` includes an `architecture_memory_presence`
check (advisory; absent packs remain compatible); `architecture_memory` is a
known optional key excluded from future-version warnings; full ADR bodies are
not included in any context or bootstrap output, and Architecture Memory is
now integrated into the governance audit (Phase 36M): `pcae governance audit`
includes an `architecture_memory` check that verifies the ADR registry is
readable, passes validation (no duplicate IDs or unknown statuses), and has
no unparseable persisted ADR files; `GovernanceAuditResult` gains an
`architecture_memory_summary` field (decision_count, accepted_count,
latest_decision, warnings, errors); `pcae governance audit --json` includes
`architecture_memory_summary`; human output shows an "Architecture memory
summary" section; malformed `.pcae/architecture/*.json` files fail the check;
`count_adr_parse_failures(root)` helper detects silently-skipped ADR files;
all operations are read-only, and Architecture Memory session restore is
available as a read-only surface for fresh AI sessions (Phase 36N):
`pcae architecture restore-session` and `--json` generate a compact restore
summary including decision_count, accepted_count, latest_decision (id, title,
status, author, phase_reference, is_human_approved), linkage_summary
(commit_reference, provenance_reference, contributors deduplicated across the
registry, is_human_approved), session_guidance (decision counts including
proposed, advisory notes, inspection commands), and advisory "Architecture
memory restore is advisory; no ADRs are modified."; proposed decisions surface
in session guidance when present; the command is fully read-only, and the multi-agent collaboration
foundation registry is available as a read-only surface (Phase 37A):
`pcae agents` and `pcae agents --json` inspect the built-in multi-agent
registry; each entry includes agent_id, agent_type, role, status,
capabilities, and preferred_workloads; initial agents are claude-local,
codex-local, and pcae-native; human output reports agent count, agent id,
role, and status; JSON output includes agents list with capability
summaries and advisory; the registry is fully read-only, vendor-neutral,
and does not perform automatic delegation, task routing, or remote
execution; the human user remains authoritative, and the multi-agent
registry is expanded with lifecycle states (Phase 37B): four lifecycle
statuses are introduced — declared, configured, available, active —
validated on construction so invalid statuses raise ValueError; three
existing agents (claude-local, codex-local, pcae-native) remain
available; five new vendor-neutral agents (kimi-local, deepseek-local,
gemini-local, grok-local, perplexity-local) are registered as declared,
indicating they are recognized but not yet configured or confirmed for
local use; `pcae agents` human output shows all eight agents with their
lifecycle status and a lifecycle summary line (e.g. available=3,
declared=5); `pcae agents --json` output includes a `lifecycle_summary`
object with per-status counts; declared agents are not executable,
available, or remotely reachable; no API integration, CLI launching,
automatic routing, or availability probing is performed; design remains
vendor-neutral and advisory, and agent configuration and availability
governance is available as read-only inspection (Phase 37C):
`pcae agents show AGENT_ID` and `pcae agents show AGENT_ID --json`
display full metadata for any registered agent (available or declared),
exiting 1 with a clear "Agent not found" message for unknown IDs;
`pcae agents validate` and `pcae agents validate --json` validate
registry consistency, checking for duplicate IDs, invalid lifecycle
statuses, non-empty roles, and that available/active agents have
capabilities and preferred workloads declared; validation reports
Validation status (valid/invalid), errors, warnings, agent count, and
the advisory "Agent configuration validation is advisory; the user
remains authoritative."; exit code is 0 when valid and 1 when errors are
found; all operations are fully read-only with no agent execution, API
integration, CLI launching, automatic routing, or availability probing;
and agent lifecycle state management is available as read-only reporting
(Phase 37D): `pcae agents lifecycle` and `pcae agents lifecycle --json`
report lifecycle state distribution and progression guidance; human
output includes agent count, state distribution (active=N, available=N,
configured=N, declared=N), agents grouped by lifecycle state (agent_id,
agent_type, role), lifecycle progression guidance for each of the four
states (declared → configured → available → active), and the advisory
"Lifecycle reporting is advisory; no agent state is modified."; JSON
output includes lifecycle_summary, agents_by_state, progression_guidance,
validation (valid, errors, warnings), and advisory; validation checks for
duplicate IDs, invalid states, and inconsistent lifecycle metadata
(available/active agents without capabilities or preferred workloads);
all operations are strictly read-only with no agent execution, API
integration, CLI launching, automatic routing, or availability probing;
and agent configuration metadata is exposed as read-only inspection
(Phase 37E): `pcae agents config show AGENT_ID` and
`pcae agents config show AGENT_ID --json` display adapter_type,
configuration_status, executable_hint, requires_manual_setup,
configuration_notes, and lifecycle_status for any registered agent;
unknown agent IDs exit 1 with a clear "Agent not found" message;
adapter types are cli, api, desktop_manual, native, and undeclared;
available agents must not use undeclared adapter; declared future agents
may use undeclared adapter; `pcae agents config validate` and
`pcae agents config validate --json` validate the configuration model
for duplicate IDs, invalid adapter types, and available/active agents
using undeclared adapter; exit code is 0 when valid and 1 when errors
exist; all operations are strictly read-only; and governed collaboration
workflow templates are exposed as read-only inspection (Phase 37F):
`pcae collaboration workflows` and `pcae collaboration workflows --json`
list four deterministic advisory workflow templates — implementation
(implementer → reviewer → validator), documentation
(author → reviewer → validator), architecture
(proposer → reviewer → validator), and handoff
(outgoing_agent → incoming_agent → validator); each step declares
step_name, recommended_agent_role, purpose, and
required_lifecycle_status; handoff.outgoing_agent requires "active",
all other steps require "available"; advisory note confirms no agents
are executed or assigned automatically; all operations are strictly
read-only; and multi-agent handoff history is exposed as read-only
governance reporting (Phase 37G): `pcae collaboration handoffs` and
`pcae collaboration handoffs --json` derive handoff records from
provenance events by scanning for `agent_released` → `agent_acquired`
pairs; each record includes source_agent, target_agent, timestamp,
phase (active task ID), active_task, continuity_verified (True when
acquire immediately follows release), architecture_memory_present (True
when architecture history has entries), summary (from preceding
phase_completed), and warnings for malformed records; records are
ordered most-recent first; all operations are strictly read-only; and
review workflow templates are exposed as read-only governance inspection
(Phase 37H): `pcae collaboration reviews` and
`pcae collaboration reviews --json` list three advisory review workflow
templates — implementation_review (implementer → reviewer → validator),
documentation_review (author → reviewer → validator), and
architecture_review (proposer → reviewer → validator); each step
declares step_name, recommended_agent_role, purpose,
required_lifecycle_status, and review_status (template default
"pending"); four governed review statuses are exposed: pending,
reviewed, validated, rejected; advisory note confirms no agents are
executed or assigned automatically; all operations are strictly
read-only.

PCAE can also discover local CLI runtime capabilities for known agents
with `pcae agents runtime-discover` and `pcae agents runtime-discover
--json` (Phase 38A): probes codex, claude, and kimi CLIs with safe
help/version subcommands; reports installed status, executable path,
version, and twelve capability fields (interactive, non-interactive,
stdin prompt, prompt file, structured output, MCP, hooks, subagents,
remote); detection is conservative — "yes" only when specific keywords
appear in help output, "unknown" otherwise; codex probes include exec,
mcp, and mcp-server subcommands; stdin=DEVNULL and 5-second timeouts
prevent interactive sessions or hangs; missing executables handled
gracefully; all operations are strictly read-only. kimi-local has been
promoted to `available` status with `adapter_type=cli` and
`executable_hint="kimi"` (Phase 38A.1), following confirmed CLI
installation of kimi v0.6.0; non_interactive capability is detected from
"non-interactively" in kimi --help output; all other kimi capabilities
remain unknown pending deterministic evidence; lifecycle summary now
reports available=4, declared=4.

PCAE also exposes a governed agent adapter model with `pcae agents adapters`
and `pcae agents adapters --json` (Phase 38B): each adapter definition
combines static registry configuration (adapter_type, notes) with runtime
discovery results (installed, version, supports_interactive,
supports_non_interactive, supports_mcp, supports_hooks, supports_remote);
`pcae agents adapter show AGENT_ID` inspects a single agent; CLI agents
(codex, claude, kimi) report discovered capabilities; native (pcae-native)
reports installed=true with capabilities unknown; declared agents report
runtime_installed=null with all capabilities unknown; adapter_summary shows
per-type counts; advisory: "Adapter reporting is advisory; no agent runtime
is modified."; all operations are strictly read-only.

PCAE also exposes modular Codex adapter capability inspection with
`pcae agents adapter inspect AGENT_ID` (Phase 38C): each capability is
a `CapabilityRecord` with name, status, source, and notes; `_CAPABILITY_SPECS`
is the single extension point for new Codex capabilities; output separates
discovered (yes) from unknown capabilities; execution_modes derived from
interactive/non_interactive discovery; JSON includes agent_id, adapter_type,
capabilities, execution_modes, executable_path, runtime_version, advisory;
all operations are strictly read-only.

PCAE also exposes an advisory remote autonomous coding execution policy with
`pcae remote policy` and `pcae remote policy --json` (Phase 39B): policy
fields include allowed_agents (claude-local, codex-local, kimi-local),
allowed_adapters (cli), allowed_execution_modes (non_interactive),
approval_required (true), require_clean_git (true), require_pcae_check
(true), require_tests (true), require_human_approval_before_commit (true),
require_human_approval_before_push (true), max_files_changed (null),
max_runtime_minutes (null), and disallowed_operations (delete_branch,
drop_table, force_push, rm_rf); policy is conservative and
approval-based; all operations are strictly read-only with no agent
execution, prompt submission, or runtime state mutation.

PCAE also generates advisory remote autonomous coding execution plans with
`pcae remote plan` and `pcae remote plan --json` (Phase 39C): plans combine
remote policy, runtime discovery, adapter model, and governance state; plan
fields include requested_agent (default: codex-local, overridable via
`--agent`), execution_mode, policy_compliance (agent_allowed,
adapter_allowed, execution_mode_allowed, compliant), required_approvals,
required_checks, safety_notes, blockers, readiness_status (ready/blocked),
and governance_readiness; blockers are generated when the agent is not in
allowed_agents, not installed, adapter not allowed, or the agent does not
support the required execution mode; all operations are strictly read-only
with no agent execution, prompt submission, or runtime state mutation.

PCAE also exposes a read-only remote job definition model with
`pcae remote jobs` and `pcae remote jobs --json` (Phase 39D): the job
schema defines eleven fields — job_id, requested_agent, requested_task,
execution_mode, approval_state, policy_compliance, status, created_at,
required_checks, required_approvals, safety_notes; seven supported
statuses are declared — draft, awaiting_approval, approved, blocked,
ready, completed, failed; the registry is deterministically empty for
this phase with no job creation, execution, or prompt submission; all
operations are strictly read-only.

PCAE also validates remote job definitions with `pcae remote validate` and
`pcae remote validate --json` (Phase 39E): validation checks schema
completeness, status validity, agent and execution mode policy compliance,
required approvals/checks presence, and policy_compliance flag; warnings
are raised for empty required_approvals or required_checks and for
non-compliant policy; blockers for disallowed agents or modes; errors for
missing fields or unsupported statuses; the empty registry validates
cleanly; `validate_remote_job()` and `build_remote_validate()` are
reusable helpers; all operations are strictly read-only.

PCAE also exposes an advisory remote execution approval workflow with
`pcae remote approvals` and `pcae remote approvals --json` (Phase 39F):
four approval states (pending, approved, denied, expired) and three
approval gates (before_execution, before_commit, before_push) are
declared; each gate reports a required flag derived from policy and a
human-readable description; pending approvals are collected from jobs
with approval_state=="pending"; the empty registry has no pending
approvals; no approval mutation, job creation, or agent execution;
all operations are strictly read-only.

PCAE also recommends the best available remote runtime adapter with
`pcae remote adapters` and `pcae remote adapters --json` (Phase 39G):
agents are evaluated from the policy's allowed_agents list; eligibility
requires adapter type in allowed_adapters, installed CLI, and confirmed
non-interactive support; remote=unknown does not block eligibility but
is noted in selection_notes and missing_capabilities; scoring prefers
remote=yes over remote=unknown with deterministic tie-breaking; kimi-local
is represented conservatively with unknown remote capability; all
operations are strictly read-only.

PCAE also exposes an advisory remote execution strategy model with
`pcae remote strategy` and `pcae remote strategy --json` (Phase 39H):
the default strategy is human_selected with preferred_runtime=null,
fallback_runtimes=[], tie_break_rule=null, and human_override=true;
four supported strategies are declared (human_selected,
capability_based, policy_based, registry_order); advisory notes state
that human selection always takes precedence, PCAE must not silently
choose a runtime, recommendations are advisory, and runtime neutrality
is preserved; all operations are strictly read-only.

PCAE introduces the first controlled Remote Autonomous Coding dry run with
`pcae remote dry-run --agent AGENT_ID --prompt TEXT` (Phase 40A):
`--agent` and `--prompt` are required; truly unknown agents exit 1 with
a clear error; known but policy-restricted agents produce a blocked result;
dry-run output includes prompt preview (truncated at 200 chars), policy
compliance, required approvals and checks, adapter capabilities from
runtime discovery, blockers, dry_run_result (would_execute/blocked), and
three safety notes confirming no agent was executed, prompt not submitted,
preview only; all operations are strictly read-only.

PCAE also previews remote job creation with
`pcae remote create --agent AGENT_ID --prompt TEXT --dry-run` (Phase 40B):
`--agent`, `--prompt`, and `--dry-run` are all required; unknown agents
exit 1; job preview includes all 11 job schema fields plus `dry_run: true`,
status=draft, approval_state=pending, and a created_at timestamp; the
preview is validated through `validate_remote_job()` — allowed agents
pass clean, policy-excluded agents produce blocked validation; three safety
notes confirm no persistence, no execution, and preview-only intent;
all operations are strictly read-only, and
`pcae remote create --agent AGENT_ID --prompt TEXT --preview-persist` (Phase 40C)
previews what would be persisted without writing any files or executing agents;
`--preview-persist` is mutually exclusive with `--dry-run` — at least one
must be present; output includes `job_file_path`
(e.g. `.pcae/remote/jobs/job-YYYYMMDD-HHMMSS.json`), `output_directory`
(`.pcae/remote/jobs/`), `job_preview` with all schema fields plus
`persist_preview: true`, and `validation` result; job_id is prefixed `job-`;
three safety notes confirm no job file is written, no agent will be executed,
and preview is for planning only; all operations are strictly read-only, and
`pcae remote create --agent AGENT_ID --prompt TEXT --persist` (Phase 40D)
persists a remote job definition to `.pcae/remote/jobs/` without executing
agents or submitting prompts; unknown agents exit 1; disallowed agents exit 1
with a clear "not allowed" error and create no file; the persisted job contains
exactly the 11 schema fields with status=draft and approval_state=pending; three
safety notes confirm no agent has been executed, no prompt has been submitted,
and human approval is required before any execution; the jobs directory is created
if absent; job files are Git-ignored via `remote/` in `.pcae/.gitignore`; human
output reports job created, job id, selected agent, persisted path, status,
approval state, and advisory "Job persisted. No agent execution has occurred.";
JSON output includes `persisted: true`, `job_path`, `job`, and `advisory`, and
job IDs are collision-proof (Phase 40D.1): job IDs use microsecond precision
(`job-YYYYMMDD-HHMMSS-FFFFFF`); `_generate_unique_job_id(jobs_dir)` loops until
it finds a non-existing path and returns `(job_id, Path)`; `persist_remote_job()`
uses `_generate_unique_job_id` and opens the file with `"x"` (exclusive-create)
mode so no existing file can ever be overwritten; `build_remote_create_persist_preview()`
also uses microsecond format for consistency; the persisted filename always equals
`{job_id}.json`, and persisted jobs can be listed with `pcae remote jobs list`
and `pcae remote jobs list --json` (Phase 40E): reads all `*.json` files from
`.pcae/remote/jobs/`, sorts by filename newest first, skips malformed files with
a warning, and handles a missing directory gracefully; `jobs` is now a subparser
group with a `list` subcommand while the existing `pcae remote jobs` flat
command is preserved; JSON output has `job_count`, `jobs`, `warnings`, and
`advisory`; human output shows job count, per-job id/agent/approval/created-at,
and warnings; `load_persisted_jobs()` added to core; `run_remote_jobs_list()`
added to commands; all operations are strictly read-only; persisted jobs can
be inspected individually with `pcae remote jobs show JOB_ID` and
`pcae remote jobs show JOB_ID --json` (Phase 40F): reads
`.pcae/remote/jobs/<JOB_ID>.json`, exits 1 with a clear error for unknown or
malformed jobs, displays all 11 schema fields in human output, JSON output
has `job` and `advisory`; `inspect_persisted_job(root, job_id)` raises
`ValueError` on error; `run_remote_jobs_show()` added to commands; `show`
subcommand with positional `job_id` wired in CLI; all operations are strictly
read-only; approval state of persisted jobs can be mutated with
`pcae remote approve JOB_ID` and `pcae remote deny JOB_ID` (Phase 40G):
approve sets `approval_state` to `"approved"` and `status` to `"ready"` when
`policy_compliance.compliant` is true, otherwise `"draft"`; deny sets
`approval_state` to `"denied"` and `status` to `"blocked"`; both commands
exit 1 for unknown or malformed jobs; mutation is written back to disk;
no agents are executed; `approve_remote_job()` and `deny_remote_job()` added
to core; `run_remote_approve()` and `run_remote_deny()` added to commands;
`approve` and `deny` subcommands wired in CLI; execution readiness of a
persisted job can be evaluated with `pcae remote ready JOB_ID` (Phase 40H):
runs 13 named checks including job_schema_valid, status_ready,
approval_state_approved, policy_compliance, agent_allowed, adapter_allowed,
execution_mode_allowed, runtime_installed, non_interactive_supported,
git_working_tree_clean, pcae_check_required, tests_required, and
required_approvals_listed; failing hard checks produce blocker messages;
`ready` is True only when blockers list is empty; strictly read-only;
`check_remote_job_readiness(root, job_id)` added to core; `run_remote_ready()`
added to commands; `ready` subcommand wired in CLI; execution can be previewed
with `pcae remote execute JOB_ID --dry-run` (Phase 41A): `--dry-run` is
required (omitting exits 1); calls the readiness gate internally; output
includes `readiness_status`, `prompt_preview` (200 chars), `command_preview`
(derived from `executable_hint` for CLI adapters), `blockers`, `safety_notes`,
and `dry_run_result` (would_execute/blocked); strictly read-only;
`build_remote_execute_dry_run(root, job_id)` added to core;
`run_remote_execute()` added to commands; `execute` subcommand wired in CLI;
real agent invocation under PCAE governance is available with
`pcae remote execute JOB_ID --invoke` (Phase 41B): `--invoke` is mutually
exclusive with `--dry-run`; readiness gate must pass or `ValueError` is raised;
per-agent command dispatch: `claude-local` → `claude --print`, `codex-local`
→ `codex exec --sandbox read-only` (corrected in Phase 41B.1, replacing the
invalid `codex --quiet` that caused `unexpected argument` errors), all others
blocked as "syntax not safely derivable";
agent subprocess captured with 300 s timeout; job status updated to
`"completed"` (rc=0) or `"failed"` (rc≠0) on disk; execution artifact
written to `.pcae/remote/executions/<job_id>_result.json`; `_run_agent_subprocess`
extracted for testability; no commit or push performed;
`invoke_remote_job()` added to core; `_run_remote_execute_invoke()` added to
commands; `--invoke` flag added to CLI.

PCAE also exposes governed execution results for persisted Remote Autonomous
Coding jobs with `pcae remote results JOB_ID` and
`pcae remote results JOB_ID --json` (Phase 41C): reads the persisted job and
any adjacent execution artifact from
`.pcae/remote/executions/<JOB_ID>_result.json`; exits 1 for unknown job IDs;
reports `result_available: false` when no artifact is present; when an
artifact exists, reports `job_id`, `requested_agent`, `command_used`,
`execution_started_at`, `execution_finished_at`, `duration_seconds`,
`exit_code`, `stdout_summary` (first 500 chars), `stderr_summary` (first 200
chars), `output_path`, `final_status`, and `readiness_at_execution` (optional
fields default to null when not recorded); advisory is
"Execution reporting is read-only; no agents are executed."; JSON output
includes `result_available`, `job_id`, `requested_agent`, `execution_result`,
and `advisory`; all operations are strictly read-only with no job mutation,
no agent execution, and no approval state changes.

## Next

- TBD: Future Remote Coding phases (execution history, aggregation, or reporting enhancements).

## Future Explorations

- Automatic low-context detection triggering handoff.
- Compact-risk handoff: trigger `pcae phase handoff` when context compaction risk is high.
- Automatic governed bootstrap: `pcae session bootstrap` invoked on agent initialization.
- Automatic session restoration: replay provenance timeline on agent resume.
- Agent context monitoring: governance-aware context health reporting.
- Automatic AI session restart orchestration triggered by bootstrap.
- True interactive next-agent selection (e.g., from a configured agent roster).
- Auto-detect available agents from lock history or policy configuration.
- Orchestration-aware agent routing based on task type or governance context.
- Heterogeneous agent governance policies (per-agent policy overrides).
- Roadmap/provenance coherence validation: detect when completed features remain in the roadmap.
- Stale roadmap detection: automated scan of governance docs against CHANGELOG/DONE history.
- Governance artifact synchronization: keep PROJECT_STATUS.md, TODO.md, CHANGELOG.md coherent.
- Orchestration narrative validation: verify agent-facing guidance matches runtime capabilities.
- Governance drift detection for documentation artifacts beyond PROJECT_STATUS.md.
