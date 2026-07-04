# Phase 113X.5 — Architecture Status Canonicalization

## Purpose

Governance repair phase, closing 113X (Cross-Agent Governance
Verification) Finding 4: Architecture Status derived coarse-grained,
per-series maturity labels from a static mapping, over-claiming
completion. This phase replaces that mapping with a canonical,
evidence-driven derivation that can never claim more than what is
actually documented as complete.

No Advisory Runtime, Runtime Snapshot, Runtime Context, Runtime
Registry, Runtime Inspect, Permission Broker, execution, authorization,
plugin, Telegram-inbound, REST, Web UI, or Dashboard changes. No
changes to Canonical Phase Identity (113X.4), the Finalization Gate
(113X.1), or the Mobile Notification Guarantee (113X.3). Architecture
Status derivation only.

## Previous Derivation Model

`_series_label()` mapped a phase's numeric series to a **static,
hardcoded string** describing that series' entire eventual scope:

```python
SERIES_MAP: dict[str, str] = {
    "110": "Runtime Foundation",
    "111": "Runtime Introspection Foundation",
    "112": "Runtime Context, Snapshot & Inspect Integration",
    "113": "Advisory Runtime (Architecture, Contract, Prototype)",
}
```

`build_architecture_status()` deduplicated completed phases by their
3-digit series prefix and used the **first** occurrence to trigger this
label, regardless of which specific lettered phases within that series
had actually completed. The moment a single "113" phase completed
(even 113A alone, "Architecture" only), the label already read
"Advisory Runtime (Architecture, Contract, Prototype)" — falsely
implying Contract and Prototype were also done.

