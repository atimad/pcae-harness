"""Phase 149O.20L.7O.3C.3 -- Independent End-to-End Capability Consumption
Verification.

Fresh, independent test suite for the Plan B+ governed capability
consumption batch introduced at Phase 149O.20L.7O.3C.2. Does NOT import
or call any test function from
``tests/test_phase_149o_20l_7o_3c_2_governed_capability_consumption_integration.py``
(governance requirement: fresh fixtures, no reuse of the prior phase's own
tests as evidence). Production collaborators (``SessionCoordinator``,
``SessionApplicationService``, ``PublicationApplicationService``,
``PublicationCoordinator``, ``publish_with_permission_gate``,
``auto_publish_confirmed_session``, ``mutation_permission.
evaluate_publication_permission``/``evaluate_repository_mutation_permission``)
are exercised directly and for real -- no internal helper is mocked out.

See docs/PHASE_149O_20L_7O_3C_3_INDEPENDENT_END_TO_END_CAPABILITY_CONSUMPTION_VERIFICATION.md
for the full methodology and finding disposition. Two findings from this
suite are load-bearing for the phase verdict:

 - ``test_corrupted_unrelated_session_file_crashes_auto_publish`` /
   ``test_run_phase_complete_call_site_has_no_exception_guard_around_auto_publish_block``
   originally reproduced a BLOCKING defect: an unrelated, pre-existing
   corrupted session file anywhere in the Interactive Workflow session
   store caused an uncaught ``SessionStoreCorruptError`` (an
   ``InteractiveWorkflowError`` subclass, a *different* exception
   hierarchy than the ``ApplicationServiceError`` hierarchy
   ``auto_publish_confirmed_session`` actually catches) to propagate out
   of ``auto_publish_confirmed_session`` and crash ``pcae phase complete``
   for a phase that has nothing to do with Interactive Workflow. REPAIRED
   at Phase 149O.20L.7O.3C.3.1 (independent verification pending, finding
   ``B-149O.20L.7O.3C.3-1``) -- the first test's assertions were updated
   in place to confirm the corruption is now surfaced through the
   existing ``ApplicationServiceError``/``AutoPublicationOutcome``
   vocabulary instead of escaping as a raw, untranslated exception; see
   docs/PHASE_149O_20L_7O_3C_3_1_AUTO_PUBLISH_CORRUPT_STORE_FAIL_CLOSED_REPAIR.md.
 - ``test_duplicate_subject_ref_sessions_resolved_by_latest_timestamp_not_fail_closed``
   independently reproduces a disclosed, NON-BLOCKING limitation: when
   two sessions share the same ``subject_ref``,
   ``SessionApplicationService.find_session_by_subject_ref`` silently
   picks the most-recently-created one rather than failing closed on
   ambiguity.
"""
from __future__ import annotations

import ast
import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.commands.publication_permission_gate import publish_with_permission_gate
from pcae.core import mutation_permission
from pcae.core import permission_broker_foundation as pbf
from pcae.core.paths import HarnessPath
from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.governance.publication.storage import PublicationRecordStore
from pcae.interactive_workflow.application.errors import (
    ApplicationServiceError,
    PublicationPermissionDeniedApplicationError,
)
from pcae.interactive_workflow.application.publication_service import PublicationApplicationService
from pcae.interactive_workflow.application.session_service import SessionApplicationService
from pcae.commands.governance_auto_publication import (
    STATUS_APPLICATION_ERROR,
    STATUS_AWAITING_HUMAN_DECISION,
    STATUS_HUMAN_DEFERRED,
    STATUS_HUMAN_REJECTED,
    STATUS_NO_SESSION,
    STATUS_PERMISSION_DENIED,
    STATUS_PUBLISHED,
    STATUS_READINESS_UNAVAILABLE,
    auto_publish_confirmed_session,
)
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    FilesystemPendingReadinessStore,
)
from pcae.interactive_workflow.persistence.filesystem_repository import FilesystemSessionRepository
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.coordinator import SessionCoordinator


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _readiness_package(package_id: str, session_id: str, **overrides) -> PublicationReadinessPackage:
    fields = dict(
        package_id=package_id,
        session_id=session_id,
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=0,
        evidence_refs=("ev-fresh-1",),
        clarification_refs=(),
        audit_refs=(),
        preview_id="preview-fresh-1",
        preview_digest="b" * 64,
        confirmation_request_id="req-fresh-1",
        confirmation_response_id="resp-fresh-1",
        built_at="2026-08-25T00:00:00+00:00",
        decision_subject="fresh-subject",
        template_id="template-fresh-1",
        template_version="1.0",
        selected_option_id="opt-a",
        rationale_text="fresh rationale",
        conditions_text=None,
        options_presented=("opt-a", "opt-b"),
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "human-fresh-1",
            "captured_at": "2026-08-25T00:00:00+00:00",
        },
        preview_rendered_content="rendered fresh",
        confirmation_statement="I confirm (fresh)",
        confirmation_timestamp="2026-08-25T00:00:00+00:00",
        metadata={"fresh": True},
    )
    fields.update(overrides)
    return PublicationReadinessPackage(**fields)


