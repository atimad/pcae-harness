# Phase 149O.20L.7O.2R.1 — Attribution-Aware Verification Gate Independent Verification

Verification-only phase. Independently reconstructs and attacks the
structured `fast_green` evidence path implemented by
149O.20L.7O.2R (`pcae.core.fast_green_attribution`,
`pcae phase fast-green-attribution`), against the pre-2R checkpoint,
without trusting 2R's own report, tests, or conclusions as proof.

## 1. Entering state

- Pre-2R checkpoint (2Q.1 tip): `0773b21e`.
- 2R commit sequence (oldest→newest): `793a99ca` (implement gate) →
  `96ecd238` (task lifecycle) → `4caf77b4` (persist evidence, 2 runs) →
  `aecdc34a` → `3978add4` → `208932bd` (sync canonical metadata) →
  `3f654eb0` → `bbcb81fd` → `93405826` → `04d58ecf` (2R's own HEAD).
- Production files inspected directly (full read, not summary):
  `src/pcae/core/fast_green_attribution.py` (788 lines),
  `src/pcae/commands/phase_fast_green_attribution.py`, the dispatch
  block and `_apply_derived_correctness`/`_apply_canonical_and_trust`/
  `finalize_phase_report` in `src/pcae/core/phase_reports.py`,
  `src/pcae/core/finalization_transaction.py` (pre-promotion gate),
  `src/pcae/commands/push.py` (`_assess_phase_report_trust`), and the
  frozen 2Q/2Q.1 design docs.

## 2. Scalar-path compatibility

`_fast_green_failure_signal()` diffed byte-for-byte, pre-2R vs current:
**identical**. The only change in `phase_reports.py` is the dispatch
wrapper; any non-`fast_green_attribution.v1`-marked value falls through
unchanged. `is_structured_fast_green()` discriminates solely on an
exact `schema_version` string match, verified directly: a hybrid
payload (structured marker + legacy `failed`/`passed` keys) routes only
to the structured path and is rejected there for field divergence —
never falls through to scalar interpretation. No dual-interpretation
ambiguity exists.

## 3. Structured schema, conservation, adversarial rejection

A fresh, independently-written adversarial suite —
`tests/test_phase_149o_20l_7o_2r_1_independent_verification.py`, 25
tests, not derived from 2R's own tests — exercises
`validate_structured_fast_green` directly, using real throwaway git
repos for commit/baseline mechanics. **25/25 pass.** Confirmed:

- A genuinely valid raw-nonzero/zero-attributable artifact is accepted
  cleanly (happy path proven, not just attack rejection).
- Relabeling a real attributable failure as pre-existing is rejected —
  preexisting/attributable are recomputed from raw node-ID sets, never
  trusted from the artifact's own bucket labels.
- Digest mismatch, artifact-path escape (`../..`, absolute paths),
  missing artifact, stale `candidate_commit`, wrong `baseline_commit`,
  duplicate/omitted raw nodes, malformed environment-exclusion entries,
  exceeding `ENVIRONMENT_EXCLUSION_BOUND=3`, spoofed
  `expected_phase_artifacts` test identity or `pushed_status`, missing
  required keys, and cross-bucket ID overlap are all rejected,
  fail-closed.
- `push.py` touches no `fast_green` field at all; it trusts only
  `compute_final_trust()` over the already-finalized canonical report.
  No second trust boundary exists. `finalize_phase_report` is the sole
  caller reaching `_apply_derived_correctness` — no bypass path found.
- Phase 2P quarantine confirmed untouched by direct inspection of the
  canonical report text and absence of any promotion/reclassification
  artifact for it. Not touched by this phase either.

## 4. Finding 1 — self-certification freshness cycle is real

2Q.1's own frozen design (§10) states: *"If any further commit is made
after evidence capture (including a metadata-only commit), the
evidence is stale... and must be regenerated."* Reconstructing 2R's
real commit sequence (§1 above) shows exactly this: evidence was
generated for candidate `96ecd238`, but embedding it into the canonical
report required six more governed lifecycle commits before the actual
completion commit (`208932bd`) landed, so `candidate_commit` could
never equal the final HEAD used to certify the phase's own completion.
This is a real, structural gap — not implementation inconvenience.

**Operationally contained today**: the only two call sites that treat
`validate_derived_correctness` as *gating*
(`finalization_transaction.py`'s pre-promotion check, and
`_apply_derived_correctness` inside `finalize_phase_report`) both run
before the commit, against the in-memory report, while HEAD is still
literally the candidate — freshness holds at generation time. The only
call site that re-validates a stale historical report against
*current* HEAD is `pcae phase-report consistency`
(`src/pcae/commands/phase_reports.py`), confirmed by direct grep to be
wired into no other gating command (`pcae check`, `pcae health`, push
check) — a standalone read-only diagnostic. So the cycle produces no
false-green anywhere today; it only means the structured path cannot
currently self-certify its own phase's completion. 2R correctly used
the pre-existing scalar+deselection convention for its own
finalization instead (verified: pre-existing, faithfully followed, not
silently normalized into the new structured model).

No existing PCAE checkpoint/report-only-commit/verification-commit
concept was found anywhere in `src/pcae/` or `docs/` (grepped
exhaustively) that already resolves this.

## 5. Finding 2 — baseline/candidate raw content is trusted verbatim

`validate_structured_fast_green` independently recomputes the
*arithmetic* (preexisting = raw ∩ baseline, attributable = raw − all
buckets) and verifies *which commit SHA* is claimed as baseline (via
`derive_phase_entry_baseline`) — but never re-executes pytest against
that baseline commit to verify `baseline_raw_failed`/
`baseline_raw_errors` are true. Directly demonstrated: a hand-forged
artifact that adds a fabricated baseline-failure entry (laundering a
real candidate regression into "pre-existing"), with a correctly
recomputed digest and the correct baseline SHA, passes validation with
zero issues.

This is honestly disclosed in the module's own docstring (an actor
with direct filesystem write access to `.pcae/` could still forge the
artifact — true of every other trust field in this repository's
governance model) and is not a new capability introduced by this
phase. The docstring's framing that it "closes the hand-typed
attribution counts failure mode... by requiring the validator to
recompute independently from raw node-ID sets" is imprecise: it closes
*label*-forgery, not *content*-forgery of the raw sets themselves.
Recommend a documentation-scope clarification in a future pass; not a
novel Blocking regression.

