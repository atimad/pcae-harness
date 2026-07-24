"""Phase 144C tests: Publication Coordinator (PEC-001 v1.0).

Covers: Authorization (missing, invalid, replay, stale); Publication
(successful atomic publication, rollback, storage failure, duplicate
execution); Boundary (Coordinator external to interactive_workflow/**,
cltr/**, and the PCAE lifecycle tree; no publish-without-authorization);
Serialization round-trips. Regression coverage for Interactive Workflow
(143O) is exercised by running that suite unmodified alongside this one
(``python -m pytest tests/test_iwc_143o_session_coordination_publication_handoff.py
tests/test_phase_144c_publication_coordinator.py``), per this phase's own
"Regression" requirement -- this module makes zero edits to any 143K-143P
file.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.governance.publication.errors import (
    AuthorizationReplayError,
    InvalidAuthorizationError,
    InvalidPublicationPackageError,
    MissingAuthorizationError,
    PublicationExecutionError,
    PublicationRollbackError,
    PublicationStorageError,
    StaleAuthorizationError,
)
from pcae.governance.publication.models import (
    PUBLICATION_EXECUTION_SCHEMA_VERSION,
    PublicationAuthorizationEvent,
    PublicationExecutionContext,
    PublicationExecutionResult,
)
from pcae.governance.publication.serialization import (
    context_from_payload,
    context_to_payload,
    result_from_payload,
    result_to_payload,
)
from pcae.governance.publication.storage import PublicationRecordStore
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.identity import generate_session_id

_TS = "2026-07-24T10:00:00+00:00"
_LATER_TS = "2026-07-24T11:00:00+00:00"
_EARLIER_TS = "2026-07-24T09:00:00+00:00"


def _package(package_id: str = "pkg-1", built_at: str = _TS, session_id: str | None = None) -> PublicationReadinessPackage:
    return PublicationReadinessPackage(
        package_id=package_id,
        session_id=session_id or generate_session_id(),
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview_id="preview-1",
        preview_digest="digest-1",
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at=built_at,
    )


def _coordinator(tmp_path: Path) -> PublicationCoordinator:
    return PublicationCoordinator(store=PublicationRecordStore(root=tmp_path / "pub-exec"))


# --- Authorization -----------------------------------------------------


def test_missing_authorization_refused(tmp_path):
    coordinator = _coordinator(tmp_path)
    package = _package()
    with pytest.raises(MissingAuthorizationError):
        coordinator.execute(package, None)


def test_invalid_authorization_wrong_type_refused(tmp_path):
    coordinator = _coordinator(tmp_path)
    package = _package()
    with pytest.raises(InvalidAuthorizationError):
        coordinator.execute(package, event="not-an-event")  # type: ignore[arg-type]


def test_invalid_authorization_wrong_package_id_refused(tmp_path):
    coordinator = _coordinator(tmp_path)
    package = _package(package_id="pkg-1")
    event = coordinator.authorize(operator_id="alice", package_id="pkg-OTHER", invoked_at=_LATER_TS)
    with pytest.raises(InvalidAuthorizationError):
        coordinator.execute(package, event)


def test_replay_refused_on_second_attempt(tmp_path):
    coordinator = _coordinator(tmp_path)
    package = _package()
    event = coordinator.authorize(operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS)
    result = coordinator.execute(package, event)
    assert result.success

    replay_event = coordinator.authorize(
        operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS
    )
    with pytest.raises(AuthorizationReplayError):
        coordinator.execute(package, replay_event)


def test_stale_authorization_predating_package_refused(tmp_path):
    coordinator = _coordinator(tmp_path)
    package = _package(built_at=_LATER_TS)
    event = coordinator.authorize(operator_id="alice", package_id=package.package_id, invoked_at=_EARLIER_TS)
    with pytest.raises(StaleAuthorizationError):
        coordinator.execute(package, event)


def test_stale_authorization_unparseable_timestamp_refused(tmp_path):
    coordinator = _coordinator(tmp_path)
    package = _package()
    event = PublicationAuthorizationEvent(
        event_id="pubauth-1", operator_id="alice", package_id=package.package_id, invoked_at="not-a-timestamp"
    )
    with pytest.raises(StaleAuthorizationError):
        coordinator.execute(package, event)


def test_invalid_package_not_ready_refused(tmp_path):
    coordinator = _coordinator(tmp_path)
    not_confirmed = PublicationReadinessPackage(
        package_id="pkg-2",
        session_id=generate_session_id(),
        session_state=SessionState.CREATED,
        transition_sequence_number=0,
        evidence_refs=(),
        clarification_refs=(),
        audit_refs=(),
        preview_id="preview-1",
        preview_digest="digest-1",
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at=_TS,
    )
    event = coordinator.authorize(operator_id="alice", package_id="pkg-2", invoked_at=_LATER_TS)
    with pytest.raises(InvalidPublicationPackageError):
        coordinator.execute(not_confirmed, event)


def test_invalid_package_wrong_type_refused(tmp_path):
    coordinator = _coordinator(tmp_path)
    event = coordinator.authorize(operator_id="alice", package_id="pkg-3", invoked_at=_LATER_TS)
    with pytest.raises(InvalidPublicationPackageError):
        coordinator.execute("not-a-package", event)  # type: ignore[arg-type]


# --- Publication ---------------------------------------------------------


def test_successful_atomic_publication(tmp_path):
    store = PublicationRecordStore(root=tmp_path / "pub-exec")
    coordinator = PublicationCoordinator(store=store)
    package = _package()
    event = coordinator.authorize(operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS)

    result = coordinator.execute(package, event)

    assert result.success is True
    assert result.record_id is not None
    assert result.record_id.startswith("chgr-")
    assert result.error_type is None
    assert result.failure_reason is None
    assert store.is_published(package.package_id)
    record_path = store._record_path(result.record_id)  # noqa: SLF001 (test-only introspection)
    assert record_path.exists()


def test_duplicate_execution_creates_exactly_one_record(tmp_path):
    store = PublicationRecordStore(root=tmp_path / "pub-exec")
    coordinator = PublicationCoordinator(store=store)
    package = _package()
    event = coordinator.authorize(operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS)

    first = coordinator.execute(package, event)
    assert first.success

    second_event = coordinator.authorize(
        operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS
    )
    with pytest.raises(AuthorizationReplayError):
        coordinator.execute(package, second_event)

    records_dir = store.root / "records"
    assert len(list(records_dir.glob("*.json"))) == 1


def test_race_lost_at_commit_rolls_back_record(tmp_path):
    """Simulate two attempts racing past the idempotency check (e.g. two
    processes) by pre-creating the marker file directly, bypassing the
    Coordinator's own check, then verifying the just-written record is
    removed and Replay is raised (PEC-REQ-053's binary rollback)."""

    store = PublicationRecordStore(root=tmp_path / "pub-exec")
    coordinator = PublicationCoordinator(store=store)
    package = _package()
    event = coordinator.authorize(operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS)

    original_commit = store.commit_publication

    def _racing_commit(package_id, record_id, marker_payload):
        # Another process wins the race right before this attempt commits.
        store._marker_path(package_id).parent.mkdir(parents=True, exist_ok=True)
        store._marker_path(package_id).write_text("{}")
        original_commit(package_id, record_id, marker_payload)

    store.commit_publication = _racing_commit  # type: ignore[method-assign]

    with pytest.raises(AuthorizationReplayError):
        coordinator.execute(package, event)

    records_dir = store.root / "records"
    assert list(records_dir.glob("*.json")) == []


def test_storage_failure_reported_and_no_record_left(tmp_path):
    class _FailingStore(PublicationRecordStore):
        def write_record(self, record_id, payload):
            raise PublicationStorageError("simulated storage failure")

    store = _FailingStore(root=tmp_path / "pub-exec")
    coordinator = PublicationCoordinator(store=store)
    package = _package()
    event = coordinator.authorize(operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS)

    with pytest.raises(PublicationStorageError):
        coordinator.execute(package, event)

    assert not store.is_published(package.package_id)
    assert list((store.root / "records").glob("*.json")) == []


def test_rollback_on_commit_os_error(tmp_path):
    class _FlakyStore(PublicationRecordStore):
        def commit_publication(self, package_id, record_id, marker_payload):
            raise OSError("simulated durability failure")

    store = _FlakyStore(root=tmp_path / "pub-exec")
    coordinator = PublicationCoordinator(store=store)
    package = _package()
    event = coordinator.authorize(operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS)

    with pytest.raises(PublicationRollbackError):
        coordinator.execute(package, event)

    assert list((store.root / "records").glob("*.json")) == []
    assert not store.is_published(package.package_id)


def test_every_attempt_accepted_or_refused_is_recorded(tmp_path):
    store = PublicationRecordStore(root=tmp_path / "pub-exec")
    coordinator = PublicationCoordinator(store=store)
    package = _package()

    with pytest.raises(MissingAuthorizationError):
        coordinator.execute(package, None)

    event = coordinator.authorize(operator_id="alice", package_id=package.package_id, invoked_at=_LATER_TS)
    coordinator.execute(package, event)

    attempts = list((store.root / "attempts").glob("*.json"))
    assert len(attempts) == 2


# --- Boundary --------------------------------------------------------------


_FORBIDDEN_IMPORT_ROOTS = (
    "pcae.interactive_workflow.session",
    "pcae.interactive_workflow.orchestration",
    "pcae.interactive_workflow.evidence",
    "pcae.interactive_workflow.clarification",
    "pcae.interactive_workflow.preview",
    "pcae.interactive_workflow.confirmation",
    "pcae.interactive_workflow.state_machine",
    "pcae.interactive_workflow.audit",
    "pcae.cltr",
)


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _publication_package_files() -> list[Path]:
    root = Path(__file__).resolve().parents[1] / "src" / "pcae" / "governance" / "publication"
    return sorted(root.glob("*.py"))


@pytest.mark.parametrize("path", _publication_package_files(), ids=lambda p: p.name)
def test_coordinator_package_has_no_forbidden_imports(path):
    modules = _imported_modules(path)
    for module in modules:
        for forbidden_root in _FORBIDDEN_IMPORT_ROOTS:
            assert not (module == forbidden_root or module.startswith(forbidden_root + ".")), (
                f"{path.name} imports {module!r}, coupling PublicationCoordinator to "
                f"{forbidden_root!r} in violation of PEC-001's Integration section."
            )


def test_coordinator_package_lives_outside_interactive_workflow_and_cltr():
    for path in _publication_package_files():
        parts = path.parts
        assert "interactive_workflow" not in parts
        assert "cltr" not in parts
        assert "governance" in parts and "publication" in parts


def test_no_publication_without_authorization_end_to_end(tmp_path):
    store = PublicationRecordStore(root=tmp_path / "pub-exec")
    coordinator = PublicationCoordinator(store=store)
    package = _package()

    with pytest.raises(PublicationExecutionError):
        coordinator.execute(package, None)

    assert list((store.root / "records").glob("*.json")) == []
    assert not store.is_published(package.package_id)


# --- Serialization -----------------------------------------------------


def test_result_serialization_round_trip_success(tmp_path):
    result = PublicationExecutionResult(
        attempt_id="pubexec-1",
        success=True,
        package_id="pkg-1",
        session_id="CDS-1",
        record_id="chgr-1",
        diagnostics=(),
        evaluated_at=_TS,
        completed_at=_LATER_TS,
    )
    payload = result_to_payload(result)
    assert payload["schema_version"] == PUBLICATION_EXECUTION_SCHEMA_VERSION
    restored = result_from_payload(payload)
    assert restored == result


def test_result_serialization_round_trip_failure():
    result = PublicationExecutionResult(
        attempt_id="pubexec-2",
        success=False,
        package_id="pkg-1",
        session_id="CDS-1",
        record_id=None,
        diagnostics=("boom",),
        evaluated_at=_TS,
        completed_at=_LATER_TS,
        error_type="MissingAuthorizationError",
        failure_reason="boom",
    )
    restored = result_from_payload(result_to_payload(result))
    assert restored == result


def test_context_serialization_round_trip():
    context = PublicationExecutionContext(
        attempt_id="pubexec-3",
        package_id="pkg-1",
        session_id="CDS-1",
        operator_id="alice",
        authorization_event_id="pubauth-1",
        authorization_invoked_at=_TS,
        evaluated_at=_TS,
    )
    restored = context_from_payload(context_to_payload(context))
    assert restored == context


# --- Model validation ----------------------------------------------------


def test_execution_result_rejects_success_with_error_fields():
    with pytest.raises(ValueError):
        PublicationExecutionResult(
            attempt_id="a",
            success=True,
            package_id="p",
            session_id="s",
            record_id="chgr-1",
            diagnostics=(),
            evaluated_at=_TS,
            completed_at=_TS,
            error_type="X",
        )


def test_execution_result_rejects_failure_without_error_fields():
    with pytest.raises(ValueError):
        PublicationExecutionResult(
            attempt_id="a",
            success=False,
            package_id="p",
            session_id="s",
            record_id=None,
            diagnostics=(),
            evaluated_at=_TS,
            completed_at=_TS,
        )


def test_execution_result_rejects_record_id_on_failure():
    with pytest.raises(ValueError):
        PublicationExecutionResult(
            attempt_id="a",
            success=False,
            package_id="p",
            session_id="s",
            record_id="chgr-1",
            diagnostics=(),
            evaluated_at=_TS,
            completed_at=_TS,
            error_type="X",
            failure_reason="y",
        )


def test_authorization_event_rejects_empty_fields():
    with pytest.raises(ValueError):
        PublicationAuthorizationEvent(event_id="", operator_id="a", package_id="p", invoked_at=_TS)