Compounding this, the existing consistency check meant to catch "X
complete while X still planned" matched by searching for the series
digits *as a literal substring inside the display label*
(`if series in comp and "Prototype" in comp`). The hardcoded label
contains no digits at all, so this check could **never fire** — the
exact reason Finding 4's impossible combination went undetected in
production (reproduced directly during the original 113X forensic
audit against this repository's own history).

## Canonical Derivation Model

### Completed

Each numeric series' label is now rendered by
`_render_series_milestone_label()` from **exactly** the phases whose
own `"## Phase X Complete"` header exists in PROJECT_STATUS.md —
never inferred, never extrapolated to a phase whose header is absent:

- A single completed phase renders as its own full title (nothing to
  abbreviate against).
- Multiple completed phases render as their titles' longest-common
  prefix (the shared "track name," e.g. `"Advisory Runtime"`) followed
  by each phase's own distinguishing remainder, joined with `" + "`,
  in phase-letter order — so the label grows **exactly in step** with
  which phases have actually completed:
  - Only 113A complete → `"Advisory Runtime Architecture"`
  - 113A + 113B complete → `"Advisory Runtime: Architecture + Contract Freeze"`
  - 113A + 113B + 113C complete → `"Advisory Runtime: Architecture + Contract Freeze + Prototype (Observation-Only)"`

`_is_milestone_phase_id()` excludes sub-phases (`113B.2`) and the
`"X"` exceptional/corrective-governance branch (`113X.1`–`113X.5`
themselves) from milestone consideration — these are governance
hardening, not architecture-track progress, and including them would
misrepresent what actually advanced the architecture. The 110–113
architectural-foundation-track scope filter is unchanged from before —
a scope boundary (which phases this section is *about*), not a
maturity claim, and therefore not part of Finding 4's actual defect.

Completed phases are sorted by `(series, branch, subphase)` — a
deterministic key independent of the order headers physically appear
in the file, closing the same "out-of-order documentation" fragility
113X Finding 6 identified in the recommendation-picking logic.

A new structured field, `completed_phase_ids` (a flat, sorted list of
the exact phase IDs behind `completed`), is now also returned —
consistency validation uses this directly instead of regex-parsing the
human-readable `completed` strings, the fragility that let Finding 4's
own detection check silently never fire.

### In Progress / Planned

Independently derived from disjoint evidence, exactly as before, with
one robustness improvement: the "Recommended next repo phase" sentence
is now read **from within the `"## Current Phase"` section's own
bounded text** (the actual latest phase's own recommendation) rather
than "nearest the top of the whole file" — closing 113X Finding 6's
latent fragility directly, where a mis-ordered file section could make
the wrong recommendation win. Falls back to the old whole-file search
only if the current section doesn't contain the sentence at all.

Neither `in_progress` nor `planned` is derived from `completed`, and
`completed` is not derived from either of them — each comes from its
own distinct regex match against PROJECT_STATUS.md.

## Consistency Guarantees (validate_phase_identity, strengthened)

All checks below are hard blockers (fail-closed), consistent with
113B.2's original design:

1. **Completed ∩ Planned = ∅.** A phase ID appearing in
   `completed_phase_ids` can never also appear as the leading ID of a
   `planned` entry — direct set-membership against structured evidence
   (this is the repaired Finding 4 check).
2. **In-progress ∩ Planned = ∅.** A phase can't be both actively
   worked on and recommended as the next phase.
3. **Runtime state vs. execution availability.** `current_runtime_
   state == "Observed"` can never coexist with `execution_availability
   != "unavailable"` — Observed is this codebase's non-executing
   ceiling (Runtime State Model, 110A); this validates Architecture
   Status's own two fields for internal agreement without reading or
   modifying Runtime Snapshot itself.
4. **Metadata execution-integration vs. Architecture Status**
   (pre-existing, unchanged): runtime-state/capability mismatches
   between `.pcae/phase-completion-metadata.json` and Architecture
   Status are flagged.

**Considered and deliberately not implemented:** a "consecutive
letters" gap check (e.g. flagging 113A + 113C complete with 113B
absent as "Contract missing"). Prototyped, then rejected after it
produced a false positive against this repository's own real history:
`111R` ("Runtime Architecture Review") legitimately follows `111D`
with a non-consecutive, mnemonic letter — this codebase's own
convention. A heuristic that can't reliably distinguish "intentional
mnemonic letter" from "genuine documentation gap" would itself be a
form of inference this phase exists to remove. The underlying
acceptance criterion (never claim unearned work) is satisfied
structurally instead: `_render_series_milestone_label()` only ever
includes phases with actual completion evidence, so a missing phase is
silently and accurately absent from the label — never fabricated,
never asserted.

## Fail-Closed Behavior

Unchanged from 113B.2: any of the four consistency checks above
failing is a hard blocker in `validate_finalization_gate()`, enforced
through 113X.1's existing quarantine path — never advisory, never
downgraded to a warning.

## Determinism

`build_architecture_status()` reads only PROJECT_STATUS.md (a
deterministic text file at report-generation time) and Runtime
Snapshot's read-only health fields; all grouping and sorting use
explicit, stable sort keys (`(series, branch, subphase)` tuples, not
set/dict iteration order or file-scan order). Two calls against
identical repository state produce byte-identical output (verified
directly, and by a scrambled-vs-ordered-file-section regression test).

## Scope

- `src/pcae/core/phase_reports.py` — `_is_milestone_phase_id()`,
  `_longest_common_prefix()`, `_render_series_milestone_label()` (new);
  `build_architecture_status()` rewritten; `_series_label()` (hardcoded
  `SERIES_MAP`) removed; `validate_phase_identity()`'s Architecture
  Status consistency checks rewritten around the new
  `completed_phase_ids` structured field, plus two new checks (runtime
  state vs. execution availability; completed-vs-planned via direct
  set membership)
- `tests/test_architecture_status_canonicalization.py` — 15 new tests
- `tests/test_phase_identity.py` — 1 pre-existing test strengthened
  from a soft ("either way acceptable") assertion to a strict one, now
  that the underlying mechanism it exercises actually works
- `docs/PHASE_113X5_ARCHITECTURE_STATUS_CANONICALIZATION.md` — this document

## Test Coverage

15 tests in `tests/test_architecture_status_canonicalization.py`:

| Group | Tests | Focus |
|---|---|---|
| Finding 4 regression | 1 | Only 113A complete never claims Contract/Prototype |
| Progressive partial completion | 3 | Architecture-only, +Contract, +Contract+Prototype |
| Mixed / incomplete phase series | 3 | Multiple series each get their own line; incomplete series show only what's evidenced; out-of-scope series excluded |
| Deterministic output | 2 | Repeated calls identical; scrambled vs. ordered file sections identical |
| Consistency validation | 6 | Recommendation consistency; completed∩planned and in-progress∩planned impossible combinations; runtime-state/execution-availability consistency (both directions); metadata capability-mismatch (pre-existing, unchanged) |

Plus 1 pre-existing test in `tests/test_phase_identity.py` strengthened.

## Validation

- `python -m pytest tests/test_architecture_status_canonicalization.py tests/test_phase_identity.py -n auto -q`
- `python -m pytest tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_finalization_gate_enforcement.py tests/test_finalization_notification_guarantee.py tests/test_canonical_phase_identity_source_repair.py tests/test_phase_report_trust_hard_fail.py tests/test_phase_report_trust_gate_cli.py tests/test_docs.py tests/test_phase.py -n auto -q`
- `python -m pytest -n auto -q` (full suite)
- `python -m pytest -m fast_green -n auto -q`
- `pcae health && pcae check && pcae doctor task-memory && pcae push check`

## Architectural Review: Report Generator vs. Dedicated Runtime Service

**Question:** should Architecture Status remain inside
`phase_reports.py`, or become a dedicated Runtime Architecture Status
Service?

**Recommendation: remain inside the report generator for now; document
the service extraction as a future option, not act on it this phase.**

**Evidence for staying put:**

- Architecture Status has exactly one consumer today: `PhaseReport`
  (via `finalize_phase_report()` → `build_architecture_status()`).
  There is no CLI command, no Runtime Snapshot integration, no
  Telegram/REST/dashboard consumer independent of the phase report
  itself (verified: `grep -rn "build_architecture_status"` across
  `src/pcae/` returns only its definition and its one call site).
  Extracting a "service" implies multiple independent consumers or an
  independent invocation surface — neither exists.
- It is a **pure function of two already-canonical, already-read-only
  sources** (PROJECT_STATUS.md text, RuntimeSnapshot's health fields).
  It doesn't own state, doesn't persist anything, doesn't require a
  registry entry or a lifecycle of its own — the defining
  characteristics of PCAE's actual "Runtime Service" pattern (compare
  `RuntimeRegistry`, which owns a live in-memory plugin store with its
  own admission/lifecycle rules) don't apply here.
- The STRICT NO-GO list for this very phase separately protects
  Runtime Snapshot, Runtime Registry, and Runtime Inspect — three
  actual dedicated Runtime subsystems. Folding Architecture Status into
  that family would require design work (a ninth/tenth RuntimeSnapshot
  domain? a new registry category?) explicitly out of this phase's
  authorized scope, and not clearly justified by current consumer
  count.

**Evidence for eventual extraction (a real, not hypothetical,
consideration):**

- If a *second* independent consumer appears — e.g. `pcae runtime
  inspect --verbose` wanting to show Architecture Status directly, or a
  future dashboard/REST endpoint — a dedicated module (not necessarily
  a full "service" with CLI/registry machinery, just
  `core/architecture_status.py` housing the pure functions this phase
  added) would let both consumers share one canonical implementation
  without importing through `phase_reports.py`'s much larger surface
  (finalization gate, notification dispatch, quarantine — none of
  which a hypothetical second consumer needs).
- `RuntimeSnapshot` (112E) already establishes the precedent of
  composing independently-owned domains into one read-only snapshot
  object; Architecture Status's inputs (PROJECT_STATUS.md text +
  `snapshot.health`) are conceptually adjacent to that pattern, and a
  tenth `architecture` domain is a plausible, evidence-grounded future
  addition **if and when** a second real consumer appears (deliberately
  not decided here, per this phase's own "no large refactor" and "do
  not modify Runtime Snapshot" constraints).

**If a future phase pursues extraction:** move the pure functions
added here (`_is_milestone_phase_id`, `_longest_common_prefix`,
`_render_series_milestone_label`, and `build_architecture_status`
itself) verbatim into a new `src/pcae/core/architecture_status.py`,
with `phase_reports.py` importing and re-exporting
`build_architecture_status` for backward compatibility. No behavior
change would be required — this is a pure module-boundary move,
correctly deferred until a second consumer creates real evidence for
it, per this phase's "no hardcoded/inferred claims" discipline applied
to architecture decisions too.

## Recommended Next Phase

**113XR — Governance Recovery Review** (final architectural review
confirming Findings 1, 3, 4, 6, and 7 are all resolved, governance
consistency is restored, and PCAE is ready to resume the Runtime
roadmap).
