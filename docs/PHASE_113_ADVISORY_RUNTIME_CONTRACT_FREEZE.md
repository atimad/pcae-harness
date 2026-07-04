# Phase 113B — Advisory Runtime Contract Freeze

## Purpose

Freeze the Advisory Runtime contracts (113A) before implementing
advisory behavior. Contract/freeze only — no advisory implementation,
no runtime behavior changes, no execution capability.

## Scope

- `docs/PCAE_ADVISORY_RUNTIME_CONTRACT.md` — the contract: a new
  principle ("Explainability precedes trust"), a fourteen-field
  `AdvisoryResult` contract (113A's nine, extended by five, one name
  reconciled rather than duplicated), an eight-facet explainability
  contract plus a reproducibility principle, a frozen `EvidenceReference`
  model (no evidence database), category extension rules, severity/
  confidence semantics (including how they differ and how ambiguity is
  handled), a six-stage advisory lifecycle (contract only), a
  presentation contract, ten absolute safety rules (113A's seven plus
  three new), and compatibility rules mirroring 112F's own discipline.
- `docs/PHASE_113_ADVISORY_RUNTIME_CONTRACT_FREEZE.md` — this document.
- `tests/test_advisory_runtime_contract.py` — documentation-
  verification tests; no runtime code exists to unit-test.

No file under `src/pcae/` is in this phase's task contract's allowed
files.

## 1. Advisory Result Contract Summary

Fourteen fields frozen: 113A's nine (`advisory_id`, `category`,
`severity`, `confidence`, `recommended_action`, `rationale`,
`evidence_references`, `affected_runtime_objects`, `timestamp`),
extended by five new ones each traced to a specific explainability or
reproducibility requirement: `source_snapshot_reference`,
`reasoning_summary`, `alternative_considerations`, `remediation`,
`implementation_status` (reused verbatim from `PermissionBrokerDecision`,
108A). **The brief's suggested `recommendation` field was reconciled,
not duplicated** — it is realized as 113A's own `recommended_action`.

## 2. Explainability Summary

Eight required explanations frozen, each mapped to a specific field or
a fixed, universal invariant sentence (restated identically on every
result, not a per-instance field, since "why this is advisory only" and
"why no execution follows" never vary). New reproducibility principle
frozen: **"Every recommendation must be reproducible from the Runtime
Snapshot"** — restates 110A §6's already-frozen "Deterministic"
Runtime Principle for Analysis specifically, anchored to the new
`source_snapshot_reference` field.

## 3. Evidence Model Summary

One frozen `EvidenceReference` shape (`domain`, `object_id`,
`field_path`, `evidence_summary`) covers every evidence concept the
phase brief named (Runtime Snapshot domain, context/registry/plugin/
capability id, governance status, health status, observation
integration id, source field/path) — realized as `domain`+`field_path`
pairs rather than one bespoke shape per concept. No evidence database,
no audit persistence — evidence is referenced, never stored durably,
the same discipline 112F §7 and 112A §7 already apply elsewhere.

## 4. Reproducibility Rule Summary

Frozen and grounded directly in already-existing architecture: given
the Runtime Snapshot named by `source_snapshot_reference` and the same
future Analysis logic version, re-running Analysis must produce an
identical `category`/`severity`/`confidence`/`recommended_action` —
110A §6's "Deterministic" principle, applied to Analysis's own output
rather than the Runtime's sequencing. Does not require storing every
Runtime Snapshot ever produced (forbidden by §3's "no evidence
database").

## 5. Severity/Confidence Summary

Severity's four levels (`info`/`advisory`/`warning`/`critical`) and
confidence's four levels (`unknown`/`observed`/`validated`/`proven`,
reused verbatim from this codebase's own capability-discovery
vocabulary) given precise meanings. Frozen as orthogonal axes, never
conflated — a `critical`/`unknown` combination and an `info`/`proven`
combination are both valid and must be reported independently.
Ambiguity handled fail-closed: lower confidence, populate
`alternative_considerations`, or emit multiple results — never
fabricate certainty.

