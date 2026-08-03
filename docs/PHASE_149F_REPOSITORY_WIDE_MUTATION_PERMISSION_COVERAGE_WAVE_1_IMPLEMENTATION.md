# Phase 149F — Repository-Wide Mutation Permission Coverage Wave 1 Implementation

**Phase ID:** 149F
**Type:** Bounded production implementation of RWMPC-001 v1.0 Wave 1
**Predecessor:** 149E (Repository-Wide Mutation Permission Coverage
Implementation Plan — completed; verdict: IMPLEMENTATION PLAN COMPLETE,
WAVE 1 READY)
**Implements:** RWMPC-001 v1.0
(`docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`),
unamended
**Depends on (unamended):** PBPC-001 v1.2, PBPA-001 v1.0, Permission
Broker Foundation (`src/pcae/core/permission_broker_foundation.py`)

Runtime posture, unaffected by this phase:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

---

## 1. Baseline

- Pre-149F HEAD: `5392a7cd` (Phase 149E completion, `origin/main..HEAD` = 0)
- 13-site mutation inventory: unchanged from RWMPC-001/149D/149E (verified
  live, Section 6 below)
- Rollback (AG3, AG5): blocked pending trusted approval evidence, unchanged
- Task-finish (TK1-3): deferred, unchanged
- Fast Green baseline entering 149F: 4391 passed

## 2. Wave-1 Scope

Implemented (six sites): **AG1, AG2, AG4, PH1, PH2, PH3**.
Explicitly not implemented: AG3, AG5 (rollback — approval-evidence gap),
TK1, TK2, TK3 (lifecycle-internal, deferred), PU1/PU2 (already certified,
unchanged).

## 3. Shared Permission Integration Primitive

**New module:** `src/pcae/core/mutation_permission.py`.

Owns:

- `evaluate_repository_mutation_permission(...)` — the single shared
  low-level Decision Consumption Point, mirroring
  `push.py:_evaluate_push_permission`'s exact shape (construct one
  canonical `PermissionBrokerRequest`, evaluate via the unmodified default
  Foundation registry, `authorized=True` only for `DECISION_ALLOW`,
  fail-closed on `DENY`/`HUMAN_REVIEW`/broker exception/malformed result).
  This is the **only** function in the codebase that constructs a
  `PermissionBrokerRequest` for a non-`pcae push` mutation
  (RWMPC-REQ-013; verified live: `build_permission_broker_request(` is
  called exactly once in `mutation_permission.py`,
  `test_mutation_permission_core.py::test_evaluate_repository_mutation_permission_is_only_request_constructor`).
- Three thin per-class adapters, each with its own operation-specific
  freshness snapshot dataclass:
  - `evaluate_commit_permission` / `CommitDecisionSnapshot` /
    `validate_commit_permission_freshness` (AG1, PH1)
  - `evaluate_alternate_push_permission` / `AlternatePushDecisionSnapshot`
    / `validate_alternate_push_permission_freshness` (AG2, and via
    `agent._dispatch_governed_push`, PH2/PH3)
  - `evaluate_promotion_permission` / `PromotionDecisionSnapshot` /
    `validate_promotion_permission_freshness` (AG4)
  - `classify_promotion_action_type` — per-target-path category
    classifier (`src/`→`ACTION_SOURCE_MUTATION`,
    `tests/`→`ACTION_TEST_MUTATION`, `docs/`→`ACTION_DOCS_MUTATION`,
    highest-risk-first when `approved_paths` spans categories), reusing
    the existing `src/`/`tests`/`docs/` path-prefix convention already
    established in `shell_gate.py:_categorize_redirection_target` — no
    new invented taxonomy.

`action_type`, `execution_class`, `requested_component`, and
`requested_capability` are hardcoded literals inside each adapter — no
Wave-1 caller/adapter exposes an `execution_class`/policy-selection
parameter (verified:
`test_mutation_permission_core.py::test_no_adapter_exposes_execution_class_or_policy_selection_parameter`,
`test_action_type_and_execution_class_are_hardcoded_literals_not_parameters`).

