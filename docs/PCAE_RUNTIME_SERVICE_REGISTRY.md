# PCAE Runtime Service Registry & Plugin Discovery Architecture

**Frozen by**: Phase 110C | **Status**: architecture/design only — no
plugin registry implementation, plugin loading, plugin discovery
execution, dependency injection framework, runtime execution, command
authorization, command denial, behavior-changing integration, shell
mediation, subprocess mediation, backend invocation, adapter invocation,
execution enablement, execution capability, Permission Broker
enforcement, audit persistence, rollback execution, emergency stop,
Telegram inbound, REST server, web server, daemon, background workers,
automatic apply, or command execution is performed by this document or
this phase.

## Purpose

Design how the PCAE Runtime discovers, resolves, validates, and reasons
about plugins without directly coupling to concrete implementations.
110A froze the Runtime and its seven-stage pipeline; 110B froze what
every plugin category's *contract* must contain. Neither phase
described how the Runtime finds a plugin, decides it is compatible, or
chooses among several candidates that declare the same capability — that
missing layer is the Runtime Service Registry, designed (not
implemented) here. This document freezes architecture; it implements no
registry, loads no plugin, executes no discovery, and injects no
dependency.

This document builds on, and changes none of:

- `docs/PCAE_RUNTIME_ARCHITECTURE.md` (110A) — the Runtime, the
  seven-stage pipeline, the ten plugin category names, the nine runtime
  services (including the already-named-but-undesigned Plugin Registry
  service this document now designs), the eleven principles, and the
  eight-state runtime state model.
- `docs/PCAE_RUNTIME_PLUGIN_CONTRACTS.md` (110B) — the eighteen-field
  contract model, the ten category contracts, the ten-class capability
  taxonomy, the eight-state plugin lifecycle model, compatibility/
  versioning rules, and the ten security boundaries.
- `docs/ROADMAP.md`'s Long-Term Runtime Vision (110B) — "Pluggable
  first. Connected second. Automated third. Executable last."

## Core Architectural Principle

```
Runtime orchestrates.
Registry resolves.
Plugins implement.
```

The Runtime (110A §1) sequences intents through the pipeline and
enforces contracts between stages — it does not itself know which
concrete plugin instance will handle a given stage. The Registry, framed
by this document, is the single resolution layer that turns "I need
capability X" into "here is a compatible, healthy plugin instance that
declares X" — it does not sequence anything and does not decide policy.
Plugins (110B) implement exactly the contract their category requires —
they do not discover each other, do not orchestrate, and do not resolve
their own compatibility.

Extending the principle with this phase's own addition:

```
Pluggable first.
Connected second.
Automated third.
Executable last.
Discoverable always.
```

"Discoverable always" is not a fifth sequential stage after
"Executable last" — it is a standing property that must hold at every
one of the other four stages simultaneously. A plugin that is merely
`defined` (110B §4) must still be discoverable as *existing*, even
before it is `registered`; a plugin that is `retired` must still be
discoverable as *having existed*, for audit and compatibility-history
purposes. Discoverability is the one property this ordering does not
gate behind the others.

## 1. The Runtime Service Registry

**Definition.** The Registry is the canonical resolution layer sitting
between the Runtime and every plugin instance. It answers exactly one
class of question: *"given a required capability (and any constraints),
which registered plugin instance(s) can satisfy it, and what do I know
about each candidate before the Runtime chooses one?"* It is
architecturally analogous to, and generalizes, two things that already
exist narrowly today: `PolicyRegistry` (108B, serves only the Permission
Broker's `PolicyRule`s) and `INTEGRATION_REGISTRY` (109C, a static,
hand-authored tuple of four `IntegrationRegistryEntry` records). Neither
existing registry does compatibility checking, health visibility, or
capability-based lookup — the Registry designed here is the
generalization that would eventually make both existing registries
special cases of one architecture, not a replacement for either
(neither is modified by this phase).

**Position in the pipeline.** The Registry is not a pipeline stage
(110A §2) — it does not sit "between" Intent Pipeline and Decision
Pipeline, for example. It is a cross-cutting resolution service every
stage may consult when it needs a concrete plugin instance, exactly as
Session/Task/Phase (110A §4) are cross-cutting Runtime Services every
stage may consult for context, not stages themselves.

