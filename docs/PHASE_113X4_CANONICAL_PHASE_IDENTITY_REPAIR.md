# Phase 113X.4 — Canonical Phase Identity Repair

## Purpose

Governance repair phase, closing 113X (Cross-Agent Governance
Verification) Finding 3 **in full**. 113X.2 only detected a
*disagreement* between a regex-derived `--summary` phase_id and
`.pcae/phase-completion-metadata.json`'s declared one; this phase
removes the regex derivation itself, replacing it with a single,
deterministic canonical-identity resolution that never consults free
text at all.

No Advisory Runtime, Runtime Snapshot, Runtime Context, Runtime
Registry, Runtime Inspect, Permission Broker, execution, authorization,
plugin, Telegram-inbound, REST, Web UI, Dashboard, or Architecture
Status changes. Canonical phase identity only.

**Note on numbering:** this repair was requested as "113X.2," but
113X.2 (Canonical Phase Identity Source Repair) and 113X.3 (Finalized
Phase Mobile Notification Guarantee) were already completed and pushed
in this same governance arc. Reusing "113X.2" would have recreated
exactly the kind of phase-identity collision this arc exists to
prevent, so this work is recorded as **113X.4** instead (confirmed with
the human operator before starting).

## Previous Identity Derivation

`_derive_phase_id()`/`_derive_phase_name()`/`_derive_next_phase()`
(`src/pcae/commands/phase.py`) extracted phase identity by regex over
free-text `--summary`:

```python
m = re.search(r"Phase\s+(\d+[A-Z](?:\.\d+)*)", summary)
```

`re.search` (not anchored) matches the **first** "Phase X" pattern
*anywhere* in the string. A summary written as "Implements the
Advisory Runtime, extending Phase 113B's frozen contract into a
concrete prototype" while completing Phase 113C would have its
identity misread as `113B` — exactly the forensic finding: contextual
references to previous work becoming the report's own identity.
113X.2 added a check that this regex-derived value did not conflict
with metadata's declared `phase_id`, but the regex derivation itself,
and the risk it represents whenever metadata is absent or a summary
happens to open with a "Phase X: ..." reference to something else,
remained.

A second instance of the same problem existed inside `validate_phase_
identity()`'s check #5 ("Summary text vs report phase_id"): it treated
a summary's leading "Phase X: ..." reference disagreeing with the
resolved `phase_id` as a hard blocker — itself a form of free text
gating (if not determining) the finalization outcome, discovered while
writing this phase's own regression tests (see Design Decisions).

## Canonical Identity Model

`resolve_canonical_phase_identity()` (`src/pcae/core/phase_reports.py`)
is the single resolution point. It takes **no summary parameter at
all** — `--summary` cannot influence the outcome even in principle, not
just "in practice by discipline." It tries four sources in a fixed
precedence order, returning the first that resolves; `phase_id` and
`phase_name` always come from the *same* winning source, never mixed:

1. **Active task contract** — the active task's own `Title` field
   (e.g. `"Phase 113X.4: Canonical Phase Identity Repair"`), parsed
   only when the title *starts* with a "Phase X: ..." reference
   (`_parse_leading_phase_reference()`, anchored at position 0 — this
   anchoring is what makes it structurally safe: a phase mentioned
   mid-prose, anywhere else in the title, never matches).
2. **Explicit phase-completion metadata** —
   `.pcae/phase-completion-metadata.json`'s structured `phase_id`/
   `phase_name` fields, read directly, never regex-parsed.
3. **Active lifecycle context** — PROJECT_STATUS.md's "## Current
   Phase" section text, but only when not already marked
   `(completed)` — i.e. only when it genuinely describes an
   in-progress phase, not the previously-finalized one.
4. **Explicit CLI argument** — new `--phase-id`/`--phase-name` flags on
   `pcae phase complete`, the last-resort override for bootstrapping.

`recommended_next_phase` is likewise structured-metadata-only now:
`commands/phase.py` no longer falls back to `_derive_next_phase(summary)`
when metadata doesn't declare one — it stays empty, and the pre-existing
`validate_finalization_gate()` blocker ("recommended_next_phase missing
as structured metadata") fails closed naturally.

## Fail-Closed Behavior

If none of the four sources resolve, `resolve_canonical_phase_identity()`
returns `None`. `_finalize_report_and_notify()` treats this as an
immediate, hard refusal: it prints an explicit message and returns
`False` **before** constructing any `PhaseReport` or writing any
artifact at all — not even a quarantined one, since there is no
identity to build a report around. This is stronger than 113X.1's
quarantine (which still produces a forensic artifact for a *known but
untrusted* identity): here there is no identity, known or otherwise, so
nothing is written.

## Design Decisions

1. **`resolve_finalization_phase_identity()` (113X.2) is retired, not
   kept alongside the new resolver.** Its entire premise — comparing a
   regex-derived `--summary` value against metadata — no longer
   applies once that regex derivation is removed; keeping it would be
   dead code implying a mechanism that no longer exists.
   `validate_finalization_gate()`'s `identity_conflict:` parameter is
   kept as a general hook (any other caller may still detect and pass
   a conflict), but `pcae phase complete` now always passes `None`.
2. **`validate_phase_identity()` check #5 ("Summary text vs report
   phase_id") was removed**, discovered as a necessary consequence
   while writing this phase's own mandated regression tests (a summary
   opening with "Phase 999Z: ..." must not block a canonically-correct
   completion). Objective 1's "free-text summaries must never
   determine phase id" extends to *validation* outcomes too, not just
   *derivation* — a hard blocker triggered by incidental summary
   phrasing is exactly the kind of free-text influence this phase
   removes. Check #6 (commit messages vs phase_id) is untouched: it is
   not `--summary`, and not in this phase's scope.