## 6. Other adversarial checks (code-level)

- **Worktree/subprocess safety**: unique `tempfile.mkdtemp` paths,
  `git worktree add --detach` + forced remove, all subprocess calls use
  argv arrays with `shell=False`. No injection surface, no destructive
  prune of user worktrees.
- **Exit codes**: `2` = infrastructure error (`AttributionError`,
  worktree/collection failure), `1` = validation FAIL, `0` = PASS.
  Baseline/candidate collection failure raises before any evidence is
  produced — cannot silently yield a false PASS.
- **Environment exclusion**: a deterministic assertion failure that
  fails again on rerun stays attributable — correct. Weak spot: a
  rerun that *times out* is classified `"error"` → `"divergent_error"`
  → excluded as environment, conflating "flaky" with "a real
  hang/deadlock introduced by candidate code" (a timeout on isolated
  single-node rerun is not proof of non-reproducibility). Non-Blocking;
  single-attempt only, correctly bounded to 3, no repeated-retry
  laundering path exists.
- **Baseline authority**: derived from `git log --reverse` scanning for
  the first commit whose subject line matches `^Phase <id>:` — soft,
  commit-message-convention-based trust, not structurally enforced. An
  early phase commit omitting the prefix would shift the derived
  baseline forward and could launder an earlier regression as
  pre-existing. Consistent with the rest of this repo's phase-identity
  conventions elsewhere; not new to this phase. Non-Blocking.
- **Artifact retention**: content-addressed by SHA-256, no cleanup
  policy (unbounded accumulation). Cosmetic; Observation only. Replay
  is blocked by the freshness check (stale `candidate_commit` always
  rejected once HEAD moves).

## 7. Independent test suite

`tests/test_phase_149o_20l_7o_2r_1_independent_verification.py` — 25
fresh tests, not copied from 2R's suite. All pass.

## 8. Regression

`tests/test_phase_149o_20l_7o_2r_1_independent_verification.py` +
`tests/test_phase_149o_20l_7o_2r_fast_green_attribution.py`: 43 passed.
Targeted push-gate / phase-report-consistency regression subset: 135
passed, 0 failed, 36201 deselected (mechanically-derived deselect
convention, pre-existing). No production code under `src/` was
modified at any point in this phase.

## 9. Verdict

**B — CORE ATTRIBUTION-AWARE FAST GREEN GATE INDEPENDENTLY VERIFIED;
SELF-CERTIFICATION LIFECYCLE REPAIR REQUIRED BEFORE THE STRUCTURED PATH
IS USED TO SELF-CERTIFY A PHASE'S OWN COMPLETION.**

- Scalar path: unchanged (proven byte-identical).
- Machine-produced attribution arithmetic: verified fail-closed against
  20+ independent adversarial attacks.
- Raw-nonzero/zero-attributable acceptance: valid.
- Push integration: no second trust boundary.
- Phase 2P: untouched, still quarantined.
- Finding 2 (raw-content trust boundary): real, precisely
  characterized, consistent with (not novel to) PCAE's existing
  filesystem-trust model — documentation-scope clarification
  recommended, not urgent repair.

## 10. Next phase

A narrow lifecycle-contract repair phase for the self-certification
freshness cycle (§4) — e.g. a governed "report-only commit" allowlist
mechanically restricted to non-test-affecting paths, or an explicit
governed verification-checkpoint concept distinct from final HEAD — so
a phase's finalization commits can follow evidence capture without
invalidating `candidate_commit` freshness. This is its own dedicated
next phase, not folded into 2R.1. Phase 2P reconciliation must not
proceed until this is resolved, since 2P reconciliation depends on
structured self-certification being trustworthy for exactly this
reason.

## No-go confirmations

No Git history rewritten; no commit amended, rebased, or deleted.
No force push. No raw `git push` — only pcae-governed commit/push
commands used.
No change to `_fast_green_failure_signal()` or its call semantics for
any non-structured value — proven byte-for-byte identical.
No weakening of the scalar gate.
No production code under `src/` modified.
No retroactive promotion, push, or reclassification of Phase
149O.20L.7O.2P — untouched, still quarantined.
No HATP/WebAuthn architecture touched.
No runtime/execution capability enabled — Observed / execution_unavailable,
unchanged.
No task-scope violation — only allowed-file-listed files touched
(`pcae check` passed throughout).
