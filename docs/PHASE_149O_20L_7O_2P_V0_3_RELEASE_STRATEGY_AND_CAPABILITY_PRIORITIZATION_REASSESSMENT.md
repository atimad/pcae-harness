# Phase 149O.20L.7O.2P — PCAE v0.3 Release Strategy and Capability Prioritization Reassessment

Status: analysis and decision only. No implementation. No production
source changes. No HATP activation. No FIDO2 enrollment. No WebAuthn
infrastructure deployment. No DNS/TLS provisioning. No RP-ID selection.
No release creation.

## Section 1 — Inspect Existing Releases

Method: `gh release view v0.1.0-rc1`, `gh release view v0.2.0`, `git tag -l`.

**PCAE v0.1.0-rc1** (tagged, GitHub pre-release, 2026-07-02):

- What was released: the first release candidate of a non-executing
  lifecycle governance harness — task/phase contracts, report-trust
  validation with hard-fail gates, golden workflow documentation,
  commit/push governance, bootstrap/session reporting, outbound-only
  Telegram phase-report notification, release-readiness checks, and
  packaging/install smoke validation.
- User problem solved: none of the *coding* problem — it solved the
  "how do we know an AI agent's session state, task boundaries, and
  phase completion claims are trustworthy" problem. It is a governance
  and reporting layer, not a coding assistant.
- Capabilities available: `pcae init`, `pcae health`, `pcae check`,
  governed task/phase lifecycle commands, packaging as an installable
  wheel/sdist.
- Intended user: an engineer or team already running AI coding agents
  who wants an audit trail and hard gates around session/phase claims,
  not a user looking for an agent to write code for them.

**PCAE v0.2.0** (tagged, GitHub release, 2026-07-07):

- What was released: the "frozen v0.2 architecture" — Repository State
  Kernel and Repository Transition Validator contracts, canonical
  phase-report promotion/trust-gating/quarantine, Evidence Framework,
  Decision Evaluation, Repository Skills, Advisory Provider/Context
  Package contracts, `pcae runtime inspect --json`, `pcae agent
  verify-handoff`, `pcae session bootstrap --compact`.
- Architectural capabilities added: a formal advisory/evidence
  architecture with an explicit non-authorizing boundary (advisory
  evidence and dry-run output cannot authorize or perform repository
  mutation), plus runtime introspection reporting the system's own
  execution posture.
- What moved from prototype to usable capability: governed commit/push
  readiness workflows, phase-report trust gating and quarantine, and
  read-only repository/project intelligence commands became exercised,
  documented, CLI-reachable surfaces rather than design docs.
- Limitations remaining (stated explicitly in the release notes): no
  live AI backend invocation, no autonomous coding behavior, no
  execution capability, no shell mediation, no Telegram inbound
  command path, no REST API/dashboard/Web UI, no model integration.
  Runtime state is `Observed`; max plugin capability is `observe`; 0
  runtime plugins registered.

## Section 2 — Current PCAE Capability Inventory

