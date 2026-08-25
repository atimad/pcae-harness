"""Repository-Wide Mutation Permission Coverage — Wave 1 (Phase 149F).

Implements the shared canonical mutation-permission integration primitive
planned by Phase 149E and governed by RWMPC-001 v1.0
(`docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md`),
which is additive to PBPC-001 v1.2 (`pcae push`'s own, unmodified,
certified consumption) and depends on the frozen Permission Broker
Foundation (`permission_broker_foundation.py`) unchanged.

This module is the *only* place in the codebase permitted to construct a
`PermissionBrokerRequest` for a non-`pcae push` mutation site
(RWMPC-REQ-013). It owns:

  - the shared low-level evaluation primitive
    (`evaluate_repository_mutation_permission`), mirroring
    `push.py:_evaluate_push_permission`'s exact shape (PBPC-001 v1.2);
  - three thin per-class adapters (commit, alternate-push,
    source-mutation/promotion) and their operation-specific freshness
    snapshots (RWMPC-001 Section 17).

It is not a new policy engine, not a replacement Permission Broker, not a
universal mutation executor, and not a Runtime Enforcement adapter
(RWMPC-001 Section 4/13 of the governing 149F instruction). `action_type`,
`execution_class`, `requested_component`, and `requested_capability` are
fixed literals inside this module's adapter functions -- never threaded
from a caller argument, CLI flag, or config value (RWMPC-REQ-016).

Every adapter here sets `simulation_only=True` (RWMPC-REQ-014/015) and
`approval_present=False` (RWMPC-REQ-017: POL-004 is not applicable to
`EXECUTION_CLASS_MUTATION`, so `False` is the *truthful* value, not a
weakening) for every Wave-1 `MUTATION`-class site. Rollback-class sites
(AG3, AG5) are explicitly out of Wave-1 scope and are not wired here.
"""

from __future__ import annotations

from dataclasses import dataclass
import subprocess

from pcae.core.paths import HarnessPath

# ═══════════════════════════════════════════════════════════════════════════
# Shared low-level primitive
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class MutationPermissionResult:
    """Mirrors `push.py:PushPermissionResult`'s shape. `authorized` is True
    only for a literal `DECISION_ALLOW` on a valid `PermissionBrokerDecision`
    (RWMPC-REQ-030). A broker construction/evaluation exception or a
    malformed result leaves `decision` as `None` and populates
    `broker_failure_reason` (RWMPC-REQ-029)."""

    authorized: bool
    request: "permission_broker_foundation.PermissionBrokerRequest"
    decision: "permission_broker_foundation.PermissionBrokerDecision | None"
    broker_failure_reason: str | None = None


def evaluate_repository_mutation_permission(
    *,
    root: HarnessPath,
    action_type: str,
    execution_class: str,
    requested_component: str,
    requested_capability: str,
    task_id: str | None,
    requested_resource: str | None,
    evidence_available: bool,
    approval_present: bool,
    simulation_only: bool,
    broker: "permission_broker_foundation.PermissionBroker | None" = None,
) -> MutationPermissionResult:
    """RWMPC-001 v1.0 canonical Decision Consumption Point for every
    in-scope, non-`pcae push` repository mutation. Constructs exactly one
    `PermissionBrokerRequest` via `build_permission_broker_request`
    (RWMPC-REQ-013), evaluates it against the unmodified default Foundation
    registry (no per-call custom policy registry, no policy subset,
    RWMPC-REQ-016), and returns `authorized=True` only for `DECISION_ALLOW`.
    Performs no dispatch and no repository mutation itself -- callers
    remain solely responsible for the real `git`/filesystem operation,
    after separately re-validating freshness (Section 17) immediately
    before dispatch.

    Broker construction and evaluation share one exception boundary
    (mirroring Chapter 148's Phase 148G.1 hardening precedent,
    `push.py:_evaluate_push_permission`): a construction failure is
    diagnostically identical to an evaluation failure, and both fail
    closed.
    """
    from pcae.core import permission_broker_foundation

    request = permission_broker_foundation.build_permission_broker_request(
        action_type=action_type,
        execution_class=execution_class,
        requested_component=requested_component,
        requested_capability=requested_capability,
        task_id=task_id,
        requested_resource=requested_resource,
        evidence_available=evidence_available,
        approval_present=approval_present,
        simulation_only=simulation_only,
    )

    try:
        broker_instance = (
            broker if broker is not None else permission_broker_foundation.PermissionBroker()
        )
        decision = broker_instance.evaluate(request)
    except Exception as error:
        return MutationPermissionResult(
            authorized=False,
            request=request,
            decision=None,
            broker_failure_reason=str(error),
        )

    if not isinstance(decision, permission_broker_foundation.PermissionBrokerDecision):
        return MutationPermissionResult(
            authorized=False,
            request=request,
            decision=None,
            broker_failure_reason="invalid_broker_result",
        )

    return MutationPermissionResult(
        authorized=decision.decision == permission_broker_foundation.DECISION_ALLOW,
        request=request,
        decision=decision,
    )


