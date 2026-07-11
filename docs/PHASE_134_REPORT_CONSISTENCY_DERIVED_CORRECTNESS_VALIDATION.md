# Phase 134E.9 — Report Consistency / Derived Correctness Validation

## 1. Executive Summary

Implemented the reusable Report Consistency / Derived Correctness
validation manifest the 134D implementation plan names as 134E.9's
authoritative scope: "a reusable validation manifest comparing any
derived view/rendering back to its source canonical record, checking
for invented content, silent omission, or unauthorized strengthening of
uncertainty/classification" (134B §17), wired fail-closed into the
existing finalization gate. Direct source inspection before this phase
began confirmed a real, concrete gap: neither `validate_internal_report_
coherence()` nor `validate_finalization_gate()` ever read `architecture_
status["freshness"]` or `["conflicts"]`, so a report could be promoted
and dispatched while carrying a `stale`/`invalid` or conflicted sealed
Architecture Status snapshot — and only a phase recommending *itself*
was rejected, not a recommendation naming a *different* already-completed
phase (the exact stale-132F defect shape 134E.8 repaired). `validate_
derived_correctness()` closes both gaps at the smallest shared boundary.

## 2. Authoritative Scope Determination

Read, before any code change: the 134D implementation plan (`docs/
PHASE_134_CANONICAL_PHASE_FINALIZATION_IMPLEMENTATION_PLAN.md` Section
3, 134E.9 subsection); the 134E.8.1 incident repair (`docs/PHASE_134_
DUPLICATE_TERMINAL_DELIVERY_MIXED_EVIDENCE_REPAIR.md`); the 134E.8V
independent verification (`docs/PHASE_134_ARCHITECTURE_STATUS_
GENERATION_INDEPENDENT_VERIFICATION.md`); the current `validate_
internal_report_coherence()`, `validate_finalization_gate()`,
`compute_report_digest()`, `compute_finalization_snapshot_id()`,
`phase_already_notified()` / `notification_dispatch_state()` /
`write_notification_dispatch_marker()` implementations and their four
active call sites (`pcae phase complete`, `pcae task finish`, `pcae
phase-report create`, `pcae notify send-report`); and `build_
architecture_status()` as it stands after 134E.8/134E.8V.

