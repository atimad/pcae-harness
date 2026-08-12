# Phase 149O.20J.3 — Class-B Full Ancestor-Chain Verification Narrow Repair

**Status:** Repair complete. **NARROW DEFECT REPAIR ONLY** — repairs
exactly one shared primitive (`_ancestor_chain_safe`) in
`src/pcae/core/hatp_class_b_topology_verifier.py`; no HMIC source-scope
evolution; no Class-B provisioning; no readiness/certification/
activation change; verifier source remains outside HMIC's frozen
25-file identity; `COMPLIANT`/`NON_COMPLIANT` remain diagnostic-only.
Independent verification (149O.20J.4) is required before any HMIC
source-scope contract evolution (149O.20K) may begin.

## 0. Baseline

Phase entry is 149O.20J.2's own exit state: repo clean, `origin/
main..HEAD = 0`, commits `66415780`, `ac98ddeb`, `8f12b998`,
`e0ae7367`, `7503ecac`, pushed. Confirmed via `pcae health`, `pcae
check`, `pcae status coherence`, `pcae doctor task-memory`, `pcae push
check`, `pcae runtime inspect`, `pcae notify status`, `pcae phase-report
show --latest`, `pcae phase-report reconcile --phase-id 149O.20J.2`:
health/check/coherence all pass; runtime `Observed / observe /
unavailable`; canonical report confirms 149O.20J.2 complete
(`report completeness: complete`) and recommends 149O.20K next (this
phase, 149O.20J.3, was separately requested to intervene first on
149O.20J.2's own disclosed ancestor-chain observation before HMIC
source-scope evolution proceeds); reconciliation reports `status:
reconciled`, `mutation: none (inspection only)`. `pcae doctor
task-memory` shows the same pre-existing, unrelated
`tasks/done/`-vs-`tasks/DONE.md` bookkeeping warnings carried forward
across many prior phases — not new to this phase and not blocking.

J-1 (.pth executable-import tab-form), J-2 (effective-GID omission),
and J-3 (trusted-Git ACL blindness) are all independently confirmed
closed by 149O.20J.2 and are **not reopened** by this phase.

## 1. Blocking Finding: B-149O.20J.2-1

149O.20J.2 §5 independently re-confirmed (and 149O.20J's own frozen
test suite had already, separately, disclosed) that the shared
`_ancestor_chain_safe` primitive stops its upward ancestor walk at the
**first** ancestor directory proven non-writable and never examines any
ancestor above that point. Concretely: for a path
`/authority/grandparent/parent/state`, if `state` and `parent` are
non-agent-writable but `grandparent` is agent-writable, the primitive
returns `safe=True` — `grandparent` is never inspected once `parent` is
judged safe. This is assigned finding ID **B-149O.20J.2-1**.

**Security consequence, re-derived from HBDC-001 §11 (not merely
accepted from 149O.20J.2's prose):** removing or renaming the directory
entry naming a directory requires write access on that entry's
*containing* directory, not on the entry itself. An agent that can
write `grandparent` can therefore rename, delete, or replace `parent`'s
directory entry outright — regardless of `parent`'s own mode bits,
regardless of how deeply "safe" `parent` and everything beneath it
look. The early-stop design's implicit assumption — that a
proven-non-writable ancestor forms a permanent "wall" the agent cannot
get through — is false. This directly undermines HBDC-REQ-017/020 and
CBD-3 (Protected Root redirection resistance) and the identical
Attack-Matrix row 4 (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.
md` §21).

This finding is **Blocking** for progression to HMIC source-scope
binding (149O.20K), per the governing prompt for this phase. Current
production remains fail-closed throughout regardless of this finding's
disposition: verifier source remains outside HMIC identity; production
authority consumers remain zero; `COMPLIANT` remains non-authoritative;
Class-B remains unprovisioned.

## 2. Historical Defect Reproduction