def permission_denial_details(result: MutationPermissionResult) -> dict:
    """Structured, non-secret diagnostics for a non-authorized result,
    distinguishing broker failure from `DENY`/`HUMAN_REVIEW` -- mirrors
    `push.py:_permission_denial_details` exactly."""
    if result.decision is None:
        return {
            "permission_decision": "BROKER_FAILURE",
            "permission_reason": result.broker_failure_reason or "unknown_broker_failure",
            "permission_causing_policy_ids": [],
        }
    return {
        "permission_decision": result.decision.decision,
        "permission_reason": result.decision.decision_reason,
        "permission_causing_policy_ids": list(result.decision.causing_policy_ids),
    }


# ═══════════════════════════════════════════════════════════════════════════
# Observation helpers (fail-closed: return None on any observation failure,
# never a fabricated empty-string/zero fallback -- item 16 of the governing
# instruction)
# ═══════════════════════════════════════════════════════════════════════════


# Git's own ref-update-hook convention for "no commit exists" (the
# all-zero object id). Used here as a stable, comparable, truthful
# observed value for a repository that genuinely has no commits yet
# (`git rev-parse HEAD` fails with "unknown revision" in that case) --
# distinct from `None`, which is reserved for a *failed* observation
# (subprocess timeout/exception). A repo with no HEAD both at decision
# time and at dispatch time is a real, unchanged state, not an
# unobservable one; a repo that gains its first commit between the two
# observations is a real, detectable HEAD change (`_NULL_SHA` ->
# real sha).
_NULL_SHA = "0" * 40


def _git_rev_parse_head(root: HarnessPath) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root.path,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        # Non-zero without an exception is git's normal "no commits yet"
        # signal (empty repository) -- a real, observable state, not a
        # failure. Any other unexpected non-zero cause is still
        # truthfully represented as "no HEAD currently observable",
        # which correctly forces a mismatch (and therefore fail-closed)
        # against any snapshot where a real HEAD had been observed.
        return _NULL_SHA
    head = result.stdout.strip()
    return head or _NULL_SHA


