# Experiment log — Campaign `RHAMP-XTEST-IDENTITY-TRACE/1`, Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R

## Method redesign (this phase)

Predecessor phases used a **continuous single-process execution-time trace**
(Model C): run the whole `tests/` suite in one process, watching
`id(HPACStoreAuthority)`/`id(HumanPrincipalRegistryStore)` after every
teardown. That trace reached ~80/571 files in a 20-minute watchdog window
before being killed, and the predecessor projected ~140 minutes for full
coverage — more than any single phase's 60-minute budget, and **not validly
resumable at file 81 in a new process** (a fresh process does not recreate
whatever cumulative state files 1–80 built up).

This phase redesigned the coverage unit as **Model A: independent
batch-composition probes**. Each unit = one fixed batch of 25 corpus files
run together with the victim (`..._30r_3_4_merged_rhamp_mechanism.py`) from
a **fresh clean process**. Each unit's outcome depends only on its own batch
+ victim, not on any other unit having run first — so units genuinely can be
skipped once checkpointed complete, unlike the predecessor's continuous
trace. Corpus: 761 `tests/test_*.py` files (rebuilt at this phase's `K0`;
grew from the predecessor's reported "~571" over the intervening phases),
761 − 1 (victim) = 760 non-victim files → 31 batches of ≤25 files.
`corpus_digest` and per-batch `unit_id`s are frozen in
`.pcae/evidence/RHAMP_XTEST_CORPUS_1_manifest.json`.

**Inherited coverage: 0/31.** The predecessor's three ad hoc clusters (15
CLTR-authority files, 22 multiprocessing files, an unreconstructable 55-file
"clean_isolated_files.txt" whose exact membership was scratch-only and not
preserved) do not align with these batch boundaries and their precise
membership could not be independently re-verified file-for-file (the
`test_cltr_authority_136a*.py` glob resolves to 23 files today, not the
reported 15; the multiprocessing grep resolves to 23, not 22 — plausibly
predecessor sub-selections, not reconstructible with confidence). Per this
phase's own instruction ("if predecessor evidence cannot support a
particular unit, leave it PENDING"), none of that prior work was imported as
checkpointed coverage. It remains valid, preserved, non-duplicated evidence
(the predecessor's own reports), just not part of this new unit scheme.

## Checkpoint-method verification (no diagnostic budget consumed — local, no pytest)

- **Restart-readability:** checkpoint K1 written, reloaded in a fresh `python3`
  process, `validate_resume()` passed.
- **Corruption-refusal:** a disposable tampered copy (mutated `coverage_count`
  without updating `self_digest`) → `validate_resume()` correctly refused
  (`self_digest mismatch`).
- **Corpus-drift-refusal:** disposable copy with wrong `corpus_digest` →
  refused (`corpus_digest mismatch`).
- **Tracer-drift-refusal:** disposable copy with wrong `tracer_version` →
  refused (`tracer_version mismatch`).
- **Verdict: CHECKPOINT METHOD VERIFIED.**

## Tracer non-interference control (2 invocations, ~7s)

Ran the victim alone without the tracer (`125 passed in 2.86s`) and with the
tracer loaded via `-p rhamp_xtest_tracer` (`125 passed in 2.86s`, 0 identity
deltas recorded). Identical substantive outcome. **Verdict: TRACER VALID
(non-interfering).** Established `VICTIM_BASELINE_IDENTITY_DIGEST` (clean
victim-alone: both classes' `(module, qualname)` stable session-start to
session-finish).

## Aborted first attempt (counted toward budget; driver crash, no checkpoint written)

Invocation with a 600s per-batch subprocess timeout on batch-000 (25 files
including `test_agent.py`, a very large generated test file) hit the
timeout; an unhandled `subprocess.TimeoutExpired` crashed the driver before
any checkpoint write. **~600s of real pytest wall-clock time was consumed
and is counted in this phase's cumulative budget accounting even though no
checkpoint captured it** — the driver was immediately repaired (catch the
timeout, cap future invocations at 240s, record aborted batches as
`INCONCLUSIVE` rather than crash) before any further invocation.

## Batch-composition advancement (26 further invocations, 2942.8s ≈ 49.0 min)

Ran the 31-unit corpus in batch order, victim + 25-file batch per invocation,
`-p rhamp_xtest_tracer`, single process, no xdist, 240s timeout per
invocation, checkpointing after every unit. Full per-invocation record
(command, duration, outcome tail, identity-delta flag) in
`.pcae/evidence/RHAMP_XTEST_INVOCATION_LOG.jsonl`; full tracer observations
in `.pcae/evidence/RHAMP_XTEST_TRACE_OBSERVATIONS.json`.

- **18/31 batches: CLEAN.** id() of both watched classes stable
  session-start→session-finish; no victim-module failure. (Each batch does
  show dozens to low-hundreds of *unrelated* failures — consistent with the
  predecessor's already-established, separately-classified
  HISTORICAL-MOVING-AUTHORITY / fixed-baseline-vs-moving-HEAD defect class
  that affects roughly a fifth to a third of this repository's tests
  independent of RHAMP; none of the 18 clean batches' failures are in the
  victim module and none show an identity delta.)
- **7/31 batches: INCONCLUSIVE (timeout).** Batches 0, 4, 7, 11, 12, 17, 25
  did not finish inside the 240s per-invocation cap — too many/slow tests
  in that specific 25-file grouping to characterize this phase. Not
  attributed either way; pending re-run (smaller sub-batch or longer cap).
- **1/31 batch: batch-013 — RELEVANT DELTA OBSERVED.** Files: `test_phase_146g_chgr_schema_envelope_implementation.py`,
  `test_phase_146h1_governance_verification_schema_version_repair.py`,
  `test_phase_146h3_confirmation_binding_verification_repair.py`,
  `test_phase_146l_chgr_cross_artifact_digest_binding_and_duplicate_match_verification_repair.py`,
  `test_phase_147g_authority_evaluation.py`,
  `test_phase_147h_authority_evaluation_independent_verification.py`,
  `test_phase_147m_authority_evaluation_integration.py`,
  `test_phase_147n_authority_evaluation_integration_independent_verification.py`,
  `test_phase_147o1_authority_evaluation_production_wiring.py`,
  `test_phase_147o2_authority_evaluation_production_wiring_independent_verification.py`,
  `test_phase_147p_authority_evaluation_persistence_boundary_hardening.py`,
  `test_phase_147q_authority_evaluation_persistence_boundary_independent_verification.py`,
  `test_phase_148c10_pbpc_v12_independent_verification.py`,
  `test_phase_148c7_permission_broker_policy_applicability_independent_verification.py`,
  `test_phase_148c8_permission_broker_production_consumption_b1_reevaluation.py`,
  `test_phase_148f_permission_broker_production_consumption_independent_verification.py`,
  `test_phase_148g2_permission_broker_operational_hardening_independent_verification.py`,
  `test_phase_149d_rwmpc_contract_independent_verification.py`,
  `test_phase_149g_rwmpc_wave1_independent_verification.py`,
  `test_phase_149j_rollback_approval_evidence_contract_independent_verification.py`,
  `test_phase_149m_rollback_approval_evidence_implementation_independent_verification.py`,
  `test_phase_149n_rollback_approval_evidence_canonical_provenance_hardening.py`,
  `test_phase_149o_10_1_hsce_001_narrow_contract_repair.py`,
  `test_phase_149o_10_2_hsce_001_atomic_no_clobber_reverification.py`,
  `test_phase_149o_10_hatp_signing_ceremony_evidence_store_contract_independent_verification.py`,
  + victim. Outcome: `37 failed, 930 passed, 79 errors in 41.15s`, including
  **2 victim-module `ERROR`s** (`test_94_counter_missing_fails_closed_not_zero`,
  `test_95_assurance_class_of_enrolled_records_is_production`) — the first
  time in this entire campaign the victim itself has shown any non-pass
  outcome. The tracer recorded `id(HPACStoreAuthority)` and
  `id(HumanPrincipalRegistryStore)` **both different** between session-start
  and session-finish, with `__module__`/`__qualname__` strings unchanged —
  the classic signature of a class object being replaced by a
  same-named-but-distinct object (e.g. via reload), which is exactly the
  failure mode a `isinstance(root, HPACStoreAuthority)` check would
  misbehave under. **This is unique**: all other 18 completed batches (and
  the earlier victim-alone control) show `id()` stable start-to-finish for
  both classes; batch-013 is the only one of 19 batches with a complete
  trace pair to show drift.

## Stop condition

**Legitimate stop condition: B — diagnostic budget exhausted.** Accounting
(pytest invocations that actually ran, per section-43-style tally): 2
tracer-validation controls + 1 aborted/crashed 600s timeout + 26 batch
invocations = **29 of the 30-invocation cap**; cumulative pytest wall-clock
time ≈ 7s + 600s + 2942.8s ≈ **3550s ≈ 59.2 of the 60-minute cap**. Both caps
are effectively exhausted; no further pytest invocation was run after
discovering and recording the batch-013 finding (confirming the finding
required only reading the already-written trace files for all 26 completed
invocations, not a new invocation — 0 additional budget spent on that
analysis).

## Why root cause remains UNRESOLVED despite the batch-013 finding

Section 31's causal-proof bar (A victim-alone clean / B trigger+victim
reproduces / C trigger removed clean / D fresh-process repeat) is **not
met**: no victim-alone-at-this-commit-with-id()-tracking control was run
*after* the batch-013 finding to re-confirm baseline stability under
identical conditions; no bisection within batch-013's 25 files was
performed to isolate which specific file(s) trigger the drift; no
trigger-removal control; no fresh-process repeat of the exact batch-013
composition. batch-013 is strong, novel, **evidence-motivated correlation**
— the single highest-priority candidate composition for a follow-on bounded
causal-isolation phase — not yet a proven cause.

