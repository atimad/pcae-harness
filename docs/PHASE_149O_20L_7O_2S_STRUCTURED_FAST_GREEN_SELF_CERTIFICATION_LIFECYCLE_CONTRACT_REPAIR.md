# Phase 149O.20L.7O.2S — Structured Fast Green Self-Certification Lifecycle Contract Repair

Architecture / contract design only. No `src/pcae/**`, `scripts/**`, or
`tests/**` file created or modified. No change to the structured
attribution engine (`src/pcae/core/fast_green_attribution.py`) or the
scalar `fast_green` gate. Phase 149O.20L.7O.2P is not reconciled,
promoted, or touched. This phase resolves the single independently
confirmed Blocking lifecycle gap from Phase 149O.20L.7O.2R.1 ("Finding
1 — self-certification freshness cycle is real") by producing
`docs/contracts/FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md`
(FGSC-001 v1.0, FROZEN).

## 1. True phase-entry commit

`fb8ab8a3` — "Phase 149O.20L.7O.2R.1: remove stale tasks/active/ files
superseded by task transitions, sync fast_green scalar evidence" (2R.1's
own final commit; HEAD at this phase's task-open event, confirmed via
`git rev-parse HEAD` before any commit of this phase).

## 2. Self-certification cycle reconstruction (the defect, restated
precisely)

`validate_structured_fast_green()` requires `evidence["candidate_commit"]
== git rev-parse HEAD` at validation time
(`src/pcae/core/fast_green_attribution.py:586-589`). A phase that wants to
use this path to certify its own completion must, after capturing that
evidence, still make the ordinary governed lifecycle commits (task
transition, PROJECT_STATUS/CHANGELOG update, canonical metadata/report
sync, task close) before `pcae phase complete` can run — each of those
commits moves HEAD past the captured `candidate_commit`, so the freshness
check fails deterministically for a phase attempting genuine self-hosted
structured certification. Regenerating evidence at the new HEAD only
produces a new commit, repeating the problem. This is the "impossible
candidate_commit == final_HEAD recursion" the objective names.

## 3. Exact 2R commit sequence, classified

