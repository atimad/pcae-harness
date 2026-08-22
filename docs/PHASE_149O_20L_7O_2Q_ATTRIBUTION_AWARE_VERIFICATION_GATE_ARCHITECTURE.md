# Phase 149O.20L.7O.2Q — Attribution-Aware Verification Gate Architecture

Status: analysis and design only. No changes to
`src/pcae/core/phase_reports.py`, `_fast_green_failure_signal()`,
`validate_derived_correctness()`, or any other live gate logic. No
change to the `fast_green` field's accepted values. Phase
149O.20L.7O.2P remains quarantined (staged pending push) and is not
touched, pushed, or promoted by this phase.

## Section 1 — Why the current gate is insufficient

`test_results["fast_green"]` is validated by
`_fast_green_failure_signal()` (`phase_reports.py:1545`), called from
`validate_derived_correctness()` (`phase_reports.py:1656`). The check
is deliberately absolute: any confidently-parsed nonzero failure count
blocks `pcae phase complete`, "regardless of how the failure is
narrated (e.g. 'pre-existing', 'unrelated') — that narration is not
itself verified evidence" (`phase_reports.py:1650-1655`). There is no
structured escape hatch; the code comment at `phase_reports.py:1508`
states this is intentional: "a governed classification cannot make a
real fast_green failure retroactively not have happened."

This was the correct fix for the failure mode it targeted (Phase
134E.9.1 — a report narrating "4389/4390, one pre-existing unrelated
failure" was accepted as complete without the codebase ever verifying
that claim). But it has a side effect the 134E.9.1 fix did not
distinguish from what it was solving: **it makes the single scalar
`fast_green` field carry two different, easily conflated meanings** —
"the repository, right now, has zero known test failures" and "this
phase introduced zero regressions." Those are different claims, and
only the second one is actually load-bearing for whether a phase's
*own work* is safe to certify.

