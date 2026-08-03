# Repository-Wide Mutation Permission Coverage Contract

## Contract identity and status

**Contract:** RWMPC-001
**Version:** 1.0
**Status:** FROZEN (partial coverage — see Section 12 for the one
execution class this version does not authorize wiring for)
**Frozen by:** Phase 149C — Repository-Wide Mutation Permission
Coverage Contract Freeze
**Depends on:** PBPA-001 v1.0 (`PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md`,
unamended), PBPC-001 v1.2 (`PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md`,
unamended), Phase 108A-C Permission Broker Foundation
(`src/pcae/core/permission_broker_foundation.py`, unamended)
**Architecture basis:** `docs/PHASE_149B_REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_ARCHITECTURE.md`
(Model E — Hybrid). Where this contract's independent reconstruction
diverges from 149B's prose, this contract is normative; Section 3
records every point of divergence.

RWMPC-001 v1.0 is the sole authoritative contract governing how
repository mutation paths *other than* `pcae push` (already governed by
PBPC-001) consume the Permission Broker Foundation as their mandatory
centralized permission-decision boundary. It is additive to PBPC-001,
not a replacement or amendment of it. Future implementation phases
SHALL cite RWMPC-001 for non-push mutation coverage and SHALL NOT
reinterpret this contract, PBPC-001, PBPA-001, or the Foundation
locally.

This is contract text only. It does not implement, activate, authorize,
or wire the Permission Broker into any new consumer. It grants no
runtime, lifecycle, or execution capability, and does not itself
authorize an implementation phase — Section 15 fixes the exact
preconditions a future implementation phase must satisfy.

Runtime posture, unaffected by this contract:

- State: **Observed**
- Maximum capability: **observe**
- Execution availability: **unavailable**

## 0. Normative language

The key words **SHALL**, **SHALL NOT**, **MUST**, **MUST NOT**, and
**MAY** are normative, with the same meaning as PBPC-001 §0. Every
mandatory behavior receives a unique, sequential, stable,
non-reused requirement identifier of the form `RWMPC-REQ-###`.
Identifiers are never renumbered or reused across revisions.

## 1. Purpose