def _git_write_tree(root: HarnessPath) -> str | None:
    try:
        result = subprocess.run(
            ["git", "write-tree"],
            cwd=root.path,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    tree = result.stdout.strip()
    return tree or None


def _git_count_commits_ahead(root: HarnessPath, remote: str, branch: str) -> int | None:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", f"{remote}/{branch}..HEAD"],
            cwd=root.path,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Commit-class adapter (AG1, PH1) -- RWMPC-001 Section 8, Table 8.1 "Commit"
# ═══════════════════════════════════════════════════════════════════════════

_COMMIT_COMPONENT = "COMP-001"
_COMMIT_CAPABILITY = "pcae_remote_commit"


@dataclass(frozen=True)
class CommitDecisionSnapshot:
    """RWMPC-001 Section 17: `HEAD`, staged-content identity (`git
    write-tree` -- binds the exact tree that would be committed, unlike
    `git diff --cached --name-only` which binds filenames only, not
    content), `task_id`. `observation_complete=False` means at least one
    decision-bound fact could not be observed -- callers must treat this
    as an unconditional fail-closed freshness failure, never as a
    trivially-matching empty value (item 16 of the governing instruction).
    """

    head: str | None
    staged_tree: str | None
    task_id: str | None
    observation_complete: bool


def observe_commit_decision_state(root: HarnessPath, task_id: str | None) -> CommitDecisionSnapshot:
    head = _git_rev_parse_head(root)
    staged_tree = _git_write_tree(root)
    return CommitDecisionSnapshot(
        head=head,
        staged_tree=staged_tree,
        task_id=task_id,
        observation_complete=head is not None and staged_tree is not None,
    )


def evaluate_commit_permission(
    root: HarnessPath, task_id: str | None
) -> tuple[MutationPermissionResult, CommitDecisionSnapshot]:
    """Shared commit-class adapter for AG1 (`commit_file_changes`) and PH1
    (backend-created-output-adoption commit), consolidated per RWMPC-001
    Section 14 (PH1 disposition: "consolidated with AG1 rather than built
    as a fourth pipeline"). The adapter evaluates permission for "commit
    the currently staged content, truthfully" -- it does not need to know
    which caller invoked it; both callers have already independently
    passed their own mechanically-restricted target-file validation before
    reaching this call (RWMPC-REQ-020 preserved unweakened)."""
    from pcae.core import permission_broker_foundation

    snapshot = observe_commit_decision_state(root, task_id)
    result = evaluate_repository_mutation_permission(
        root=root,
        action_type=permission_broker_foundation.ACTION_COMMIT,
        execution_class=permission_broker_foundation.EXECUTION_CLASS_MUTATION,
        requested_component=_COMMIT_COMPONENT,
        requested_capability=_COMMIT_CAPABILITY,
        task_id=task_id,
        requested_resource=None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    return result, snapshot


def validate_commit_permission_freshness(
    root: HarnessPath, snapshot: CommitDecisionSnapshot
) -> tuple[bool, list[str]]:
    """Immediately-before-dispatch re-observation (RWMPC-001 Section 17).
    Any mismatch -- including an observation failure at decision time or
    re-observation time -- is material: the caller SHALL NOT dispatch
    using the existing decision and must obtain a fresh one."""
    if not snapshot.observation_complete:
        return False, ["commit-bound state could not be observed at permission-decision time"]

    from pcae.core.tasks import find_latest_active_task

    current = observe_commit_decision_state(root, snapshot.task_id)
    if not current.observation_complete:
        return False, ["commit-bound state could not be re-observed before dispatch"]

    active_task = find_latest_active_task(root)
    current_task_id = active_task.task_id if active_task else None

    mismatches: list[str] = []
    if current.head != snapshot.head:
        mismatches.append(f"local HEAD changed ({snapshot.head} -> {current.head})")
    if current.staged_tree != snapshot.staged_tree:
        mismatches.append("staged content changed since permission decision")
    if current_task_id != snapshot.task_id:
        mismatches.append(f"active task changed ({snapshot.task_id} -> {current_task_id})")

    return (not mismatches, mismatches)


# ═══════════════════════════════════════════════════════════════════════════
# Alternate-push adapter (AG2, direct; PH2/PH3, routed) -- RWMPC-001
# Section 8, Table 8.1 "Push (alternate dispatch, pending routing)"
# ═══════════════════════════════════════════════════════════════════════════

_PUSH_COMPONENT = "COMP-001"
_PUSH_CAPABILITY = "pcae_remote_push"


@dataclass(frozen=True)
class AlternatePushDecisionSnapshot:
    """RWMPC-001 Section 17: `HEAD`, target branch, unpushed-commit
    identity, `task_id` -- same shape as PBPC-001's existing push
    snapshot, generalized to the `git push <remote> HEAD:<branch>` shape
    AG2/PH2/PH3 share (distinct from `pcae push`'s own upstream-tracking
    push -- Chapter 148's `push.py` is not reused or modified)."""

    head: str | None
    remote: str
    branch: str
    unpushed: int | None
    task_id: str | None
    observation_complete: bool


def observe_alternate_push_decision_state(
    root: HarnessPath, remote: str, branch: str, task_id: str | None
) -> AlternatePushDecisionSnapshot:
    head = _git_rev_parse_head(root)
    unpushed = _git_count_commits_ahead(root, remote, branch)
    return AlternatePushDecisionSnapshot(
        head=head,
        remote=remote,
        branch=branch,
        unpushed=unpushed,
        task_id=task_id,
        observation_complete=head is not None and unpushed is not None,
    )


def evaluate_alternate_push_permission(
    root: HarnessPath, remote: str, branch: str, task_id: str | None
) -> tuple[MutationPermissionResult, AlternatePushDecisionSnapshot]:
    """Shared alternate-push adapter for AG2 (`push_file_changes`) and, via
    `agent._dispatch_governed_push`, PH2/PH3's routed dispatch
    (RWMPC-REQ-035). Evaluated exactly once per concrete dispatch attempt
    -- PH2/PH3 routing to this adapter does not add a second broker
    evaluation on top of their own existing mechanical gates."""
    from pcae.core import permission_broker_foundation

    snapshot = observe_alternate_push_decision_state(root, remote, branch, task_id)
    result = evaluate_repository_mutation_permission(
        root=root,
        action_type=permission_broker_foundation.ACTION_PUSH,
        execution_class=permission_broker_foundation.EXECUTION_CLASS_MUTATION,
        requested_component=_PUSH_COMPONENT,
        requested_capability=_PUSH_CAPABILITY,
        task_id=task_id,
        requested_resource=f"refs/heads/{branch}",
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    return result, snapshot


def validate_alternate_push_permission_freshness(
    root: HarnessPath, snapshot: AlternatePushDecisionSnapshot
) -> tuple[bool, list[str]]:
    if not snapshot.observation_complete:
        return False, ["push-bound state could not be observed at permission-decision time"]

    from pcae.core.tasks import find_latest_active_task

    current = observe_alternate_push_decision_state(
        root, snapshot.remote, snapshot.branch, snapshot.task_id
    )
    if not current.observation_complete:
        return False, ["push-bound state could not be re-observed before dispatch"]

    active_task = find_latest_active_task(root)
    current_task_id = active_task.task_id if active_task else None

    mismatches: list[str] = []
    if current.head != snapshot.head:
        mismatches.append(f"local HEAD changed ({snapshot.head} -> {current.head})")
    if current.unpushed != snapshot.unpushed:
        mismatches.append(
            f"unpushed commit count changed ({snapshot.unpushed} -> {current.unpushed})"
        )
    if current_task_id != snapshot.task_id:
        mismatches.append(f"active task changed ({snapshot.task_id} -> {current_task_id})")

    return (not mismatches, mismatches)


# ═══════════════════════════════════════════════════════════════════════════
# Source-mutation adapter (AG4 -- promotion apply) -- RWMPC-001 Section 8,
# Table 8.1 "Working-tree/source mutation (promotion apply)"
# ═══════════════════════════════════════════════════════════════════════════

_PROMOTION_COMPONENT = "COMP-001"
_PROMOTION_CAPABILITY = "pcae_promotion_apply"


def classify_promotion_action_type(approved_paths: "list[str] | tuple[str, ...]") -> str:
    """Per-target-path category classification (RWMPC-001 Section 8.1),
    reusing the existing repository-native `src/`/`tests/`/`docs/`
    path-prefix convention already used for mutation classification
    elsewhere in PCAE (`shell_gate.py:_categorize_redirection_target`) --
    no new invented taxonomy. One broker decision covers the entire
    bounded apply operation (RWMPC-001 Section 9.3/16), so when
    `approved_paths` spans more than one category, the highest-risk
    category present is used: `src/` (can include `src/pcae/**` itself,
    RWMPC-001's own highest-priority self-modification concern) takes
    precedence over `tests/`, which takes precedence over `docs/`. This
    does not change the broker's decision (POL-006 only checks
    `action_type` membership in `KNOWN_ACTION_TYPES`, never differentiates
    among the three `MUTATION`-class action types) -- it is a truthful,
    non-caller-selected diagnostic classification only.
    """
    from pcae.core import permission_broker_foundation

    if any(path.startswith("src/") for path in approved_paths):
        return permission_broker_foundation.ACTION_SOURCE_MUTATION
    if any(path.startswith("tests/") for path in approved_paths):
        return permission_broker_foundation.ACTION_TEST_MUTATION
    if any(path.startswith("docs/") for path in approved_paths):
        return permission_broker_foundation.ACTION_DOCS_MUTATION
    return permission_broker_foundation.ACTION_SOURCE_MUTATION


@dataclass(frozen=True)
class PromotionDecisionSnapshot:
    """RWMPC-001 Section 17: reuses the existing ECP/EPR/PER integrity
    model (no new digest invented, RWMPC-REQ-043) -- bound facts are EPR
    id, ECP id, `approved_paths` set identity, and `task_id`. Candidate
    content identity is already the existing per-file `before_hash`/
    `after_hash` on the ECP/EPR record; this snapshot does not duplicate
    it, it binds *which* approved-paths/EPR/ECP triple the `ALLOW`
    decision covers."""

    epr_id: str
    ecp_id: str | None
    approved_paths: tuple[str, ...]
    task_id: str | None


def evaluate_promotion_permission(
    root: HarnessPath,
    task_id: str | None,
    epr_id: str,
    ecp_id: str | None,
    approved_paths: "list[str] | tuple[str, ...]",
) -> tuple[MutationPermissionResult, PromotionDecisionSnapshot]:
    """AG4's adapter, called once per bounded promotion-apply operation
    (RWMPC-REQ-040/041): after the existing divergence check and PER
    `in_progress` persistence, strictly before the apply loop's first
    file write/unlink."""
    from pcae.core import permission_broker_foundation

    approved_paths_tuple = tuple(approved_paths)
    action_type = classify_promotion_action_type(approved_paths_tuple)
    result = evaluate_repository_mutation_permission(
        root=root,
        action_type=action_type,
        execution_class=permission_broker_foundation.EXECUTION_CLASS_MUTATION,
        requested_component=_PROMOTION_COMPONENT,
        requested_capability=_PROMOTION_CAPABILITY,
        task_id=task_id,
        requested_resource=",".join(sorted(approved_paths_tuple)) or None,
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
    snapshot = PromotionDecisionSnapshot(
        epr_id=epr_id,
        ecp_id=ecp_id,
        approved_paths=approved_paths_tuple,
        task_id=task_id,
    )
    return result, snapshot


def validate_promotion_permission_freshness(
    snapshot: PromotionDecisionSnapshot,
    *,
    current_epr_id: str,
    current_ecp_id: str | None,
    current_approved_paths: "list[str] | tuple[str, ...]",
    current_task_id: str | None,
) -> tuple[bool, list[str]]:
    """Immediately-before-first-mutation re-observation. The caller
    supplies freshly re-derived facts (this module intentionally does not
    import `agent.py`'s EPR/ECP lookup helpers, to avoid a
    core-module-imports-command-module-internals cycle -- `agent.py`
    re-reads its own records and passes the current values in)."""
    mismatches: list[str] = []
    if current_epr_id != snapshot.epr_id:
        mismatches.append(f"EPR id changed ({snapshot.epr_id} -> {current_epr_id})")
    if current_ecp_id != snapshot.ecp_id:
        mismatches.append(f"ECP id changed ({snapshot.ecp_id} -> {current_ecp_id})")
    if tuple(current_approved_paths) != snapshot.approved_paths:
        mismatches.append("approved_paths changed since permission decision")
    if current_task_id != snapshot.task_id:
        mismatches.append(f"active task changed ({snapshot.task_id} -> {current_task_id})")
    return (not mismatches, mismatches)


# ═══════════════════════════════════════════════════════════════════════════
# Publication adapter (CHGR/publication-path gap closure) -- Phase
# 149O.20L.7O.3C.2, closing the gap 3C.1 §7.3/§10 identified: CHGR
# publication (`PublicationCoordinator.execute()`, via
# `PublicationApplicationService.hand_off`) was the one root/external-
# effect-adjacent action with no Permission Broker coverage at all.
# ═══════════════════════════════════════════════════════════════════════════

_PUBLICATION_COMPONENT = "COMP-001"
_PUBLICATION_CAPABILITY = "pcae_governance_record_publish"


def evaluate_publication_permission(
    root: HarnessPath,
    *,
    session_id: str,
    package_id: str,
    task_id: str | None,
) -> MutationPermissionResult:
    """Publication adapter for `PublicationApplicationService.hand_off`
    (Phase 149O.20L.7O.3C.2). Evaluated once per hand-off attempt,
    strictly before `PublicationCoordinator.execute()` is invoked --
    mirroring every other Wave-1 adapter's "gate before the real effect,
    never after" placement.

    `action_type` uses the existing `ACTION_DOCS_MUTATION` literal, not a
    new invented action type (RWMPC-REQ-016's "fixed literals" discipline,
    and Phase 149O.20L.7O.3C.2's own "no new invented taxonomy" scope
    rule): a CHGR record is a structured governance document written to
    `.pcae/governance-records/**`, the same shape of repository-adjacent
    write `classify_promotion_action_type` already classifies as a
    `docs`-class mutation when a promotion's approved paths land under
    `docs/`. `execution_class` is `EXECUTION_CLASS_MUTATION`, identical to
    every other Wave-1 site -- publication is not a new execution class,
    it is the same `simulation_only=True`, non-authoritative broker
    evaluation every existing adapter performs.

    Session identity (`session_id`) and package identity (`package_id`)
    are surfaced as the requested resource -- not `task_id` alone --
    because a publication attempt's decision-relevant identity is the
    Confirmable Decision Session/readiness package being published, which
    may or may not have an active PCAE task bound (`task_id` may be
    `None`, e.g. a human running `governance-record publish` directly by
    hand outside any governed task)."""
    from pcae.core import permission_broker_foundation

    return evaluate_repository_mutation_permission(
        root=root,
        action_type=permission_broker_foundation.ACTION_DOCS_MUTATION,
        execution_class=permission_broker_foundation.EXECUTION_CLASS_MUTATION,
        requested_component=_PUBLICATION_COMPONENT,
        requested_capability=_PUBLICATION_CAPABILITY,
        task_id=task_id,
        requested_resource=f"session:{session_id};package:{package_id}",
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
    )
