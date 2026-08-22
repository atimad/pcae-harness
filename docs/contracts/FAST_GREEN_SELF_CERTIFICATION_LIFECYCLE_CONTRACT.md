# Fast Green Self-Certification Lifecycle Contract

## Contract identity and status

**Contract:** FGSC-001
**Version:** 1.0
**Status:** FROZEN
**Frozen by:** Phase 149O.20L.7O.2S — Structured Fast Green Self-Certification
Lifecycle Contract Repair
**Architecture basis:** Phase 149O.20L.7O.2Q (`docs/PHASE_149O_20L_7O_2Q_
ATTRIBUTION_AWARE_VERIFICATION_GATE_ARCHITECTURE.md`), Phase 149O.20L.7O.2Q.1
(`docs/PHASE_149O_20L_7O_2Q_1_QUARANTINED_ANCESTOR_PUSH_STATE_AND_
ATTRIBUTION_GATE_CONTRACT_RECONCILIATION.md`), Phase 149O.20L.7O.2R
implementation (`src/pcae/core/fast_green_attribution.py`), Phase
149O.20L.7O.2R.1 independent verification (`docs/PHASE_149O_20L_7O_2R_1_
ATTRIBUTION_AWARE_VERIFICATION_GATE_INDEPENDENT_VERIFICATION.md`, Finding 1).
**Governed subject:** how a governed phase using the structured
`fast_green_attribution.v1` evidence path may reach `pcae phase complete`
without the candidate-freshness check invalidating its own evidence through
the phase's own finalization commits.

This contract is the sole normative authority governing the relationship
between **verification checkpoint**, **finalization delta**, and **final
phase HEAD** for a structured-mode phase. It does not modify
`_fast_green_failure_signal()`, the scalar `fast_green` path, the five-bucket
classification rules frozen by 2Q.1, or `validate_structured_fast_green()`'s
existing arithmetic. It does not reconcile, promote, or reclassify Phase
149O.20L.7O.2P. It is contract text only — no implementation is authorized or
performed by this contract's freezing.

Where this contract and the 2Q/2Q.1/2R documents differ in force, this
contract is normative for the self-certification lifecycle question
specifically; it does not override 2Q/2Q.1's classification rules, which
remain independently authoritative for evidence content.

## 0. Normative language

**MUST**/**MUST NOT**, **SHALL**/**SHALL NOT**, **MAY** are normative in the
conventional RFC 2119 sense. A future implementation phase's code and tests
are bound by every MUST/MUST NOT in this contract; SHOULD/MAY leave
implementation-phase discretion.

## 1. Problem statement

