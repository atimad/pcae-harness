# Phase 113A — Advisory Runtime Architecture

## Purpose

Design the Advisory Runtime: the Runtime subsystem responsible for
producing read-only recommendations from Runtime Snapshot. Analytical
only — never executes, never authorizes, never modifies Runtime
Context. Architecture/freeze phase only — no implementation of
advisory logic, no Runtime behavior changes.

## Scope

- `docs/PCAE_ADVISORY_RUNTIME.md` — the architecture: subsystem
  definition and boundaries, a new principle ("Recommendation precedes
  authorization"), the five-stage Advisory Pipeline (Snapshot →
  Analysis → Recommendation → Advisory Result → Presentation), a
  nine-field Advisory Result model (architecture only), eight advisory
  categories (frozen as an open, extensible taxonomy — deliberately
  unlike 110B's closed plugin taxonomy), Runtime Snapshot-only
  integration, a named (not resolved) plugin-integration gap, a
  five-consumer presentation model, and seven absolute safety rules.
- `docs/PHASE_113_ADVISORY_RUNTIME_ARCHITECTURE.md` — this document.
- `tests/test_advisory_runtime_architecture.py` — documentation-
  verification tests; no runtime code exists to unit-test.

No file under `src/pcae/` is in this phase's task contract's allowed
files.

## 1. Advisory Runtime Architecture Summary

Advisory Runtime is frozen as the first subsystem in this arc to ask
"given what is true (Runtime Snapshot), what should a human consider
doing" rather than "what is true." It sits between Runtime Snapshot
(112E/112F, unchanged) and Presentation, consuming exactly one
`RuntimeSnapshot` per analysis pass and producing zero-or-more
Advisory Results. Explicitly distinguished from this codebase's
pre-existing, unrelated "IRG Challenge" advisory concept (which
reviews strategic/roadmap decisions, not Runtime Snapshot) — the two
share a word, not an architecture.

## 2. Advisory Pipeline Summary

Five stages frozen, strictly one-directional: Runtime Snapshot →
Analysis → Recommendation → Advisory Result → Presentation. No stage
may execute anything; Analysis/Recommendation never mutate the
snapshot they read; Advisory Result is the one frozen, transport-
agnostic record every Presentation consumer reads unchanged.

## 3. Advisory Result Summary

Nine fields frozen (architecture only, no concrete type): `advisory_id`,
`category`, `severity` (new four-level vocabulary: `info`/`advisory`/
`warning`/`critical`, deliberately distinct from `dry_run.py`'s
enforcement-flavored `simulation_severity`), `confidence` (reuses this
codebase's own existing capability-discovery vocabulary verbatim:
`unknown`/`observed`/`validated`/`proven`), `rationale`,
`evidence_references` (dot-path pointers into Runtime Snapshot's own
frozen schema, never copies), `recommended_action` (free text, never
executable), `affected_runtime_objects` (reuses 112B's own frozen
identity formats), `timestamp`.

## 4. Runtime Integration Summary

Advisory Runtime consumes Runtime Snapshot exclusively — no direct
dependency on CLI, Telegram, REST, or any transport. This is the same
layering discipline 112E's `runtime_snapshot.py` already applies
(compose the layer beneath, expose upward, never reach sideways),
applied a second time one layer higher.

## 5. Plugin Architecture Summary

Named, not resolved: none of 110B's ten frozen plugin categories fits
"read Runtime Snapshot, produce an analytical recommendation" — Policy
Plugin is the closest in spirit but is a pre-execution authorization
concern, not a post-hoc analytical one. This document does not add an
eleventh category (extending 110B's closed taxonomy is out of this
phase's own scope); it names the extension point a future phase could
build (a new plugin category contributing findings into Analysis,
never producing an `AdvisoryResult` directly) without deciding whether
or how.

## 6. Safety Boundary Summary

Seven absolute rules frozen: never executes; never authorizes (the new
"Recommendation precedes authorization" principle names the ordering,
grants no authority); never mutates Runtime Context; never mutates
Runtime Snapshot; never invokes Permission Broker; never invokes shell;
never invokes adapters — the third instance, in this arc, of the same
isolation guarantee `runtime_context.py` (112C) and `runtime_snapshot.py`
(112E) already hold.

## 7. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's content. This
phase adds one new principle ("Recommendation precedes authorization")
and one new subsystem concept, consistent in kind with every prior
phase-scoped principle addition in this arc; the roadmap's standing
principles already cover it at a coarser grain. **No change to
`docs/ROADMAP.md` was needed or made**, matching every prior
110/111/112-series phase's own evaluation outcome. (`docs/ROADMAP.md`'s
own "Current State" section remains stale, per 112B.1's
already-documented, still-unrepaired finding — unchanged by this
phase.)

## Execution Integration Status

Unchanged — this phase adds no new command-path integration, touches
no source code, and introduces no execution capability:

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
- **Why the Advisory Runtime design itself cannot silently become an
  implementation:** every concept in this document (pipeline, Advisory
  Result fields, categories, integration rules, safety rules) is
  prose-only — no code, no schema, no data structure any runtime could
  load or execute.
- **Why naming the plugin-integration gap honestly (§5/§6 of the
  architecture doc) is itself a safety property:** silently inventing
  an eleventh plugin category, or silently shoehorning advisory
  contribution into an existing category (Policy Plugin), would risk
  baking an unexamined assumption into a future implementation phase —
  this document's discipline of naming, not resolving, the gap is
  deliberate, continuing the same discipline 111R/112A/112B already
  established.

## Limitations

- This phase designs the Advisory Runtime *shape*; it does not
  validate that shape against a prototype implementation, since none
  exists (113B, contract freeze, is the recommended next phase,
  mirroring the 110A→110B, 112A→112B, and 112E→112F "design phase
  followed by contract-freeze phase" pattern already established three
  times).
- The plugin-integration question (§5/§6 of the architecture doc) is
  named, not resolved, and is explicitly a future phase's to decide.
- No concrete `AdvisoryResult` type, storage format, or serialization
  is designed — this document freezes the field list, not an
  implementation.

## No-Go Confirmations

No advisory execution. No runtime execution. No command authorization.
No command denial. No Permission Broker enforcement. No plugin
loading. No plugin instantiation. No plugin invocation. No dependency
injection. No shell mediation. No backend invocation. No adapter
invocation. No execution enablement. No execution capability. No
automatic apply. No audit persistence. No rollback execution. No
Telegram inbound. No REST server. No web UI. No daemon. No background
workers. `implementation_status` remains unconditionally
`"execution_unavailable"` on every Permission Broker decision. Current
maximum runtime state remains `Observed`. Current maximum plugin
capability remains `observe`. `v0.1.0-rc1` remains non-executing by
design. v0.2 remains the autonomy target (Level 3, not Level 4/5).
GitHub Release for `v0.1.0-rc1` and branch protection on `main` are
unchanged. No new tag. No new GitHub Release. No PyPI/GitHub Packages
publication.

## Recommended Next Phase

**113B — Advisory Runtime Contract Freeze.**
