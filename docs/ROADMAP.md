# PCAE Roadmap

> **Canonical roadmap.** This is the single source of truth for PCAE's product direction. Phase-specific plans, registry exports, and README snapshots derive from this document.

## Current State (June 2026)

PCAE has completed 90 phases across three major arcs:

| Arc | Phases | Status |
|-----|--------|--------|
| **Governance foundation** | 44A–68D | Complete — task contracts, runtime governance, multi-runtime, capability intelligence, strategic governance, execution governance activation (69A–69O) |
| **Multi-agent and intelligence** | 82A–87J | Complete — agent discovery, governed action gates, dry-run evaluation, permission broker architecture, shell gate architecture |
| **Advisory and enforcement readiness** | 88P–90B | Complete — shell gate prototype, permission broker prototype, advisory mode, dry-run simulation, enforcement readiness (threat model, audit/rollback/approval models, gate checklist, test plan, audit/rollback/approval/readiness prototypes, enforcement boundary design), full-suite baseline repair |

**Current phase:** 90B complete. Full suite green (9530/9530). Enforcement remains simulation-only.

## Roadmap Principles

1. **Governance before autonomy.** No agent capability is introduced until the governance infrastructure that contains it is in place.
2. **Evidence before enforcement.** Every enforcement action must be traceable to the evidence that produced it.
3. **Read-only before write.** Every new execution capability begins in read-only/simulation mode.
4. **Human authority.** The human operator is the authoritative decision-maker. PCAE governs; the operator decides.
5. **Hard blocks are non-overridable.** No human, no approval, no accepted risk can override a hard block (88V §16).
6. **Fail closed.** Uncertainty, missing evidence, or internal error → block, never allow.
7. **Task contracts before execution.** Every governed action is scoped by an explicit task contract.
8. **Production v1 before full pluggability.** Deliver a coherent governed platform first. Pluggable adapters come after the core is production-ready.
9. **One product, one roadmap.** PCAE is a single coherent product, not a collection of disconnected feature tracks.

---

## Production v1 Path

Production v1 is the first release of PCAE suitable for operator use in real engineering workflows. It includes a functional permission broker, governed action gates, shell gate classification, phase reporting, and outbound notification delivery.

### 90 Series — Enforcement Boundary and Test Foundation

| Phase | Name | Type | Purpose |
|-------|------|------|---------|
| **90A** | Permission Broker Enforcement Boundary Design | Design ✅ | Define broker enforcement boundary, layer responsibilities, input/output model |
| **90B** | Full-Suite Baseline Repair | Repair ✅ | Restore full suite to green (9530/9530) |
| **90B.1** | Roadmap Coherence and Production v1 Plan | Planning ✅ | This phase — canonical roadmap with Production v1 path |
| **90C** | Permission Broker Enforcement Boundary Test Plan | Test planning | Define tests for the enforcement boundary defined in 90A |

### 91 Series — Permission Broker Simulation Prototype

| Phase | Name | Type | Purpose |
|-------|------|------|---------|
| **91A** | Permission Broker Simulation Prototype | Implementation | Build the broker as a simulation-only decision aggregator with structured output |
| **91B** | Broker CLI and Decision Explanation | CLI/UX | `pcae broker check --command "..."`, explain decisions, JSON output |
| **91C** | Hard-Block Policy Readiness | Hardening | Verify all hard blocks are non-overridable, document policy surface |

### 92 Series — Phase Reporting and Notification

| Phase | Name | Type | Purpose |
|-------|------|------|---------|
| **92A** | Phase Report Artifact Model | Design | Define the durable phase report artifact schema |
| **92B** | Pluggable Notification Foundation | Design | Define the notification adapter interface (no implementation) |
| **92C** | Telegram Outbound Phase Report Delivery | Implementation | Send phase-finalization summaries via Telegram (outbound only) |
| **92D** | Automatic Phase-Finalization Notification Hook | Implementation | Trigger notification on `pcae phase complete` |

### 93 Series — Shell Gate Hardening

| Phase | Name | Type | Purpose |
|-------|------|------|---------|
| **93A** | Narrow Shell Gate Design | Design | Design the minimal shell gate for production: which commands to classify, which to block |
| **93B** | Narrow Shell Gate Prototype | Implementation | Implement the narrow shell gate in simulation-only mode |

### 94 Series — Governed Backend Invocation

| Phase | Name | Type | Purpose |
|-------|------|------|---------|
| **94A** | Governed Backend Invocation Design | Design | Design the backend invocation gate: when PCAE may invoke a backend, what evidence is required, how output is quarantined |

### 95–96 Series — Production Readiness

| Phase | Name | Type | Purpose |
|-------|------|------|---------|
| **95A** | Production v1 Documentation / Install / Demo | Documentation | Operator guide, install instructions, demo script |
| **96A** | Production v1 Governance Review | Review | Final governance review before Production v1 tag |

---

## Telegram Scope (Outbound Only)

Telegram integration in Production v1 is **outbound only** — PCAE sends notifications to the operator; the operator does not send commands to PCAE.

**What Production v1 Telegram does:**

- PCAE creates durable phase report artifacts (structured JSON files).
- On phase finalization (`pcae phase complete`), PCAE sends a short summary to a configured Telegram chat.
- The full phase report is attached as a file/document.
- Automatic send is enabled only after manual report delivery is confirmed stable.

