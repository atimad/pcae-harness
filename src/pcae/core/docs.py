from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pcae.core.paths import HarnessPath


COMMANDS_RELATIVE_PATH = Path("docs") / "COMMANDS.md"
ARCHITECTURE_RELATIVE_PATH = Path("docs") / "ARCHITECTURE.md"
GLOSSARY_RELATIVE_PATH = Path("docs") / "GLOSSARY.md"


@dataclass(frozen=True)
class DocsGenerateResult:
    relative_path: Path
    created: bool
    overwritten: bool


def render_commands_reference() -> str:
    return """# PCAE Command Reference

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
"""


def generate_commands_reference(
    root: HarnessPath,
    force: bool = False,
) -> DocsGenerateResult:
    return write_docs_artifact(
        root,
        COMMANDS_RELATIVE_PATH,
        render_commands_reference(),
        force,
    )


def render_architecture_overview() -> str:
    return """# PCAE Architecture Overview

## Motivation

AI coding agents can produce real changes to real repositories — commits, pushes, file rewrites — with no approval gate, no audit trail, and no rollback plan. A single unconstrained invocation can leave a codebase in an inconsistent state with no recorded path back to a known-good one.

PCAE exists to put a governed, evidence-producing boundary around that process: every step from "a human approved this prompt" to "this content was written to root" to "this write was reversed" is a structured, append-only artifact, not an unrecorded side effect. The system does not make AI execution safe by trusting the agent; it makes it governable by recording what was authorized, what was attempted, what changed, who reviewed it, and what was actually written or reverted — and by refusing to proceed when that evidence is missing.

## Governance Principles

- **Human approval is authoritative.** No prompt is invoked, no content is promoted to root, and no promotion is rolled back without an explicit human decision recorded in an artifact.
- **Evidence before action.** Every stage in the chain is gated on the prior stage's artifact existing and being in an eligible state. A missing or ineligible artifact blocks outright; it is never inferred or assumed.
- **Failure is never silent.** Where a post-execution step (such as evidence capture) can fail, the failure itself is recorded as a stored, inspectable artifact rather than discarded.
- **Mutation is the exception, not the default.** Of PCAE's entire command surface, exactly two commands mutate the root repository — `pcae promote` and `pcae rollback` — and both require prior human-reviewed evidence (an EPR or a PER) before they will act.
- **Idempotency over retry magic.** Promotion and rollback are safe to re-run against the same evidence: already-applied or already-reverted paths are skipped and recorded as such, never re-written, with no separate `--resume` flag.
- **Divergence blocks, it does not guess.** If root has changed since the evidence was captured, the entire promotion or rollback attempt is aborted before any file is touched. There is no automatic conflict resolution.
- **Approval, activation, commit, and push are distinct decisions.** Implementing a capability does not make it active; activating a phase does not authorize a commit; authorizing a commit does not authorize a push. Each is a separate human decision (see [Current Limitations](#current-limitations)).
- **No silent roadmap advancement.** The roadmap's authoritative phase registry (`_CRI_KNOWN_PHASES`) requires exactly one active phase at all times; this is enforced as a blocking `pcae check` condition, not a convention.

## Artifact Model

PCAE's execution governance is a chain of structured artifacts. Each one gates the next; none of them invoke an AI runtime or write to root except where stated.

| Artifact | Name | Phase | Store | Role |
|---|---|---|---|---|
| **APA** | Approved Prompt Artifact | 69B | `.pcae/approvals/` | Records that a specific prompt + agent combination has been explicitly human-approved before any invocation is considered. |
| **ARA** | Authorization Record | 69E | `.pcae/authorizations/` | Records that an approved, contract-validated invocation has been explicitly authorized to proceed. |
| **EAR** | Execution Audit Record | 69F | `.pcae/audit/` | Append-only audit trail entry created for every invocation attempt, regardless of outcome. |
| **ESA** | Execution Snapshot Artifact | 69J | `.pcae/execution-snapshots/` | Captures git working-tree state at a point in time, used as the before/after reference for change detection. |
| **ERR** | Execution Result Record | 69G | `.pcae/results/` | The structured outcome of an invocation attempt (technical status, captured output), classified by `pcae execution-result-governance`. |
| **ECR** | Execution Change Record | 69J | `.pcae/execution-changes/` | The set of file-level changes detected between two ESAs, classified by severity and rollback-candidacy. Captures which paths changed, not their content. |
| **ECP** | Execution Change Package | 69M | `.pcae/execution-packages/` | Full evidentiary capture of sandbox-produced content: per-file diffs, before/after content, and SHA-256 hashes, captured immediately before the sandbox is destroyed. Closes the gap left by ECR capturing paths but not content. |
| **EPR** | Execution Promotion Review | 69M | `.pcae/promotion-reviews/` | A human's explicit content-level review of a specific ECP, with partial-path approval support and a separate `promotion_authorized` flag. |
| **PER** | Promotion Execution Record | 69N | `.pcae/promotion-executions/` | Durable record of an actual write to the root repository, created before the first file write and persisted after every file. The first artifact where root mutation actually occurs. |
| **RER** | Rollback Execution Record | 69O | `.pcae/rollback-executions/` | Durable record of an actual reversal of a PER's writes, using the originating ECP's before-content and hashes as evidence. The first artifact whose subject is reversing a root mutation. |

The canonical chain, in the order evidence is produced for a single governed invocation:

```
APA -> ARA -> EAR -> ESA -> ERR/ECR -> ECP -> EPR -> PER -> RER
```

A companion artifact, **ERRA** (Execution Result Review Artifact, Phase 69I, `.pcae/result-reviews/`), records a human's disposition on an ERR's outcome (e.g. `acceptable_for_context`, `needs_follow_up`). It is distinct from EPR: ERRA reviews whether an execution's outcome was acceptable; EPR reviews whether specific captured content should be promoted to root. Neither ERRA's review nor any disposition on it authorizes execution, retry, rollback, commit, or push — those boundaries are stated explicitly in `_ERRA_GOVERNANCE_BOUNDARIES`.

## Execution Lifecycle

The path from an approved prompt to a classified result, run inside an isolated workspace:

1. **Approval** (69B) — a human approves a specific prompt/agent pair, producing an APA.
2. **Contract and pathway validation** (69C–69D) — invocation contracts and runtime contracts for the selected agent are validated; all required gates are evaluated together into a single `authorization_status`.
3. **Authorization** (69E) — an ARA is recorded for the specific invocation.
4. **Audit** (69F) — an EAR is created for the attempt before it proceeds.
5. **Activation** (69G) — `pcae execution-activation invoke` runs the invocation inside a sandboxed workspace (Phase 69L: a `git worktree` + `rsync` overlay, not the root checkout), producing an ERR.
6. **Result governance** (69H) — the ERR is classified along technical status, governance attention, and severity axes.
7. **Snapshot and change detection** (69J–69K) — ESAs taken before and after the attempt are diffed into an ECR, with automatic snapshot integration removing the need for a manual snapshot step.
8. **Result review** (69I) — a human records a disposition on the ERR as an ERRA.

At every one of these steps, `execution_allowed` is hard-coded `False`. No command in this lifecycle invokes a real AI runtime against the live root checkout, and none of them write to root.

## Promotion Lifecycle

Promotion is what turns sandboxed, reviewed content into a root-repository write:

1. **Change capture** (69M) — immediately before the sandbox is destroyed, an ECP captures every changed file's diff, before/after content, and hashes. Hard exclusions (`.git/`, `.pcae/`, external symlink escapes) can never be overridden; default exclusions (toolchain artifacts, gitignored files, oversized binaries) can be reviewed per-path.
2. **Promotion review** (69M) — a human reviews the ECP and records an EPR: a disposition (`approved`/`rejected`/`deferred`/`escalated`/`cancelled`), optionally a partial set of `approved_paths`, and a separate `promotion_authorized` flag that nothing before 69N consumes.
3. **Promotion execution** (69N) — `pcae promote --epr-id <id>` is the first command in PCAE's history that mutates root. It is gated strictly on `EPR.promotion_authorized=True`, never on an ECP alone. For each eligible path it performs a three-way divergence check against the current root content (`pending` / `already_applied` / `conflict`); any conflict aborts the entire attempt before any file is touched. A PER is created with `status="in_progress"` before the first write and persisted after every file, so an interrupted promotion is always a stored, inspectable record, and a second `pcae promote` against the same EPR resumes safely (`already_applied` paths are skipped, not re-written).

`execution_allowed` remains `False` through promotion. `pcae promote` does not invoke a runtime; it writes content that a human already reviewed and authorized in the EPR.

## Rollback Lifecycle

Rollback is the mirror image of promotion, reversing a specific promotion's writes using evidence captured during that promotion — never user-specified paths, never a range of PERs:

1. **Eligibility gate** — `pcae rollback --per-id <id>` is refused outright unless the target PER has `status` in `{completed, partial}` and `rollback_payload_available=True`. No RER is created on refusal.
2. **Plan derivation** — the rollback's file plan is derived strictly from `PER.file_results` where `outcome="success"`; `already_applied` entries from the original promotion are excluded, since those paths were never written by the PER being rolled back.
3. **Divergence check (inverted from promotion)** — a path whose current root hash matches the PER's `after_hash` is `pending` (still promoted, needs reverting); a path matching `before_hash` is `already_reverted` and is skipped without error; a path matching neither is a `conflict` that aborts the entire attempt before any file is touched.
4. **Restore** — for each file actually reverted, `before_exists=True` restores the original `before_content`; `before_exists=False` removes the file. An RER is created with `status="in_progress"` before the first restore and persisted after every file.
5. **Resumability, not retry** — re-running `pcae rollback` against the same PER resumes a partial rollback via the `already_reverted` skip; there is no `--resume` flag. `pcae rollback-execution mark-interrupted` transitions an interrupted RER from `in_progress` to `partial` as pure bookkeeping — it never writes a file.

There is no mechanism to target an RER for reversal: the rollback build function accepts only a `per_id`, never an `rer_id`. Rollback-of-rollback is forbidden by construction, not by a runtime check that could be bypassed.

## Strategic Lineage Philosophy

PCAE distinguishes three kinds of record that are easy to conflate:

- **Roadmap state** (`_CRI_KNOWN_PHASES` in `src/pcae/core/agent.py`) — which phase is active, completed, or superseded. Mutable in the sense that statuses advance, but only one phase may be active at a time, enforced as a blocking check.
- **Activation evidence** (provenance events) — a timestamped record that a phase was activated.
- **Strategic decision lineage** (`.pcae/strategic-lineage.json`, Phase 65J) — an append-only record of *why* a human made a given strategic decision: the rationale, the alternatives considered and deferred, and the Strategic Lineage Record (SLR) entries documenting accepted scope. This file is authoritative only for human strategic decisions and their rationale. It does not own roadmap state, does not own activation evidence, and a later phase's lineage record superseding an earlier one (`supersedes_lineage_id`) never mutates or deletes the earlier record — supersession is reference-derived, not a status flip.

Sitting alongside lineage is the **Independent Review Governance (IRG) Challenge** (Phases 66E–68D): an automated, advisory-only mechanism that surfaces assumptions, blind spots, counterfactuals, and uncertainty about a strategic decision for human attention. It is deliberately *not* an approval authority — it never recommends approval or rejection, never prescribes implementation, and never gates a command's outcome. Its findings are surfaced at session bootstrap, phase handoff, and phase completion, with full detail available on demand (`pcae irg-challenge`).

The underlying principle, stated explicitly in this project's accepted decisions: **implementation approval does not imply activation approval, commit approval, or push approval.** A capability can be fully coded and tested and still not be the thing a human has authorized as "the current active phase," let alone authorized to commit or push. PCAE's own roadmap registry has carried this distinction since Phase 65I/65J, and it applies recursively to PCAE's own development process, not just to the code it governs.

## Current Limitations

- **No real AI runtime invocation.** `execution_allowed=False` everywhere, including inside the sandboxed execution lifecycle and through `pcae promote`/`pcae rollback`. Promotion and rollback write content a human already authorized; they do not invoke an agent.
- **Workspace isolation is not OS-level containment.** The Phase 69L sandbox is a `git worktree` + `rsync` overlay with the subprocess `cwd` pointed at the sandbox directory — it isolates *relative* working-tree changes, not absolute-path filesystem access, process isolation, or network isolation. `production_containment_ready=False` is asserted explicitly and cannot be auto-asserted true.
- **The sandbox shares git's object store with root.** A git commit made inside the sandbox lands in the same object database as the root checkout (Phase 69L, SLR-69L-006).
- **No commit or push automation anywhere.** Every governed write path stops at a file-level write or reversal; `git commit` and `git push` remain exclusively human actions.
- **Phase Activation Governance is unresolved roadmap debt.** PCAE has no first-class mechanism that separates "implementation approved" from "activation approved" from "commit approved" from "push approved" as distinct, independently-recorded human decisions — today this distinction is enforced by convention and by the single-active-phase invariant, not by a dedicated artifact.
- **Single active phase, no designated successor for 69O.** The roadmap registry's "exactly one active phase" invariant means a phase cannot be marked `completed` without a successor phase taking over `active` status. As of this writing, Phase 69O is BR-005's last implemented phase and remains the formally active phase pending a future, explicitly human-approved phase activation decision — even though the BR-005 capability set described above is fully implemented end to end (see [PROJECT_STATUS.md](../PROJECT_STATUS.md)).

## Deferred Capabilities

Explicitly out of scope for the BR-005 execution governance chain as implemented through Phase 69O:

- Automatic promotion or automatic rollback — both require an explicit human-invoked command every time.
- Rollback-of-rollback — no entry point accepts an `rer_id` as a rollback target.
- Multi-PER batch rollback — `pcae rollback` takes exactly one `--per-id`.
- Divergence override consumption — EPR's `override_divergence` field is recorded but not consumed by `pcae promote`; a conflict always aborts the attempt.
- Container-based or OS-level sandbox providers — `docker_dependency_forbidden=True` and `sandbox_exec_dependency_forbidden=True` are explicit constraints; only `git worktree` workspace isolation exists.
- Forensic retention of sandbox directories — sandbox directories are ephemeral and destroyed after evidence capture; no separate forensic copy is retained.
- Atomic, staged-rename file writes for promotion — promotion and rollback write sequentially per file with incremental PER/RER persistence, not as a single atomic transaction.
- Any git commit or push step inside the governed write/rollback chain.
"""


