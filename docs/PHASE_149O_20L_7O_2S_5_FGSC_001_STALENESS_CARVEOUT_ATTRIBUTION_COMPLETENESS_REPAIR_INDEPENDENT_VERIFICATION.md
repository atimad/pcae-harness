# Phase 149O.20L.7O.2S.5 — FGSC-001 Staleness Carve-Out Attribution Completeness Repair Independent Verification

Verification-only phase. No production code, FGSC-001, or carried findings
were modified. No real S22.1/S22.2 was executed. Phase 149O.20L.7O.2P
remains untouched.

## 1. True phase entry

- Phase-entry HEAD / current `origin/main`: `4a3b27abae4740f96ee25cab947fe75d03321613`
  (identical — repo was clean/pushed at 2S.5 entry).
- Exact 2S.4 commit range (oldest → newest):
  `a9fb1151` → `5be1b555` → `5b013191` → `df8e3a8e` → `eb624b4f` →
  `b5618a4f` → `4a3b27ab` (7 commits; implementation commit `a9fb1151`,
  remainder are the standard PROJECT_STATUS/task-lifecycle/metadata/report
  ceremony commits).
- Vulnerable pre-2S.4 checkpoint: `b9b83c28653d8068440e345aca796809a0429ec`
  (`a9fb1151^`, the 2S.3 completion commit "NOT VERIFIED (staleness
  carve-out defect)").
- FGSC-001 version: v1.0, FROZEN (unmodified this phase; contract at
  `docs/contracts/FAST_GREEN_SELF_CERTIFICATION_LIFECYCLE_CONTRACT.md`).

## 2. Independent pre-repair reproduction

Built a disposable script (not copied from any 2S.3/2S.4 test) that:
constructs a synthetic git repo, captures real structured Fast Green
evidence via `build_attribution_evidence`/`persist_evidence`, injects one
unclassified regression node into `raw_failed` post-capture (re-signing the
digest), advances HEAD with one ordinary FGSC-allowed finalization commit,
then calls `validate_structured_fast_green`.

Run via `git worktree` checkout of `b9b83c28` with `PYTHONPATH` pointed at
its own `src/`, so the *old* code executes the reproduction:

```
=== OLD (pre-2S.4, b9b83c28) ===
ISSUES: ["structured fast_green evidence is stale — candidate_commit ... != current HEAD ..."]
STALE_ONLY: [the same message]
NON_STALE: []
RESULT: ACCEPTED-AS-STALENESS-ONLY (defect reproduced)

=== NEW (current HEAD) ===
ISSUES: ["structured fast_green attributable_failures does not match the recomputed default set — claimed=[] computed=['tests/test_sample.py::test_hidden_regression']"]
STALE_ONLY: []
NON_STALE: [the attributable-failures issue]
RESULT: REJECTED (regression visible)
```

The exact 2S.3 Blocking scenario independently reproduces against the old
checkpoint (identical mechanism reported: staleness-only issue list despite
a genuine unclassified regression) and does **not** reproduce against
current HEAD.

## 3. 2S.4 production diff (independently reconstructed)

`git diff a9fb1151^ a9fb1151 --stat`: touches only
`src/pcae/core/fast_green_attribution.py` (production), one new doc, and
three test files (2S.1/2S.3 test edits + new 2S.4 suite). Confirmed:

- no `phase_reports.py` change
- no `finalization_transaction.py` change
- no Stage-B change
- no path-classification (`_CLASS_A_PATH_PREFIXES` etc.) change
- no scalar Fast Green (`_fast_green_failure_signal`) change
- no `docs/contracts/**` contract change

The production diff itself is a pure relocation: deletes the freshness
check block from immediately after the digest/inline-evidence checks, and
re-inserts the identical block (only a doc-comment added) immediately
before the function's final `return issues`, after the nonzero-
`attributable_failures` check.

## 4. Root-cause re-derivation — validation ordering

Full early-return audit of `validate_structured_fast_green` at current
HEAD, in execution order:

1. Required-key schema check → return on failure.
2. Provenance shape / artifact_path+digest presence → return on failure.
3. Path-escape check → return on failure.
4. Artifact existence / readability / digest match → return on failure
   (artifact integrity).
5. Inline-vs-persisted field divergence → `if issues: return issues`.
6. Baseline authority (`derive_phase_entry_baseline`): hard error → return;
   soft mismatch → issue appended, **no return** (falls through).
7. Test-selection command equivalence: mismatch → issue appended, no
   return.
