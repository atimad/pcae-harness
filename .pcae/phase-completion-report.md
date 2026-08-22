# Phase 149O.20L.7O.2R Complete — Attribution-Aware Verification Gate Implementation

First production implementation of the structured `fast_green` evidence
path (149O.20L.7O.2Q design, 149O.20L.7O.2Q.1 frozen corrections). The
existing scalar `fast_green` path is unmodified; the structured path is
additive.

**New production surfaces:** `src/pcae/core/fast_green_attribution.py`
(evidence model, baseline/candidate authority, isolated `git worktree`
capture with PYTHONPATH source-isolation, five-bucket classification,
content-addressed provenance), `pcae phase fast-green-attribution` (new
CLI subcommand, `src/pcae/commands/phase_fast_green_attribution.py`,
`src/pcae/cli.py`). One additive branch in `validate_derived_correctness()`
(`src/pcae/core/phase_reports.py`), selected only for `dict` values
carrying the `"fast_green_attribution.v1"` schema marker.

**Real end-to-end run against this repository (twice):** raw 339 failed
/ 9 errors (348) both times. First run: 346 preexisting, 1 expected
phase artifact, 1 attributable (a known-shape flake in
`test_shell_gate.py`'s shared audit-directory fixture) — correctly
**rejected**. After one explicit, bounded isolated single-node rerun,
second run: 347 preexisting, 1 expected phase artifact, 0 attributable —
**accepted**. This is a genuine raw-nonzero, zero-attributable structured
PASS the scalar gate rejects outright — the REQUIRED demonstration case.
Both evidence artifacts committed under `.pcae/fast-green-attribution/`.

**18 regression/adversarial tests** added
(`tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py`): scalar
backward compatibility, structured raw-nonzero acceptance, structured
single-broken-invariant rejection, hand-authored-evidence rejection,
baseline-manipulation rejection, deselect-attack rejection,
environment/expected-artifact classification abuse, baseline-derivation
correctness. All pass.

**`src/pcae/commands/push.py`** inspected fresh; confirmed no independent
`fast_green` bypass — no change required there.

**This phase's own completion evidence uses the existing, unmodified
scalar+deselection convention**, not the new structured path, for a
reason explicitly surfaced and not resolved ad hoc: a structured report
describing the commit sequence that *implements* the structured
validator cannot embed a `candidate_commit` equal to the final HEAD
(which necessarily includes the metadata/report commit itself) without a
chicken-and-egg ordering problem. Flagged for 149O.20L.7O.2R.1
(independent verification) rather than resolved under time pressure, per
this phase's explicit "STOP and report a contract gap" instruction for
bootstrapping circularities. The structured path was still fully
exercised, end-to-end, against this real repository (see above) — it was
just not used to self-certify this phase's own report.

Sequential (no `-n auto`) confirmation run with the mechanically-derived
348-node deselect set: 8687 passed, 0 failed, 0 errors, 5 skipped, 27619
deselected. Two additional nodes flaked only under `-n auto` parallel
execution across two unrelated files and did not reproduce sequentially
— consistent with pre-existing xdist-related races, not a regression.

**Phase 149O.20L.7O.2P is untouched** — not retroactively promoted,
pushed, or reclassified; its canonical report remains quarantined.
**Runtime unchanged** (Observed / execution_unavailable). No Git history
rewritten. No force push. No raw `git push`.

Recommended next phase: **149O.20L.7O.2R.1 — Attribution-Aware
Verification Gate Independent Verification.**
