# Phase 149O.20L.7O.2U — PCAE v0.3 Release Execution Plan and Critical-Path Freeze

Status: strategy / planning / critical-path-freeze only. No production
implementation. No execution enablement. No HATP/FIDO2/WebAuthn work. No
release or tag creation. No permission-broker changes. No adapter code.

This phase converts the reconciled Phase 149O.20L.7O.2P v0.3 strategy
(`docs/PHASE_149O_20L_7O_2P_V0_3_RELEASE_STRATEGY_AND_CAPABILITY_PRIORITIZATION_REASSESSMENT.md`)
into a concrete, short, execution-oriented release plan. 2P's strategic
conclusions are used as-is per the handoff instruction ("do not silently
rewrite its strategic conclusions unless current evidence clearly
invalidates them") — nothing found this phase invalidates them.

## 1–2. Actual v0.1 / v0.2 Released Baseline

Method: `gh release list`, `gh release view v0.1.0-rc1`, `gh release view
v0.2.0`, `git tag -l`. Two tags exist: `v0.1.0-rc1`, `v0.2.0`. Both are
real, published GitHub releases on `atimad/pcae-harness`.

**PCAE v0.1.0-rc1** (pre-release, published 2026-07-02, tag
`v0.1.0-rc1`, assets: `pcae_harness-0.1.0-py3-none-any.whl`,
`pcae_harness-0.1.0.tar.gz`) delivered:
- Governed task/phase/session contracts and lifecycle commands.
- Report-trust validation with hard-fail gates.
- Golden workflow documentation.
- Commit/push governance.
- Bootstrap/session reporting.
- Outbound-only Telegram phase-report notification.
- Release-readiness checks; packaging/install smoke validation
  (wheel/sdist build and install verified).
- Explicit non-goals stated in the release notes: no autonomous
  execution, no shell mediation, no real AI backend invocation, no
  Telegram inbound control, no runtime enforcement.
- Quality bar at release: fast_green 4390/4390.

**PCAE v0.2.0** (full release, published 2026-07-07, tag `v0.2.0`)
delivered:
- Repository State Kernel and Repository Transition Validator contracts
  (centralized repository-state validation).
- Canonical phase-report promotion, trust gating, and quarantine,
  exercised through governed lifecycle commands (not just documented).
- Evidence Framework, Decision Evaluation, Repository Skills, Advisory
  Provider/Context Package contracts frozen.
- `pcae runtime inspect --json` (self-reported non-executing posture).
- `pcae agent verify-handoff` (cross-agent handoff safety).
- `pcae session bootstrap --compact --profile implementation`.
- Explicit non-goals restated: no live AI backend invocation, no
  autonomous coding, no execution capability, no shell mediation, no
  Telegram inbound path, no REST API/dashboard/Web UI, no model
  integration. Runtime state `Observed`, max plugin capability
  `observe`, 0 registered plugins.
- Quality bar at release: full suite 18063 passed; fast_green 4390
  passed.

No PyPI/package-index publication has occurred for either release
(GitHub release assets only). This is a real, current gap relevant to
onboarding friction (see §28).

## 3. Current Project Status (Live Verification)

`pcae health`: healthy, git clean, active task present, agent lock held,
session continuity verified. `pcae runtime inspect --json`: runtime
posture is unchanged since v0.2.0 — `Observed` / `execution_unavailable`
/ max plugin capability `observe` / 0 registered plugins. `PROJECT_STATUS.md`
current-phase entry confirms Phase 149O.20L.7O.2T closed the Fast
Green/FGSC detour: FGSC-001 is operationally certified (149O.20L.7O.2S.6),
2P is technically reconciled (149O.20L.7O.2T), and the recommended next
step was explicitly "return to the v0.3 product roadmap," not further
Fast-Green work. Since v0.2.0 (~3,200+ commits, per 2P's own count), the
overwhelming majority of subsequent phase work has been governance/
verification-infrastructure hardening (Fast Green self-certification,
attribution gates, HATP/HMIC/WebAuthn architecture) — not user-facing
product surface. This confirms 2P's adoption-gap diagnosis rather than
invalidating it.

## 4. Current Capability Matrix

Classification legend: **Released** (user-usable today via a documented
CLI command against a real repo) · **Implemented, not surfaced**
(working code, no first-class onboarding path) · **Architecture-only**
(contracts/schemas frozen, no live consumer) · **Experimental/internal**
· **Enterprise extension** · **Deferred** · **v0.3 candidate**.

| Capability area | Classification | Basis |
|---|---|---|
| Repository init / setup (`pcae init`) | Released | Live command, produces `.pcae/` scaffolding |
| Task lifecycle (`pcae task new/update/transition/finish`) | Released | Exercised continuously; this phase used it directly |
| Governed change lifecycle (task-scoped file allow-lists) | Released | `pcae check` enforces allowed-file/zone policy |
| Commit governance (`pcae commit implementation`) | Released | Used every phase, including this one |
| Push governance (`pcae push`, `pcae push check`) | Released | Readiness gate on health/check/task-memory/phase-report-identity |
| Permission Broker | Architecture-only (v0.3 candidate) | Phase 148 "Production Consumption architecture" designed and contract-frozen; not load-bearing in any live enforcement path (confirmed by 2P, unchanged) |
| Execution boundary (advisory/evidence non-authorizing separation) | Released (as a safety property) | Every CLI command spot-checked evaluates/reports, never performs the action it evaluates |
| Runtime execution | Architecture-only / Deferred | `runtime_status: not_implemented`, `execution_availability: unavailable`, 0 registered plugins — confirmed live this phase, unchanged since v0.2.0 |
| Runtime introspection (`pcae runtime inspect`) | Released | Live, JSON-capable |
| Runtime context / snapshots (`context`, `execution-snapshot`, `memory-snapshot`) | Released (read-only) | Live CLI surfaces |
| Repository intelligence (`repository-intelligence`, `architecture`, `artifact-index`, dependency graph) | Released (read-only) | Phase 118A–118R; real, working, queryable |
| Historical memory | Released (read-only) | Same family; queryable, not feeding automated decisions |
| Cross-artifact intelligence (`project-state`, `governance-timeline`, `decision-log`, `risk-register`) | Released (read-only) | Phase 86A–86I; 183 tests, integrates 5 layers |
| Advisory governance (dozens of `*-design`/dry-run commands) | Released (as advisory-only tooling) | Real commands, but explicitly non-authorizing by design |
| Human governance / approvals (`approval-store`, `authorization-store`, `promotion-review`) | Released | Live in the 69A–69O activation chain |
| Publication workflow (GitHub release) | Implemented, not surfaced | Manual `gh release` process used for v0.1/v0.2; no `pcae`-governed release command exists |
| Plugin/runtime adapter architecture | Architecture-only | Scaffolding exists; 0 plugins registered, nothing runs through it |
| Multi-agent / agent-harness integration | Architecture-only / Deferred | Extensive design docs (82A–87J), `implementation_status=not_started` for runtime execution; `pcae agent verify-handoff` is the one live cross-agent primitive |
| HATP | Enterprise extension | First-class architecture (Typed Authority Model); purely repository-internal governance metadata, no user-facing surface |
| HMIC | Enterprise extension | Frozen contract (HMIC-001) gating HATP/WebAuthn credential steps; process overhead, not a typical-adopter feature |
| FIDO2 | Deferred / Future research | No hardware enrollment anywhere in repo history |
| Remote WebAuthn | Deferred / Future research | No domain, no DNS/TLS, no `RemoteWebAuthnProvider` instantiated |
| Deployment governance (Class-B verifier, RP-ID/origin) | Enterprise extension | Documentation and independent-verification cycles only |
| Telemetry/notifications | Released | Telegram outbound-only phase-report notification, live and configured in this environment |

## 5. Architecture vs. Product

For every candidate v0.3 feature, the operative test is: *can a user
install PCAE and actually use this today?* Governance kernel, task
lifecycle, commit/push governance, repository-intelligence read-only
commands: **yes**. Permission Broker enforcement, any live runtime
execution, any multi-agent orchestration, HATP/WebAuthn: **no** — each
has a concrete, named implementation/usability gap (Permission Broker:
not wired to any real gate call site; runtime execution: 0 registered
plugins; multi-agent: `implementation_status=not_started`; HATP/WebAuthn:
no deployment identity/domain exists anywhere, even internally).

## 6. v0.3 Headline

**PCAE v0.3 enables verifiable, scope-bounded AI coding sessions for
developers and small teams already using AI coding agents (Claude Code,
Cursor, and similar) by providing a lightweight, install-in-minutes
governance layer that gates task scope, validates completion claims
against real repo state, and produces an audit trail — without
requiring a new agent, new hardware, or new infrastructure.**

(Carried forward verbatim from 2P §3 — current evidence does not
invalidate it; if anything, the volume of governance-hardening work
since v0.2.0 without a matching adoption surface strengthens the
diagnosis.)

## 7. Primary Target User

Primary: **A. individual AI-assisted developer** (or a small team
acting as one unit), already running an existing coding agent on a real
repository, evaluated first. v0.3 does not require choosing between A/B/C
exclusively — a small dev team (B) is a natural secondary beneficiary of
the same core flow — but the release's install-in-minutes, no-
infrastructure promise is designed and prioritized for A/B, not C
(enterprise). This matches 2P and is not revised.

## 8. Core User Journey (v0.3, Derived From Current Code)

1. `pip install pcae-harness` (or from the GitHub release wheel/sdist —
   no PyPI publication exists today, see §28).
2. `pcae init` in an existing Git repository.
3. `pcae task new "<title>" --goal "..." --allowed-file <path> ...` to
   scope what the agent (human- or AI-driven) is permitted to touch.
4. Run the existing AI coding agent (Claude Code, Cursor, etc.)
   normally, alongside PCAE.
5. `pcae check` — validates real repo state (file changes) against the
   task's allow-list; this is the concrete, already-implemented
   "governs a session" moment.
6. `pcae commit implementation` — governed commit tied to the task
   contract.
7. `pcae push check` / `pcae push` — governed readiness validation
   before push.
8. `pcae task finish` / phase-completion report — audit trail artifact
   produced (`.pcae/phase-completion-report.md`, phase-completion
   metadata).

This is the actually-feasible journey today: steps 2, 3, 5, 6, 7, 8 are
all live, tested commands. No invented capability. What is *not* in this
journey (a live intercept/deny of an agent's in-flight action) is the
execution gap analyzed in §9.

## 9. Execution Gap Analysis (Critical Section)

**What is already implemented**: a complete advisory/evidence pipeline
— approval-store, authorization-store, audit-record, execution-
activation (sandboxed via `git worktree` + `rsync` overlay),
execution-result-governance, execution-change-package,
promotion-review, and exactly two commands that mutate the root
repository: `pcae promote` and `pcae rollback`, both human-gated on
prior reviewed evidence. This is a real, tested, 69A–69O activation
chain — not vaporware.

**What is contract-only**: the Permission Broker (Phase 148) and the
plugin/runtime adapter model (`current_maximum_plugin_capability:
observe`, 0 registered plugins). The architecture to route a live
runtime's proposed action through a broker decision exists as a
contract; no runtime is registered to call it.

**What is intentionally disabled**: live AI backend invocation, shell
mediation, and autonomous execution — a repeated, explicit project
doctrine (`docs/V0_2_AUTONOMY_ROADMAP.md`: broader execution is "Future
(v0.3+)... requires Level 3 to be proven safe first"). This is a
deliberate safety boundary, not an accidental gap.

**Minimum safe execution capability releasable in v0.3**: PCAE does not
need to invoke a live AI backend to demonstrate governed execution. The
missing piece is narrower: a single reference **adapter** that lets an
already-running external agent session (not one PCAE spawns) report its
proposed file changes to PCAE's *existing* execution-activation/
promotion chain, so `pcae promote`/`pcae rollback` govern a real,
observable action instead of only a synthetic EPR/PER fixture. This
requires zero new authority surface — the approval/audit/promotion gates
already exist — only a thin, well-scoped intake path (e.g., "stage this
diff as an EPR candidate for human review") wired to the sandboxed
activation chain that already exists.

**What would make PCAE visibly different from a documentation/
governance framework**: a demoable sequence where an external agent's
actual proposed change is captured, reviewed, and either promoted or
rolled back through PCAE's existing (not new) machinery — visible,
recorded, reversible. This is achievable without touching the safety
boundary above (no live backend invocation, no shell mediation, no
broadened autonomy).

No execution capability is enabled in this phase. This is analysis only.

## 10. First Real Value Demonstration

Demo: an external AI coding agent (developer's existing tool) proposes a
file change in a governed repo. PCAE's task-scope check (`pcae check`)
flags an out-of-scope file before commit — **deny path**. A second,
in-scope change is captured, promoted via the existing `pcae promote`
evidence chain — **allow path**. Both produce an audit artifact
(`.pcae/phase-completion-report.md`-equivalent evidence + `pcae
project-state --json`). This answers "why does PCAE exist" using only
capability that already exists in the repo today (task scope gating +
the 69A–69O promotion/rollback chain), not new execution machinery.

## 11. Competitive Differentiation

Do not compete with general agent harnesses (e.g., DeepSeek Harness) on
autonomy or breadth. PCAE's differentiated, defensible value is
narrower and orthogonal: **governed execution, permission boundary,
auditability, human authority, explainability — a trust kernel around
agent harnesses**, not a replacement for them. v0.3 should ship
something visibly differentiated along exactly these axes (deny/allow
demo with audit trail, §10) rather than attempting feature parity with
autonomous coding agents.

## 12. Plugin / Outer-Adapter Strategy

Recommendation: v0.3 should ship **one reference integration/adapter**
(intake path described in §9) plus the **generic adapter interface**
needed to support it cleanly, rather than either (a) CLI-only governed
execution with zero live-agent connection, or (b) a second/third
integration. A single concrete adapter proves the pattern without
committing to a specific vendor's runtime as a permanent dependency.
DeepSeek integration is explicitly out of scope for this decision —
the private DeepSeek research repository is out of scope for this phase
entirely per the handoff.

**This is flagged as a candidate human decision point** — see §34 —
because *which* external agent/tool the reference adapter targets
(Claude Code, a generic file-diff intake, or something else) materially
affects the demo and the next 1–2 implementation phases, and the
handoff explicitly asks that integration-target choices not be silently
frozen.

## 13. Must-Have v0.3 Scope

- A concrete, documented intake path connecting an external AI coding
  agent's proposed change to PCAE's existing execution-activation/
  promotion/rollback chain (§9, §12) — even if the intake itself is
  manual/scripted at first, not a live daemon.
- A 5-minute quick-start: `pip install` (or documented wheel install) →
  `pcae init` → `pcae task new` → one real deny + one real allow
  demonstrated — zero domain/TLS/hardware setup.
- A curated "core command" quick-reference distinct from the hundreds of
  design/prototype/advisory subcommands (documentation-only change,
  no CLI removal).

## 14. Should-Have Scope

- Move the Permission Broker from designed (Phase 148) to consumed by
  at least the reference adapter's intake path.
- Standalone surfacing of Repository Intelligence (dependency graph,
  change impact) as a value-add usable without the full governance
  ceremony.
- PyPI publication of the wheel/sdist (currently GitHub-release-only;
  lowers install friction without being release-blocking).

## 15. Explicitly Deferred / Enterprise Scope

Not v0.3 adoption blockers, preserved (not deleted) for later
resumption: HATP activation, FIDO2 enrollment, remote WebAuthn
infrastructure, user-owned domains, DNS/TLS/VPN setup, enterprise
identity, managed WebAuthn service, multi-tenant control plane,
centralized company-wide governance.

## 16. WebAuthn Status

Architecture/contract work substantially advanced (Typed Authority
Model, RP-ID/origin planning, Class-B deployment-verifier design); **not
required or enforced for v0.3's default user path**. No small residual
"finish the chapter" item was identified this phase that is both (a)
infrastructure/adoption-neutral and (b) worth scheduling ahead of v0.3
execution work — if one exists it was not surfaced by 2P or by this
phase's inspection, so none is scheduled.

## 17. HATP Status

Classification: **HATP optional/experimental — documented, not
activated, not on the v0.3 critical path.** Hardware-backed trust is not
made mandatory for normal adoption. This matches 2P's classification
(Enterprise extension) and current evidence does not change it.

## 18. Release Blockers

| ID | Current state | Why it blocks user value | Closure criterion | Likely phase(s) |
|---|---|---|---|---|
| RB-1: No live-agent intake path | Contract-only (execution-activation chain exists, nothing feeds it a real external agent's proposed change) | Without this, v0.3's headline ("governs a session you actually run") is unproven — v0.2 already has the advisory pipeline with nothing plugged into it | A documented, working intake path from at least one real external agent workflow into the existing EPR/promotion chain, demonstrated end-to-end | 1 implementation phase, likely 1 independent-verification phase |
| RB-2: No deny+allow public demo | Not built | v0.3's "why does PCAE exist" moment (§10) does not exist yet in demoable form | A reproducible demo script/repo showing one denied and one allowed change with audit evidence | 1 phase (can combine with RB-1's verification) |
| RB-3: No curated onboarding path | Not built | Hundreds of subcommands with no "start here" — a new adopter cannot find the 5-minute path today | A documented quick-start (README section + doc) exercised by a fresh clone/install | 1 documentation phase |

## 19. Non-Blocking Debt

- Historical Fast Green test drift and FGSC carried non-blocking
  findings (prefix-match issue-identity fragility, noted in
  149O.20L.7O.2S.5 — non-currently-exploitable).
- `pcae doctor task-memory` pre-existing historical `tasks/DONE.md` sync
  warnings (documented by multiple prior phases, unrelated to this
  work).
- HATP/WebAuthn deferred architecture work (§15–17).
- No PyPI publication (should-have, §14, not release-blocking).
- Large docs-to-code ratio noted by 2P (~489K doc lines vs. ~276K src) —
  a legibility debt, not a release blocker.

## 20. v0.3 Release Acceptance Criteria

- Clean-environment install succeeds (documented wheel/sdist install at
  minimum; PyPI is should-have).
- `pcae init` / task-lifecycle quick-start works end-to-end from a fresh
  clone.
- Reference governed workflow (§8) works end-to-end.
- The RB-1 intake path governs at least one real external-agent-
  proposed change.
- Deny path proven (task-scope violation caught by `pcae check`).
- Allow path proven (`pcae promote` on a reviewed, real change).
- Audit/evidence output produced and inspectable
  (`pcae project-state --json` or equivalent).
- Commit/push governance exercised as part of the demo, not just in
  isolation.
- Clean quick-start documentation exists and was exercised by someone
  other than the implementer if feasible.
- No open Blocking findings; fast_green baseline clean (deselecting
  only pre-existing, attributed, documented failures per existing
  project convention).
- A tagged `v0.3.0-rc1` (see §31 for exact naming).

## 21. Release Non-Goals

v0.3 explicitly does not promise: a general-purpose autonomous coding
harness; mandatory FIDO2/WebAuthn; a multi-tenant SaaS; enterprise SSO;
full centralized fleet governance; every possible agent-harness
integration; unattended maximum-capability execution.

## 22. Next 3–5 Governed Phases (Central Deliverable)

1. **149O.20L.7O.2U.1 — Reference Adapter Contract Freeze.**
   Objective: freeze the exact intake contract (schema + CLI surface)
   for feeding one external agent's proposed change into the existing
   EPR/promotion chain. Critical path because RB-1 cannot be
   implemented against a moving contract. Expected change: a frozen
   schema/contract document, no runtime behavior change. Acceptance:
   contract reviewed and frozen; `pcae check` passes; no `src/pcae/**`
   runtime change. Independent verification: not required (design-only,
   like 2P/2U itself) unless the contract materially changes an
   existing authority boundary.

2. **149O.20L.7O.2U.2 — Reference Adapter Implementation.**
   Objective: implement the frozen intake path as a real, tested CLI
   command wired to the existing execution-activation/promotion chain.
   Critical path: this is RB-1 itself. Expected production change:
   new `src/pcae/**` command + tests; no change to the promotion/
   rollback authority model (still human-gated). Acceptance: end-to-end
   test demonstrating a real proposed change captured, reviewed, and
   promoted or refused. Independent verification: **required** — this
   phase adds a new authority-adjacent surface (an intake boundary), so
   this repo's own doctrine (independent-verification-before-risky-
   implementation) applies.

3. **149O.20L.7O.2U.3 — Reference Adapter Independent Verification.**
   Objective: independently verify 2U.2 (different authority boundary
   than governed implementation itself — matches this repo's own
   phase-count-discipline exception list, §23). Expected outcome:
   Blocking/Non-Blocking findings resolved or explicitly deferred;
   no promotion/rollback safety property weakened.

4. **149O.20L.7O.2U.4 — Deny/Allow Demo and Quick-Start Documentation.**
   Objective: build the reproducible demo (§10) and the curated 5-minute
   quick-start (§13, RB-3), batched together since both are
   documentation/demo-surface work with the same verification story
   (no production authority change). Expected change: demo script/repo
   reference + README/docs quick-start section. Acceptance: a fresh
   clone can follow the quick-start and reproduce the deny+allow demo.
   Independent verification: not required (no authority-boundary
   change) unless the demo reveals a defect.

5. **149O.20L.7O.2U.5 — v0.3 Release Candidate Preparation.**
   Objective: quality-gate re-verification (fast_green, full suite),
   release-readiness checks, packaging, `v0.3.0-rc1` tag/release
   (mirrors the v0.1.0-rc1 → v0.1.0-equivalent pattern used previously,
   see §31). Critical path: this is the release itself. Expected
   change: version metadata, CHANGELOG, release notes, tag. Acceptance:
   release-readiness checks pass; RC published. Independent
   verification: recommended (release/deployment-effect phase, per
   §23's own exception list) but scoped narrowly to release-readiness
   evidence, not a full re-audit.

This avoids "analysis → analysis → architecture → architecture" — only
2U.1 is contract-only, and it is a short, narrowly-scoped freeze
immediately followed by real implementation.

## 23. Phase-Count Discipline Applied

2U.2 (implementation) and 2U.3 (independent verification) are kept as
separate phases because they cross a materially different authority
boundary (a new intake surface touching the existing promotion chain) —
this matches the discipline's own stated exception ("independent
verification... materially different authority boundary"). 2U.4
(demo+docs) is deliberately batched rather than split into a demo phase
and a separate docs phase, since both share the same implementation
surface (documentation/demo artifacts) and the same verification story
(no authority change). 2U.5 (release) is kept separate as a
deployment-effect phase per the same exception list.

## 24–26. 30/60/90-Day Targets

**30-day target**: 2U.1 (contract freeze) and 2U.2 (reference adapter
implementation) complete and independently verified (2U.3) — a real,
working, demoable governed intake path exists, even before the polished
public demo/docs are built.

**60-day target**: 2U.4 (deny/allow demo + quick-start docs) complete;
Permission Broker consumption (should-have, §14) started if time
permits, not required.

**90-day target**: `v0.3.0-rc1` tagged and published (2U.5), meeting the
acceptance criteria in §20. If 30/60-day targets land on schedule, this
is achievable meaningfully sooner than 90 days — the critical path
identified here is short (5 phases, one implementation-sized) compared
to the ~3,200-commit Fast-Green/FGSC/HATP detour the project has been on
since v0.2.0. This roadmap is not padded to fill 90 days.

## 27. Demo / Reference Project Decision

Yes, v0.3 needs one canonical reference demo (§10) — a small, real
repository (can be a purpose-built toy repo, not a production codebase)
showing PCAE governing a real AI coding task from proposal through
execution/commit/push, proving: task-scope deny, human-gated allow via
`pcae promote`, and audit-trail evidence. Not implemented in this phase.

## 28. Install / Onboarding Assessment

Current friction: install is GitHub-release-wheel/sdist only (no PyPI);
first-use requires understanding `pcae init` + task-contract concepts
before any CLI command is useful; the CLI's hundreds of subcommands
(most of them architecture-preview/dry-run) dominate `--help` output
and `pcae --help`'s own listing, which is confusing for a first-time
user (confirmed directly by this phase's own `pcae phase complete
--help` / `pcae --help` inspection). None of this requires
domain/DNS/TLS/VPN/FIDO2/WebAuthn — the enterprise track is correctly
decoupled already. Requirements for v0.3: a documented install command
(PyPI should-have), a minimal default task-contract template so
`pcae task new` doesn't require reading the full contract schema first,
and the curated core-command quick-reference from §13.

## 29. Documentation Requirements (Minimum for Release)

README positioning (revise "Current Capabilities" framing to lead with
the v0.3 headline, not the architecture catalog); a 5-minute quick-start
doc; a "first governed task" walkthrough; an execution/governance model
explainer; a supported/unsupported capability table (this phase's §4
matrix is a direct input); a security model summary; explicit
"Enterprise Extension" labeling for HATP/HMIC/WebAuthn material; no
v0.2→v0.3 migration steps are anticipated since v0.3 is additive
(intake path is new, not a breaking change to existing commands) — this
should be confirmed, not assumed, during 2U.2.

## 30. Release Packaging Assessment

Current packaging: `pyproject.toml`-based build producing wheel/sdist,
manually attached to GitHub releases via `gh release create` (per
v0.1.0-rc1/v0.2.0 asset lists). No `pcae`-governed release-automation
command exists (confirmed in §4 — "Publication workflow: Implemented,
not surfaced"). Work needed for `v0.3.0-rc1`: version bump in
`pyproject.toml`, updated CHANGELOG/release notes (mirroring the
v0.1.0-rc1/v0.2.0 notes structure read in §1–2), a fresh wheel/sdist
build + smoke-install verification (as done for v0.1), and `gh release
create` with the built assets. No tag/release created in this phase.

## 31. Versioning Recommendation

Established convention in this repo: `v0.1.0-rc1` (prerelease) preceded
a full `v0.2.0` release without a `v0.2.0-rc1` step ever having been
published as a separate tag (only `v0.1.0-rc1` and `v0.2.0` tags exist).
**Recommendation**: publish `v0.3.0-rc1` first (matching the only
precedent this repo has for a first-of-major-version release), then
promote to `v0.3.0` once the acceptance criteria in §20 are met and any
RC feedback is incorporated. This is a recommendation, not a silent
freeze — flagged for confirmation, not because the evidence is
ambiguous (it isn't: there is exactly one applicable precedent) but
because it commits the project to a specific release cadence.

## 32. Security / Governance Bar

No proposed item in this plan bypasses the permission broker (it isn't
enforced by anything yet, and remains should-have, not a shortcut),
bypasses the trust gate, weakens fail-closed behavior, removes
auditability, bypasses governed commit/push, or enables unsafe
execution. RB-1's intake path explicitly reuses the *existing*
human-gated promotion/rollback chain rather than adding a new mutation
path — this was a deliberate design constraint in §9 and §12, not an
oversight.

## 33. What Not to Continue Now

Per the handoff and confirmed by this phase's evidence: FGSC mechanics,
2P quarantine, HATP activation, WebAuthn RP-ID/domain work, DNS/TLS/VPN,
DeepSeek private research, and further historical architecture cleanup
are all deferred unless a new real defect surfaces. None of the next 5
phases (§22) touch any of these.

## 34. User Decision Checkpoints

Two decisions are surfaced for the human rather than silently frozen:

1. **Which external agent/tool the reference adapter (§12) targets
   first** — e.g., a Claude-Code-specific integration vs. a generic
   file-diff/JSON intake usable by any agent. This materially changes
   the shape of 2U.1/2U.2 and was not fully resolved by 2P (2P discussed
   the *strategy* of "bring your existing agent under governance" but
   did not name a first integration target).
2. **Release candidate timing/cadence confirmation** (§31) — the
   `v0.3.0-rc1` recommendation is evidence-supported but is a genuine
   release-cadence commitment, not a fact derivable from code alone.

No other major product/architecture decision in this plan was left open
— HATP/WebAuthn positioning, target user, and headline all reuse 2P's
already-reconciled conclusions, which current evidence does not
invalidate.

## 35. v0.3 Critical-Path Graph

```
released v0.2.0
      |
      v
149O.20L.7O.2U (this phase — plan frozen)
      |
      v
2U.1 reference-adapter contract freeze
      |
      v
2U.2 reference-adapter implementation  ---->  [independent verification: 2U.3]
      |
      v
2U.4 deny/allow demo + quick-start docs
      |
      v
2U.5 release-candidate prep, quality gates, packaging
      |
      v
v0.3.0-rc1  -->  v0.3.0

Deferred / enterprise branch (parallel, non-blocking):
HATP activation -- FIDO2 enrollment -- remote WebAuthn infra
-- deployment-binding / RP-ID -- multi-tenant control plane
```

## 36. Success Metrics

- Time-to-first-governed-action from a clean clone (target: under 10
  minutes including install).
- Number of required setup steps for the core path (target: init + one
  task-new + one check — no domain/FIDO/TLS step).
- Successful allow/deny demo reproducible by someone other than the
  implementer.
- Auditable evidence produced and independently readable
  (`pcae project-state --json` or equivalent, not hand-authored prose).
- At least one external-repo (non-pcae-harness) install/test success.

## 37. Release Risk Register (Top Risks Only)

| Risk | Probability | Impact | Mitigation | Release blocker? |
|---|---|---|---|---|
| RB-1 reference-adapter scope creeps into a second execution/authority path | Medium | High (would reopen the safety-bar concerns in §32) | Freeze the contract in 2U.1 before implementation; independent verification in 2U.3 | Yes if it creeps |
| No PyPI publication raises adoption friction below the 5-minute target | Medium | Medium | Should-have, not launch-blocking; document wheel-install path clearly | No |
| Demo repo is unconvincing/too contrived | Low-Medium | Medium | Use a real (if small) governed change, not a synthetic fixture | No, but should be revisited if 2U.4 output is weak |
| Team re-opens Fast-Green/FGSC/HATP work mid-critical-path | Medium (historical pattern: ~3,200 commits of detour since v0.2.0) | High (delays v0.3 indefinitely) | This document + §33's explicit "what not to continue now" list | Yes if it recurs |

## 38. Mac / Dell Deployment Roles

v0.3's core adoption path (§8) requires no Dell reference deployment —
by design, no domain/TLS/hardware dependency exists in the core path.
**Recommendation**: v0.3 developer quickstart works locally on Mac-only,
with no remote Dell dependency; Dell remains relevant only to the
deferred Enterprise/HATP/WebAuthn branch (§35), on its own independent
cadence, unblocked by and not blocking v0.3 core. This is a
recommendation grounded in the fact that the core journey (§8) touches
no deployment-topology-specific capability; it does not require a new
human decision (§34 already lists the two genuine open decisions, and
this is not one of them, since v0.2's own release notes already
establish the no-infrastructure posture).

## 39. Enterprise-Extension Positioning

Suggested wording: *"Optional hardware-backed enterprise trust layer"*
for HATP/FIDO2/WebAuthn — communicates real, substantial architecture
work without implying it is production-ready or required. Do not market
HATP/WebAuthn as shipped/enabled in v0.3 release notes; label explicitly
as "architecture complete, not yet activated" per §16–17.

## 40. DeepSeek / Agent-Harness Positioning

Release messaging should emphasize: **"bring your existing coding agent
under governance"** — this claim is now partially supportable (task
scope + promotion/rollback chain already exist) but not fully
supportable until RB-1 (§18) ships a real intake path connecting an
external agent's actual proposed action to that chain. Until then, the
honest claim is "governs your repository's task scope and change
history around whatever agent you use," not yet "governs your agent's
live actions" — §9's gap is exactly this distinction. The private
DeepSeek research repository remains out of scope and was not inspected
in this phase.

---

## Final Decision Format

**PCAE v0.3 IS:** a lightweight, install-in-minutes governance layer
that gates AI-agent task scope, validates completion claims against
real repo state, and produces an audit trail around an existing coding
agent — not a new agent, not new infrastructure.

**PRIMARY USER:** an individual AI-assisted developer or small team
already running an existing coding agent on a real repository.

**MUST SHIP:** a real intake path connecting an external agent's
proposed change to PCAE's existing execution-activation/promotion/
rollback chain (RB-1); a reproducible deny+allow demo with audit
evidence (RB-2); a curated 5-minute quick-start (RB-3).

**WILL NOT BLOCK v0.3:** HATP activation, FIDO2/WebAuthn infrastructure,
domain/DNS/TLS/VPN setup, Permission Broker enforcement (should-have),
PyPI publication (should-have), any further Fast-Green/FGSC work.

**NEXT PHASE:** 149O.20L.7O.2U.1 — Reference Adapter Contract Freeze.

**ESTIMATED CRITICAL-PATH PHASE COUNT:** 5 (2U.1 through 2U.5).

**MAJOR HUMAN DECISIONS REQUIRED BEFORE IMPLEMENTATION:** (1) which
external agent/tool the reference adapter targets first; (2) confirm
`v0.3.0-rc1` as the next release-candidate tag name.

## Expected Verdict

PCAE v0.3 RELEASE EXECUTION PLAN — FROZEN.

v0.1 / v0.2 RELEASE BASELINE: reconstructed from actual published
GitHub releases (`v0.1.0-rc1`, `v0.2.0`).

v0.3 PRIMARY VALUE: governed, scope-bounded AI-assisted coding sessions
with an audit trail — not yet a full governed-execution control plane,
but a concrete step toward one via the RB-1 intake path.

CORE ADOPTION PATH: no domain / no FIDO2 / no WebAuthn infrastructure
required.

ENTERPRISE TRUST: optional / deferred from release-blocker status.

CRITICAL PATH: short (5 phases), implementation-oriented — one contract
freeze, one implementation phase, one independent verification, one
demo/docs phase, one release-candidate phase.

FAST GREEN / FGSC: no longer on critical path.

NEXT ENGINEERING PHASE: 149O.20L.7O.2U.1 — Reference Adapter Contract
Freeze.
