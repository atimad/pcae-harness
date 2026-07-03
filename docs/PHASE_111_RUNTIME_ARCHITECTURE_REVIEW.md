# Phase 111R — Runtime Architecture Review

## Purpose

A deliberate architectural checkpoint across the nine phases (110A–111D)
that built the PCAE Runtime subsystem, before starting the Runtime
Context track (112A). Review/documentation only — no new functionality,
no source behavior changes.

## Scope

- `docs/PCAE_RUNTIME_ARCHITECTURE_REVIEW.md` — the review: responsibility
  separation, dependency direction, plugin isolation, registry/
  introspection purity, Runtime Inspect CLI assessment, safety
  invariants, Runtime Context readiness, a seven-item risk register, a
  principle-by-principle assessment, and a recommendation.
- `docs/PHASE_111_RUNTIME_ARCHITECTURE_REVIEW.md` — this document.
- `tests/test_runtime_architecture_review.py` — documentation-
  verification tests; no runtime code exists to unit-test, and this
  phase adds none.

No file under `src/pcae/` is in this phase's task contract's allowed
files. `docs/ROADMAP.md` was evaluated for an update; see §6 below.

## 1. Method

Every finding in the review document was produced by a runnable check
against live source, live CLI output, or live doc text — direct
`dir()` inspection of `RuntimeRegistry` and `runtime_introspection`'s
public surface, direct reading of every reviewed module's actual
`import` statements, a live `pcae runtime --help`/`pcae --help`
invocation, and a live `PermissionBroker().evaluate()` call — rather
than re-summarizing what each of the nine prior phases already claimed
about itself. This is deliberate: a review that only restates prior
phases' own self-assessment would not be an independent check.

## 2. Key Findings Summary

**Two strengths identified:** the ten-category, multi-instance plugin
taxonomy comfortably covers all twelve example future plugin types
named in the brief without needing an eleventh category (R-2); the
Registry's implementation pattern (frozen records, passive store,
shared validation between admission and re-audit) is a proven,
directly reusable template for Runtime Context's new object types
(R-6).

**Five risks identified, all Low or Medium, none Blocker:**

- **R-1 (Low):** the CLI imports `RuntimeRegistry`/`INTEGRATION_REGISTRY`
  directly rather than exclusively through Introspection — a minor
  layering impurity, not a reverse dependency or cycle.
- **R-3 (Low):** manifest exclusion from CLI output is a convention
  living in the CLI layer, not enforced at the Introspection layer
  itself — today's one consumer does it correctly, but nothing would
  force a hypothetical second consumer to.
- **R-4 (Medium):** `pcae runtime inspect`'s plugin/capability sections
  are structurally always empty (no cross-invocation persistence),
  limiting the command's practical usefulness for an AI agent asking
  "what is registered right now" — a direct, correct consequence of
  110E's deliberate no-persistence scope, not a defect.
- **R-5 (Medium):** Intent, Approval, Broker decision, and Evidence
  have no persistence model at all today — Runtime Context (112A) must
  design this explicitly for each, not silently inherit the Registry's
  in-memory-only choice.
- **R-7 (Low–medium):** roughly thirty unrelated, pre-existing
  `pcae runtime-*` top-level advisory commands (from an earlier,
  unrelated design-only series) share a naming prefix with, but have no
  relationship to, this arc's `pcae runtime` command group — a
  navigability/coherence concern, not a safety one.

## 3. Dependency Direction Verified Acyclic

The actual import graph across `runtime_registry.py`,
`runtime_introspection.py`, `runtime_inspect.py`,
`permission_broker_foundation.py`, and `command_path_observation.py`
was read directly from source and confirmed acyclic, with both
`runtime_registry.py` and `permission_broker_foundation.py` as
zero-dependency leaves — the two most foundational modules are also the
most isolated, the correct shape for a metadata store and a policy
evaluator respectively.

## 4. Safety Invariants Reconfirmed