Every Wave-1 request sets `simulation_only=True` (RWMPC-REQ-014/015) and
`approval_present=False` (RWMPC-REQ-017 — truthful for `MUTATION` class,
not a weakening).

### 3.1 Fail-closed observation

`_git_rev_parse_head`/`_git_write_tree`/`_git_count_commits_ahead` return
`None` only on a genuine subprocess exception (timeout), forcing
`observation_complete=False` and an unconditional freshness failure. A
non-zero return code without an exception on `git rev-parse HEAD`
(a repository with no commits yet) is represented by the stable,
comparable, git-native null-SHA sentinel (`"0"*40`, git's own
ref-update-hook convention for "no commit") rather than `None` — a
repository with no HEAD both at decision time and at dispatch time is a
real, unchanged, truthfully-observed state, not an unobservable one; a
repository that gains its first commit between the two observations is a
real, detectable change (null-SHA → real SHA). This distinction was
required to make Wave-1 governance correctly permit an initial commit in
a fresh repository rather than universally deny it as an "unobservable"
state.

## 4. AG1 — Commit (`commit_file_changes`, `agent.py`)

Inserted between staging (`_run_git_add`) and dispatch (`_run_git_commit`):
permission evaluation (`evaluate_commit_permission`) → freshness
re-validation (`validate_commit_permission_freshness`) → dispatch. All
pre-existing mechanical validation (`scope_validation.valid`,
`change_approval_state=="approved"`, working-tree/expected-files match)
is unchanged and unweakened, and remains strictly before the permission
call. Decision-bound facts: `HEAD` (`git rev-parse HEAD`), staged-content
identity (`git write-tree` — binds the exact staged tree, not just
filenames), `task_id`. `approval_present=False`, `simulation_only=True`,
`action_type=ACTION_COMMIT`, `requested_capability="pcae_remote_commit"`.

## 5. PH1 — Commit (backend-created-output-adoption commit, `phase.py`)

Consolidated with AG1 per RWMPC-001 Section 14: calls the same
`evaluate_commit_permission`/`validate_commit_permission_freshness` pair,
inserted immediately before the existing `git commit --no-verify`
dispatch, after this function's own audit-warning/
real-execution-disabled/runner-execution-refusal/idempotency gates
(unchanged).

## 6. AG2 — Alternate Push (`push_file_changes`, `agent.py`) and the Shared Dispatcher

New `_dispatch_governed_push(root, remote, branch, task_id)` in
`agent.py`: evaluates permission
(`evaluate_alternate_push_permission`) → freshness
(`validate_alternate_push_permission_freshness`) → dispatch
(`_run_git_push`, unchanged). `push_file_changes` (AG2) now calls this
dispatcher after its existing commit-SHA-ancestry mechanical check
(unchanged). Decision-bound facts: `HEAD`, target branch, unpushed-commit
count against `<remote>/<branch>` (`git rev-list --count
<remote>/<branch>..HEAD` — the shape AG2/PH2/PH3 share, distinct from
`pcae push`'s own upstream-tracking `@{u}..HEAD`), `task_id`.

## 7. PH2/PH3 — Routed Alternate Push (`phase.py`)

Per RWMPC-REQ-035, PH2 (backend-created-output-adoption push) and PH3
(final-verification-tooling push) no longer construct an independent
`git push` dispatch. Both now call `agent._dispatch_governed_push("origin",
"main", ...)` — the same function AG2 uses — exactly once per attempt.
Their own mechanical gates (audit-warning, real-execution-disabled,
runner-execution-refusal, idempotency for PH2;
`--approve-keep`/`--approved-by`/`--reason` presence and
working-tree/commit-freshness pre-checks for PH3) are unchanged and
remain command-owned; none of PH3's flags are read by the Permission
Broker request or mapped to `approval_present`.

**`push.py` (Chapter 148) is not touched.** PH2/PH3's operation shape
(`git push origin main`, unconditional target) is structurally different
from `pcae push`'s own upstream-tracking push governed by
`assess_push_readiness` — routing into `push.py` would have required
either faking readiness state or bypassing it entirely. AG2's own
dispatcher was extracted instead (149E plan Section 13's decision,
implemented as designed).

Verified by direct source inspection
(`test_repository_wide_mutation_inventory_guard.py`,
`test_mutation_permission_push_routing_integration.py`): `phase.py`
contains zero `_sp.run(["git", "push", ...])` calls and never references
`permission_broker_foundation`/`PermissionBroker(` directly.

## 8. AG4 — Promotion Apply (`build_promotion_execution`, `agent.py`)

Highest-risk site (can target `src/pcae/**`), implemented last per the
149E plan's sequencing, with the most accumulated confidence in the
shared primitive. Inserted strictly after the existing divergence check
and PER `in_progress` persistence, strictly before the apply loop's first
`write_text`/`write_bytes`/`unlink` call: permission evaluation
(`evaluate_promotion_permission`, one decision covers the entire bounded
apply operation, no per-file re-evaluation) → freshness re-validation
(`validate_promotion_permission_freshness`, re-deriving current EPR id,
ECP id, `approved_paths`, and active task from live state) → the existing
apply loop (unchanged). A `DENY`/`HUMAN_REVIEW`/broker-failure result
sets the PER's status to `"permission_denied"` and persists it (no root
write ever attempted); a stale decision sets `"permission_stale"`. Both
new PER statuses are exclusively pre-write outcomes — the existing
`partial`/`failed`/`completed`/`aborted_divergence` model is otherwise
untouched (RWMPC-REQ-041, no new transaction semantics invented).

