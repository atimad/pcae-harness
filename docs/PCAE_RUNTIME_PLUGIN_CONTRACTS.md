# PCAE Runtime Plugin Contracts

**Frozen by**: Phase 110B | **Status**: contract/freeze only — no plugin
loading, plugin registry implementation, dependency injection framework,
runtime execution, command authorization, command denial,
behavior-changing integration, shell mediation, subprocess mediation,
backend invocation, adapter invocation, execution enablement, execution
capability, Permission Broker enforcement, audit persistence, rollback
execution, emergency stop, Telegram inbound, REST server, web server,
daemon, background workers, automatic apply, or command execution is
performed by this document or this phase.

## Purpose

Turn the ten plugin categories `docs/PCAE_PLUGIN_MODEL.md` (110A) named
into stable, versionable **contracts**: the exact set of fields, allowed
and forbidden responsibilities, input/output shapes, lifecycle
requirements, security constraints, and failure behavior every future
plugin implementation in that category must satisfy. This document
freezes contract shape; it implements no plugin, loads no plugin,
executes no plugin, and injects no dependency. Every claim below is
either "already true today" (an existing, non-pluggable precedent named
in 110A) or "not implemented" (the contract itself, and any conforming
implementation).

This document builds on, and changes none of:

- `docs/PCAE_RUNTIME_ARCHITECTURE.md` (110A) — the Runtime, the
  seven-stage pipeline, the ten plugin category names, the nine runtime
  services, the eight interface contracts, the eleven principles, the
  capability matrix, and the eight-state runtime state model.
- `docs/PCAE_PLUGIN_MODEL.md` (110A) — the ten plugin categories' purpose,
  responsibilities, lifecycle, inputs, outputs, current status, and
  future implementation phase, at the level of detail 110A established.
- `docs/V0_2_AUTONOMY_CONTRACT.md` (107B), `docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md`
  (107C), and `src/pcae/core/permission_broker_foundation.py` (108A–108D)
  — unmodified.

## 1. Canonical Plugin Contract Model

Every plugin contract, regardless of category, is defined by exactly
eighteen standard fields. A future implementation phase that defines a
concrete Python protocol/ABC for any category must populate all
eighteen; a contract missing any field is incomplete, not partially
valid.

| # | Field | Meaning |
|---|---|---|
| 1 | **Plugin ID** | A stable, category-scoped identifier (e.g. `ISP-001` for the first Intent Source Plugin) — never reused, never renumbered, exactly as `COMP-NNN` (107B) and `INT-NNN` (109C) IDs are never renumbered once frozen. |
| 2 | **Plugin type** | Which of the ten categories (§2) this plugin belongs to. A plugin belongs to exactly one category; cross-category plugins are not permitted by this contract model. |
| 3 | **Purpose** | One-sentence statement of what the plugin exists to do — inherited from, and must not contradict, the category-level purpose (110A). |
| 4 | **Responsibilities** | The specific, enumerable things this plugin instance does, bounded by the category's allowed responsibilities (§2, per category) and never exceeding them. |
| 5 | **Inputs** | The exact shape of data the Runtime hands this plugin, conforming to the category's input schema description (§2). |
| 6 | **Outputs** | The exact shape of data this plugin returns to the Runtime, conforming to the category's output schema description (§2). |
| 7 | **Lifecycle hooks** | Which of the eight lifecycle states (§4) this plugin implementation responds to, and what it does at each transition. |
| 8 | **Capability declaration** | Which capability classes (§3) this plugin instance claims — a plugin must declare capabilities honestly; the Runtime is not obligated to trust an undeclared capability. |
| 9 | **Configuration model** | What configuration this plugin accepts, and its defaults — backed by the Configuration Runtime Service (110A §4). |
| 10 | **Health reporting** | How this plugin reports its own health (a required field for every category — mirrors `pcae hooks status`/`pcae doctor` precedents already working today for other subsystems). |
| 11 | **Versioning** | This plugin instance's semantic version, per §5's rules. |
| 12 | **Compatibility rules** | Which Runtime/contract versions this plugin instance is compatible with, per §5. |
| 13 | **Security boundaries** | Which of the ten security boundaries (§6) apply, and how this plugin instance satisfies each — every plugin must address all ten, not just the ones it considers relevant. |
| 14 | **Evidence requirements** | What evidence (if any) this plugin instance's actions must produce for the Evidence Pipeline (110A §2) — most categories require none until Execution Adapter/Audit are implemented, but the field is still mandatory to state explicitly. |
| 15 | **Failure behavior** | What this plugin instance does when it cannot complete its responsibility — must be fail-closed (§6) by default; any deviation must be justified in the contract, not silently assumed. |
| 16 | **Approval requirements** | Whether this plugin instance's action requires a prior Approval Plugin outcome before it may run — `None` for most categories today (since Approval itself is not implemented), but the field must be explicit rather than omitted. |
| 17 | **Audit expectations** | What, if anything, must be recorded about this plugin instance's invocation — distinct from Evidence Requirements (field 14, which covers the *result*); this field covers the *invocation itself*. |
| 18 | **Current implementation status** | One of: `not_implemented`, `foundation_implemented`, `partially_implemented`. No plugin contract may claim `implemented` — no plugin loading mechanism exists to make any contract runnable (No-Go, this phase). |