8. Baseline/raw list-shape checks → return on type failure.
9. Raw duplicate / raw_failed∩raw_errors overlap → issue appended, no
   return.
10. `excluded_preexisting_failures` recomputation + malformed-entry/
    baseline-mismatch/duplicate checks → return only on type failure;
    content mismatches append and continue.
11. `excluded_environment_failures` recomputation + bound/malformed/
    rerun-commit/duplicate checks → same pattern.
12. `expected_phase_artifacts` recomputation + malformed/wrong-predictor/
    wrong-identity/already-pushed/predicted-value/duplicate checks → same
    pattern.
13. **Checkpoint A** — `if issues: return issues` (end of the bucket-
    validation section, immediately before conservation).
14. Conservation: cross-bucket overlap → issue appended, no return.
15. `attributable_failures` independent recomputation: type failure →
    return; value mismatch → issue appended, no return.
16. Unknown-node-in-buckets check → issue appended, no return.
17. **Checkpoint B** — `if issues: return issues` (immediately after
    attribution/conservation, before the nonzero-attributable check).
18. Nonzero-`attributable_failures` check → issue appended, **no return**
    (deliberately falls through to freshness).
19. **Freshness check (last)** → issue appended if stale; function returns
    `issues` unconditionally at the end.

## 5. Freshness-must-be-last invariant

