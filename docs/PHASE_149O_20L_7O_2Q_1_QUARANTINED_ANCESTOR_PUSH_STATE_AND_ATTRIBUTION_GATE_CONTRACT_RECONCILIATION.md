# Phase 149O.20L.7O.2Q.1 — Quarantined Ancestor Push-State and Attribution-Gate Contract Reconciliation

**Reconciliation and design only.** No `src/pcae/**` or `scripts/**`
file created or modified. No gate code changed. Phase 149O.20L.7O.2P
is not retroactively promoted, pushed, or reclassified as complete. No
Git history rewritten, no force push, no raw `git push`. This phase
corrects documentation prose and freezes terminology/acceptance rules
for the next implementation phase (2R).

## 0. Summary of findings

Two real defects existed, both confirmed against live Git evidence and
`.pcae` state read fresh this phase, not against prior report prose:

1. **PROJECT_STATUS.md/CHANGELOG.md carried a now-false claim** — "Not
   pushed" for Phase 149O.20L.7O.2P — because the Git evidence at
   phase entry shows 2P's own nine commits are ancestors of
   `origin/main` (pulled in as ancestors of 2Q's later governed push,
   since 2Q built directly on top of 2P's already-committed local
   history). The commits are transported; 2P's canonical report and
   phase-trust state are not. This phase corrects the prose to state
   both facts without conflating them.
2. **2Q's canonical `recommended_next_phase` field misstates the
   verification invariant** for the structured `fast_green` path,
   saying it must confirm the new path "cannot be used to pass a
   report the existing scalar-form gate would reject" — literally
   false, since passing exactly such reports (raw-nonzero,
   zero-attributable) is the entire purpose of the structured path.
   Section 27 below freezes the corrected invariant.

Neither defect involved any bypass, any gate-code change, or any raw
`git push`. Both are documentation/metadata accuracy defects in the
completed 2P/2Q reports, being repaired here before 2R implementation
begins on a document that would otherwise hand it an incorrect
acceptance criterion.

## 1. Re-derived current Git state

Read fresh this phase via `git rev-parse` / `git merge-base` / `git
log`, not from prior report prose:

- **Phase-entry HEAD** (before this phase's own commits):
  `fff331aa` (`Phase 149O.20L.7O.2Q: set pushed_status/pcae_push_check
  to exact post-push literal values`).
- **`origin/main`** (after `git fetch origin`): `fff331aa` — identical
  to phase-entry HEAD.
- **merge-base(HEAD, origin/main):** `fff331aa` — HEAD and
  `origin/main` are the same commit; `git log origin/main..HEAD` and
  `git log HEAD..origin/main` are both empty.
- **Every one of 2P's nine commits** (`deeca31c`, `2cfed3ef`,
  `beb925b2`, `66c89b00`, `65aefd10`, `e4cb3b03`, `a0df808e`,
  `e3548d72`, and the shared boundary commit `a9c860f1`) is confirmed
  `origin-reachable` via `git merge-base --is-ancestor <sha>
  origin/main` (exit 0 for each).
- **Every one of 2Q's ten commits** (`9538237b`, `cb0df7eb`,
  `08281645`, `a9c860f1`, `52db5468`, `eca5a152`, `56d8030e`,
  `ee1174bc`, `c42f0ef8`, `fff331aa`) is likewise confirmed
  `origin-reachable`.
- (`a9c860f1` — "remove stale post-2P active task placeholder" — is
  the shared boundary commit: the last commit made while 2P's task was
  still open, before 2Q's own dedicated task existed, so it correctly
  appears in both phases' local commit ranges without being double
  counted as belonging to two governed phases.)

Confirmed at phase entry: 2P's commits are not merely locally
committed — they are on `origin/main`, and so is all of 2Q.

## 2. Re-derived 2P canonical state

Read fresh from `.pcae/phase-reports/quarantine/` and
`.pcae/phase-completion-metadata.json` history, not from prior report
prose:

- **`.pcae/phase-reports/quarantine/`** contains three `.blocked.md`/
  `.blocked.json` pairs for Phase 149O.20L.7O.2P
  (`20260822-080431-874278-149O.20L.7O.2P-ef8d74e36d37.blocked.*`,
  `...-091658-774148-...-1049094e1892.blocked.*`,
  `...-094926-890398-...-004c451540a8.blocked.*`) — the harness's own
  `write_quarantined_report()` output (`src/pcae/core/phase_reports.py`),
  confirming 2P's canonical report never reached promoted/non-quarantined
  status through the normal `pcae phase complete` path.