**Self-modification (RWMPC-REQ-019, 149E plan Section 9.4):** no new
mechanical protected-path hard block was added for `src/pcae/**` targets.
The permission boundary applies identically regardless of target — a
target under `src/pcae/**` still requires `ALLOW` and is neither more nor
less strictly gated than any other target
(`test_mutation_permission_promotion_integration.py::test_src_pcae_target_requires_allow_like_any_other_target`,
`test_deny_blocks_src_pcae_target_too`).

## 9. AG3, AG5, TK1-3 — Non-Interference

- **AG3** (`execute_rollback`) and **AG5** (`build_rollback_execution`):
  zero behavioral change. `_run_git_revert` (AG3) and the write/unlink
  loop inside `build_rollback_execution` (AG5) remain classified
  `ROLLBACK_BLOCKED` by the inventory guard test; both are BLOCKED —
  NO TRUSTED APPROVAL EVIDENCE, exactly as RWMPC-001 §12.1 records
  independently of this phase.
- **TK1, TK2, TK3** (`task.py`): `git diff 5392a7cd..HEAD --
  src/pcae/commands/task.py` is empty. `task.py` still contains exactly
  its 3 pre-existing `git commit --no-verify` dispatches, still contains
  no reference to `permission_broker_foundation`/`PermissionBroker(`/
  `mutation_permission`
  (`test_task_finish_permission_non_interference.py`, including a real,
  end-to-end `pcae task finish --commit` dispatch confirming zero
  Permission Broker consultation).

## 10. Historical Guard Sweep (item 43 of the governing instruction)