## Process accounting

No diagnostic subprocess left running: `ps aux | grep -i pytest` (post-run)
returns nothing; the driver process (`run_campaign.py`) exited cleanly after
the 26th invocation and its exit was observed before this report was
written.

## Phase 149O...1R.1R.1R (batch-013 causal isolation) -- 14 invocations, ~171.4s

Continuation of the SAME campaign/corpus/checkpoint chain (no reset). Fresh
budget for this phase: 30 invocations / 60 minutes; used 14 invocations /
~171.4s (~2.9 min) -- stopped voluntarily at legitimate stop condition A
(root cause identified AND reachability adjudicated), not by exhaustion.

Bisection path (all against the frozen victim
`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_3_4_merged_rhamp_mechanism.py`,
single process, `-p rhamp_xtest_tracer2` -- a reconstructed tracer, the
predecessor's own tracer script having been scratch-only like its other
ephemeral driver code; same `tracer_version=1` semantics, `id()`/module/
qualname of `HPACStoreAuthority` and `HumanPrincipalRegistryStore` at
collection-finish vs session-finish):

1. Victim alone: 125 passed -- baseline CLEAN (control A).
2. Full batch-013 (25 files + victim): 36 failed, 931 passed, 79 errors,
   id() drift both classes -- REPRODUCED (vs. predecessor's 37/930/79;
   1-test difference attributable to the separately-classified HISTORICAL-
   MOVING-AUTHORITY defect class, not this signal).