`validate_structured_fast_green()` (`src/pcae/core/fast_green_attribution.py:
586-589`) requires the evidence artifact's `candidate_commit` to equal `git
rev-parse HEAD` at validation time — exact equality, no tolerance. Phase
149O.20L.7O.2R's own real commit sequence (reconstructed independently by
149O.20L.7O.2R.1, §1) shows this is unsatisfiable for a phase that finalizes
itself: evidence was captured for candidate `96ecd238`, but reaching a
promoted canonical report required six further commits
(`4caf77b4, aecdc34a, 3978add4, 208932bd, 3f654eb0, bbcb81fd, 93405826,
04d58ecf` — eight, precisely; see §3 of the companion phase document for the
full classified reconstruction), so `candidate_commit` could never equal the
HEAD that exists when the report is actually promoted. 2R correctly did not
attempt to use the structured path to self-certify; it fell back to the
pre-existing scalar+deselection convention. This contract closes that gap
without weakening the freshness invariant the check exists to enforce.

## 2. Selected model: Two-Stage Verification

Rejected alternatives (see companion phase document §6 for full reasoning):

- **Option B (report-only commit allowlist without a bound checkpoint
  concept)** is subsumed by this contract rather than rejected outright — the
  allowlist mechanism in §6 below *is* Option B's content, but it is bound to
  an explicit checkpoint SHA (Option A) rather than floating relative to
  whatever HEAD happens to be at validation time. A bare allowlist with no
  checkpoint anchor cannot answer "allowlisted relative to what baseline
  state," which is exactly the ambiguity this contract must close.
- **Option C (sidecar evidence outside the Git commit graph)** is rejected:
  it would detach the evidence's authority from Git's own ancestry/immutability
  guarantees, reintroducing exactly the kind of free-standing,
  filesystem-only trust claim that 2Q.1 §8 required evidence to *not* be (a
  content-addressed artifact committed into the repository is strictly
  stronger provenance than one that lives outside version control).
- **Option D**: no existing PCAE construct was found (2R.1 §4 confirms an
  exhaustive grep of `src/pcae/` and `docs/` found none) that already solves
  this without new definition.

**Adopted: Option A, an explicit governed verification checkpoint, combined
with a closed two-stage verification model (§13 of the phase brief).**

- **Stage A — Behavioral Verification.** `baseline → verification_checkpoint_
  commit`. Runs the existing structured Fast Green machinery unchanged
  (`pcae phase fast-green-attribution`, `validate_structured_fast_green()`).
  Certifies the **behavioral verification proposition** (§5).
- **Stage B — Finalization Integrity Verification.**
  `verification_checkpoint_commit → final_phase_head`. A closed,
  mechanically-checked delta (§6-§7) plus a focused lifecycle-check set (§8),
  never a re-run of the full Fast Green suite.

Phase completion under the structured path requires **both** stages to pass.
Scalar-mode phases are wholly unaffected (§14).

## 3. Verification checkpoint — definition

**`verification_checkpoint_commit`** is the exact Git commit SHA that was
`HEAD` at the moment `pcae phase fast-green-attribution` captured its
evidence for the current phase — i.e., it is **exactly** the existing
`candidate_commit` field already recorded in the evidence artifact by
`persist_evidence()` (`fast_green_attribution.py`), given a new name for its
role in the lifecycle. **No new command or flag is introduced to "freeze" a
checkpoint separately from evidence capture** — the act of capturing
structured evidence *is* the act of freezing the checkpoint, because
`candidate_commit` is already recorded as an immutable field in a
content-addressed artifact at that moment. This contract does not invent a
second, independent freeze mechanism; it names and binds lifecycle
consequences to a value that already exists.

Authority: the checkpoint commit MUST be the phase's own most recent
IMPLEMENTING-mode commit (§9 state machine) — i.e., the last commit
containing any change capable of affecting the verification proposition,
made before the lifecycle enters `FINALIZING`. It is never caller-arbitrary:
it is mechanically equal to whatever `current_head(repo_root)` returned when
evidence capture ran, exactly as today.

The checkpoint MUST be an exact SHA, never a symbolic ref (`HEAD`,
branch name). This is already true of `candidate_commit` today and is
carried forward unchanged.

## 4. Post-checkpoint delta — path classification

Every path touched between `verification_checkpoint_commit` (exclusive) and
`final_phase_head` (inclusive) MUST fall into exactly one of two classes.
**Unknown defaults to class C (forbidden) — fail closed.**

**Class A — verification-affecting (forbidden after checkpoint without
re-verification):**

- `src/pcae/**`, `scripts/**` — any change requires Stage A to be regenerated
  against a new checkpoint (§10).
- `tests/**` — any change, addition, deletion, or rename requires Stage A
  regeneration. No exception, matching the frozen rule in the phase brief
  (§16 of the objective): zero discretion.
- `docs/contracts/**` — content-digest-bound by existing tests (confirmed
  this phase: `tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_
  amendment_independent_verification.py` and sibling HATP/authority tests
  bind specific `docs/contracts/*.md` files by content). A change here can
  alter what a contract-bound test asserts, which is exactly the kind of
  fast_green-affecting change Class A exists to catch. Forbidden after
  checkpoint.
- `pyproject.toml`, any `conftest.py`, any pytest plugin/hook configuration,
  `.githooks/**` — these are consumed during test collection/execution
  itself; a change here can alter Stage A's own result without altering a
  single test file. Forbidden after checkpoint.
- Any file that would change an HMIC digest, a trusted-source-scope
  definition, a permission-broker policy, an authority/decision record, or
  runtime configuration (§19 of the objective) — forbidden after checkpoint,
  regardless of which directory it lives in. This is a content-class rule,
  not a path rule: a governance-authority-bearing file is Class A even if it
  happens to live under a directory otherwise open to Class B (§4 below,
  content-sensitivity).

**Class B — finalization-only (permitted after checkpoint, diff-authority
checked):**

- `.pcae/phase-completion-metadata.json`, `.pcae/phase-completion-report.md`
  — the canonical report staging pair. Data-only JSON/Markdown; not imported,
  not executed, not collected by pytest. **Caveat (§20 of the objective,
  resolved):** `phase_reports.py`'s own tests read these files' *shape*
  (schema validity) as part of `pcae check`, but not as part of the `pytest
  -m fast_green` selection that Stage A's evidence is bound to — a change
  here cannot alter `raw_failed`/`raw_errors`/baseline sets already captured
  and frozen in the Stage A evidence artifact. Permitted.
- `.pcae/fast-green-attribution/<digest>.json` — the evidence artifact
  itself. Necessarily created in the commit immediately after the checkpoint
  (§11, irreducibly post-verification). Permitted, and in practice mandatory.
- `PROJECT_STATUS.md`, `CHANGELOG.md` — prose. Not collected by pytest, not
  imported by any production or test module (confirmed: neither file has a
  `.py` extension and no `import` statement in the tree references them by
  path other than doc-generation tooling under `pcae docs`, which is not
  part of the `fast_green`-marked test selection). Permitted.
- `tasks/DONE.md`, `tasks/active/*`, `tasks/done/*` — task lifecycle
  metadata. **Caveat resolved:** `pcae doctor task-memory` reads these, but
  that check is a Stage B focused check (§8), never part of `pytest -m
  fast_green`. Permitted, subject to §5's ordering preference.
- `session/`-scoped lifecycle metadata (`.pcae/session.json` and
  equivalents) written by `pcae session bootstrap`/`pcae task transition` —
  same reasoning as task files. Permitted.

**Content-sensitive restriction (both classes):** within a Class-B-eligible
directory, a file MUST additionally be of a data format
(`.md`, `.json`, `.txt`) to qualify — an executable file
(`.py`, `.sh`, any file with the executable bit set, any file loaded by an
import machinery or a hook) appearing under an otherwise-open path is Class A
regardless of directory, because directory-based allowance was only ever
justified by these files being inert data, and an executable file breaks
that justification. No such file exists in today's Class-B path set; this
restriction exists to keep the rule correct if one is ever added.

## 5. Task lifecycle and report-generation ordering (SHOULD)

To keep the post-checkpoint delta minimal (design goal, objective §45):
implementers of a structured-mode phase SHOULD perform, before freezing the
checkpoint: all production/test edits, task-lifecycle transition into the
phase's dedicated task, PROJECT_STATUS.md/CHANGELOG.md drafting, and as much
of the canonical report's content as does not depend on the verification
result itself. Only Stage A evidence capture, the resulting evidence
artifact, and the report fields that can only be known after Stage A runs
(verdict, `raw_failures` counts, `candidate_commit` itself) are irreducibly
post-checkpoint (§11). This is a SHOULD, not a MUST: 2R's own real sequence
did not follow this ordering and remains a valid historical record under
§14's backward-compatibility guarantee; it is a preference for future
structured-mode phases to minimize trusted post-checkpoint surface, not a
retroactive requirement.

## 6. Diff authority (MUST, mechanical)

Stage B integrity verification computes `git diff --name-only
verification_checkpoint_commit..final_phase_head` and requires every listed
path to satisfy Class B (§4) exactly, including the content-sensitivity
restriction. Any path outside Class B, or ambiguous/unrecognized, is fail
closed: **the checkpoint is invalidated and Stage A must be regenerated**
(§10). Commit message text is explicitly **not** authority for this check
(objective §25) — only the actual changed-path set and, where the
content-sensitivity restriction applies, the actual file type.

## 7. Merge commits and history rewrites (MUST)

- **Merge commits** in the range `verification_checkpoint_commit..
  final_phase_head` are rejected outright unless a future governed contract
  revision explicitly authorizes a specific merge-topology exception. No
  exception is authorized by this contract. Rationale: a merge can introduce
  changes from a side-branch ancestry that never went through Stage A at all,
  defeating diff authority's completeness.
- **Any history rewrite** (amend, rebase, filter) that changes the ancestry
  between `verification_checkpoint_commit` and `final_phase_head` — such
  that the checkpoint is no longer a real ancestor of final HEAD by the
  original SHA — invalidates the checkpoint unconditionally. No substitute
  checkpoint may be chosen after the fact ("whichever commit passes");
  evidence must be regenerated against a new, genuine checkpoint (§10).

## 8. Stage B focused checks (MUST)

Stage B integrity verification additionally requires each of the following
to pass against `final_phase_head` (not a re-run of `pytest -m fast_green`):

- `pcae check`
- `pcae status coherence`
- `pcae doctor task-memory`
- `pcae push check`
- `pcae phase-report consistency` (read-only diagnostic; informational under
  today's tooling — see §12 for its required future behavior)

A failure in any focused check does not, by itself, invalidate Stage A's
behavioral evidence (the checkpoint's diff authority may still hold) — it
blocks progression to `FINALIZATION_VERIFIED` (§9) until the underlying
Class-B-only defect is fixed with a further Class-B-only commit and the
focused checks are rerun. It does **not** require Stage A regeneration
unless fixing it requires a Class-A change, in which case §10 governs.

## 9. Lifecycle state machine (MUST)

States (repository-consistent naming, matching the objective's suggested
vocabulary):

```
IMPLEMENTING
  -> CANDIDATE_FROZEN        [pcae phase fast-green-attribution captures
                               evidence; HEAD at that instant becomes
                               verification_checkpoint_commit]
CANDIDATE_FROZEN
  -> BEHAVIOR_VERIFIED       [validate_structured_fast_green() PASS against
                               the checkpoint artifact]
  -> IMPLEMENTING            [FAIL — regenerate from a new checkpoint after
                               fixing the underlying Class-A defect]
BEHAVIOR_VERIFIED
  -> FINALIZING              [first post-checkpoint commit begins;
                               lifecycle enters finalization-only mode]
FINALIZING
  -> FINALIZATION_VERIFIED   [diff authority (S6) + Stage B focused checks
                               (S8) both pass against current HEAD]
  -> IMPLEMENTING            [a Class-A change is required — see S10,
                               return-to-work]
FINALIZATION_VERIFIED
  -> READY_TO_PUSH           [pcae phase complete --stage-pending-report
                               succeeds]
READY_TO_PUSH
  -> PUSHED                  [pcae push succeeds; origin/main == HEAD]
  -> READY_TO_PUSH            [push failure — no state change, no
                               behavioral rerun, repository state
                               unchanged; retry]
PUSHED
  -> COMPLETE                 [pcae phase complete (promote) succeeds;
                               canonical report promoted, notification
                               dispatched]
  -> FINALIZING                [post-push field-correction needed — see
                                S11's PUSH_STATE_SYNC note; re-enter
                                FINALIZING with the *same* checkpoint,
                                Class-B-only commit, re-run S6+S8 only,
                                never Stage A]
```

`FINALIZING` is the explicit "finalization-only mode" the objective's §23
asks for: while a phase is in `FINALIZING` or later, any commit containing a
Class A path is a contract violation — the correct response is to invalidate
the checkpoint, transition back to `IMPLEMENTING`, and restart at
`CANDIDATE_FROZEN` only after the Class-A change and a fresh Stage A run.

## 10. Return-to-work / invalidation semantics (MUST)

If, after `CANDIDATE_FROZEN`, a Class-A defect is discovered (a real bug, a
missed test, anything touching `src/pcae/**`, `scripts/**`, `tests/**`,
`docs/contracts/**`, or test-execution configuration):

1. The current checkpoint and any Stage A evidence bound to it are
   invalidated immediately — they MUST NOT be reused, patched, or amended
   in place ("no patching behind the checkpoint," objective §24).
2. The lifecycle returns to `IMPLEMENTING`.
3. The required change is made as an ordinary implementation commit.
4. A new checkpoint is frozen (a new `pcae phase fast-green-attribution`
   run against the new HEAD).
5. Stage A is re-run in full against the new checkpoint.

No shortcut exists for "just this one small fix" — this is deliberate: the
freshness/checkpoint model exists precisely to make "small fix after
verification" always re-verify, closing the self-certification gap without
opening a narration-based escape hatch.

## 11. Irreducibly post-checkpoint artifacts (frozen list)

Only the following categories cannot exist before Stage A's result is known,
and are therefore always expected in the `FINALIZING` delta even under the
minimized-ordering preference (§5):

- The evidence artifact itself (`.pcae/fast-green-attribution/<digest>.json`)
  and the `test_results["fast_green"]` value embedding its reference.
- The final verdict/summary fields of the canonical report that describe the
  verification outcome (pass/fail, bucket counts, `predicted_by` references).
- Final completion metadata (`status: "completed"`, `phase_commits`, digest
  fields computed over the final report).
- Push-state fields not yet knowable pre-push (§12).

Any other doc/status content SHOULD be drafted before the checkpoint per §5.

## 12. Push-state fields and post-push metadata (MUST)

`pushed_status` and `governance_results.pcae_push_check` cannot be known to
equal their final literal values (`pushed`/`clean`/`nothing_to_push`,
per `project_phase_completion_procedure.md`) until after `pcae push` actually
runs. Two cases:

- **Predicted-correct case (expected steady state):** the `FINALIZING`-stage
  commit that stages the canonical report for `--stage-pending-report`
  already writes the *target* post-push literal value (this is the existing
  established convention — memory correction #3 — carried forward
  unchanged). No commit is required after `pcae push` in this case;
  `final_phase_head` is the commit that existed immediately before `pcae
  push` was invoked (§13).
- **Correction case (prediction was wrong):** if, after push,
  `pcae push check` reveals the pre-written literal was wrong, a further
  Class-B-only commit correcting the field is required, followed by a
  second `pcae push`. This is modeled as a return to `FINALIZING` with the
  **same checkpoint** (no Stage A re-run — the correction is Class B only),
  re-checked by S6+S8 only. This is bounded: it is a data-entry-correction
  loop, not a verification loop, and terminates once the literal value
  matches actual push state (empirically at most one extra round trip per
  `project_phase_completion_procedure.md`'s own recorded history).

This resolves objective §48: the existing PCAE convention of syncing
post-push state fields does **not** create a *behavioral*-verification
recursion — it is bounded within Stage B, never touches Stage A, and Stage
A's checkpoint and evidence remain valid and unregenerated throughout.

## 13. Final HEAD definition (MUST)

**`final_phase_head`** is the commit that is `HEAD` at the moment `pcae phase
complete` (the promoting invocation, without `--stage-pending-report`)
succeeds and promotes the canonical report to `COMPLETE`. Concretely, in the
well-formed case (§12's predicted-correct case), this is the same commit that
was pushed — i.e. `origin/main == final_phase_head` is expected to hold at
promotion time, not merely at push time, because no further commit is made
between push and promotion in the steady state. In the correction case,
`final_phase_head` is the commit after the correcting push. Either way,
**`final_phase_head` is defined operationally as "HEAD at successful
promotion," not "HEAD at push"** — this distinguishes it from `origin/main`
parity, which §14/§29 of the objective ask to be checked separately and is
governed unchanged by existing push-check machinery (this contract does not
alter `pcae push check`'s semantics).

## 14. Candidate freshness — replaced condition (MUST)

`validate_structured_fast_green()`'s freshness check (§ current code,
`fast_green_attribution.py:586-589`) is, by this contract, **conceptually**
replaced for the *lifecycle-completion* question (not for the function's own
unit behavior, which stays a strict equality check against whatever HEAD is
passed to it — see §15) by:

Structured evidence is **lifecycle-fresh** iff **all** of:

1. `candidate_commit == verification_checkpoint_commit` (the SHA recorded at
   capture, unchanged from today).
2. `baseline_commit` remains the authoritative phase-entry baseline per
   `derive_phase_entry_baseline()`, unchanged.
3. `verification_checkpoint_commit` is an ancestor of `final_phase_head`
   (`git merge-base --is-ancestor`).
4. Every commit in `verification_checkpoint_commit..final_phase_head` is a
   single-parent (non-merge) commit whose changed paths satisfy Class B
   exactly (§4, §6, §7).
5. Stage B's required focused checks (§8) pass against `final_phase_head`.

Condition 1 is **exactly** today's check, unweakened — candidate SHA binding
is never loosened (objective §20's explicit instruction). Conditions 3-5 are
new and additive: they let a phase's finalization commits exist *after* a
valid candidate without ever asking condition 1 to tolerate a moving target.

## 15. Verification proposition (frozen, exact)

Structured Fast Green, under this contract, certifies exactly:

> "This phase introduced no attributable production/test regressions through
> `verification_checkpoint_commit`, and every commit between that checkpoint
> and the phase's final HEAD belongs to a mechanically verified,
> non-verification-affecting finalization class."

It explicitly does **not** certify:

> "`final_phase_head` produces byte-identical global test results to
> `verification_checkpoint_commit`."

Finalization commits are not asserted to be behaviorally inert in the sense
of "cannot possibly affect any test ever" — they are asserted to be outside
the specific, closed class of paths/content this contract requires Stage A's
`pytest -m fast_green` selection to be sensitive to (§4's own resolution of
"does not affect production" vs. "cannot affect any Fast Green result").
Where a Class B path is *also* checked by a *non*-fast_green-marked
diagnostic (e.g. `pcae doctor task-memory`), that diagnostic is exactly
Stage B's focused-check set (§8), not Stage A's certified proposition.

## 16. Scalar-mode backward compatibility (MUST, unchanged)

Nothing in this contract applies to a report whose `test_results["fast_green"]`
is not a dict carrying `schema_version == "fast_green_attribution.v1"`. Every
historical and future scalar-mode phase completes exactly as it does today —
no verification checkpoint, no Stage B, no diff authority. This contract
introduces no forced migration.

## 17. Push trust-boundary preservation (MUST)

This contract does not add any structured-evidence interpretation to
`src/pcae/commands/push.py`. `push.py` continues to trust exclusively
`compute_final_trust()` over the already-finalized canonical report (2R.1 §3,
confirmed no second trust boundary exists). Any future implementation of
this contract MUST preserve that: checkpoint/diff-authority verification
happens inside the phase-report-promotion pipeline
(`finalization_transaction.py` pre-promotion certification and
`_apply_derived_correctness`/`finalize_phase_report` in `phase_reports.py`),
never inside `push.py` directly.

## 18. Report semantics (MUST)

A canonical report produced under this contract MUST record both
`verification_checkpoint_commit` and `final_phase_head` as distinct fields
and MUST NOT imply, in prose or schema, that they are required to be equal.
A "COMPLETE, trusted" report under this contract means: behavioral checkpoint
verified (Stage A) **and** finalization delta authorized (Stage B diff
authority) **and** final lifecycle checks clean (Stage B focused checks) —
never "Fast Green was executed literally at the final metadata commit."

## 19. Future `phase-report consistency` behavior (design target, not
implemented here)

`pcae phase-report consistency` (`src/pcae/commands/phase_reports.py:887`)
currently re-validates a historical report's structured evidence against
*current* HEAD using the unmodified strict-equality freshness check, so any
promoted structured-mode report already necessarily reads as "stale" the
moment any later commit lands — a false-negative under this contract's own
model, though harmless today because this diagnostic is read-only and gates
nothing (confirmed by 2R.1 §4's grep). A future implementation phase SHOULD
teach this diagnostic to evaluate the §14 replaced condition (checkpoint
freshness + authorized finalization delta) instead of naive
`candidate_commit == current HEAD`, for the report it is inspecting at the
`final_phase_head` recorded in that same report — not for arbitrary current
HEAD, which may be many phases later. **Not implemented by this contract.**

## 20. Non-goals / carried-forward findings (explicitly out of scope)

This contract does not resolve, and does not claim to resolve:

- **Baseline/candidate raw-content trust** (2R.1 Finding 2): the validator
  recomputes attribution arithmetic but trusts persisted
  `baseline_raw_failed`/`baseline_raw_errors` content verbatim rather than
  re-executing pytest against the baseline commit. Unaffected by this
  contract; carried forward as a documentation-scope clarification, not an
  urgent repair.
- **Environment-exclusion timeout classification** (2R.1 §6): a rerun that
  times out is classified as a divergent error, conflating "flaky" with "a
  genuine hang." Unaffected; future hardening.
- **Baseline commit-message authority** (`derive_phase_entry_baseline()`
  relies on a `"Phase <id>: ..."` subject-line convention, not a structural
  guarantee). Unaffected; a phase-entry commit lacking the exact prefix would
  shift the derived baseline. This contract's `verification_checkpoint_
  commit` is orthogonal to baseline derivation and does not change how the
  baseline itself is computed.
- **Evidence-artifact retention** (`.pcae/fast-green-attribution/` has no
  cleanup policy). Observation only.
- **Phase 149O.20L.7O.2P reconciliation.** Explicitly frozen as
  out of scope until this contract is implemented, independently verified,
  and proven usable end-to-end by a disposable self-hosting phase (§21).

## 21. Acceptance tests for a future implementation (frozen requirement list)

A future implementation phase MUST provide tests covering at minimum:

1. Valid checkpoint → Stage A pass → Class-B-only finalization delta →
   Stage B pass → completion succeeds.
2. A `src/pcae/**` change after checkpoint is rejected (checkpoint
   invalidated, Stage A regeneration required).
3. A `tests/**` change after checkpoint is rejected, unconditionally.
4. A `docs/contracts/**` change after checkpoint is rejected.
5. An allowed Class B finalization artifact (metadata/report/status/
   task file) is accepted.
6. An unrecognized/unknown path after checkpoint defaults to rejection
   (fail closed).
7. Finalization-delta count/set integrity: every changed path between
   checkpoint and final HEAD is accounted for; none silently ignored.
8. A stale checkpoint (candidate_commit mismatch, condition 1 of §14) is
   rejected exactly as today.
9. A rewritten/rebased ancestry between checkpoint and final HEAD is
   rejected (checkpoint no longer a real ancestor).
10. A merge commit in the checkpoint..final-HEAD range is rejected.
11. Return-to-work: a Class-A defect discovered after checkpoint correctly
    invalidates the checkpoint and requires full Stage A regeneration; no
    "patch behind the checkpoint" path exists.
12. Crash/restart reconstruction: lifecycle state (checkpoint SHA,
    Stage A/B pass state) is fully reconstructable from Git history plus
    `.pcae/` canonical metadata alone — no ephemeral-only authority.
13. Scalar-mode backward compatibility: an unmarked `fast_green` value is
    entirely unaffected by any of the above.
14. Structured self-hosting positive (§22.1).
15. Structured self-hosting negative (§22.2).
16. Finite termination: no scenario in the test suite requires an unbounded
    commit/verify/commit loop; every retry path (push failure, push-state
    correction) is bounded and does not re-trigger Stage A.

## 22. Self-hosting acceptance tests (future, decisive)

**22.1 — Positive.** A disposable governed phase MUST, to prove this
contract operationally: (1) make a small test-affecting change; (2) freeze a
verification checkpoint; (3) run structured Fast Green (Stage A pass); (4)
commit only Class B finalization artifacts; (5) pass Stage B; (6) complete
canonical report promotion; (7) `pcae phase complete` succeeds; (8) governed
push succeeds; (9) origin parity achieved; (10) no scalar deselection
fallback used anywhere in the cycle.

**22.2 — Negative.** After Stage A evidence capture, modifying one
forbidden/Class-A file MUST cause finalization to reject the stale/invalidated
evidence and require full re-verification — not silently proceed.

Neither test is executed by this contract-freezing phase. This contract is
not operationally complete until 22.1 succeeds on a real disposable phase.

## 23. Amendment

This contract may only be revised by a future governed phase producing an
explicit version increment (v1.1, v2, ...) with its own frozen change list,
following the same pattern as PGP-001 v1.0 → v1.1 (`docs/contracts/
PILOT_GOVERNANCE_PROTOCOL_CONTRACT.md`).