`grep -rl "PermissionBroker\|permission_broker_foundation" tests/` found
30 files (149E's partial 2-file check, F-149E-1, is now closed). All 30
were run against the implemented Wave 1; one genuinely stale invariant
was found and repaired:

- `tests/test_phase_148f_permission_broker_production_consumption_independent_verification.py::test_permission_broker_consumer_scope_inventory`
  asserted exactly one authorized Permission Broker consumer (`push.py`).
  Narrowed (not deleted) to recognize `mutation_permission.py` as a
  second, Chapter-149-authorized consumer, while preserving the negative
  invariant that no *third*, unclassified consumer exists, and that
  `phase.py`/`core/agent.py` still never reference the Foundation or
  broker *directly* (only via `mutation_permission.py`).

Two further docstring-only narrowings (assertions already held mechanically,
since `phase.py` never contains the literal strings `PermissionBroker(`
or `permission_broker_foundation` — only an import of the sanctioned
`mutation_permission` adapter module) were made for accuracy, not because
they were failing:

- `tests/test_permission_broker_observation_verification.py::test_lifecycle_command_modules_never_import_broker_directly`
- `tests/test_permission_broker_verification_compatibility.py::test_broker_not_imported_by_lifecycle_command_modules`

`tests/test_phase_149d_rwmpc_contract_independent_verification.py`'s
raw-regex dispatch-count test
(`TestMutationInventory::test_thirteen_sites_across_four_files`) was
updated to reflect Wave-1's intended effect: `phase.py`'s literal
`["git", "push", ...]` count intentionally dropped from 3 to 2 (PH2's
`push_command` variable is now diagnostic-only, never dispatched; PH3's
literal is gone entirely, replaced by routing) — a new companion test
(`test_ph2_ph3_route_through_shared_alternate_push_dispatcher`)
independently confirms the *routing*, not merely the absence of a
literal.

No other stale invariant was found across the remaining files.

## 11. Mutation Inventory Guard

`tests/test_repository_wide_mutation_inventory_guard.py` — AST-based (not
substring), classifies every `subprocess.run(["git", "commit"/"push"/
"revert"/"reset", ...])` and every `write_text`/`write_bytes`/`unlink`
call inside `build_promotion_execution`/`build_rollback_execution`
against the frozen 13-site table. `EXISTING_CERTIFIED` (PU1, PU2, 2),
`WAVE1_GOVERNED` (AG1 `_run_git_commit`, AG2 `_run_git_push`, AG4, PH1,
4 functions), `ROLLBACK_BLOCKED` (AG3, AG5, 2), `TASK_FINISH_DEFERRED`
(TK1+TK2 in `run_task_finish`, TK3 in `run_task_finish_recover`, 2
functions), `CANONICALLY_ROUTED` (PH2, PH3 — required to contain **zero**
independent dispatch calls). A repo-wide sweep (all of `src/pcae/`, not
just the four named files) confirms no 14th git-mutation dispatch site
exists anywhere else.

## 12. Test Suite Summary

New files (51 tests total):

| File | Tests | Purpose |
|---|---|---|
| `test_mutation_permission_core.py` | 14 | Shared primitive: ALLOW-only consumption, DENY/HUMAN_REVIEW/exception/malformed-result fail-closed, POL-001/POL-004/POL-005 controls, no caller-selectable classification |
| `test_mutation_permission_commit_integration.py` | 9 | AG1: real ALLOW dispatches; DENY/HUMAN_REVIEW/broker-failure/missing-task block; staged-content/HEAD/task drift blocks; commit-message drift does not |
| `test_mutation_permission_promotion_integration.py` | 11 | AG4: real ALLOW writes; DENY/HUMAN_REVIEW/broker-failure/missing-task block with zero write; divergence-conflict pre-permission gate unaffected; `approved_paths`/task drift blocks; `src/pcae/**` target requires ALLOW like any other |
| `test_mutation_permission_push_routing_integration.py` | 6 | AG2 real ALLOW pushes once; DENY/HUMAN_REVIEW/broker-failure/freshness-drift block; PH2/PH3 contain zero independent dispatch; exactly-once evaluation |
| `test_repository_wide_mutation_inventory_guard.py` | 5 | AST-based 13-site classification, zero UNKNOWN, zero 14th site, PH2/PH3 empty |
| `test_task_finish_permission_non_interference.py` | 4 | TK1-3 source/behavior byte-identical; zero Permission Broker consultation |

Modified existing files: `tests/test_agent.py` (fixture repair only —
`_init_git_root`/`_patch_push_helpers` now provide the active task/git
state Wave-1's real permission-evaluation code needs, mirroring how
`_run_git_push`/`_run_git_commit` were already faked; zero assertion
changed), `tests/test_phase.py` (one fixture: added a task contract to
`test_77s_execute_creates_commit`).

## 13. Regressions Run

- `tests/test_agent.py`: **4236 passed**
- `tests/test_lifecycle_regression.py`, `test_lifecycle_next_command.py`,
  `test_phase.py`, `test_lifecycle_status_command.py`,
  `test_lifecycle_summary_command.py`, `test_lifecycle_gate_approval.py`:
  **954 passed**
- All 30 historical Permission-Broker-referencing test files: **2236
  passed** (post-repair)
- `test_permission_broker_push_production_consumption.py`,
  `test_permission_broker_push_operational_hardening.py`,
  `test_phase_148c10_pbpc_v12_independent_verification.py`,
  `test_phase_148f_...independent_verification.py`,
  `test_phase_148g2_...independent_verification.py` (Chapter 148): all
  green, `push.py` byte-unchanged
- `test_cltr_authority_136at_quarantine_record.py`,
  `test_cltr_authority_136au_quarantine_record_independent.py`,
  `test_cltr_rehearsal_rollback.py`,
  `test_cltr_rehearsal_135u_independent_verification.py`: **389 passed**
- `test_runtime_context_verification.py`, `test_runtime_inspect_cli.py`,
  `test_runtime_inspect_verification.py`, `test_runtime_snapshot.py`:
  **236 passed**
- Fast Green (`python -m pytest -m fast_green -n auto -q`): **4391
  passed** — identical to the pre-149F baseline (new Wave-1 tests are not
  `fast_green`-marked, per the plan's own note that a changed count would
  only be expected if they were)

## 14. Production Diff Summary

```
git diff --stat 5392a7cd..HEAD -- src/pcae/
 src/pcae/commands/phase.py | 109 +++++++++++++++-
 src/pcae/core/agent.py     | 192 ++++++++++++++++++++++++-
 2 files changed, 476 insertions(+), 33 deletions(-)   (incl. new mutation_permission.py, untracked)
```

- `src/pcae/core/mutation_permission.py` — **new**, shared primitive +
  three adapters (Section 3)
- `src/pcae/core/agent.py` — AG1 permission gate, `_dispatch_governed_push`
  + AG2 permission gate, AG4 permission gate (Sections 4, 6, 8)
- `src/pcae/commands/phase.py` — PH1 permission gate, PH2/PH3 routing
  (Sections 5, 7)
- `src/pcae/commands/push.py` — **empty diff** (unchanged)
- `src/pcae/commands/task.py` — **empty diff** (unchanged)
- `src/pcae/core/permission_broker_foundation.py`,
  `src/pcae/core/permission_broker.py` — **empty diff** (unchanged)
- `docs/contracts/**` — **empty diff** (unchanged)

No unrelated production hunk exists; every changed line in `agent.py`/
`phase.py` belongs to one of AG1/AG2/AG4/PH1/PH2-routing/PH3-routing/the
shared dispatcher extraction.

## 15. Mutation Inventory — Final Matrix

| Site | Mutation | Pre-149F | Post-149F |
|---|---|---|---|
| PU1 | `git push` (primary) | BROKER_WIRE, certified | unchanged |
| PU2 | `git push` (staged-file-aware) | BROKER_WIRE, certified | unchanged |
| AG1 | `git commit` | ungated | **WAVE1_GOVERNED** |
| AG2 | `git push <remote> HEAD:<branch>` | ungated | **WAVE1_GOVERNED** |
| AG3 | `git revert --no-edit` | ungated | ROLLBACK_BLOCKED (unchanged, not implemented) |
| AG4 | file write/unlink (promotion apply) | ungated | **WAVE1_GOVERNED** |
| AG5 | file write/unlink (promotion restore) | ungated | ROLLBACK_BLOCKED (unchanged, not implemented) |
| TK1 | `git commit --no-verify` (pathspec) | ungated | TASK_FINISH_DEFERRED (unchanged) |
| TK2 | `git commit --no-verify` (repo-wide) | ungated | TASK_FINISH_DEFERRED (unchanged) |
| TK3 | `git commit --no-verify` (recover) | ungated | TASK_FINISH_DEFERRED (unchanged) |
| PH1 | `git commit --no-verify` | ungated | **WAVE1_GOVERNED** (shared with AG1) |
| PH2 | `git push origin main` | ungated | **CANONICALLY_ROUTED** (via AG2) |
| PH3 | `git push origin main` | ungated | **CANONICALLY_ROUTED** (via AG2) |

Coverage: 2/13 → **8/13** Permission-Broker-governed (PU1, PU2, AG1, AG2,
AG4, PH1) + 2/13 canonically routed into a governed dispatcher (PH2, PH3)
= **10/13** with no ungated direct dispatch bypass reachable. 3/13
(AG3, AG5, and the three TK sites) remain explicitly, individually
unresolved — recorded, not silently dropped.

## 16. Findings

No BLOCKING findings.

| ID | Classification | Finding |
|---|---|---|
| F-149F-1 | OBSERVATION | `_git_rev_parse_head`'s "no commits yet" handling (Section 3.1) was a genuine, previously-unconsidered edge case discovered during implementation (existing `test_agent.py`/`test_phase.py` fixtures create fresh, commit-less repos); resolved using git's own null-SHA convention rather than weakening the fail-closed contract. |
| F-149F-2 | OBSERVATION | AG4's self-modification threat (`pcae promote` targeting `src/pcae/**`) remains without a new mechanical hard block in Wave 1, per RWMPC-REQ-019 — carried forward from 149E's F-149E-3, not re-litigated here. |
| F-149F-3 | OBSERVATION | `test_agent.py`'s size (65k+ lines) remains a pre-existing structural risk unrelated to RWMPC-001, carried forward from 149E's F-149E-2. |

## 17. Excluded / Deferred — Explicit Reconfirmation

- **AG3, AG5 (rollback):** not implemented, remain blocked on missing
  trusted `approval_present=True` evidence (RWMPC-001 §12.1). No approval
  was fabricated. No Interactive Workflow Confirmation artifact was
  treated as approval. No Authority Evaluation/AESIC result was treated
  as permission.
- **TK1, TK2, TK3 (task-finish):** not implemented, remain explicitly
  deferred (`LIFECYCLE_INTERNAL / DEFERRED_COVERAGE`), byte-identical
  behavior confirmed.

## 18. No-Go Confirmations

- RWMPC-001 v1.0, PBPC-001 v1.2, PBPA-001 v1.0 remain unamended (verified:
  empty `docs/contracts/` diff).
- No POL-001..012 meaning was changed; no POL-013+ was added.
- `permission_broker_foundation.py` and `permission_broker.py` are
  byte-unchanged.
- `push.py` and `task.py` are byte-unchanged.
- No mutation was routed through Runtime Enforcement.
- No Prompt Generation, Prompt Dispatch, or agent-invocation capability
  was implemented.
- Runtime remains `Observed`, maximum capability remains `observe`,
  execution availability remains `unavailable` (verified: `pcae runtime
  inspect`, before and after).
- No caller-selectable classification/policy mechanism exists anywhere in
  Wave-1 scope (verified by inspection and test).
- No agent self-permission path exists — `action_type`, `execution_class`,
  `approval_present` are fixed by trusted adapter code only.

## 19. Wave-1 Verdict

**WAVE 1 IMPLEMENTED — READY FOR INDEPENDENT VERIFICATION.**

All six authorized Wave-1 sites (AG1, AG2, AG4, PH1, PH2, PH3) satisfy
their frozen RWMPC-001 disposition. No ungated direct-dispatch bypass
remains reachable for any of them. AG3, AG5, and TK1-3 remain
untouched and explicitly recorded as still unresolved. This is **not** a
claim that all repository mutation is now Permission-Broker governed —
Chapter 149 remains incomplete pending a future, narrowly scoped
rollback-approval-evidence phase.

## 20. Recommended Next Phase

**149G — Repository-Wide Mutation Permission Coverage Wave 1 Independent
Verification.** Must independently attack: all six new sites; canonical
routing (PH2/PH3 → AG2); stale-decision handling; the mutation inventory
guard; rollback non-interference (AG3/AG5); TK1-3 deferral;
Chapter-148 compatibility. Wave 1 is not self-certified by this phase's
own tests alone.