**What the Runtime must not know.** The Runtime's sequencing logic
(110A §1) must never hardcode a concrete plugin class, module path, or
instance identity. It asks the Registry for "a Decision Plugin
compatible with this intent's requirements" — never "the
`FooDecisionPlugin` class." This is the direct architectural reason a
Registry is needed at all: without it, "Runtime orchestrates" would
collapse into "Runtime orchestrates *and* hardcodes," violating
Principle 2 (Pluggable, 110A §6) by construction.

**What plugins must not know.** No plugin instance may discover or call
another plugin instance directly (restated from 110B §6's "Plugins do
not own: discovering/calling each other directly"). A Policy Plugin that
needs Context Plugin output does not look up a Context Plugin itself —
it receives that context because the Runtime, via the Registry,
assembled it beforehand and handed it in as an Input (110B §1, field 5).
Plugin-to-plugin lookup would create a direct coupling the Registry
exists specifically to prevent.

**What the Registry must not own.** The Registry resolves; it does not
orchestrate, decide, execute, or persist (§4 below enumerates this
precisely). A Registry that started sequencing pipeline stages would be
a second Runtime in disguise; a Registry that started composing policy
decisions would be a second Decision Plugin in disguise. Keeping
"resolves" as the Registry's sole verb is what keeps the three-part
principle a genuine separation of concerns rather than a relabeling.

**Current implementation status: not implemented.** No file, class, or
function implementing a Registry exists in `src/pcae/` today. The
Runtime Service Registry entry in 110A §4's service table already named
"Plugin Registry" as `not_implemented`; this document is the design that
a future implementation phase would build against, not the
implementation itself.

## 2. Service Discovery

Discovery is how the Registry comes to know what it knows about a
candidate plugin, before any capability resolution (§4) is attempted
against that knowledge. Eight facets are frozen:

| Facet | What it captures | Precedent |
|---|---|---|
| **Plugin identity** | A stable Plugin ID (110B §1, field 1) — never reused, never renumbered. | `COMP-NNN` (107B), `INT-NNN` (109C), `POL-NNN` (108B) — every existing ID scheme in this codebase is already permanent-once-assigned. |
| **Plugin type** | Which of the ten categories (110A §3, 110B §2) the instance belongs to — exactly one. | 110B §1, field 2. |
| **Capability declarations** | Which capability classes (110B §3) the instance honestly claims — `observe`, `advise`, etc. | 110B §1, field 8; 110B §3's "a plugin must declare capabilities honestly." |
| **Version compatibility** | The instance's own semantic version (110B §5) and which Runtime/contract versions it is compatible with. | 110B §5's versioning/compatibility rules, unmodified. |
| **Health status** | The instance's current Health Reporting output (110B §1, field 10). | Precedent: `pcae hooks status`/`pcae doctor` (108E) already report a subsystem's health today, non-pluggably. |
| **Lifecycle state** | Which of the eight plugin lifecycle states (110B §4) the instance currently occupies. | 110B §4, unmodified. |
| **Security posture** | Which of the ten security boundaries (110B §6) the instance's contract addresses, and how. | 110B §1, field 13; 110B §6. |
| **Current implementation status** | `not_implemented` / `foundation_implemented` / `partially_implemented` — never `implemented` (110B §1, field 18, unchanged). | 110B §1, field 18. |

Discovery is read-only with respect to the plugin instances it
inspects — the Registry observes these eight facets, it does not compute
or influence any of them (a plugin's own Health Reporting hook produces
its health status; the Registry only surfaces what that hook reports).

## 3. Plugin Manifest Concept (Future — No Implementation)

A future implementation phase would need every registered plugin
instance to publish a **manifest** — a structured, static declaration
the Registry reads at discovery time. This document freezes what such a
manifest *would contain*, not its file format, serialization, or
loading mechanism (all explicitly out of scope, per the No-Go list).

| # | Manifest field | Corresponds to |
|---|---|---|
| 1 | Plugin ID | 110B §1, field 1 |
| 2 | Plugin name | *(new — human-readable, distinct from the stable ID)* |
| 3 | Plugin type | 110B §1, field 2 |
| 4 | Version | 110B §1, field 11 |
| 5 | Compatible runtime version | 110B §5's compatibility rules, made concrete per-instance |
| 6 | Capabilities provided | 110B §1, field 8 (Capability declaration) |
| 7 | Capabilities required | *(new — a plugin instance may itself depend on another capability being resolvable, e.g. an Audit Plugin instance requiring a Storage capability)* |
| 8 | Dependencies | *(new — generalizes "capabilities required" into any other Plugin ID or capability class this instance cannot function without)* |
| 9 | Lifecycle hooks | 110B §1, field 7 |
| 10 | Configuration schema | 110B §1, field 9 (Configuration model), expressed as a schema rather than a live configuration value |
| 11 | Security boundaries | 110B §1, field 13 |
| 12 | Evidence requirements | 110B §1, field 14 |
| 13 | Approval requirements | 110B §1, field 16 |
| 14 | Audit expectations | 110B §1, field 17 |
| 15 | Current status | 110B §1, field 18 |

Thirteen of the fifteen manifest fields map directly onto an existing
110B contract field; only "Plugin name" (field 2) and "Capabilities
required" / "Dependencies" (fields 7–8, closely related) are new to this
document — introduced because manifest-level *discovery* needs a
human-readable name and an explicit dependency graph in a way an
individual plugin *contract* (110B, scoped to one plugin in isolation)
did not need to express.

**No manifest schema, file format, parser, or loader is implemented by
this phase.** The manifest is a concept a future phase would need to
give a concrete shape (JSON Schema, a Python dataclass, a TOML file) —
this document only freezes *what information* it must carry.

## 4. Capability Resolution

The canonical resolution flow, once a Registry exists to run it (not
implemented by this phase):

```
Intent:      "Run tests"
                |
                v
Runtime:     needs capability `test.execution` (or `command.test`)
                |
                v
Registry:    resolves compatible plugin candidates
                |
                v
Runtime:     selects one candidate according to policy
                |
                v
Plugin:      implements the capability
```

Five steps, each with a single owner:

1. **Intent arrives** at the Runtime (110A §2, Intent Source → Runtime).
   The intent itself does not name a plugin — it names, directly or
   indirectly, a *need*.
2. **The Runtime translates that need into a capability identifier** —
   a dotted string like `test.execution` or `command.test` (illustrative
   naming only; no capability-identifier grammar is frozen by this
   phase). This step is the Runtime's own responsibility, not the
   Registry's — the Registry never guesses what a Runtime *meant*.
3. **The Registry resolves candidates.** Given a capability identifier,
   it returns every plugin instance whose manifest (§3) declares that
   capability *and* whose discovery facets (§2) currently indicate
   compatible version, healthy status, and an appropriate lifecycle
   state (`available`, 110B §4). The Registry never itself picks a
   winner among multiple candidates — that would be a policy decision,
   which the Registry does not own (§5).
4. **The Runtime selects** one candidate from the Registry's returned
   set, "according to policy" — meaning whatever selection policy a
   future phase defines (e.g. highest compatible version, a configured
   preference, round-robin), consulted the same way the Decision
   Pipeline consults the Permission Broker (110A §2) today: as a
   distinct, named step the Runtime performs, not something the
   Registry does on the Runtime's behalf.
5. **The plugin implements** the capability, strictly within its
   category contract's allowed responsibilities (110B §2).

**No implementation.** This flow is illustrative and architectural; no
capability identifier grammar, no resolution algorithm, and no
selection-policy mechanism is implemented by this phase.

## 5. Registry Responsibilities

**The Registry owns:**

- Registration metadata (which plugin instances exist, and their
  manifests, §3).
- Discovery (§2 — surfacing the eight facets for any registered
  instance).
- Compatibility checks (version compatibility, per 110B §5's rules,
  applied per-instance).
- Capability lookup (§4, step 3 — resolving candidates for a requested
  capability).
- Plugin health visibility (surfacing, not computing, each instance's
  Health Reporting output).
- Lifecycle visibility (surfacing, not driving, each instance's current
  lifecycle state, 110B §4).
- Dependency metadata (surfacing the manifest's "capabilities required"
  / "dependencies" fields, §3, fields 7–8).
- Current availability (whether an instance is presently reachable —
  narrower than lifecycle state's `available`, since an instance could
  be lifecycle-`available` yet transiently unreachable, e.g. a network
  partition for a remote plugin).

**The Registry does not own:**

- Orchestration (that is the Runtime's job, 110A §1).
- Policy decisions (that is the Policy/Decision Plugin categories' job,
  110B §2.2–§2.3).
- Approval decisions (that is the Approval Plugin category's job, 110B
  §2.4).
- Execution (that is the Execution Adapter Plugin category's job, 110B
  §2.5 — the Registry may tell the Runtime *which* adapter is available,
  it never invokes one).
- Audit persistence (that is the Audit Plugin category's job, 110B
  §2.6).
- Rollback execution (that is Rollback Boundary/`COMP-008`'s job, 107B —
  not implemented anywhere, including here).

This split mirrors, at the plugin-infrastructure layer, the same
separation 108B established at the policy layer: `PolicyRegistry`
evaluates every rule and returns results, but `_compose()` — a distinct
function — decides what those results mean. The Registry is this
phase's `PolicyRegistry`-equivalent for plugins in general: it surfaces
facts, it does not decide what to do with them.

## 6. Plugin Responsibility Boundaries

**Plugins own:**

- Declared capability implementation (exactly what their manifest, §3,
  and category contract, 110B §2, say they implement — no more).
- Local health signal (the plugin instance's own Health Reporting hook,
  110B §1 field 10 — the Registry surfaces this, but the plugin produces
  it).
- Lifecycle hooks (110B §1 field 7 — a plugin instance responds to
  lifecycle transitions the Registry/future implementation drives, but
  the *response* — e.g. what "become healthy" means for this specific
  plugin — is the plugin's own logic).
- Bounded inputs/outputs (exactly its category's input/output schema
  description, 110B §2 — never more, never less).
- Evidence emission where applicable (110B §1 field 14 — for categories
  where Evidence Requirements is non-trivial, e.g. Execution Adapter,
  Audit).

**Plugins do not own:**

- Global orchestration (Runtime's job).
- Self-authorization (110B §6, boundary 4, unchanged: "No plugin may
  grant itself... an approval, decision, or capability it was not
  explicitly configured with").
- Bypassing the Permission Broker (110B §6, boundary 9, unchanged).
- Bypassing approval (110B §6, boundary 8, unchanged).
- Bypassing audit (110B §6, boundary 10, unchanged).
- Discovering or calling each other directly (§1 above, "What plugins
  must not know").

Every "do not own" item here is either a direct restatement of an
already-frozen 110B security boundary or the direct architectural
consequence of the Registry existing as the sole discovery path (the
last item). No new prohibition is invented by this section — this
section exists to collect the plugin-facing consequences of §5's
Registry-facing responsibility split into one place.

## 7. Plugin Classes: Infrastructure vs. Capability

Two classes are distinguished among the ten plugin categories (110A §3,
110B §2):

**Infrastructure plugins** — provide services other plugins and the
Runtime itself depend on, but do not themselves decide, approve, or
execute anything intent-specific:

- Identity Plugin
- Storage Plugin
- Notification Plugin
- Audit Plugin
- Context Plugin

**Capability plugins** — participate directly in evaluating or acting on
a specific intent's pipeline journey:

- Intent Source Plugin
- Policy Plugin
- Decision Plugin
- Approval Plugin
- Execution Adapter Plugin

**Why the distinction matters:**

- **Different discovery cardinality.** A given Runtime typically needs
  *one* healthy instance of most Infrastructure categories at a time
  (one Storage backend, one Identity resolver) — resolving multiple
  candidates and picking one (§4) is the common case for Capability
  plugins (e.g. several Execution Adapter Plugins for different
  execution targets), less so for Infrastructure plugins.
- **Different failure blast radius.** An unavailable Infrastructure
  plugin (e.g. Storage) can silently degrade *every* Capability plugin
  that depends on it (§3's manifest "dependencies" field exists
  specifically to make this dependency explicit rather than discovered
  the hard way at runtime). An unavailable Capability plugin (e.g. one
  specific Execution Adapter) degrades only the specific intents needing
  that exact capability.
- **Different security posture emphasis.** Infrastructure plugins
  disproportionately carry boundaries 5–7 from 110B §6 (no hidden
  network access, no secret leakage, no untracked mutation) since they
  are where credentials, records, and delivery channels live. Capability
  plugins disproportionately carry boundaries 3–4, 8–10 (no implicit
  execution, no self-authorization, no bypass of approval/broker/audit)
  since they are where an intent's fate is actually decided or acted on.
- **Different long-term vision framing.** The roadmap's Long-Term
  Runtime Vision (110B, `docs/ROADMAP.md`) names intent sources (Claude,
  Codex, DeepSeek, Telegram, etc.) and execution targets (shell, git,
  filesystem, backend agents, network calls, cloud runners) as the two
  most consequential plugin populations precisely because they are
  Capability plugins (Intent Source and Execution Adapter respectively)
  — the roadmap's "Pluggable first... Executable last" ordering is a
  Capability-plugin concern first and foremost; Infrastructure plugins
  are what makes that ordering *observable and auditable* rather than
  what the ordering is fundamentally about.

## 8. Static vs. Dynamic Runtime Model

Two distinct models are frozen, and this document explicitly designs
only the first:

**Static runtime** — what exists independent of any specific intent
being processed right now:

- Architecture (110A, unchanged).
- Contracts (110B, unchanged).
- Registry (this document — resolution structure and rules).
- Plugin metadata (manifests, §3; discovery facets, §2).
- Compatibility (110B §5's rules, and this document's §5 compatibility
  checks).

**Dynamic runtime** — what exists only while a specific intent is being
processed:

- Session (110A §4 Runtime Service, already partially implemented via
  `pcae session bootstrap`).
- Task (110A §4 Runtime Service, already partially implemented via
  `pcae task`).
- Phase (110A §4 Runtime Service, already partially implemented via
  `pcae phase`).
- Intent (110A §8 state model — the specific `Intent` → `Observed` →
  ... progression for one proposed action).
- Approval (§6 above — a specific human decision for a specific intent,
  not implemented anywhere today).
- Broker decision (108A, already implemented, but ephemeral per-call —
  a `PermissionBrokerDecision` exists only for the duration of one
  `evaluate()` call and is discarded by every current observation
  integration, 109B–109D).
- Execution state (110A §8 — `Executable`/`Executed`/etc., not
  implemented anywhere today).

**This document designs only the static runtime.** The dynamic runtime
— how a specific intent's session/task/phase/approval/decision/execution
state would actually flow through a live Registry at runtime — is
explicitly **a future phase, not implemented here.** This mirrors 110A's
own distinction between the Runtime's architecture (frozen) and its
concrete entry point (not designed, left to a future phase) and 110B's
distinction between a plugin's contract (frozen) and any live plugin
instance (none exist). Conflating static and dynamic runtime design in
one phase would risk designing the dynamic behavior around a
still-unvalidated static structure — this document deliberately avoids
that risk by stopping at the static boundary.

## No-Go Confirmations

No plugin registry implementation. No plugin loading. No plugin
discovery execution. No dependency injection framework. No runtime
execution. No command authorization. No command denial. No
behavior-changing integration. No shell mediation. No subprocess
mediation. No backend invocation. No adapter invocation. No execution
enablement. No execution capability. No Permission Broker enforcement.
No audit persistence. No rollback execution. No emergency stop. No
Telegram inbound. No REST server. No web server. No daemon. No
background workers. No automatic apply. No command execution.
`implementation_status` remains unconditionally `"execution_unavailable"`
on every Permission Broker decision. Current maximum runtime state
remains `Observed` (110A §8, unchanged). Current maximum plugin
capability remains `observe` (110B §3, unchanged). No dynamic runtime
context is implemented — only the static runtime model is designed.
`v0.1.0-rc1` remains non-executing by design. v0.2 remains the autonomy
target (Level 3, not Level 4/5). GitHub Release for `v0.1.0-rc1` and
branch protection on `main` are unchanged. No new tag. No new GitHub
Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**110D — Runtime Registry Contract Freeze.**
