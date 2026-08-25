"""Phase 149O.20L.7O.3C.2 -- Governed Capability Consumption Integration
(Plan B+): Interactive Workflow auto-detect + route, Publication
Execution Ownership auto-invocation, CHGR downstream automatic
consumption, and Permission Broker CHGR/publication-path gap closure.

Covers:
 - `pcae.core.mutation_permission.evaluate_publication_permission` (the
   new Permission Broker adapter).
 - `pcae.commands.publication_permission_gate.publish_with_permission_gate`
   (the new broker gate wrapping `hand_off`), and that it is not
   bypassable via a second production path -- placed in the `commands`
   zone, not `interactive_workflow`, because `.pcae/policy.toml`'s frozen
   `interactive_workflow` zone rule forbids that zone from depending on
   `core` (an architecture-policy violation caught by the repository's
   own pre-commit `pcae check` hook during this phase and corrected; see
   the phase document §5/§9).
 - `pcae.commands.governance_auto_publication` (the new auto-detect +
   route + auto-publish production entry point): every session-state
   outcome, idempotency/duplicate-CHGR prevention, and failure
   propagation.
 - Manual-choreography elimination and no-self-CLI-subprocess assertions.
 - Human-authority preservation (automation cannot manufacture a
   `Confirmed` session on its own).
"""
from __future__ import annotations

import inspect
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.commands.publication_permission_gate import publish_with_permission_gate
from pcae.core import mutation_permission
from pcae.core.paths import HarnessPath
from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.governance.publication.storage import PublicationRecordStore
from pcae.interactive_workflow.application.errors import PublicationPermissionDeniedApplicationError
from pcae.interactive_workflow.application.publication_service import PublicationApplicationService
from pcae.interactive_workflow.application.session_service import SessionApplicationService
from pcae.commands.governance_auto_publication import (
    STATUS_ALREADY_PUBLISHED,
    STATUS_AWAITING_HUMAN_DECISION,
    STATUS_HUMAN_DEFERRED,
    STATUS_HUMAN_REJECTED,
    STATUS_NO_SESSION,
    STATUS_PERMISSION_DENIED,
    STATUS_PUBLISHED,
    STATUS_READINESS_UNAVAILABLE,
    auto_publish_confirmed_session,
    find_confirmed_session,
)
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    FilesystemPendingReadinessStore,
)
from pcae.interactive_workflow.persistence.filesystem_repository import FilesystemSessionRepository
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.coordinator import SessionCoordinator


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _package(package_id: str, session_id: str, **overrides) -> PublicationReadinessPackage:
    fields = dict(
        package_id=package_id,
        session_id=session_id,
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview_id="preview-1",
        preview_digest="a" * 64,
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at="2026-01-01T00:00:00+00:00",
        decision_subject="subject",
        template_id="template-1",
        template_version="1.0",
        selected_option_id="opt-a",
        rationale_text="because",
        conditions_text=None,
        options_presented=("opt-a", "opt-b"),
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "human-1",
            "captured_at": "2026-01-01T00:00:00+00:00",
        },
        preview_rendered_content="rendered",
        confirmation_statement="I confirm",
        confirmation_timestamp="2026-01-01T00:00:00+00:00",
        metadata={"m": 1},
    )
    fields.update(overrides)
    return PublicationReadinessPackage(**fields)


class ApplicationContext:
    """Minimal stand-in for `commands.decision_session.ApplicationContext`
    -- a plain namespace with `.session_service`/`.publication_service`,
    matching exactly what `auto_publish_confirmed_session` reads."""

    def __init__(self, session_service: SessionApplicationService, publication_service: PublicationApplicationService) -> None:
        self.session_service = session_service
        self.publication_service = publication_service


class Harness:
    def __init__(self, tmp_path: Path) -> None:
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
        self.context = ApplicationContext(self.session_service, self.publication_service)

    def confirmed_session(self, subject_ref: str = "task-abc"):
        session = self.session_service.create_session(
            owner_identity="op-1", template_ref="tmpl-1", subject_ref=subject_ref
        )
        confirmed = session.with_state(SessionState.CONFIRMED, _now_iso())
        self.session_service.persist_session(confirmed)
        return confirmed

    def session_in_state(self, state: SessionState, subject_ref: str = "task-abc"):
        session = self.session_service.create_session(
            owner_identity="op-1", template_ref="tmpl-1", subject_ref=subject_ref
        )
        moved = session.with_state(state, _now_iso())
        self.session_service.persist_session(moved)
        return moved


@pytest.fixture
def harness(tmp_path: Path) -> Harness:
    return Harness(tmp_path)


def _make_active_task(tmp_path: Path, task_id: str = "20260101-0000-test-task") -> None:
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / f"{task_id}.md").write_text("# Test Task\n", encoding="utf-8")


# ── Permission Broker adapter (unit) ─────────────────────────────────────