Verified against live `pcae runtime inspect --json`, `pcae health`, a
spot-check of ~15 CLI subcommands, and `docs/` grep as of the current
head phase (149O.20L.7O.2N.18, "COMPLETE — VERDICT A", explicitly: "NO
PROVISIONING. NO PRODUCTION SOURCE CHANGED."). Runtime posture is
**unchanged from the frozen v0.2.0 posture**: `runtime_status:
not_implemented`, `execution_availability: unavailable`,
`current_runtime_state: Observed`, `current_maximum_plugin_capability:
observe`, `registered_plugin_count: 0`.

| Capability area | Classification | Basis |
|---|---|---|
| Governance kernel (task/phase/session lifecycle, trust gates, quarantine) | **Released** | Live in v0.1/v0.2, exercised continuously through 3,200+ commits since |
| Execution boundary (advisory/evidence non-authorizing separation) | **Released** | Frozen v0.2 contract; every CLI command spot-checked returns real governance data, never performs the action it evaluates |
| Permission Broker | **Candidate for v0.3** | Phase 148 (~91 commits) built "Production Consumption architecture" — designed and contract-frozen, not yet load-bearing for any live enforcement path |
| Runtime architecture (plugin/adapter model) | **Internal architecture** | `current_maximum_plugin_capability: observe`, 0 registered plugins — the scaffolding for a real runtime exists, nothing runs through it |
| Repository Intelligence (change impact, dependency graph, historical memory) | **Released** (as read-only inspection) | Phase 118A–118R; these are real, working, read-only CLI surfaces (`repository-intelligence`, `architecture`, `artifact-index`, etc.) |
| Historical Memory | **Released** (read-only) | Same phase family as above; queryable, not yet feeding any automated decision |
| Context/Snapshot system | **Released** (read-only) | `context`, `execution-snapshot`, `memory-snapshot` commands are live |
| Multi-agent orchestration | **Enterprise extension / Future research** | Extensive design docs (`collaboration-design`, `orchestration-design`, `coordinator-design`, `consensus-design`) but no live multi-agent execution — 0 registered runtime plugins means there is nothing to orchestrate yet |
| Plugin/runtime adapter model | **Internal architecture** | Same as runtime architecture row — contract exists, unpopulated |
| HATP (repository identity / trust-store / handoff authority) | **Enterprise extension** | ~67 commit-message hits; first-class architecture (Typed Authority Model, phases 135/136/137/143) but purely repository-internal governance metadata, not user-facing |
| HMIC (mandatory independent-verification certification) | **Enterprise extension** | Frozen contract (HMIC-001, phase 149O.19.2) gating HATP/WebAuthn credential steps; process overhead, not a product feature a typical adopter touches |
| FIDO2 | **Future research** | No hardware enrollment has occurred anywhere in the repo's history; explicitly gated behind independent verification before "first credential registration" |
| Remote WebAuthn | **Future research** | No domain, no DNS/TLS, no `RemoteWebAuthnProvider` instantiated; current phase (149O.20L.7O.2N.18) is itself a plan-verification phase, one more layer removed from any deployment |
| Deployment governance | **Enterprise extension** | Deployment-binding, Class-B verifier, and RP-ID/origin planning phases exist only as documentation and independent-verification cycles |

## Section 3 — Define PCAE v0.3 Product Goal

**Why would somebody install PCAE v0.3?**

Not because it "does more architecture" — v0.2 already has more
governed architecture than almost any adopter will read. They would
install it because it answers a question every team running AI coding
agents already has and currently solves with ad hoc discipline: *"How
do I know what an AI agent actually did, whether it stayed inside its
assigned scope, and whether I can trust its own report of what it
did?"* v0.1/v0.2 built the governance skeleton for that answer but
never connected it to a real coding session a user would actually run
day to day — every CLI command a user would touch is inspection,
simulation, or advisory, not something that changes what their agent
does.

Target user: **an individual developer or small team already running
Claude Code, Cursor, or similar AI coding agents on a real repository**,
who wants task-scoped guardrails and an audit trail without adopting a
new agent framework or giving up their existing workflow.

Primary problem solved: **agent scope drift and unverifiable
completion claims** — the agent says "done," touches files outside the
stated task, and nobody catches it until review or production.

Core v0.3 promise: **drop PCAE into an existing repo in under five
minutes and get real governed guardrails around your existing AI
coding agent's session** — not a new agent, not a new orchestration
layer, not new hardware.

**Complete**: PCAE v0.3 enables **verifiable, scope-bounded AI coding
sessions** for **developers and small teams already using AI coding
agents** by providing **a lightweight, install-in-minutes governance
layer that gates task scope, validates completion claims against real
repo state, and produces an audit trail — without requiring a new
agent, new hardware, or new infrastructure.**

## Section 4 — Reassess HATP and WebAuthn Direction

Analysis:

- **Onboarding friction**: HATP/HMIC/WebAuthn as currently scoped
  require a named domain, DNS/TLS provisioning, a deployment-binding
  identity, and (eventually) FIDO2 hardware enrollment, each gated
  behind its own independent-verification cycle. None of this exists
  today even internally — the project's own reference deployment has
  not done it.
- **Domain/DNS/TLS requirements**: real and currently blocking — the
  repo's own phase history repeatedly stops at "no domain selected" as
  a hard boundary.
- **Hardware requirements**: FIDO2 requires a physical authenticator
  (or platform authenticator) per user/device — a nontrivial ask for
  someone evaluating a governance CLI for the first time.
- **Operational complexity**: RP-ID/origin selection, deployment-class
  verification (Class-B), and certification contracts (HMIC-001) are
  security-engineering-grade process, appropriate for a regulated or
  enterprise deployment, not a `pip install` evaluation flow.
- **Adoption impact**: gating any part of the core v0.3 promise (task
  scoping, completion verification) behind this stack would make v0.3
  strictly harder to adopt than v0.2, which is the wrong direction for
  a release whose stated goal is adoption, not completeness.

**Explicit answers**: A normal PCAE user should **not** need a domain,
TLS infrastructure, FIDO2 hardware, or WebAuthn setup to get value from
v0.3. None of these are prerequisites for the core promise in Section 3.

**Recommendation**: HATP/HMIC/WebAuthn is real, valuable work — but it
is an **Enterprise Security Extension**, not a v0.3 core-adoption-path
dependency. It should ship (when ready) as an optional, separately
documented track that a security-conscious enterprise adopter opts
into after already getting value from core PCAE, not as something
every evaluator has to understand or configure.

## Section 5 — Competitive Position

**Strengths**:

- Governance and auditability depth — trust-gated phase reports,
  quarantine, and repository-transition validation are more rigorous
  than anything in mainstream AI coding tools, which generally trust
  the agent's own "done" claim.
- Explicit non-authorizing evidence/advice boundary is a genuinely
  differentiated safety property (no hidden authorization path through
  advisory data, scope matches, or notification state).
- Human-authoritative model is a clear, defensible position against
  tools racing toward more autonomy.
- Repository intelligence (change impact, dependency graph, historical
  memory) is real, working, read-only tooling that could be a
  standalone selling point if surfaced better.

**Weaknesses**:

- Zero live execution capability after two releases and ~3,200
  commits — competitors ship working autonomous or semi-autonomous
  coding agents; PCAE ships governance *around* a coding agent it
  doesn't itself provide, and that gap has not narrowed.
- Enormous CLI surface (hundreds of subcommands) with no clear
  narrative for a first-time user — most commands are architecture
  previews or dry-runs, which is confusing for adoption even though it
  is accurate to the project's honesty about its own posture.
- Documentation-to-code ratio (docs ~489K lines vs. src ~276K lines,
  tests ~414K lines) signals a project optimized for internal
  governance ceremony over external legibility.
- No concrete "install this, point it at your existing agent, see
  value in 5 minutes" story exists yet.

**Adoption blockers**:

- Nothing to *do* with PCAE v0.2 alone — it observes and reports but
  doesn't yet connect to a real agent session a user is running.
- No documented integration with any actual coding agent (Claude Code,
  Cursor, Copilot, etc.) as of this analysis.
- The scale and vocabulary of the governance model (HATP, HMIC,
  Repository State Kernel, Typed Authority Model) is intimidating
  relative to the value a new user can currently extract.

## Section 6 — v0.3 Scope Proposal

**Must Have**:

- A concrete, documented integration point where PCAE observes or
  gates an actual AI coding agent's session on a real repo (even if
  read-only/advisory at first) — this is the single most important gap
  identified above.
