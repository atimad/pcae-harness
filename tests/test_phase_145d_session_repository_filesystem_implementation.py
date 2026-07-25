"""Phase 145D unit tests: filesystem ``SessionRepository`` implementation.

Covers repository operations, atomicity, corruption detection, version
validation, security (path traversal / symlink rejection), last-write-wins
concurrency, interrupted-write recovery, and the dependency-boundary rule
(IWPC-001 v1.1 §13, IWPC-REQ-066-077; §19.1; §21; §22; §23). No test in
this module implements or exercises a CLI command, a transport adapter,
the Pending-Readiness Store, or publication orchestration -- Phase 145D's
explicit no-go boundary.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest

from pcae.interactive_workflow.errors import (
    InvalidIdentifierError,
    PersistenceUnavailableError,
    SessionAlreadyExistsError,
    SessionNotFoundError,
    SessionStoreCorruptError,
)
from pcae.interactive_workflow.models.session import Session, SessionState
from pcae.interactive_workflow.persistence.filesystem_repository import (
    DEFAULT_STORAGE_ROOT,
    STORE_SCHEMA_VERSION,
    FilesystemSessionRepository,
)
from pcae.interactive_workflow.persistence.repository import (
    CHGR_STORAGE_PREFIX,
    SessionRepository,
)
from pcae.interactive_workflow.session.identity import generate_session_id


def _session(session_id: str | None = None, **overrides) -> Session:
    fields = dict(
        session_id=session_id or generate_session_id(),
        owner_identity="alice",
        template_ref="template-ref",
        subject_ref="subject-ref",
        session_state=SessionState.CREATED,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
    fields.update(overrides)
    return Session(**fields)


def _repo(tmp_path: Path) -> FilesystemSessionRepository:
    return FilesystemSessionRepository(root=tmp_path / "decision-sessions")


# --- Interface conformance ---------------------------------------------


def test_filesystem_repository_is_a_session_repository(tmp_path):
    repo = _repo(tmp_path)
    assert isinstance(repo, SessionRepository)


def test_default_storage_root_matches_contract_location():
    assert str(DEFAULT_STORAGE_ROOT) == str(Path(".pcae") / "decision-sessions")


# --- Repository operations ----------------------------------------------


def test_create_then_load_round_trips(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    loaded = repo.load(session.session_id)
    assert loaded == session


def test_create_rejects_existing_session_id(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    with pytest.raises(SessionAlreadyExistsError):
        repo.create(session)


def test_load_missing_raises_session_not_found(tmp_path):
    repo = _repo(tmp_path)
    with pytest.raises(SessionNotFoundError):
        repo.load(generate_session_id())


def test_persist_overwrites_existing_record(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    updated = session.with_state(SessionState.EVIDENCE_READY, updated_at="2026-01-02T00:00:00Z")
    repo.persist(updated)
    assert repo.load(session.session_id).session_state is SessionState.EVIDENCE_READY


def test_persist_never_creates(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    with pytest.raises(SessionNotFoundError):
        repo.persist(session)
    assert not repo.exists(session.session_id)


def test_exists_true_after_create_false_before(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    assert repo.exists(session.session_id) is False
    repo.create(session)
    assert repo.exists(session.session_id) is True


def test_exists_is_side_effect_free(tmp_path):
    repo = _repo(tmp_path)
    session_id = generate_session_id()
    repo.exists(session_id)
    assert not repo.root.exists() or list(repo.root.iterdir()) == []


def test_list_session_ids_reflects_created_sessions(tmp_path):
    repo = _repo(tmp_path)
    ids = {generate_session_id() for _ in range(3)}
    for sid in ids:
        repo.create(_session(session_id=sid))
    assert set(repo.list_session_ids()) == ids


def test_list_session_ids_empty_when_root_absent(tmp_path):
    repo = _repo(tmp_path)
    assert list(repo.list_session_ids()) == []


def test_list_session_ids_deterministic_order(tmp_path):
    repo = _repo(tmp_path)
    for _ in range(5):
        repo.create(_session())
    assert repo.list_session_ids() == sorted(repo.list_session_ids())


def test_list_session_ids_skips_unrecognized_files(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    repo.root.mkdir(parents=True, exist_ok=True)
    (repo.root / "not-a-session.json").write_text("{}")
    (repo.root / ".hidden.json").write_text("{}")
    (repo.root / "subdir").mkdir()
    assert repo.list_session_ids() == [session.session_id]


def test_list_session_ids_does_not_load_every_session(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)

    def _fail(*args, **kwargs):
        raise AssertionError("list_session_ids must not load session bodies")

    monkeypatch.setattr(
        "pcae.interactive_workflow.persistence.filesystem_repository.from_payload", _fail
    )
    assert repo.list_session_ids() == [session.session_id]


# --- Storage layout / wire format ---------------------------------------


def test_storage_file_naming_is_session_id_json(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    assert (repo.root / f"{session.session_id}.json").is_file()


def test_persisted_file_carries_store_schema_version(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    raw = json.loads((repo.root / f"{session.session_id}.json").read_text())
    assert raw["schema_version"] == STORE_SCHEMA_VERSION
    assert raw["session_id"] == session.session_id
    assert raw["session"]["schema_version"] == session.schema_version


def test_persisted_session_state_literal_is_pascal_case(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    raw = json.loads((repo.root / f"{session.session_id}.json").read_text())
    assert raw["session"]["session_state"] == "Created"


def test_repository_never_writes_under_chgr_storage_prefix():
    with pytest.raises(ValueError):
        FilesystemSessionRepository(root=Path(CHGR_STORAGE_PREFIX))
    with pytest.raises(ValueError):
        FilesystemSessionRepository(root=Path(CHGR_STORAGE_PREFIX) / "nested")


# --- Atomicity -----------------------------------------------------------


def test_create_leaves_no_temp_files_behind(tmp_path):
    repo = _repo(tmp_path)
    repo.create(_session())
    leftovers = [p for p in repo.root.iterdir() if p.name.startswith(".tmp-")]
    assert leftovers == []


def test_persist_uses_atomic_replace(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)

    calls = []
    real_replace = os.replace

    def _tracking_replace(src, dst):
        calls.append((src, dst))
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", _tracking_replace)
    repo.persist(session.with_state(SessionState.EVIDENCE_READY, updated_at="x"))
    assert len(calls) == 1


def test_interrupted_write_leaves_prior_record_intact(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)

    def _boom(src, dst):
        raise OSError("simulated interruption")

    monkeypatch.setattr(os, "replace", _boom)
    with pytest.raises(PersistenceUnavailableError):
        repo.persist(session.with_state(SessionState.EVIDENCE_READY, updated_at="x"))
    # Prior record is untouched -- no partial write ever lands at the final path.
    assert repo.load(session.session_id) == session
    leftovers = [p for p in repo.root.iterdir() if p.name.startswith(".tmp-")]
    assert leftovers == []


def test_interrupted_create_leaves_no_session_file(tmp_path, monkeypatch):
    repo = _repo(tmp_path)
    session = _session()

    def _boom(src, dst):
        raise OSError("simulated interruption")

    monkeypatch.setattr(os, "replace", _boom)
    with pytest.raises(PersistenceUnavailableError):
        repo.create(session)
    assert not repo.exists(session.session_id)
    leftovers = [p for p in repo.root.iterdir() if p.name.startswith(".tmp-")]
    assert leftovers == []


def test_orphan_temp_file_does_not_prevent_recovery(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    orphan = repo.root / ".tmp-orphan123"
    orphan.write_text("garbage")
    # A stray temp file from a hypothetical prior crash must not confuse
    # enumeration, load, or a subsequent successful persist.
    assert repo.list_session_ids() == [session.session_id]
    repo.persist(session.with_state(SessionState.EVIDENCE_READY, updated_at="x"))
    assert repo.load(session.session_id).session_state is SessionState.EVIDENCE_READY
    assert orphan.exists()  # not this repository's job to sweep unrelated files


# --- Corruption detection -------------------------------------------------


def test_load_malformed_json_raises_store_corrupt(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    (repo.root / f"{session.session_id}.json").write_text("{not json")
    with pytest.raises(SessionStoreCorruptError):
        repo.load(session.session_id)


def test_load_truncated_file_raises_store_corrupt(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    path = repo.root / f"{session.session_id}.json"
    original = path.read_text()
    path.write_text(original[: len(original) // 2])
    with pytest.raises(SessionStoreCorruptError):
        repo.load(session.session_id)


def test_load_unsupported_store_schema_version_raises_store_corrupt(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    path = repo.root / f"{session.session_id}.json"
    payload = json.loads(path.read_text())
    payload["schema_version"] = "decision-session-store/999.0"
    path.write_text(json.dumps(payload))
    with pytest.raises(SessionStoreCorruptError):
        repo.load(session.session_id)


def test_load_missing_nested_session_payload_raises_store_corrupt(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    path = repo.root / f"{session.session_id}.json"
    payload = json.loads(path.read_text())
    del payload["session"]
    path.write_text(json.dumps(payload))
    with pytest.raises(SessionStoreCorruptError):
        repo.load(session.session_id)


def test_load_mismatched_top_level_session_id_raises_store_corrupt(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    path = repo.root / f"{session.session_id}.json"
    payload = json.loads(path.read_text())
    payload["session_id"] = generate_session_id()
    path.write_text(json.dumps(payload))
    with pytest.raises(SessionStoreCorruptError):
        repo.load(session.session_id)


def test_load_does_not_attempt_partial_recovery(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    path = repo.root / f"{session.session_id}.json"
    payload = json.loads(path.read_text())
    payload["session"]["owner_identity"] = None
    path.write_text(json.dumps(payload))
    with pytest.raises(SessionStoreCorruptError):
        repo.load(session.session_id)
    # The corrupt file is left exactly as found -- no silent repair/rewrite.
    assert json.loads(path.read_text())["session"]["owner_identity"] is None


# --- Security --------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_id",
    [
        "../etc/passwd",
        "CDS-../../etc/passwd",
        "CDS-" + "x" * 10,
        "not-a-session-id",
        "",
        "CDS-1234/5678",
        "CDS-1234\\5678",
    ],
)
def test_path_traversal_identifiers_rejected_before_filesystem_access(tmp_path, bad_id):
    repo = _repo(tmp_path)
    with pytest.raises(InvalidIdentifierError):
        repo.load(bad_id)
    with pytest.raises(InvalidIdentifierError):
        repo.exists(bad_id)
    # No file was ever written or probed outside the storage root.
    assert not (tmp_path / "etc").exists()


def test_load_rejects_symlinked_session_file(tmp_path):
    repo = _repo(tmp_path)
    real_session = _session()
    repo.create(real_session)
    target_id = generate_session_id()
    repo.root.mkdir(parents=True, exist_ok=True)
    symlink_path = repo.root / f"{target_id}.json"
    symlink_path.symlink_to(repo.root / f"{real_session.session_id}.json")
    with pytest.raises(PersistenceUnavailableError):
        repo.load(target_id)


def test_persist_refuses_to_write_through_symlink(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    outside_target = tmp_path / "outside.json"
    outside_target.write_text("{}")
    path = repo.root / f"{session.session_id}.json"
    path.unlink()
    path.symlink_to(outside_target)
    with pytest.raises(PersistenceUnavailableError):
        repo.persist(session)
    assert outside_target.read_text() == "{}"


def test_no_world_writable_files_created(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    mode = (repo.root / f"{session.session_id}.json").stat().st_mode
    assert not mode & 0o002  # not world-writable


# --- Concurrency (last-write-wins, no locking primitive; IWPC-REQ-073/141) --


def test_concurrent_persist_is_last_write_wins(tmp_path):
    repo = _repo(tmp_path)
    session = _session()
    repo.create(session)
    first_writer = session.with_state(SessionState.EVIDENCE_READY, updated_at="first")
    second_writer = session.with_state(SessionState.AWAITING_DECISION, updated_at="second")
    repo.persist(first_writer)
    repo.persist(second_writer)
    assert repo.load(session.session_id).session_state is SessionState.AWAITING_DECISION


def test_repository_uses_no_locking_primitive_module():
    import pcae.interactive_workflow.persistence.filesystem_repository as module

    source = Path(module.__file__).read_text()
    for forbidden in ("fcntl", "portalocker", "filelock"):
        assert forbidden not in source


# --- Compatibility / round-trip -------------------------------------------


def test_round_trip_preserves_every_session_field(tmp_path):
    repo = _repo(tmp_path)
    session = _session(
        human_selection_id="sel-1",
        human_rationale_text="because",
        human_conditions_text="none",
        disclosure_acknowledgements=("ack-1", "ack-2"),
        template_version="v1",
        options_presented=("opt-a", "opt-b"),
        metadata={"k": "v"},
    )
    repo.create(session)
    assert repo.load(session.session_id) == session


# --- Dependency boundary (IWPC-001 v1.1 dependency rules) ------------------


_FORBIDDEN_IMPORT_ROOTS = (
    "pcae.cli",
    "pcae.commands",
    "pcae.governance.publication",
    "pcae.lifecycle",
    "pcae.core.permission_broker",
    "pcae.core.permission_broker_foundation",
    "pcae.governance.verification",
    "pcae.governance.inspection",
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


def test_filesystem_repository_module_has_no_forbidden_imports():
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "pcae"
        / "interactive_workflow"
        / "persistence"
        / "filesystem_repository.py"
    )
    modules = _imported_modules(module_path)
    for module in modules:
        for forbidden_root in _FORBIDDEN_IMPORT_ROOTS:
            assert not (module == forbidden_root or module.startswith(forbidden_root + ".")), (
                f"filesystem_repository.py imports {module!r}, coupling "
                f"SessionRepository to {forbidden_root!r} in violation of "
                "IWPC-001's dependency rules."
            )