## 2. Contracts for the Ten Plugin Categories

Each category below inherits all eighteen fields from §1; only the
category-specific values are given here (fields that are identical
across every category — e.g. field 18 is `not_implemented` or
`foundation_implemented`/`partially_implemented` for every category, per
110A's own status table — are stated once per category rather than
repeated as boilerplate). For each category this section also states:
**allowed responsibilities**, **forbidden responsibilities**, **input
schema description**, **output schema description**, **lifecycle
requirements**, **security/no-go constraints**, **failure behavior**,
and **current status**.

### 2.1 Intent Source Plugin

- **Allowed responsibilities:** capture originator identity, action
  description, and timestamp; hand a well-formed intent to the Runtime.
- **Forbidden responsibilities:** evaluating policy; making any
  decision; executing anything; approving anything.
- **Input schema description:** whatever the source natively supplies
  (CLI arguments, an event payload, a trigger condition) — not
  standardized by this contract, since normalization is the *next*
  stage's job (Intent Pipeline, 110A §2), not this plugin's.
- **Output schema description:** one intent record: `{originator,
  action_description, timestamp}` at minimum.
- **Lifecycle requirements:** stateless between productions; must be
  independently `registered`/`configured`/`healthy` (§4) before the
  Runtime will accept intents from it.
- **Security/no-go constraints:** no implicit execution (an Intent
  Source Plugin producing an intent must never itself act on it); no
  hidden network access beyond what its own nature requires (e.g. a
  Telegram intent source legitimately needs network access to receive
  messages, but must declare it, not hide it).
- **Failure behavior:** if a source cannot produce a well-formed intent,
  it must produce no intent at all — never a partially-formed one the
  Runtime would have to guess-fill.
- **Current status:** `not_implemented` as a plugin. Informal precedent:
  every governed CLI command today is an ad hoc, non-pluggable intent
  source.

### 2.2 Policy Plugin

- **Allowed responsibilities:** evaluate one normalized intent against
  one policy concern; return a triggered/not-triggered result.