## 6. Presentation Contract Summary

Restates 113A's five named consumers (CLI, Telegram, REST, Dashboard,
AI agents) as a frozen contract: every consumer renders the same
underlying `AdvisoryResult` model, varying only in how much detail is
shown (mirroring 112F §5's concise/verbose split), never in which facts
are shown.

## 7. Safety Boundary Summary

Ten absolute rules frozen: 113A's seven (never executes, authorizes,
mutates Runtime Context, mutates Runtime Snapshot, invokes Permission
Broker, invokes shell, invokes adapters) plus three new ones — never
denies, never implies approval, never bypasses human review or future
audit.

## 8. Compatibility Rules Summary

Mirrors 112F §3/§4's own Runtime Snapshot compatibility discipline
directly: additive-only within a major version; breaking changes
(removal, rename, category-meaning change) require a major version
bump; consumers must ignore unknown fields; reproducibility
expectations restated. **No versioning field is added by this phase**
— consistent with 112F's own decision not to implement
`snapshot_schema_version` during a freeze phase, this document does
not add an `advisory_contract_version` field either.

## 9. Roadmap Evaluation

`docs/ROADMAP.md` was reviewed against this phase's content. This
phase adds one new principle ("Explainability precedes trust") and
resolves no open architectural tension requiring a roadmap-level
change; the roadmap's standing principles already cover it at a
coarser grain. **No change to `docs/ROADMAP.md` was needed or made**,
matching every prior 110/111/112/113-series phase's own evaluation
outcome.

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
  limited to documentation files, one test file, and standard
  status-tracking files.
- **Why extending 113A's field list carefully matters:** each of the
  five new `AdvisoryResult` fields is traced to a specific explainability
  or reproducibility requirement in §1/§2 of the contract document —
  none was added merely because the brief suggested it might be
  possible, and the brief's own suggested `recommendation` field was
  reconciled into the existing `recommended_action` rather than kept
  as a duplicate, avoiding the exact kind of undocumented schema
  bloat §9's compatibility rules exist to prevent.
- **Why the evidence model's "no database" rule is itself a safety
  property:** an evidence database would be a new, real persistence
  mechanism — exactly what this phase's hard boundary forbids
  ("no audit persistence"). Defining `EvidenceReference` as a
  reference-only shape, with a durable `evidence_summary` gloss rather
  than the underlying value, satisfies explainability without crossing
  into persistence.

## Limitations

- This phase freezes the `AdvisoryResult` contract; it does not
  implement a concrete type, storage format, or serialization — that
  is 113C's (prototype) scope.
- The advisory lifecycle's four future stages
  (`acknowledged`/`superseded`/`resolved`/`dismissed`) are named, not
  designed in detail — a future phase decides their concrete mechanism.
- No `advisory_contract_version` field exists yet — this document's
  compatibility rules govern whichever future phase adds one.

## No-Go Confirmations

No advisory runtime implementation. No advisory execution. No command
authorization. No command denial. No Permission Broker enforcement. No
runtime execution. No plugin loading. No plugin instantiation. No
plugin invocation. No dependency injection. No shell mediation. No
backend invocation. No adapter invocation. No execution enablement. No
execution capability. No automatic apply. No audit persistence. No
rollback execution. No Telegram inbound. No REST server. No web UI. No
daemon. No background workers. `implementation_status` remains
unconditionally `"execution_unavailable"` on every Permission Broker
decision. Current maximum runtime state remains `Observed`. Current
maximum plugin capability remains `observe`. `v0.1.0-rc1` remains
non-executing by design. v0.2 remains the autonomy target (Level 3, not
Level 4/5). GitHub Release for `v0.1.0-rc1` and branch protection on
`main` are unchanged. No new tag. No new GitHub Release. No PyPI/
GitHub Packages publication.

## Recommended Next Phase

**113C — Advisory Runtime Prototype (Observation-Only).**