**What Production v1 Telegram does NOT do:**

- No inbound command reception (`/run`, `/commit`, `/push`, etc.).
- No remote shell access.
- No commit or push from Telegram.
- No inbound command gateway of any kind.
- No Telegram bot that accepts operator commands.

**When inbound commands may be considered (future v2+):**

- Only after the permission broker and shell gate are mature and proven in production.
- Only with explicit operator authentication and command confirmation.
- Only with the same governance constraints as CLI commands.
- Never as a shell replacement or remote execution mechanism.

---

## Future v2 / Pluggability Track

Full pluggability belongs in a future version, after Production v1 is stable. The pluggability architecture will allow PCAE to be extended without modifying core governance logic.

### Notification Adapters

- Pluggable notification backends: Telegram, Slack, email, webhook, custom.
- Common adapter interface defined in 92B.
- Each adapter handles delivery; PCAE core handles artifact creation.
- New adapters added without changing PCAE core.

### Backend Adapters

- Pluggable AI backend connectors: Claude, DeepSeek, Kimi, OpenAI, local models.
- Common adapter interface for invocation, capture, and quarantine.
- Runtime trust assessment per adapter.
- New backends added without changing PCAE core.

### Policy Modules

- Pluggable policy modules: per-repository, per-organization, per-workflow.
- Policy modules can define custom gate rules, custom hard blocks, custom approval chains.
- Core governance invariants (hard blocks non-overridable, fail closed, human authority) are not overridable by policy modules.

### Audit Storage Adapters

- Pluggable audit storage: local JSONL, remote database, cloud storage.
- Common adapter interface for write, read, validate, rotate.
- Audit integrity (checksum chain, tamper evidence) is guaranteed by PCAE core regardless of storage adapter.

### Multi-Agent Orchestration Plugins

- Pluggable orchestration strategies: sequential, parallel review, swarm, custom.
- Agent capability discovery feeds into orchestration planner.
- Human approval gates remain regardless of orchestration strategy.

### Mobile / Operator Command Gateway (Future, Post-v2)

- Controlled inbound Telegram commands only after broker and shell gate maturity.
- Operator authentication required (Telegram user ID whitelist).
- Command confirmation required (reply with "confirm" to execute).
- No shell access, no `/run`, no commit/push from mobile.
- All commands subject to the same governance as CLI commands.

### External Packaging / Release Hardening

- PyPI package, Homebrew formula, Docker image.
- Release versioning policy.
- Signed releases, checksum verification.
- Upgrade/migration tooling.

---

## Guiding Constraints

### For All Phases

- Every phase begins with a governed task contract.
- Source and test changes are scoped to the active task.
- `pcae check` and `python -m pytest -n auto` before every commit.
- Fast-green must not regress.
- No raw git commit, no raw git push, no force push.

### For Implementation Phases

- Begin in simulation-only / read-only mode.
- Safety invariants (`no_execution=True`, `no_enforcement=True`, `is_authorization=False`) must be preserved.
- Hard blocks must remain non-overridable.
- Tests must pass before the phase is complete.

### For Production v1

- Enforcement remains simulation-only until all readiness gates are satisfied (69 gates from 89J).
- Operator must explicitly authorize any transition from simulation to enforcement.
- Shell gate never installs wrappers or modifies shell configuration.
- PCAE never executes commands, invokes backends without governance, or grants authorization.

---

## Historical Context

### Completed Arcs (for reference)

**Governance Foundation (44A–68D):** Task contracts, runtime governance, multi-runtime registry, capability intelligence, strategic governance, execution governance activation chain (69A–69O).

**Multi-Agent and Intelligence (82A–87J):** Agent capability discovery, multi-agent task contracts, governed action gates (15 gates), dry-run evaluation, permission broker architecture, shell gate architecture.

**Advisory and Enforcement Readiness (88P–90B):** Shell gate prototype (88P, 88Q, 89A), permission broker prototype (88R), advisory mode (88X), dry-run simulation (89B–89E), enforcement readiness design (89G–89K), enforcement prototypes (89L–89N), enforcement boundary design (90A), full-suite baseline repair (90B).

### Prior Roadmap Documents (Informational)

The following documents informed this roadmap but are not canonical:

- `docs/ROADMAP_REGISTRY.md` — Machine-generated phase registry from `pcae roadmap`. Regenerated on demand.
- `docs/MULTI_AGENT_LIFECYCLE_LESSONS_ROADMAP.md` — Phase 84A deliverable. Historical context for multi-agent governance.
- `docs/PHASE_85_IMPLEMENTATION_ROADMAP.md` — Phase 86A deliverable. Historical context for Phase 85 implementation.
- `docs/ROADMAP_RECONCILIATION_PHASE_85_PLAN.md` — Phase 84L deliverable. Historical reconciliation plan.

**Future cleanup note:** These phase-specific roadmap documents may be consolidated or archived after Production v1. They are retained for historical provenance.

---

*This roadmap supersedes all prior roadmap documents. The README.md Roadmap Snapshot derives from this document. Phase-specific plans reference this document as the authoritative source for PCAE's product direction.*
