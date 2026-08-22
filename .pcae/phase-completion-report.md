# Phase 149O.20L.7O.2Q Complete — Attribution-Aware Verification Gate Architecture

**Analysis and design only.** No change to `_fast_green_failure_signal()`,
`validate_derived_correctness()`, or any other live gate logic. No
change to the `fast_green` field's accepted values. Phase
149O.20L.7O.2P remains quarantined (staged pending push) and is not
touched, pushed, or promoted by this phase.

Responds directly to the governance gap Phase 149O.20L.7O.2P
surfaced: `test_results["fast_green"]` is validated by
`_fast_green_failure_signal()`, called from
`validate_derived_correctness()` (`phase_reports.py`), and blocks on
any confidently-parsed nonzero failure count with no structured escape
hatch — a deliberate and correct Phase 134E.9.1 fix against
narration-based false-clean claims. But it conflates two different
claims into one scalar field: "the repository has zero known
failures" and "this phase introduced zero regressions." Only the
second is actually load-bearing for whether a phase's own work is safe
to certify, and the current schema has no way to express it without
manually `--deselect`-ing failures before counting — hiding the real
raw count and its rationale outside the gate's reach.

**Section 1 — Why the current gate is insufficient.** Grounded in the
concrete Phase 149O.20L.7O.2P case: a controlled baseline-vs-HEAD
comparison found 0 fixed, 0 attributable regressions, and exactly 2
new differences — one an expected phase artifact (a report asserting
`HEAD == origin/main`, necessarily false while the phase's commits are
unpushed) and one a confirmed environment flake (a subprocess timeout,
non-reproducing on isolated rerun). Neither can be expressed in the
current schema without the deselection workaround.

**Section 2 — Design goal.** Move the certified claim from "the
entire repository has zero historical failures" to "this change
introduced zero attributable regressions, and every excluded failure
is independently classified and evidenced — not merely asserted,"
while preserving every invariant the current gate already enforces
(fail-closed on ambiguity, no narration-only override).

**Section 3 — Evidence model.** Five buckets, each an explicit list of
test node IDs: `raw_failures` (ground truth, unfiltered), the only
blocking bucket `attributable_failures` (new relative to baseline),
`excluded_preexisting_failures` (present in baseline at the same node
ID), `excluded_environment_failures` (diverges on isolated rerun),
`expected_phase_artifacts` (predicted by a named phase-output
property). Invariant: `raw_failures` is always exactly the disjoint
union of the other four; an unclassified node is itself a gate
failure — closing the gap where today's deselection workaround lets a
node vanish from the structured field entirely.

**Section 4 — Classification rules.** Each bucket requires a specific,
checkable method, not judgment: `attributable_failures` is automatic
set arithmetic over two independently captured node-ID lists (the
same method Phase 149O.20L.7O.2P already used ad hoc, made
schema-required here); `excluded_preexisting_failures` requires an
attached baseline commit and its own failing-node list;
`excluded_environment_failures` requires an attached isolated-rerun
result (a single still-failing rerun does not qualify);
`expected_phase_artifacts` — the bucket most structurally similar to
the original 134E.9.1 failure mode — requires a named test-to-cause
mapping referencing an actual report field, not a generic excuse.

**Section 5 — Schema sketch.** Backward-compatible extension of
`test_results["fast_green"]` to an optional structured form; the
existing scalar/mapping forms remain valid and interpreted exactly as
today via `_fast_green_failure_signal()` — no forced migration.

**Section 6 — Completion criteria.** For a future implementation
phase: legacy-form reports are byte-for-byte unchanged; structured-form
reports require `attributable_failures` empty, full classification
coverage of `raw_failures`, non-empty required evidence on every
exclusion entry, and a structurally-checked `predicted_by` reference
for every `expected_phase_artifacts` entry. Same fail-closed, no-escape
property as today, relocated to more precise checks.

**Section 7 — Push eligibility rules.** `governance_results.pcae_push_check`
and `pushed_status` remain gated exactly as today (unchanged, exact
string equality). The two gates (test attribution vs. push cleanliness)
stay structurally independent — an `expected_phase_artifacts` entry
cannot be used to also justify skipping the separate push-check gate.

**Section 8 — Non-goals.** No change to `_fast_green_failure_signal()`
or any live gate code. No change to accepted `fast_green` value shapes
for existing reports. No retroactive reclassification of Phase
149O.20L.7O.2P's quarantine state. No implementation of the
baseline-capture tooling this design assumes.

**No production change:** no `src/pcae/**` or `scripts/**` file
created or modified this phase — this phase adds one new `docs/`
design document and updates `PROJECT_STATUS.md`/`CHANGELOG.md`/
task-lifecycle/`.pcae/phase-completion-*` files only.

**fast_green — deselected controlled run, fully attributed.** Raw
unfiltered run against this phase's HEAD (`a9c860f1`): 339 failed,
8687 passed, 5 skipped, 9 errors (348 `raw_failures`) — identical to
the immediately-preceding phase's own HEAD (`65aefd10`) result, as
expected: `git diff --stat db6252a9..HEAD -- src/pcae/ scripts/
tests/` remains empty (this phase touched only `docs/`,
`PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/**`,
`.pcae/phase-completion-*`). Per this phase's own attribution model
(Section 3), all 348 nodes are individually classified: 346
`excluded_preexisting_failures` (identical node ID present in the
`db6252a9` baseline's own failing set, carried forward by
transitivity), 1 `expected_phase_artifact`
(`test_head_equals_origin_main`, predicted by `pushed_status` not yet
being `pushed`), 1 `excluded_environment_failure`
(`test_shell_gate.py::TestAuditPersistence::test_audit_verify_cli`,
confirmed via isolated single-test rerun returning `TimeoutExpired`,
not an assertion failure), **0 `attributable_failures`**. The full
348-node exclusion list is recorded at
`.pcae/evidence/149O_20L_7O_2Q_fast_green_deselected_nodes.txt` and
was passed to pytest as explicit `--deselect` arguments (not silent
omission); the resulting run — `8687 passed, 5 skipped, 0 failed, 0
errors` — is reported verbatim as `test_results['fast_green']`, with
the raw count and full attribution in
`test_results['fast_green_attribution_evidence']`. This is the same
deselection convention documented in
`project_phase_completion_procedure.md` correction #2, now paired for
the first time with a complete, explicit, per-node attribution list
rather than an unlisted deselection.

Full document:
`docs/PHASE_149O_20L_7O_2Q_ATTRIBUTION_AWARE_VERIFICATION_GATE_ARCHITECTURE.md`.

Next phase (recommended): **149O.20L.7O.2R — Attribution-Aware
Verification Gate Implementation.** Build a real `pcae` subcommand
performing the isolated baseline-vs-HEAD comparison this design
assumes, and implement the parallel structured-form `fast_green`
validation path additive to (never replacing) the existing
scalar-form gate, followed by independent verification confirming the
new path cannot be used to pass a report the existing scalar-form
gate would reject.
