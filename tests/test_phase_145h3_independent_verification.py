"""Phase 145H.3 independent verification tests.

Independently attacks Phase 145H.2's Post-Consumption Readiness
Uniqueness repair (IWPC-001 v1.4 §35, IWPC-REQ-197-209), closing Blocking
Finding H-1. Written fresh for this phase: does not reuse or rerun Phase
145H.2's own new tests, and does not trust that phase's report or
conclusions as evidence. Exercises the production call graph directly
(``FilesystemPendingReadinessStore``, ``PublicationApplicationService``,
``SessionApplicationService``) plus one full CLI-transport-level
end-to-end assertion, targeting exactly the adversarial scenarios this
phase's governing prompt enumerates: duplicate historical records
(pending+pending, pending+consumed, consumed+consumed), corrupted
records, identity-validation ordering ahead of any idempotent/cache-hit
branch, publication-ownership isolation, and restart-equivalent
persistence (a fresh ``ApplicationContext``/store/service instance per
call, never a shared in-memory object).

Verification only: no production code is modified by this phase. This
file's presence is the phase's sole authorized production of new
artifacts (docs/report and this test file).
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from datetime import datetime, timezone
from unittest import mock

import pytest

from pcae.commands.decision_session import (
    EXIT_SUCCESS,
    build_application_context,
    run_decision_session_confirm,
    run_decision_session_create,
    run_decision_session_evidence,
    run_decision_session_preview,
    run_decision_session_readiness,
    run_decision_session_select,
)
from pcae.commands.governance_record import run_governance_record_publish
from pcae.interactive_workflow.application.publication_service import (
    PublicationApplicationService,
)
from pcae.interactive_workflow.application.session_service import (
    SessionApplicationService,
)
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    FilesystemPendingReadinessStore,
    PendingReadinessStoreCorruptError,
)
from pcae.interactive_workflow.persistence.filesystem_repository import (
    FilesystemSessionRepository,
)
from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.interactive_workflow.session.coordinator import SessionCoordinator


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _Args:
    def __init__(self, **kwargs):
        self.json = True
        self.as_identity = "alice"
        for key, value in kwargs.items():
            setattr(self, key, value)


def _run(handler, **kwargs) -> tuple[int, dict]:
    args = _Args(**kwargs)
    buf = io.StringIO()
    with redirect_stdout(buf):
        exit_code = handler(args)
    return exit_code, json.loads(buf.getvalue())


@pytest.fixture(autouse=True)
def _isolated_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Phase 149O.20L.7O.3C.2: see the identical comment in
    # test_phase_145g_decision_session_cli.py -- CHGR publication now
    # requires an active-task contract (POL-001), mirroring commit/push/
    # promotion's existing invariant.
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / "20260101-0000-phase-145h3-cli-fixture-task.md").write_text(
        "# Phase 145H.3 CLI fixture task\n", encoding="utf-8"
    )
    yield tmp_path


def _fresh_application_context():
    """Build a brand-new ApplicationContext from brand-new component
    instances -- deliberately not reusing any object across calls, to
    independently verify persistence-backed (not in-memory-cached)
    idempotency (restart-equivalence, IWPC-REQ-197/198)."""

    return build_application_context()


def _confirm_session_via_cli(owner: str = "alice") -> str:
    """Drive a session from Created through Confirmed using only the real
    CLI handlers (not direct model construction), returning session_id."""

    exit_code, payload = _run(
        run_decision_session_create,
        template_ref="tmpl-1",
        subject_ref="subj-1",
        owner_id=owner,
    )
    assert exit_code == EXIT_SUCCESS
    session_id = payload["session"]["session_id"]

    exit_code, _ = _run(
        run_decision_session_evidence,
        session_id=session_id,
        declare="ev-1",
        as_identity=owner,
    )
    assert exit_code == EXIT_SUCCESS

    exit_code, _ = _run(
        run_decision_session_select,
        session_id=session_id,
        option_id="opt-1",
        options_presented=["opt-1", "opt-2"],
        template_version="1.0",
        as_identity=owner,
        rationale="because",
        conditions=None,
    )
    assert exit_code == EXIT_SUCCESS

    exit_code, preview = _run(
        run_decision_session_preview,
        session_id=session_id,
        as_identity=owner,
    )
    assert exit_code == EXIT_SUCCESS
    digest = preview["preview_digest"]

    exit_code, _ = _run(
        run_decision_session_confirm,
        session_id=session_id,
        preview_digest=digest,
        statement="I confirm",
        as_identity=owner,
    )
    assert exit_code == EXIT_SUCCESS
    return session_id


# ---------------------------------------------------------------------------
# 5.1 -- exact H-1 CLI reproduction, full transport-level, filesystem-verified
# ---------------------------------------------------------------------------


def test_h1_sequence_end_to_end_single_package_single_chgr(tmp_path):
    session_id = _confirm_session_via_cli()

    exit_code, r1 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    assert exit_code == EXIT_SUCCESS
    pkg1 = r1["package_id"]
    assert r1["disposition"] == "pending"

    exit_code, p1 = _run(run_governance_record_publish, package_id=pkg1, operator_id="bob")
    assert exit_code == EXIT_SUCCESS
    chgr1 = p1["record_id"]

    exit_code, r2 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    assert exit_code == EXIT_SUCCESS
    pkg2 = r2["package_id"]

    # The core H-1 assertion: no second package_id is ever minted.
    assert pkg2 == pkg1
    assert r2["disposition"] == "consumed"
    assert r2["record_id"] == chgr1

    exit_code, p2 = _run(run_governance_record_publish, package_id=pkg2, operator_id="bob")
    assert exit_code != EXIT_SUCCESS
    assert p2["error_type"] == "publication_already_completed"
    assert p2["record_id"] == chgr1

    store = FilesystemPendingReadinessStore()
    pending_ids = store.list_package_ids()
    assert pending_ids == []
    consumed_dir = tmp_path / ".pcae" / "decision-sessions" / "pending-packages" / "consumed"
    consumed_files = sorted(p.name for p in consumed_dir.glob("*.json"))
    assert consumed_files == [f"{pkg1}.json"]

    records_dir = tmp_path / ".pcae" / "publication-execution" / "records"
    chgr_files = list(records_dir.glob("*.json"))
    # Phase 146G: one Publication Execution durably persists four
    # independently schema-validated CHGR-001 v1.2 artifacts, not one flat
    # record; the top-level human_governance_record's own id is still
    # exactly the reported record_id.
    assert len(chgr_files) == 4
    assert {p.stem for p in chgr_files} & {chgr1} == {chgr1}


def test_repeated_readiness_before_publication_is_stable():
    session_id = _confirm_session_via_cli()
    ids = set()
    digests = set()
    for _ in range(3):
        exit_code, r = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
        assert exit_code == EXIT_SUCCESS
        assert r["disposition"] == "pending"
        ids.add(r["package_id"])
        digests.add(r["package_digest"])
    assert len(ids) == 1
    assert len(digests) == 1


def test_readiness_after_publication_repeated_calls_stay_stable_across_fresh_contexts():
    session_id = _confirm_session_via_cli()
    exit_code, r1 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    pkg1 = r1["package_id"]
    _run(run_governance_record_publish, package_id=pkg1, operator_id="bob")

    seen_ids = set()
    for _ in range(3):
        # Each iteration constructs services from scratch (restart-
        # equivalent): idempotency must come from disk, not a cached
        # Python object.
        context = _fresh_application_context()
        record = context.publication_service.ensure_readiness_package(
            session_id, caller_identity="alice"
        )
        seen_ids.add(record.package_id)
        assert record.disposition == "consumed"
    assert seen_ids == {pkg1}


# ---------------------------------------------------------------------------
# 5.7 / 5.8 / 5.9 -- duplicate historical records fail closed
# ---------------------------------------------------------------------------


def _persist_second_candidate_package(session_id: str, publish_it: bool = False):
    """Bypass the idempotent-by-key application-service check to force a
    second, independently-valid pending record onto disk for a session
    that may already have one -- simulating a pre-145H.1 historical
    inconsistency. ``FilesystemPendingReadinessStore.create`` is keyed
    solely by package_id (confirmed by direct inspection), so this is
    the only way such a record could ever have been produced, matching
    IWPC-REQ-204's own framing of the scenario as historical, not
    reachable through any current, correctly-gated code path."""

    session_repository = FilesystemSessionRepository()
    session_coordinator = SessionCoordinator(session_repository)
    session_service = SessionApplicationService(session_coordinator)
    store = FilesystemPendingReadinessStore()

    package = session_service.construct_readiness_package(session_id, caller_identity="alice")
    store.create(package, persisted_at=_now())

    if publish_it:
        coordinator = PublicationCoordinator()
        publication_service = PublicationApplicationService(store, session_service, coordinator)
        prepared = publication_service.prepare_publication_request(package.package_id)
        publication_service.hand_off(prepared, operator_id="bob")

    return package.package_id


def test_duplicate_pending_records_fail_closed():
    session_id = _confirm_session_via_cli()
    _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    _persist_second_candidate_package(session_id)

    store = FilesystemPendingReadinessStore()
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.find_by_session_id(session_id)

    # Must also fail closed through the CLI layer, not silently pick one.
    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    assert exit_code != EXIT_SUCCESS
    assert payload["error_type"] == "persistence_corrupt"


def test_pending_and_consumed_duplicate_fail_closed():
    session_id = _confirm_session_via_cli()
    exit_code, r1 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    pkg1 = r1["package_id"]
    _run(run_governance_record_publish, package_id=pkg1, operator_id="bob")

    # Second pending candidate persisted directly (bypassing the gate).
    _persist_second_candidate_package(session_id)

    store = FilesystemPendingReadinessStore()
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.find_by_session_id(session_id)

    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    assert exit_code != EXIT_SUCCESS
    assert payload["error_type"] == "persistence_corrupt"


def test_multiple_consumed_records_fail_closed():
    session_id = _confirm_session_via_cli()
    exit_code, r1 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    pkg1 = r1["package_id"]
    _run(run_governance_record_publish, package_id=pkg1, operator_id="bob")

    # A second candidate package, also published (both now "consumed").
    _persist_second_candidate_package(session_id, publish_it=True)

    store = FilesystemPendingReadinessStore()
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.find_by_session_id(session_id)


def test_non_matching_records_do_not_interfere():
    session_a = _confirm_session_via_cli()
    session_b = _confirm_session_via_cli()

    exit_code, ra = _run(run_decision_session_readiness, session_id=session_a, as_identity="alice")
    assert exit_code == EXIT_SUCCESS
    exit_code, rb = _run(run_decision_session_readiness, session_id=session_b, as_identity="alice")
    assert exit_code == EXIT_SUCCESS
    assert ra["package_id"] != rb["package_id"]

    _run(run_governance_record_publish, package_id=ra["package_id"], operator_id="bob")

    store = FilesystemPendingReadinessStore()
    record_a = store.find_by_session_id(session_a)
    record_b = store.find_by_session_id(session_b)
    assert record_a.package_id == ra["package_id"]
    assert record_a.disposition == "consumed"
    assert record_b.package_id == rb["package_id"]
    assert record_b.disposition == "pending"


# ---------------------------------------------------------------------------
# 5.10 / 5.11 -- corrupted records must not become "not found"
# ---------------------------------------------------------------------------


def test_corrupted_pending_record_does_not_permit_duplicate_construction():
    session_id = _confirm_session_via_cli()
    store = FilesystemPendingReadinessStore()

    corrupt_path = store.root / "prp-deadbeefdeadbeefdeadbeefdeadbeef.json"
    corrupt_path.parent.mkdir(parents=True, exist_ok=True)
    corrupt_path.write_text("{not valid json", encoding="utf-8")

    # A corrupted, unrelated pending record must fail closed rather than
    # being silently skipped en route to constructing a *new* package for
    # this session_id.
    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    assert exit_code != EXIT_SUCCESS
    assert payload["error_type"] == "persistence_corrupt"

    # No *new* package must have been constructed as a side effect of the
    # corrupted-record error path -- the only file present is the
    # corrupt one this test planted itself.
    assert store.list_package_ids() == [corrupt_path.stem]


def test_corrupted_consumed_record_does_not_permit_duplicate_construction():
    session_id = _confirm_session_via_cli()
    store = FilesystemPendingReadinessStore()

    consumed_dir = store.consumed_root
    consumed_dir.mkdir(parents=True, exist_ok=True)
    corrupt_path = consumed_dir / "prp-deadbeefdeadbeefdeadbeefdeadbeef.json"
    corrupt_path.write_text("{not valid json", encoding="utf-8")

    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    assert exit_code != EXIT_SUCCESS
    assert payload["error_type"] == "persistence_corrupt"
    assert store.list_package_ids() == []


# ---------------------------------------------------------------------------
# 5.13 -- identity validation must run before any cache-hit / idempotent
# return, for both pending and consumed matches
# ---------------------------------------------------------------------------


def test_identity_validation_precedes_pending_cache_hit():
    session_id = _confirm_session_via_cli(owner="alice")
    exit_code, r1 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    assert exit_code == EXIT_SUCCESS
    assert r1["disposition"] == "pending"

    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id, as_identity="mallory")
    assert exit_code != EXIT_SUCCESS
    assert payload["error_type"] == "identity_binding_mismatch"


def test_identity_validation_precedes_consumed_cache_hit():
    session_id = _confirm_session_via_cli(owner="alice")
    exit_code, r1 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    pkg1 = r1["package_id"]
    _run(run_governance_record_publish, package_id=pkg1, operator_id="bob")

    exit_code, payload = _run(run_decision_session_readiness, session_id=session_id, as_identity="mallory")
    assert exit_code != EXIT_SUCCESS
    assert payload["error_type"] == "identity_binding_mismatch"
    # A mismatched-identity caller must never learn the existing
    # package's identity/digest through the error payload.
    assert pkg1 not in json.dumps(payload)


# ---------------------------------------------------------------------------
# 5.14 -- readiness never invokes publication authority
# ---------------------------------------------------------------------------


def test_readiness_never_calls_publication_coordinator():
    session_id = _confirm_session_via_cli()

    with mock.patch.object(
        PublicationCoordinator, "authorize", side_effect=AssertionError("must not be called")
    ), mock.patch.object(
        PublicationCoordinator, "execute", side_effect=AssertionError("must not be called")
    ):
        exit_code, r1 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
        assert exit_code == EXIT_SUCCESS
        pkg1 = r1["package_id"]

        # Repeat after the package exists (pending branch) -- still must
        # never touch the Coordinator.
        exit_code, r2 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
        assert exit_code == EXIT_SUCCESS
        assert r2["package_id"] == pkg1

    # Now publish for real (Coordinator un-mocked), then confirm the
    # post-consumption readiness path *still* never touches the
    # Coordinator.
    _run(run_governance_record_publish, package_id=pkg1, operator_id="bob")

    with mock.patch.object(
        PublicationCoordinator, "authorize", side_effect=AssertionError("must not be called")
    ), mock.patch.object(
        PublicationCoordinator, "execute", side_effect=AssertionError("must not be called")
    ):
        exit_code, r3 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
        assert exit_code == EXIT_SUCCESS
        assert r3["package_id"] == pkg1
        assert r3["disposition"] == "consumed"


# ---------------------------------------------------------------------------
# 5.5 -- failed publication does not duplicate readiness identity
# ---------------------------------------------------------------------------


def test_failed_publication_then_successful_retry_yields_single_chgr():
    session_id = _confirm_session_via_cli()
    exit_code, r1 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    pkg1 = r1["package_id"]

    session_repository = FilesystemSessionRepository()
    session_coordinator = SessionCoordinator(session_repository)
    session_service = SessionApplicationService(session_coordinator)
    store = FilesystemPendingReadinessStore()
    coordinator = PublicationCoordinator()
    publication_service = PublicationApplicationService(store, session_service, coordinator)

    prepared = publication_service.prepare_publication_request(pkg1)
    with mock.patch.object(
        PublicationCoordinator, "execute", side_effect=RuntimeError("simulated execution failure")
    ):
        with pytest.raises(Exception):
            publication_service.hand_off(prepared, operator_id="bob")

    # Package must remain pending and unduplicated after the failure.
    record = store.load(pkg1)
    assert record.disposition == "pending"
    exit_code, r2 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    assert exit_code == EXIT_SUCCESS
    assert r2["package_id"] == pkg1
    assert r2["disposition"] == "pending"

    # Real retry succeeds.
    exit_code, p1 = _run(run_governance_record_publish, package_id=pkg1, operator_id="bob")
    assert exit_code == EXIT_SUCCESS
    chgr1 = p1["record_id"]

    exit_code, r3 = _run(run_decision_session_readiness, session_id=session_id, as_identity="alice")
    assert exit_code == EXIT_SUCCESS
    assert r3["package_id"] == pkg1
    assert r3["record_id"] == chgr1
