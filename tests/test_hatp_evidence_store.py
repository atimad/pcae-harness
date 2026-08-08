"""Phase 149O.12A, Wave B -- `HATPEvidenceStore` exclusive-publication
storage tests for `pcae.core.hatp_evidence_store`.

Real filesystem, real `os.link` calls throughout (governing-prompt §93):
the race-safety guarantee this suite exercises is a real-filesystem
property, not a mockable abstraction. `os.link` itself is mocked only in
the dedicated fault-injection tests (E4), never in the positive-path
suite.
"""
from __future__ import annotations

import errno
import os
import stat
import threading
import uuid
from pathlib import Path

import pytest

from pcae.core.hatp_evidence_store import (
    EvidenceConflictError,
    EvidenceNotFoundError,
    EvidencePersistenceFailureError,
    HATPEvidenceStore,
)
from pcae.core.hatp_signed_evidence import (
    EvidenceIdDigestMismatchError,
    HATPSignedEvidenceError,
    InvalidEvidenceIdError,
    build_hatp_signed_evidence_envelope,
    serialize_hatp_signed_evidence,
)
from pcae.core.human_approval_trusted_provenance import (
    Ag3OperationReference,
    HumanApprovalProvenanceProof,
    RollbackSite,
)
from pcae.core.paths import HarnessPath

_IS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0


def _repo_id() -> str:
    return str(uuid.uuid4())


def _proof(job_id: str = "job-1") -> HumanApprovalProvenanceProof:
    return HumanApprovalProvenanceProof(
        proof_version=1,
        principal_id="alice",
        signer_key_id="signer-1",
        provider_profile="HATP_HARDWARE_PROVIDER_V1",
        repository_id=_repo_id(),
        decision_record_id="chgr-record-1",
        decision_record_digest="a" * 64,
        binding_id="rae-binding-1",
        binding_digest="b" * 64,
        rollback_site=RollbackSite.AG3,
        operation_reference=Ag3OperationReference(job_id=job_id, original_commit_sha="c" * 40),
        issued_at="2026-08-06T00:00:00.000Z",
    )


def _make_store(tmp_path: Path) -> HATPEvidenceStore:
    return HATPEvidenceStore(HarnessPath(tmp_path))


# ═══════════════════════════════════════════════════════════════════════════
# Store root / no-mutation-on-construction (HSCE-REQ-007/041/055)
# ═══════════════════════════════════════════════════════════════════════════


def test_store_root_is_repository_local_and_isolated_from_rae(tmp_path):
    store = _make_store(tmp_path)
    assert store.repository_root == tmp_path
    assert store.envelopes_dir == tmp_path / ".pcae" / "hatp-evidence" / "envelopes"
    assert "rollback-approval-evidence" not in str(store.envelopes_dir)


def test_construction_creates_no_directory(tmp_path):
    _make_store(tmp_path)
    assert not (tmp_path / ".pcae").exists()


def test_path_for_creates_no_directory_and_performs_no_io(tmp_path):
    store = _make_store(tmp_path)
    path = store.path_for("a" * 64)
    assert path == tmp_path / ".pcae" / "hatp-evidence" / "envelopes" / f"{'a' * 64}.json"
    assert not (tmp_path / ".pcae").exists()


# ═══════════════════════════════════════════════════════════════════════════
# Path validation / traversal / case alias (attacks 1, 2)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "bad_id",
    [
        "../../../etc/passwd",
        "/etc/passwd",
        "a" * 63,
        "a" * 65,
        "A" * 64,
        "a" * 31 + "/" + "a" * 32,
        "a" * 31 + "\\" + "a" * 32,
        "%2e%2e" + "a" * 58,
        " " + "a" * 63,
    ],
)
def test_path_for_rejects_malicious_ids_before_filesystem_access(tmp_path, bad_id):
    store = _make_store(tmp_path)
    with pytest.raises(InvalidEvidenceIdError):
        store.path_for(bad_id)
    assert not (tmp_path / ".pcae").exists()


def test_publish_rejects_malicious_evidence_id_before_any_write(tmp_path):
    store = _make_store(tmp_path)
    # Directly attempt to compute a path for a traversal ID -- never
    # reaches os.link or mkdir.
    with pytest.raises(InvalidEvidenceIdError):
        store.path_for("../../evil")
    assert not (tmp_path / ".pcae").exists()


# ═══════════════════════════════════════════════════════════════════════════
# Winner / idempotent / conflict (attacks 3, 4)
# ═══════════════════════════════════════════════════════════════════════════


