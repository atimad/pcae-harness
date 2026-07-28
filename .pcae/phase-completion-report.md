# Phase 146F — CHGR-001 Schema-Envelope Implementation Planning

**Status:** Complete (implementation-planning-stage document only; no
schema, contract, or production code modified; no CLI implemented; no
runtime, Publication Coordinator, or Interactive Workflow change; no
execution capability added; no implementation authorized or performed).
**Mode:** Implementation Planning.
**Predecessor:** Phase 146E — CHGR-001 Authority-Basis Amendment
Independent Verification (verdict: VERIFIED).
**Question answered:** per explicit human authorization following Phase
146E's VERIFIED verdict — produce a complete implementation plan for
CHGR-REQ-194 through CHGR-REQ-209.
**Runtime:** Observed / observe / unavailable, confirmed unchanged before
and after this phase (`pcae runtime inspect`).
**Pushed:** pushed (this phase's own commits pushed to `origin/main`).

Every implementation responsibility, risk, and integration point below
was independently derived from primary sources — CHGR-001 §26/§28 in
full, the current implementation (`record.py`, `coordinator.py`,
`storage.py`, `PublicationReadinessPackage`), the complete CHGR schema
family and `manifest.json`, and the existing generic `schema_runtime`
validation infrastructure — not restated from any prior phase's own
summary.

---

## 1. Bootstrap

`git status --short`: clean at phase start. `git branch --show-current`:
`main`. `git rev-list --count origin/main..HEAD` / `HEAD..origin/main`:
0/0 at phase start. `pcae session bootstrap --agent-id claude-local`:
lock held, health healthy, check passed. Latest completed phase: 146E
(completed, report: complete). `pcae task new`/`pcae task close` closed
the post-146E idle placeholder and opened this phase's own task. `pcae
check`/`pcae health`/`pcae doctor task-memory`: passed/healthy/clean.
`pcae runtime inspect`: `Observed`/`observe`/`unavailable`. `pcae push
check`: clean, 0 unpushed commits (prior to this phase's own commits).
`PROJECT_STATUS.md` treated as authoritative; no conflict found.

## 2. Independent reconstruction

Directly read: CHGR-001 §26 and §28 in full (all judgment calls, the
Migration Strategy, the Regression and Compatibility reviews);
`src/pcae/governance/publication/record.py`, `coordinator.py`,
`storage.py` in full; `src/pcae/interactive_workflow/publication_handoff/models.py`
and `handoff.py`; all four CHGR record schemas
(`human_governance_record.schema.json` v1.1 and its three siblings) plus
all six `shared/*.schema.json` files and `manifest.json`;
`src/pcae/schema_runtime/registry.py` and `validation.py` in full.

Independently confirmed CHGR-REQ-207 (`authority_basis_claimed` removed
from `required`) already present in the on-disk schema, matching Phase
146D's own claim. Independently confirmed the current
`build_publication_record` output shares no field names, envelope, or
identity discipline with `human_governance_record.schema.json` — the gap
CHGR-REQ-194–209 exists to close is a content-transformation and
validation-gate-insertion task, not a new subsystem.

## 3. Implementation responsibilities

Nine responsibilities independently identified and mapped to all sixteen
requirements (CHGR-REQ-194–209), each with an owner, inputs, outputs,
invariants, and failure conditions: manifest-sourced envelope
construction; canonical identity/digest assignment across four
independently-identified artifacts; an explicit construction order
resolving a forward-reference cycle between
`human_governance_record.integrity_ref` and
`governance_record_integrity.payload_digest`; `lifecycle_state`
assignment (fixed `"published"`); `authority_basis_claimed`
non-fabrication with mandatory `limitations` disclosure; `assurance_level`
derivation from `evidence_kind` (L0/L1 only); the three sibling
artifacts' remaining fields; a new, previously-nonexistent deterministic
human-readable rendering function; and manifest/digest-utility reuse. See
`docs/PHASE_146F_CHGR001_SCHEMA_ENVELOPE_IMPLEMENTATION_PLANNING.md` §3
for full detail.

## 4. Fail-closed validation design

Specified in full: execution point (inside the widened construction
function, strictly before `PublicationRecordStore.write_record`);
validation ordering (four independent schema validations via
`validate_record_shape`, then CHGR-REQ-208's own disclosure predicate);
failure propagation (a new `ChgrSchemaConformanceError`, a
`PublicationExecutionError` subclass, caught by `coordinator.py`'s
existing exception-handling block with no new branch needed); diagnostic
expectations (reusing `ShapeValidationResult.issues`' structured
per-field detail); rollback expectations (none needed — the gate runs
before any write); and publication refusal behavior (identical to every
existing refusal path). CHGR-REQ-208's disclosure check is specified as
an independent Python predicate, since JSON Schema alone cannot express
"if field X is absent, array Y must contain a matching entry." Full
detail in the planning document §4.

## 5. Integration design

`PublicationCoordinator.execute`'s one call site (today's
`build_publication_record` call) is widened, not replaced structurally;
`record.py`'s construction function's return shape changes from one flat
dict to a four-key bundle (a disclosed, non-external-surface-breaking
change — no CLI or external caller depends on today's shape). The
already-existing, already-generic `schema_runtime` package
(`build_offline_registry`, `validate_record_shape`) is reused unchanged,
pointed at `src/pcae/schema_resources/chgr` instead of `cltr_cutover`. No
existing ownership boundary (144G's forbidden-import boundary,
`interactive_workflow`'s own internals) is redesigned. Full detail in the
planning document §5.

## 6. Migration strategy

A six-step sequence: three independently-landable, zero-behavioral-change
steps (new exception class, new rendering function, new
envelope-construction helper) followed by one atomic widening step
(construction + fail-closed gate + `storage.py` + `coordinator.py`'s call
site, landed together — a half-migrated state would break immediately),
then test updates. No live Publication Execution callers exist today, so
no data migration or deprecation window is needed; a revert restores
exactly today's status. Full detail in the planning document §6.

## 7. Testing strategy

Unit tests (schema construction, manifest resolution, identity
generation, digest generation, authority-basis handling, assurance-level
handling, validation failures); integration tests (publication path
end-to-end, fail-closed behavior, schema validation, manifest validation,
deterministic reproduction); regression tests (all 25 existing tests in
`tests/test_phase_144c_publication_coordinator.py`, the forbidden-import
boundary, PEC-REQ-051's fixed validation ordering, CHGR schemas, canonical
reports, runtime invariants). Full detail in the planning document §7.

## 8. Risk assessment

Seven risks independently identified (R-1 through R-7), each with a
stated mitigation or an explicitly disclosed, not-silently-resolved
judgment call. Two are newly discovered by this phase, not previously
disclosed by 146A–146E:

- **R-3 (timestamp format mismatch):** every `_now_iso()` helper in the
  repository (five independent copies) emits a `+00:00`-suffixed
  timestamp; the CHGR envelope schema's `timestamp` shape requires a
  literal `Z` suffix. Every constructed artifact would fail schema
  validation on every timestamp field unconditionally unless repaired. A
  minimum-necessary repair (normalize at the CHGR construction boundary)
  is recommended but left as a disclosed judgment call, not frozen by
  this planning-only phase.
- **R-1 (construction-order hazard):** a genuine forward-reference cycle
  in the four-artifact reference graph, resolved with an explicit
  construction order.

R-2 (breaking return-shape change, low risk, no external surface), R-4
(field-pattern mismatches newly surfaced by the gate — expected, not a
defect), R-5 (storage-layout choice left open), R-6 (no authority risk
identified), R-7 (regression risk bounded by §7's test list) are also
recorded. Full detail in the planning document §8.

## 9. Governance validation

```
pcae check              -> passed
pcae health              -> healthy
pcae doctor task-memory  -> clean
pcae runtime inspect     -> Observed / observe / unavailable (unchanged)
pcae push check          -> clean (nothing_to_push, after this phase's own push)
```

No architecture-policy file (`.pcae/policy.toml`) touched. No
strategic-lineage file (`.pcae/strategic-lineage.json`) touched. No
contract, schema, manifest, or production `src/` file touched by this
phase.

## 10. Regression evidence

`fast_green` marker suite re-run fresh: **4391 passed** — identical to
Phase 146A's/146B's/146C's/146D's/146E's own baseline.

## 11. No-go boundary — confirmations

No schema file was modified (`src/pcae/schema_resources/chgr/**`
untouched). No contract file was modified (`docs/contracts/**`
untouched). No production code was modified (`src/pcae/**` untouched,
including `src/pcae/governance/publication/**` and
`src/pcae/interactive_workflow/**`). No test file under `tests/` was
modified. No CLI command was added or changed. No runtime behavior was
changed. No lifecycle sequencing was altered. No authority ownership was
altered. No execution capability was added. No `.pcae/policy.toml` edit
was made. No `.pcae/strategic-lineage.json` edit was made. No
implementation of CHGR-REQ-194–209 was begun or performed — this
document and its companion deliverable are prose/Markdown planning only.

## 12. Final verdict

**IMPLEMENTATION PLAN COMPLETE WITH OBSERVATIONS.** Every one of
CHGR-REQ-194–209 is mapped to a concrete implementation responsibility;
the fail-closed validation architecture, integration design, migration
sequence, and testing strategy are fully specified. The "WITH
OBSERVATIONS" qualifier reflects three disclosed, not-silently-resolved
open judgment calls (R-1's construction order, R-3's timestamp-repair
strategy, R-5's storage-layout choice) — each has a stated recommendation
but none is frozen as binding by this planning-only document. No Blocking
findings.

## 13. Recommended next phase

**146G — CHGR-001 Schema-Envelope Implementation** (a recommendation, not
an authorization). Does not authorize any implementation of
CHGR-REQ-194–209's construction rules.

## 14. Files changed

- `docs/PHASE_146F_CHGR001_SCHEMA_ENVELOPE_IMPLEMENTATION_PLANNING.md`
  (this phase's full deliverable, new).
- `PROJECT_STATUS.md` — Current Phase section updated, prior content
  demoted to "Phase 146E Complete".
- `CHANGELOG.md`, `tasks/DONE.md`,
  `tasks/done/20260728-2012-idle-awaiting-next-governed-phase-post-146e.md`
  (post-146E idle-placeholder closure),
  `tasks/active/20260728-2102-phase-146f-chgr-001-schema-envelope-implementation-planning.md`
  (this phase's own task contract).
- `.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`
  — this file.

No file under `docs/contracts/**`, `src/pcae/schema_resources/chgr/**`,
`src/pcae/governance/publication/**`, `src/pcae/interactive_workflow/**`,
or `tests/` was modified.
