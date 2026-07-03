# Phase 110B — Runtime Plugin Contract Freeze

## Purpose

Freeze the canonical runtime plugin contracts that all future PCAE
plugins must implement, turning the ten plugin categories 110A named
into stable, versionable contracts — without implementing plugin
loading, plugin execution, dependency injection, runtime execution, or
any adapter invocation. This is a contract/freeze phase only; no runtime
plugin lifecycle exists after this phase, only its frozen vocabulary.

## Scope

- `docs/PCAE_RUNTIME_PLUGIN_CONTRACTS.md` — the eighteen-field canonical
  contract model, contracts for all ten plugin categories, the
  ten-class capability taxonomy, the eight-state plugin lifecycle model,
  compatibility/versioning rules, and ten security boundaries.
- `docs/PHASE_110_RUNTIME_PLUGIN_CONTRACT_FREEZE.md` — this document.
- `docs/ROADMAP.md` — long-term runtime vision language added (§4
  below).
- `tests/test_runtime_plugin_contracts.py` — documentation-verification
  tests; no runtime code exists to unit-test.

No file under `src/pcae/` is in this phase's task contract's allowed
files. No plugin loading mechanism, plugin registry implementation, or
dependency injection framework is added.

## 1. Plugin Contract Summary

Every plugin contract, regardless of category, is now defined by
exactly eighteen standard fields: Plugin ID, Plugin type, Purpose,
Responsibilities, Inputs, Outputs, Lifecycle hooks, Capability
declaration, Configuration model, Health reporting, Versioning,
Compatibility rules, Security boundaries, Evidence requirements, Failure
behavior, Approval requirements, Audit expectations, and Current
implementation status. No plugin contract may claim `implemented` for
field 18 — only `not_implemented`, `foundation_implemented`, or
`partially_implemented` — because no plugin loading mechanism exists to
make any contract runnable.

## 2. Plugin Category Summary

All ten categories from 110A now have a full contract: allowed
responsibilities, forbidden responsibilities, input/output schema
descriptions, lifecycle requirements, security/no-go constraints,
failure behavior, and current status.

| Category | Current status |
|---|---|
| Intent Source Plugin | not_implemented (informal CLI precedent) |
| Policy Plugin | foundation_implemented (`PolicyRule`, 108B — not pluggable) |
| Decision Plugin | foundation_implemented (`PermissionBroker`, 108A — not pluggable) |
| Approval Plugin | not_implemented (`COMP-003`; enforcement is Phase 111A) |
| Execution Adapter Plugin | not_implemented (`COMP-004`/`005`/`006`) |
| Audit Plugin | not_implemented (`COMP-007`) |
| Notification Plugin | **partially_implemented** (`pcae notify`, working sinks — not pluggable) |
| Storage Plugin | not_implemented (`.pcae/` filesystem precedent) |
| Identity Plugin | not_implemented |
| Context Plugin | not_implemented (`pcae session bootstrap` precedent) |

Every category's contract is defined strictly in terms of 110A's
already-frozen pipeline stages and runtime services — no new pipeline
stage, service, or interface is introduced by this phase.

## 3. Capability Taxonomy Summary

Ten capability classes are frozen: `observe`, `advise`, `approve`,
`deny`, `enforce`, `execute`, `audit`, `notify`, `store`,
`rollback_prepare`. **Current maximum capability actually exercised by
any real PCAE code path today: `observe`** — exactly the ceiling the
four existing observation integrations (INT-001..004) already sit at.
No plugin, category, or code path may declare `enforce` or `execute`
today; both are named in the taxonomy so a future phase has a frozen
vocabulary to declare against, not because either is available.

## 4. Lifecycle State Summary

Eight plugin lifecycle states are frozen: `defined → registered →
configured → healthy → available`, with `available` able to transition
to `disabled → failed → retired`. This describes a *plugin instance's*
existence, distinct from the Runtime State Model (110A §8), which
describes an *intent's* lifecycle. **Current implementation status:
contracts only.** No runtime plugin lifecycle implementation exists —
no Plugin Registry (110A §4) exists to hold any instance in the first
place.

## 5. Security Boundary Summary