Reproduced first as an ad hoc script against the live pre-repair source
(commit `8429765d`, 149O.20J.2's own close-idle commit — the exact
parent of this phase's repair), then formalized as
`tests/test_phase_149o_20j_3_class_b_full_ancestor_chain_verification_
narrow_repair.py::test_historical_source_stops_at_first_safe_ancestor`,
which extracts (via `ast`, not a hand-copied inline rewrite) the exact
pre-repair `_ancestor_chain_safe` function node from
`git show 8429765d:src/pcae/core/hatp_class_b_topology_verifier.py` and
executes it directly against a `grandparent(agent-writable)/parent(0o500)
/state(0o500)` fixture with a stubbed deterministic ACL result:

```
safe = True
diagnostics = ('ancestor_boundary:.../grandparent/parent',)
```

Confirmed: the walk stopped the instant `parent` was proven safe. The
diagnostics tuple contains exactly one entry — `grandparent` (agent-
writable) was never inspected at all. **Historical early-stop defect
reproduced: YES.**

## 3. HBDC Requirement Reconstruction

**HBDC-REQ-017** (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`
§11): *"Every ancestor directory of Protected Root, up to the point the
agent principal has no write access at all, SHALL be non-agent-
writable. Protected-child ownership is insufficient on its own: an
agent that can write a writable parent directory can rename or replace
the directory entry naming Protected Root even without write access to
Protected Root's own bytes. This requirement closes that channel
jointly with HBDC-REQ-013..016."*

**HBDC-REQ-020** (§11): *"An implementation SHALL treat 'the agent
principal can delete or rename the directory entry naming an
authority-bearing file, even without write access to that file's own
bytes' as a compliance failure equivalent to a direct write. This is
satisfied jointly by HBDC-REQ-017 (parent-path protection) and is not
separately re-derivable from file-level mode bits alone."*

149O.20J.2 §5 itself already posed the interpretive question this
phase resolves: is HBDC-REQ-017's "up to the point the agent principal
has no write access at all" wording best read as (a) "stop at the
first non-writable ancestor" (the pre-repair implementation), or (b)
"every ancestor must be non-writable, all the way to a true root
boundary" (the stricter reading)? 149O.20J.2 §5 already identified the
correct answer without adopting it: *"removing/renaming a directory
entry requires write on its containing directory, not on the entry
itself"* — which is exactly reading (b). Reading (a) is refuted by its
own rationale: a "safe boundary" ancestor is only safe against direct
mutation of its own bytes; it offers no protection against its own
containing directory being agent-writable. **This phase adopts reading
(b): every ancestor, not merely the nearest one, must be proven
non-writable.**

## 4. Trust-Boundary Derivation

HBDC-001's text names no intermediate admin-owned trust anchor between
Protected Root and the filesystem root — Protected Root itself resolves
to a fixed, platform-keyed absolute path (`/etc/pcae/hatp/trust-store`
on Linux, `/Library/Application Support/PCAE/HATP/trust-store` on
macOS; HBDC-REQ-011), whose own ancestors (`/etc`, `/Library`,
`/Library/Application Support`, `/`) are ordinary admin-owned system
directories in any real deployment. `docs/PHASE_149O_20H_CLASS_B_
DEPLOYMENT_VERIFIER_MODEL_A_ENVIRONMENT_LOCK_IMPLEMENTATION_PLAN.md`
§11's original design text explicitly proposed the early-stop rule
("the walk terminates the first time a non-writable ancestor is found
... it does not need to prove every ancestor up to `/` is non-writable")
— this phase determines that rationale was a design error in 149O.20H
itself (not merely an implementation slip), refuted by the same
directory-entry-replacement mechanics HBDC-REQ-017's own text invokes.

**Boundary independently derived: YES.** The only trust boundary
HBDC-REQ-017's text supports without inventing an unwritten anchor is
the actual filesystem root — the walk continues, inspecting every
ancestor, until `path.parent == path` (the OS-level root). No
intermediate designated trust anchor exists in HBDC-001, 149O.20A, or
149O.20H's Protected Root topology to stop at instead.

## 5. Historical Stop Rule vs. Repaired Stop Rule

**Historical (defective):** stop at the first ancestor proven
non-writable → report `safe=True` immediately, never inspecting any
ancestor above it.

**Repaired:** inspect every ancestor from `start.parent` up to the
filesystem root. A `write is False` (locally safe) result **never**
short-circuits the walk — it is recorded as an `ancestor_safe:` entry
and the walk continues to the parent. The walk still stops immediately
(fail-fast, not fail-slow) on:
- a proven-writable ancestor → `False` (`NON_COMPLIANT`), or
- a symlinked ancestor → `False` (`NON_COMPLIANT`), or
- the loop-guard (`>2048` iterations) being exceeded → `None`
  (`INDETERMINATE`), fail-closed against a pathological/cyclic path.

Only once the walk reaches the actual filesystem root (`parent ==
current`) with no writable/symlinked/indeterminate ancestor found does
it return `True`.

## 6. Repair Implementation

`src/pcae/core/hatp_class_b_topology_verifier.py::_ancestor_chain_safe`
— the only production change this phase makes:

- Removed the early `return True, ...` on a locally-safe (`write is
  False`) result; replaced with `diagnostics.append("ancestor_safe:
  ...")` and continued the loop.
- Added a `saw_indeterminate` flag: an indeterminate ancestor
  (`write is None`, e.g. ACL tooling unavailable) no longer aborts the
  walk either — it is recorded and the walk continues, but the overall
  result is forced to `None` (never `True`) if any ancestor along the
  full chain was indeterminate, preserving fail-closed semantics for
  partial evidence (HBDC-REQ-053).
- The loop-guard-exceeded path now returns `None` (indeterminate,
  fail-closed) instead of falling through to the old "diagnostics
  non-empty → `None`, else → `True`" tail logic, which is no longer
  reachable in its old form since `diagnostics` is now always
  non-empty by construction.
- No change to symlink handling, ACL/group/mode-bit effective-access
  logic, `_effective_write_access`, `_resolve_trusted_executable`, or
  any other function — the repair is confined to the single loop
  control-flow defect in `_ancestor_chain_safe`.

No other function in `hatp_class_b_topology_verifier.py` was modified.
`hatp_environment_lock_verifier.py` and `hatp_class_b_conformance.py`
are byte-unchanged (confirmed: §11 below).

## 7. Immediate Parent (Regression, Unchanged)

An agent-writable immediate parent still rejects unconditionally —
`test_live_immediate_writable_parent_still_rejected`. **Immediate
writable parent rejected: YES** (unchanged from pre-repair).

## 8. Deep-Ancestor / Grandparent Attack (Decisive New Case)

`test_live_deep_ancestor_writable_grandparent_rejected`: `state`
(0o500) → `parent` (0o500, proven safe) → `grandparent` (0o700,
agent-writable). Repaired result: `safe=False`, diagnostics contain
both `ancestor_safe:<parent>` and `ancestor_writable:<grandparent>`.
**Safe parent + writable grandparent rejected: YES.**

## 9. Multi-Level Matrix

`test_live_multi_level_matrix_every_writable_level_rejected`: a 5-level
nested chain (`l1/l2/l3/l4/l5/state`); each level parametrized in turn
as the sole writable ancestor. **Every one of the 5 levels
independently rejects**, each producing an `ancestor_writable:<that
level>` diagnostic. **All relevant ancestor levels individually
tested: YES.**

## 10. Safe Full Chain (Positive Case)

`test_live_safe_full_chain_passes` and
`test_live_walk_reaches_filesystem_root_marker_on_full_safe_chain`:
every constructed ancestor non-writable, with everything above the
fixture's own `tmp_path` deterministically stubbed safe (representing
an admin-controlled boundary the way Protected Root's real ancestors
are admin-owned in production — `tmp_path` itself is unavoidably agent-
owned/writable on any real test host, which is why a genuine full-depth
positive case cannot rely on the real filesystem above it). Result:
`safe=True`, diagnostics end with the `ancestor_walk_reached_
filesystem_root` sentinel. **Safe full chain passes: YES** — the repair
does not make the verifier permanently fail-closed.

## 11. ACL-Only and Effective-GID-Only Higher-Ancestor Authority

- `test_live_acl_only_higher_ancestor_write_rejected`: mode bits safe
  at every level; `grandparent` grants write only via a stubbed ACL
  result. **ACL-only higher-ancestor write rejected: YES.**
- `test_live_effective_gid_only_higher_ancestor_write_rejected` and
  `test_live_current_agent_identity_folds_effective_gid_end_to_end`:
  `grandparent` group-writable with its gid reachable only via the
  independent `os.getegid()` fold-in (J-2 semantics), never via
  `os.getgroups()` supplementary membership alone; sanity-checked that
  omitting the fold-in makes the grant invisible, then confirmed
  including it rejects. **Effective-GID-only higher-ancestor write
  rejected: YES.** This also proves J-2's repair and this phase's
  ancestor-walk repair compose correctly end-to-end, not merely in
  isolation.

## 12. Symlink and Error Fail-Closed Higher-Ancestor Handling

- `test_live_symlinked_higher_ancestor_rejected`: a symlinked
  grandparent-level directory rejects with `ancestor_symlink` in
  diagnostics. **Symlinked higher ancestor rejected: YES.**
- `test_live_inspection_error_at_higher_ancestor_fails_closed`: an
  injected `OSError` during a higher ancestor's inspection is never
  interpreted as safe — the public `_check_ancestor_chain` check
  (wrapped by `_safe_check`) reports `satisfied=False`. **Inspection
  error at higher ancestor fails closed: YES.**
- `test_live_indeterminate_higher_ancestor_never_reported_safe`: an ACL
  tool returning `None` (unavailable) at a higher ancestor forces the
  overall result to `None` (indeterminate), never `True`.

## 13. Boundary Verification

`test_boundary_is_not_arbitrary_walk_always_continues_past_safe_
ancestor` statically confirms (via `ast`) that the repaired function's
`write is None / else:` branch — the locally-safe path — contains no
`Return` statement; the only `Return`s inside the loop body correspond
to a proven-unsafe ancestor or the guard-exceeded fail-closed path.
Combined with §10's positive test proving the walk does reach and
correctly report the filesystem root, and §8/§9 proving it does not
stop early: **stop boundary is not arbitrary; walk does not stop
earlier than the filesystem root; walk does not extend above it
(there is nothing above `/` to extend into).**

## 14. Trusted-Git and Protected-Root Equivalence

`_resolve_trusted_executable_with_effective_access` (used for trusted-
Git resolution, HBDC-REQ-038) and `_check_ancestor_chain` (used for
Protected Root, HBDC-REQ-017) both call the exact same
`_ancestor_chain_safe` symbol — confirmed by source inspection
(`test_git_and_protected_root_use_identical_ancestor_walk_function`),
not merely by convention. No divergent Git-only or Protected-Root-only
walker was introduced. Live tests confirm both call sites reject a deep
writable ancestor identically:
`test_git_deep_ancestor_writable_grandparent_rejected_after_repair` and
`test_protected_root_deep_ancestor_writable_grandparent_rejected`.
**Git uses repaired full-chain semantics: YES. Protected Root uses
repaired full-chain semantics: YES. Git/topology ancestor semantics
equivalent: YES** (by construction — one shared primitive).

## 15. Now-Superseded Historical Assertions (Not Rewritten)

Mirroring 149O.20J.1's own precedent for its now-superseded `getegid`-
gap-confirmation assertion, this phase does **not** edit the two
pre-existing test assertions that documented the early-stop design as
intended behavior — they remain historical evidence and are expected
to fail post-repair, not silently rewritten:

- `tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_
  environment_lock_independent_implementation_verification.py::
  test_deep_ancestor_writable_beyond_immediate_parent_is_caught`
  (asserted `safe is True` for the exact grandparent-writable case this
  phase now rejects).
- `tests/test_phase_149o_20j_2_class_b_deployment_verifier_narrow_
  defect_repair_independent_verification.py::
  test_git_deep_ancestor_acl_only_grant_bounded_by_first_safe_boundary`
  (asserted `resolved is not None` for the identical Git-resolution
  case).

Both are now correctly re-proven, with matching-but-corrected
assertions, in the new 149O.20J.3 test module (§8, §14 above).

The one test file this phase *does* modify beyond the new module and
production source is `tests/test_phase_149o_20i_hatp_class_b_topology_
verifier.py::test_ancestor_chain_safe_boundary` — 149O.20I's own
first-party unit test for the primitive, not a later phase's
independent-verification snapshot. Its original fixture asserted
`safe=True` for a chain whose safe boundary sat directly under
`tmp_path` — which, under the repaired full-chain walk, would now
(correctly, but spuriously for the *test's own intent*) also inspect
`tmp_path` itself, which is unavoidably agent-owned/writable on any
real test host. The test is updated to stub the region outside its own
constructed fixture as a deterministic admin-controlled boundary (the
same technique used throughout the new 149O.20J.3 module), while
retaining its original positive assertion (`safe is True`) for the
fixture's own constructed levels — this is a like-for-like fix to keep
the test *meaningful* under the corrected semantics, not a hand-edit of
its result.

## 16. J-1 / J-2 / J-3 Regression

- **J-1** (.pth tab-form): `test_pth_line_classification_unaffected_by_
  ancestor_repair` — `hatp_environment_lock_verifier.py` byte-unchanged
  (§17). **J-1 remains closed: YES.**
- **J-2** (effective-GID): `test_effective_gid_fold_in_unaffected_by_
  ancestor_repair` — `_current_agent_identity` still folds
  `os.getegid()` independently of `os.getgroups()`. **J-2 remains
  closed: YES.**
- **J-3** (trusted-Git ACL): `test_trusted_git_acl_awareness_
  unaffected_by_ancestor_repair` — `_resolve_trusted_executable_with_
  effective_access` still applies ACL-inclusive effective-access
  checking to the resolved executable itself. **J-3 remains closed:
  YES.**

## 17. Aggregator / Environment-Verifier Stability

`test_aggregator_module_unchanged` and
`test_environment_lock_verifier_unchanged` confirm via `git diff
--name-only` that `hatp_class_b_conformance.py` and
`hatp_environment_lock_verifier.py` are untouched by this phase.
**Aggregator changed: NO. Environment verifier changed: NO.**

## 18. Read-Only Guarantee

`test_read_only_no_mutation_around_ancestor_walk` snapshots mode bits
on the fixture directories before and after `_ancestor_chain_safe`
runs and confirms no change; `test_module_source_still_contains_no_
mutation_call` re-runs the module's own static forbidden-mutation-
attribute scan (`mkdir`, `chmod`, `chown`, `unlink`, `rename`,
`symlink`, `link`, `write_bytes`, etc.) against the repaired source and
confirms it still finds none.

## 19. Zero Authority Consumers / HMIC Non-Binding

`test_zero_production_consumers_of_topology_verifier`: a fresh
repository-wide `grep -rl` for `hatp_class_b_topology_verifier` under
`src/pcae/` finds only the three 149O.20I/J modules themselves — zero
external production consumers.
`test_verifier_source_not_in_hmic_frozen_scope`: `hatp_mandatory_
certification._FROZEN_AUTHORITY_BEARING_FILES` still has exactly 25
entries and names none of the three Class-B verifier modules.
Independently re-confirmed outside the test suite via direct
interpreter invocation (`len(_FROZEN_AUTHORITY_BEARING_FILES) == 25`,
`class_b in scope: False`, `env_lock in scope: False`).

## 20. Status Vocabulary

`test_status_vocabulary_unchanged` confirms
`ClassBConformanceStatus`'s six-member closed vocabulary is unchanged.
**Status vocabulary changed: NO.**

## 21. Real-Host Result and Non-Mutation

Direct interpreter invocation of `verify_class_b_topology_
conformance()` on this real host returns `ClassBConformanceStatus.
NON_COMPLIANT` (Protected Root absent — not provisioned). Confirmed
post-invocation: repo git status unaffected by the call itself (working
tree state is this phase's own source/test edits only, unchanged by
running the verifier); Protected Root remains absent; no certification,
binding, revocation, Cutover Record, or activation state exists or was
created; environment (interpreter, venv, `PYTHONPATH`) unchanged.

## 22. Test Suite

New module: `tests/test_phase_149o_20j_3_class_b_full_ancestor_chain_
verification_narrow_repair.py` — 27 tests, all passing, covering §2–§21
above (historical reproduction, live grandparent/multi-level/safe-full-
chain, ACL-only/effective-GID-only higher-ancestor, symlink/error
fail-closed, boundary proof, Git/Protected-Root equivalence, read-only
guarantee, J-1/J-2/J-3 regression, aggregator/environment-verifier
stability, zero-consumer/HMIC-non-binding, status vocabulary).

Modified: `tests/test_phase_149o_20i_hatp_class_b_topology_verifier.py`
(one test, §15 above — like-for-like fix, not a semantic loosening).

Left unmodified (historical evidence, expected to fail post-repair,
per §15): `tests/test_phase_149o_20j_class_b_deployment_verifier_
model_a_environment_lock_independent_implementation_verification.py`,
`tests/test_phase_149o_20j_2_class_b_deployment_verifier_narrow_
defect_repair_independent_verification.py`.

## 23. Fast Green

`python -m pytest -m "fast_green" -n auto -ra --durations=50`:
baseline (pre-repair, `git stash`) — 70 failed / 6745 passed / 5
skipped / 1 collection error (missing `fido2` dependency, pre-existing,
unrelated). Post-repair — 81 failed / 6761 passed / 5 skipped / 1
collection error. Delta independently classified via sorted `diff`
between the two `FAILED` line lists:

- **6 dirty-working-tree self-checks** (e.g. `test_no_src_pcae_files_
  dirty_in_working_tree`, `test_git_status_touches_no_src_pcae_or_
  contract_file`) newly failing solely because this phase's own
  uncommitted production/test edits leave `src/pcae/` dirty at test-run
  time — these are transient artifacts of running the suite pre-commit,
  not logic regressions, and clear once this phase's changes are
  committed.
- **2 intentionally-superseded historical assertions** (§15): the old
  `test_deep_ancestor_writable_beyond_immediate_parent_is_caught` and
  `test_git_deep_ancestor_acl_only_grant_bounded_by_first_safe_
  boundary`, deliberately left asserting the pre-repair behavior.
- **1 unrelated flaky test-name flip** in `test_backend_cli.py`
  (`test_create_json_deterministic` ↔ `test_create_persists_to_latest`
  under `-n auto` parallel execution) — same file, same class, a
  pre-existing xdist worker-ordering/shared-state interaction unrelated
  to this phase's diff scope (`src/pcae/core/hatp_class_b_topology_
  verifier.py`, `tests/test_phase_149o_20*` files only).

No other delta. The 27 new 149O.20J.3 tests and 3 corrected 20I
assertions all pass. **Fast Green trust citation for this phase's
canonical report:** the clean, post-commit re-run (§25) is the primary
`test_results.fast_green` value, not the pre-commit dirty-tree count,
per this repository's established convention (a raw dirty-tree fast_green
result cannot be certified complete on its own).

## 24. Broad Sweep

`python -m pytest -k "class_b or hbdc or hmic or 149o_20" -q
--continue-on-collection-errors`: baseline 45 failed / 1188 passed / 5
skipped / 1 collection error; post-repair 54 failed / 1206 passed / 5
skipped / 1 collection error (same pre-existing `fido2` import error).
Delta: the same 6 dirty-working-tree self-checks + the same 2
intentionally-superseded assertions = 8, exactly matching the broader
count above restricted to this narrower selector. No other delta.

## 25. Post-Commit Clean Re-Run

After committing this phase's changes, `pcae push check`'s working-tree
requirement is satisfied and the dirty-tree self-checks above resolve.
The clean Fast Green and broad-sweep re-runs, performed post-commit,
are cited as the canonical `test_results` values in the phase-
completion metadata (see `.pcae/phase-completion-metadata.json` for the
exact clean counts).

## 26. Governance Close Checks

`pcae health`, `pcae check`, `pcae status coherence`, `pcae doctor
task-memory`, `pcae push check`, `pcae runtime inspect`, `pcae notify
status` re-run post-repair: health/check/coherence pass; task-memory
warnings unchanged (pre-existing, unrelated bookkeeping); runtime still
`Observed / observe / unavailable`; Telegram notification path still
configured and ready.

## 27. Blocking-Condition Check

None of the Blocking conditions enumerated by this phase's governing
prompt (item 67) are triggered: the historical defect was reproduced;
the repaired walker checks the complete relevant chain and never stops
at the first safe ancestor; writable grandparents/higher ancestors,
ACL-only grants, and effective-GID-only grants all reject; symlinked
higher ancestors reject; the traversal stop boundary (filesystem root)
is derived, not arbitrary, and does not extend beyond the threat
model; errors during higher-ancestor inspection fail closed; Git and
Protected Root use identical semantics; J-1/J-2/J-3 do not regress;
the read-only guarantee holds; no caller authority, authority
consumer, HMIC binding, readiness integration, contract change,
existing-HMIC-bound-source change, real provisioning,
certification/binding, activation, PB/POL-005/COMP-002 change, or
runtime change occurred.

## 28. Repair Verdict

```
CLASS-B FULL ANCESTOR-CHAIN VERIFICATION:
REPAIRED
— COMPLETE CONTRACT-DEFINED ANCESTOR WALK IMPLEMENTED
— WRITABLE HIGHER ANCESTORS FAIL CLOSED
— INDEPENDENT VERIFICATION PENDING

B-149O.20J.2-1:
REPAIRED
— INDEPENDENT VERIFICATION PENDING
— NOT CLOSED

J-1/J-2/J-3:
REMAIN INDEPENDENTLY CLOSED

CBV-S1:
VERIFIER REPAIR IMPLEMENTED
— INDEPENDENT VERIFICATION REQUIRED
— HMIC SOURCE-SCOPE BINDING STILL PENDING
— NOT CLOSED

CBV-S10:
UNCHANGED
— NOT CLOSED

Class-B:
CONTRACT VERIFIED
— VERIFIER REPAIRED NON-AUTHORITATIVELY
— NOT PROVISIONED

HATP:
NOT READY
```

## 29. Recommended Next Phase

**149O.20J.4 — Class-B Full Ancestor-Chain Verification Repair
Independent Verification.** Must independently: reproduce the
historical early-stop behavior from the pre-repair commit; independently
derive the contract-defined ancestor boundary (not merely accept §4's
derivation); prove the repaired implementation checks every relevant
ancestor; prove writable-grandparent/higher-ancestor rejection;
ACL-only and effective-GID-only higher-ancestor rejection; symlink/error
fail-closed handling; prove Git and Protected Root share equivalent
complete-walk semantics; verify J-1/J-2/J-3 remain closed; verify zero
consumers; verify the verifier remains outside HMIC scope. **149O.20K
(HMIC source-scope contract evolution) must not begin until 149O.20J.4
passes.** Not started by this phase; not authorized by this phase.