Reconstructed directly from `git log --oneline 0773b21e..04d58ecf` (2Q.1
tip to 2R's own final commit), independently re-confirmed this phase
(matches 2R.1's own §1, re-derived rather than trusted):

| Order | Commit | Subject | Class |
|---|---|---|---|
| 1 | `793a99ca` | implement attribution-aware Fast Green verification gate | **Production/test-affecting** (`src/pcae/core/fast_green_attribution.py`, `phase_reports.py`, `cli.py`, `phase_fast_green_attribution.py`, new test file) |
| 2 | `96ecd238` | task lifecycle transition to dedicated phase task | Task-lifecycle (Class B) — **this is where `pcae phase fast-green-attribution` was run; its `candidate_commit` == this SHA** |
| 3 | `4caf77b4` | persist controlled Fast Green attribution evidence (2 runs) | Evidence-artifact commit (Class B, irreducibly post-checkpoint) |
| 4 | `aecdc34a` | update PROJECT_STATUS.md/CHANGELOG.md | Metadata/report (Class B) |
| 5 | `3978add4` | sync active task file | Task-lifecycle (Class B) |
| 6 | `208932bd` | sync canonical phase-completion metadata and report | Metadata/report (Class B) |
| 7 | `3f654eb0` | fix metadata validation_results/test_results wiring | Metadata/report (Class B) |
| 8 | `bbcb81fd` | close out task lifecycle, open idle placeholder | Task-lifecycle (Class B) |
| 9 | `93405826` | set pushed_status/pcae_push_check to post-push literals | Push-state sync (Class B) |
| 10 | `04d58ecf` | sync active task file | Task-lifecycle (Class B) — 2R's own final HEAD |

HEAD advanced through **eight** further commits after structured evidence
was captured for candidate `96ecd238` (commit 2) before reaching 2R's own
final HEAD (commit 10). Every one of those eight is, under this phase's
own classification (§4 of the frozen contract), Class B —
finalization-only, non-verification-affecting. None touches
`src/pcae/**`, `scripts/**`, `tests/**`, or `docs/contracts/**`. This
empirically validates the contract's Class B allowlist against a real,
already-completed phase's actual commit shape, without needing to
fabricate a hypothetical sequence.

## 4. Existing lifecycle concepts inspected (independent re-derivation,
not assumed from 2R.1's proposed repair shape)

- `src/pcae/core/finalization_transaction.py` — has its own "checkpoint"
  concept (`_save_checkpoint`/`_load_checkpoint`, `checkpoint_path`), but
  this is a **resumable-transaction checkpoint** (durable state for
  resuming an interrupted finalization run after a crash), unrelated to
  Git-commit verification. Naming collision noted; this contract's
  `verification_checkpoint_commit` is a distinct concept and the two must
  not be conflated. No behavioral overlap found.
- `pcae phase-report consistency`
  (`src/pcae/commands/phase_reports.py:887`, `run_phase_report_
  consistency`) — read-only, re-derives `validate_derived_correctness()`
  against the latest promoted report's sealed Architecture Status
  snapshot. Confirmed (matching 2R.1 §4) wired into no gating command.
  Its future required behavior under this contract is frozen in §19 of
  `FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md` — not implemented
  this phase.
- `src/pcae/commands/push.py` (`_assess_phase_report_trust`,
  `compute_final_trust` in `src/pcae/core/phase_report_trust.py`) —
  confirmed to touch no `fast_green` field; trusts only the already-
  promoted canonical report. No second trust boundary; nothing to change
  here for this contract (§17 of the frozen contract preserves this).
- `docs/contracts/*.md` naming/status convention (`PILOT_GOVERNANCE_
  PROTOCOL_CONTRACT.md` used as the template: `Contract:`/`Version:`/
  `Status: FROZEN`/`Frozen by:` header block, numbered normative
  sections, amendment section). Adopted verbatim for FGSC-001.
- `docs/contracts/**` content-digest binding confirmed by direct grep:
  multiple independent tests (e.g.
  `tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_
  independent_verification.py`) assert against specific contract file
  content/digests — this is why Class A forbids `docs/contracts/**`
  changes after checkpoint (§4 of the contract) rather than defaulting it
  to Class B by directory-only reasoning.
- No existing "candidate freeze," "phase-owned commit," or
  "verification checkpoint" concept was found anywhere in `src/pcae/` or
  `docs/` beyond the unrelated transaction-checkpoint noted above
  (grepped exhaustively this phase, independently of 2R.1's own grep).

## 5. Selected lifecycle model and rejected alternatives

See `FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md` §2. Summary:
**Option A (explicit governed verification checkpoint) combined with a
two-stage (Behavioral / Finalization Integrity) verification model** is
adopted. Option B (bare report-only allowlist) is subsumed as Stage B's
content, anchored to a checkpoint rather than floating. Option C (sidecar
evidence outside Git) is rejected — it would weaken provenance below
2Q.1 §8's own machine-produced-evidence bar. Option D (existing
construct) does not exist (§4 above).

## 6. Verification checkpoint, authority, and freshness

Full definitions frozen in the contract §3, §9, §14. Summary: the
checkpoint is **not** a new artifact — it is the existing
`candidate_commit` field `pcae phase fast-green-attribution` already
records, given lifecycle meaning. Freshness is replaced (for the
lifecycle-completion question only; the function's own unit check is
untouched) by five conjunctive conditions: exact checkpoint SHA match,
authoritative baseline, checkpoint-is-ancestor-of-final-HEAD, every
intervening commit Class B and non-merge, and Stage B focused checks
passing.

## 7. Post-checkpoint delta — path/content classification

Full classification in the contract §4, empirically validated against
2R's real 8-commit delta (§3 above — every commit classifies as Class B
under this rule, with zero ambiguous cases). Path-based classification
alone was explicitly assessed as insufficient (objective §10): resolved
by tying the JSON/Markdown-only Class B files to the specific claim they
are not part of the `pytest -m fast_green` selection (the actual
verification proposition, §15 of the contract) even though some are read
by other, non-gating diagnostics (`pcae check`, `pcae doctor
task-memory`) — which is exactly why Stage B's focused-check set exists,
rather than relying on path allowance alone to prove safety.

## 8. Task lifecycle and report-generation ordering

Frozen as a SHOULD (contract §5), not a MUST: 2R's own real sequence
interleaved task-lifecycle commits with metadata sync rather than
front-loading everything before evidence capture, and remains a valid
historical record. A future structured-mode phase is encouraged, not
required, to minimize the post-checkpoint delta by ordering task
transition, PROJECT_STATUS/CHANGELOG drafting, and as much of the report
as does not depend on the verification result itself, before freezing
the checkpoint.

## 9. Two-stage verification result

Stage A (Behavioral): unchanged existing machinery
(`pcae phase fast-green-attribution`,
`validate_structured_fast_green()`), bound to `verification_checkpoint_
commit`. Stage B (Finalization Integrity): new construct, frozen this
phase, not implemented — diff authority (`git diff --name-only
checkpoint..final_HEAD` checked against Class B) plus the five focused
checks in contract §8. Both required for completion under the structured
path (contract §2).

## 10. Candidate freshness semantics (replaced condition)

See contract §14, reproduced in full there; not duplicated here. Key
point: condition 1 (`candidate_commit == checkpoint`) is unweakened —
the exact same equality check as today, applied to the checkpoint SHA
rather than to a moving final HEAD.

## 11. Checkpoint invalidation, return-to-work, merges, rewrites

Frozen in contract §7, §10. A Class-A change after checkpoint, a merge
commit in the checkpoint..final-HEAD range, or any history rewrite
breaking checkpoint ancestry, all unconditionally invalidate the
checkpoint and require full Stage A regeneration against a new
checkpoint — no partial repair, no checkpoint substitution.

## 12. Origin/push relationship and post-push state

Frozen in contract §12, §13. The existing `pushed_status`/
`pcae_push_check` post-push-literal-sync convention
(`project_phase_completion_procedure.md` correction #3) is modeled
explicitly: in the well-formed case it requires **zero** commits after
`pcae push` (the target literal is pre-written before push, per the
existing convention); in the correction case (prediction wrong) exactly
one bounded Class-B-only round trip is required, re-entering `FINALIZING`
with the *same* checkpoint — never re-triggering Stage A. This directly
answers objective §48: the existing post-push metadata convention does
not create a Stage-A-level recursion; it is fully contained in Stage B.

`final_phase_head` is defined operationally (contract §13) as "HEAD at
successful `pcae phase complete` promotion" — distinguished from "HEAD at
push," since in the correction case they can differ by one Class-B
commit.

## 13. Lifecycle state machine and finite termination

Full state machine in contract §9:
`IMPLEMENTING → CANDIDATE_FROZEN → BEHAVIOR_VERIFIED → FINALIZING →
FINALIZATION_VERIFIED → READY_TO_PUSH → PUSHED → COMPLETE`, with explicit
invalidation transitions back to `IMPLEMENTING` (Class-A defect) and a
bounded `COMPLETE`-adjacent correction loop (`PUSHED → FINALIZING`, same
checkpoint) for push-state field correction only. No unbounded loop
exists in this state machine: every retry edge either (a) requires a
Class-A change and therefore a genuinely new checkpoint and Stage A run
(finite because each such loop iteration corresponds to a real code
change, not a metadata-only regeneration), or (b) is a Class-B-only
correction bounded to Stage B's cheap checks, empirically observed to
terminate in at most one extra round trip in this repository's own prior
history (`project_phase_completion_procedure.md` correction #3).

## 14. Crash recovery

Not implemented this phase (contract §21 item 12, future test
requirement). Design intent, stated for a future implementation phase:
checkpoint SHA, Stage A pass/fail state, and Stage B pass/fail state must
all be reconstructable from Git history (the checkpoint commit itself,
the evidence artifact's content-addressed file) plus `.pcae/` canonical
metadata already on disk — no hidden ephemeral-only state. This mirrors
`finalization_transaction.py`'s existing durable-checkpoint pattern for
crash recovery of the promotion step specifically (a different mechanism,
per §4 above, but a precedent for "resumability must be reconstructable
from disk," which this contract's future implementation should follow).

## 15. Canonical report semantics and phase-report-consistency future
behavior

Frozen in contract §18-§19. A COMPLETE trusted report must record both
`verification_checkpoint_commit` and `final_phase_head` without implying
equality. `pcae phase-report consistency`'s current naive re-check
(strict `candidate_commit == current HEAD`, evaluated against whatever
HEAD is at diagnostic-run time, not the report's own final HEAD) is
identified as a false-negative-prone design once structured self-hosting
begins — every later commit anywhere in the repo makes a past structured
report look "stale" under today's logic even though nothing about that
report's own trustworthiness changed. A future implementation phase
SHOULD repair this specific diagnostic's evaluation logic; **not
implemented here.**

## 16. Push trust-boundary preservation

Confirmed and frozen unchanged (contract §17): no structured-evidence
interpretation is added to `push.py`. All checkpoint/diff-authority logic
belongs inside the phase-report-promotion pipeline
(`finalization_transaction.py`, `phase_reports.py`), matching where
`validate_derived_correctness()` already lives today.

## 17. Scalar backward compatibility

Unaffected, unconditionally (contract §16). No historical or future
scalar-mode phase is required to adopt any part of this contract.

## 18. Findings carried forward (not solved by this phase, scope limited
per instruction)

1. **Baseline/candidate raw-content trust** (2R.1 Finding 2) — the
   validator trusts persisted baseline raw-failure content verbatim
   rather than re-executing pytest against the baseline commit. Outside
   this phase's scope; not affected by the checkpoint/Stage-B model
   (Stage B never touches Stage A's arithmetic).
2. **Environment-exclusion timeout classification** — a timed-out rerun
   currently becomes an environment exclusion without independently
   proving non-reproducibility. Outside scope; classified as separate
   future hardening, unaffected by this contract.
3. **Baseline commit-message authority** — `derive_phase_entry_baseline()`
   depends on the `"Phase <id>: ..."` subject convention. Outside scope;
   this contract's checkpoint concept is orthogonal to how the baseline
   itself is derived.
4. **Evidence artifact retention** — `.pcae/fast-green-attribution/` has
   no cleanup policy. Observation only, unaffected.

## 19. Phase 149O.20L.7O.2P reconciliation gate (frozen, unchanged
disposition)

2P remains quarantined, untouched, not reconciled. Per 2R.1 §10 and this
phase's own instruction: 2P reconciliation may be reconsidered only
after (a) this lifecycle contract's future implementation phase lands,
(b) that implementation is independently verified, and (c) the §22
self-hosting acceptance tests (positive and negative) succeed on a real
disposable phase. None of those three preconditions is satisfied by this
contract-freezing phase alone.

## 20. Implementation impact (identified, not performed)

A future implementation phase will need to touch, at minimum:

- `src/pcae/core/fast_green_attribution.py` — add checkpoint-vs-final-HEAD
  aware validation entry point (or a wrapping function) implementing
  contract §14's five-condition freshness replacement, without touching
  the existing strict single-commit equality check's own unit semantics.
- `src/pcae/core/finalization_transaction.py` — pre-promotion
  certification needs to evaluate Stage B (diff authority + focused
  checks) in addition to Stage A, when the report is structured-mode.
- `src/pcae/core/phase_reports.py` — `_apply_derived_correctness()`
  dispatch and canonical report schema need `verification_checkpoint_
  commit`/`final_phase_head` fields (§18 of the contract).
- `pcae phase complete` CLI — surfacing lifecycle state
  (`FINALIZING`/`FINALIZATION_VERIFIED`/etc.) and enforcing the
  invalidation transitions.
- `pcae phase-report consistency`
  (`src/pcae/commands/phase_reports.py:887`) — future-behavior repair
  per contract §19.
- Task lifecycle / commit lifecycle / push lifecycle CLIs — no change to
  their own mechanics is anticipated; they remain the source of the
  Class B commits Stage B classifies, not gate-implementing code
  themselves.
- Canonical report schema — new fields as above; must remain backward
  compatible with scalar-mode reports carrying neither field.

None of these files were modified this phase.

## 21. Authority / HMIC consequence

This lifecycle contract governs whether a structured-mode report may be
promoted `COMPLETE` while carrying commits after its own verification
evidence — a governance-critical determination (objective §57). No
`docs/contracts/HATP_*` or HMIC-scope document was touched or requires
amendment at this contract-freeze time: this contract does not grant, by
itself, any new authority to accept a report that today's scalar/
structured gates would reject on Stage A grounds — it only precisely
scopes what may follow a verified Stage A result. A future
implementation phase, when it actually wires this into
`finalization_transaction.py`/`phase_reports.py`, is the point at which
HMIC-scope re-review should be considered if the implementation's
mechanism (e.g. a new field in the trust computation) intersects
existing trust-field enumeration — flagged for that future phase, not
resolved here.

## 22. Focused verification (this phase's own governance evidence)

This is a documentation/contract-design phase with **zero** diff to
`src/pcae/**`, `scripts/**`, or `tests/**` — the same carry-forward
methodology 2Q and 2Q.1 used for their own completion, verified this
phase via `git diff --stat` against phase-entry commit `fb8ab8a3`
restricted to those three path prefixes (empty). Governed checks run
this phase:

- `pcae health`
- `pcae check`
- `pcae status coherence`
- `pcae doctor task-memory`
- `pcae push check`
- `pcae runtime inspect`

Results recorded in the Governance section of `PROJECT_STATUS.md`'s new
entry and in `.pcae/phase-completion-metadata.json`'s
`governance_results`.

## 23. No production implementation

Confirmed: no file under `src/pcae/**`, `scripts/**`, or `tests/**` was
created or modified by this phase. The only files touched are this
document, the frozen contract, `PROJECT_STATUS.md`, `CHANGELOG.md`, task
lifecycle files, and `.pcae/phase-completion-metadata.json`/
`.pcae/phase-completion-report.md`.

## 24. Runtime

Unchanged: Observed / observe / unavailable throughout, as in every prior
phase in this series.

## 25. No-Go confirmation

- No implementation performed; no production/test file touched.
- No change to `validate_structured_fast_green()`, the five-bucket
  classification, or `_fast_green_failure_signal()`.
- No reconciliation or promotion of Phase 149O.20L.7O.2P.
- No Git history rewritten; no commit amended, rebased, or deleted.
- No force push; no raw `git push` — governed `pcae push` only.
- No HATP/WebAuthn architecture touched.
- No runtime/execution capability enabled.
- No task-scope violation — only allowed-file-listed paths touched.

## 26. Recommended next phase

**An independent verification phase of the FGSC-001 v1.0 contract text
itself** — reconstructing this document's own reasoning from primary
sources exactly as 2R.1 did for 2R, attacking each frozen rule (§4's
classification, §7's merge/rewrite rejection, §9's state machine, §14's
five-condition freshness replacement) for gaps or unstated assumptions —
before any implementation phase is authorized. Only after that
independent verification passes should an implementation phase build the
mechanism this contract specifies; that implementation must itself be
independently verified and then proven via the §22 self-hosting
acceptance tests (positive and negative) on a real disposable governed
phase. Only after all of that succeeds should Phase 149O.20L.7O.2P
reconciliation be reconsidered (§19 above).