Ten cross-cutting security boundaries apply to every plugin category
without exception: fail-closed behavior, least privilege, no implicit
execution, no self-authorization, no hidden network access, no secret
leakage, no untracked mutation, no bypass of human approval, no bypass
of the Permission Broker, no bypass of audit requirements. Boundaries 9
and 10 directly restate already-verified guarantees (108D/109D's
lifecycle-modules-never-import-the-broker-directly check; the
Audit-must-persist-before-Notification-fires interface contract from
110A §5).

## 6. Roadmap Update Summary

`docs/ROADMAP.md` gains a new "Long-Term Runtime Vision" section
stating: PCAE is a governed automation runtime where every capability is
modular, pluggable, connected, observable, automatable, and governed.
Intent sources (Claude, Codex, DeepSeek, Telegram, future REST APIs, VS
Code extensions, web UIs) are plugins. Execution targets (shell, git,
filesystem, backend agents, network calls, cloud runners) are Execution
Adapter Plugins. The Runtime does not privilege any one agent or
execution mechanism — it normalizes intent, evaluates policy, routes
decisions, requires approval where needed, preserves audit evidence,
prepares rollback, and only then allows bounded execution through
controlled adapters. Execution is not the center of PCAE; it is one
governed plugin capability inside the runtime. The section states the
ordering principle: **Pluggable first. Connected second. Automated
third. Executable last.**

## Compatibility and Versioning Summary

Semantic versioning (`MAJOR.MINOR.PATCH`) is expected of every plugin
instance. `MINOR`/`PATCH` changes require no Runtime re-validation as
long as the category contract is still satisfied; `MAJOR` changes always
require explicit re-validation. The eighteen standard fields and ten
category contracts frozen by this document may only be *extended* in a
future phase, never silently altered — a genuine change requires a new
document version and an explicit deprecation notice, with at least one
full phase cycle of continued validity after that notice.

## Execution Integration Status

Unchanged from 110A — this phase adds no new command-path integration,
touches no source code, and introduces no execution capability:

| Field | Value |
|---|---|
| Observed command paths | **4** (`pcae health`, `pcae check`, `pcae doctor task-memory`, `pcae push check` — unchanged) |
| Behavior-changing paths | **0** |
| Authorized paths | **0** |
| Execution-capable paths | **0** |
| Current execution capability | **Execution unavailable** |
| Current maximum runtime state | **Observed** (110A §8, unchanged) |
| Current maximum plugin capability | **`observe`** (§3 above) |

## Safety Case

- **Why this phase cannot introduce execution capability:** it touches
  no file under `src/pcae/` — its task contract's allowed files are
  limited to documentation, one test file, and standard status-tracking
  files. There is no code path by which a contract-freeze phase could
  grant execution capability.
- **Why the contracts themselves cannot silently become enforcement:**
  every contract is defined purely in prose (fields, allowed/forbidden
  responsibilities, schema descriptions) — there is no executable
  artifact anywhere in this document that any runtime could load or
  invoke. The `enforce`/`execute` capability classes are named but
  explicitly marked undeclarable by any category today.
- **Why the security boundaries are not merely aspirational:** eight of
  the ten (fail-closed, least privilege, no self-authorization, no
  bypass of the Permission Broker, no bypass of audit) are restatements
  of guarantees already verified in code (108B/108C/108D/109D), not new
  promises invented for this document.

## Limitations

- This phase freezes contracts; it does not validate that they are
  implementable without further design work. The Plugin Registry
  service (110A §4) that would give these contracts a place to be
  `registered` is itself not designed in detail — that is explicitly
  deferred to 110C.
- Two categories (Storage, Context) are still described partly in terms
  of multiple informal precedents rather than one canonical
  implementation, unchanged from 110A's own limitation note; this phase
  gives them full contracts but does not reconcile the underlying ad hoc
  call sites.
- The eighteen-field contract model has not been validated against a
  real plugin implementation, since none exists — validation is
  necessarily structural (does the document define each field for each
  category) rather than behavioral.

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
on every Permission Broker decision. Current maximum runtime state
remains `Observed`. `v0.1.0-rc1` remains non-executing by design. v0.2
remains the autonomy target (Level 3, not Level 4/5). GitHub Release for
`v0.1.0-rc1` and branch protection on `main` are unchanged. No new tag.
No new GitHub Release. No PyPI/GitHub Packages publication.

## Recommended Next Phase

**110C — Runtime Plugin Registry Design.**