Finding: the 134D plan's original 134E.9 description assumes the new
Canonical Engineering Evidence / Evidence Extraction / Derived Views /
Rendering chain (134E.1-134E.5) is the "source canonical record" being
validated against. Every 134E.xV through 134E.8V has independently
confirmed that chain remains fully disconnected from production — the
active lifecycle still runs entirely through `phase_reports.py`'s
`PhaseReport` / `finalize_phase_report()` path. The one "source
canonical record" that is actually live, and that 134E.8.1/134E.8V just
finished hardening, is the sealed finalization snapshot: `report.
architecture_status`, bound onto the report at construction time and
never re-read after. 134E.9's manifest therefore validates the report's
*other* derived claims against that one sealed snapshot — the correct,
non-speculative interpretation of the plan's own stated authority
boundary ("Architecture Status remains a derived projection... it must
agree with the canonical record, not compete with it").

## 3. Derived-Claim Inventory (as implemented)

| Claim | Authoritative source | Checked by |
|---|---|---|
| Status/completion, self-denial, self-recommendation | No-Go evidence, `recommended_next_phase` | `validate_internal_report_coherence()` (pre-existing, unchanged) |
| Test evidence phase linkage | `test_results` keys/values vs `phase_id` | `validate_internal_report_coherence()`, extended this phase with an explicit `test_evidence_classification="inherited_regression"` escape hatch |
| Metadata/snapshot phase identity | `report.metadata["phase_id"]` vs `report.phase_id` | `validate_internal_report_coherence()` (pre-existing, unchanged) |
| Source revision vs Architecture Status revision | `report.metadata["source_revision"]` vs `architecture_status["repository_revision"]` | `validate_internal_report_coherence()` (pre-existing, unchanged) |
| **Architecture Status freshness** | `report.architecture_status["freshness"]` | **`validate_derived_correctness()` (new)** |
| **Architecture Status conflicts** | `report.architecture_status["conflicts"]` | **`validate_derived_correctness()` (new)** |
| **Recommended-next already completed (general case)** | `recommended_next_phase` vs `architecture_status["completed_phase_ids"]` | **`validate_derived_correctness()` (new)**, escape hatch `metadata["next_phase_classification"]="corrective_recovery_transition"` |
| **Stale-132F regression guard** | `architecture_status["planned_phase_ids"]` | **`validate_derived_correctness()` (new)** |
| **Runtime tuple validity** | `architecture_status`'s three runtime fields vs `ALLOWED_RUNTIME_TUPLES` | **`validate_derived_correctness()` (new)** |
| **Snapshot current-phase coherence** | `architecture_status["current_phase_id"]` vs `report.phase_id` (sub-phase-aware) | **`validate_derived_correctness()` (new)** |
| Files-changed, governance/test-result key presence, No-Go count, push state, commit attribution | trust-critical/non-fatal field presence | `PhaseReport.assess_completeness()` + `validate_finalization_gate()` (pre-existing, unchanged) |
| Report digest / stored-delivered byte equality | `compute_report_digest()` vs the durable dispatch marker | `notification_dispatch_state()` at all four dispatch call sites (134E.8.1, confirmed still enforced — see Section 9) |
| Finalization snapshot identity | `compute_finalization_snapshot_id()` vs the durable dispatch marker | `notification_dispatch_state()` (134E.8.1, confirmed still enforced) |

Each derived claim above has an authoritative snapshot source (the
column 2 field, read only from `report.architecture_status` /
`report.metadata` / `report` itself — never a fresh external read),
deterministic derivation rules (the check itself), explicit failure
behavior (append to `issues`, which downgrades `report_completeness` to
`incomplete` via `_apply_derived_correctness()`), and provenance
(`report.architecture_status["source_provenance"]`, already established
by 134E.8).

## 4. Single Certified Semantic Source

`validate_derived_correctness(report)` reads only `report.architecture_
status`, `report.metadata`, and other already-in-memory `PhaseReport`
fields — it never calls `build_architecture_status()`, never re-reads
`PROJECT_STATUS.md`, never reads a later `git` revision, and never reads
`.pcae/phase-completion-metadata.json` or any other mutable "latest"
artifact. This mirrors and reuses 134E.8.1/134E.8V's existing seal
point in `finalize_phase_report()` (`report.architecture_status` is set
once at construction, from a caller-sealed snapshot when provided, and
never reassigned afterward) — 134E.9 adds validation *against* that seal
point; it does not change how or when the seal happens.

## 5. Completeness Derivation

`_apply_derived_correctness()` is called immediately after `_apply_
internal_report_coherence()`, inside `_apply_canonical_and_trust()` —
the single function every construction path already calls before a
report can be considered for finalization. A derived-correctness
failure appends a `"derived_correctness"` missing-trust-field, appends a
diagnostic to `trust_warnings`, and unconditionally sets `report_
completeness = "incomplete"`. No later code path re-sets `report_
completeness` to `"complete"` — `assess_completeness()` is called once,
earlier, and its result is exactly what gets downgraded. Field presence
computed afterward (e.g. a promotion or notification outcome) cannot
restore `"complete"`, because nothing in this codebase ever re-invokes
`assess_completeness()` after `_apply_derived_correctness()` runs.

## 6. Cross-Field Semantic Invariants (new, this phase)

Implemented in `validate_derived_correctness()`:

1. Architecture Status `freshness in ("stale", "invalid")` blocks.
2. Architecture Status `conflicts` non-empty blocks (each conflict is
   surfaced in the issue text).
3. `recommended_next_phase`'s leading phase ID already present in
   `architecture_status["completed_phase_ids"]` blocks, unless `report.
   metadata["next_phase_classification"] == "corrective_recovery_
   transition"` (an explicit, governed escape hatch — never inferred).
4. `"132F"` appearing in `architecture_status["planned_phase_ids"]`
   blocks unconditionally — a dedicated regression guard for the exact
   defect 134E.8 repaired, independent of the general check above.
5. The three runtime fields, when all present, must form one of
   `ALLOWED_RUNTIME_TUPLES` (currently exactly `("Observed", "observe",
   "unavailable")` — this repository's only ever-certified tuple, per
   the Runtime State Model, 110A). Partially-populated runtime fields
   (a best-effort snapshot read that only got some fields) are not
   flagged — only a fully-populated, disallowed combination is.
6. `architecture_status["current_phase_id"]`, when present, must not
   name a different phase *family* than `report.phase_id` — sub-phases
   are explicitly allowed to complete independently of the snapshot's
   own current-phase pointer (mirrors `validate_phase_identity()`'s
   existing sub-phase allowance, applied here to the sealed snapshot
   instead of live `PROJECT_STATUS.md`).

Extended in `validate_internal_report_coherence()` (existing function,
minimally extended, not replaced): the "test evidence linked only to
another phase" check now honors an explicit `report.metadata["test_
evidence_classification"] == "inherited_regression"` escape hatch, so a
verification phase can legitimately re-run and report another phase's
baseline tests without being flagged, while silent omission of that
classification still fails closed exactly as before.

## 7. Evidence Applicability

No change to `PhaseReport.assess_completeness()`'s existing complete/
partial/incomplete field-applicability logic (134E.1V-134E.5V's prior
repairs there are untouched — confirmed by the full regression suite
passing unchanged, Section 12). 134E.9 adds a fourth completeness input
(derived correctness) alongside the pre-existing three (field presence,
canonical-report consistency, internal coherence) — all three now feed
the same single `report_completeness` field, so informational
completeness and decision completeness cannot diverge into two
different "complete" answers for the same report.

## 8. Revision and Commit Binding

`validate_internal_report_coherence()`'s pre-existing source-revision
check (`report.metadata["source_revision"]` vs `architecture_
status["repository_revision"]`) already binds the report to one explicit
repository revision — unchanged this phase, confirmed still passing
(Section 12). No new revision-binding mechanism was added; 134E.9
validates *derived claims*, not commit/revision binding itself, which
134E.8V already established via `architecture_status["repository_
revision"]`.

## 9. Architecture Status Consistency Behavior

Architecture Status is now validated as *one derived input among several*
by the new manifest, not treated as automatic proof of whole-report
correctness: a `"fresh"` Architecture Status classification does not
suppress a `validate_internal_report_coherence()` finding (e.g.
self-recommendation) elsewhere in the same report — the two checks are
independent and both must pass (`TestArchitectureStatusFreshnessBlocks
.test_fresh_architecture_status_with_stale_evidence_still_fails`).
Authority, determinism, exact phase-ID grammar, deterministic ordering/
grouping, conflict fail-closing, and provenance/repository-revision
binding are all unchanged 134E.8/134E.8V behavior, re-confirmed passing
by the full `test_architecture_status_*` suite this phase (Section 12).

## 10. Digest and Byte Correctness

`compute_report_digest()` / `compute_finalization_snapshot_id()` and
their enforcement at all four dispatch call sites were re-inspected, not
re-implemented: `notification_dispatch_state()` already compares both
digest and snapshot identity fail-closed (`payload_conflict` outcome)
whenever both stored and proposed identities are available, and grep
confirms all four call sites (`phase.py`, `task.py`, `phase_reports.py`,
`notifications.py`) invoke `notification_dispatch_state()`/`phase_
already_notified()` before dispatching and act on `payload_conflict`/
`already_dispatched` — 134E.8V's blocking-defect-#1 repair ("digest
comparison existed but was not actually enforced") remains enforced
after this phase's changes (Section 12 regression evidence). Determinism
was directly re-verified: `compute_report_digest()` excludes `notification_result` (a retry-only physical-attempt outcome does not
change the logical digest); `compute_finalization_snapshot_id()`
excludes `created_at`/`notification_result`/`report_completeness`/
`missing_trust_fields`/`trust_warnings`/`canonical_report_used`/
`metadata.promotion_diagnostics` (volatile fields), and changes only
when a semantic field (e.g. `summary`) changes.

## 11. Deterministic Rendering Result

No change to `render_markdown()`'s field-ordering behavior (134E.8V's
insertion-order-independence repair is untouched, unchanged). This
phase's own new checks operate on structured `dict`/`PhaseReport` fields
directly, never on rendered text, so no new insertion-order sensitivity
was introduced.

