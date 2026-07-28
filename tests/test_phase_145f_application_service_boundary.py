"""Phase 145F unit tests: Interactive Workflow + Publication
application/service boundary (IWPC-001 v1.1, IWC-001 v1.2, PEC-001 v1.1;
Phase 145D `FilesystemSessionRepository`, Phase 145E
`FilesystemPendingReadinessStore`).

Covers session-lifecycle coordination, readiness-package coordination,
publication-request construction, the publication boundary hand-off,
publication result processing, replay/stale detection, recovery, error
mapping, and the dependency-boundary rule. No test in this module
implements or exercises a CLI command, a transport adapter, or
engineering execution -- Phase 145F's explicit no-go boundary.
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytest

from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.governance.publication.errors import (
    AtomicPublicationFailure,
    AuthorizationReplayError,
    InvalidAuthorizationError,
    InvalidPublicationPackageError,
    MissingAuthorizationError,
    PublicationRollbackError,
    PublicationStorageError,
    StaleAuthorizationError,
)
from pcae.governance.publication.storage import PublicationRecordStore
from pcae.interactive_workflow.application.errors import (
    ApplicationServiceError,
    InvalidSessionIdentifierApplicationError,
    PublicationAlreadyCompletedApplicationError,
    PublicationAuthorizationFailedApplicationError,
    PublicationCoordinationError,
    PublicationExecutionFailedApplicationError,
    ReadinessCoordinationError,
    ReadinessDigestMismatchApplicationError,
    ReadinessPackageNotFoundApplicationError,
    ReadinessPackageStaleApplicationError,
    ReadinessSessionNotConfirmedApplicationError,
    ReadinessStoreCorruptApplicationError,
    SessionAlreadyExistsApplicationError,
    SessionCoordinationError,
    SessionNotFoundApplicationError,
    SessionNotTerminalApplicationError,
)
from pcae.interactive_workflow.application.models import PreparedPublicationRequest
from pcae.interactive_workflow.application.publication_service import PublicationApplicationService
from pcae.interactive_workflow.application.session_service import SessionApplicationService
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    DISPOSITION_CONSUMED,
    DISPOSITION_PENDING,
    FilesystemPendingReadinessStore,
)
from pcae.interactive_workflow.persistence.filesystem_repository import FilesystemSessionRepository
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.coordinator import SessionCoordinator
from pcae.interactive_workflow.session.identity import generate_session_id


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

    def confirmed_session(self):
        session = self.session_service.create_session(
            owner_identity="owner-1", template_ref="tmpl-1", subject_ref="subj-1"
        )
        confirmed = session.with_state(SessionState.CONFIRMED, _now_iso())
        self.session_service.persist_session(confirmed)
        return confirmed

    def expired_session(self):
        session = self.confirmed_session()
        expired = session.with_state(SessionState.EXPIRED, _now_iso())
        self.session_service.persist_session(expired)
        return expired


@pytest.fixture
def harness(tmp_path: Path) -> Harness:
    return Harness(tmp_path)


# --- Session lifecycle coordination -----------------------------------------


def test_create_session_returns_created_session(harness: Harness):
    session = harness.session_service.create_session(
        owner_identity="owner-1", template_ref="tmpl-1", subject_ref="subj-1"
    )
    assert session.session_state is SessionState.CREATED
    assert harness.session_repo.exists(session.session_id)


def test_load_session_round_trips(harness: Harness):
    created = harness.session_service.create_session(
        owner_identity="owner-1", template_ref="tmpl-1", subject_ref="subj-1"
    )
    loaded = harness.session_service.load_session(created.session_id)
    assert loaded == created


def test_load_session_not_found_maps_to_application_error(harness: Harness):
    with pytest.raises(SessionNotFoundApplicationError) as excinfo:
        harness.session_service.load_session(generate_session_id())
    assert excinfo.value.session_id is not None
    assert isinstance(excinfo.value, SessionCoordinationError)
    assert isinstance(excinfo.value, ApplicationServiceError)


def test_load_session_invalid_identifier_maps_to_application_error(harness: Harness):
    with pytest.raises(InvalidSessionIdentifierApplicationError):
        harness.session_service.load_session("../etc/passwd")


def test_persist_session_updates_state(harness: Harness):
    session = harness.session_service.create_session(
        owner_identity="owner-1", template_ref="tmpl-1", subject_ref="subj-1"
    )
    updated = session.with_state(SessionState.EVIDENCE_READY, _now_iso())
    harness.session_service.persist_session(updated)
    loaded = harness.session_service.load_session(session.session_id)
    assert loaded.session_state is SessionState.EVIDENCE_READY


def test_persist_session_not_found_maps_to_application_error(harness: Harness):
    ghost = harness.session_service.create_session(
        owner_identity="owner-1", template_ref="tmpl-1", subject_ref="subj-1"
    )
    # Persisting a session whose repository record was never created (a
    # freshly-built Session object, not one returned by create_session)
    # must fail with SessionNotFoundApplicationError, not create silently.
    unregistered = ghost.with_state(SessionState.CANCELLED, _now_iso())
    object.__setattr__(unregistered, "session_id", generate_session_id())
    with pytest.raises(SessionNotFoundApplicationError):
        harness.session_service.persist_session(unregistered)


def test_update_session_is_alias_for_persist(harness: Harness):
    session = harness.session_service.create_session(
        owner_identity="owner-1", template_ref="tmpl-1", subject_ref="subj-1"
    )
    updated = session.with_state(SessionState.EVIDENCE_READY, _now_iso())
    harness.session_service.update_session(updated)
    assert harness.session_service.load_session(session.session_id).session_state is SessionState.EVIDENCE_READY


def test_complete_session_requires_terminal_state(harness: Harness):
    session = harness.session_service.create_session(
        owner_identity="owner-1", template_ref="tmpl-1", subject_ref="subj-1"
    )
    with pytest.raises(SessionNotTerminalApplicationError):
        harness.session_service.complete_session(session)


def test_complete_session_persists_terminal_session(harness: Harness):
    session = harness.session_service.create_session(
        owner_identity="owner-1", template_ref="tmpl-1", subject_ref="subj-1"
    )
    confirmed = session.with_state(SessionState.CONFIRMED, _now_iso())
    result = harness.session_service.complete_session(confirmed)
    assert result is confirmed
    assert harness.session_service.load_session(session.session_id).session_state is SessionState.CONFIRMED


def test_create_session_already_exists_maps_to_application_error(harness: Harness, monkeypatch):
    session = harness.session_service.create_session(
        owner_identity="owner-1", template_ref="tmpl-1", subject_ref="subj-1"
    )
    monkeypatch.setattr(
        "pcae.interactive_workflow.session.coordinator.generate_session_id", lambda: session.session_id
    )
    with pytest.raises(SessionAlreadyExistsApplicationError):
        harness.session_service.create_session(owner_identity="owner-2", template_ref="tmpl-1", subject_ref="subj-2")


# --- Readiness coordination --------------------------------------------------


def test_persist_readiness_package_requires_confirmed_session(harness: Harness):
    session = harness.session_service.create_session(
        owner_identity="owner-1", template_ref="tmpl-1", subject_ref="subj-1"
    )
    package = _package("pkg-1", session.session_id)
    with pytest.raises(ReadinessSessionNotConfirmedApplicationError) as excinfo:
        harness.publication_service.persist_readiness_package(package)
    assert isinstance(excinfo.value, ReadinessCoordinationError)


def test_persist_readiness_package_persists_new_package(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    record = harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    assert record.package == package
    assert record.disposition == DISPOSITION_PENDING


def test_persist_readiness_package_idempotent_by_session_key(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    first = harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    duplicate = _package("pkg-2", session.session_id)
    second = harness.publication_service.persist_readiness_package(duplicate, persisted_at=_now_iso())
    assert second.package_id == first.package_id
    assert harness.readiness_store.exists("pkg-2") is False


def test_get_readiness_package_not_found_maps_to_application_error(harness: Harness):
    with pytest.raises(ReadinessPackageNotFoundApplicationError):
        harness.publication_service.get_readiness_package("does-not-exist")


def test_get_readiness_package_digest_mismatch_maps_to_application_error(harness: Harness, tmp_path: Path):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())

    stored_path = harness.readiness_store.root / "pkg-1.json"
    text = stored_path.read_text()
    tampered = text.replace('"rationale_text": "because"', '"rationale_text": "tampered"')
    assert tampered != text
    stored_path.write_text(tampered)

    with pytest.raises(ReadinessDigestMismatchApplicationError):
        harness.publication_service.get_readiness_package("pkg-1")


def test_find_readiness_package_for_session_returns_none_when_absent(harness: Harness):
    session = harness.confirmed_session()
    assert harness.publication_service.find_readiness_package_for_session(session.session_id) is None


def test_find_readiness_package_for_session_returns_existing(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    found = harness.publication_service.find_readiness_package_for_session(session.session_id)
    assert found is not None
    assert found.package_id == "pkg-1"


# --- Phase 145H.2: post-consumption readiness uniqueness (IWPC-001 v1.4 §35) --


def test_find_readiness_package_for_session_returns_consumed_after_publish(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    prepared = harness.publication_service.prepare_publication_request("pkg-1")
    result = harness.publication_service.hand_off(prepared, operator_id="operator-1")

    found = harness.publication_service.find_readiness_package_for_session(session.session_id)
    assert found is not None
    assert found.package_id == "pkg-1"
    assert found.disposition == DISPOSITION_CONSUMED
    assert found.record_id == result.record_id


def test_persist_readiness_package_after_consumption_never_mints_second_package_id(harness: Harness):
    """IWPC-REQ-197 invariant 5: a caller re-presenting a freshly-built
    package for an already-consumed session must never cause a second
    package_id to be persisted -- the original, consumed record is
    returned unchanged."""

    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    prepared = harness.publication_service.prepare_publication_request("pkg-1")
    harness.publication_service.hand_off(prepared, operator_id="operator-1")

    second_build = _package("pkg-2", session.session_id)
    returned = harness.publication_service.persist_readiness_package(second_build, persisted_at=_now_iso())

    assert returned.package_id == "pkg-1"
    assert returned.disposition == DISPOSITION_CONSUMED
    with pytest.raises(ReadinessPackageNotFoundApplicationError):
        harness.publication_service.get_readiness_package("pkg-2")


def test_find_readiness_package_for_session_fails_closed_on_duplicate_historical_records(harness: Harness):
    session = harness.confirmed_session()
    harness.readiness_store.create(_package("pkg-a", session.session_id), persisted_at=_now_iso())
    harness.readiness_store.create(_package("pkg-b", session.session_id), persisted_at=_now_iso())

    with pytest.raises(ReadinessStoreCorruptApplicationError):
        harness.publication_service.find_readiness_package_for_session(session.session_id)


# --- Publication request construction ---------------------------------------


def test_prepare_publication_request_success(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    prepared = harness.publication_service.prepare_publication_request("pkg-1")
    assert isinstance(prepared, PreparedPublicationRequest)
    assert prepared.package_id == "pkg-1"
    assert prepared.session_id == session.session_id
    assert prepared.confirmation_request_id == "req-1"
    assert prepared.confirmation_response_id == "resp-1"


def test_prepare_publication_request_not_found(harness: Harness):
    with pytest.raises(ReadinessPackageNotFoundApplicationError):
        harness.publication_service.prepare_publication_request("missing")


def test_prepare_publication_request_stale_when_session_expired(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())

    expired = session.with_state(SessionState.EXPIRED, _now_iso())
    harness.session_service.persist_session(expired)

    with pytest.raises(ReadinessPackageStaleApplicationError):
        harness.publication_service.prepare_publication_request("pkg-1")


def test_prepare_publication_request_already_completed(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    prepared = harness.publication_service.prepare_publication_request("pkg-1")
    harness.publication_service.hand_off(prepared, operator_id="operator-1")

    with pytest.raises(PublicationAlreadyCompletedApplicationError) as excinfo:
        harness.publication_service.prepare_publication_request("pkg-1")
    assert excinfo.value.record_id is not None


# --- Publication boundary hand-off / results --------------------------------


def test_hand_off_success_consumes_package_and_returns_result(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    prepared = harness.publication_service.prepare_publication_request("pkg-1")

    result = harness.publication_service.hand_off(prepared, operator_id="operator-1")

    assert result.success is True
    assert result.record_id is not None
    record = harness.readiness_store.load("pkg-1")
    assert record.disposition == DISPOSITION_CONSUMED
    assert record.record_id == result.record_id
    assert len(record.attempts) == 1
    assert record.attempts[0].outcome == "succeeded"
    assert harness.record_store.is_published("pkg-1") is True


def test_hand_off_requires_nonempty_operator_id(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    prepared = harness.publication_service.prepare_publication_request("pkg-1")

    with pytest.raises(ValueError):
        harness.publication_service.hand_off(prepared, operator_id="")


def test_hand_off_already_consumed_short_circuits_before_authorize(harness: Harness, monkeypatch):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    prepared = harness.publication_service.prepare_publication_request("pkg-1")
    harness.publication_service.hand_off(prepared, operator_id="operator-1")

    calls = []
    monkeypatch.setattr(
        harness.publication_coordinator,
        "authorize",
        lambda **kwargs: calls.append(kwargs) or pytest.fail("authorize should not be called"),
    )
    with pytest.raises(PublicationAlreadyCompletedApplicationError):
        harness.publication_service.hand_off(prepared, operator_id="operator-1")
    assert calls == []


class _FakeCoordinator:
    """A duck-typed stand-in for ``PublicationCoordinator`` used to force
    every branch of ``hand_off``'s exception-mapping without needing to
    engineer real ``PublicationCoordinator``/``PublicationRecordStore``
    preconditions for each one (e.g. ``StaleAuthorizationError`` requires
    a specific clock relationship ``hand_off`` deliberately gives no
    caller-facing lever to control, IWPC-REQ-121)."""

    def __init__(self, real: PublicationCoordinator, raise_on_execute: Exception) -> None:
        self._real = real
        self._raise_on_execute = raise_on_execute

    def authorize(self, **kwargs):
        return self._real.authorize(**kwargs)

    def execute(self, package, event):
        raise self._raise_on_execute


@pytest.mark.parametrize(
    "exc,expected",
    [
        (AuthorizationReplayError("replayed"), PublicationAlreadyCompletedApplicationError),
        (MissingAuthorizationError("missing"), PublicationAuthorizationFailedApplicationError),
        (InvalidAuthorizationError("invalid"), PublicationAuthorizationFailedApplicationError),
        (StaleAuthorizationError("stale"), PublicationAuthorizationFailedApplicationError),
        (InvalidPublicationPackageError("bad package"), PublicationExecutionFailedApplicationError),
        (PublicationStorageError("storage down"), PublicationExecutionFailedApplicationError),
        (PublicationRollbackError("rolled back"), PublicationExecutionFailedApplicationError),
        (AtomicPublicationFailure("atomic failure"), PublicationExecutionFailedApplicationError),
    ],
)
def test_hand_off_maps_coordinator_exceptions(harness: Harness, exc: Exception, expected):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    prepared = harness.publication_service.prepare_publication_request("pkg-1")

    fake = _FakeCoordinator(harness.publication_coordinator, exc)
    service = PublicationApplicationService(harness.readiness_store, harness.session_service, fake)

    with pytest.raises(expected) as excinfo:
        service.hand_off(prepared, operator_id="operator-1")
    assert isinstance(excinfo.value, PublicationCoordinationError)
    assert isinstance(excinfo.value, ApplicationServiceError)

    record = harness.readiness_store.load("pkg-1")
    assert record.disposition == DISPOSITION_PENDING
    if expected is PublicationAlreadyCompletedApplicationError:
        # A replay signal never fabricates a new attempt-linkage entry --
        # nothing about this store's own bookkeeping changes.
        assert record.attempts == ()
    else:
        assert len(record.attempts) == 1
        assert record.attempts[0].outcome == "failed"


# --- Recovery ----------------------------------------------------------------


class _FlakyOnceCoordinator:
    """Fails the first ``execute`` call, then delegates normally --
    simulates an interrupted publication attempt followed by a genuine
    retry (IWPC-REQ-033/148-156)."""

    def __init__(self, real: PublicationCoordinator) -> None:
        self._real = real
        self._failed_once = False

    def authorize(self, **kwargs):
        return self._real.authorize(**kwargs)

    def execute(self, package, event):
        if not self._failed_once:
            self._failed_once = True
            raise PublicationStorageError("simulated interruption")
        return self._real.execute(package, event)


def test_resume_publication_retries_after_interrupted_failure(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())

    flaky = _FlakyOnceCoordinator(harness.publication_coordinator)
    service = PublicationApplicationService(harness.readiness_store, harness.session_service, flaky)

    with pytest.raises(PublicationExecutionFailedApplicationError):
        service.resume_publication("pkg-1", operator_id="operator-1")
    assert harness.readiness_store.load("pkg-1").disposition == DISPOSITION_PENDING

    result = service.resume_publication("pkg-1", operator_id="operator-1")
    assert result.success is True
    record = harness.readiness_store.load("pkg-1")
    assert record.disposition == DISPOSITION_CONSUMED
    assert len(record.attempts) == 2
    assert [a.outcome for a in record.attempts] == ["failed", "succeeded"]


def test_resume_publication_after_success_reports_already_completed(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    harness.publication_service.resume_publication("pkg-1", operator_id="operator-1")

    with pytest.raises(PublicationAlreadyCompletedApplicationError) as excinfo:
        harness.publication_service.resume_publication("pkg-1", operator_id="operator-2")
    assert excinfo.value.record_id is not None


def test_resume_publication_stale_session_blocks_recovery(harness: Harness):
    session = harness.confirmed_session()
    package = _package("pkg-1", session.session_id)
    harness.publication_service.persist_readiness_package(package, persisted_at=_now_iso())
    expired = session.with_state(SessionState.EXPIRED, _now_iso())
    harness.session_service.persist_session(expired)

    with pytest.raises(ReadinessPackageStaleApplicationError):
        harness.publication_service.resume_publication("pkg-1", operator_id="operator-1")


# --- Error taxonomy -----------------------------------------------------------


def test_application_errors_carry_identifiers():
    err = SessionNotFoundApplicationError("boom", session_id="CDS-x")
    assert err.session_id == "CDS-x"
    assert err.package_id is None
    assert err.record_id is None
    assert str(err) == "boom"


def test_error_hierarchy():
    assert issubclass(SessionCoordinationError, ApplicationServiceError)
    assert issubclass(ReadinessCoordinationError, ApplicationServiceError)
    assert issubclass(PublicationCoordinationError, ApplicationServiceError)
    assert issubclass(ApplicationServiceError, Exception)


# --- Dependency boundary -------------------------------------------------------


def _imported_modules(path: Path) -> set:
    tree = ast.parse(path.read_text(), filename=str(path))
    modules: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


_APPLICATION_PACKAGE_ROOT = (
    Path(__file__).resolve().parents[1] / "src" / "pcae" / "interactive_workflow" / "application"
)

_UNIVERSALLY_FORBIDDEN_IMPORT_ROOTS = (
    "pcae.cli",
    "pcae.commands",
    "pcae.lifecycle",
    "pcae.core.permission_broker",
    "pcae.core.permission_broker_foundation",
    "pcae.governance.verification",
    "pcae.governance.inspection",
)

# session_service.py additionally must not depend on the Publication
# subsystem at all -- session-lifecycle coordination has no business
# knowing Publication exists (only publication_service.py crosses that
# boundary, deliberately, per this phase's own governing prompt).
_SESSION_SERVICE_ADDITIONAL_FORBIDDEN_ROOTS = ("pcae.governance.publication",)


def _application_package_files():
    return sorted(_APPLICATION_PACKAGE_ROOT.glob("*.py"))


@pytest.mark.parametrize("path", _application_package_files(), ids=lambda p: p.name)
def test_application_package_has_no_universally_forbidden_imports(path: Path):
    modules = _imported_modules(path)
    for module in modules:
        for forbidden_root in _UNIVERSALLY_FORBIDDEN_IMPORT_ROOTS:
            assert not (module == forbidden_root or module.startswith(forbidden_root + ".")), (
                f"{path.name} imports {module!r}, coupling the application-service "
                f"boundary to {forbidden_root!r} in violation of IWPC-001's Dependency "
                "Contract (no CLI, transport, lifecycle, or Permission Broker coupling)."
            )


def test_session_service_does_not_import_publication_subsystem():
    path = _APPLICATION_PACKAGE_ROOT / "session_service.py"
    modules = _imported_modules(path)
    for module in modules:
        for forbidden_root in _SESSION_SERVICE_ADDITIONAL_FORBIDDEN_ROOTS:
            assert not (module == forbidden_root or module.startswith(forbidden_root + ".")), (
                f"session_service.py imports {module!r}; session-lifecycle coordination "
                "must not depend on the Publication subsystem."
            )


def test_publication_service_does_not_import_orchestration_or_session_coordinator():
    path = _APPLICATION_PACKAGE_ROOT / "publication_service.py"
    modules = _imported_modules(path)
    forbidden = ("pcae.interactive_workflow.orchestration", "pcae.interactive_workflow.session.coordinator")
    for module in modules:
        for forbidden_root in forbidden:
            assert not (module == forbidden_root or module.startswith(forbidden_root + ".")), (
                f"publication_service.py imports {module!r}; it must coordinate session "
                "state exclusively through SessionApplicationService, never a second, "
                "parallel path into SessionCoordinator/WorkflowOrchestrator."
            )


def test_application_package_lives_under_interactive_workflow():
    for path in _application_package_files():
        parts = path.parts
        assert "interactive_workflow" in parts
        assert "application" in parts