3. **"Active lifecycle context" only counts when not `(completed)`.**
   This project's own convention marks "## Current Phase" as completed
   *before* running `pcae phase complete`, so in practice this source
   rarely fires (task contract or metadata usually resolve first) —
   but it exists as a defined, working fallback exactly as specified,
   for the case where a phase is genuinely mid-flight with no active
   task or metadata file yet.
4. **`pcae task finish --commit`'s identity path is untouched.** It
   already reads `phase_id` solely from structured metadata (never
   `--summary`), so it already complied with objective 1 and needed no
   change — consistent with 113X.1/113X.2/113X.3 precedent of scoping
   fixes to the authoritative `pcae phase complete` path.
5. **Backward compatible by construction, not by preserving old
   behavior.** "Existing lifecycle commands continue working" is
   satisfied because the *contract* (`pcae phase complete --summary
   ...` completes a phase, blocks on real problems, writes a report)
   is unchanged; only *how* `phase_id`/`phase_name`/
   `recommended_next_phase` are determined changes. Every phase
   completed under the old regime with metadata correctly populated
   continues to resolve identically (metadata is precedence level 2 in
   both models).

## Scope

- `src/pcae/core/phase_reports.py` — `CanonicalPhaseIdentity`,
  `_parse_leading_phase_reference()`, `resolve_canonical_phase_identity()`
  (new); `resolve_finalization_phase_identity()` removed;
  `validate_phase_identity()` check #5 removed
- `src/pcae/commands/phase.py` — `_derive_phase_id()`/
  `_derive_phase_name()`/`_derive_next_phase()` removed; new
  `_read_lifecycle_current_phase_line()`; `_finalize_report_and_notify()`
  rewritten to use the canonical resolver, gains `cli_phase_id`/
  `cli_phase_name` parameters, fails closed on unresolved identity
- `src/pcae/cli.py` — `pcae phase complete` gains `--phase-id`/
  `--phase-name` optional arguments
- `tests/test_canonical_phase_identity_source_repair.py` — 27 new tests
  (supersedes and replaces `tests/test_canonical_phase_identity_repair.py`,
  113X.2, which tested the now-removed comparison mechanism)
- `tests/test_phase_identity.py` — 2 pre-existing tests updated (they
  exercised the retired check #5 / used it as their blocker example)
- `tests/test_finalization_notification_guarantee.py` — 1 pre-existing
  test updated (113X.2's "conflict" scenario is now "metadata wins
  cleanly, summary is irrelevant" — not a conflict at all)
- `docs/PHASE_113X4_CANONICAL_PHASE_IDENTITY_REPAIR.md` — this document

## Safety Invariants

- No Advisory Runtime, Runtime Snapshot, Runtime Context, Runtime
  Registry, Runtime Inspect, or Permission Broker changes
- No execution capability introduced or changed
- No authorization, plugin, Telegram-inbound, REST, Web UI, or
  Dashboard changes
- No Architecture Status derivation or label changes
- Runtime state remains Observed
- Maximum plugin capability remains `observe`
- Execution availability remains unavailable
- 113X.1 quarantine semantics unchanged (blocked reports never write
  `latest.*`, remain silent)
- 113X.3 notification-outcome model and branch-aware phase-ID ordering
  unchanged

## Test Coverage

27 tests in `tests/test_canonical_phase_identity_source_repair.py`:

| Group | Tests | Focus |
|---|---|---|
| Resolver precedence (unit) | 6 | Each of the 4 sources wins in the right circumstance; fail-closed on none |
| Forensic scenario reproduction | 4 | Summary mentioning previous/future/multiple phases never affects identity; canonical identity always wins over a contradicting summary |
| Invalid identity fails closed | 2 | No source resolves → refuse, write nothing; explicit `--phase-id` resolves as last resort |
| Report matches canonical sources | 2 | `phase_id` matches active task; `phase_name` matches canonical metadata |
| Recommendation chain correct | 2 | `recommended_next_phase` from metadata, not summary; absent metadata value fails closed via the pre-existing gate blocker |
| Backward compatibility | 4 | Matching identity completes normally; 113X.1 quarantine intact; `--allow-partial-report` intact; 113X.3 branch-aware check intact |

Plus 2 pre-existing tests updated in `tests/test_phase_identity.py` and
1 in `tests/test_finalization_notification_guarantee.py`.

## Validation

- `python -m pytest tests/test_canonical_phase_identity_source_repair.py tests/test_phase_identity.py -n auto -q`
- `python -m pytest tests/test_finalization_gate_enforcement.py tests/test_finalization_notification_guarantee.py tests/test_phase_reports.py tests/test_phase_reports_cli.py tests/test_phase_report_trust_hard_fail.py tests/test_phase_report_trust_gate_cli.py -n auto -q`
- `python -m pytest tests/test_docs.py tests/test_phase.py tests/test_provenance.py tests/test_task_finish_notification_ordering.py tests/test_task_finish_report_trust_notification.py -q`
- `python -m pytest -n auto -q` (full suite)
- `python -m pytest -m fast_green -n auto -q`
- `pcae health && pcae check && pcae doctor task-memory && pcae push check`

## Recommended Next Phase

**113X.5 — Architecture Status Derivation Hardening** (the requesting
brief's own "113X.4" recommendation, shifted by the same +2 offset as
this phase's own renumbering — 113X.3 already exists).