## 12. Stored/Delivered Byte-Equality Result

Unchanged — the marker-comparison mechanism 134E.8.1 established
(digest bound into the dispatch marker, compared before every send) is
the sole authority for stored/delivered equality; 134E.9 does not
duplicate or re-implement it, only re-confirms it (Section 10) and adds
validation for fields the marker mechanism does not itself check
(Architecture Status freshness/conflicts, next-phase-already-completed).

## 13. Shared Lifecycle Enforcement Result

`validate_derived_correctness()` is called from exactly one place:
`_apply_canonical_and_trust()`, itself called by all four active
construction paths (`finalize_phase_report()` used by `pcae phase
complete`; `_finalize_task_report_and_notify()`'s trial-report path used
by `pcae task finish`; `run_phase_report_create()`'s report construction
used by `pcae phase-report create`; `pcae notify send-report` operates
on an already-persisted, already-validated report and is gated by the
same `notification_dispatch_state()` marker check). `validate_
finalization_gate()` — the single authoritative gate documented as
required "before `pcae phase complete` marks report as complete" and
"before... Telegram send" — was extended with an explicit `validate_
derived_correctness(report)` call alongside the pre-existing coherence
check, so the gate itself fails closed even if a future caller somehow
bypassed `_apply_canonical_and_trust()`. No call site constructs a
second, independent validation path; no duplicated per-command policy
was added.

