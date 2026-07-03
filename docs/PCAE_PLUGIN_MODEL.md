# PCAE Plugin Model

**Frozen by**: Phase 110A | **Status**: architecture/freeze only — no
plugin loading implementation, dependency injection framework, runtime
execution, command authorization, command denial, shell mediation,
subprocess mediation, backend invocation, adapter invocation, execution
enablement, execution capability, Permission Broker enforcement, audit
persistence, rollback execution, emergency stop, Telegram inbound, REST
server, web server, daemon, background workers, automatic apply, or
command execution is performed by this document or this phase.

## Purpose

Freeze the ten canonical plugin categories that make up PCAE's future
extension surface, as introduced in `docs/PCAE_RUNTIME_ARCHITECTURE.md`
§3. Each category below is a **contract definition**, not a class, not
an interface in code, and not a loading mechanism. A future
implementation phase would give each category a concrete Python
protocol/ABC and a registration mechanism (the Plugin Registry service,
`docs/PCAE_RUNTIME_ARCHITECTURE.md` §4) — this document intentionally
stops short of that, exactly as `docs/V0_2_PERMISSION_BROKER_COMMAND_PATH_INTEGRATION.md`
(109A) froze command-path integration architecture without integrating
anything.

For every category, this document defines: **Purpose**,
**Responsibilities**, **Lifecycle**, **Inputs**, **Outputs**, **Current
Status**, and **Future Implementation Phase**.

## Plugin Diagram

```
                              +------------------+
                              |     Runtime      |
                              |  (coordination    |
                              |   layer only)     |
                              +--------+---------+
                                       |
       +-------------------+----------+----------+-------------------+
       |                   |                     |                   |
       v                   v                     v                   v
+-------------+     +-------------+       +-------------+     +-------------+
|   Intent    |     |   Policy    |       |  Decision   |     |  Approval   |
|   Source    |     |   Plugin    |       |   Plugin    |     |   Plugin    |
|   Plugin    |     |             |       |             |     |             |
+-------------+     +-------------+       +-------------+     +-------------+

       +-------------------+----------+----------+-------------------+
       |                   |                     |                   |
       v                   v                     v                   v
+-------------+     +-------------+       +-------------+     +-------------+
|  Execution  |     |    Audit    |       | Notification|     |   Storage   |
|   Adapter   |     |   Plugin    |       |   Plugin    |     |   Plugin    |
|   Plugin    |     |             |       |             |     |             |
+-------------+     +-------------+       +-------------+     +-------------+

                     +-------------+       +-------------+
                     |  Identity   |       |   Context   |
                     |   Plugin    |       |   Plugin    |
                     +-------------+       +-------------+
```

Every plugin category reports to the Runtime and only to the Runtime —
no plugin-to-plugin direct call is part of this model (Principle 3,
"Connected", `docs/PCAE_RUNTIME_ARCHITECTURE.md` §6). Cross-cutting
categories (Storage, Identity, Context) are drawn separately because
they are consulted by more than one pipeline stage rather than owning a
single stage outright.

## 1. Intent Source Plugin

- **Purpose:** Produce a well-formed intent — the first artifact the
  Runtime ever sees for a proposed action.
- **Responsibilities:** Capture who/what proposed the action, what
  action is being proposed, and when; hand a structurally valid intent
  to the Runtime. Never itself evaluates policy, never itself executes.
- **Lifecycle:** `register → produce(intent) → (repeat)`. Stateless
  between productions; a single Intent Source Plugin may produce many
  intents over its lifetime (e.g. one instance per CLI command family).
- **Inputs:** Whatever a human, an AI agent, or a triggering condition
  supplies natively (a CLI invocation's arguments, a scheduled event, an
  API call in some hypothetical future) — not standardized by this
  document.
- **Outputs:** One well-formed intent per production, conforming to the
  Runtime → Intent Pipeline contract (`docs/PCAE_RUNTIME_ARCHITECTURE.md`
  §5).
- **Current Status:** Not implemented as a plugin. Every governed CLI
  command today (`pcae commit`, `pcae push`, `pcae check`, etc.) is an
  *informal* intent source — it produces an implicit "run this command"
  intent — but none of them construct a standardized intent object, and
  there is no Intent Source Plugin registration surface.
