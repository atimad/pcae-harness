# Phase 110D — Runtime Registry Contract Freeze & Resolution Semantics

## Purpose

Freeze the canonical Runtime Registry contract before any registry
implementation begins: the Registry API surface, capability namespace
conventions, resolution outcome semantics, plugin selection strategies,
compatibility rules, lifecycle interaction model, and failure behavior.
This is contract/freeze only — no registry implementation, plugin
loading, or dependency injection exists after this phase, only its
frozen contract.

## Scope

- `docs/PCAE_RUNTIME_REGISTRY_CONTRACT.md` — the Registry as sole
  service-resolution interface, the nine-operation canonical API
  (design only), eighteen illustrative capability namespaces, nine
  resolution outcomes, seven plugin selection strategies (design only),
  five compatibility dimensions plus a migration-policy placeholder,
  lifecycle interaction (observation only), Registry/Runtime/Plugin
  responsibilities restated as contract, and four failure-behavior
  scenarios.
- `docs/PHASE_110_RUNTIME_REGISTRY_CONTRACT_FREEZE.md` — this document.
- `tests/test_runtime_registry_contract.py` — documentation-verification
  tests; no runtime code exists to unit-test.

No file under `src/pcae/` is in this phase's task contract's allowed
files. No registry implementation, plugin loading, or dependency
injection framework is added. `docs/ROADMAP.md` was evaluated for an
update; see §7 below for the outcome.

## 1. Registry Contract Summary

The Registry is frozen as the Runtime's single authoritative
service-resolution interface — restated from 110C §1, not modified: the
Runtime interacts only with the Registry, plugins never communicate
directly, and the Registry never owns orchestration. This document adds
no new architectural rule at this level; it names the existing
110A/110B/110C constraints as one citable contract clause.

## 2. Canonical Registry API Summary

Nine operations are frozen as the Registry's canonical API surface,
design only: `RegisterPlugin()`, `UnregisterPlugin()`,
`DiscoverCapabilities()`, `ResolveCapability()`, `ListPlugins()`,
`GetPluginMetadata()`, `GetPluginHealth()`, `ValidateCompatibility()`,
`ListCapabilityProviders()`. No signature, interface, abstract base
class, or concrete implementation of any operation exists in
`src/pcae/` after this phase. `ResolveCapability()` (filtered, currently
usable candidates) and `ListCapabilityProviders()` (unfiltered, all
declared candidates) are frozen as distinct operations so a future
diagnostic path can see why a candidate was filtered out.

## 3. Capability Namespace Summary

A dotted `domain.action` naming convention is frozen with eighteen
illustrative namespaces spanning all ten plugin categories (110A
§3/110B §2): `intent.receive`, `intent.plan`, `policy.evaluate`,
`decision.observe`, `decision.advise`, `approval.request`,
`approval.record`, `execution.shell`, `execution.git`,
`execution.backend`, `execution.filesystem`, `audit.write`,
`audit.verify`, `notification.send`, `storage.read`, `storage.write`,
`identity.resolve`, `context.session`, `context.phase`. No namespace
validator, parser, or grammar is implemented; the list is illustrative
of the convention, not exhaustive or enforced.

## 4. Resolution Semantics Summary

Nine resolution outcomes are frozen for `ResolveCapability()`:
`Resolved`, `MultipleCandidates`, `NoProvider`, `Incompatible`,
`Disabled`, `Unavailable`, `HealthRejected`, `VersionRejected`,
`PolicyRejected`. Each is documented with its meaning and Runtime
consequence; none is implemented as an enum, exception, or
outcome-computation algorithm. `PolicyRejected` reflects a policy
evaluation the Registry surfaces, not one it performs — 110C §5's
"Registry does not own policy decisions" is unchanged.

## 5. Plugin Selection Semantics Summary

Seven future selection strategies are frozen as vocabulary, none
implemented and none designated a default: `HighestPriority`,
`HighestVersion`, `Healthiest`, `PolicyPreferred`, `UserPreferred`,
`ManualSelection`, `FirstCompatible`. Selection remains the Runtime's
responsibility (110C §4 step 4, unchanged) — the Registry never selects
among `MultipleCandidates`.

## 6. Compatibility Rules Summary

Five compatibility dimensions are frozen for `ValidateCompatibility()`:
runtime version, plugin version, manifest version, contract version,
capability version. A future migration policy (deprecation windows,
forced-upgrade policies, compatibility shims) is explicitly named as an
open question, not defined here — mirroring 110C §8's static/dynamic
boundary discipline. No version-comparison algorithm or compatibility
matrix is implemented.