def test_first_publish_is_winner(tmp_path):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")
    result = store.publish(envelope)
    assert result.idempotent is False
    assert result.evidence_id == envelope.evidence_id
    assert result.path.read_bytes() == serialize_hatp_signed_evidence(envelope)


def test_byte_identical_rewrite_is_idempotent(tmp_path):
    store = _make_store(tmp_path)
    proof = _proof()
    envelope = build_hatp_signed_evidence_envelope(proof, b"assertion")
    first = store.publish(envelope)
    second = store.publish(build_hatp_signed_evidence_envelope(proof, b"assertion"))
    assert first.idempotent is False
    assert second.idempotent is True
    assert first.path == second.path
    assert first.path.read_bytes() == serialize_hatp_signed_evidence(envelope)


def test_differing_rewrite_same_id_conflicts_and_winner_unchanged(tmp_path):
    store = _make_store(tmp_path)
    proof = _proof()
    winner = build_hatp_signed_evidence_envelope(proof, b"assertion-a")
    loser = build_hatp_signed_evidence_envelope(proof, b"assertion-b")
    assert winner.evidence_id == loser.evidence_id

    store.publish(winner)
    with pytest.raises(EvidenceConflictError):
        store.publish(loser)

    on_disk = store.path_for(winner.evidence_id).read_bytes()
    assert on_disk == serialize_hatp_signed_evidence(winner)


def test_same_proof_different_assertion_only_first_persists(tmp_path):
    """Attack-matrix item 4's specific variant (governing-prompt §57)."""

    store = _make_store(tmp_path)
    proof = _proof()
    envelope_a = build_hatp_signed_evidence_envelope(proof, b"first-attempt")
    envelope_b = build_hatp_signed_evidence_envelope(proof, b"second-attempt")

    store.publish(envelope_a)
    with pytest.raises(EvidenceConflictError):
        store.publish(envelope_b)


# ═══════════════════════════════════════════════════════════════════════════
# Load API (explicit-ID-only, missing, corrupt, digest mismatch)
# ═══════════════════════════════════════════════════════════════════════════


def test_load_returns_published_envelope(tmp_path):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")
    store.publish(envelope)
    loaded = store.load(envelope.evidence_id)
    assert loaded == envelope


def test_load_missing_evidence_raises_not_found(tmp_path):
    store = _make_store(tmp_path)
    with pytest.raises(EvidenceNotFoundError):
        store.load("a" * 64)


def test_load_never_creates_a_file(tmp_path):
    store = _make_store(tmp_path)
    with pytest.raises(EvidenceNotFoundError):
        store.load("a" * 64)
    assert not store.path_for("a" * 64).exists()


def test_load_corrupt_json_propagates_parse_error(tmp_path):
    store = _make_store(tmp_path)
    path = store.path_for("a" * 64)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"{not json")
    with pytest.raises(HATPSignedEvidenceError):
        store.load("a" * 64)