- A 5-minute quick-start that gets a new user from `pip install` to a
  visible, believable guardrail (e.g., a scope violation caught) with
  zero domain/TLS/hardware setup.
- Consolidation/curation of the CLI surface into a documented "core"
  command set for adopters, distinct from the internal
  architecture-preview commands (which can stay, but shouldn't be the
  first thing a new user sees).

**Should Have**:

- Permission Broker taken from "Production Consumption architecture"
  (designed, Phase 148) to an actually consumed, load-bearing gate in
  at least one real workflow.
- Better surfacing of Repository Intelligence as a standalone
  value-add (dependency graph, change impact) usable independent of
  the full governance ceremony.

**Enterprise Track**:

- HATP, HMIC, Remote WebAuthn/FIDO2, deployment-binding, and
  multi-agent orchestration — continue as a parallel, explicitly
  labeled Enterprise Security Extension track, not blocking core v0.3.

**Deferred**:

- Live AI backend invocation / autonomous execution (Level 4 autonomy
  per `docs/V0_2_AUTONOMY_ROADMAP.md`) — explicitly out of scope until
  Level 3 is proven safe and audited, consistent with existing project
  doctrine.
- REST API, dashboard, Web UI.
- Any further HATP/HMIC/WebAuthn sub-phase work beyond what's needed
  to keep the Enterprise track coherent for later resumption.