Every early return in steps 1–12 above precedes Checkpoint A; every return
inside conservation/attribution (step 15's type-failure return) precedes
Checkpoint B; both checkpoints are ordinary `if issues: return issues`
guards. Consequence: **the freshness check at step 19 executes only when
`issues` was empty at both Checkpoint A and Checkpoint B** — i.e. every
schema, artifact-integrity, baseline, command, duplicate/overlap, bucket-
content, conservation, and attribution check above already ran to
completion and found nothing. No early return before Checkpoint A/B can
"hide" behind a subsequently-appended staleness issue, because if such a
return fires, the function exits before the freshness code ever runs and
the returned list contains only that check's own issue (not staleness) —
so the FGSC-001 caller (§6 below) never sees a staleness-only list at all
in that case. This is the required invariant; it is satisfied by
construction, not by inspection of specific test fixtures.

## 6. Issue-list completeness (the key property)

Handoff's required property: *if the returned issue set contains only the
recognized staleness issue, then no hidden non-freshness defect remains
that could change the trust outcome.*

Proof from §5: reaching a return value of exactly
`["structured fast_green evidence is stale ..."]` requires (a) Checkpoint
A found `issues == []`, so every check in steps 1–12 passed; (b) Checkpoint
B found `issues == []`, so conservation and `attributable_failures`
recomputation both passed exactly (`attributable_computed == []`,
`attributable_claimed` matches, no cross-bucket overlap, no unknown nodes);
(c) step 18's nonzero-attributable check therefore added nothing; (d) step
19 is the only step left, and it can only add the one staleness message.
No other code path can append to `issues` between an empty Checkpoint B and
the freshness check. Property holds. Independently confirmed by
`TestSoleStalenessAccepted` and all ten `TestStalenessPlusEachDefectRejected`
cases in the fresh 2S.5 suite (§9 below) — every injected non-freshness
defect surfaces in the returned issue set, never silently absorbed behind
staleness.

## 7. Original vulnerable case — post-repair result

REJECTED. See §2's "NEW" transcript: the independently reconstructed 2S.3
exploit input, run against current HEAD, returns the
`attributable_failures` mismatch issue (non-freshness), not a
staleness-only list. (In this specific reconstruction the returned list
does not also contain the staleness message, because Checkpoint B returns
before step 19 runs — this is expected and still proves fail-closed
semantics: the genuine regression is visible and blocking either way.)

## 8. Valid sole-staleness case — result

PASSES. `TestSoleStalenessAccepted::test_valid_sole_staleness_certifies_finalization_verified`:
an otherwise fully valid, non-tampered artifact whose only condition is one
ordinary finalization commit advancing HEAD past the captured checkpoint
reaches `validate_derived_correctness() == []` and
`report.metadata["fgsc_lifecycle_state"] == "FINALIZATION_VERIFIED"`.
Confirms the repair does not disable FGSC-001's intended self-certification
path.

## 9. Staleness + each other defect — results

All ten cases in `TestStalenessPlusEachDefectRejected`
(`tests/test_phase_149o_20l_7o_2s_5_fgsc_001_staleness_carveout_independent_verification.py`)
REJECT, each with the specific expected issue substring and
`fgsc_lifecycle_state != "FINALIZATION_VERIFIED"`:

| Case | Result |
|---|---|
| staleness + attributable regression | REJECT (`attributable_failures` mismatch) |
| staleness + omitted raw node | REJECT (`attributable_failures` mismatch) |
| staleness + cross-bucket duplicate node | REJECT (`bucket membership overlaps`) |
| staleness + forged pre-existing label | REJECT (`excluded_preexisting_failures does not match`) |
| staleness + count/conservation mismatch | REJECT (`attributable_failures` mismatch) |
| staleness + raw error (collection/setup) node | REJECT (`attributable_failures` mismatch) |
| staleness + environment-exclusion bound abuse | REJECT (`exceeds the bounded policy`); `ENVIRONMENT_EXCLUSION_BOUND` confirmed still `3` |
| staleness + expected-artifact-identity abuse | REJECT (`does not match the closed test identity`) |
| staleness + digest/provenance defect | REJECT (`digest mismatch`) |
| staleness + wrong/non-authoritative baseline | REJECT (`baseline is not authoritative`) |

## 10. Non-FGSC strict staleness

`TestNonFGSCFreshnessStillStrict`: calling `validate_structured_fast_green`
directly (outside the `phase_reports.py` FGSC carve-out wiring) still
reports the staleness issue for a stale-but-otherwise-valid artifact.
Ordering changed; the check itself did not become weaker or conditional.

## 11. Scalar compatibility

`git diff a9fb1151^ a9fb1151 -- src/pcae/core/fast_green_attribution.py`
shows zero lines touching `_fast_green_failure_signal` or any scalar
dispatch code. `tests/test_88n5_fast_green_validation.py` (scalar path,
historical cases) — 100% pass at current HEAD, no changes needed.

## 12. Five-bucket / caller carve-out exactness

Bucket definitions (`preexisting_computed`, `environment_ids`,
`expected_ids`, `attributable_computed = raw_set - all_classified`) are
byte-identical before/after 2S.4 (diff confirms no lines in that region
changed). `phase_reports.py`'s carve-out
(`validate_derived_correctness`) recognizes eligibility via
`issue.startswith("structured fast_green evidence is stale")` — a
**prefix** match, not exact identity. Static scan of every
`issues.append(...)` string literal in `validate_structured_fast_green`
(`TestIssueIdentityNotOverbroad`) confirms exactly one issue-message
template shares that prefix (the freshness check's own message) — the
prefix match is not currently overbroad in practice. **Non-blocking
finding (carried forward, not repaired this phase):** a prefix match is
inherently less robust than a typed/coded issue identity; a future
addition of a differently-worded issue message beginning with the same
text would silently become carve-out-eligible with no test forcing
awareness of that risk. Recommend a typed identity in a future phase; out
of scope for 2S.5 (verification-only, no redesign permitted).

## 13. Stage B / recursion / finalization transaction / consistency / push boundary

- Stage B: `run_stage_b_focused_checks` signature/call site unchanged
  (2S.4 diff does not touch it); re-run via the 2S.1–2S.4 suites (all
  green) and monkeypatched in the 2S.5 suite exactly as in 2S.3/2S.4 — no
  behavior change detected.
- Recursion: call graph `validate_derived_correctness` →
  `validate_structured_fast_green` → (on sole-staleness)
  `check_finalization_delta` → `run_stage_b_focused_checks`; none of these
  call back into `validate_derived_correctness` or finalization. No change
  from 2S.4 (single-file diff confined to
  `validate_structured_fast_green`).
- `finalization_transaction.py`: zero diff since 2S.4;
  `tests/test_finalization_transaction_134e10.py` green.
- Phase-report consistency: unaffected — no diff to the consistency
  diagnostic code.
- Push trust boundary: `git diff` and `tests/test_push.py` (37 tests) both
  confirm `push.py` carries no attribution/FGSC recomputation logic;
  single trust boundary (validated canonical report → push eligibility)
  preserved.

## 14. Path classification / merge-history / lifecycle regressions

`tests/test_phase_149o_20l_7o_2r_1_independent_verification.py` (Class A/B
path classification, merge/history-rewrite/rename/symlink/mode
classification) — full pass, no diff to
`_CLASS_A_PATH_PREFIXES`/`_CLASS_A_EXACT_PATHS` or classification logic
since 2S.4. Eight-state lifecycle representation untouched (no diff to
lifecycle-state code).

## 15. Carried findings (re-examined, not repaired)

N1 (overbroad `docs/contracts/**` digest-binding citation), N2 ("class C"
naming inconsistency), N3 (push-correction-loop termination empirical, not
structurally bounded), and the four 2R.1 findings (raw artifact-content
trust boundary; environment-timeout exclusion weakness; commit-message-
derived baseline authority; artifact retention observation) are all
unaffected — 2S.4's single-file diff does not touch any of the code
regions those findings concern. None worsened by 2S.4.

## 16. HMIC/trust-scope

`src/pcae/core/fast_green_attribution.py` falls under the existing
`_CLASS_A_PATH_PREFIXES = ("src/pcae/", "scripts/", "tests/",
"docs/contracts/")` Class A trusted-source scope (same module, line ~828),
predating 2S.4 by several phases and unmodified by it. No membership-set
evolution required or performed.

## 17. 2S.4 push-reporting consistency

2S.4's canonical `.pcae/phase-completion-report.md` and doc contain no
"push itself deferred" prose (2S.4's own doc explicitly states "no
'Pushed: pushed' / 'push itself deferred' prose mismatch"). Current
`.pcae/phase-completion-metadata.json` for 2S.4:
`governance_results.pcae_push_check == "clean"`,
`pushed_status == "nothing_to_push"`. `git rev-parse HEAD origin/main` at
2S.5 phase-entry: both `4a3b27ab...` — confirmed genuinely pushed, no
stale/contradictory prose found requiring correction.

## 18. 2S.3 Blocking finding — final disposition

**INDEPENDENTLY CONFIRMED CLOSED.** The exact 2S.3 Blocking finding
(staleness-only issue list reachable despite unclassified regression, via
the pre-check-order `if issues: return issues` guard) independently
reproduces against checkpoint `b9b83c28` and does not reproduce against
current HEAD (`4a3b27ab`). The general issue-completeness property (§6) is
proven structurally, not only against the original fixture.

## 19. Test evidence (proportional, per §38 of the handoff)

- Fresh independent 2S.5 suite: 13/13 pass
  (`tests/test_phase_149o_20l_7o_2s_5_fgsc_001_staleness_carveout_independent_verification.py`).
- Existing relevant suites, unmodified, re-run at current HEAD: 2S.1, 2S.2,
  2S.3, 2S.4, 2R.1 (121 tests) + 88N.5 scalar, 2R attribution,
  finalization-transaction 134E.10, push (107 tests) — all pass, 228
  targeted tests total, zero regressions.
- Controlled A/B: §2's old-checkpoint-vs-current-HEAD comparison via git
  worktree + PYTHONPATH swap.
- No attempt made to force a literal-zero full-repository `-m fast_green`
  run (per §38's explicit instruction and 2S.4's own documented sandbox
  unreliability finding, independently not re-litigated this phase).

## 20. Proof of no scope violations

- No production source modified this phase (only this doc, the fresh test
  file, and the standard task-lifecycle/PROJECT_STATUS/CHANGELOG/metadata
  files touched).
- No real S22.1/S22.2 executed.
- Phase 149O.20L.7O.2P: not inspected, referenced, or modified beyond this
  report's citation of its gated status.
- No runtime execution enabled; no Git history rewritten; no force-push;
  no raw `git push` (governed `pcae push` only).

## 21. Verdict

**A — 2S.3 BLOCKING FINDING: INDEPENDENTLY CONFIRMED CLOSED. FGSC REPAIR:
INDEPENDENTLY VERIFIED**, with one non-blocking finding carried forward
(§12: prefix-match issue-identity fragility, not currently exploitable).

FULL NON-FRESHNESS STRUCTURED VALIDATION: COMPLETES BEFORE CARVE-OUT.
SOLE STALENESS: FGSC-CARVE-OUT ELIGIBLE. STALENESS + ANY OTHER VALIDATION
DEFECT: REJECTED. NON-FGSC STRUCTURED FRESHNESS: STRICT. SCALAR PATH:
UNCHANGED. STAGE B: UNCHANGED / FAIL-CLOSED. PHASE 2P: UNCHANGED /
QUARANTINED.

**REAL S22.1/S22.2 SELF-HOSTING MAY PROCEED.**

## 22. Recommended next phase

A dedicated real FGSC S22 self-hosting acceptance phase executing both
S22.1 (positive: a real disposable governed phase completes end-to-end
using structured Fast Green self-certification, no scalar+deselection
fallback) and S22.2 (negative: after verification checkpoint/evidence
capture, introduce one forbidden verification-affecting change and prove
the old checkpoint/evidence is rejected). Only after both pass should
149O.20L.7O.2P reconciliation be considered.