- The most recent quarantine artifact's own recorded blocker is exact:
  `Missing trust fields: pushed_status, origin_main_head,
  governance_results.pcae_push_check` plus a `derived_correctness`
  failure — `test_results['fast_green'] reports 346 failure(s) ...
  a failing fast_green result cannot be certified complete`. This is
  the harness's own gate output, not a narrative reconstruction.
- `git log -- .pcae/phase-completion-metadata.json` shows 2P's commits
  (`66c89b00`, `65aefd10`, `e4cb3b03`, `e3548d72`) syncing the
  canonical metadata file locally, but no corresponding non-quarantined
  promotion event for 2P exists anywhere in the repository — the
  canonical `.pcae/phase-completion-metadata.json`/`report.md` pair
  was overwritten by 2Q's own `phase_id: "149O.20L.7O.2Q"` sync
  (`52db5468`) before 2P was ever promoted, so no promoted-2P canonical
  state exists to inspect at all; only the quarantine artifacts do.
- **PROJECT_STATUS.md/CHANGELOG.md prose** (as entering this phase)
  says of 2P: "**Not pushed.** `pcae`'s finalization gate requires a
  literal zero raw `fast_green` count ... The phase is completed
  locally (`--allow-partial-report`, task lifecycle closed) but left
  unpushed." — true when written (2P's commits were then only
  `local_only`), but stale now that a later governed push transported
  them to `origin/main`.

**Exact distinction, in PCAE's own terminology:**