## 7. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's contract-freeze
content. The roadmap's Long-Term Runtime Vision (110B) already states
"Pluggable first. Connected second. Automated third. Executable last,"
and 110C already added "Discoverable always" to that document where
applicable. This phase's content (API surface, namespaces, resolution/
selection/compatibility semantics, failure behavior) is Registry-
contract detail, not a change to long-term vision or roadmap ordering —
**no change to `docs/ROADMAP.md` was needed or made**, matching 110C's
own evaluation outcome for the same reason.

## 8. Lifecycle Interaction and Responsibility Summary

The Registry observes six of 110B §4's eight plugin lifecycle states
(`Registered`, `Available`, `Unavailable`, `Disabled`, `Deprecated`,
`Removed`) and never executes a transition. Registry, Runtime, and
Plugin responsibilities (110C §5/§6, 110A §1) are restated verbatim as
contract clauses — no responsibility is added, removed, or reworded.
"Registry modification" is clarified as never permitted by another
plugin instance, restating 110C §6's "discovering or calling each other
directly" for the Registry API surface specifically.

## 9. Failure Behavior Summary

Four failure scenarios are frozen, each resolving toward *less*
execution capability, never more: no provider → no execution; multiple
providers → no automatic execution; Registry unavailable → execution
unavailable; manifest invalid or compatibility failure → plugin
unavailable. No exception hierarchy or error-handling code path is
implemented; this section freezes the required *direction* of failure
as a contract constraint.

## Execution Integration Status

Unchanged from 110C — this phase adds no new command-path integration,
touches no source code, and introduces no execution capability:

| Field | Value |
|---|---|
| Observed command paths | **4** (unchanged) |
| Behavior-changing paths | **0** |
| Authorized paths | **0** |
| Execution-capable paths | **0** |
| Current execution capability | **Execution unavailable** |
| Current maximum runtime state | **Observed** (unchanged) |
| Current maximum plugin capability | **`observe`** (unchanged) |

## Safety Case

- **Why this phase cannot introduce execution capability:** it touches
  no file under `src/pcae/` — its task contract's allowed files are
  limited to documentation, one test file, and standard status-tracking
  files.
- **Why the API/namespace/resolution/selection/compatibility freeze
  cannot silently become an implementation:** every concept in this
  document (nine operations, eighteen namespaces, nine outcomes, seven
  strategies, five compatibility dimensions) is prose-only — no code, no
  enum, no schema, no data structure any runtime could load or execute.
- **Why failure behavior is frozen toward less capability, not more:**
  every one of the four failure scenarios (§11 of the contract document)
  resolves to "no execution," "no automatic execution," "execution
  unavailable," or "plugin unavailable" — none resolves to an implicit
  default execution path, preserving the same fail-safe direction 108A's
  Permission Broker already established for its own decisions.
- **Why restating 110C's responsibility split as "contract" changes
  nothing substantive:** §8/§9/§10 of the contract document are verbatim
  restatements of already-frozen 110A/110B/110C material — no
  responsibility moves between the Registry, the Runtime, or a plugin.

## Limitations

- This phase freezes the Registry's contract *vocabulary*; it does not
  validate that vocabulary against a prototype implementation, since
  none exists (110E is the recommended next phase for a first,
  observation-only prototype).
- The capability-identifier grammar (§3 of the contract document) and
  the priority field referenced by `HighestPriority` (§5) are both named
  as open, undefined concepts a future phase must resolve deliberately,
  not pre-decided here.
- The future migration policy for compatibility failures (§6 of the
  contract document) is explicitly out of scope, matching 110C §8's own
  practice of naming open questions rather than guessing at answers.

## No-Go Confirmations

No registry implementation. No plugin loading. No plugin discovery
execution. No dependency injection framework. No runtime execution. No
command authorization. No command denial. No behavior-changing
integration. No shell mediation. No subprocess mediation. No backend
invocation. No adapter invocation. No execution enablement. No
execution capability. No Permission Broker enforcement. No audit
persistence. No rollback execution. No emergency stop. No Telegram
inbound. No REST server. No web server. No daemon. No background
workers. No automatic apply. No command execution.
`implementation_status` remains unconditionally `"execution_unavailable"`
on every Permission Broker decision. Current maximum runtime state
remains `Observed`. Current maximum plugin capability remains `observe`.
No dynamic runtime context implemented. `v0.1.0-rc1` remains
non-executing by design. v0.2 remains the autonomy target (Level 3, not
Level 4/5). GitHub Release for `v0.1.0-rc1` and branch protection on
`main` are unchanged. No new tag. No new GitHub Release. No PyPI/GitHub
Packages publication.

## Recommended Next Phase

**110E — Runtime Registry Prototype (Observation-Only).** The prototype
should implement only passive registration and discovery of plugin
metadata. It must not instantiate plugins, invoke plugins, authorize
commands, or introduce any execution capability.