RWMPC-REQ-001: This contract SHALL govern the consumption of the
existing, already-frozen Permission Broker Foundation by every
repository-mutating production command path *other than* `pcae push`
(PBPC-001's exclusive domain), identified in Section 4.

RWMPC-REQ-002: This contract SHALL preserve every currently-enforced
mechanical/structural safeguard on each in-scope path (Section 9),
introduce no new mutation capability, introduce no autonomous
authority, create no second permission authority alongside the
Permission Broker (Section 10), and not elevate runtime capability.

RWMPC-REQ-003: Conformance with RWMPC-001 alone SHALL NOT authorize
implementation. Section 15 states the complete precondition set.

RWMPC-REQ-004: This contract SHALL NOT amend PBPC-001, PBPA-001, or
POL-001..012, and SHALL NOT introduce POL-013 or any further policy
rule. Where a truthful request cannot obtain a resolvable decision
under the existing, unamended Foundation, this contract records that
fact as a scoped gap (Section 12) rather than working around it.

## 2. Scope

RWMPC-REQ-005: **In scope** — every mutation class independently
confirmed present in Section 4's inventory: local-history mutation
(commit), remote-repository mutation (push, outside `pcae push`
itself), rollback/recovery mutation (git revert and promotion-restore),
and working-tree/source mutation (promotion file-apply).

RWMPC-REQ-006: **Out of scope**, per direct evidence and consistent
with 149A/149B's boundary: `.pcae/**` lifecycle-state/bookkeeping
writes (governed by task-lifecycle/phase-reporting contracts, not this
one); canonical artifact publication under Chapter 114/144-146
authority; external notifications (Telegram/sinks); manual human `git`
usage outside any PCAE command; test/fixture code; Prompt Creation,
Prompt Dispatch, agent invocation, and runtime capability activation
(each separately gated and separately authorized; Phase 45F remains
deferred).

RWMPC-REQ-007: `pcae task finish --commit` and `pcae task finish
recover` (Section 4, sites T1-T3) SHALL be treated as **in scope** for
classification purposes (they are real `git commit` dispatches) but are
assigned disposition `LIFECYCLE_INTERNAL / DEFERRED_COVERAGE` (Section
9) rather than `BROKER_WIRE`, for the reason stated there. This is an
explicit, evidenced exclusion from immediate wiring, not a silent
scope drop (per the instruction that motivated this phase, this
question SHALL NOT be resolved by omission).

## 3. Divergence from Phase 149B

RWMPC-REQ-008: 149B (§21/§22) left the file-apply execution-class
mapping and the rollback approval-evidence question explicitly
unresolved as "STRATEGIC_POLICY_GAP" findings for this phase to close.
This contract closes the first (Section 8.3) using only the existing,
unamended taxonomy, and records the second as a genuine, unresolved
blocking gap rather than closing it (Section 12) — 149B anticipated
both outcomes were possible and instructed this phase not to fabricate
a resolution where none exists.

## 4. Independently Reconstructed Mutation Inventory

RWMPC-REQ-009: The following inventory was reconstructed by direct
reading of current source (not by trusting 149B's summary), searching
`src/pcae/commands/push.py`, `src/pcae/core/agent.py`,
`src/pcae/commands/task.py`, and `src/pcae/commands/phase.py` for
`git commit`/`git push`/`git revert`/`git reset` subprocess dispatch
and direct filesystem write/unlink calls outside `.pcae/**`. It
independently arrives at **13 real, CLI-reachable production mutation
dispatch sites**, matching 149B's count — an independent confirmation,
not an assumption.

| ID | File:line | Command surface | Operation |
|---|---|---|---|
| PU1 | `push.py:698` | `pcae push` | `git push` (primary dispatch) |
| PU2 | `push.py:898` | `pcae push` (fallback path) | `git push origin main` |
| AG1 | `agent.py:4572` | `pcae remote changes commit` | `git commit` |
| AG2 | `agent.py:4732` | `pcae remote changes push` | `git push <remote> HEAD:<branch>` |
| AG3 | `agent.py:5099` | `pcae remote rollback execute` | `git revert --no-edit` |
| AG4 | `agent.py:~93390-93417` | `pcae promote` (`build_promotion_execution` apply loop) | direct file write/unlink into `approved_paths` (can include `src/pcae/**`) |
| AG5 | `agent.py:~93820-93841` | `pcae promote` promotion-failure restore path | direct file write/unlink restoring `before_content` |
| TK1 | `task.py:308` | `pcae task finish --commit` (staged-file-aware branch) | `git commit --no-verify` (pathspec-scoped) |
| TK2 | `task.py:316` | `pcae task finish --commit` (repo-wide branch) | `git commit --no-verify` |
| TK3 | `task.py:1100` | `pcae task finish recover` | `git commit --no-verify` |
| PH1 | `phase.py:18457` | backend-created-output-adoption commit | `git commit --no-verify` |
| PH2 | `phase.py:19563` | backend-created-output-adoption push | `git push origin main` |
| PH3 | `phase.py:20295` | final-verification-tooling push | `git push origin main` |

RWMPC-REQ-010: Current Permission Broker coverage: **2 of 13** (PU1,
PU2 — both `pcae push`, governed by PBPC-001 v1.2). The remaining
**11** are dispatch-reachable today with zero Permission Broker
consultation — confirmed by direct inspection, not inference.

RWMPC-REQ-011: Runtime Enforcement coverage: **0 of 13**. None of these
13 sites are shell/backend/adapter invocations (Runtime Enforcement's
domain per PBPC-001 §25); all are direct `git` subprocess calls or
direct filesystem writes. This contract SHALL NOT route any of them
through Runtime Enforcement (Section 13).

## 5. Mutation Taxonomy

RWMPC-REQ-012: This contract freezes exactly the taxonomy needed for
enforcement, using existing repository-native vocabulary — it does not
adopt 149B's full 8-category descriptive taxonomy verbatim, retaining
only the four classes with enforcement consequence:

| Taxonomy class | Definition | Sites |
|---|---|---|
| **Local-history mutation** | Creates a new commit on the current branch | AG1, TK1, TK2, TK3, PH1 |
| **Remote-repository mutation** | Transmits local history to a remote | PU1, PU2, AG2, PH2, PH3 |
| **Rollback/recovery mutation** | Reverts or restores prior content/history | AG3, AG5 |
| **Working-tree/source mutation** | Writes or deletes file content directly (not via `git`) | AG4 |

## 6. Canonical Request Model

RWMPC-REQ-013: Every in-scope path SHALL construct exactly one
`permission_broker_foundation.PermissionBrokerRequest` per mutation
attempt via `build_permission_broker_request`, reusing the existing
dataclass unchanged. No new request schema, and no mutation-specific
subclass or wrapper, is introduced by this contract — independently
verified: every field listed below already exists and every in-scope
operation can be truthfully represented with it.

| Field | Meaning | Source of truth | Caller-influenceable? |
|---|---|---|---|
| `request_id`, `timestamp` | Generated by the builder | `build_permission_broker_request` | No |
| `action_type` | What kind of mutation | Section 8.1 table, fixed by the adapter | No (RWMPC-REQ-016) |
| `execution_class` | Foundation-recognized capability class | Section 8.1/8.3 tables, fixed by the adapter | No (RWMPC-REQ-016) |
| `task_id` | Governing task, if any | Current task-memory state | Indirectly (reflects real state) |
| `phase_id` | Governing phase, if any | Current phase state | Indirectly (reflects real state) |
| `requested_component` | Owning component (`COMP-xxx`) | Component registry | No |
| `requested_capability` | Named capability (e.g. `pcae_push`) | Fixed per adapter | No |
| `requested_resource` | Concrete target (path/ref/job id) | Observed at request time | No — reflects, does not choose |
| `evidence_available` | Whether supporting evidence exists | Adapter's own observation | No — reflects, does not choose |
| `approval_present` | Section 8.2 | Section 11 evidence sources only | No (RWMPC-REQ-018) |
| `simulation_only` | Section 7 | Fixed `True`, Foundation-wide, all classes | No |

## 7. `simulation_only` Semantics (Satisfiability Finding)

RWMPC-REQ-014: `simulation_only` on `PermissionBrokerRequest` means,
per the dataclass's own docstring (Section 6, Phase 108A): *the
Foundation has no execution boundary (`COMP-002` is
`not_implemented`), so every request the broker evaluates today is
inherently a policy simulation, regardless of whether the calling
command subsequently performs a real mutation.* It does **not** mean
"this caller promises not to really mutate anything." PBPC-001's own
production consumer (`push.py:480-490`) already sets
`simulation_only=True` on `pcae push`'s real dispatch request — the
one and only PCAE mutation with production history — establishing this
as the governing, load-bearing precedent rather than a push-specific
carve-out.

RWMPC-REQ-015: Every in-scope path under this contract SHALL set
`simulation_only=True` uniformly, for the same reason PBPC-001 does.
Independent satisfiability testing (Section 12) confirms: setting
`simulation_only=False` for any real mutation attempt unconditionally
triggers POL-005 (`ExecutionDisabledRule`) DENY, because POL-005 is
"unconditionally active by construction" pending `COMP-002` — this
would make **every** in-scope class permanently unsatisfiable, which
would be a Foundation-scope contradiction, not a Chapter-149-specific
one. This contract does not weaken POL-005; it applies the existing,
already-established `simulation_only=True` meaning generally instead
of only to `pcae push`.

## 8. Classification Ownership

RWMPC-REQ-016: `action_type`, `execution_class`, and
`requested_component`/`requested_capability` SHALL be fixed by trusted
PCAE adapter code (Section 6.3 tables), never by the mutation caller.
No in-scope path SHALL expose a caller-facing mechanism equivalent to
`--execution-class`, `--policy-profile`, `exclude_policies`,
`selected_policy_ids`, or `skip_policy`. None exists in current source
(confirmed by inspection of all 13 sites' argument parsers); this
contract prohibits any future path from introducing one.

### 8.1 Action-type / execution-class table (satisfiable classes)

| Mutation type | Sites | `action_type` | `execution_class` |
|---|---|---|---|
| Push (canonical, already governed) | PU1, PU2 | `ACTION_PUSH` | `EXECUTION_CLASS_MUTATION` |
| Push (alternate dispatch, pending routing — Section 14) | AG2, PH2, PH3 | `ACTION_PUSH` | `EXECUTION_CLASS_MUTATION` |
| Commit | AG1, TK1, TK2, TK3, PH1 | `ACTION_COMMIT` | `EXECUTION_CLASS_MUTATION` |
| Working-tree/source mutation (promotion apply) | AG4 | `ACTION_SOURCE_MUTATION` / `ACTION_DOCS_MUTATION` / `ACTION_TEST_MUTATION`, selected per target path's category, never caller-selected | `EXECUTION_CLASS_MUTATION` |

### 8.2 Approval semantics per class

RWMPC-REQ-017: `POL-004` (`MissingHumanApprovalRule`) is scoped to
`applicable_execution_classes = {SHELL, BACKEND, ADAPTER, ROLLBACK}` —
`MUTATION` and `NONE` are excluded by the Foundation's own design
(PBPA-REQ-063/064), independently re-verified by direct reading of
`permission_broker_foundation.py:459-468`. Therefore:

- For every `EXECUTION_CLASS_MUTATION` site (push, commit,
  promotion-apply): `approval_present=False` is the **truthful** value
  — POL-004 does not apply, no approval evidence is needed for POL-004
  to resolve, and the field must not be set `True` merely because it
  is harmless to do so (RWMPC-REQ-020 forbids fabrication regardless).
- For every `EXECUTION_CLASS_ROLLBACK` site (Section 8.3): POL-004
  *is* applicable and `approval_present` must reflect a real evidence
  source (Section 11) or the request truthfully cannot obtain `ALLOW`.

### 8.3 Rollback / recovery classification

RWMPC-REQ-018: 149B (§21/§22) left file-apply's execution-class
mapping open specifically for the promotion-restore path
(AG5). Independent classification, using only the existing taxonomy:
`execute_rollback` (AG3, `git revert`) and the promotion-failure
restore path (AG5, writing back `before_content`) are both, in
substance, "revert content/history to a prior recorded state" — the
same operation semantics `EXECUTION_CLASS_ROLLBACK` already exists to
name. This contract therefore classifies AG5 as `ACTION_ROLLBACK` /
`EXECUTION_CLASS_ROLLBACK`, identically to AG3, rather than as
`EXECUTION_CLASS_MUTATION`. This resolves 149B's open mapping question
using the existing taxonomy's own operational (not risk-based)
definition, introducing no new class and no POL-013.

| Mutation type | Sites | `action_type` | `execution_class` |
|---|---|---|---|
| Rollback / recovery | AG3, AG5 | `ACTION_ROLLBACK` | `EXECUTION_CLASS_ROLLBACK` |

RWMPC-REQ-019: The heightened risk of promotion apply (AG4) being able
to target `src/pcae/**` (Section 16) is a real strategic risk but SHALL
NOT be addressed by misclassifying AG4 as `EXECUTION_CLASS_ROLLBACK` or
any other approval-requiring class merely to obtain a stricter gate
(prohibited by the instruction motivating this phase). Section 16
records it as a threat-model item requiring a mechanical (command-
owned), not policy, control.

## 9. Mechanical-vs-Permission Boundary

RWMPC-REQ-020: For every in-scope path, the following current checks
remain **command-owned mechanical validation**, unchanged by this
contract, and are never reclassified as Permission Broker `DENY`
territory:

| Path family | Mechanical checks that remain command-owned |
|---|---|
| `pcae remote changes commit/push` (AG1, AG2) | `scope_validation.valid`, `change_approval_state == "approved"`, working-tree/expected-files match (`commit_file_changes`); commit-SHA ancestry check (`push_file_changes`) |
| `pcae remote rollback execute` (AG3) | `rollback_approval_state == "approved"`, rollback eligibility, `rollback_mode_recommendation == "revert_commit"`, clean working tree, commit reachability |
| `pcae promote` (AG4, AG5) | EPR `review_state`/`promotion_authorized` flag check, ECP `capture_outcome`, divergence check, in-progress duplicate guard — all preserved as pre-broker structural gates |
| `pcae task finish --commit`/`recover` (TK1-TK3) | Task-finish validation (health/check unless `--skip-checks`), staged-file-aware conflict detection, closure-file path restriction |
| backend-created-output-adoption (PH1, PH2) | Audit-warning gate, real-execution-disabled gate, runner-execution-refusal gate, already-committed/pushed idempotency guard |
| final-verification-tooling-push (PH3) | `--approve-keep`/`--approved-by`/`--reason` presence check, working-tree/commit-freshness pre-checks |

RWMPC-REQ-021: The Permission Broker becomes the sole normative
**permission** authority for every in-scope path; none of the checks
in the table above are reclassified as permission decisions, and the
Permission Broker's decision does not replace or weaken any of them —
both layers apply, mechanical first (as today), then permission,
consistent with PBPC-001's existing pattern for `pcae push`.

## 10. Agent Self-Permission Prohibition

RWMPC-REQ-022: `agent requests mutation ≠ agent grants permission`.
The requesting agent (human or automated caller) SHALL NOT control
`execution_class`, `action_type`, `approval_present`'s truth value,
policy selection, the broker's decision, or freshness validation
outcome, for any in-scope path. No Permission Broker decision or
canonical request field may be constructed from agent-authored output
(e.g. an AI-generated `approved=true` claim) — such output SHALL NOT
satisfy `approval_present`.

RWMPC-REQ-023: Confirmation is not approval. Interactive Workflow
Confirmation, task-finish health/check validation, and any other
process-hygiene confirmation artifact SHALL NOT populate
`approval_present`, regardless of which operation needs approval.
Authority Evaluation / AESIC results SHALL NOT be treated as
permission or approval evidence — AESIC remains disclosure-only.

## 11. Approval Evidence Analysis

RWMPC-REQ-024: For each legacy CLI flag observed to resemble approval,
independent classification:

| Flag / site | Classification | Trusted approval evidence? |
|---|---|---|
| `--promotion-authorized`, `--reviewed-by` (`pcae epr create`, feeding AG4/AG5) | Unauthenticated CLI self-declaration — any caller (human or script) can pass these; no identity binding exists | **No** |
| `approve_rollback`/`rollback_approval_state` flag (AG3, `pcae remote rollback approve`) | Bare state-flag toggle, no identity/reason field | **No** |
| `change_approval_state` (AG1/AG2, `pcae remote changes approve`) | Bare state-flag toggle, no identity/reason field | **No** |
| `--approve-keep`, `--approved-by`, `--reason` (PH3) | Named, structured CLI flags with explicit intent — closer in shape to real approval evidence than the others, but still an unauthenticated self-declaration; nothing verifies the caller's claimed identity | **No** (strongest legacy candidate, still insufficient) |
| Task-finish health/check pass (TK1-TK3) | Mechanical/structural confirmation, not a disposition decision | **No** (confirmation, per RWMPC-REQ-023) |

RWMPC-REQ-025: **No existing artifact in the repository today
constitutes trusted, authenticated `approval_present=True` evidence**
for any `EXECUTION_CLASS_ROLLBACK` site. This is recorded truthfully
(Section 12) rather than treating any of the flags above as sufficient.

## 12. Satisfiability Matrix and Blocking Finding

RWMPC-REQ-026: Constructed truthful conceptual requests for every
in-scope operation class and evaluated their resolvability against the
current, unmodified Foundation (no code executed — evaluated by
tracing `permission_broker_foundation.py`'s policy registry against
each request's field values):

| Operation class | `execution_class` | `approval_present` (truthful) | `simulation_only` | POL-004 applicable? | POL-005 result | Resolvable decision | Contract satisfiable now? |
|---|---|---|---|---|---|---|---|
| Commit | `MUTATION` | `False` | `True` | No | not triggered | `ALLOW` (no other policy blocks a well-formed request) | **Yes** |
| Push (non-`pcae push` sites, pending routing) | `MUTATION` | `False` | `True` | No | not triggered | `ALLOW` | **Yes** |
| Source/working-tree mutation (promotion apply) | `MUTATION` | `False` | `True` | No | not triggered | `ALLOW` | **Yes** |
| Rollback / recovery (git revert, promotion restore) | `ROLLBACK` | `False` (no trusted source exists — RWMPC-REQ-025) | `True` | **Yes** | not triggered | `HUMAN_REVIEW` (POL-004 triggers on `approval_present=False`) — zero dispatch, unresolvable without fabricating evidence | **No — BLOCKING (Section 12.1)** |

### 12.1 Blocking finding: rollback-class approval evidence gap

RWMPC-REQ-027: **BLOCKING.** For every `EXECUTION_CLASS_ROLLBACK` site
(AG3, AG5), a truthful request necessarily carries `approval_present
=False` today, which POL-004 correctly routes to `HUMAN_REVIEW` —
zero mutation dispatch, by design, not a defect. This is the intended
policy result: POL-004 is not weakened, and this contract does not
attempt to make `approval_present=True` become truthful by inventing
an evidence source. **Rollback-class Permission Broker coverage (AG3,
AG5) is NOT SATISFIABLE under this contract until a future, narrowly
scoped phase defines a legitimate `approval_present=True` evidence
source** (e.g., an authenticated human-approval artifact distinct from
today's bare flags) **or an equivalent mechanism** is established by a
separate contract/architecture phase. This is a missing-approval-
evidence gap, not a policy-applicability gap, a request-model gap, or a
simulation-semantics gap — those are all independently confirmed
resolved (rows above).

RWMPC-REQ-028: This blocking finding scopes only to the two
`EXECUTION_CLASS_ROLLBACK` sites. It does not prevent freezing or
implementing coverage for the nine `EXECUTION_CLASS_MUTATION` sites,
whose satisfiability is independently confirmed above. Per the
instruction that motivated this phase: do not freeze around fabricated
approval, and do not let one unsatisfiable class sink an otherwise
satisfiable contract when the two are severable — they are severable
here because POL-004's applicability (not this contract) is what
already separates them.

## 13. Fail-Closed Semantics

RWMPC-REQ-029: For every in-scope mutation path, the following SHALL
result in zero mutation dispatch, without exception and without
fallback to pre-broker legacy behavior:

- Broker decision `DENY`
- Broker decision `HUMAN_REVIEW`
- Broker construction or evaluation exception
- Malformed or non-`PermissionBrokerDecision` broker result
- Any applicability/classification failure (unknown `action_type` or
  `execution_class` — Section 8, RWMPC-REQ-016)

RWMPC-REQ-030: Only a literal `decision == DECISION_ALLOW` on a valid
`PermissionBrokerDecision` object authorizes continuation past the
permission boundary, mirroring PBPC-REQ-052's existing pattern
verbatim.

RWMPC-REQ-031: `ALLOW ≠ guaranteed mutation`. Mechanical/structural
validation (Section 9) may still reject after `ALLOW`. Execution
failure (subprocess non-zero exit, filesystem error) after `ALLOW` is
distinct from permission failure and SHALL NOT cause any rewriting of
the already-recorded permission decision.

RWMPC-REQ-032: An unrecognized future mutation `action_type` or
`execution_class` SHALL NOT silently inherit `EXECUTION_CLASS_MUTATION`
or any other permissive default — classification failure SHALL result
in zero dispatch (already the existing behavior of `POL-006`, the
Unknown Capability rule, reused unchanged).

## 14. Per-Path Disposition

RWMPC-REQ-033: Every one of the 13 sites receives an explicit,
unambiguous disposition. `BROKER_WIRE` = build/consume a canonical
request per Sections 6/8; `ROUTE_TO_CANONICAL_COMMAND` = stop
independent dispatch, invoke the shared adapter instead;
`LIFECYCLE_INTERNAL / DEFERRED_COVERAGE` = real mutation, in scope for
classification, but not wired in the sequence this contract implies
without further evidence.

| Site | Disposition | Rationale |
|---|---|---|
| PU1, PU2 (`pcae push`) | Already `BROKER_WIRE` (PBPC-001 v1.2, certified) | No change; this contract is additive |
| AG1 (`pcae remote changes commit`) | `BROKER_WIRE` | Real, autonomy-critical commit dispatch; satisfiable (Section 12) |
| AG2 (`pcae remote changes push`) | `BROKER_WIRE` | Real, autonomy-critical push dispatch; satisfiable |
| AG3 (`pcae remote rollback execute`) | `BROKER_WIRE` — **blocked pending approval-evidence phase (Section 12.1)** | Real mutation, correctly gated by POL-004; not satisfiable today |
| AG4 (`pcae promote` apply) | `BROKER_WIRE` — highest implementation priority | Highest-risk site (can target `src/pcae/**`); satisfiable as `MUTATION` class (Section 8.3) |
| AG5 (`pcae promote` restore) | `BROKER_WIRE` — **blocked pending approval-evidence phase (Section 12.1)** | Same rollback-semantics gap as AG3 |
| TK1, TK2 (`pcae task finish --commit`) | `LIFECYCLE_INTERNAL / DEFERRED_COVERAGE` | Real commit, but mechanically restricted to task-closure paths only (staged-file-aware conflict check rejects any other staged content); not an autonomy-critical adoption pipeline (Section 16) — justified exclusion, not a silent drop (RWMPC-REQ-007) |
| TK3 (`pcae task finish recover`) | `LIFECYCLE_INTERNAL / DEFERRED_COVERAGE` | Same rationale as TK1/TK2 |
| PH1 (backend-created-output-adoption commit) | `BROKER_WIRE`, consolidated with AG1 rather than built as a fourth pipeline | Real, autonomy-critical, currently ungated |
| PH2 (backend-created-output-adoption push) | `ROUTE_TO_CANONICAL_COMMAND` | Duplicates `pcae push`/AG2 semantics; must not become a third independent push implementation |
| PH3 (final-verification-tooling push) | `ROUTE_TO_CANONICAL_COMMAND` | Same rationale; retains its `--approved-by`/`--reason` as a future *input signal* for evidence work, not as `approval_present` today |

RWMPC-REQ-034: No in-scope real mutation path (Section 4) is left
without a disposition. `RETIRE` and unqualified `OUT_OF_SCOPE` are not
used above because independent review found no in-scope site that
should simply be deleted or excluded without justification.

## 15. Canonical Routing and Direct-Dispatch Prohibition

RWMPC-REQ-035: Every site marked `ROUTE_TO_CANONICAL_COMMAND` (PH2,
PH3) SHALL, upon implementation, stop performing independent `git push`
dispatch and instead invoke the same adapter `pcae push`/AG2 use.

RWMPC-REQ-036: Upon implementation of each `BROKER_WIRE` site, no
alternate code path in the codebase SHALL construct a competing
`PermissionBrokerRequest` for the same mutation class outside its
designated adapter — this includes consolidating `push.py:698` and
`push.py:898`'s existing duplicate construction onto one shared
push-adapter call, a pre-existing duplication this contract does not
require resolving in 149C itself (no `src/pcae/**` change) but binds
a future implementation phase to address.

RWMPC-REQ-037: **Non-bypassability.** Every autonomy-critical
production repository mutation dispatch SHALL be statically
traceable (by code inspection: the dispatch function's only caller
path includes its class's adapter) and dynamically traceable (by test:
no code path reaches `subprocess.run(["git", ...])` or a raw
`write_text`/`write_bytes`/`unlink` on an in-scope target without a
preceding adapter call) to a valid Permission Broker decision
consumption point. A future implementation phase SHALL demonstrate
both, not just one.

## 16. Threat Model

RWMPC-REQ-038: This contract's threat model extends PBPC-001 §22-24's
categories to every in-scope path:

| Threat | Control |
|---|---|
| Direct mutation bypass | Adapters become the sole sanctioned dispatch path per class (RWMPC-REQ-035/037) |
| Agent self-permission | RWMPC-REQ-022/023 |
| Legacy alternate path | Explicit disposition, no path left ambiguous (Section 14) |
| Stale `ALLOW` (decision reused for a changed operation) | Decision lifetime, per-attempt only (RWMPC-REQ-039) |
| Execution-class downgrading | RWMPC-REQ-016 |
| Policy exclusion (caller-selected policy set) | RWMPC-REQ-016 |
| Approval fabrication | RWMPC-REQ-023/025; Section 12.1 records rather than papers over the gap |
| Confirmation-as-approval | RWMPC-REQ-023 |
| Partial mutation | RWMPC-REQ-041 |
| Rollback abuse (rollback as a bypass for unrelated mutation) | Rollback target/intent bound to the original governed commit via existing ancestry/eligibility checks (Section 9); Permission Broker coverage additionally blocked pending Section 12.1 |
| Mechanical override | Section 9 checks preserved unweakened |
| Promotion-authorization spoofing | `--promotion-authorized` independently confirmed non-trusted (RWMPC-REQ-024); not treated as `approval_present` |
| **Self-modification** (mutation alters PCAE's own governance/permission code via `pcae promote` targeting `src/pcae/**`) | AG4 is the highest-priority `BROKER_WIRE` site precisely because of this threat (RWMPC-REQ-033); this contract records the risk and requires `BROKER_WIRE` coverage but does not itself add a protected-path hard block — that remains a mechanical (command-owned, Section 9) control for a future implementation phase to add if evidence supports it, per the instruction not to invent a hard block without authority |
| New mutation path appearing without coverage | RWMPC-REQ-042 |

RWMPC-REQ-039: Permission decisions SHALL be operation-specific,
attempt-specific, non-transferable, and non-cacheable across a changed
operation — no "mutation authorized for this session/agent" broad
token. Freshness/operation-binding facts differ by class (Section 17)
but the non-reuse principle is uniform.

RWMPC-REQ-040: Permission SHALL be established before the first
irreversible mutation step of any in-scope operation. For AG4's
per-file apply loop specifically, the existing PER (`in_progress`
before the first write) SHALL continue recording state before any
write, and the Permission Broker decision SHALL be obtained before
that first write, not interleaved per-file.

RWMPC-REQ-041: Multi-step/multi-file operations (AG4 in particular)
bind to their *existing* partial-outcome semantics
(`final_status: partial/failed/completed/aborted_divergence`, already
implemented in the current PER model) — this contract does not invent
new transaction/atomicity behavior.

RWMPC-REQ-042: Any future production mutation path added under Chapter
149's scope SHALL declare its `action_type`, `execution_class`,
permission-boundary adapter, and freshness model (Section 17) before
becoming CLI-dispatch-reachable. This is a requirement on future
implementation phases, not a mechanism this contract itself builds.

## 17. Freshness / Operation Binding

RWMPC-REQ-043: Chapter 148's freshness mechanism (`push.py`'s
decision-bound snapshot, PBPC-001 §16/17) SHALL generalize per class,
not uniformly:

| Class | Decision-bound facts to re-observe before dispatch |
|---|---|
| Commit | `HEAD`, index/staged-content identity (the set of paths being committed), `task_id` |
| Push (non-`pcae push`) | `HEAD`, target branch, unpushed-commit identity, `task_id` — same shape as PBPC-001's existing push snapshot |
| Rollback | Current `HEAD`, rollback target commit SHA, branch, task/job identity |
| Source/working-tree mutation (AG4) | Candidate content identity (already hashed per-file in the existing PER `before_hash`/`after_hash`), target path, repository divergence state — reusing ECP/EPR/PER's existing integrity model rather than duplicating it |

RWMPC-REQ-044: This contract does not require a durable Permission
Broker decision artifact (no new schema) — consistent with Chapter
148's precedent (in-process decision only). Whether AG4's existing PER
model, extended, is sufficient as a durable mutation receipt is left to
a future implementation phase's evidence, not decided here (149B §28's
open question is preserved, not resolved).

## 18. Relationship to Runtime Enforcement and the Governed Execution-Attempt Boundary

RWMPC-REQ-045: Repository-Wide Mutation Permission Coverage remains
parallel to, not routed through, Runtime Enforcement, for as long as
Model E (149B §18) remains selected — consistent with PBPC-001 §25.
A future implementation phase SHALL NOT silently route any in-scope
direct git/file mutation through Runtime Enforcement without a
separate contract amendment authorizing that.

RWMPC-REQ-046: For agent-driven mutation, permission evaluation occurs
*before* dispatch, at the adapter boundary defined in Section 6 — this
is upstream of, not inside, any governed execution-attempt boundary
that governs shell/backend/adapter invocation (a distinct domain per
RWMPC-REQ-011).

RWMPC-REQ-047: `agent proposes mutation → trusted PCAE mutation adapter
constructs the canonical request (Section 6) → Permission Broker
decides → trusted PCAE dispatch executes.` The agent constructs no
part of the canonical request's `action_type`, `execution_class`, or
`approval_present` fields (RWMPC-REQ-022).

## 19. Compatibility

RWMPC-REQ-048: PBPC-001 v1.2 remains unamended and continues to
exclusively govern `pcae push` (PU1, PU2). This contract does not
duplicate or redefine PBPC-001's push semantics; other push-shaped
sites (AG2, PH2, PH3) either route to the canonical `pcae push`
adapter or consume equivalent broker semantics via their own adapter,
per Section 14/15.

RWMPC-REQ-049: PBPA-001 v1.0 remains unamended.
`applicable_policy_ids`/`non_applicable_policy_ids` resolution for
every in-scope request under this contract uses PBPA-001's existing
predicate unchanged — independently verified: no in-scope operation's
truthful classification (Section 8) required a PBPA-001 amendment to
resolve (the one gap found, Section 12.1, is an evidence-availability
gap, not an applicability-model gap).

RWMPC-REQ-050: Layering, most-foundational first:

```
PBPA-001 (policy applicability)
  -> Permission Broker Foundation (Phase 108A-C)
    -> PBPC-001 v1.2 (pcae push specialization)
    -> RWMPC-001 v1.0 (this contract — broader mutation coverage,
       additive, not overlapping PBPC-001's push domain)
```

## 20. Truthfulness and Missing-Field Behavior

RWMPC-REQ-051: All request facts SHALL be truthful. No integration
code may manipulate `action_type`, `execution_class`,
`approval_present`, `simulation_only`, `task_id`, `evidence_available`,
or component/capability identity merely to obtain `ALLOW`.

RWMPC-REQ-052: If a required truthful field's value is unavailable at
request-construction time, the adapter SHALL fail closed (zero
dispatch) rather than fabricate a value.

## 21. Legacy Approval Flags — Final Classification

RWMPC-REQ-053: `--promotion-authorized`, `--reviewed-by`,
`--approve-keep`, `--approved-by`, `--reason`, `approve_rollback`, and
`change_approval_state` remain, respectively, unauthenticated CLI
self-declaration or mechanical state flags (Section 11). None becomes
`approval_present` evidence under this contract. This contract
introduces no new CLI approval flag and no insecure convenience shim.

## 22. Chapter Completion Criteria

RWMPC-REQ-054: Chapter 149 (this contract's implementation) is
complete only when:

1. The independently reconstructed inventory (Section 4) has every
   site's disposition satisfied (`BROKER_WIRE` implemented and
   verified, `ROUTE_TO_CANONICAL_COMMAND` implemented and verified,
   or `LIFECYCLE_INTERNAL / DEFERRED_COVERAGE` re-affirmed with
   current evidence).
2. Every `EXECUTION_CLASS_MUTATION` site constructs a truthful request
   per Section 6/8 and consumes `ALLOW`-only authorization (Section
   13).
3. `EXECUTION_CLASS_ROLLBACK` coverage (AG3, AG5) is either wired
   after a future approval-evidence phase resolves Section 12.1, or
   explicitly re-certified as still blocked with current evidence —
   Chapter 149 SHALL NOT be certified complete while claiming rollback
   coverage that does not truthfully exist.
4. No caller-selectable classification/policy mechanism exists
   anywhere in scope (RWMPC-REQ-016).
5. No agent self-permission path exists (RWMPC-REQ-022).
6. Direct-dispatch bypass is closed for every `BROKER_WIRE`/
   `ROUTE_TO_CANONICAL_COMMAND` site (RWMPC-REQ-037), independently
   verified.
7. Freshness/operation-binding (Section 17) is implemented per class.
8. Mechanical protections (Section 9) remain unweakened.
9. Zero unresolved `BLOCKING` findings remain against this contract's
   own text (a rollback-coverage gap resolved by a *separate* future
   phase does not itself block re-certifying this contract; an
   unresolved gap in this contract's own logic would).
10. Runtime remains `Observed`/`observe`/`unavailable` unless
    separately authorized.

## 23. Non-Goals

RWMPC-REQ-055: This contract does not: implement any Permission Broker
consumer; modify `src/pcae/**`; modify PBPC-001, PBPA-001, or
POL-001..012; add POL-013+; change any mutation path's current
behavior; route any command through Runtime Enforcement; implement
Prompt Generation, Prompt Dispatch, or agent invocation; or activate
runtime execution capability.

## 24. Versioning

RWMPC-REQ-056: Future amendments increment the version and append a
dated changelog entry here, following PBPC-001's convention (§ pattern
in that document). No amendment may renumber or reuse an existing
`RWMPC-REQ-###` identifier.

## 25. Freeze Verdict

**RWMPC-001 v1.0 FROZEN**, with the following exact, non-papered-over
scope: full coverage is frozen and satisfiable now for every
`EXECUTION_CLASS_MUTATION` site (PU1, PU2, AG1, AG2, AG4, PH1, PH2,
PH3 — 8 of 13 sites, plus the 2 already-certified push sites already
counted within PU1/PU2); `EXECUTION_CLASS_ROLLBACK` coverage (AG3, AG5
— 2 of 13 sites) is frozen at the *classification and requirement*
level (Section 8.3, 13, 16) but is **not implementation-ready** pending
Section 12.1's approval-evidence gap; `LIFECYCLE_INTERNAL /
DEFERRED_COVERAGE` sites (TK1-TK3 — 3 of 13 sites) are frozen with an
explicit, evidenced non-wiring rationale (Section 14) rather than left
ambiguous.

This is not a "CONTRACT NOT FROZEN" outcome: no truthful in-scope
`MUTATION`-class request is unsatisfiable, no existing contract or
policy required weakening, and the one blocking finding (Section 12.1)
is narrowly scoped, explicitly severable, and does not leave any site
without a disposition.