The practical consequence, reproduced directly in Phase 149O.20L.7O.2P:
a controlled baseline-vs-HEAD comparison (isolated worktree, exact
failing-node-ID diff, no `--deselect`) found 0 fixed, 0 attributable
regressions, and exactly 2 new differences — one an expected phase
artifact (a report asserting `HEAD == origin/main`, which is
necessarily false while the phase's own commits are unpushed) and one
a confirmed environment flake (a subprocess timeout in an audit-persist
test, non-reproducing on isolated rerun). Both are real, non-regression
explanations. Neither can be expressed in the current schema without
writing descriptive prose into the `fast_green` string field — which
memory `project_phase_completion_procedure.md` (correction #2) already
documents as the established workaround: report a **deselected** clean
run as the structured field, and put the raw unfiltered count with
attribution only in prose. That workaround works, but it means the
one piece of the report the gate actually machine-checks is, by
convention, no longer the real number — it is a pre-filtered number the
author chose to construct, with the filtering rationale living entirely
outside the gate's reach. The gate is verifying an artifact of the
reporting convention, not the repository.

Three concrete gaps follow from this:

1. **No distinction between "clean" and "clean by construction."** A
   `fast_green: "4390/4390"` field looks identical whether the repo
   truly has zero failures or whether N known failures were
   `--deselect`-ed before the count was taken. The gate cannot tell
   these apart because it never sees the deselected set.
2. **No first-class category for expected phase artifacts.** A test
   that necessarily fails *because* the phase did its job correctly
   (e.g. an "unpushed commits == 0" assertion during a phase that
   intentionally produces unpushed commits pending review) has no
   representation other than being silently folded into the same
   deselection an author would use for a real pre-existing failure.
3. **No first-class category for environment flakes.** A
   non-reproducing subprocess timeout and a genuine regression both
   currently require the same manual deselection-and-prose workaround,
   so the report format cannot itself distinguish "I re-ran this in
   isolation and it passed" from "I am asserting this without
   rechecking."

None of this means the current gate should be loosened. Its core
property — a report cannot narrate its way past a real, unattributed
failure — must be preserved exactly. The goal is to give the gate more
categories to reason with, not fewer constraints.

## Section 2 — Design goal

Replace the single free-text `fast_green` scalar's implicit
responsibilities with an explicit **attribution record** that the gate
validates structurally, while preserving every invariant the current
regex/mapping-based `_fast_green_failure_signal()` already enforces
(fail-closed on ambiguity, no narration-only override, type-aware
parsing). The certified claim moves from:

> "the entire repository has zero historical failures"

to:

> "this change introduced zero attributable regressions, and every
> excluded failure is independently classified and evidenced — not
> merely asserted."

This is a stricter claim in one sense (classification itself must now
be evidenced, not just the base pass/fail count) and a more accurate
one in the sense that matters for a long-lived repository: it lets
`fast_green.failed == 0` retire as a proxy for "safe to certify" in
favor of a claim that is actually true of what the phase did.

## Section 3 — Evidence model

An attribution-aware verification result is a structured record with
five buckets, each an explicit list of test node IDs (never a bare
count), plus the method used to produce the record:

| Field | Meaning |
|---|---|
| `raw_failures` | Every failing node ID from an unfiltered run against HEAD. Ground truth; never edited by hand. |
| `attributable_failures` | Subset of `raw_failures` that the baseline-vs-HEAD comparison shows as *newly* failing (absent from the baseline's own failing set). This is the only bucket that blocks completion. |
| `excluded_preexisting_failures` | Subset of `raw_failures` present in the baseline's failing set at the same node ID — i.e., failing before this phase's commits existed, unchanged by them. |
| `excluded_environment_failures` | Subset of `raw_failures` for which an isolated rerun (same commit, same node ID, no other change) diverged from the batch-run result — i.e., a flake, not a deterministic failure. Requires the rerun's own result to be attached as evidence (see Section 4). |
| `expected_phase_artifacts` | Subset of `raw_failures` where the phase's own recommended-next-phase/summary text, or a structural property of the diff (e.g. a test literally named to assert `pushed_status == pushed` during a phase whose deliverable is intentionally unpushed pending review), predicts the failure as a direct, correct consequence of the phase's own governed output. This bucket requires the strictest evidence: a named test-to-cause mapping, not a bucket of convenience. |

Invariant: `raw_failures` is always exactly the disjoint union of the
other four buckets. A node ID present in `raw_failures` but absent
from all four exclusion/attribution buckets is itself a gate failure
("unclassified failure") — this is the structural replacement for
today's "malformed" fail-closed branch, and it closes the gap the
current deselection workaround leaves open (a deselected node simply
never appears anywhere in today's structured field at all; under this
model it must appear, classified, or the report is invalid).

## Section 4 — Classification rules (method, not narration)

Each bucket assignment must be backed by a specific, checkable
method — this is the direct fix for 134E.9.1 ("narration is not itself
verified evidence"), generalized to more buckets instead of collapsed
back into one:

- **`attributable_failures`**: derived automatically from the
  baseline-vs-HEAD node-ID set difference. No human/agent judgment
  call is permitted here — it is set arithmetic over two independently
  captured node-ID lists (baseline run, HEAD run), exactly the method
  Phase 149O.20L.7O.2P already used ad hoc (isolated worktree, no
  `--deselect`, exact node-ID diff). This phase's contribution is to
  make that method the schema-required source of this bucket, not an
  optional verification style.
- **`excluded_preexisting_failures`**: automatic — any node in
  `raw_failures ∩ baseline_failures` at the same node ID. Requires the
  baseline commit hash and its own independently captured failing-node
  list to be attached as evidence (not just asserted); the baseline
  must be an ancestor of HEAD reachable without the phase's own
  commits, so a baseline cannot be cherry-picked to manufacture cover.
- **`excluded_environment_failures`**: requires an isolated rerun of
  the exact same node ID against the exact same commit, recorded with
  its own pass/fail result and a timestamp. A single rerun that still
  fails does *not* qualify for this bucket — it must go to
  `attributable_failures` or stay `raw_failures`/unclassified. This
  prevents "I reran it and it happened to pass this time" from being a
  silent way to launder a real intermittent regression; flake
  classification requires the rerun evidence to be attached to the
  report, inspectable by the same trust-gate machinery that already
  inspects `governance_results`.
- **`expected_phase_artifacts`**: requires a named mapping from test
  node ID to the specific phase-output property that predicts its
  failure (e.g. `"test_head_equals_origin_main" ->
  "phase_commits present and pushed_status != pushed (by design,
  pending push confirmation)"`). This is the narrowest, highest-bar
  bucket, deliberately: it is the one most structurally similar to the
  134E.9.1 failure mode (a plausible-sounding narrative excusing a
  failure), so it gets the least discretion — a generic phrase like
  "expected due to phase state" does not satisfy the mapping
  requirement; the predicted cause must name the specific report field
  or commit property responsible.

## Section 5 — Schema sketch

Extends `PhaseReport.test_results["fast_green"]` from a scalar to a
structured value (backward-compatible: the existing scalar/mapping
forms remain valid and are interpreted as before via
`_fast_green_failure_signal()` for reports that don't opt into
attribution-aware evidence — no forced migration of historical
reports):

```python
test_results["fast_green"] = {
    "raw_failures": ["path::TestX::test_a", "path::TestY::test_b", ...],
    "attributable_failures": [],
    "excluded_preexisting_failures": [
        {"node_id": "...", "baseline_commit": "<hash>", "baseline_evidence": "..."},
    ],
    "excluded_environment_failures": [
        {"node_id": "...", "rerun_result": "pass", "rerun_at": "<iso8601>"},
    ],
    "expected_phase_artifacts": [
        {"node_id": "...", "predicted_by": "<report field or commit property>"},
    ],
    "method": "baseline_vs_head_isolated_worktree",
    "baseline_commit": "<hash>",
    "head_commit": "<hash>",
}
```

## Section 6 — Completion criteria (gate behavior)

The gate change this design proposes, to be implemented in a
*separate, later* phase, is:

1. If `test_results["fast_green"]` is the legacy scalar/mapping form,
   behavior is byte-for-byte unchanged — `_fast_green_failure_signal()`
   keeps its current fail-closed semantics forever. This design adds a
   parallel path, not a replacement.
2. If it is the structured attribution form: completion requires (a)
   `attributable_failures` is empty, (b) `raw_failures` is exactly the
   union of the four buckets (no unclassified node), (c) every entry in
   `excluded_preexisting_failures` and `excluded_environment_failures`
   carries its required evidence field, non-empty, and (d) every entry
   in `expected_phase_artifacts` carries a `predicted_by` that
   references an actual field name present elsewhere in the same
   report (checked structurally, the same way `validate_derived_correctness`
   already cross-checks other fields against `report.architecture_status`).
   Any missing evidence field, any unclassified `raw_failures` member,
   or any nonempty `attributable_failures` fails closed exactly like
   today's malformed-value branch — same "no escape hatch" property,
   relocated to more precise checks instead of removed.
3. The `attributable_failures` bucket itself is never permitted to be
   overridden by narration, `no_go_confirmations`, or any other report
   field — preserving the 134E.9.1 invariant exactly.

## Section 7 — Push eligibility rules

`governance_results.pcae_push_check` and `pushed_status` remain gated
exactly as today (`phase_reports.py:361-369`, exact-string equality
against the literal accepted values). This design does not touch push
eligibility directly. The one interaction worth naming: an
`expected_phase_artifacts` entry that predicts a failure *because* of
current unpushed state (as in the 149O.20L.7O.2P case) must not be
usable to also justify skipping the separate, unrelated push-check
gate — the two gates check different claims (test attribution vs.
push cleanliness) and this design keeps them structurally independent,
so a phase cannot use one to launder the other.

## Section 8 — Non-goals / explicitly out of scope for this phase

- No change to `_fast_green_failure_signal()`, `_FAST_GREEN_FAILURE_RE`,
  or any other live parsing/gating code.
- No change to the `fast_green` field's currently accepted value
  shapes for existing/historical reports.
- No retroactive reclassification of Phase 149O.20L.7O.2P's quarantine
  state. It remains staged pending push under the existing gate,
  unaffected by this design.
- No implementation of the baseline-capture tooling this design
  assumes (an automated isolated-worktree baseline-vs-HEAD runner).
  Phase 149O.20L.7O.2P's controlled comparison was performed manually;
  a follow-on implementation phase would need to build this as a real
  `pcae` subcommand rather than a one-off manual procedure, since
  manual procedures are exactly the kind of unverified claim this
  design exists to stop trusting.

## Section 9 — Recommended next phase

**149O.20L.7O.2R — Attribution-Aware Verification Gate Implementation
(structured `fast_green` parser + baseline-capture tooling)**, scoped
to: (1) a `pcae` subcommand that performs the isolated
baseline-vs-HEAD comparison this phase's design assumes, producing the
Section 5 schema as real output rather than a hand-authored one; (2)
the parallel structured-form validation path described in Section 6,
additive to (never replacing) the existing scalar-form gate. Should
remain a contained implementation phase — no gate loosening, no change
to legacy-form behavior, before an independent verification pass
confirms the new path cannot be used to pass a report that the
existing scalar-form gate would reject.