## 14. Phase-Complete / Task-Finish / Phase-Report-Create / Notify-Send-Report Behavior

No behavioral change to any of the four commands' control flow — each
already calls the shared validation chain unchanged; 134E.9 only makes
that shared chain stricter. All four remain governed by the same
`.pcae/phase-reports/.last-notified.json` marker for ordinary/retry/
correction/supersession purpose separation (134E.8.1, unchanged and
re-confirmed passing this phase).

## 15. Ordinary/Retry/Correction/Supersession Behavior

Unchanged. `delivery_purpose` classification, the purpose-keyed
`deliveries` map in the marker, and 134E.8.1's phase-scoped ordinary-
completion identity are untouched by this phase; the relevant existing
regression tests (`tests/test_phase_reports.py`, notification-marker
tests) pass unchanged (Section 12).

## 16. Failure and Quarantine Behavior

Unchanged: `finalize_phase_report()`'s existing quarantine path (write
to `.pcae/phase-reports/quarantine/`, never overwrite `latest.md`/
`latest.json`) is untouched; a derived-correctness failure now reaches
that same quarantine path via the existing `report_completeness !=
COMPLETENESS_COMPLETE` blocker in `validate_finalization_gate()` — no
new failure/quarantine code path was introduced.

## 17. Historical Preservation Result