**WebAuthn/HATP decision**: **Enterprise extension**, not v0.3 core.

## Section 7 — 90-Day Roadmap

**Engineering priorities**:

- Weeks 1–3: build and document one concrete integration surface
  between PCAE's existing governance/evidence commands and a real
  coding-agent session (session-scoped file/task boundary checks
  running alongside an actual agent, using capabilities that already
  exist — `pcae agent verify-handoff`, `context`, `execution-snapshot`
  — rather than new execution machinery).
- Weeks 4–6: curate and document a "core" CLI command set; deprecate
  nothing, but restructure `--help` and quick-start docs so the
  hundreds of design/prototype commands don't dominate a new user's
  first impression.
- Weeks 7–10: move Permission Broker from designed to consumed in the
  core workflow identified in weeks 1–3.
- Weeks 11–13: hardening, quality-gate re-verification (fast_green,
  full suite), release-readiness checks for v0.3.

**Documentation priorities**:

- A single "why PCAE" landing narrative anchored on Section 3's
  promise, not the full architecture catalog.
- A 5-minute quick-start doc/screencast script.
- An explicit "Core vs. Enterprise Extension" split in the docs index
  so HATP/HMIC/WebAuthn material is discoverable but clearly optional.

**Adoption/demo priorities**:

- A demo repo showing PCAE catching a real scope-drift or
  false-completion-claim scenario against an actual agent session.
- Public-facing comparison (governance/auditability framing, not
  autonomy framing) against mainstream AI coding tools.

**Reference deployment priorities**:

- None required for v0.3 core (by design — no domain/TLS/hardware
  dependency).
- Enterprise track reference deployment (the RP-ID/domain/DNS/TLS work
  already in progress) continues on its own independent-verification
  cadence, unblocked by and not blocking v0.3 core.

## Section 8 — Final Recommendation

**PCAE v0.3 should focus on**: closing the gap between "governs
sessions in the abstract" and "governs a session a real user is
actually running," with a curated onboarding path that gets a new
adopter to visible value in minutes, using capability that already
exists in the repo today.

**PCAE v0.3 should not include**: HATP activation, FIDO2 enrollment,
Remote WebAuthn deployment, DNS/TLS/domain provisioning, live
autonomous code execution, or any expansion of the enterprise
governance ceremony as a prerequisite for core adoption.

**HATP/WebAuthn decision**: Enterprise Security Extension — continue
its own architecture/verification track in parallel, explicitly
decoupled from v0.3's adoption-focused core scope.

**Reasoning**: v0.1 and v0.2 built (and honestly, repeatedly
re-verified) a deep, trustworthy governance and evidence architecture,
but two releases and ~3,200 commits in, the project still has no
documented moment where a new user connects PCAE to an agent session
they actually run and sees a guardrail catch something. Continuing to
invest in HATP/HMIC/WebAuthn — real but enterprise-grade,
infrastructure-heavy work — before that adoption gap is closed would
optimize for architectural completeness PCAE already has in abundance,
at the direct expense of the adoption PCAE still lacks entirely. The
project's own existing roadmap doctrine (`V0_2_AUTONOMY_ROADMAP.md`:
broader execution capability is "Future (v0.3+)... requires Level 3 to
be proven safe first") already points the same direction this analysis
does: prove value at the current safety level before adding scope, not
before adding security infrastructure most adopters will never touch.