def generate_architecture_overview(
    root: HarnessPath,
    force: bool = False,
) -> DocsGenerateResult:
    return write_docs_artifact(
        root,
        ARCHITECTURE_RELATIVE_PATH,
        render_architecture_overview(),
        force,
    )


def render_glossary() -> str:
    return """# PCAE Governance Glossary

## active task

The single task contract currently governing a work session. `pcae check` enforces
scope restrictions drawn from the active task. Only one task may be active at a time.

## agent lock

A local lease file (`.pcae/agent-lock.json`) that records which agent is performing
governed work. Prevents accidental concurrent agent sessions in the same repository.
Acquired with `pcae agent acquire` and released with `pcae agent release`.

## allowed files

A set of file paths declared in the active task contract that the agent is permitted
to read or modify. `pcae check` reports a violation if a file outside this set is
touched during the session.

## allowed zones

Named directory prefixes declared in the active task contract. Files under an allowed
zone are implicitly permitted. Zones provide coarser-grained scope control than
individual allowed files.

## architecture history

A local append-only log (`.pcae/architecture-history.json`) of architecture check
snapshots. Each entry records zone counts, rule violations, enforcement mode, and
timestamp. Read by `pcae analytics` and `pcae architecture metrics`.

## architecture rules

Constraints declared in `policy.toml` that govern module boundaries, import
directions, or file placement within architecture zones. Violations are recorded in
architecture history and surfaced by `pcae check`.

## architecture zones

Named directory regions defined in `policy.toml` that partition the repository into
logical modules (e.g. `src/`, `tests/`, `docs/`). Rules are expressed in terms of
zones. `pcae architecture snapshot` classifies files into zones at check time.

## CI drift

A divergence between the generated `.github/workflows/pcae-governance.yml` and the
canonical workflow content expected by the current harness version. Detected by
`pcae ci drift` and repaired by `pcae ci repair`.

## CI repair

The act of regenerating the GitHub Actions governance workflow to eliminate CI drift.
`pcae ci repair --dry-run` previews the repair; `pcae ci repair --force` writes it.

## daemon dry-run

A simulated single monitoring cycle executed by `pcae daemon run --dry-run`. Reports
which governance checks would run without starting a persistent process or writing
files.

## enforcement mode

A policy setting (`advisory` or `strict`) that controls how `pcae check` treats
violations. In `advisory` mode violations are reported but do not cause a non-zero
exit. In `strict` mode any violation causes the check to fail.

## fleet drift

A divergence in governance state detected across one or more repositories in the fleet
registry. `pcae fleet drift` aggregates per-repo drift signals and reports which repos
require attention.

## fleet registry

The local list of governed repository paths stored in `.pcae/fleet.json`. Managed
with `pcae fleet add`, `pcae fleet list`, and `pcae fleet remove`. Used by all
`pcae fleet` subcommands.

## forbidden files

File paths explicitly excluded by the active task contract. Touching a forbidden file
during a session is a scope violation regardless of allowed-zone declarations.

## forbidden zones

Named directory prefixes explicitly excluded by the active task contract. Files under
a forbidden zone are out of scope even if they would otherwise be permitted by an
allowed-zone declaration.

## governance bundle

A portable JSON export of current governance state produced by `pcae export bundle`.
Contains policy, task contracts, session snapshot, and architecture history. Can be
imported into another repository with `pcae import bundle`.

## governance health

A summary of whether a repository meets all PCAE readiness criteria. Reported by
`pcae health` (human-readable) or `pcae health --json` (machine-readable). Aggregates
policy validity, active task presence, session continuity, and agent lock state.

## governance risk

A computed score summarizing the likelihood of governance degradation based on
architecture history trends. Reported by `pcae analytics risk`. Higher scores indicate
accumulating drift, stale tasks, or repeated enforcement violations.

## governance runtime

The set of local files and processes that enforce PCAE governance: `policy.toml`,
task contracts, session snapshots, architecture history, and the `pcae check` and
`pcae health` commands. The runtime operates entirely within the repository without
external services.

## pipeline dry-run

A preview of a named governance workflow produced by `pcae pipeline run --dry-run`.
Reports which checks and exports would execute without writing operational artifacts
or advancing session state.

## session continuity

A property verified by `pcae check` confirming that a valid session snapshot exists
and that the current agent context matches the recorded session. Broken continuity
indicates a session was not properly started or was interrupted without being finalized.

## task contract

A structured TOML file in `tasks/active/` that defines the scope, goal, allowed
files, forbidden files, allowed zones, forbidden zones, and enforcement mode for a
unit of governed work. Created with `pcae task new` and consumed by `pcae check`.
"""


def generate_glossary(
    root: HarnessPath,
    force: bool = False,
) -> DocsGenerateResult:
    return write_docs_artifact(
        root,
        GLOSSARY_RELATIVE_PATH,
        render_glossary(),
        force,
    )


def write_docs_artifact(
    root: HarnessPath,
    relative_path: Path,
    content: str,
    force: bool,
) -> DocsGenerateResult:
    target = root.join(relative_path)
    if target.exists() and not force:
        raise FileExistsError(
            f"{relative_path.as_posix()} already exists. Use --force to overwrite."
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    existed = target.exists()
    with target.open("w", encoding="utf-8", newline="\n") as file:
        file.write(content)

    return DocsGenerateResult(
        relative_path=relative_path,
        created=not existed,
        overwritten=existed,
    )