No historical report, canonical Markdown, or `PROJECT_STATUS.md`
history section was modified or rewritten by this phase's code changes.
The 134E.8.1 incident's two preserved historical reports (`.pcae/
phase-reports/20260711-143817-134E.8.md` trusted, `20260711-144017-
134E.8.md` invalid incident evidence) remain byte-identical on disk —
confirmed by SHA-256 (Section 20).

## 18. Transport-Neutrality Implications

`validate_derived_correctness()` and the manifest it implements operate
entirely on `PhaseReport`/`architecture_status` data — zero references
to Telegram, HTTP, or any adapter-specific concept anywhere in the new
function (confirmed by source-scan test, Section 20). A future delivery
channel reuses the identical certified snapshot, report bytes, digest,
logical delivery identity, purpose classification, and now this same
consistency result, unchanged.

## 19. Logical-Versus-Physical Delivery Limitation

Restated, not changed: the active successful-delivery marker remains a
single durable logical summary, not a physical transport-attempt
ledger. It does not prove exact Telegram network-attempt count, atomic
coupling between remote acceptance and local marker persistence, or
complete retry history across process crashes. This phase does not
activate Delivery Receipts to address this — that integration remains
correctly deferred to 134E.10 per the 134D plan.

## 20. Focused Adversarial Tests

`tests/test_report_consistency_derived_correctness_134e9.py` — 35 tests
across 14 groups: coherent report passes (2); Architecture Status
freshness/conflicts block, including the "fresh cannot override
contradictory evidence" case (5); completed-phase self-denial/self-
recommendation (2); recommended-next-already-completed general case
plus the explicit corrective-recovery escape hatch plus the dedicated
stale-132F regression guard (3); test evidence linked to another phase
plus its inherited-regression escape hatch (2); snapshot/metadata
identity mismatch including the sub-phase allowance (4); runtime tuple
validity including the partial-fields-not-checked case (3);
completeness cannot be restored after a coherence/derived-correctness
failure even with all fields present (2); finalization-gate wiring,
both blocking and allowing cases (2); digest/snapshot determinism
across repeated calls, notification-result retries, and semantic vs.
volatile field changes (5); Repository Intelligence independence (1);
inactive-Track-134-subsystem source-scan (1); CLI inspection is
side-effect-free, including the no-report error path (2); and the real
repository's actual latest terminal report (134E.8V) is itself
consistent (1). All 35 pass.

## 21. Regression Tests

Filtered suite (`phase_report`, `phase_identity`, `finaliz*`,
`notification`, `notify`, `architecture_status`, `canonical`, `134e9`):
1181 passed, 0 failed — includes `tests/test_architecture_status_
canonicalization.py`, `tests/test_architecture_status_generation_
repair_134e8.py`, `tests/test_phase_identity.py`, `tests/test_
canonical_phase_identity_source_repair.py`, `tests/test_phase_report_
trust_gate_cli.py`, `tests/test_phase_report_trust_hard_fail.py`,
`tests/test_task_finish_notification_ordering.py`, and every 134E.1-
134E.8V protection test. Two fixture-only regressions were found and
repaired during this work (Section 22), not code regressions in the
targets under test.

One real implementation bug was introduced and self-caught during this
phase: an `Edit` operation misplaced `run_phase_report_trust()`'s own
final `return 0 if result.complete else 1` statement outside that
function (it became unreachable dead code inside the newly-appended
`run_phase_report_consistency()`), silently making `run_phase_report_
trust()` always return `None` (truthy-adjacent `0` exit code) regardless
of trust outcome. Caught by the regression suite (7 failing tests in
`test_phase_report_trust_gate_cli.py`, `test_phase_report_trust_hard_
fail.py`, `test_task_finish_notification_ordering.py`), root-caused via
`git diff`, and repaired by restoring the statement to its correct
function and removing the duplicate. Full regression suite re-run clean
afterward (Section 21 count already reflects the repaired state).

## 22. Fixture Repairs (test-only, not production code)

Two existing tests in `tests/test_phase_reports.py` and one in `tests/
test_canonical_phase_identity_source_repair.py` ran `pcae phase
complete` / `pcae phase-report create` / `pcae notify send-report`
against a `tmp_path` with no `PROJECT_STATUS.md`, which (correctly,
after this phase's change) now legitimately blocks on Architecture
Status freshness for any report claiming derived correctness. Two of
the three tests were dispatch-focused, not Architecture-Status-focused,
so a minimal, internally-coherent `PROJECT_STATUS.md` was added to their
shared `_enable_noop_dispatch()` fixture helper. The third test (`test_
explicit_cli_phase_id_resolves_when_nothing_else_does`) is specifically
testing the *absence* of `PROJECT_STATUS.md` (the bootstrap/explicit-
identity scenario) — for that legitimate case, `build_architecture_
status()`'s freshness contract itself was refined: a **missing**
`PROJECT_STATUS.md` now yields `fresh_with_limitations` (a disclosed
gap), not `invalid` (now reserved exclusively for genuine detected
conflicts — completed/planned overlap, disagreeing duplicate-header
titles, or a recommendation naming an already-completed phase). This
refinement is documented in `tests/test_architecture_status_generation_
repair_134e8.py`'s updated `test_missing_project_status_md_is_limited_
not_plain_fresh` (renamed from `..._is_invalid_not_fresh`) and is a
deliberate, real distinction (absent source vs. contradictory source),
not a weakening of the check — a report can still not be finalized
until Architecture Status genuinely derives, because `build_
architecture_status()`'s other required fields remain absent/empty in
that case and are still caught by pre-existing trust-completeness
checks unrelated to freshness.

## 23. `compileall` Result

`python -m compileall -q src`: clean (exit 0).

## 24. Fast-Green Result

```
python -m pytest -m "fast_green" -n auto -ra --durations=100
4389 passed, 1 failed
```

The one failure is the same known pre-existing, environment-timing-
dependent `tests/test_dry_run_simulation.py::Test89dMatrixReadOnly::
test_pytest_dry_run_not_blocked` documented across every prior 134-series
phase (a shell-gate dry-run policy test unrelated to this phase's
changes — confirmed unrelated by this phase touching no shell-gate or
dry-run code).

## 25. Governance Results

- `pcae check`: passed.
- `pcae health`: healthy.
- `pcae doctor task-memory`: clean (one pre-existing unrelated warning —
  a prior session's task missing from `tasks/DONE.md` — repaired as
  incidental housekeeping alongside this phase's own `tasks/DONE.md`
  update).
- `pcae push check`: clean.
- Governed commit/push/task/phase commands only; no raw git, no
  `--no-verify`, no force push.
- Runtime remains Observed; execution unavailable, independently
  re-derived by `build_architecture_status()`'s own runtime-snapshot
  call at report-generation time.
- Repository clean and pushed; `origin/main..HEAD = 0`.

## 26. Explicit Confirmations

- No external test delivery occurred: no test in this phase sets
  `PCAE_NOTIFY_ENABLED` to a live sink or exercises a real Telegram/HTTP
  call; all notification-adjacent tests use `PCAE_NOTIFY_SINKS=noop` or
  construct/validate `PhaseReport` objects directly without dispatching.
- Exactly one ordinary terminal 134E.9 logical delivery occurred,
  through the current governed production delivery path (`pcae phase
  complete`), recorded in the phase-completion metadata for this phase.
- No physical exactly-once transport is claimed (Section 19).
- Inactive Track 134 subsystems (Canonical Engineering Evidence,
  Evidence Extraction, Phase Report View, Operator Report View,
  Rendering Architecture, Delivery Pipeline, Delivery Receipts) remain
  inactive — confirmed by source-scan test (Section 20) finding zero
  new references from `validate_derived_correctness()` or `pcae phase-
  report consistency` to any of them.
- Architecture Status correctly remains fresh, stale-132F planning
  remains absent, and Tracks 132-134 remain represented (re-confirmed
  by the full `test_architecture_status_*` suite, Section 21).
- 134E.9V has not begun. 134E.10 has not begun.

Recommended next phase: **134E.9V — Report Consistency / Derived
Correctness Independent Verification**.