Every invariant named in the brief (execution unavailable, runtime
state `Observed`, maximum plugin capability `observe`, no plugin
loading, no broker enforcement, no command authorization/denial,
fail-closed posture) was re-verified live, not re-trusted from prior
phases' documentation — including one live `PermissionBroker().evaluate()`
call reconfirming `implementation_status` is still unconditionally
`"execution_unavailable"`. No invariant has weakened at any point across
110A–111D; each successive phase reconfirmed prior invariants with
equal or stronger verification tooling.

## 5. Recommendation

**Proceed to 112A**, with one condition: 112A's own phase brief should
explicitly require a documented Persistence Model decision for each of
Intent, Approval, Broker decision, and Evidence — mirroring 110E's own
explicit, documented in-memory-only choice for the Registry, not
silently inherited or assumed uniform across all four. No finding rose
to Blocker; inserting a separate remediation phase before 112A would
not resolve the two Medium-risk findings (R-4, R-5) any better than
112A resolving them as first-class design questions within its own
scope, and 110E/110F's Registry precedent (R-6) gives 112A a proven
template to design against.

## Execution Integration Status

Unchanged from 111D — this phase adds no code, no command-path
integration, no execution capability:

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
  limited to two documentation files, one test file, and standard
  status-tracking files.
- **Why the review's findings cannot be mistaken for implementation
  claims:** every risk/strength finding is phrased as an observation
  about existing, already-shipped code or an open design question for a
  *future* phase — none describes anything this phase itself built or
  changed, confirmed directly by dedicated tests asserting no
  implementation-claim language appears in either document.
- **Why "Proceed to 112A" is not itself an authorization of anything:**
  the recommendation names a phase number and a design condition; it
  grants no execution capability, bypasses no governance gate, and
  changes no No-Go confirmation anywhere in this codebase.

## 6. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's content. This
phase is a review of already-shipped material; it introduces no new
principle, no new plugin category, and no change to the roadmap's
long-term vision or phase ordering. **No change to `docs/ROADMAP.md`
was needed or made**, matching every prior 110/111-series phase's own
evaluation outcome.

## Limitations

- This review is a point-in-time checkpoint against the codebase as it
  exists after 111D; it does not, and cannot, anticipate defects a
  future phase might introduce.
- The risk register (§9 of the review document) reflects this
  reviewer's judgment applied to directly-verified evidence — it is not
  a formal, tooling-enforced audit the way, e.g., the AST-based
  isolation tests in prior phases are. A future phase disagreeing with
  a classification here is expected and welcome; the evidence each
  finding cites is reproducible independently of the classification
  attached to it.
- Finding R-7 (naming overlap with the pre-existing `runtime-*` command
  family) was not exhaustively audited — every command name was listed
  and verified to be a distinct top-level command from `pcae runtime`,
  but not every one of the roughly thirty commands' full implementation
  was individually re-read; a spot-check of two (`runtime-registry`,
  `runtime-execution-prototype`) confirmed the pattern.

## No-Go Confirmations

No source behavior changes. No Runtime Context. No runtime execution.
No plugin loading. No plugin instantiation. No plugin invocation. No
dependency injection. No command authorization. No command denial. No
shell mediation. No backend invocation. No adapter invocation. No
execution enablement. No execution capability. No Permission Broker
enforcement. No audit persistence. No rollback execution. No emergency
stop. No Telegram inbound. No REST endpoint. No web UI. No daemon. No
background worker. No automatic apply. `implementation_status` remains
unconditionally `"execution_unavailable"` on every Permission Broker
decision. Current maximum runtime state remains `Observed`. Current
maximum plugin capability remains `observe`. `v0.1.0-rc1` remains
non-executing by design. v0.2 remains the autonomy target (Level 3, not
Level 4/5). GitHub Release for `v0.1.0-rc1` and branch protection on
`main` are unchanged. No new tag. No new GitHub Release. No PyPI/GitHub
Packages publication.

## Recommended Next Phase

**112A — Runtime Context Architecture**, with the persistence-model
condition stated in §5.
