# Project Status

## Current Phase

Phase 35R: Governance artifact lifecycle classification.

## Governance Coherence Note

Governance documents are operational artifacts. Stale roadmap references in
PROJECT_STATUS.md, tasks/TODO.md, or CHANGELOG.md create orchestration risk:
agents read them as forward-looking guidance and attempt to implement work
that has already been done. Provenance history, runtime capabilities, and
roadmap guidance must remain coherent. When they drift, run
`pcae status coherence` to surface stale references.

## Current State

PCAE can preview and refresh adoption with init options, generate command,
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
in JSON output; the classifier is deterministic and read-only.

## Next

- No pending governed phases.

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
