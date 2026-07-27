"""Phase 145E unit tests: filesystem Pending-Readiness Store
implementation (IWPC-001 v1.1 §14, IWPC-REQ-078-092; §15 Artifact
Binding; §19.1; §21; §22; §23).

Covers store operations, exact artifact preservation, digest
verification, duplicate/conflict behavior, atomicity, corruption
detection, security, concurrency, recovery, and the dependency-boundary
rule. No test in this module implements or exercises a CLI command, a
transport adapter, Publication Coordinator invocation, or higher-level
workflow behavior -- Phase 145E's explicit no-go boundary.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest

from pcae.interactive_workflow.errors import (
    PendingReadinessAlreadyConsumedError,
    PendingReadinessAttemptConflictError,
    PendingReadinessDigestMismatchError,
    PendingReadinessPackageAlreadyExistsError,
    PendingReadinessPackageNotFoundError,
    PendingReadinessStoreCorruptError,
    PersistenceUnavailableError,
)
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    CONSUMED_SUBDIRECTORY,
    DEFAULT_STORAGE_ROOT,
    DISPOSITION_CONSUMED,
    DISPOSITION_PENDING,
    OUTCOME_FAILED,
    OUTCOME_SUCCEEDED,
    STORE_SCHEMA_VERSION,
    FilesystemPendingReadinessStore,
    is_valid_package_id,
)
from pcae.interactive_workflow.persistence.repository import CHGR_STORAGE_PREFIX
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.serialization.publication_handoff_schema import to_payload
from pcae.interactive_workflow.session.identity import generate_session_id


def _package(package_id: str = "pkg-1", session_id: str | None = None, **overrides) -> PublicationReadinessPackage:
    fields = dict(
        package_id=package_id,
        session_id=session_id or generate_session_id(),
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=0,
        evidence_refs=("ev-1",),
        clarification_refs=(),
        audit_refs=(),
        preview_id="preview-1",
        preview_digest="preview-digest-1",
        confirmation_request_id="req-1",
        confirmation_response_id="resp-1",
        built_at="2026-01-01T00:00:00Z",
        decision_subject="subject",
        template_id="template-1",
        template_version="v1",
        selected_option_id="opt-a",
        rationale_text="because",
        conditions_text=None,
        options_presented=("opt-a", "opt-b"),
        decision_maker_identity_evidence={"k": "v"},
        preview_rendered_content="rendered",
        confirmation_statement="I confirm",
        confirmation_timestamp="2026-01-01T00:00:00Z",
        metadata={"m": 1},
    )
    fields.update(overrides)
    return PublicationReadinessPackage(**fields)


def _store(tmp_path: Path) -> FilesystemPendingReadinessStore:
    return FilesystemPendingReadinessStore(root=tmp_path / "pending-packages")


# --- Store identity / default location ------------------------------------


def test_default_storage_root_matches_contract_location():
    assert str(DEFAULT_STORAGE_ROOT) == str(Path(".pcae") / "decision-sessions" / "pending-packages")


def test_consumed_subdirectory_name():
    assert CONSUMED_SUBDIRECTORY == "consumed"


def test_store_never_writes_under_chgr_storage_prefix():
    with pytest.raises(ValueError):
        FilesystemPendingReadinessStore(root=Path(CHGR_STORAGE_PREFIX))
    with pytest.raises(ValueError):
        FilesystemPendingReadinessStore(root=Path(CHGR_STORAGE_PREFIX) / "nested")


# --- Core operations --------------------------------------------------------


def test_create_then_load_round_trips(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="2026-01-01T00:00:01Z")
    record = store.load(package.package_id)
    assert record.package == package
    assert record.disposition == DISPOSITION_PENDING
    assert record.attempts == ()
    assert record.record_id is None


def test_create_rejects_existing_package_id(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    with pytest.raises(PendingReadinessPackageAlreadyExistsError):
        store.create(package, persisted_at="t1")


def test_create_rejects_different_content_same_package_id(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    conflicting = _package(session_id=package.session_id, decision_subject="different")
    with pytest.raises(PendingReadinessPackageAlreadyExistsError):
        store.create(conflicting, persisted_at="t1")


def test_load_missing_raises_not_found(tmp_path):
    store = _store(tmp_path)
    with pytest.raises(PendingReadinessPackageNotFoundError):
        store.load("pkg-missing")


def test_exists_true_after_create_false_before(tmp_path):
    store = _store(tmp_path)
    package = _package()
    assert store.exists(package.package_id) is False
    store.create(package, persisted_at="t0")
    assert store.exists(package.package_id) is True


def test_exists_false_for_invalid_identifier(tmp_path):
    store = _store(tmp_path)
    assert store.exists("../etc/passwd") is False


def test_list_package_ids_reflects_created_packages(tmp_path):
    store = _store(tmp_path)
    ids = {f"pkg-{i}" for i in range(3)}
    for pid in ids:
        store.create(_package(package_id=pid), persisted_at="t0")
    assert set(store.list_package_ids()) == ids


def test_list_package_ids_empty_when_root_absent(tmp_path):
    store = _store(tmp_path)
    assert store.list_package_ids() == []


def test_list_package_ids_deterministic_order(tmp_path):
    store = _store(tmp_path)
    for i in range(5):
        store.create(_package(package_id=f"pkg-{i}"), persisted_at="t0")
    assert store.list_package_ids() == sorted(store.list_package_ids())


def test_list_package_ids_skips_unrecognized_files(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    (store.root / "not-json").write_text("{}")
    (store.root / ".hidden.json").write_text("{}")
    assert store.list_package_ids() == [package.package_id]


def test_list_package_ids_does_not_load_every_package(tmp_path, monkeypatch):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")

    def _fail(*args, **kwargs):
        raise AssertionError("list_package_ids must not load package bodies")

    monkeypatch.setattr(
        "pcae.interactive_workflow.persistence.filesystem_pending_readiness_store._package_from_payload",
        _fail,
    )
    assert store.list_package_ids() == [package.package_id]


def test_find_by_session_id_returns_matching_pending_package(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    found = store.find_by_session_id(package.session_id)
    assert found is not None
    assert found.package_id == package.package_id


def test_find_by_session_id_returns_none_when_absent(tmp_path):
    store = _store(tmp_path)
    assert store.find_by_session_id(generate_session_id()) is None


# --- Exact artifact preservation --------------------------------------------


def test_round_trip_preserves_every_package_field(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    assert store.load(package.package_id).package == package


def test_payload_preserved_verbatim_in_wire_format(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    raw = json.loads((store.root / f"{package.package_id}.json").read_text())
    assert raw["package"] == to_payload(package)


def test_package_payload_unchanged_after_metadata_update(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_FAILED, timestamp="t1"
    )
    assert store.load(package.package_id).package == package


def test_consumed_package_payload_unchanged(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id,
        attempt_id="a1",
        outcome=OUTCOME_SUCCEEDED,
        timestamp="t1",
        record_id="rec-1",
        publication_attempt_id="pub-1",
    )
    assert store.load(package.package_id).package == package


# --- Digest verification ----------------------------------------------------


def test_valid_digest_round_trips(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    record = store.load(package.package_id)
    assert record.package_digest


def test_tampered_payload_detected_on_load(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    payload = json.loads(path.read_text())
    payload["package"]["decision_subject"] = "TAMPERED"
    path.write_text(json.dumps(payload))
    with pytest.raises(PendingReadinessDigestMismatchError):
        store.load(package.package_id)


def test_tampered_stored_digest_detected_on_load(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    payload = json.loads(path.read_text())
    payload["package_digest"] = "0" * 64
    path.write_text(json.dumps(payload))
    with pytest.raises(PendingReadinessDigestMismatchError):
        store.load(package.package_id)


def test_manual_file_modification_detected(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    payload = json.loads(path.read_text())
    payload["package"]["metadata"] = {"injected": True}
    path.write_text(json.dumps(payload))
    with pytest.raises(PendingReadinessDigestMismatchError):
        store.load(package.package_id)


# --- Duplicate and conflict behavior ----------------------------------------


def test_cross_session_reuse_of_package_id_fails_closed(tmp_path):
    store = _store(tmp_path)
    package = _package(session_id=generate_session_id())
    store.create(package, persisted_at="t0")
    other_session_package = _package(package_id=package.package_id, session_id=generate_session_id())
    with pytest.raises(PendingReadinessPackageAlreadyExistsError):
        store.create(other_session_package, persisted_at="t1")


def test_conflicting_publication_attempts_rejected(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_FAILED, timestamp="t1"
    )
    with pytest.raises(PendingReadinessAttemptConflictError):
        store.record_publication_attempt(
            package.package_id,
            attempt_id="a1",
            outcome=OUTCOME_SUCCEEDED,
            timestamp="t2",
            record_id="rec-1",
        )


def test_identical_duplicate_attempt_is_idempotent(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    first = store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_FAILED, timestamp="t1"
    )
    second = store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_FAILED, timestamp="t1"
    )
    assert first.attempts == second.attempts == (
        store.load(package.package_id).attempts
    )
    assert len(second.attempts) == 1


def test_conflicting_terminal_disposition_rejected(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id,
        attempt_id="a1",
        outcome=OUTCOME_SUCCEEDED,
        timestamp="t1",
        record_id="rec-1",
    )
    with pytest.raises(PendingReadinessAlreadyConsumedError):
        store.record_publication_attempt(
            package.package_id, attempt_id="a2", outcome=OUTCOME_FAILED, timestamp="t2"
        )


def test_succeeded_outcome_requires_record_id(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    with pytest.raises(ValueError):
        store.record_publication_attempt(
            package.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1"
        )


def test_invalid_outcome_rejected(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    with pytest.raises(ValueError):
        store.record_publication_attempt(
            package.package_id, attempt_id="a1", outcome="bogus", timestamp="t1"
        )


# --- Publication disposition ------------------------------------------------


def test_successful_publication_moves_to_consumed(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id,
        attempt_id="a1",
        outcome=OUTCOME_SUCCEEDED,
        timestamp="t1",
        record_id="rec-1",
        publication_attempt_id="pub-1",
    )
    assert not (store.root / f"{package.package_id}.json").exists()
    assert (store.consumed_root / f"{package.package_id}.json").exists()
    record = store.load(package.package_id)
    assert record.disposition == DISPOSITION_CONSUMED
    assert record.record_id == "rec-1"
    assert record.publication_attempt_id == "pub-1"


def test_failed_publication_leaves_package_pending(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_FAILED, timestamp="t1"
    )
    assert (store.root / f"{package.package_id}.json").exists()
    assert not (store.consumed_root / f"{package.package_id}.json").exists()
    record = store.load(package.package_id)
    assert record.disposition == DISPOSITION_PENDING
    assert record.record_id is None


def test_retry_after_failure_can_still_succeed(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_FAILED, timestamp="t1"
    )
    record = store.record_publication_attempt(
        package.package_id,
        attempt_id="a2",
        outcome=OUTCOME_SUCCEEDED,
        timestamp="t2",
        record_id="rec-1",
    )
    assert record.disposition == DISPOSITION_CONSUMED
    assert len(record.attempts) == 2


def test_consumed_package_excluded_from_list_but_still_found_by_session(tmp_path):
    """IWPC-001 v1.4 §35 (IWPC-REQ-198): list_package_ids remains
    pending-only (unaffected), but find_by_session_id must now reach a
    consumed/ record -- this is the exact H-1 fix."""

    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1", record_id="rec-1"
    )
    assert store.list_package_ids() == []
    found = store.find_by_session_id(package.session_id)
    assert found is not None
    assert found.package_id == package.package_id
    assert found.disposition == DISPOSITION_CONSUMED
    assert found.record_id == "rec-1"


def test_find_by_session_id_does_not_construct_or_mutate_consumed_record(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1", record_id="rec-1"
    )
    before = store.load(package.package_id)
    store.find_by_session_id(package.session_id)
    store.find_by_session_id(package.session_id)
    after = store.load(package.package_id)
    assert before == after
    assert not (store.root / f"{package.package_id}.json").exists()
    assert (store.consumed_root / f"{package.package_id}.json").exists()


def test_find_by_session_id_repeated_after_consumption_returns_same_identity(tmp_path):
    """Reproduces the original H-1 sequence: readiness -> publish ->
    readiness (again) MUST return package A, never mint a second
    package_id (IWPC-REQ-197 invariant 5)."""

    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1", record_id="rec-1"
    )
    first = store.find_by_session_id(package.session_id)
    second = store.find_by_session_id(package.session_id)
    assert first.package_id == second.package_id == package.package_id
    assert store.list_package_ids() == []


def test_find_by_session_id_fails_closed_on_duplicate_historical_records(tmp_path):
    """IWPC-REQ-204: a repository already carrying more than one readiness
    record for a single session_id (a pre-145H.2 historical inconsistency)
    must fail closed, not silently select one record as authoritative."""

    store = _store(tmp_path)
    session_id = generate_session_id()
    package_a = _package(package_id="pkg-dup-a", session_id=session_id)
    package_b = _package(package_id="pkg-dup-b", session_id=session_id)
    store.create(package_a, persisted_at="t0")
    store.create(package_b, persisted_at="t0")
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.find_by_session_id(session_id)


def test_find_by_session_id_fails_closed_on_duplicate_across_pending_and_consumed(tmp_path):
    store = _store(tmp_path)
    session_id = generate_session_id()
    package_a = _package(package_id="pkg-dup-c", session_id=session_id)
    package_b = _package(package_id="pkg-dup-d", session_id=session_id)
    store.create(package_a, persisted_at="t0")
    store.create(package_b, persisted_at="t0")
    store.record_publication_attempt(
        package_a.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1", record_id="rec-1"
    )
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.find_by_session_id(session_id)


def test_find_by_session_id_fails_closed_on_corrupted_consumed_record(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1", record_id="rec-1"
    )
    consumed_path = store.consumed_root / f"{package.package_id}.json"
    payload = json.loads(consumed_path.read_bytes())
    payload["package_digest"] = "0" * 64
    consumed_path.write_bytes(json.dumps(payload).encode("utf-8"))
    with pytest.raises(PendingReadinessDigestMismatchError):
        store.find_by_session_id(package.session_id)


def test_consumed_package_still_loadable_for_replay(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1", record_id="rec-1"
    )
    record = store.load(package.package_id)
    assert record.package == package
    assert record.record_id == "rec-1"


# --- Atomicity ---------------------------------------------------------------


def test_create_leaves_no_temp_files_behind(tmp_path):
    store = _store(tmp_path)
    store.create(_package(), persisted_at="t0")
    leftovers = [p for p in store.root.iterdir() if p.name.startswith(".tmp-")]
    assert leftovers == []


def test_interrupted_create_leaves_no_package_file(tmp_path, monkeypatch):
    store = _store(tmp_path)
    package = _package()

    def _boom(src, dst):
        raise OSError("simulated interruption")

    monkeypatch.setattr(os, "replace", _boom)
    with pytest.raises(PersistenceUnavailableError):
        store.create(package, persisted_at="t0")
    assert not store.exists(package.package_id)
    leftovers = [p for p in store.root.iterdir() if p.name.startswith(".tmp-")]
    assert leftovers == []


def test_interrupted_disposition_update_leaves_prior_record_intact(tmp_path, monkeypatch):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")

    def _boom(src, dst):
        raise OSError("simulated interruption")

    monkeypatch.setattr(os, "replace", _boom)
    with pytest.raises(PersistenceUnavailableError):
        store.record_publication_attempt(
            package.package_id, attempt_id="a1", outcome=OUTCOME_FAILED, timestamp="t1"
        )
    record = store.load(package.package_id)
    assert record.attempts == ()
    assert record.disposition == DISPOSITION_PENDING


def test_orphan_temp_file_does_not_prevent_recovery(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    orphan = store.root / ".tmp-orphan"
    orphan.write_text("garbage")
    assert store.list_package_ids() == [package.package_id]
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_FAILED, timestamp="t1"
    )
    assert orphan.exists()


def test_exclusive_create_conflict_repeated_operation_is_deterministic(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    for _ in range(3):
        with pytest.raises(PendingReadinessPackageAlreadyExistsError):
            store.create(package, persisted_at="t1")


# --- Corruption detection -----------------------------------------------------


def test_load_malformed_json_raises_store_corrupt(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    (store.root / f"{package.package_id}.json").write_text("{not json")
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.load(package.package_id)


def test_load_truncated_file_raises_store_corrupt(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    original = path.read_text()
    path.write_text(original[: len(original) // 2])
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.load(package.package_id)


def test_missing_wrapper_top_level_raises_store_corrupt(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    path.write_text(json.dumps(["not", "an", "object"]))
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.load(package.package_id)


def test_missing_package_payload_raises_store_corrupt(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    payload = json.loads(path.read_text())
    del payload["package"]
    path.write_text(json.dumps(payload))
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.load(package.package_id)


def test_unsupported_schema_version_raises_store_corrupt(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    payload = json.loads(path.read_text())
    payload["schema_version"] = "pending-readiness-store/999.0"
    path.write_text(json.dumps(payload))
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.load(package.package_id)


def test_package_id_mismatch_raises_store_corrupt(tmp_path):
    store = _store(tmp_path)
    package_a = _package(package_id="pkg-a")
    package_b = _package(package_id="pkg-b")
    store.create(package_a, persisted_at="t0")
    store.create(package_b, persisted_at="t0")
    path_a = store.root / "pkg-a.json"
    path_b = store.root / "pkg-b.json"
    payload_a = json.loads(path_a.read_text())
    payload_b = json.loads(path_b.read_text())
    path_a.write_text(json.dumps(payload_b))
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.load("pkg-a")


def test_session_id_binding_mismatch_raises_store_corrupt(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    payload = json.loads(path.read_text())
    payload["session_id"] = generate_session_id()
    path.write_text(json.dumps(payload))
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.load(package.package_id)


def test_malformed_disposition_raises_store_corrupt(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    payload = json.loads(path.read_text())
    payload["disposition"] = "not-a-real-state"
    path.write_text(json.dumps(payload))
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.load(package.package_id)


def test_inconsistent_attempt_metadata_raises_store_corrupt(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    payload = json.loads(path.read_text())
    payload["attempts"] = [{"attempt_id": "a1"}]  # missing outcome/timestamp
    path.write_text(json.dumps(payload))
    with pytest.raises(PendingReadinessStoreCorruptError):
        store.load(package.package_id)


def test_load_does_not_attempt_partial_recovery(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    path = store.root / f"{package.package_id}.json"
    payload = json.loads(path.read_text())
    payload["package"]["decision_subject"] = None
    path.write_text(json.dumps(payload))
    with pytest.raises((PendingReadinessStoreCorruptError, PendingReadinessDigestMismatchError)):
        store.load(package.package_id)
    assert json.loads(path.read_text())["package"]["decision_subject"] is None


# --- Security ------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_id",
    [
        "../etc/passwd",
        "/etc/passwd",
        "a/b",
        "a\\b",
        "..",
        ".",
        "",
        "x" * 300,
        "!not-safe",
    ],
)
def test_invalid_package_ids_rejected(bad_id):
    assert is_valid_package_id(bad_id) is False


@pytest.mark.parametrize(
    "bad_id",
    [
        "../etc/passwd",
        "a/b",
        "a\\b",
        "",
    ],
)
def test_path_traversal_identifiers_rejected_before_filesystem_access(tmp_path, bad_id):
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        store.load(bad_id)
    assert not (tmp_path / "etc").exists()


def test_load_rejects_symlinked_package_file(tmp_path):
    store = _store(tmp_path)
    real_package = _package(package_id="pkg-real")
    store.create(real_package, persisted_at="t0")
    store.root.mkdir(parents=True, exist_ok=True)
    symlink_path = store.root / "pkg-symlink.json"
    symlink_path.symlink_to(store.root / "pkg-real.json")
    with pytest.raises(PersistenceUnavailableError):
        store.load("pkg-symlink")


def test_create_refuses_symlinked_target(tmp_path):
    store = _store(tmp_path)
    store.root.mkdir(parents=True, exist_ok=True)
    outside_target = tmp_path / "outside.json"
    outside_target.write_text("{}")
    symlink_path = store.root / "pkg-1.json"
    symlink_path.symlink_to(outside_target)
    with pytest.raises(PersistenceUnavailableError):
        store.create(_package(package_id="pkg-1"), persisted_at="t0")
    assert outside_target.read_text() == "{}"


def test_no_world_writable_files_created(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    mode = (store.root / f"{package.package_id}.json").stat().st_mode
    assert not mode & 0o002


def test_store_uses_no_locking_primitive_module():
    import pcae.interactive_workflow.persistence.filesystem_pending_readiness_store as module

    source = Path(module.__file__).read_text()
    for forbidden in ("fcntl", "portalocker", "filelock"):
        assert forbidden not in source


# --- Concurrency (last-write-wins for non-authority-relevant metadata) -----


def test_simultaneous_identical_creation_second_call_fails_deterministically(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    with pytest.raises(PendingReadinessPackageAlreadyExistsError):
        store.create(package, persisted_at="t0")


def test_concurrent_attempt_binding_races_are_deterministic(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    # Two "concurrent" callers race to record the same successful outcome.
    first = store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1", record_id="rec-1"
    )
    second = store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1", record_id="rec-1"
    )
    assert first.record_id == second.record_id == "rec-1"
    assert first.disposition == second.disposition == DISPOSITION_CONSUMED


# --- Recovery ---------------------------------------------------------------


def test_restart_after_completed_publication_reports_consumed(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1", record_id="rec-1"
    )
    fresh_store = FilesystemPendingReadinessStore(root=store.root)
    record = fresh_store.load(package.package_id)
    assert record.disposition == DISPOSITION_CONSUMED


def test_restart_after_failed_publication_reports_pending(tmp_path):
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_FAILED, timestamp="t1"
    )
    fresh_store = FilesystemPendingReadinessStore(root=store.root)
    record = fresh_store.load(package.package_id)
    assert record.disposition == DISPOSITION_PENDING
    assert len(record.attempts) == 1


def test_recovery_prefers_consumed_over_stale_pending_duplicate(tmp_path):
    # Simulate an interruption between the consumed write and the pending
    # unlink (IWPC-REQ-154): both files present, consumed authoritative.
    store = _store(tmp_path)
    package = _package()
    store.create(package, persisted_at="t0")
    store.record_publication_attempt(
        package.package_id, attempt_id="a1", outcome=OUTCOME_SUCCEEDED, timestamp="t1", record_id="rec-1"
    )
    consumed_path = store.consumed_root / f"{package.package_id}.json"
    stale_pending_path = store.root / f"{package.package_id}.json"
    stale_pending_path.write_text(consumed_path.read_text())
    # Rewrite the stale pending copy's own disposition back to "pending"
    # to simulate the pre-move state exactly.
    payload = json.loads(stale_pending_path.read_text())
    payload["disposition"] = DISPOSITION_PENDING
    payload["record_id"] = None
    payload["consumed_at"] = None
    payload["package_digest"] = payload["package_digest"]
    stale_pending_path.write_text(json.dumps(payload))
    record = store.load(package.package_id)
    assert record.disposition == DISPOSITION_CONSUMED
    assert store.list_package_ids() == []


# --- Dependency boundary ----------------------------------------------------


_FORBIDDEN_IMPORT_ROOTS = (
    "pcae.cli",
    "pcae.commands",
    "pcae.governance.publication",
    "pcae.lifecycle",
    "pcae.core.permission_broker",
    "pcae.core.permission_broker_foundation",
    "pcae.governance.verification",
    "pcae.governance.inspection",
    "pcae.interactive_workflow.orchestration",
    "pcae.interactive_workflow.session.coordinator",
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


def test_store_module_has_no_forbidden_imports():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "pcae"
        / "interactive_workflow"
        / "persistence"
        / "filesystem_pending_readiness_store.py"
    )
    modules = _imported_modules(module_path)
    for module in modules:
        for forbidden_root in _FORBIDDEN_IMPORT_ROOTS:
            assert not (module == forbidden_root or module.startswith(forbidden_root + ".")), (
                f"filesystem_pending_readiness_store.py imports {module!r}, coupling "
                f"the Pending-Readiness Store to {forbidden_root!r} in violation of "
                "IWPC-001's dependency rules."
            )


def test_store_schema_version_constant():
    assert STORE_SCHEMA_VERSION == "pending-readiness-store/1.0"