- **Forbidden responsibilities:** composing multiple results (that is
  the Decision Plugin's job, §2.3); mutating any state; short-circuiting
  another Policy Plugin's evaluation.
- **Input schema description:** a normalized request — the existing
  `PermissionBrokerRequest` (108A, frozen, unmodified) is the direct
  precedent for this shape.
- **Output schema description:** a `PolicyResult`-shaped value —
  `triggered`, `decision`, `decision_reason`, matched IDs — the existing
  `PolicyResult` dataclass (108B) is the direct precedent.
- **Lifecycle requirements:** stateless; every registered Policy Plugin
  must run for every intent (no short-circuiting, exactly as
  `PolicyRegistry.evaluate_all()`, 108B, already guarantees).
- **Security/no-go constraints:** fail-closed on malformed output —
  exactly `_sanitize_result()`'s existing behavior (108C, unmodified);
  no self-authorization (a Policy Plugin may never mark its own result
  `ALLOW` as final — only the Decision Plugin composes finality).
- **Failure behavior:** a raising or malformed Policy Plugin is
  sanitized into a fail-closed `DENY`-triggering result, never silently
  dropped — restating 108C's frozen guarantee as this contract's
  requirement.
- **Current status:** `foundation_implemented` as `PolicyRule` (108B) —
  twelve hardcoded instances exist, but none is independently
  registrable; not yet a general plugin category.

### 2.3 Decision Plugin

- **Allowed responsibilities:** compose every triggered Policy Plugin
  result into one decision, using fixed precedence
  (`DENY > HUMAN_REVIEW > ALLOW`).
- **Forbidden responsibilities:** evaluating policy itself (that is the
  Policy Plugin's job); executing anything; granting real authorization
  (every decision's `implementation_status` remains unconditionally
  `execution_unavailable`, unchanged since 108A).
- **Input schema description:** the tuple of every Policy Plugin's
  results for one intent.
- **Output schema description:** a `PermissionBrokerDecision`-shaped
  value (108A, frozen, unmodified).
- **Lifecycle requirements:** stateless; exactly one Decision Plugin
  composes a given intent's final decision (no multi-Decision-Plugin
  composition is defined by this contract — that would require a
  meta-composition rule this phase does not design).
- **Security/no-go constraints:** fail-closed on an empty result set —
  exactly `_compose()`'s existing behavior (108C, unmodified: "an empty
  results tuple cannot vouch for ALLOW and fails closed to DENY").
- **Failure behavior:** identical fail-closed posture; a Decision Plugin
  that cannot compose a valid decision must return `DENY`, never `None`
  and never a silent pass-through.
- **Current status:** `foundation_implemented` as `PermissionBroker`
  (108A) plus `_compose()` (108C) — exactly one implementation exists,
  and it is not independently pluggable.

### 2.4 Approval Plugin

- **Allowed responsibilities:** present a proposed action and its
  decision to a human; capture an explicit approve/deny action.
- **Forbidden responsibilities:** inferring approval from silence,
  timeout, or any automated signal (INV-003, 107B, restated here as a
  hard contract requirement, not merely a principle); executing
  anything; self-approving (an Approval Plugin may never approve an
  action it itself proposed — that would violate least privilege, §6).
- **Input schema description:** the intent plus the Decision Plugin's
  output.
- **Output schema description:** an explicit `ApprovalOutcome` —
  `approved` / `denied` / `no_response_yet` — never a fourth, implicit
  "assumed" state.
- **Lifecycle requirements:** may be long-lived (waiting on a human)
  rather than immediately returning, unlike Policy/Decision plugins.
- **Security/no-go constraints:** no bypass of human approval (this
  category exists specifically to prevent that bypass, so a
  non-compliant implementation would be a contradiction in terms); no
  hidden network access beyond what presenting the action to a human
  legitimately requires.
- **Failure behavior:** if approval cannot be captured (human
  unreachable, plugin error), the outcome is `no_response_yet` — the
  Runtime must not proceed as though approval occurred, ever.
- **Current status:** `not_implemented`. Corresponds to `COMP-003`
  (Human Approval Gate, 107B), whose own status note states enforcement
  is Phase 111A.

### 2.5 Execution Adapter Plugin

- **Allowed responsibilities:** mediate one specific execution
  mechanism (shell, backend, adapter) for an already-`Executable`
  intent (110A §8's state model).
- **Forbidden responsibilities:** accepting any intent not carrying
  proof of prior authorization; evaluating policy; approving anything;
  direct, unmediated execution outside its own declared mechanism.
- **Input schema description:** an authorized intent (state
  `Executable`, 110A §8).
- **Output schema description:** an `ExecutionOutcome` — success/failure
  and any resulting artifact.
- **Lifecycle requirements:** must refuse (fail-closed) any intent
  lacking proof of `Executable` state — this is the single most
  security-critical lifecycle requirement of any category in this
  document.
- **Security/no-go constraints:** every one of the ten security
  boundaries (§6) applies without exception; this category is the
  direct precedent for why the No-Go list bans "execution enablement" —
  a contract existing for this category does not enable it.
- **Failure behavior:** any execution failure must produce an
  `ExecutionOutcome` marked failed, consumed next by the Audit Plugin —
  never a silent failure.
- **Current status:** `not_implemented`. Corresponds to `COMP-004`
  (Shell Boundary) / `COMP-005` (Backend Boundary) / `COMP-006` (Adapter
  Boundary), 107B, all "not implemented."

### 2.6 Audit Plugin

- **Allowed responsibilities:** produce exactly one evidence record per
  execution attempt (success or failure).
- **Forbidden responsibilities:** executing anything; modifying an
  existing evidence record after it is written (audit records are
  append-only by contract); suppressing a record because the outcome was
  a failure.
- **Input schema description:** an `ExecutionOutcome` from an Execution
  Adapter Plugin.
- **Output schema description:** a durable `EvidenceRecord`, persisted
  via a Storage Plugin (§2.8).
- **Lifecycle requirements:** must persist before any Notification
  Plugin fires — the Audit → Notification interface contract (110A §5)
  restated here as this category's own requirement.
- **Security/no-go constraints:** no untracked mutation (every write
  this plugin performs is, by definition, the tracking mechanism itself
  — it cannot legitimately have untracked side effects of its own).
- **Failure behavior:** if a record cannot be persisted, the triggering
  execution attempt must be treated as unaudited and therefore
  incomplete — never treated as successfully audited by default.
- **Current status:** `not_implemented`. Corresponds to `COMP-007`
  (Audit Boundary, 107B), "not implemented."

### 2.7 Notification Plugin

- **Allowed responsibilities:** format and deliver a payload via one
  configured sink.
- **Forbidden responsibilities:** treating delivery as a substitute for
  an Audit Plugin's evidence record; inbound message handling (Telegram
  inbound remains explicitly out of scope, unchanged since the 94-series
  and restated in every phase's No-Go list since).
- **Input schema description:** a payload — today, a phase-completion
  report; in the future, potentially any Evidence Pipeline record.
- **Output schema description:** a `DeliveryOutcome` (sent / failed /
  skipped), itself worth storing via a Storage Plugin (110A §5,
  Notification → Storage interface).
- **Lifecycle requirements:** must report `DeliveryOutcome` for every
  attempt, including configured-but-unreachable sinks.
- **Security/no-go constraints:** no secret leakage (a Notification
  Plugin handling, e.g., a Telegram token must never include it in the
  payload it sends); no hidden network access — every sink's network use
  must be declared in its capability declaration (§1, field 8).
- **Failure behavior:** a failed delivery reports `failed`, never
  silently drops the payload and reports `sent`.
- **Current status:** **`partially_implemented`** — the one category
  with a real, working, exercised implementation: `pcae notify`
  (`COMP-009`), Telegram/stdout/filesystem/mock/noop sinks, exercised
  every phase via `pcae phase complete` with `PCAE_NOTIFY_ENABLED=1`. Not
  yet reorganized under this formal plugin contract — today's sinks are
  a fixed, hardcoded set.

### 2.8 Storage Plugin

- **Allowed responsibilities:** durable read/write of structured
  records on behalf of Audit, Notification, or a Runtime Service.
- **Forbidden responsibilities:** interpreting the meaning of what it
  stores (that is the caller's responsibility, not the Storage Plugin's);
  executing anything.
- **Input schema description:** a `(key, record)` pair for write, a
  `key` for read.
- **Output schema description:** write confirmation, or the requested
  record on read.
- **Lifecycle requirements:** typically long-lived (persists for the
  hosting process's lifetime); must report health (field 10) reflecting
  actual read/write availability, not just process liveness.
- **Security/no-go constraints:** no untracked mutation (every write
  must be attributable to the caller that requested it); no secret
  leakage (a Storage Plugin must not log record contents at a verbosity
  that could expose secrets it is asked to store).
- **Failure behavior:** a failed write must be reported as failed to the
  caller, never silently swallowed — a caller (e.g. Audit) that assumes
  a write succeeded when it didn't would violate its own "exactly one
  evidence record" contract (§2.6).
- **Current status:** `not_implemented` as a plugin. Ad hoc filesystem/JSON
  storage already exists throughout `.pcae/` (task contracts, session
  state, phase-completion metadata, phase reports) as a real, working,
  non-pluggable precedent.

### 2.9 Identity Plugin

- **Allowed responsibilities:** resolve an intent's originating
  identity, for use by Approval and Audit.
- **Forbidden responsibilities:** granting or denying anything (identity
  resolution and authorization are deliberately separate — least
  privilege, §6); executing anything.
- **Input schema description:** the raw intent or its Intent Source
  context.
- **Output schema description:** a resolved `Identity` value.
- **Lifecycle requirements:** stateless per resolution; must fail closed
  (return "identity unresolved," never guess) if it cannot confidently
  resolve an identity.
- **Security/no-go constraints:** no secret leakage (credentials used to
  resolve identity, if any, must never appear in the `Identity` value
  returned to callers); no hidden network access.
- **Failure behavior:** an unresolved identity must block downstream
  Approval/Audit from proceeding as though a specific identity was
  confirmed — fail closed, never default to an implicit "local operator."
- **Current status:** `not_implemented`. Today's commands assume a
  single implicit local operator; there is no multi-identity resolution
  anywhere in PCAE.

### 2.10 Context Plugin

- **Allowed responsibilities:** aggregate Session/Task/Phase Runtime
  Services (110A §4) into a single context object per intent.
- **Forbidden responsibilities:** mutating any service it reads from;
  executing anything; making any policy or approval decision.
- **Input schema description:** an intent plus access to the
  Session/Task/Phase Runtime Services.
- **Output schema description:** a `Context` value, consumed by the
  Intent Pipeline and, for display purposes, by Approval/Audit.
- **Lifecycle requirements:** read-only with respect to every service it
  aggregates; must be re-computed per intent, never cached across
  intents in a way that could serve stale session/task/phase state.
- **Security/no-go constraints:** no untracked mutation (this category
  is read-only by definition — any mutation would be a contract
  violation, not just a bad practice); no secret leakage (session/task
  context must not surface credentials even if some underlying service
  happens to hold them).
- **Failure behavior:** if a service is unavailable, the resulting
  `Context` must explicitly mark that service's data as unavailable —
  never substitute a default that looks like real data.
- **Current status:** `not_implemented` as a plugin. `pcae session
  bootstrap --compact --profile implementation` is a real, working,
  non-pluggable precedent for what context assembly looks like.

## 3. Plugin Capability Taxonomy

Ten capability classes are frozen. A plugin's **capability declaration**
(§1, field 8) must be drawn from this list; no plugin may claim a
capability outside it.

| Capability class | Meaning | Which categories may declare it |
|---|---|---|
| `observe` | Consult a decision-relevant source without acting on the result. | Policy, Decision, Context (read-only observation) |
| `advise` | Surface a decision or recommendation without enforcing it. | Decision, Notification |
| `approve` | Record an explicit human approval. | Approval only |
| `deny` | Record an explicit human or policy denial. | Approval, Policy, Decision |
| `enforce` | Cause a decision to have a binding effect on downstream flow. | *(none today — no category may currently declare this; enforcement is not implemented anywhere in PCAE)* |
| `execute` | Cause a real action to run. | *(none today — no category may currently declare this; Execution Adapter Plugin is the only category architecturally destined to declare it, and only once implemented)* |
| `audit` | Produce a durable evidence record. | Audit only |
| `notify` | Deliver a payload to a human or system. | Notification only |
| `store` | Persist or retrieve a structured record. | Storage only |
| `rollback_prepare` | Verify a rollback path exists, without invoking it. | *(none today — Rollback Boundary, `COMP-008`, is not implemented)* |

**Current maximum capability actually exercised by any real PCAE code
path today: `observe`.** This is the exact ceiling the four existing
observation integrations (INT-001..004, 109B–109D) already sit at — the
Permission Broker is consulted (`observe` capability), and nothing
downstream reads the result. No plugin, category, or code path may
declare `enforce` or `execute` today; both remain undeclarable because
no implementation of either exists to back the declaration.

**Execution unavailable.** `enforce` and `execute` are named in this
taxonomy so that a future phase has a frozen vocabulary to declare them
against — naming them is not the same as making them available, exactly
as `docs/PCAE_RUNTIME_ARCHITECTURE.md` §8 named `Executed` as a state
without making it reachable.

## 4. Plugin Lifecycle States

Eight lifecycle states are frozen, describing a plugin instance's
existence independent of any specific intent it might process (contrast
with the Runtime State Model, 110A §8, which describes an *intent's*
lifecycle, not a *plugin's*):

```
defined -> registered -> configured -> healthy -> available
                                          |
                                          v
                                       disabled
                                          |
                                          v
                                       failed
                                          |
                                          v
                                       retired
```

| State | Meaning |
|---|---|
| `defined` | The plugin's contract (this document, §1–§2) exists; no instance exists yet. |
| `registered` | An instance has been recorded in a Plugin Registry (110A §4, not implemented). |
| `configured` | The instance has a valid Configuration Model (§1, field 9) applied. |
| `healthy` | The instance's Health Reporting (§1, field 10) currently reports healthy. |
| `available` | The instance is reachable by the Runtime for its declared capability. |
| `disabled` | The instance exists and is configured but is deliberately not available (operator choice, not a failure). |
| `failed` | The instance's health reporting currently reports unhealthy. |
| `retired` | The instance has been permanently removed from consideration; its Plugin ID (§1, field 1) is never reused. |

**Current implementation status: contracts only.** No runtime plugin
lifecycle implementation exists — no code transitions any plugin through
these eight states today, because no Plugin Registry (110A §4) exists to
hold a plugin instance in the first place. This state model is frozen
so a future phase implementing the Plugin Registry has an unambiguous
vocabulary to implement against, not because any instance currently
occupies any of these states.

## 5. Compatibility and Versioning Rules

- **Semantic versioning expected.** Every plugin instance's Versioning
  field (§1, field 11) must be a `MAJOR.MINOR.PATCH` value. `MAJOR`
  changes signal a breaking change to the plugin's own input/output
  shape (not the category contract, which is frozen by this document
  and does not itself version independently per plugin).
- **Backward compatibility rule.** A plugin instance may increment
  `MINOR`/`PATCH` without requiring Runtime changes, provided it
  continues to satisfy every field in its category's contract (§2)
  unchanged. A `MAJOR` increment requires the Runtime (or the operator
  registering the plugin) to explicitly re-validate compatibility — it
  is never assumed.
- **Contract evolution rule.** The eighteen standard fields (§1) and the
  ten category contracts (§2) frozen by this document may only be
  extended (new optional fields, new categories) in a future phase, not
  silently altered. Removing or redefining an existing field's meaning
  requires a new document version and an explicit deprecation notice
  (below) — it is never a same-document edit.
- **Deprecation policy.** A capability class (§3), lifecycle state (§4),
  or contract field (§1) may be marked deprecated in a future phase's
  documentation, but must remain valid to reference for at least one
  full phase cycle after the deprecation notice, so that any
  in-progress design work referencing it is not broken out from under
  it.
- **Compatibility with the 110A Runtime Architecture.** Every plugin
  contract in this document is defined strictly in terms of 110A's
  already-frozen pipeline stages, runtime services, and interfaces — no
  new pipeline stage, runtime service, or interface is introduced here.
  A plugin contract that could not be satisfied by 110A's existing
  architecture would indicate a defect in this document, not a reason to
  silently extend 110A without a dedicated phase.

## 6. Security Boundaries

Every one of the ten plugin categories (§2) must satisfy all ten
boundaries below — restated once here as shared, cross-cutting
requirements rather than repeated in full under each category (§2's
"Security/no-go constraints" subsection calls out only what is
*distinctive* per category; every category is still bound by all ten):

1. **Fail-closed behavior.** Identical to the Permission Broker's own
   design principle (108B/108C): anything unknown, unavailable,
   malformed, or unsupported resolves to the least-permissive outcome.
2. **Least privilege.** A plugin only receives the inputs its category's
   input schema (§2) specifies — never more, regardless of what might be
   technically available to hand it.
3. **No implicit execution.** No plugin outside the (not-implemented)
   Execution Adapter Plugin category may cause a real action to run,
   under any circumstance, regardless of what its own internal logic
   concludes.
4. **No self-authorization.** No plugin may grant itself, or any other
   plugin instance, an approval, decision, or capability it was not
   explicitly configured with — an Approval Plugin cannot approve its
   own proposal; a Policy Plugin cannot mark its own result as final.
5. **No hidden network access.** Any network access a plugin instance
   performs must be declared in its Capability Declaration (§1, field
   8); undeclared network access is a contract violation regardless of
   the plugin's category.
6. **No secret leakage.** No plugin may include a credential, token, or
   other secret in its Outputs (§1, field 6) unless that secret is the
   explicit, declared purpose of the output (and even then, must not
   appear in any log, evidence record, or notification payload).
7. **No untracked mutation.** Any plugin that mutates state (chiefly
   Storage, potentially Audit) must do so only through its declared
   Outputs — no side-channel writes.
8. **No bypass of human approval.** No plugin outside the Approval
   Plugin category may cause an intent to reach `Approved` (110A §8)
   without an Approval Plugin's explicit outcome.
9. **No bypass of the Permission Broker.** No plugin may cause an intent
   to proceed past the Decision Pipeline stage (110A §2) without that
   stage's Decision Plugin having actually run — mirrors the existing,
   unmodified guarantee that `commit.py`/`push.py`/`task.py`/`phase.py`
   never import the broker directly (108D, re-verified 109D, still
   true).
10. **No bypass of audit requirements.** No plugin may cause an
    Execution Adapter Plugin's outcome to be treated as final without
    an Audit Plugin's evidence record having been produced for it
    (§2.6's "must persist before any Notification Plugin fires"
    requirement, restated here as a universal boundary).

## No-Go Confirmations

No plugin loading. No plugin registry implementation. No dependency
injection framework. No runtime execution. No command authorization. No
command denial. No behavior-changing integration. No shell mediation. No
subprocess mediation. No backend invocation. No adapter invocation. No
execution enablement. No execution capability. No Permission Broker
enforcement. No audit persistence. No rollback execution. No emergency
stop. No Telegram inbound. No REST server. No web server. No daemon. No
background workers. No automatic apply. No command execution.
`implementation_status` remains unconditionally `"execution_unavailable"`
on every Permission Broker decision. No `enforce` or `execute`
capability is declared or declarable by any plugin today. Current
maximum runtime state remains `Observed` (110A §8), unchanged.
`v0.1.0-rc1` remains non-executing by design. v0.2 remains the autonomy
target (Level 3, not Level 4/5). GitHub Release for `v0.1.0-rc1` and
branch protection on `main` are unchanged. No new tag. No new GitHub
Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**110C — Runtime Plugin Registry Design.**