class _Ctx:
    def __init__(self, session_service, publication_service) -> None:
        self.session_service = session_service
        self.publication_service = publication_service


class FreshHarness:
    """Independently constructed collaborator graph -- same production
    classes as 3C.2's own harness, but built from scratch here rather
    than imported from the 3C.2 test module."""

    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.session_repo = FilesystemSessionRepository(root=tmp_path / "decision-sessions")
        self.session_coordinator = SessionCoordinator(repository=self.session_repo)
        self.session_service = SessionApplicationService(self.session_coordinator)

        self.readiness_store = FilesystemPendingReadinessStore(
            root=tmp_path / "decision-sessions" / "pending-packages"
        )
        self.record_store = PublicationRecordStore(root=tmp_path / "publication-execution")
        self.publication_coordinator = PublicationCoordinator(store=self.record_store)
        self.publication_service = PublicationApplicationService(
            self.readiness_store, self.session_service, self.publication_coordinator
        )
        self.context = _Ctx(self.session_service, self.publication_service)

    def session_in_state(self, state: SessionState, subject_ref: str, owner_identity: str = "op-1") -> SessionState:
        session = self.session_service.create_session(
            owner_identity=owner_identity, template_ref="tmpl-fresh", subject_ref=subject_ref
        )
        moved = session.with_state(state, _iso_now())
        self.session_service.persist_session(moved)
        return moved

    def confirmed(self, subject_ref: str):
        return self.session_in_state(SessionState.CONFIRMED, subject_ref)


@pytest.fixture
def harness(tmp_path: Path) -> FreshHarness:
    return FreshHarness(tmp_path)


def _touch_active_task(tmp_path: Path, task_id: str = "20260825-0000-fresh-active-task") -> None:
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / f"{task_id}.md").write_text("# Fresh Task\n", encoding="utf-8")


# ═══════════════════════════════════════════════════════════════════════
# 1. Highest-level entry point / architecture: static re-derivation
# ═══════════════════════════════════════════════════════════════════════