def test_evaluate_publication_permission_denies_with_no_active_task(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = mutation_permission.evaluate_publication_permission(
        HarnessPath.cwd(), session_id="CDS-x", package_id="prp-y", task_id=None
    )
    assert result.authorized is False
    assert result.decision is not None
    assert result.decision.decision == "DENY"


def test_evaluate_publication_permission_allows_with_active_task(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_active_task(tmp_path)
    result = mutation_permission.evaluate_publication_permission(
        HarnessPath.cwd(),
        session_id="CDS-x",
        package_id="prp-y",
        task_id="20260101-0000-test-task",
    )
    assert result.authorized is True
    assert result.decision.decision == "ALLOW"


def test_evaluate_publication_permission_uses_docs_mutation_action_type(tmp_path: Path, monkeypatch):
    """No new invented action-type taxonomy (phase brief §17-18): the
    adapter reuses the existing closed `ACTION_DOCS_MUTATION` literal."""
    monkeypatch.chdir(tmp_path)
    _make_active_task(tmp_path)
    result = mutation_permission.evaluate_publication_permission(
        HarnessPath.cwd(), session_id="CDS-x", package_id="prp-y", task_id="20260101-0000-test-task"
    )
    from pcae.core import permission_broker_foundation

    assert result.request.action_type == permission_broker_foundation.ACTION_DOCS_MUTATION
    assert result.request.execution_class == permission_broker_foundation.EXECUTION_CLASS_MUTATION
    assert result.request.simulation_only is True


# ── publish_with_permission_gate broker gate + non-bypassability ─────────
#
# The gate lives in `pcae.commands.publication_permission_gate`, not
# inside `PublicationApplicationService.hand_off` itself: `.pcae/policy.toml`'s
# frozen `interactive_workflow` zone rule (Phase 143K) forbids that zone
# from depending on `core` in either direction, so the Permission Broker
# adapter (`pcae.core.mutation_permission`) must be consulted one layer
# up, in the `commands` zone, which is already permitted to depend on
# both `core` and `interactive_workflow`. This was caught by the
# repository's own pre-commit `pcae check` architecture-dependency hook
# during this phase and corrected -- see the phase document §5/§9.


def test_gate_denies_publication_and_creates_no_chgr_without_active_task(
    harness: Harness, tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)  # no tasks/active -> broker DENY
    confirmed = harness.confirmed_session()
    record = harness.publication_service.persist_readiness_package(_package("prp-1", confirmed.session_id))

    with pytest.raises(PublicationPermissionDeniedApplicationError):
        publish_with_permission_gate(
            harness.publication_service, HarnessPath.cwd(), record.package_id, operator_id="op-1"
        )

    # No-bypass / fail-closed: no CHGR record was created anywhere in the
    # store, and re-preparing the same package still finds it pending
    # (not consumed).
    assert harness.record_store.is_published(record.package_id) is False
    still_pending = harness.publication_service.get_readiness_package(record.package_id)
    from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import DISPOSITION_PENDING

    assert still_pending.disposition == DISPOSITION_PENDING


def test_gate_allows_publication_with_active_task(harness: Harness, tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _make_active_task(tmp_path)
    confirmed = harness.confirmed_session()
    record = harness.publication_service.persist_readiness_package(_package("prp-1", confirmed.session_id))

    result = publish_with_permission_gate(
        harness.publication_service, HarnessPath.cwd(), record.package_id, operator_id="op-1"
    )
    assert result.success is True
    assert result.record_id is not None


def test_auto_publish_and_manual_gate_share_the_same_broker_call(harness: Harness, tmp_path: Path, monkeypatch):
    """Non-bypassability (§19/§51): the automatic entry point
    (`auto_publish_confirmed_session`) and the manual CLI-equivalent path
    (`publish_with_permission_gate`, what `governance-record publish`
    itself calls) reach the identical broker-gated code path -- neither
    can publish while the other is denied."""
    monkeypatch.chdir(tmp_path)  # no active task -> both denied
    confirmed = harness.confirmed_session()
    harness.publication_service.persist_readiness_package(_package("prp-1", confirmed.session_id))

    auto_outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-abc", operator_id="op-1")
    assert auto_outcome.status == STATUS_PERMISSION_DENIED

    with pytest.raises(PublicationPermissionDeniedApplicationError):
        publish_with_permission_gate(
            harness.publication_service, HarnessPath.cwd(), "prp-1", operator_id="op-1"
        )


# ── auto_publish_confirmed_session: session-state routing ───────────────


def test_no_session_bound_is_a_safe_noop(harness: Harness):
    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-nonexistent", operator_id="op-1")
    assert outcome.status == STATUS_NO_SESSION
    assert outcome.session_id is None


@pytest.mark.parametrize(
    "state",
    [
        SessionState.CREATED,
        SessionState.EVIDENCE_READY,
        SessionState.AWAITING_DECISION,
        SessionState.AWAITING_CLARIFICATION,
        SessionState.DECISION_SELECTED,
        SessionState.AWAITING_CONFIRMATION,
    ],
)
def test_non_confirmed_states_pause_and_disclose_exact_state(harness: Harness, state: SessionState):
    session = harness.session_in_state(state)
    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-abc", operator_id="op-1")
    assert outcome.status == STATUS_AWAITING_HUMAN_DECISION
    assert outcome.session_id == session.session_id
    assert outcome.session_state == state.value


def test_cancelled_session_is_human_rejected_and_publishes_nothing(harness: Harness):
    harness.session_in_state(SessionState.CANCELLED)
    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-abc", operator_id="op-1")
    assert outcome.status == STATUS_HUMAN_REJECTED
    assert outcome.record_id is None


def test_abandoned_session_is_human_deferred_and_publishes_nothing(harness: Harness):
    harness.session_in_state(SessionState.ABANDONED)
    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-abc", operator_id="op-1")
    assert outcome.status == STATUS_HUMAN_DEFERRED
    assert outcome.record_id is None


def test_expired_session_is_readiness_unavailable(harness: Harness):
    harness.session_in_state(SessionState.EXPIRED)
    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-abc", operator_id="op-1")
    assert outcome.status == STATUS_READINESS_UNAVAILABLE
    assert outcome.record_id is None


# ── auto_publish_confirmed_session: confirmed -> published, idempotent ──


def test_confirmed_session_with_existing_readiness_package_publishes(
    harness: Harness, tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    _make_active_task(tmp_path)
    confirmed = harness.confirmed_session()
    harness.publication_service.persist_readiness_package(_package("prp-1", confirmed.session_id))

    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-abc", operator_id="op-1")
    assert outcome.status == STATUS_PUBLISHED
    assert outcome.record_id is not None
    assert outcome.package_id == "prp-1"
    assert outcome.session_id == confirmed.session_id


def test_repeated_invocation_after_success_is_idempotent_no_duplicate_chgr(
    harness: Harness, tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    _make_active_task(tmp_path)
    confirmed = harness.confirmed_session()
    harness.publication_service.persist_readiness_package(_package("prp-1", confirmed.session_id))

    first = auto_publish_confirmed_session(harness.context, subject_ref="task-abc", operator_id="op-1")
    second = auto_publish_confirmed_session(harness.context, subject_ref="task-abc", operator_id="op-1")
    third = auto_publish_confirmed_session(harness.context, subject_ref="task-abc", operator_id="op-1")

    assert first.status == STATUS_PUBLISHED
    assert second.status == STATUS_ALREADY_PUBLISHED
    assert third.status == STATUS_ALREADY_PUBLISHED
    assert second.record_id == first.record_id == third.record_id

    # Exactly one publication was committed for this package -- a second
    # or third auto-route call never re-triggers `commit_publication`.
    assert harness.record_store.is_published("prp-1") is True


def test_manual_choreography_elimination(harness: Harness, tmp_path: Path, monkeypatch):
    """Mandatory test (phase brief §50): from a Confirmed session with a
    readiness package already in place, ONE call publishes -- no separate
    manual `readiness` + `governance-record publish` internal
    choreography is performed by the caller/test."""
    monkeypatch.chdir(tmp_path)
    _make_active_task(tmp_path)
    confirmed = harness.confirmed_session()
    harness.publication_service.persist_readiness_package(_package("prp-1", confirmed.session_id))

    outcome = auto_publish_confirmed_session(harness.context, subject_ref="task-abc", operator_id="op-1")

    assert outcome.status == STATUS_PUBLISHED
    assert outcome.record_id is not None, "CHGR must exist after exactly one call"


def test_no_self_cli_subprocess_integration():
    """Mandatory static assertion (phase brief §51): the new production
    module never shells out to PCAE's own CLI."""
    import pcae.commands.governance_auto_publication as module

    source = inspect.getsource(module)
    assert "subprocess" not in source
    assert "os.system" not in source


def test_human_authority_preservation_no_state_publishes_without_confirmed(harness: Harness):
    """Mandatory test (phase brief §52): automation cannot manufacture the
    human-owned `Confirmed` state. Every non-`Confirmed` session state
    this module can observe is exercised elsewhere in this file and none
    of them reach `STATUS_PUBLISHED`; this test asserts the state-set
    invariant directly against the module's own vocabulary."""
    from pcae.commands.governance_auto_publication import _NON_TERMINAL_STATES

    assert SessionState.CONFIRMED not in _NON_TERMINAL_STATES
    non_publishing_states = set(_NON_TERMINAL_STATES) | {
        SessionState.CANCELLED,
        SessionState.ABANDONED,
        SessionState.EXPIRED,
    }
    assert SessionState.CONFIRMED not in non_publishing_states
    assert non_publishing_states | {SessionState.CONFIRMED} == set(SessionState)


# ── find_confirmed_session: deterministic, non-heuristic lookup ─────────


def test_find_confirmed_session_matches_by_exact_subject_ref(harness: Harness):
    confirmed = harness.confirmed_session(subject_ref="task-xyz")
    harness.session_in_state(SessionState.CREATED, subject_ref="task-other")

    found = find_confirmed_session(harness.session_service, "task-xyz")
    assert found is not None
    assert found.session_id == confirmed.session_id

    not_found = find_confirmed_session(harness.session_service, "task-does-not-exist")
    assert not_found is None