def test_load_digest_mismatch_propagates(tmp_path):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")
    canonical_id = envelope.evidence_id
    tampered_id = "f" * 64

    path = store.path_for(tampered_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    import json as _json

    document = _json.loads(serialize_hatp_signed_evidence(envelope))
    document["evidence_id"] = tampered_id
    path.write_text(_json.dumps(document))

    with pytest.raises(EvidenceIdDigestMismatchError):
        store.load(tampered_id)
    assert canonical_id != tampered_id


def test_load_has_no_latest_or_glob_fallback(tmp_path):
    """SC-6: lookup is always explicit-`evidence_id`-only -- no `list`/
    `latest` public method exists on the store."""

    assert not hasattr(HATPEvidenceStore, "latest")
    assert not hasattr(HATPEvidenceStore, "list_latest")
    assert not hasattr(HATPEvidenceStore, "list")
    assert not hasattr(HATPEvidenceStore, "exists")
    assert not hasattr(HATPEvidenceStore, "overwrite")
    assert not hasattr(HATPEvidenceStore, "update")
    assert not hasattr(HATPEvidenceStore, "approve")
    assert not hasattr(HATPEvidenceStore, "delete_authority")


# ═══════════════════════════════════════════════════════════════════════════
# Symlink safety (attacks 13, 14)
# ═══════════════════════════════════════════════════════════════════════════


def test_publish_rejects_symlinked_final_destination(tmp_path):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")

    outside_target = tmp_path.parent / f"outside-{uuid.uuid4()}.json"
    outside_target.write_bytes(b"not evidence")
    try:
        final_path = store.path_for(envelope.evidence_id)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        final_path.symlink_to(outside_target)

        with pytest.raises(EvidencePersistenceFailureError):
            store.publish(envelope)
        # The symlink itself, and the outside target, are both untouched.
        assert final_path.is_symlink()
        assert outside_target.read_bytes() == b"not evidence"
    finally:
        outside_target.unlink(missing_ok=True)


def test_load_rejects_symlinked_final_destination(tmp_path):
    store = _make_store(tmp_path)
    outside_target = tmp_path.parent / f"outside-{uuid.uuid4()}.json"
    outside_target.write_bytes(b"not evidence")
    try:
        final_path = store.path_for("a" * 64)
        final_path.parent.mkdir(parents=True, exist_ok=True)
        final_path.symlink_to(outside_target)

        with pytest.raises(EvidencePersistenceFailureError):
            store.load("a" * 64)
    finally:
        outside_target.unlink(missing_ok=True)


@pytest.mark.parametrize("escaping_component", [".pcae", "hatp-evidence", "envelopes"])
def test_publish_rejects_escaping_path_component_symlink(tmp_path, escaping_component):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")

    outside_dir = tmp_path.parent / f"outside-dir-{uuid.uuid4()}"
    outside_dir.mkdir()
    try:
        components = [".pcae", "hatp-evidence", "envelopes"]
        idx = components.index(escaping_component)
        parent = tmp_path.joinpath(*components[:idx])
        parent.mkdir(parents=True, exist_ok=True)
        (parent / escaping_component).symlink_to(outside_dir)

        with pytest.raises(EvidencePersistenceFailureError):
            store.publish(envelope)
        # Nothing was created inside the escaped-to directory.
        assert list(outside_dir.iterdir()) == []
    finally:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# 149O.10.2-Obs-3: unsafe existing-final-object -> evidence_persistence_failure
# ═══════════════════════════════════════════════════════════════════════════


def test_publish_existing_directory_at_final_path_fails_closed(tmp_path):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")
    final_path = store.path_for(envelope.evidence_id)
    final_path.mkdir(parents=True, exist_ok=True)

    with pytest.raises(EvidencePersistenceFailureError):
        store.publish(envelope)
    assert final_path.is_dir()


def test_publish_existing_fifo_at_final_path_fails_closed(tmp_path):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")
    final_path = store.path_for(envelope.evidence_id)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    os.mkfifo(str(final_path))

    with pytest.raises(EvidencePersistenceFailureError):
        store.publish(envelope)
    assert stat.S_ISFIFO(os.lstat(final_path).st_mode)


@pytest.mark.skipif(_IS_ROOT, reason="root bypasses file permission bits")
def test_publish_unreadable_existing_final_fails_closed(tmp_path):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")
    final_path = store.path_for(envelope.evidence_id)
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_bytes(b"pre-existing, unreadable")
    os.chmod(final_path, 0o000)
    try:
        with pytest.raises(EvidencePersistenceFailureError):
            store.publish(envelope)
    finally:
        os.chmod(final_path, 0o644)


# ═══════════════════════════════════════════════════════════════════════════
# Temp-file lifecycle / no post-link writes (extra attacks E2, temp cleanup)
# ═══════════════════════════════════════════════════════════════════════════


def test_temp_file_cleaned_up_after_successful_publish(tmp_path):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")
    store.publish(envelope)
    remaining = list(store.envelopes_dir.iterdir())
    assert remaining == [store.path_for(envelope.evidence_id)]


def test_temp_file_cleaned_up_after_idempotent_publish(tmp_path):
    store = _make_store(tmp_path)
    proof = _proof()
    store.publish(build_hatp_signed_evidence_envelope(proof, b"assertion"))
    store.publish(build_hatp_signed_evidence_envelope(proof, b"assertion"))
    remaining = list(store.envelopes_dir.iterdir())
    assert len(remaining) == 1


def test_temp_file_cleaned_up_after_conflict(tmp_path):
    store = _make_store(tmp_path)
    proof = _proof()
    store.publish(build_hatp_signed_evidence_envelope(proof, b"assertion-a"))
    with pytest.raises(EvidenceConflictError):
        store.publish(build_hatp_signed_evidence_envelope(proof, b"assertion-b"))
    remaining = list(store.envelopes_dir.iterdir())
    assert len(remaining) == 1


def test_loader_never_treats_temp_file_as_evidence(tmp_path):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")
    store.envelopes_dir.mkdir(parents=True, exist_ok=True)
    orphan_temp = store.envelopes_dir / f".{envelope.evidence_id}.orphan.tmp"
    orphan_temp.write_bytes(b"garbage, must never be loaded")

    with pytest.raises(EvidenceNotFoundError):
        store.load(envelope.evidence_id)


def test_write_descriptor_closed_before_link_is_attempted(tmp_path, monkeypatch):
    """Extra attack E2: the writable temp file descriptor MUST already be
    closed by the time `os.link` is called -- instrumented by attempting
    to write through the captured fd from inside a wrapped `os.link`."""

    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")

    captured = {}
    real_fdopen = os.fdopen
    real_link = os.link

    def spy_fdopen(fd, *args, **kwargs):
        captured["fd"] = fd
        return real_fdopen(fd, *args, **kwargs)

    def spy_link(src, dst, *args, **kwargs):
        fd = captured.get("fd")
        assert fd is not None, "temp file descriptor was never captured"
        with pytest.raises(OSError):
            os.write(fd, b"post-link-mutation-attempt")
        return real_link(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "fdopen", spy_fdopen)
    monkeypatch.setattr(os, "link", spy_link)

    result = store.publish(envelope)
    assert result.idempotent is False
    assert result.path.read_bytes() == serialize_hatp_signed_evidence(envelope)


def test_no_post_link_write_mutates_canonical_evidence(tmp_path):
    """After a successful publish, the persisted bytes must be exactly
    the canonical bytes -- nothing writes through the temp inode after
    the hard link is established."""

    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")
    result = store.publish(envelope)
    canonical = serialize_hatp_signed_evidence(envelope)
    assert result.path.read_bytes() == canonical
    # Re-reading later (simulating a subsequent process) confirms no
    # further mutation occurred.
    assert store.load(envelope.evidence_id) == envelope


# ═══════════════════════════════════════════════════════════════════════════
# Fault injection: non-EEXIST os.link errors (extra attack E4)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("error_code", [errno.EXDEV, errno.EPERM])
def test_non_eexist_link_errors_fail_closed_no_fallback(tmp_path, monkeypatch, error_code):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")

    def raising_link(src, dst):
        raise OSError(error_code, os.strerror(error_code))

    monkeypatch.setattr(os, "link", raising_link)

    with pytest.raises(EvidencePersistenceFailureError):
        store.publish(envelope)

    assert not store.path_for(envelope.evidence_id).exists()
    # No leftover temp file either.
    assert list(store.envelopes_dir.glob("*.tmp")) == []


def test_unsupported_hard_link_filesystem_fails_closed_no_replace_fallback(tmp_path, monkeypatch):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")

    replace_called = {"value": False}
    real_os_replace = os.replace

    def spy_replace(*args, **kwargs):
        replace_called["value"] = True
        return real_os_replace(*args, **kwargs)

    def raising_link(src, dst):
        raise OSError(errno.ENOTSUP, "hard links not supported on this filesystem")

    monkeypatch.setattr(os, "link", raising_link)
    monkeypatch.setattr(os, "replace", spy_replace)

    with pytest.raises(EvidencePersistenceFailureError):
        store.publish(envelope)

    assert replace_called["value"] is False
    assert not store.path_for(envelope.evidence_id).exists()


# ═══════════════════════════════════════════════════════════════════════════
# Partial write / fsync failure (attack 15 analogue)
# ═══════════════════════════════════════════════════════════════════════════


def test_fsync_failure_leaves_no_partial_final_artifact(tmp_path, monkeypatch):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")

    def raising_fsync(fd):
        raise OSError("simulated fsync failure")

    monkeypatch.setattr(os, "fsync", raising_fsync)

    with pytest.raises(EvidencePersistenceFailureError):
        store.publish(envelope)

    assert not store.path_for(envelope.evidence_id).exists()
    assert list(store.envelopes_dir.glob("*.tmp")) == []


def test_write_failure_leaves_no_partial_final_artifact(tmp_path, monkeypatch):
    store = _make_store(tmp_path)
    envelope = build_hatp_signed_evidence_envelope(_proof(), b"assertion")

    import io

    class FailingWriter(io.RawIOBase):
        def writable(self):
            return True

        def write(self, data):
            raise OSError("simulated partial write failure")

    real_fdopen = os.fdopen

    def raising_fdopen(fd, mode="r", *args, **kwargs):
        os.close(fd)
        return FailingWriter()

    monkeypatch.setattr(os, "fdopen", raising_fdopen)

    with pytest.raises(EvidencePersistenceFailureError):
        store.publish(envelope)

    assert not store.path_for(envelope.evidence_id).exists()


# ═══════════════════════════════════════════════════════════════════════════
# Real filesystem concurrency (attacks 3, 4, 15, extra attack E3)
# ═══════════════════════════════════════════════════════════════════════════


def _publish_concurrently(store, envelopes):
    results = [None] * len(envelopes)
    errors = [None] * len(envelopes)
    barrier = threading.Barrier(len(envelopes))

    def worker(index):
        barrier.wait()
        try:
            results[index] = store.publish(envelopes[index])
        except Exception as exc:  # noqa: BLE001 -- captured for assertion, not swallowed
            errors[index] = exc

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(len(envelopes))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results, errors


def test_two_identical_concurrent_writers_race_safely(tmp_path):
    store = _make_store(tmp_path)
    proof = _proof()
    envelopes = [build_hatp_signed_evidence_envelope(proof, b"same-assertion") for _ in range(2)]

    results, errors = _publish_concurrently(store, envelopes)
    assert all(err is None for err in errors), errors
    winners = [r for r in results if not r.idempotent]
    losers = [r for r in results if r.idempotent]
    assert len(winners) == 1
    assert len(losers) == 1
    assert store.path_for(envelopes[0].evidence_id).read_bytes() == serialize_hatp_signed_evidence(envelopes[0])


def test_two_differing_concurrent_writers_race_safely(tmp_path):
    store = _make_store(tmp_path)
    proof = _proof()
    envelopes = [
        build_hatp_signed_evidence_envelope(proof, b"assertion-a"),
        build_hatp_signed_evidence_envelope(proof, b"assertion-b"),
    ]

    results, errors = _publish_concurrently(store, envelopes)
    successes = [r for r in results if r is not None]
    conflicts = [e for e in errors if isinstance(e, EvidenceConflictError)]
    assert len(successes) == 1
    assert len(conflicts) == 1
    winner_bytes = store.path_for(envelopes[0].evidence_id).read_bytes()
    assert winner_bytes in (
        serialize_hatp_signed_evidence(envelopes[0]),
        serialize_hatp_signed_evidence(envelopes[1]),
    )


@pytest.mark.parametrize("writer_count", [8, 16])
def test_many_identical_writers_exactly_one_canonical_file(tmp_path, writer_count):
    store = _make_store(tmp_path)
    proof = _proof()
    envelopes = [build_hatp_signed_evidence_envelope(proof, b"identical") for _ in range(writer_count)]

    results, errors = _publish_concurrently(store, envelopes)
    assert all(err is None for err in errors), errors
    winners = [r for r in results if not r.idempotent]
    assert len(winners) == 1
    files = list(store.envelopes_dir.glob("*.json"))
    assert len(files) == 1


def test_many_mixed_writers_identical_and_differing(tmp_path):
    store = _make_store(tmp_path)
    proof = _proof()
    envelopes = []
    for i in range(8):
        # Half identical (empty-string suffix collapses to two distinct
        # byte strings across the whole set), half distinct.
        assertion = b"identical-group" if i % 2 == 0 else f"distinct-{i}".encode()
        envelopes.append(build_hatp_signed_evidence_envelope(proof, assertion))

    results, errors = _publish_concurrently(store, envelopes)
    successes = [r for r in results if r is not None]
    conflicts = [e for e in errors if isinstance(e, EvidenceConflictError)]
    assert len(successes) + len(conflicts) == 8
    assert len(successes) >= 1
    files = list(store.envelopes_dir.glob("*.json"))
    assert len(files) == 1
    # Exactly one on-disk byte-sequence is canonical.
    canonical_bytes = store.path_for(envelopes[0].evidence_id).read_bytes()
    assert canonical_bytes in {serialize_hatp_signed_evidence(e) for e in envelopes}


def test_race_stability_repeated_iterations(tmp_path):
    """Governing-prompt §65: avoid timing-dependent false assurance --
    run the race multiple times, each in its own isolated subdirectory."""

    for iteration in range(5):
        iteration_root = tmp_path / f"iter-{iteration}"
        iteration_root.mkdir()
        store = _make_store(iteration_root)
        proof = _proof()
        envelopes = [build_hatp_signed_evidence_envelope(proof, b"same") for _ in range(6)]
        results, errors = _publish_concurrently(store, envelopes)
        assert all(err is None for err in errors), (iteration, errors)
        winners = [r for r in results if not r.idempotent]
        assert len(winners) == 1, iteration
