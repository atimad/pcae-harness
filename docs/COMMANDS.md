# PCAE Command Reference

Commands are organized by capability area. All commands that have a `--json` variant are listed with both forms. Run `pcae <command> --help` for detailed usage.

**Capability Areas:**

- [Core Governance](#core-governance) — health, check, inspect
- [Task and Session Management](#task-and-session-management) — task, session, phase, status
- [Provenance and Architecture](#provenance-and-architecture) — provenance, architecture, analytics
- [Export, Fleet, and Infrastructure](#export-fleet-and-infrastructure) — export/import, repo, fleet, pipeline, daemon, agent, ci, docs
- [Orchestration](#orchestration) — orchestration, context
- [Design and Prototype Scaffolds](#design-and-prototype-scaffolds) — early design phases
- [Roadmap and Prompt Governance](#roadmap-and-prompt-governance) — roadmap generation, prompt governance
- [Execution Governance Activation (69A–69P)](#execution-governance-activation-69a69p) — approval, authorization, audit, activation, sandboxing, change capture, promotion, rollback, traceability
- [Invocation Governance Scaffolds (Pre-Activation Design)](#invocation-governance-scaffolds-pre-activation-design) — pre-69A invocation lifecycle scaffolds
- [Runtime and Invocation Governance](#runtime-and-invocation-governance) — runtime trust, read-only invocation, multi-agent pilots
- [Governance State and Invariants](#governance-state-and-invariants) — governance state audit, invariants, drift, lock governance
- [Controlled Write Governance (50A–50K)](#controlled-write-governance-50a50k) — write authorization chain
- [Controlled Execution Orchestration (51A–51K)](#controlled-execution-orchestration-51a51k) — execution orchestration chain
- [Recovery Planning (52A–52E)](#recovery-planning-52a52e) — task, session, governance, lock, corruption recovery
- [Runtime Hardening (52F–52I)](#runtime-hardening-52f52i) — contract, sandbox, timeout, output integrity
- [Concurrency and Multi-Agent Coordination (52J–52M)](#concurrency-and-multi-agent-coordination-52j52m) — concurrency safety, coordination, conflict resolution
- [Chaos Engineering and Resilience (52N–52Q)](#chaos-engineering-and-resilience-52n52q) — chaos testing, failure injection, corruption simulation, recovery validation
- [Runtime Integration (54A+)](#runtime-integration-54a) — runtime integration readiness
- [Capability and Roadmap Intelligence (64B Series)](#capability-and-roadmap-intelligence-64b-series) — capability inventory, roadmap/prompt/skill intelligence
- [Strategic Governance and Independent Review (65A–68D)](#strategic-governance-and-independent-review-65a68d) — strategic roadmap governance, write-invocation approval gateway, independent review, IRG challenge

---

# Core Governance

## init

- `pcae init --dry-run`
- `pcae init --force`

## health

- `pcae health`
- `pcae health --json`

## check

- `pcae check`
- `pcae check --json`

## inspect

- `pcae inspect`
- `pcae inspect --json`

---

# Task and Session Management

## task

- `pcae task new "<title>"`
- `pcae task list`
- `pcae task show`
- `pcae task update`
- `pcae task pause`
- `pcae task resume`
- `pcae task complete`
- `pcae task close [task-id]`
- `pcae task transition`
- `pcae task transition --next "<task title>"`
- `pcae task transition --json`

## session

- `pcae session start`
- `pcae session read`
- `pcae session write`
- `pcae session update`
- `pcae session end`
- `pcae session bootstrap --agent-id <id>`
- `pcae session bootstrap --agent-id <id> --json`

## phase

- `pcae phase start --agent-id <id>`
- `pcae phase complete --summary "<text>"`
- `pcae phase handoff --summary "<text>" --next-agent <id>`
- `pcae phase handoff --summary "<text>" --work-type <type>`
- `pcae phase handoff --summary "<text>" --workflow <name>`
- `pcae phase handoff --json`

## status

- `pcae status coherence`
- `pcae status coherence --json`

## governance

- `pcae governance audit`
- `pcae governance audit --json`
- `pcae governance repair --dry-run`
- `pcae governance repair --dry-run --json`

## runtime

- `pcae runtime snapshot --preview`
- `pcae runtime snapshot --preview --json`
- `pcae runtime snapshot export`
- `pcae runtime snapshot export --json`
- `pcae runtime snapshot inspect <path>`
- `pcae runtime snapshot inspect <path> --json`
- `pcae runtime snapshot restore <path> --dry-run`
- `pcae runtime snapshot restore <path> --dry-run --json`
- `pcae runtime snapshot compatibility <path>`
- `pcae runtime snapshot compatibility <path> --json`
- `pcae runtime snapshot manifest`
- `pcae runtime snapshot manifest --json`
- `pcae runtime snapshot retention --dry-run`
- `pcae runtime snapshot retention --dry-run --json`
- `pcae runtime snapshot lineage`
- `pcae runtime snapshot lineage --json`
- `pcae runtime snapshot validate-restore <path>`
- `pcae runtime snapshot validate-restore <path> --json`

---

# Orchestration

## orchestration

- `pcae orchestration policy`
- `pcae orchestration policy --json`
- `pcae orchestration agents`
- `pcae orchestration agents --json`
- `pcae orchestration capabilities`
- `pcae orchestration capabilities --json`
- `pcae orchestration select <task_type>`
- `pcae orchestration select <task_type> --json`
- `pcae orchestration explain <task_type>`
- `pcae orchestration explain <task_type> --json`
- `pcae orchestration recommend --work-type <type>`
- `pcae orchestration recommend --work-type <type> --json`
- `pcae orchestration plan --workflow <name>`
- `pcae orchestration plan --workflow <name> --json`
- `pcae orchestration simulate --workflow <name>`
- `pcae orchestration simulate --workflow <name> --json`
- `pcae orchestration validate --workflow <name>`
- `pcae orchestration validate --workflow <name> --json`
- `pcae orchestration readiness --workflow <name>`
- `pcae orchestration readiness --workflow <name> --json`

## context

- `pcae context pack --preview`
- `pcae context pack --preview --json`

---

# Provenance and Architecture

## provenance

- `pcae provenance status`
- `pcae provenance history`
- `pcae provenance history --json`
- `pcae provenance history --event-type <type>`
- `pcae provenance history --agent-id <id>`
- `pcae provenance timeline`
- `pcae provenance timeline --json`
- `pcae provenance sessions`
- `pcae provenance sessions --json`
- `pcae provenance session current`
- `pcae provenance session current --json`
- `pcae provenance record --event-type <type> --summary "<text>"`
- `pcae provenance export`
- `pcae provenance export --json`

## architecture

- `pcae architecture snapshot`
- `pcae architecture history`
- `pcae architecture metrics`
- `pcae architecture metrics --json`

## analytics

- `pcae analytics trends`
- `pcae analytics trends --json`
- `pcae analytics risk`
- `pcae analytics risk --json`

---

# Export, Fleet, and Infrastructure

## export/import

- `pcae export bundle`
- `pcae import bundle <bundle.json> --dry-run`
- `pcae import bundle <bundle.json>`
- `pcae import bundle <bundle.json> --merge-history`

## repo

- `pcae repo trial <path> --dry-run`
- `pcae repo trial <path> --dry-run --json`
- `pcae repo apply <path> --dry-run`
- `pcae repo apply <path> --force`

## fleet

- `pcae fleet add <path>`
- `pcae fleet list`
- `pcae fleet remove <path>`
- `pcae fleet health`
- `pcae fleet health --json`
- `pcae fleet inspect`
- `pcae fleet inspect --json`
- `pcae fleet drift`
- `pcae fleet drift --json`
- `pcae fleet apply --dry-run`
- `pcae fleet apply --force`
- `pcae fleet export`

## pipeline

- `pcae pipeline list`
- `pcae pipeline list --json`
- `pcae pipeline run`
- `pcae pipeline run default`
- `pcae pipeline run --dry-run`
- `pcae pipeline run --json`

## daemon

- `pcae daemon run --dry-run`
- `pcae daemon run --dry-run --json`
- `pcae daemon status`
- `pcae daemon status --json`
- `pcae daemon watch --dry-run`
- `pcae daemon watch --dry-run --json`

## agent

- `pcae agent acquire --agent-id <id>`
- `pcae agent release --agent-id <id>`
- `pcae agent release --agent-id <id> --force-stale`
- `pcae agent status`
- `pcae agent status --json`

## ci

- `pcae ci generate github --dry-run`
- `pcae ci generate github`
- `pcae ci generate github --force`
- `pcae ci status`
- `pcae ci status --json`
- `pcae ci drift`
- `pcae ci drift --json`
- `pcae ci repair --dry-run`
- `pcae ci repair --force`

## docs

- `pcae docs commands --dry-run`
- `pcae docs commands --force`
- `pcae docs architecture --dry-run`
- `pcae docs architecture --force`
- `pcae docs glossary --dry-run`
- `pcae docs glossary --force`

## hooks

- `pcae hooks install`

## remote

- `pcae remote status`
- `pcae remote status --json`
- `pcae remote adapters`
- `pcae remote adapters --json`

---

# Design and Prototype Scaffolds

## planning-execution-design

- `pcae planning-execution-design`
- `pcae planning-execution-design --json`

## execution-framework-design

- `pcae execution-framework-design`
- `pcae execution-framework-design --json`

## adapter-design

- `pcae adapter-design`
- `pcae adapter-design --json`

## invocation-design

- `pcae invocation-design`
- `pcae invocation-design --json`

## real-planning-design

- `pcae real-planning-design`
- `pcae real-planning-design --json`

## consensus-execution-design

- `pcae consensus-execution-design`
- `pcae consensus-execution-design --json`

## runtime-execution-prototype

- `pcae runtime-execution-prototype`
- `pcae runtime-execution-prototype --json`

## planner-adapter-prototype

- `pcae planner-adapter-prototype`
- `pcae planner-adapter-prototype --json`

## multi-agent-prototype

- `pcae multi-agent-prototype`
- `pcae multi-agent-prototype --json`

## consensus-prototype

- `pcae consensus-prototype`
- `pcae consensus-prototype --json`

## invocation-pilot

- `pcae invocation-pilot`
- `pcae invocation-pilot --json`

## multi-runtime-pilot

- `pcae multi-runtime-pilot`
- `pcae multi-runtime-pilot --json`

## consensus-runtime-pilot

- `pcae consensus-runtime-pilot`
- `pcae consensus-runtime-pilot --json`

## governed-execution-dry-run

- `pcae governed-execution-dry-run`
- `pcae governed-execution-dry-run --json`

## invocation-contracts

- `pcae invocation-contracts`
- `pcae invocation-contracts --json`

## execution-readiness

- `pcae execution-readiness`
- `pcae execution-readiness --json`

## adapter-registry-design

- `pcae adapter-registry-design`
- `pcae adapter-registry-design --json`

## collaboration-design

- `pcae collaboration-design`
- `pcae collaboration-design --json`

## orchestration-design

- `pcae orchestration-design`
- `pcae orchestration-design --json`

## coordinator-design

- `pcae coordinator-design`
- `pcae coordinator-design --json`

## parallel-execution-design

- `pcae parallel-execution-design`
- `pcae parallel-execution-design --json`

## planning-prototype-design

- `pcae planning-prototype-design`
- `pcae planning-prototype-design --json`

## planning-dry-run

- `pcae planning-dry-run`
- `pcae planning-dry-run --json`

---

# Roadmap and Prompt Governance

## roadmap-generation-design

- `pcae roadmap-generation-design`
- `pcae roadmap-generation-design --json`

## roadmap-evidence

- `pcae roadmap-evidence`
- `pcae roadmap-evidence --json`

## roadmap-proposal-dry-run

- `pcae roadmap-proposal-dry-run`
- `pcae roadmap-proposal-dry-run --json`

## multi-agent-roadmap

- `pcae multi-agent-roadmap`
- `pcae multi-agent-roadmap --json`

## roadmap-approval-design

- `pcae roadmap-approval-design`
- `pcae roadmap-approval-design --json`

## prompt-generation-design

- `pcae prompt-generation-design`
- `pcae prompt-generation-design --json`

## adaptive-prompt-design

- `pcae adaptive-prompt-design`
- `pcae adaptive-prompt-design --json`

## prompt-validation-design

- `pcae prompt-validation-design`
- `pcae prompt-validation-design --json`

## prompt-governance-design

- `pcae prompt-governance-design`
- `pcae prompt-governance-design --json`

## prompt-artifact-design

- `pcae prompt-artifact-design`
- `pcae prompt-artifact-design --json`

## prompt-approval-design

- `pcae prompt-approval-design`
- `pcae prompt-approval-design --json`

## autonomous-phase-proposal

- `pcae autonomous-phase-proposal`
- `pcae autonomous-phase-proposal --json`

## autonomous-prompt-proposal

- `pcae autonomous-prompt-proposal`
- `pcae autonomous-prompt-proposal --json`

## prompt-render

- `pcae prompt-render`
- `pcae prompt-render --json`

## prompt-execution-readiness

- `pcae prompt-execution-readiness`
- `pcae prompt-execution-readiness --json`

## prompt-execution-dry-run

- `pcae prompt-execution-dry-run`
- `pcae prompt-execution-dry-run --json`

---

# Execution Governance Activation (69A–69P)

The governed execution chain implemented end to end: approval, authorization,
audit, activation, result classification, sandboxed execution, change
capture, human promotion review, governed promotion to root, and governed
rollback. `execution_allowed` remains `False` throughout this entire chain,
including for `pcae promote` and `pcae rollback`. Those two commands are the
only ones in PCAE's history that mutate the root repository, and they do so
only through explicit human invocation gated on prior human-reviewed
evidence (an EPR with `promotion_authorized=True` for promotion; a PER with
`rollback_payload_available=True` for rollback) — never through automatic or
AI-driven invocation.

## approval-store

- `pcae approval-store write --prompt-id <id> --approved-by <human> --approved-agent <id>`
- `pcae approval-store write --prompt-id <id> --approved-by <human> --approved-agent <id> --json`
- `pcae approval-store show --prompt-id <id>`
- `pcae approval-store show --prompt-id <id> --json`
- `pcae approval-store list`
- `pcae approval-store list --json`

## invocation-contract-validation

- `pcae invocation-contract-validation --prompt-id <id> --selected-agent <id>`
- `pcae invocation-contract-validation --prompt-id <id> --selected-agent <id> --json`

## execution-pathway-integration

- `pcae execution-pathway-integration --prompt-id <id> --selected-agent <id>`
- `pcae execution-pathway-integration --prompt-id <id> --selected-agent <id> --json`

## authorization-store

- `pcae authorization-store write --prompt-id <id> --authorized-by <human> --selected-agent <id>`
- `pcae authorization-store write --prompt-id <id> --authorized-by <human> --selected-agent <id> --json`
- `pcae authorization-store show --prompt-id <id>`
- `pcae authorization-store show --prompt-id <id> --json`
- `pcae authorization-store list`
- `pcae authorization-store list --json`
- `pcae authorization-store list --prompt-id <id>`
- `pcae authorization-store list --prompt-id <id> --json`

## audit-record

- `pcae audit-record create --authorization-id <id> --prompt-id <id>`
- `pcae audit-record create --authorization-id <id> --prompt-id <id> --json`
- `pcae audit-record show --audit-id <id>`
- `pcae audit-record show --audit-id <id> --json`
- `pcae audit-record list --prompt-id <id>`
- `pcae audit-record list --authorization-id <id>`
- `pcae audit-record list --prompt-id <id> --json`

## review

- `pcae review execution-governance-readiness`
- `pcae review execution-governance-readiness --json`

## execution-activation

- `pcae execution-activation invoke --prompt-id <id> --authorization-id <id> --audit-id <id>`
- `pcae execution-activation invoke --prompt-id <id> --authorization-id <id> --audit-id <id> --json`
- `pcae execution-activation show --result-id <id>`
- `pcae execution-activation show --result-id <id> --json`
- `pcae execution-activation list --prompt-id <id>`
- `pcae execution-activation list --prompt-id <id> --json`

## execution-result-governance

- `pcae execution-result-governance --result-id <id>`
- `pcae execution-result-governance --result-id <id> --json`

## result-review

- `pcae result-review create --result-id <id> --reviewer <name> --disposition <value>`
- `pcae result-review create --result-id <id> --reviewer <name> --disposition <value> --json`
- `pcae result-review show --review-id <id>`
- `pcae result-review show --review-id <id> --json`
- `pcae result-review list --result-id <id>`
- `pcae result-review list --result-id <id> --json`
- `pcae result-review list-open`
- `pcae result-review list-open --json`

## execution-snapshot

- `pcae execution-snapshot create --prompt-id <id> --authorization-id <id> --audit-id <id>`
- `pcae execution-snapshot create --prompt-id <id> --authorization-id <id> --audit-id <id> --json`
- `pcae execution-snapshot show --snapshot-id <id>`
- `pcae execution-snapshot show --snapshot-id <id> --json`
- `pcae execution-snapshot list --prompt-id <id>`
- `pcae execution-snapshot list --prompt-id <id> --json`

## execution-change

- `pcae execution-change compare --snapshot-id <id> --result-id <id>`
- `pcae execution-change compare --snapshot-id <id> --result-id <id> --json`
- `pcae execution-change show --change-id <id>`
- `pcae execution-change show --change-id <id> --json`
- `pcae execution-change list`
- `pcae execution-change list --prompt-id <id> --json`
- `pcae execution-change list-candidates`
- `pcae execution-change list-candidates --json`

## execution-change-package

- `pcae execution-change-package show --ecp-id <id>`
- `pcae execution-change-package show --ecp-id <id> --json`
- `pcae execution-change-package list --prompt-id <id>`
- `pcae execution-change-package list --prompt-id <id> --json`

## promotion-review

- `pcae promotion-review create --ecp-id <id> --reviewed-by <human> --disposition <disposition>`
- `pcae promotion-review create --ecp-id <id> --reviewed-by <human> --disposition <disposition> --approved-path <path> --json`
- `pcae promotion-review show --epr-id <id>`
- `pcae promotion-review show --epr-id <id> --json`
- `pcae promotion-review list --ecp-id <id>`
- `pcae promotion-review list --ecp-id <id> --json`
- `pcae promotion-review list --prompt-id <id>`
- `pcae promotion-review list --prompt-id <id> --json`

## promote

- `pcae promote --epr-id <id>`
- `pcae promote --epr-id <id> --dry-run`
- `pcae promote --epr-id <id> --json`

## promotion-execution

- `pcae promotion-execution show --per-id <id>`
- `pcae promotion-execution show --per-id <id> --json`
- `pcae promotion-execution list --epr-id <id>`
- `pcae promotion-execution list --epr-id <id> --json`
- `pcae promotion-execution list --prompt-id <id>`
- `pcae promotion-execution list --prompt-id <id> --json`
- `pcae promotion-execution mark-interrupted --per-id <id>`
- `pcae promotion-execution mark-interrupted --per-id <id> --json`

## rollback

- `pcae rollback --per-id <id>`
- `pcae rollback --per-id <id> --dry-run`
- `pcae rollback --per-id <id> --json`

## rollback-execution

- `pcae rollback-execution show --rer-id <id>`
- `pcae rollback-execution show --rer-id <id> --json`
- `pcae rollback-execution list --per-id <id>`
- `pcae rollback-execution list --per-id <id> --json`
- `pcae rollback-execution list --prompt-id <id>`
- `pcae rollback-execution list --prompt-id <id> --json`
- `pcae rollback-execution mark-interrupted --rer-id <id>`
- `pcae rollback-execution mark-interrupted --rer-id <id> --json`

## exec

- `pcae exec status --prompt-id <id>`
- `pcae exec status --prompt-id <id> --json`

## doctor

- `pcae doctor execution-chain`
- `pcae doctor execution-chain --json`
- `pcae doctor execution-chain --prompt-id <id>`
- `pcae doctor execution-chain --prompt-id <id> --json`

---

# Invocation Governance Scaffolds (Pre-Activation Design)

Earlier scaffold and pilot commands that predate the 69A–69O execution
activation chain above. These remain advisory readiness/design reports;
none of them invoke a runtime or write files.

## human-agent-execution-design

- `pcae human-agent-execution-design`
- `pcae human-agent-execution-design --json`

## governed-execution-pilot

- `pcae governed-execution-pilot`
- `pcae governed-execution-pilot --json`

## live-execution-readiness

- `pcae live-execution-readiness`
- `pcae live-execution-readiness --json`

## execution-audit-design

- `pcae execution-audit-design`
- `pcae execution-audit-design --json`

## execution-consensus-design

- `pcae execution-consensus-design`
- `pcae execution-consensus-design --json`

## live-execution-pilot

- `pcae live-execution-pilot`
- `pcae live-execution-pilot --json`

## invocation-workload-validation

- `pcae invocation-workload-validation`
- `pcae invocation-workload-validation --json`

## execution-authorization-design

- `pcae execution-authorization-design`
- `pcae execution-authorization-design --json`

## read-only-invocation-pilot

- `pcae read-only-invocation-pilot`
- `pcae read-only-invocation-pilot --json`

## execution-result-review-design

- `pcae execution-result-review-design`
- `pcae execution-result-review-design --json`

## authorization-expiration-design

- `pcae authorization-expiration-design`
- `pcae authorization-expiration-design --json`

## invocation-pilot-status

- `pcae invocation-pilot-status`
- `pcae invocation-pilot-status --json`

## multi-agent-invocation-pilot

- `pcae multi-agent-invocation-pilot`
- `pcae multi-agent-invocation-pilot --json`

## execution-quality-design

- `pcae execution-quality-design`
- `pcae execution-quality-design --json`

## read-only-invocation-execution-pilot

- `pcae read-only-invocation-execution-pilot`
- `pcae read-only-invocation-execution-pilot --json`

## write-invocation-design

- `pcae write-invocation-design`
- `pcae write-invocation-design --json`

## write-preflight-dry-run

- `pcae write-preflight-dry-run`
- `pcae write-preflight-dry-run --json`

## write-candidate-design

- `pcae write-candidate-design`
- `pcae write-candidate-design --json`

## write-invocation-pilot

- `pcae write-invocation-pilot`
- `pcae write-invocation-pilot --json`

## multi-agent-readonly-pilot

- `pcae multi-agent-readonly-pilot`
- `pcae multi-agent-readonly-pilot --json`

## consensus-engine

- `pcae consensus-engine`
- `pcae consensus-engine --json`

## arbitration

- `pcae arbitration`
- `pcae arbitration --json`

## evidence-framework

- `pcae evidence-framework`
- `pcae evidence-framework --json`

## decision-record

- `pcae decision-record`
- `pcae decision-record --json`

## capability-registry

- `pcae capability-registry`
- `pcae capability-registry --json`

## capability-discovery

- `pcae capability-discovery`
- `pcae capability-discovery --json`

## capability-validation

- `pcae capability-validation`
- `pcae capability-validation --json`

## collaboration

- `pcae collaboration workflows`
- `pcae collaboration workflows --json`
- `pcae collaboration handoffs`
- `pcae collaboration handoffs --json`
- `pcae collaboration reviews`
- `pcae collaboration reviews --json`

## write-result-review-design

- `pcae write-result-review-design`
- `pcae write-result-review-design --json`

## write-rollback-validation-design

- `pcae write-rollback-validation-design`
- `pcae write-rollback-validation-design --json`

## write-execution-readiness

- `pcae write-execution-readiness`
- `pcae write-execution-readiness --json`

## write-rollback-dry-run

- `pcae write-rollback-dry-run`
- `pcae write-rollback-dry-run --json`

## live-readonly-readiness

- `pcae live-readonly-readiness`
- `pcae live-readonly-readiness --json`

## live-write-readiness

- `pcae live-write-readiness`
- `pcae live-write-readiness --json`

## live-readonly-pilot

- `pcae live-readonly-pilot`
- `pcae live-readonly-pilot --json`

## rollback-execution-pilot

- `pcae rollback-execution-pilot`
- `pcae rollback-execution-pilot --json`

## live-write-pilot

- `pcae live-write-pilot`
- `pcae live-write-pilot --json`

---

# Runtime and Invocation Governance

## runtime-contracts

- `pcae runtime-contracts`
- `pcae runtime-contracts --json`

## governance-audit

- `pcae governance-audit`
- `pcae governance-audit --json`

## runtime-trust

- `pcae runtime-trust`
- `pcae runtime-trust --json`

## governance-maturity

- `pcae governance-maturity`
- `pcae governance-maturity --json`

## readonly-invocation

- `pcae readonly-invocation`
- `pcae readonly-invocation --json`

## invocation-result-capture

- `pcae invocation-result-capture`
- `pcae invocation-result-capture --json`

## runtime-contract-enforcement

- `pcae runtime-contract-enforcement`
- `pcae runtime-contract-enforcement --json`

## invocation-authorization-enforcement

- `pcae invocation-authorization-enforcement`
- `pcae invocation-authorization-enforcement --json`

## invocation-audit

- `pcae invocation-audit`
- `pcae invocation-audit --json`

## readonly-runtime-pilot

- `pcae readonly-runtime-pilot`
- `pcae readonly-runtime-pilot --json`

## invocation-result-review

- `pcae invocation-result-review`
- `pcae invocation-result-review --json`

## invocation-evidence

- `pcae invocation-evidence`
- `pcae invocation-evidence --json`

## multi-agent-governance-audit

- `pcae multi-agent-governance-audit`
- `pcae multi-agent-governance-audit --json`

---

# Governance State and Invariants

## governance-state-audit

- `pcae governance-state-audit`
- `pcae governance-state-audit --json`

## governance-state-repair

- `pcae governance-state-repair`
- `pcae governance-state-repair --json`

## task-transition-governance

- `pcae task-transition-governance`
- `pcae task-transition-governance --json`

## session-continuity-governance

- `pcae session-continuity-governance`
- `pcae session-continuity-governance --json`

## governance-invariants

- `pcae governance-invariants`
- `pcae governance-invariants --json`

## runtime-safety-invariants

- `pcae runtime-safety-invariants`
- `pcae runtime-safety-invariants --json`

## governance-drift

- `pcae governance-drift`
- `pcae governance-drift --json`

## governance-drift-review

- `pcae governance-drift-review`
- `pcae governance-drift-review --json`

## agent-lock-governance

- `pcae agent-lock-governance`
- `pcae agent-lock-governance --json`

## agent-lock-conflicts

- `pcae agent-lock-conflicts`
- `pcae agent-lock-conflicts --json`

## governance-recovery-plan

- `pcae governance-recovery-plan`
- `pcae governance-recovery-plan --json`

---

# Controlled Write Governance (50A–50K)

## write-authorization

- `pcae write-authorization`
- `pcae write-authorization --json`

## write-authorization-review

- `pcae write-authorization-review`
- `pcae write-authorization-review --json`

## write-authorization-decision

- `pcae write-authorization-decision`
- `pcae write-authorization-decision --json`

## write-authorization-lifecycle

- `pcae write-authorization-lifecycle`
- `pcae write-authorization-lifecycle --json`

## write-plan

- `pcae write-plan`
- `pcae write-plan --json`

## write-readiness

- `pcae write-readiness`
- `pcae write-readiness --json`

## write-evidence

- `pcae write-evidence`
- `pcae write-evidence --json`

## write-audit

- `pcae write-audit`
- `pcae write-audit --json`

## write-rollback-verification

- `pcae write-rollback-verification`
- `pcae write-rollback-verification --json`

## write-governance-audit

- `pcae write-governance-audit`
- `pcae write-governance-audit --json`

## write-recommendation

- `pcae write-recommendation`
- `pcae write-recommendation --json`

---

# Controlled Execution Orchestration (51A–51K)

## execution-request

- `pcae execution-request`
- `pcae execution-request --json`

## execution-review

- `pcae execution-review`
- `pcae execution-review --json`

## execution-decision

- `pcae execution-decision`
- `pcae execution-decision --json`

## execution-lifecycle

- `pcae execution-lifecycle`
- `pcae execution-lifecycle --json`

## execution-plan

- `pcae execution-plan`
- `pcae execution-plan --json`

## execution-readiness-assessment

- `pcae execution-readiness-assessment`
- `pcae execution-readiness-assessment --json`

## execution-evidence

- `pcae execution-evidence`
- `pcae execution-evidence --json`

## execution-audit

- `pcae execution-audit`
- `pcae execution-audit --json`

## execution-rollback-verification

- `pcae execution-rollback-verification`
- `pcae execution-rollback-verification --json`

## execution-governance-audit

- `pcae execution-governance-audit`
- `pcae execution-governance-audit --json`

## execution-recommendation

- `pcae execution-recommendation`
- `pcae execution-recommendation --json`

---

# Recovery Planning (52A–52E)

## task-lifecycle-hardening

- `pcae task-lifecycle-hardening`
- `pcae task-lifecycle-hardening --json`

## session-recovery

- `pcae session-recovery`
- `pcae session-recovery --json`

## governance-state-recovery

- `pcae governance-state-recovery`
- `pcae governance-state-recovery --json`

## agent-lock-recovery

- `pcae agent-lock-recovery`
- `pcae agent-lock-recovery --json`

## corruption-recovery

- `pcae corruption-recovery`
- `pcae corruption-recovery --json`

---

# Runtime Hardening (52F–52I)

## runtime-contract-hardening

- `pcae runtime-contract-hardening`
- `pcae runtime-contract-hardening --json`

## sandbox-hardening

- `pcae sandbox-hardening`
- `pcae sandbox-hardening --json`

## timeout-hardening

- `pcae timeout-hardening`
- `pcae timeout-hardening --json`

## output-integrity-verification

- `pcae output-integrity-verification`
- `pcae output-integrity-verification --json`

---

# Concurrency and Multi-Agent Coordination (52J–52M)

## concurrency-safety

- `pcae concurrency-safety`
- `pcae concurrency-safety --json`

## parallel-agent-coordination

- `pcae parallel-agent-coordination`
- `pcae parallel-agent-coordination --json`

## multi-agent-state-consistency

- `pcae multi-agent-state-consistency`
- `pcae multi-agent-state-consistency --json`

## conflict-resolution-engine

- `pcae conflict-resolution-engine`
- `pcae conflict-resolution-engine --json`

---

# Chaos Engineering and Resilience (52N–52Q)

## chaos-testing

- `pcae chaos-testing`
- `pcae chaos-testing --json`

## failure-injection

- `pcae failure-injection`
- `pcae failure-injection --json`

## corruption-simulation

- `pcae corruption-simulation`
- `pcae corruption-simulation --json`

## recovery-validation

- `pcae recovery-validation`
- `pcae recovery-validation --json`

---

# Runtime Integration (54A+)

## runtime-integration-readiness

- `pcae runtime-integration-readiness`
- `pcae runtime-integration-readiness --json`

## read-only-runtime-invocation

- `pcae read-only-runtime-invocation`
- `pcae read-only-runtime-invocation --json`

## runtime-output-persistence

- `pcae runtime-output-persistence`
- `pcae runtime-output-persistence --json`

## runtime-output-review

- `pcae runtime-output-review`
- `pcae runtime-output-review --json`

## multi-agent-read-only-execution

- `pcae multi-agent-read-only-execution`
- `pcae multi-agent-read-only-execution --json`

## controlled-write-dry-run

- `pcae controlled-write-dry-run`
- `pcae controlled-write-dry-run --json`

## single-file-write-pilot

- `pcae single-file-write-pilot`
- `pcae single-file-write-pilot --json`

## runtime-registry

- `pcae runtime-registry`
- `pcae runtime-registry --json`

## runtime-discovery

- `pcae runtime-discovery`
- `pcae runtime-discovery --json`

## runtime-capability-inventory

- `pcae runtime-capability-inventory`
- `pcae runtime-capability-inventory --json`

## runtime-trust-model

- `pcae runtime-trust-model`
- `pcae runtime-trust-model --json`

## task-lifecycle-governance

- `pcae task-lifecycle-governance`
- `pcae task-lifecycle-governance --json`

## agent-handoff-modernization

- `pcae agent-handoff-modernization`
- `pcae agent-handoff-modernization --json`

## roadmap-continuity

- `pcae roadmap-continuity`
- `pcae roadmap-continuity --json`

## handoff-state-refresh

- `pcae handoff-state-refresh`
- `pcae handoff-state-refresh --json`

## phase-test-selection

- `pcae phase-test-selection`
- `pcae phase-test-selection --json`

## runtime-execution-pilot

- `pcae runtime-execution-pilot`
- `pcae runtime-execution-pilot --json`

## runtime-output-capture

- `pcae runtime-output-capture`
- `pcae runtime-output-capture --json`

## runtime-audit-persistence

- `pcae runtime-audit-persistence`
- `pcae runtime-audit-persistence --json`

## runtime-review-workflow

- `pcae runtime-review-workflow`
- `pcae runtime-review-workflow --json`

## task-state-alignment

- `pcae task-state-alignment`
- `pcae task-state-alignment --json`

## runtime-review-decision

- `pcae runtime-review-decision`
- `pcae runtime-review-decision --json`

## runtime-approval-gates

- `pcae runtime-approval-gates`
- `pcae runtime-approval-gates --json`

## runtime-rollback-boundaries

- `pcae runtime-rollback-boundaries`
- `pcae runtime-rollback-boundaries --json`

## multi-runtime-registry

- `pcae multi-runtime-registry`
- `pcae multi-runtime-registry --json`

## runtime-selection-engine

- `pcae runtime-selection-engine`
- `pcae runtime-selection-engine --json`

## runtime-arbitration

- `pcae runtime-arbitration`
- `pcae runtime-arbitration --json`

## multi-runtime-audit-chain

- `pcae multi-runtime-audit-chain`
- `pcae multi-runtime-audit-chain --json`

## runtime-failure-recovery

- `pcae runtime-failure-recovery`
- `pcae runtime-failure-recovery --json`

## runtime-quarantine

- `pcae runtime-quarantine`
- `pcae runtime-quarantine --json`

## multi-runtime-execution-planning

- `pcae multi-runtime-execution-planning`
- `pcae multi-runtime-execution-planning --json`

## multi-runtime-execution-readiness

- `pcae multi-runtime-execution-readiness`
- `pcae multi-runtime-execution-readiness --json`

## multi-runtime-orchestration-execution

- `pcae multi-runtime-orchestration-execution`
- `pcae multi-runtime-orchestration-execution --json`

## runtime-coordination-policy

- `pcae runtime-coordination-policy`
- `pcae runtime-coordination-policy --json`

## orchestration-audit-model

- `pcae orchestration-audit-model`
- `pcae orchestration-audit-model --json`

## orchestration-readiness-gate

- `pcae orchestration-readiness-gate`
- `pcae orchestration-readiness-gate --json`

---

# Capability and Roadmap Intelligence (64B Series)

## capability-inventory

- `pcae capability-inventory`
- `pcae capability-inventory --json`

## capability list

- `pcae capability list`
- `pcae capability list --json`

## capability show

- `pcae capability show <capability_id>`
- `pcae capability show <capability_id> --json`

## capability dependencies

- `pcae capability dependencies`
- `pcae capability dependencies --json`

## roadmap current

- `pcae roadmap current`
- `pcae roadmap current --json`

## roadmap tracks

- `pcae roadmap tracks`
- `pcae roadmap tracks --json`

## roadmap evolution

- `pcae roadmap evolution`
- `pcae roadmap evolution --json`

## prompt next

- `pcae prompt next`
- `pcae prompt next --json`

## prompt phase

- `pcae prompt phase <phase_id>`
- `pcae prompt phase <phase_id> --json`

## prompt validate

- `pcae prompt validate`
- `pcae prompt validate --json`

## skill list

- `pcae skill list`
- `pcae skill list --json`

## skill show

- `pcae skill show <skill_id>`
- `pcae skill show <skill_id> --json`

## skill validate

- `pcae skill validate`
- `pcae skill validate --json`

## skill invoke

- `pcae skill invoke <skill_id>`
- `pcae skill invoke <skill_id> --json`

---

# Strategic Governance and Independent Review (65A–68D)

## roadmap-recommendation-hardening

- `pcae roadmap-recommendation-hardening`
- `pcae roadmap-recommendation-hardening --json`

## strategic-roadmap-governance

- `pcae strategic-roadmap-governance`
- `pcae strategic-roadmap-governance --json`

## strategic-state-summary

- `pcae strategic-state-summary`
- `pcae strategic-state-summary --json`

## mapping-review-governance

- `pcae mapping-review-governance`
- `pcae mapping-review-governance --json`

## governed-write-invocation-design

- `pcae governed-write-invocation-design`
- `pcae governed-write-invocation-design --json`

## governed-write-invocation-candidate

- `pcae governed-write-invocation-candidate`
- `pcae governed-write-invocation-candidate --json`

## write-invocation-approval-gateway

- `pcae write-invocation-approval-gateway`
- `pcae write-invocation-approval-gateway --json`

## independent-review-governance

- `pcae independent-review-governance`
- `pcae independent-review-governance --json`

## strategic-review-governance

- `pcae strategic-review-governance`
- `pcae strategic-review-governance --json`
- `pcae strategic-review-governance --refresh`

## objective-coverage-hardening

- `pcae objective-coverage-hardening`
- `pcae objective-coverage-hardening --json`

## irg-challenge

- `pcae irg-challenge`
- `pcae irg-challenge --json`
- `pcae irg-challenge --impact`
- `pcae irg-challenge --impact --json`

## strategic-continuity

- `pcae strategic-continuity show current`
- `pcae strategic-continuity show current --json`
- `pcae strategic-continuity history`
- `pcae strategic-continuity history --json`
- `pcae strategic-continuity validate`
- `pcae strategic-continuity validate --json`

## preflight scope

- `pcae preflight scope --requested-action ACTION`
- `pcae preflight scope --json --requested-action ACTION`
- `pcae preflight scope --json --requested-action ACTION --requested-file PATH`
- `pcae preflight scope --json --requested-action ACTION --requested-file PATH --requested-file PATH`

## preflight backend

- `pcae preflight backend --requested-backend BACKEND --requested-action ACTION`
- `pcae preflight backend --json --requested-backend BACKEND --requested-action ACTION`
- `pcae preflight backend --json --requested-backend BACKEND --requested-action ACTION --prompt-present`
- `pcae preflight backend --json --requested-backend BACKEND --requested-action ACTION --prompt-present --prompt-hash HASH`
- `pcae preflight backend --json --requested-backend BACKEND --requested-action ACTION --requested-file PATH --prompt-present --prompt-hash HASH`

## preflight mutation

- `pcae preflight mutation --requested-action ACTION`
- `pcae preflight mutation --json --requested-action ACTION`
- `pcae preflight mutation --json --requested-action ACTION --requested-file PATH`
- `pcae preflight mutation --json --requested-action ACTION --captured-output-present --captured-output-hash HASH`
- `pcae preflight mutation --json --requested-action ACTION --adoption-review-present --adoption-approval-present`
- `pcae preflight mutation --json --requested-action ACTION --requested-file PATH --source-backend BACKEND`

## preflight commit

- `pcae preflight commit`
- `pcae preflight commit --json`
- `pcae preflight commit --json --commit-message MSG --diff-present --tests-present --tests-passed --pcae-check-passed --pcae-health-passed --doctor-passed`

## preflight push

- `pcae preflight push`
- `pcae preflight push --json`
- `pcae preflight push --json --push-target TARGET --push-check-passed --tests-present --tests-passed --pcae-check-passed --pcae-health-passed --doctor-passed`
- `pcae preflight push --json --raw-git-push-requested`
- `pcae preflight push --json --force-push-requested`
