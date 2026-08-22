# Phase 149O.20L.7O.2R — Attribution-Aware Verification Gate Implementation

Implements the structured `fast_green` evidence path designed by
149O.20L.7O.2Q (`docs/PHASE_149O_20L_7O_2Q_ATTRIBUTION_AWARE_VERIFICATION_
GATE_ARCHITECTURE.md`) and frozen/corrected by 149O.20L.7O.2Q.1
(`docs/PHASE_149O_20L_7O_2Q_1_QUARANTINED_ANCESTOR_PUSH_STATE_AND_
ATTRIBUTION_GATE_CONTRACT_RECONCILIATION.md`). Additive only: the existing
scalar `fast_green` path (`_fast_green_failure_signal()`,
`validate_derived_correctness()`) is byte-for-byte unchanged for any
`test_results["fast_green"]` value that is not a dict carrying the new
schema marker.

## Production surfaces changed

- `src/pcae/core/fast_green_attribution.py` (new) — evidence model,
  isolated-worktree baseline/candidate capture, classification, and the
  structured validator (`validate_structured_fast_green`).
- `src/pcae/core/phase_reports.py` — `validate_derived_correctness()`
  gains one new branch: when `test_results["fast_green"]` is a dict with
  `schema_version == "fast_green_attribution.v1"`, delegate to the
  structured validator instead of `_fast_green_failure_signal()`. Any
  other value (including today's scalar dict/string/int forms) takes the
  exact same path as before this phase.
- `src/pcae/commands/phase_fast_green_attribution.py` (new) — CLI handler
  for `pcae phase fast-green-attribution`.
- `src/pcae/cli.py` — registers the new subcommand under the existing
  `phase` command family (matches the repo's `phase <verb>` convention;
  no new naming style introduced).

## Command surface

```
pcae phase fast-green-attribution --phase-id <ID> [--pushed-status <status>]
    [--rerun-node <node_id> ...] [--timeout <seconds>] [--json]
```

Performs one controlled comparison: derives the authoritative baseline,
runs the governed Fast Green selection against baseline and candidate in
two isolated `git worktree` checkouts, classifies every raw failure/error
node into exactly one of the four buckets, persists the evidence as a
content-addressed artifact under `.pcae/fast-green-attribution/<digest>.json`,
and prints/returns the structured value meant to be embedded verbatim as
`test_results["fast_green"]`.

## Baseline / candidate authority

- **Baseline**: `derive_phase_entry_baseline(repo_root, phase_id)` — the
  parent of the oldest commit on `HEAD`'s ancestry whose subject line is
  `"Phase <phase_id>: ..."` (same `^Phase\s+(\S+?)\s*[:—–-]` extraction
  convention already used in `agent.py` for handoff parsing). Never a
  caller-supplied argument in the authoritative path — there is no
  `--baseline` flag. If no commit is yet attributed to the phase, baseline
  collapses to HEAD (documented, degenerate case).
- **Candidate**: exact current `git rev-parse HEAD`, re-checked for
  movement immediately after both the baseline and candidate captures —
  if HEAD moved mid-capture, the command fails with `AttributionError`
  rather than emitting evidence for a commit that is no longer HEAD.

## Source isolation

Both baseline and candidate runs execute inside a disposable
`git worktree add --detach <tmp> <sha>` checkout (same pattern as the
existing `_esb_create_sandbox()` in `src/pcae/core/agent.py`), with
`PYTHONPATH` explicitly prepended with that worktree's own `src/`
directory ahead of any ambient editable-install path. This is the direct
regression fix for the cross-tree contamination discovered in Phase 2P
(baseline tests silently importing the current-HEAD `pcae` package via
the ambient editable install rather than the baseline's own source).
`tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py`'s
`_make_repo_with_baseline_and_candidate()` fixture exercises this in
miniature (two commits with genuinely different `tests/test_sample.py`
content) and the resulting evidence correctly reflects the *baseline's*
test content when computing `excluded_preexisting_failures`, not the
candidate's.

## Test-result collection

A small, dependency-free pytest plugin (materialized to a temp file per
run, `_COLLECTOR_PLUGIN_SOURCE` in `fast_green_attribution.py`) hooks
`pytest_runtest_logreport`/`pytest_collectreport`/`pytest_sessionfinish`
to record exact `failed`/`errors` node-ID lists (not just counts) to a
JSON file named via `PCAE_FG_OUTPUT`. Both runs invoke the identical
command: `<python> -m pytest -m fast_green -q --no-header -p
pcae_fg_collector_plugin` — no `-n auto`, deliberately: this trades wall
time for hook-firing correctness (xdist's controller-side aggregation of
`pytest_collectreport` was not independently verified for this phase's
timeline, and 2Q.1 §17 requires exact command-equivalence, not
equivalence to the human-invoked default specifically). Both sides always
use the exact same `FAST_GREEN_PYTEST_ARGS` constant; the validator
independently checks the persisted `command` field matches this exactly,
which is what closes the deselection-attack case (§ below).

## Five-bucket classification

- `attributable_failures` and `excluded_preexisting_failures` are **never
  trusted from the evidence artifact's own labels** during validation —
  `validate_structured_fast_green()` recomputes both directly from
  `raw_failed ∪ raw_errors` (candidate) and `baseline_raw_failed ∪
  baseline_raw_errors` (baseline), both of which are persisted in the
  same artifact. `preexisting = raw ∩ baseline`; `attributable = raw −
  preexisting − environment − expected`. This is stronger than the 2Q
  design's minimum bar (which required the *bucket entries* to carry
  evidence) — here the classification itself is mechanically
  irreproducible-to-forge without also forging the raw sets it's derived
  from.
- `excluded_environment_failures`: only ever populated by an explicit,
  caller-requested (`--rerun-node`), bounded (`ENVIRONMENT_EXCLUSION_BOUND
  = 3`) isolated single-node rerun against the exact candidate commit. A
  rerun that fails identically is discarded, not classified (2Q.1 §12).
  2Q.1 left the exact bound unfrozen ("some bounded, evidence-backed
  policy is required... not open-ended agent discretion") — `3` is this
  phase's own documented choice, revisitable by a future governed phase.
- `expected_phase_artifacts`: closed to exactly one case (2Q.1 §13, §20)
  — a node whose test *function name* is literally
  `test_head_equals_origin_main`, classified only when the report's own
  `pushed_status` is not one of the three "already pushed" literals
  (`pushed`/`clean`/`nothing_to_push`), with `predicted_by` structurally
  tied to `pushed_status` and `predicted_value` required to equal the
  report's actual value. No other `predicted_by` value is recognized —
  attempting one is rejected, not silently ignored.

## Provenance / machine-production

`persist_evidence()` writes the full evidence dict to
`.pcae/fast-green-attribution/<sha256-of-canonical-json>.json` and embeds
`{"artifact_path", "artifact_digest"}` in the value that goes into
`test_results["fast_green"]`. Validation recomputes the digest from the
artifact file's actual on-disk content (source of truth) and additionally
requires every inline field to equal the persisted artifact
byte-for-byte — a value with no matching artifact, or a mismatched
digest, or an inline/artifact divergence, is rejected outright. This is
explicitly **procedural provenance, not cryptographic tamper-evidence**
(no signing key) — documented as such in the module docstring and in
Finding/HMIC-consequence notes below; it closes "hand-typed attribution
counts in metadata" (134E.9.1's failure shape) but not a determined
actor with direct filesystem write access to `.pcae/`, which is true of
every other trust field in this repository's governance model already.

## Freshness / staleness

`candidate_commit` in the persisted artifact must equal `git rev-parse
HEAD` at validation time; any later commit (including a metadata-only
commit) invalidates prior evidence, forcing regeneration — proven by
`TestStructuredRejection::test_stale_candidate_rejected`.

## Count / set conservation

`validate_structured_fast_green()` enforces, independently of the
artifact's own claims:
- No duplicate node IDs within `raw_failed`/`raw_errors` or within any
  bucket.
- No node ID classified into more than one bucket.
- No classified node ID absent from `raw_failed ∪ raw_errors`.
- `attributable_failures` (computed) is empty for PASS.

## Backward compatibility

`validate_derived_correctness()` only enters the structured path when
`test_results["fast_green"]` is a `dict` with
`schema_version == "fast_green_attribution.v1"`. Every existing scalar
shape (`str`, `int`, `bool`, or a `dict` without that marker, including
the `{"passed": N, "failed": 0}` mapping form) is routed to
`_fast_green_failure_signal()` exactly as before — unmodified function,
unmodified call site for that branch.
`tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py::
TestScalarBackwardCompatibility` proves this for clean-pass, failing, and
mapping-form scalar values.

## Push eligibility integration

`src/pcae/commands/push.py` was inspected fresh this phase and confirmed
(as 2Q.1 §22 also found) to have no independent `fast_green`
parsing/bypass — push eligibility flows exclusively through canonical
report promotion, which already calls `validate_derived_correctness()`.
No change was required in `push.py` to wire the structured path into push
eligibility; a second bypass would have been a defect, and none exists.

## Quarantined-ancestor / 2P disposition

This phase does not touch, promote, retroactively evaluate, or reclassify
Phase 149O.20L.7O.2P. Its canonical report remains quarantined. A future
phase *may* re-run 2P's original manual comparison through
`pcae phase fast-green-attribution` and, if it independently passes,
promote a **new** canonical report for that re-evaluation — not attempted
here, per 2Q.1 §24's explicit "requires its own governed ceremony"
instruction.

## Recommended next phase

**149O.20L.7O.2R.1 — Attribution-Aware Verification Gate Independent
Verification**, to independently reconstruct and attack this gate before
any reconciliation of 2P is considered.