| Layer | State |
|---|---|
| Commit reachability (`git merge-base --is-ancestor`) | `origin_reachable` (transported as ancestors of 2Q's push) |
| Canonical report promotion (`write_quarantined_report` / non-quarantined promotion) | `quarantined` — never promoted |
| Phase trust state (`pcae phase complete` outcome) | 2P never reached `status: completed` in a *promoted, non-quarantined* canonical report; it exists only in `--allow-partial-report` local task-closure form plus three `blocked` quarantine artifacts |
| Push ceremony (`pcae push` run naming 2P as the phase being pushed) | Never attempted to completion — no `pcae push` was ever run while 2P was the active/reported phase; 2P's task was closed and 2Q's task opened before any push occurred |

These four are independent facts. Git transported the *commits*
(a repository-reachability fact) as a side effect of pushing 2Q, which
was built directly on top of 2P's already-committed local history —
this did not touch, promote, or evaluate 2P's *canonical report* or
*phase trust* at all, and no `pcae push` command was ever invoked
naming 2P as its subject.

## 3. Corrected 2Q push-state prose

`PROJECT_STATUS.md` and `CHANGELOG.md` are corrected in this phase's
commits (not rewritten in `git log` — new commits, prior history
untouched) to replace the now-stale "Not pushed" sentence for 2P with
language distinguishing all four facts in §2, using the vocabulary
frozen in §4. 2Q's own entry already correctly said "pushed / origin
parity confirmed" (`pushed_status: "nothing_to_push"`,
`governance_results.pcae_push_check: "nothing_to_push"`, and this
phase's own §1 confirms `HEAD == origin/main`) and required no
correction — 2Q's own push ceremony did succeed, and 2Q's report never
claimed otherwise. Only the 2P paragraph was stale.

**This phase does not claim 2P completed its own push gate.** 2P's
canonical report is still quarantined; only commit reachability
changed, as a side effect of a later phase's own successful push.

## 4. Push-state vocabulary (frozen, documentation-only this phase)

No schema/code change is made. The following terms are frozen for use
in phase documentation and for 2R's implementation to adopt as field
names/enum values:

- **`commit_reachability`**: `local_only` | `origin_reachable` —
  whether a phase's commits are present in `origin/main`'s ancestry,
  as of a stated Git ref pair, independent of any canonical-report
  state.
- **`phase_push_ceremony`**: `not_attempted` | `blocked` | `succeeded`
  — whether `pcae push` was run naming this phase as its subject and
  what it returned. `blocked` covers a `pcae push`/`pcae phase
  complete` invocation that was attempted and refused by a gate
  (e.g. a quarantined canonical report); `not_attempted` covers a
  phase whose task was closed without any `pcae push` invocation at
  all (2P's actual case — its task was closed via
  `--allow-partial-report` and the next phase's task opened without
  ever invoking `pcae push` for 2P specifically).
- **`canonical_report_state`**: `quarantined` | `promoted` — whether
  the phase's canonical report reached non-quarantined promotion via
  `pcae phase complete` (`write_quarantined_report()` not invoked, or
  its `promotion_status` recorded `"promoted"`).

These three axes are independent and must be recorded independently;
none may be inferred from another. 2P's actual state under this
vocabulary: `commit_reachability: origin_reachable`,
`phase_push_ceremony: not_attempted`, `canonical_report_state:
quarantined`.

## 5. Structured `fast_green` purpose (re-stated)

- **Scalar path** (existing, unchanged): `fast_green` is a literal
  clean result — a real or effectively-zero raw failure count,
  verified by `_fast_green_failure_signal()`
  (`src/pcae/core/phase_reports.py`). Unchanged by this phase or 2Q.
- **Structured path** (2Q design, not yet implemented): the raw suite
  run may be nonzero, but a machine-produced, evidence-backed
  comparison against a fixed baseline establishes whether *this
  phase's own changes* introduced any new (attributable) failure.
  This is not a weaker "ignore failures and pass anyway" path — it is
  a *different, stricter-in-a-different-dimension* claim: instead of
  certifying "the repository has zero known failures" (a fact often
  false for reasons unrelated to the current phase), it certifies
  "this phase introduced zero attributable regressions, and every
  excluded raw failure carries machine-checkable evidence for its
  exclusion." A structured report with unclassified or unevidenced
  exclusions must fail exactly as a scalar nonzero count does today.

## 6. Five-bucket model — re-verified

`raw_failures`, `attributable_failures`,
`excluded_preexisting_failures`, `excluded_environment_failures`,
`expected_phase_artifacts`, as designed in 2Q
(`docs/PHASE_149O_20L_7O_2Q_ATTRIBUTION_AWARE_VERIFICATION_GATE_ARCHITECTURE.md`,
Section 3). Re-verified this phase: the four non-`raw_failures`
buckets are intended as **mutually exclusive and collectively
exhaustive (MECE)** over the members of `raw_failures`. The 2Q design
did not previously state this as an explicit closed invariant with a
named conservation rule and residual-forbidding clause; this phase
freezes it as one (§7) and states the classification order needed to
keep the buckets exclusive (§14: `attributable_failures` is the
fail-closed default — a node is only ever placed in one of the other
three buckets if it *positively* meets that bucket's specific evidence
rule; otherwise it remains `attributable_failures`, which guarantees
no node can silently qualify for two exclusion buckets at once, since
a node is tested against the exclusion rules and only removed from the
attributable set on a positive match).

## 7. Raw count conservation invariant (frozen)

For **failure and error nodes counted together** as `raw_failures`
(see §19 for the failed-vs-error schema question):

```
raw_failures
  = attributable_failures
  + excluded_preexisting_failures
  + excluded_environment_failures
  + expected_phase_artifacts
```

as a **disjoint union** (no node ID appears in more than one bucket;
every `raw_failures` node ID appears in exactly one of the four).
Implementation (2R) must reject a structured report where this
equation does not hold exactly, or where any node ID appears in more
than one bucket. No unclassified residual is permitted — an
unclassified node is itself a gate failure, identical in effect to a
scalar nonzero count today.

## 8. Machine-produced evidence (frozen requirement)

Structured evidence is invalid if it is hand-authored counts in phase
metadata prose, however precise-looking. It must be reproducible from:

- a fixed baseline commit SHA (§9);
- a fixed candidate commit SHA (§10);
- a clean isolated worktree/environment (not the working tree with
  uncommitted phase changes present) for the baseline run, so the
  baseline result cannot be contaminated by in-progress candidate
  changes;
- the exact test command/selection used for both runs (§17);
- the exact node-ID result sets for both runs (not summary counts
  alone);
- a deterministic diff/classification process over those two node-ID
  sets producing the four exclusion/attribution buckets.

2R must persist this evidence as a content-addressable artifact (e.g.
hash of the baseline/candidate node-ID lists and command line) rather
than free text, so that a later `pcae phase-report consistency`-style
check can re-verify the evidence was not edited after capture. This
phase freezes the requirement; it does not implement the artifact
format.

## 9. Baseline authority (frozen rule)

**Baseline = the true phase-entry commit** — the commit that was
`HEAD` immediately before the first commit attributed to the current
phase (i.e. `merge-base` of the phase's own first commit's parent).
This must not be a caller-chosen "convenient" older commit — 2R must
derive it programmatically (e.g. from the phase's task-open event or
its first phase-attributed commit's parent SHA recorded in
provenance), not accept an arbitrary `--baseline` argument without
independently verifying it equals that phase-entry point. A caller
supplying a stale or cherry-picked baseline that predates known-fixed
regressions must be rejected.

## 10. Candidate authority (frozen rule)

**Candidate = the exact commit SHA under evidence capture**, recorded
literally in the evidence artifact. HEAD must not move between
capture and use. If any further commit is made after evidence capture
(including a metadata-only commit), the evidence is stale (§ below)
and must be regenerated against the new candidate SHA before
completion — this mirrors the existing `origin_main_head`/candidate
freshness pattern already enforced elsewhere in the gate.

**Freshness rule:** structured evidence is valid only if its recorded
candidate SHA equals the report's actual candidate SHA at validation
time. Any mismatch invalidates the evidence outright (fail closed, not
a warning).

## 11. Pre-existing classification rule (frozen)

A node may be placed in `excluded_preexisting_failures` **only** if
the identical node ID fails in the controlled baseline run, under an
equivalent test selection/environment to the candidate run (§17-§18).
Inference from comments, phase narration, or historical report prose
alone is explicitly forbidden — this is exactly the failure mode the
134E.9.1 fix targeted and that this bucket must not reopen.

## 12. Environment failure classification rule (frozen)

Requires machine evidence, not a narration label:

- Example categories: timeout, resource exhaustion, external
  dependency unavailability.
- Classification requires an isolated single-node (or minimally
  scoped) rerun whose result **diverges** from the original failing
  result in a way consistent with non-determinism (e.g. the rerun
  passes, or fails with a different, explicitly non-assertion signal
  such as a subprocess timeout) — a rerun that fails identically again
  does **not** qualify and must remain `attributable_failures` (or
  `excluded_preexisting_failures` if it also independently meets §11).
  A single still-failing rerun is explicitly insufficient (per the
  2Q design's own Section 4).
- **Environment failures do not auto-pass a phase on their own
  narrative merit.** 2R must apply a bounded policy — e.g. permit at
  most a fixed, small number of environment-classified nodes per
  structured report, or require the divergent rerun itself to be
  captured as part of the same machine-produced evidence artifact
  (not a separately asserted claim) — rather than an unbounded
  "arbitrary flake" escape hatch. This phase does not freeze the exact
  numeric bound; it freezes that *some* bounded, evidence-backed policy
  is required, not open-ended agent discretion.

## 13. `expected_phase_artifact` classification rule (frozen — narrow)

Defined narrowly: a node may be classified `expected_phase_artifacts`
only if it fails **because of a named, closed lifecycle state**
inherent to the phase-completion ceremony itself, not any semantic
choice made by the phase's implementation. The only concrete example
this and the prior phase (2P/2Q) have actually produced is: a test
asserting `HEAD == origin/main` failing during pre-push verification,
because the candidate's own commits are not yet pushed — a state that
is expected precisely because the report is being produced *before*
`pcae push`, tied to the `phase_push_ceremony` vocabulary in §4. This
bucket must be tied to a **structurally checked** `predicted_by`
reference (a specific report field/lifecycle state, e.g.
`pushed_status != "pushed"`), not a free-text agent-supplied "this is
expected" annotation — matching the 2Q design's own Section 4
requirement verbatim. §20-§21 below give this bucket's primary use
case (the push-ceremony circularity) a full design.

## 14. Attributable failure default (frozen)

Any raw failure/error node not meeting one of the three closed
exclusion rules above (§11-§13) is `attributable_failures` by default.
Fail closed — this is the same posture the scalar gate already has for
any nonzero count, simply narrowed to the subset of failures actually
attributable to the current phase.

## 15. Structured completion rule (frozen, corrected)

The structured path passes only if **all** of the following hold,
each independently checked from machine-produced evidence, not
narration:

1. Evidence artifact is present, well-formed, and internally valid
   (§8).
2. Baseline commit matches the authoritative phase-entry rule (§9).
3. Candidate commit SHA matches the report's actual candidate SHA and
   evidence is fresh (§10).
4. Every `raw_failures` node ID is classified into exactly one of the
   four terminal buckets — no residual, no duplicate membership (§7).
5. `attributable_failures` is empty.
6. Every `excluded_preexisting_failures` entry meets §11.
7. Every `excluded_environment_failures` entry meets §12's bounded
   policy.
8. Every `expected_phase_artifacts` entry meets §13's closed,
   structurally-checked rule.
9. Baseline and candidate runs used equivalent test selection — no
   candidate-only narrowing (§17).
10. Test-inventory drift (added/removed/renamed tests, collection
    errors) between baseline and candidate is accounted for, not
    silently dropped (§18).

`raw_failures == 0` is explicitly **not** required for structured-mode
completion — that would collapse the structured path back into the
scalar path and defeat its purpose.

## 16. Scalar mode preservation (frozen)

The existing scalar `fast_green` form (a literal clean count, or the
existing free-text/mapping forms `_fast_green_failure_signal()`
already parses) remains valid, unchanged, and independently sufficient
for completion, exactly as today. No historical report is required to
be retroactively expressed in structured form. The structured path is
strictly additive.

## 17. Structured mode must not mask test deselection (frozen)

The baseline and candidate runs that produce the machine evidence in
§8 **must use the identical test-selection command** (same paths,
same markers, same `--deselect`/`-k` arguments if any) — 2R must
capture and compare the literal command lines, not just result sets.
Forbidden, explicitly: candidate-only deselection, failure-list-driven
deselection (deselecting exactly the nodes that would otherwise fail),
or any post-hoc shrinking of the candidate suite relative to the
baseline's selection. Any difference in test-selection scope between
the two runs invalidates the evidence (§8) rather than being silently
absorbed into the diff.

If a phase's own scope genuinely requires excluding some tests from
both runs (e.g. a known-broken suite unrelated to fast_green entirely),
that exclusion must be part of the single governed test-selection
definition applied identically to both baseline and candidate — never
applied only to one side.

## 18. Test inventory drift handling (frozen)

Between baseline and candidate, tests may be added, removed, or
renamed. 2R must:

- Treat a node ID present in the candidate result set but absent from
  the baseline result set as **not** eligible for
  `excluded_preexisting_failures` (§11 requires identical node ID
  presence in baseline) — a new failing test on a new/renamed node ID
  must default to `attributable_failures` unless it independently
  meets `expected_phase_artifacts`'/`excluded_environment_failures`'
  narrower rules. Renaming a failing test must not be usable to make
  it "new" and therefore harder, nor to make it disappear as
  "pre-existing under a different name" — node-ID identity is the only
  recognized continuity signal; no fuzzy/semantic matching across
  renames is permitted.
- Treat a **collection error** (a node that fails to even collect,
  rather than execute and fail) as a member of `raw_failures` subject
  to the same classification requirement as any other failure/error —
  it must not be silently excluded from the raw count because it
  never "ran." (See §19.)
- A baseline run that itself fails to collect the full candidate test
  set (e.g. because a test file is new in the candidate) makes that
  new file's tests ineligible for `excluded_preexisting_failures` by
  construction (§11), which is the correct, conservative default.

## 19. Error vs. failure representation (frozen)

2P's own raw evidence already distinguished `failed` (339) from
`errors` (9) as separate pytest outcome categories, both contributing
to a single `raw_failures` total (348) in the 2Q design. This phase
freezes that **both must remain represented, and both must be
individually classifiable** — 2R's schema should carry
`raw_failed`/`raw_errors` as the captured raw evidence (matching
pytest's own vocabulary and preventing accidental double-counting or
loss of collection/setup errors, which pytest reports as `errors` not
`failed`), while the four classification buckets (§6-§7) operate over
the **union** of both as `raw_failures` for the purpose of the
conservation invariant in §7. A collection/setup error must never be
dropped from `raw_failures` merely because it is an `error` rather
than a `failed` assertion outcome.

## 20. Push-ceremony artifact — explicit design

The concrete recurring case (2N.14 through 2Q, per
`project_phase_completion_procedure.md` and this session's own
evidence) is a test asserting `HEAD == origin/main`, which is
necessarily false during pre-push verification, since the phase's own
commits are by definition not yet pushed at that point.

**Adopted model: recognized lifecycle artifact, evaluated relative to
the report's own declared push-ceremony stage.** Concretely:

- While a report is being produced with `pushed_status` in a
  pre-push state (i.e. *not* `"pushed"`/`"clean"`/`"nothing_to_push"`
  — the exact literal values `project_phase_completion_procedure.md`
  already freezes), a `HEAD == origin/main` test failing is a
  **closed, named** `expected_phase_artifacts` case, tied via
  `predicted_by` to that same report's own `pushed_status` field value
  (§13) — not a free-text excuse.
- This artifact classification is **not evaluated after push** and is
  **not simply excluded from pre-push fast_green by blanket contract**
  — both of those alternatives either reopen circularity (see §21) or
  discard a genuine signal (a `HEAD == origin/main` test that fails
  for a reason *other* than the expected pre-push state, e.g. because
  `origin/main` diverged unexpectedly, must not be silently
  swallowed). Tying the exclusion to the report's own declared
  `pushed_status` value keeps the exclusion narrow and falsifiable:
  if `pushed_status` is already `"pushed"`/`"nothing_to_push"` and the
  test still fails, it is **not** an `expected_phase_artifacts` case
  and defaults to `attributable_failures` (§14).

## 21. No circular push gate (frozen analysis)

Dependency graph, as currently implemented (`phase_reports.py`,
`push.py`) and as 2R must preserve:

```
verification (fast_green, derived_correctness)
  → canonical report promotion (pcae phase complete)
    → pcae push (requires a promoted, non-quarantined report)
      → post-push status (pushed_status/pcae_push_check literals)
```

The 2P incident's actual circularity was **not** in this dependency
chain being logically circular — it is a strict one-way chain, and
2P correctly stopped at the first gate it could not pass rather than
forcing itself through. The apparent circularity `project_
phase_completion_procedure.md` documents (steps 8-10: `--stage-
pending-report`, then push, then re-run `phase complete` without that
flag) is a **two-phase promotion protocol**, not a cycle: step 8
produces a report staged as *pending*, not blocked; the push in step 9
operates against that staged report; step 10 *promotes* the already-
staged report to `COMPLETE` using post-push facts. No condition
required *before* step 9's push is only satisfiable *after* it — the
`--stage-pending-report` mechanism exists precisely to break that
would-be cycle, and it worked correctly for 2Q. **§20's
`expected_phase_artifacts` design is what allows a `HEAD ==
origin/main` test to coexist with this two-phase protocol under the
*structured* path** — it is not a new circularity fix; it is
2R's mechanism for the *scalar* gate's binary literal-zero requirement,
which historically forced the deselection workaround (`project_
phase_completion_procedure.md` correction #2) to route around a
condition (`HEAD == origin/main`, false pre-push) that the two-phase
protocol already handles correctly for the push-check fields
specifically. This phase's dependency-graph analysis confirms no
condition-before-push is unsatisfiable-before-push once the
`--stage-pending-report` two-step is used — the residual problem 2Q
addresses is narrower: expressing the *test-level* `HEAD ==
origin/main` failure without a manual `--deselect`, not resolving a
graph-level cycle.

## 22. Quarantined-ancestor policy (frozen recommendation)

**Current actual behavior, confirmed by reading `src/pcae/commands/
push.py` fresh this phase:** the only ancestor-related check in the
push path is a force-push guard (`git merge-base --is-ancestor
origin/main HEAD`, `push.py:815-820`) — there is **no** check anywhere
in the push path for whether the commit range being pushed contains
commits originally attributed to a still-quarantined earlier phase's
canonical report. The current behavior (2P's commits transported
silently as ancestors of 2Q's push) is confirmed **accidental** —
absence of a check, not a designed-and-chosen policy. This phase does
not assume that accidental behavior is correct, per the explicit
instruction, and freezes a recommendation instead of leaving it
implicit.

**Recommended policy: (B) allow commit reachability, but preserve
canonical phase quarantine — paired with (C)'s reporting discipline.**
Reasoning:

- **(A) hard block** is rejected: it would make an earlier phase's
  quarantine (which may be permanently expected, e.g. a phase
  correctly reporting known pre-existing failures without forcing a
  literal-zero via deselection, as 2P did on principle) transitively
  block *all* later development indefinitely, including work entirely
  unrelated to the quarantined phase's own concern. That is a
  disproportionate blast radius for a report-promotion gate.
- **(B) allow transport, preserve quarantine** is correct because Git
  commit history is fundamentally linear/cumulative — a later phase's
  commits necessarily build on an earlier phase's already-committed
  tree state regardless of that earlier phase's own report-promotion
  status, and blocking that would effectively require squashing or
  rewriting history to "hide" the quarantined phase, which §29's
  no-go list already forbids.
- **(C) require an explicit reconciliation ceremony** is not rejected
  but **subsumed**: this very phase (2Q.1) *is* that ceremony for the
  2P case, performed narrowly and after the fact rather than being
  required to block 2Q's own push at the time. The frozen
  recommendation is: **(B) is the default technical behavior (no push
  block), but PCAE must additively report quarantined-ancestor
  presence** — a later phase's push/completion report should
  explicitly surface (not silently omit) any ancestor commit ranges
  whose *originating* phase's canonical report remains quarantined, so
  that omission is a visible fact, not a silent one, going forward.
  This phase does not implement that reporting; it freezes it as a
  requirement for 2R or a dedicated follow-on (see §26).

## 23. Later-phase push semantics (frozen)

Under the (B) policy: pushing a later phase's commits over a
quarantined ancestor **must never cause PCAE to report the ancestor
phase as having successfully completed its own push ceremony.**
Concretely, `phase_push_ceremony` (§4) for the ancestor phase remains
`not_attempted` or `blocked` exactly as it was before the later push —
`commit_reachability` changing to `origin_reachable` must not be
allowed to leak into or overwrite `phase_push_ceremony` or
`canonical_report_state` for the ancestor phase in any report, doc, or
metadata field. This phase's own corrected prose (§3) is the concrete
instance of enforcing that separation for 2P.

## 24. 2P current disposition (frozen, not promoted)

- **Commit remote reachability:** `origin_reachable` (§1) — all nine
  2P commits are ancestors of current `origin/main`.
- **Canonical report state:** `quarantined` — three `blocked` quarantine
  artifacts exist (§2); no promoted 2P canonical report exists.
- **Not retroactively promoted or reclassified by this phase.** This
  phase performs no `pcae phase complete` invocation naming 2P, writes
  no new 2P canonical metadata, and does not alter the existing
  quarantine artifacts.
- **Future re-evaluation path:** once 2R implements the structured
  `fast_green` path, a future phase *may* re-run the controlled
  baseline-vs-HEAD comparison already performed manually for 2P
  (documented in PROJECT_STATUS.md's 2P entry: 0 fixed, 2 new,
  346/346 unchanged, 0 attributable regressions) through the real
  structured-mode validator, and, if it independently passes every
  §15 criterion, promote a **new** canonical report for that
  re-evaluation — not retroactively alter the existing quarantined
  artifacts, which remain as an accurate historical record that the
  *original* scalar-gate attempt was correctly blocked. This requires
  an explicit governed ceremony (its own phase/task), not an implicit
  side effect of 2R landing.

## 25. 2Q current disposition (corrected)

2Q's own canonical metadata already recorded `pushed_status:
"nothing_to_push"` and `governance_results.pcae_push_check:
"nothing_to_push"` truthfully, and this phase's own §1 confirms `HEAD
== origin/main` with zero unpushed commits on either side. **2Q's own
push ceremony succeeded; origin parity is real and confirmed fresh
this phase.** No self-contradictory No-Go language concerning 2Q's
*own* push exists in its canonical report — the only stale prose was
PROJECT_STATUS.md/CHANGELOG.md's *2P* paragraph (§3), now corrected.

## 26. Corrected 2R scope

Phase 149O.20L.7O.2R (**Attribution-Aware Verification Gate
Implementation**) should implement, in a single contained
implementation phase:

- A real `pcae` subcommand performing the controlled
  baseline-vs-candidate comparison (§8-§10), replacing the manual
  isolated-worktree procedure used ad hoc for 2P/2Q.
- Machine-produced structured evidence persisted per §8, with
  freshness enforcement per §10.
- The structured `fast_green` validation path additive to the scalar
  path (§16), implementing the five-bucket model (§6), conservation
  check (§7), and all classification rules (§11-§14).
- Stale-evidence detection (§10).
- Count-conservation checks (§7) rejecting unclassified/duplicate
  node IDs.
- Closed classification rules exactly as frozen here (§11-§14),
  not looser ones.
- Scalar-mode backward compatibility (§16) — no forced migration of
  historical reports.
- The push-ceremony artifact handling frozen in §20 (`HEAD ==
  origin/main` as a `predicted_by`-tied `expected_phase_artifacts`
  case, not a blanket pre-push exclusion).
- Deselection-prohibition enforcement (§17) and test-inventory-drift
  handling (§18).
- The quarantined-ancestor **reporting** requirement frozen in §22
  (surfacing quarantined-ancestor presence in later push/completion
  reports) — implementation of the push-block policy itself is out of
  scope per §22's chosen (B) policy (no block), but the *reporting*
  is in scope since it is what makes (B) safe.

Independent verification after 2R must confirm the **corrected**
criterion from §27, not the misstated one in 2Q's current
`recommended_next_phase` field (also corrected by this phase's
metadata sync, §"Governance" below).

## 27. Corrected 2R verification criterion (normative)

**Replace** (2Q's current, incorrect):

> "structured path cannot be used to pass a report the existing
> scalar-form gate would reject."

**With** (frozen, normative):

> The structured path **may** accept a report with a raw-nonzero
> `fast_green` result that the scalar path would reject, but **only**
> when machine-produced evidence (§8), captured against an
> authoritative baseline (§9) and a fresh, fixed candidate SHA (§10),
> independently proves every structured acceptance invariant in §15 —
> full classification coverage (§7), zero `attributable_failures`
> (§14), closed exclusion rules correctly applied (§11-§13), no
> masked deselection (§17), and correct test-inventory-drift handling
> (§18). Independent verification of 2R must construct or locate at
> least one concrete case where the structured path **correctly
> accepts** a raw-nonzero report meeting all criteria (proving the
> path is not vacuously strict), and at least one case where it
> **correctly rejects** a raw-nonzero report that fails exactly one
> criterion (proving each criterion is independently load-bearing,
> not redundant) — not merely a single "does it ever reject bad
> input" smoke test.

## 28. Security / abuse cases (frozen threat model for 2R)

2R's implementation must resist, by construction, not by policy
statement alone:

- Choosing a convenient/older baseline to hide since-introduced
  failures — closed by §9's programmatic phase-entry derivation.
- Hand-editing attribution counts in metadata — closed by §8's
  machine-produced-evidence requirement (counts must be derivable from
  the persisted node-ID evidence, not accepted as free-standing
  integers).
- Omitting failing nodes from the evidence set — closed by §7's exact
  conservation check against the full raw result set.
- Classifying arbitrary failures as `excluded_environment_failures`
  without reproduction — closed by §12's mandatory divergent-rerun
  evidence.
- Moving HEAD after evidence capture — closed by §10's freshness rule.
- Candidate-only test deselection — closed by §17's identical-command
  requirement.
- Hiding collection/setup errors by treating them as "didn't run,
  don't count" — closed by §19's explicit `raw_errors` inclusion.
- Duplicate bucket membership (double-counting exclusions to make the
  conservation math work without full classification) — closed by
  §7's disjointness requirement.
- Stale `origin/main` assumptions (comparing against a locally cached
  ref instead of a freshly fetched one) — 2R must fetch before deriving
  any origin-relative fact, matching this phase's own §1 methodology.
- Later push silently laundering a quarantined ancestor's *phase
  trust* (not just its commits) — closed by §23's explicit separation
  of `commit_reachability` from `phase_push_ceremony`/
  `canonical_report_state`.

## 29. No-Go confirmation

- No implementation performed.
- No production source file (`src/pcae/**`, `scripts/**`) modified.
- No test file (`tests/**`) created or modified.
- No gate code (`_fast_green_failure_signal()`,
  `validate_derived_correctness()`, or any push-eligibility check)
  touched.
- No retroactive promotion of Phase 149O.20L.7O.2P — its canonical
  report remains quarantined; no new promoted canonical report was
  written for it.
- No Git history rewritten; no commit amended, rebased, or deleted.
- No force push.
- No raw `git push` — this phase, like 2Q, has nothing new to push
  beyond its own governed commits, verified via `pcae push check`
  before completion.
- No fabricated literal-green claim — this phase makes no `fast_green`
  claim of its own beyond reusing the already-established
  `HEAD == origin/main`, zero-diff-to-`src/pcae/**`/`scripts/**`
  carry-forward methodology 2Q itself used (see Governance section
  below for this phase's own fast_green evidence).
- No production execution capability altered.
- No task-scope violation — only the files listed in this task's
  `--allowed-file` set were touched.

## 30. Next phase

If clean (this document's own verdict, §31 below): proceed to
**149O.20L.7O.2R — Attribution-Aware Verification Gate
Implementation**, scoped per §26 and verified per the corrected
criterion in §27. The quarantined-ancestor push semantics reconciled
in §22-§23 do not reveal a defect large enough to require a further
narrow repair phase before 2R — the current push path's absence of a
quarantined-ancestor check is confirmed accidental (§22) but not
unsafe under the recommended (B) policy, since phase trust and commit
reachability were already, in practice, kept separate (2P's canonical
report was never overwritten or falsely promoted by 2Q's push); the
gap is a **missing report-surfacing feature** (folded into 2R's scope,
§26), not an active trust defect requiring emergency repair.