- **Future Implementation Phase:** Not scheduled. A natural candidate
  would formalize the existing CLI commands as the first Intent Source
  Plugin implementation, analogous to how `pcae health` became the first
  observation integration (109B) by being the lowest-risk existing
  command.

## 2. Policy Plugin

- **Purpose:** Evaluate a normalized intent against one policy concern
  and return a triggered/not-triggered result.
- **Responsibilities:** Evaluate independently of every other Policy
  Plugin (no short-circuiting, exactly as `PolicyRegistry.evaluate_all()`,
  108B, already guarantees for `PolicyRule`); never mutate state; never
  raise uncaught (a malformed or failing plugin must be sanitized to a
  fail-closed result, exactly as `_sanitize_result()`, 108C, already does
  for `PolicyRule`).
- **Lifecycle:** `register → evaluate(request) -> PolicyResult →
  (repeat, stateless)`.
- **Inputs:** A normalized request (the Intent Pipeline's output).
- **Outputs:** A `PolicyResult`-shaped value: `triggered`, `decision`,
  `decision_reason`, and matched IDs — the existing `PolicyResult`
  dataclass (108B, `src/pcae/core/permission_broker_foundation.py`) is
  the direct precedent for this shape.
- **Current Status:** **Foundation-implemented**, but not yet a general
  plugin category — today's twelve `PolicyRule` instances
  (`DEFAULT_POLICY_RULES`, 108B/108C) are hardcoded into the Permission
  Broker's own `PolicyRegistry`, not independently registrable plugins.
- **Future Implementation Phase:** Not scheduled. Generalizing
  `PolicyRule` into a registrable Policy Plugin category would be a
  natural 110-series follow-on, but is not this phase's objective.

## 3. Decision Plugin

- **Purpose:** Compose the results of every triggered Policy Plugin into
  a single decision.
- **Responsibilities:** Precedence composition (`DENY > HUMAN_REVIEW >
  ALLOW`, fail-closed on an empty result set) — exactly
  `_compose()`'s existing, frozen behavior (108C). A Decision Plugin
  category generalizes this beyond the one hardcoded implementation the
  Permission Broker uses today.
- **Lifecycle:** `register → compose(results) -> Decision → (repeat,
  stateless)`.
- **Inputs:** The tuple of every Policy Plugin's results for one intent.
- **Outputs:** A single decision value (`ALLOW`/`DENY`/`HUMAN_REVIEW`),
  shaped like today's `PermissionBrokerDecision` (108A).
- **Current Status:** **Foundation-implemented** as `PermissionBroker`
  (108A) and its internal `_compose()` (108C), but — like Policy
  Plugin — not yet a general, independently-registrable category; there
  is exactly one Decision Plugin implementation today, and it is not
  pluggable.
- **Future Implementation Phase:** Not scheduled.

## 4. Approval Plugin

- **Purpose:** Require and record an explicit human approval before an
  intent may move from a broker decision to an executable state.
- **Responsibilities:** Present the proposed action and its decision
  clearly; capture an unambiguous approve/deny action from a human;
  refuse to infer approval from silence, timeout, or any automated
  signal — this is INV-003 (107B), already frozen, restated here as the
  contract this plugin category must satisfy.
- **Lifecycle:** `register → request_approval(intent, decision) ->
  ApprovalOutcome`. Unlike Policy/Decision plugins, this lifecycle may be
  long-lived (waiting on a human) rather than immediately returning.
- **Inputs:** The intent and the Decision Pipeline's output.
- **Outputs:** An explicit `ApprovalOutcome` (approved / denied / no
  response yet) — never inferred, never defaulted to approved.
- **Current Status:** Not implemented. `COMP-003` (Human Approval Gate,
  107B) has the same "not implemented" status this plugin category
  inherits.
- **Future Implementation Phase:** **111A**, per `docs/V0_2_AUTONOMY_CONTRACT.md`'s
  own component status note for `COMP-003` ("Enforcement of this gate is
  Phase 111A").

## 5. Execution Adapter Plugin

- **Purpose:** The single mediated boundary through which an authorized
  intent actually runs.
- **Responsibilities:** Refuse any intent not carrying proof of prior
  `AUTHORIZED`/`Executable` status (§8 of the Runtime Architecture
  document); mediate all real action — shell, backend, or adapter —
  never allow a direct, unmediated path.
- **Lifecycle:** `register → execute(authorized_intent) ->
  ExecutionOutcome`.
- **Inputs:** An authorized intent.
- **Outputs:** An `ExecutionOutcome` (success/failure and any resulting
  artifact), consumed next by the Audit Plugin.
- **Current Status:** Not implemented. Corresponds to `COMP-004`
  (Shell Boundary), `COMP-005` (Backend Boundary), `COMP-006` (Adapter
  Boundary) — all "not implemented" per 107B.
- **Future Implementation Phase:** Not scheduled.

## 6. Audit Plugin

- **Purpose:** Produce exactly one evidence record per execution
  attempt, success or failure.
- **Responsibilities:** Never allow a "silent" execution outcome; persist
  before any Notification Plugin fires (the Audit → Notification
  contract, `docs/PCAE_RUNTIME_ARCHITECTURE.md` §5).
- **Lifecycle:** `register → record(execution_outcome) -> EvidenceRecord`.
- **Inputs:** An `ExecutionOutcome` from an Execution Adapter Plugin.
- **Outputs:** A durable `EvidenceRecord`, using the Storage Plugin
  category for actual persistence.
- **Current Status:** Not implemented. Corresponds to `COMP-007` (Audit
  Boundary, 107B), "not implemented."
- **Future Implementation Phase:** Not scheduled.

## 7. Notification Plugin

- **Purpose:** Surface an outcome (or, in observation mode, a phase
  completion) to a human or system.
- **Responsibilities:** Format and deliver via a configured sink; never
  treat delivery as a substitute for the Audit Plugin's evidence record.
- **Lifecycle:** `register → notify(payload) -> DeliveryOutcome`.
- **Inputs:** A payload — today, a phase-completion report; in the
  future, potentially any Evidence Pipeline record.
- **Outputs:** A `DeliveryOutcome` (sent/failed/skipped per sink).
- **Current Status:** **Partially implemented** — this is the one plugin
  category with a working, exercised implementation today: `pcae notify`
  (`COMP-009`) supports `noop`, `stdout`, `filesystem`, `mock`, and
  `telegram` sinks, and outbound Telegram delivery is exercised at the
  end of every governed phase in this project via `pcae phase complete`
  with `PCAE_NOTIFY_ENABLED=1`. It is not yet reorganized under a formal
  plugin-registration contract — today's sinks are a fixed, hardcoded
  set rather than independently pluggable.
- **Future Implementation Phase:** Not scheduled. Generalizing today's
  sink set into registrable Notification Plugins is a natural, low-risk
  follow-on given the working precedent, but is not this phase's
  objective. Telegram **inbound** remains explicitly out of scope
  regardless (No-Go, both this phase and every prior phase since 94-series).

## 8. Storage Plugin

- **Purpose:** Durable persistence backing the Evidence Pipeline and any
  Runtime Service that needs to survive across invocations.
- **Responsibilities:** Provide read/write access to structured records;
  never itself interpret the meaning of what it stores (that is the
  Audit Plugin's or a Runtime Service's responsibility).
- **Lifecycle:** `register → write(key, record) / read(key) ->
  record`. Long-lived; a Storage Plugin instance typically persists for
  the process lifetime of whatever hosts the Runtime.
- **Inputs:** Structured records from Audit, Notification, or a Runtime
  Service.
- **Outputs:** Confirmation of write, or the requested record on read.
- **Current Status:** Not implemented as a plugin. Ad hoc filesystem/JSON
  storage already exists throughout `.pcae/` (task contracts, session
  state, phase-completion metadata, phase reports) — this is a real,
  working precedent for *what* gets stored, but it is not organized
  behind a Storage Plugin contract; each subsystem reads and writes its
  own files directly today.
- **Future Implementation Phase:** Not scheduled.

## 9. Identity Plugin

- **Purpose:** Establish who (human or agent) originated a given intent,
  for use by Approval and Audit.
- **Responsibilities:** Resolve an intent's originating identity;
  never itself grant or deny anything — identity resolution and
  authorization are deliberately separate concerns (least privilege,
  `docs/PCAE_RUNTIME_ARCHITECTURE.md` §6 principle 8).
- **Lifecycle:** `register → resolve(intent) -> Identity`.
- **Inputs:** The raw intent (or its Intent Source context).
- **Outputs:** A resolved `Identity` value, consumed by Approval and
  Audit plugins.
- **Current Status:** Not implemented. Today's commands assume a single
  implicit local operator; there is no multi-identity resolution
  anywhere in PCAE.
- **Future Implementation Phase:** Not scheduled.

## 10. Context Plugin

- **Purpose:** Assemble the ambient context (session, task, phase,
  repository state) a pipeline stage or plugin needs without each one
  re-deriving it independently.
- **Responsibilities:** Aggregate Runtime Services (Session, Task,
  Phase) into a single context object per intent; never mutate the
  services it reads from.
- **Lifecycle:** `register → assemble(intent) -> Context`.
- **Inputs:** An intent plus access to the Session/Task/Phase Runtime
  Services.
- **Outputs:** A `Context` value, consumed by the Intent Pipeline and
  potentially by Approval/Audit for display purposes.
- **Current Status:** Not implemented as a plugin. `pcae session
  bootstrap --compact --profile implementation` is a real, working
  precedent for *what* context assembly looks like (it already
  aggregates active task, governance health, last handoff, phase, and
  strategic decision context into one compact report) — but it is a
  standalone command, not a Context Plugin any other stage can invoke
  programmatically.
- **Future Implementation Phase:** Not scheduled.

## Cross-Cutting Category Summary

Three categories — Storage, Identity, Context — do not own a single
pipeline stage; they are consulted *by* multiple stages and multiple
other plugin categories. This is deliberate: a Storage Plugin backs both
the Evidence Pipeline (via Audit) and any Runtime Service needing
persistence; a Context Plugin backs both the Intent Pipeline and, for
display purposes, Approval/Audit. This mirrors how the existing,
working `pcae session bootstrap` command already aggregates
session/task/phase context for *every* command family, not just one.

## Plugin Category Status Summary

| # | Category | Current Status |
|---|---|---|
| 1 | Intent Source Plugin | not_implemented (informal CLI precedent) |
| 2 | Policy Plugin | foundation_implemented (hardcoded `PolicyRule`, not pluggable) |
| 3 | Decision Plugin | foundation_implemented (hardcoded `PermissionBroker`, not pluggable) |
| 4 | Approval Plugin | not_implemented |
| 5 | Execution Adapter Plugin | not_implemented |
| 6 | Audit Plugin | not_implemented |
| 7 | Notification Plugin | partially_implemented (working sinks, not pluggable) |
| 8 | Storage Plugin | not_implemented (ad hoc filesystem precedent) |
| 9 | Identity Plugin | not_implemented |
| 10 | Context Plugin | not_implemented (`pcae session bootstrap` precedent) |

**No plugin loading mechanism, plugin discovery mechanism, or dependency
injection framework exists for any of these ten categories.** Every
"Current Status" above describes an existing, hardcoded, non-pluggable
precedent at most — never a working plugin system. Execution capability
remains unavailable across all ten plugin categories: `implementation_status`
is unconditionally `"execution_unavailable"` on every Permission Broker
decision (unchanged since 108A), and none of the ten categories provide
any path around that.

## No-Go Confirmations

No plugin loading implementation. No dependency injection framework. No
runtime execution. No command authorization. No command denial. No shell
mediation. No subprocess mediation. No backend invocation. No adapter
invocation. No execution enablement. No execution capability. No
Permission Broker enforcement. No audit persistence. No rollback
execution. No emergency stop. No Telegram inbound. No REST server. No
web server. No daemon. No background workers. No automatic apply. No
command execution. `v0.1.0-rc1` remains non-executing by design. v0.2
remains the autonomy target (Level 3, not Level 4/5). GitHub Release for
`v0.1.0-rc1` and branch protection on `main` are unchanged. No new tag.
No new GitHub Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**110B — Runtime Plugin Contract Freeze.**