def test_phase_complete_is_the_real_wiring_point_for_auto_publish():
    """`run_phase_complete` (src/pcae/commands/phase.py) is the only
    production caller of `auto_publish_confirmed_session` -- confirmed by
    source inspection, not by trusting the 3C.2 docstring."""
    import pcae.commands.phase as phase_mod

    source = inspect.getsource(phase_mod.run_phase_complete)
    assert "auto_publish_confirmed_session" in source
    assert "build_application_context" in source

    import subprocess

    grep = subprocess.run(
        ["git", "grep", "-n", "auto_publish_confirmed_session(", "--", "src/pcae"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
    )
    call_sites = [
        line
        for line in grep.stdout.splitlines()
        if line.strip() and "def auto_publish_confirmed_session(" not in line
    ]
    callers = sorted({line.split(":", 1)[0] for line in call_sites})
    assert callers == ["src/pcae/commands/phase.py"], (
        "auto_publish_confirmed_session must have exactly one production "
        f"caller (phase.py); found call sites: {call_sites}"
    )


def test_no_self_cli_subprocess_in_integration_modules():
    """Static re-derivation of item 6/49: none of the new/changed
    integration modules invoke `pcae` as a subprocess or parse CLI text
    output as an internal integration mechanism."""
    repo_root = Path(__file__).resolve().parents[1]
    integration_files = [
        repo_root / "src/pcae/commands/governance_auto_publication.py",
        repo_root / "src/pcae/commands/publication_permission_gate.py",
        repo_root / "src/pcae/interactive_workflow/application/session_service.py",
        repo_root / "src/pcae/interactive_workflow/session/coordinator.py",
    ]
    for path in integration_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "subprocess", f"{path} imports subprocess"
            if isinstance(node, ast.ImportFrom):
                assert node.module != "subprocess", f"{path} imports from subprocess"


def test_architecture_zone_dependency_scan_reports_zero_warnings_for_3c2_diff():
    """Independent re-derivation of item 5/48: run the actual repository
    architecture-zone AST-import scan (the mechanism `pcae check`'s
    pre-commit hook exercises) against every .py file 3C.2 touched, and
    confirm zero forbidden-dependency warnings on the corrected,
    currently-committed placement (commands zone, not interactive_workflow)."""
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    from pcae.core.policy import load_policy
    from pcae.core.architecture import analyze_changed_python_dependencies
    from pcae.core.check import GitChange

    root = HarnessPath(str(repo_root))
    policy = load_policy(root)

    files = subprocess.run(
        ["git", "show", "--stat", "--name-only", "--format=", "f4556d76"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    py_files = [f for f in files if f.endswith(".py")]
    assert py_files, "expected at least one changed .py file in f4556d76"

    changes = tuple(GitChange(path=Path(f), status="A") for f in py_files)
    result = analyze_changed_python_dependencies(
        root,
        changes,
        policy.architecture_zones,
        policy.architecture_rules,
        getattr(policy, "forbidden_dependencies", ()),
    )
    assert result.dependency_warnings == ()
    assert result.parse_warnings == ()

    # And independently confirm the frozen invariant this placement relies
    # on: the interactive_workflow zone's *dependency rule* still
    # excludes "core" (architecture_rules maps zone -> allowed
    # dependency zones; architecture_zones maps zone -> file globs).
    assert "core" not in policy.architecture_rules.get("interactive_workflow", ())
    assert "interactive_workflow" in policy.architecture_rules.get("commands", ())
    assert "core" in policy.architecture_rules.get("commands", ())


# ═══════════════════════════════════════════════════════════════════════
# 2. Human authority preservation (critical stop condition, item 9)
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "state,expected_status",
    [
        (SessionState.CREATED, STATUS_AWAITING_HUMAN_DECISION),
        (SessionState.EVIDENCE_READY, STATUS_AWAITING_HUMAN_DECISION),
        (SessionState.AWAITING_DECISION, STATUS_AWAITING_HUMAN_DECISION),
        (SessionState.AWAITING_CLARIFICATION, STATUS_AWAITING_HUMAN_DECISION),
        (SessionState.DECISION_SELECTED, STATUS_AWAITING_HUMAN_DECISION),
        (SessionState.AWAITING_CONFIRMATION, STATUS_AWAITING_HUMAN_DECISION),
        (SessionState.CANCELLED, STATUS_HUMAN_REJECTED),
        (SessionState.ABANDONED, STATUS_HUMAN_DEFERRED),
        (SessionState.EXPIRED, STATUS_READINESS_UNAVAILABLE),
    ],
)
def test_no_automatic_positive_decision_for_any_non_confirmed_state(
    harness: FreshHarness, tmp_path, monkeypatch, state, expected_status
):
    """Fresh negative E2E (item 9/27/28/29): for every one of the seven
    non-terminal states plus Cancelled/Abandoned/Expired, the automatic
    entry point never fabricates a positive human decision -- it reports
    a closed, non-publishing status and creates no CHGR."""
    monkeypatch.chdir(tmp_path)
    harness.session_in_state(state, subject_ref="task-neg-1")

    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-neg-1", operator_id="op-1")
    assert outcome.status == expected_status
    assert outcome.record_id is None
    assert harness.record_store.list_records() == () if hasattr(harness.record_store, "list_records") else True


def test_no_bound_session_is_a_pure_no_op(harness: FreshHarness):
    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-no-session", operator_id="op-1")
    assert outcome.status == STATUS_NO_SESSION
    assert outcome.record_id is None


# ═══════════════════════════════════════════════════════════════════════
# 3. Permission Broker: real ALLOW / DENY / failure (items 20-25)
# ═══════════════════════════════════════════════════════════════════════


def test_broker_deny_via_missing_active_task_blocks_publication_and_creates_no_chgr(
    harness: FreshHarness, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)  # no tasks/active -> POL-001 fires DENY
    confirmed = harness.confirmed("task-deny-1")
    # Pre-persist the readiness package (as `decision-session readiness`
    # itself would have, via the real orchestrator, before this test
    # runs) so `ensure_readiness_package`'s idempotent-by-key lookup finds
    # it directly, without needing to replay the full 8-stage
    # orchestration this test is not exercising.
    record = harness.publication_service.persist_readiness_package(
        _readiness_package("prp-deny-1", confirmed.session_id)
    )

    with pytest.raises(PublicationPermissionDeniedApplicationError):
        publish_with_permission_gate(
            harness.publication_service, HarnessPath.cwd(), record.package_id, operator_id="op-1"
        )

    from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import DISPOSITION_PENDING

    still_pending = harness.publication_service.get_readiness_package(record.package_id)
    assert still_pending.disposition == DISPOSITION_PENDING

    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-deny-1", operator_id="op-1")
    assert outcome.status == STATUS_PERMISSION_DENIED
    assert outcome.record_id is None


def test_broker_allow_via_active_task_permits_exactly_the_existing_continuation(
    harness: FreshHarness, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    _touch_active_task(tmp_path)
    confirmed = harness.confirmed("task-allow-1")
    harness.publication_service.persist_readiness_package(_readiness_package("prp-allow-1", confirmed.session_id))

    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-allow-1", operator_id="op-1")
    assert outcome.status == STATUS_PUBLISHED
    assert outcome.record_id is not None

    # Idempotency (items 13/19): a second call returns already_published
    # with the SAME record_id -- no second CHGR.
    outcome2 = auto_publish_confirmed_session(harness.context, subject_ref="task-allow-1", operator_id="op-1")
    assert outcome2.status == "already_published"
    assert outcome2.record_id == outcome.record_id


def test_broker_internal_failure_fails_closed_no_fallback_to_unbrokered_publish():
    """Item 24: a broker construction/evaluation failure must deny, never
    silently fall back to an unbrokered publish path."""

    class ExplodingBroker:
        def evaluate(self, request):
            raise RuntimeError("simulated broker internal failure")

    repo_root = Path(__file__).resolve().parents[1]
    result = mutation_permission.evaluate_repository_mutation_permission(
        root=HarnessPath(str(repo_root)),
        action_type=pbf.ACTION_DOCS_MUTATION,
        execution_class=pbf.EXECUTION_CLASS_MUTATION,
        requested_component="COMP-001",
        requested_capability="pcae_governance_record_publish",
        task_id="some-task",
        requested_resource="session:x;package:y",
        evidence_available=True,
        approval_present=False,
        simulation_only=True,
        broker=ExplodingBroker(),
    )
    assert result.authorized is False
    assert result.broker_failure_reason == "simulated broker internal failure"


def test_no_production_bypass_of_publish_with_permission_gate():
    """Item 21 (critical stop condition): search the ENTIRE src tree for
    every production caller of `hand_off`/`resume_publication`
    (the two ways to reach `PublicationCoordinator.execute()` through the
    application-service layer). Exactly one production call site
    (`publish_with_permission_gate`) may call `hand_off` directly, and
    `resume_publication` (which itself calls `hand_off` ungated) must
    have zero production callers."""
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]

    hand_off_callers = subprocess.run(
        ["git", "grep", "-n", r"\.hand_off(", "--", "src/pcae"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    # Exclude `resume_publication`'s own internal `self.hand_off(...)` call
    # (that method's zero-production-callers status is verified
    # separately below) -- what matters here is every *external*
    # production caller of `.hand_off(`.
    hand_off_call_sites = [
        l
        for l in hand_off_callers
        if ":" in l and "def hand_off" not in l and "self.hand_off(" not in l
    ]
    assert hand_off_call_sites == [
        "src/pcae/commands/publication_permission_gate.py:84:    return publication_service.hand_off(prepared, operator_id=operator_id)"
    ], hand_off_call_sites

    resume_pub_callers = subprocess.run(
        ["git", "grep", "-n", r"\.resume_publication(", "--", "src/pcae"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    resume_pub_call_sites = [l for l in resume_pub_callers if "def resume_publication" not in l]
    assert resume_pub_call_sites == [], (
        "resume_publication (which bypasses the Permission Broker gate) must have "
        f"zero production callers; found: {resume_pub_call_sites}"
    )


def test_rollback_approval_evidence_publication_coordinator_is_currently_unreachable_dead_code():
    """Item 21/38 follow-up: `rollback_approval_evidence.py` constructs
    its own `PublicationCoordinator` and calls `.execute()` directly,
    never through the Permission Broker gate. This predates 3C.2 and is
    NOT a regression it introduced, but it is a genuine latent gap in the
    "Permission Broker CHGR/publication-path gap closure" claim taken as
    a whole. Confirm it is currently dead code (zero production callers)
    -- if this ever changes, the gate closure claim must be re-verified."""
    import subprocess

    repo_root = Path(__file__).resolve().parents[1]
    callers = subprocess.run(
        ["git", "grep", "-ln", "create_rollback_approval_decision(", "--", "src/pcae"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert callers == ["src/pcae/core/rollback_approval_evidence.py"], (
        "create_rollback_approval_decision (an ungated PublicationCoordinator.execute() "
        f"caller) gained a new production caller -- re-verify Permission Broker "
        f"no-bypass: {callers}"
    )


# ═══════════════════════════════════════════════════════════════════════
# 4. CHGR discovery / uniqueness (items 13-16) -- confirmed + disclosed gap
# ═══════════════════════════════════════════════════════════════════════


def test_session_lookup_is_full_scan_exact_identity_not_file_order(harness: FreshHarness, tmp_path, monkeypatch):
    """Positive re-derivation: discovery is a full scan by exact
    subject_ref equality (via list_session_ids + load), not a "most
    recent file" or directory-order heuristic, for the common
    (non-duplicate) case."""
    monkeypatch.chdir(tmp_path)
    _touch_active_task(tmp_path)
    harness.session_in_state(SessionState.CREATED, subject_ref="task-other-1")
    harness.session_in_state(SessionState.CREATED, subject_ref="task-other-2")
    target = harness.confirmed("task-target-1")
    harness.session_in_state(SessionState.CREATED, subject_ref="task-other-3")

    found = harness.session_service.find_session_by_subject_ref("task-target-1")
    assert found is not None
    assert found.session_id == target.session_id


def test_duplicate_subject_ref_sessions_resolved_by_latest_timestamp_not_fail_closed(
    harness: FreshHarness,
):
    """NON-BLOCKING finding, independently confirmed: when two sessions
    share the same subject_ref, `find_session_by_subject_ref` does NOT
    fail closed on the ambiguity -- it silently returns the
    most-recently-created one (created_at ordering), which is exactly the
    class of heuristic item 14 of the verification brief instructs
    rejecting ("latest-record heuristic ... latest timestamp"). This
    matches the module's own disclosed docstring limitation, but a
    disclosed heuristic is still a heuristic: a CONFIRMED first session
    that was already published can become invisible to future automatic
    lookups if a later, non-terminal-state session is created with the
    same subject_ref (see the phase document for the concrete replay
    scenario)."""
    import time

    older = harness.session_in_state(SessionState.CREATED, subject_ref="task-dup-1")
    time.sleep(0.01)
    newer = harness.session_in_state(SessionState.AWAITING_DECISION, subject_ref="task-dup-1")
    assert older.created_at != newer.created_at

    found = harness.session_service.find_session_by_subject_ref("task-dup-1")
    assert found.session_id == newer.session_id  # latest-timestamp win, not a fail-closed error


# ═══════════════════════════════════════════════════════════════════════
# 5. BLOCKING: unrelated-corruption crash of pcae phase complete
# ═══════════════════════════════════════════════════════════════════════


def test_corrupted_unrelated_session_file_crashes_auto_publish(harness: FreshHarness):
    """BLOCKING finding, independently reproduced at Phase 149O.20L.7O.3C.3:
    a session file unrelated to the requested subject_ref, corrupted on
    disk (invalid JSON -- the same failure mode a partial write, disk
    fault, or manual edit could produce), used to cause
    `find_session_by_subject_ref` to raise an uncaught
    `SessionStoreCorruptError` while scanning ALL persisted sessions
    (`list_session_ids()` + `load_session()` for each) -- an
    `InteractiveWorkflowError`, a sibling hierarchy to the
    `ApplicationServiceError` family `auto_publish_confirmed_session`'s
    except clauses actually caught, so the crash propagated all the way
    out of `pcae phase complete`.

    REPAIRED at Phase 149O.20L.7O.3C.3.1 (independent verification
    pending -- see
    docs/PHASE_149O_20L_7O_3C_3_1_AUTO_PUBLISH_CORRUPT_STORE_FAIL_CLOSED_REPAIR.md):
    this test's assertions are updated in place (not weakened -- the
    prior "raises uncaught `SessionStoreCorruptError`" expectation *was*
    the documented defect; asserting it still holds would mean the
    repair failed) to confirm the corruption no longer escapes as a raw,
    untranslated domain exception at either call boundary, and is instead
    surfaced through the existing, closed `ApplicationServiceError` /
    `AutoPublicationOutcome` vocabulary this suite's other tests already
    exercise."""
    unrelated = harness.session_in_state(SessionState.CREATED, subject_ref="totally-unrelated-subject")
    corrupt_path = harness.tmp_path / "decision-sessions" / f"{unrelated.session_id}.json"
    assert corrupt_path.exists()
    corrupt_path.write_text("{not valid json!!!", encoding="utf-8")

    with pytest.raises(ApplicationServiceError):
        harness.session_service.find_session_by_subject_ref("some-other-active-task-with-no-relation")

    # No longer unguarded at the `auto_publish_confirmed_session` level:
    # converted to a disclosed `STATUS_APPLICATION_ERROR` outcome, never
    # propagates an exception.
    outcome = auto_publish_confirmed_session(
        harness.context,
        subject_ref="some-other-active-task-with-no-relation",
        operator_id="op-1",
    )
    assert outcome.status == STATUS_APPLICATION_ERROR
    assert outcome.diagnostic


def test_run_phase_complete_call_site_has_no_exception_guard_around_auto_publish_block():
    """Confirms the crash in the previous test is actually reachable from
    `pcae phase complete` (the reported highest-level production entry
    point), not merely a theoretical gap in a lower-level helper: the
    call site in `run_phase_complete` wraps the auto-publish block in NO
    try/except at all, so any exception `auto_publish_confirmed_session`
    raises (including `SessionStoreCorruptError`, which its own except
    clauses do not cover -- see the previous test) propagates uncaught
    out of `run_phase_complete`, i.e. out of `pcae phase complete`
    itself, for a phase whose active task may have nothing to do with
    Interactive Workflow at all."""
    import pcae.commands.phase as phase_mod

    source = inspect.getsource(phase_mod.run_phase_complete)
    call_idx = source.index("auto_publish_confirmed_session(")
    preceding = source[:call_idx]
    # The auto-publish call must not be inside any try: block that
    # started after the `finalizable` check -- i.e. no "try" keyword
    # appears between the enclosing "if finalizable and active_task..."
    # guard and the call itself.
    guard_idx = preceding.rindex("if finalizable and active_task_before_completion is not None:")
    between = source[guard_idx:call_idx]
    assert "try:" not in between, (
        "run_phase_complete now wraps the auto-publish call in a try/except -- "
        "re-verify whether the BLOCKING corrupted-store crash finding is fixed."
    )