3. First half (files 1-13 + victim): reproduces, 79 errors, id() drift.
4. First 6 of that half (146g/146h1/146h3/146l/147g/147h + victim):
   reproduces, 79 errors.
5. 146g+146h1+146h3 + victim: 177 passed -- CLEAN.
6. 146l+147g+147h + victim: 5 failed, 269 passed, 79 errors, id() drift --
   REPRODUCES.
7. 146l alone + victim: 170 passed -- CLEAN.
8. 147g alone + victim: 218 passed -- CLEAN.
9. **147h alone + victim: 5 failed, 131 passed, 79 errors, id() drift --
   REPRODUCES (file-level minimal reproducer).**
10. 147h + victim, fresh process repeat: identical (5 failed, 131 passed,
    79 errors) -- control D.
11. Single node
    `test_phase_147h_authority_evaluation_independent_verification.py::TestForbiddenDependenciesIndependent::test_no_forbidden_root_is_importable_transitively_via_authority_evaluation_alone`
    alone + victim: 5 failed, 42 passed, 79 errors, id() drift -- REPRODUCES
    (node-level minimal reproducer).
12. 147h file with that one node `--deselect`ed + victim: 214 passed, 1
    deselected, id() stable -- CLEAN (control C, trigger-removal).
13. Bounded clean-context band (Gate5 x2, Gate9 x4, hpac_verifier x4,
    merged-RHAMP-IV, protected-presentation-real-assurance-IV, PAWA v1.1
    contract-freeze-IV, PAWA writer-anchor-slice1, PAWA writer-capability-
    integrity-IV -- 15 files, fresh process, no batch-013 files present):
    700 passed, 2 failed (the pre-existing, previously-adjudicated
    `test_object_dunder_new_bypasses_trusted_construction_seal` /
    `test_forged_via_object_new_would_report_real_runtime_eligible` --
    "NONBLOCKING THROUGH ACTUAL CONSUMPTION PATH", unchanged), id() stable.
14. Configured-agent-identity-threading-repair IV suite (bounded band):
    35 passed, 3 skipped, 3 failed -- all 3 failures are pre-existing
    point-in-time guards (`test_iv_entry_sha_is_current_head` compares
    against a frozen historical HEAD; the other two raise `PermissionError`
    reading `/Library/Application Support/PCAE/HPAC/protected-root/.authority/*`
    in this execution context rather than returning a definite pass/fail --
    see F-5 hold reasoning below), unrelated to the identity-drift signal.

### Root cause: IDENTIFIED

`tests/test_phase_147h_authority_evaluation_independent_verification.py`
lines 780-791
(`TestForbiddenDependenciesIndependent::test_no_forbidden_root_is_importable_transitively_via_authority_evaluation_alone`)
deletes every `sys.modules` entry matching `pcae.authority_evaluation*` OR
any of `_FORBIDDEN_IMPORT_ROOTS` (line 732-742) -- which includes the
literal string `"pcae.core"` -- then calls
`importlib.import_module("pcae.authority_evaluation")`. This deletes
`pcae.core.hpac_foundation` and `pcae.core.human_principal_registry` from
`sys.modules` without invalidating references other already-imported code
holds to the OLD class objects. A subsequent fresh import (triggered later
by the victim) constructs NEW module/class objects with identical
`__module__`/`__qualname__` but a distinct `id()` -- exactly the drift the
tracer observed. **Mechanism: DUPLICATE MODULE IMPORT / STALE REFERENCE.**
Full four-way causal proof (A/B/C/D) in invocations 1, 9, 12, 10 above.

**Uniqueness (repository-wide):** `grep -rl "del sys.modules\[" tests/`
finds 6 files total. The other 5 use unique synthetic module names (3 HATP
files) or scope to `pcae.cltr.authority`/`pcae.authority_evaluation` only
(1 cltr file, this file's own 2 sibling tests) -- none touch `pcae.core`.
Zero occurrences of `del sys.modules`/`importlib.reload` in `src/pcae`.
`scripts/hpac_protected_presentation_admin.py` and
`scripts/hpac_protected_root_admin.py` contain no `sys.modules`
manipulation. **Contamination stage: TEST-EXECUTION. Location: TEST-HARNESS
ONLY** -- this specific causal defect fully explains the batch-013 signal
and cannot occur via any supported production/PPA-registration code path;
per governed item 23, the remaining 5 never-attempted + 7 inconclusive
batches were not scanned this phase (their own failure counts are already
independently attributed to the separately-classified HISTORICAL-MOVING-
AUTHORITY defect class, not this identity-drift signal, and no batch besides
013 showed the signal among the 19 with complete trace pairs).

### F-5 EXECUTION HOLD: REMAINS (narrow reason)

11 of 12 governed clearance criteria (item 33) are satisfied by the evidence
above. The blocker is criterion 11 (no current generation-1 invariant
violation): `test_host_protected_root_generation_and_helper_digest_unchanged`
and `test_ppa_current_generation_and_installation_absent_on_host` both threw
`PermissionError` on `.stat()` of
`/Library/Application Support/PCAE/HPAC/protected-root/.authority/*` in this
diagnostic phase's own process/user context, rather than returning a
definite pass -- so this phase cannot positively confirm the host's
generation-1 / PPA-absent state. Per item 34 ("relevant verification remains
unreliable"), the hold REMAINS pending exactly that one narrow re-check
under adequate filesystem permissions; no further contamination-campaign
diagnostic work is required first.

### Stop condition

**A -- root cause identified and reachability adjudicated** (item 60).
Diagnostic budget used this phase: 14/30 invocations, ~171s/3600s -- stopped
voluntarily, not by exhaustion.
