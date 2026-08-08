"""Phase 149O.18A — HATP Mandatory Cutover State Foundation.

Unit coverage for `pcae.core.hatp_mandatory_cutover` (HMRC-001 §13/§17-19,
Wave A): mode vocabulary, Cutover Record model/parser, protected-path
safety, mode resolution (first-install / valid record / deleted / corrupt
/ wrong-repository / unknown-version / boolean-version), the monotonic
activation-history marker, transition-graph validation, and the internal
transition-write seam (downgrade rejection, concurrent-transition safety).

Attack-matrix coverage (HMRC-001 §29): 22, 39, 40, 41, 42.
"""
from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core.hatp_mandatory_cutover import (
    REASON_FAIL_CLOSED_INTERNAL_CONSISTENCY,
    REASON_FAIL_CLOSED_NO_REPOSITORY_IDENTITY,
    REASON_FAIL_CLOSED_RECORD_CORRUPT_AFTER_PRIOR_ACTIVATION,
    REASON_FAIL_CLOSED_RECORD_MISSING_AFTER_PRIOR_ACTIVATION,
    REASON_FIRST_INSTALL,
    REASON_RECORD_VALID,
    CutoverActivationMarker,
    CutoverMode,
    CutoverRecord,
    CutoverStateMalformedError,
    CutoverStateSymlinkError,
    CutoverTransitionRejectedError,
    _resolve_cutover_mode_at_root,
    _write_activation_marker_if_absent,
    _write_cutover_transition,
    is_valid_cutover_transition,
    parse_cutover_activation_marker,
    parse_cutover_record,
)

pytestmark = pytest.mark.skipif(__import__("os").name != "posix", reason="POSIX-only symlink/lock semantics")


def _repo_id() -> str:
    return str(uuid.uuid4())


def _record_document(*, repository_instance_id: str, mode: str = "PREPARED", version: object = 1, activated_at: str = "2026-08-08T12:00:00.000Z", activated_by: str = "admin-operator") -> dict:
    return {
        "version": version,
        "repository_instance_id": repository_instance_id,
        "mode": mode,
        "activated_at": activated_at,
        "activated_by": activated_by,
    }


def _write_record(root: Path, document: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "cutover-record.json").write_text(json.dumps(document), encoding="utf-8")


def _write_marker(root: Path, document: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "cutover-activation-marker.json").write_text(json.dumps(document), encoding="utf-8")


def _marker_document(*, repository_instance_id: str, version: object = 1, first_activated_at: str = "2026-08-01T00:00:00.000Z") -> dict:
    return {
        "version": version,
        "repository_instance_id": repository_instance_id,
        "first_activated_at": first_activated_at,
    }


# ── Cutover Mode vocabulary ─────────────────────────────────────────────


def test_exactly_three_modes() -> None:
    assert {m.value for m in CutoverMode} == {"LEGACY_COMPATIBLE", "PREPARED", "HATP_MANDATORY"}


# ── Transition graph (HMRC-REQ-038/039) ─────────────────────────────────


@pytest.mark.parametrize(
    "current,target,expected",
    [
        (CutoverMode.LEGACY_COMPATIBLE, CutoverMode.PREPARED, True),
        (CutoverMode.PREPARED, CutoverMode.HATP_MANDATORY, True),
        (CutoverMode.LEGACY_COMPATIBLE, CutoverMode.HATP_MANDATORY, False),
        (CutoverMode.PREPARED, CutoverMode.LEGACY_COMPATIBLE, False),
        (CutoverMode.HATP_MANDATORY, CutoverMode.PREPARED, False),
        (CutoverMode.HATP_MANDATORY, CutoverMode.LEGACY_COMPATIBLE, False),
        (CutoverMode.LEGACY_COMPATIBLE, CutoverMode.LEGACY_COMPATIBLE, False),
        (CutoverMode.PREPARED, CutoverMode.PREPARED, False),
        (CutoverMode.HATP_MANDATORY, CutoverMode.HATP_MANDATORY, False),
    ],
)
def test_transition_graph(current: CutoverMode, target: CutoverMode, expected: bool) -> None:
    assert is_valid_cutover_transition(current, target) is expected


# ── Cutover Record parser: valid ────────────────────────────────────────


def test_parse_valid_prepared_record() -> None:
    repo_id = _repo_id()
    record = parse_cutover_record(_record_document(repository_instance_id=repo_id, mode="PREPARED"))
    assert record == CutoverRecord(
        version=1,
        repository_instance_id=repo_id,
        mode=CutoverMode.PREPARED,
        activated_at="2026-08-08T12:00:00.000Z",
        activated_by="admin-operator",
    )


def test_parse_valid_mandatory_record() -> None:
    repo_id = _repo_id()
    record = parse_cutover_record(_record_document(repository_instance_id=repo_id, mode="HATP_MANDATORY"))
    assert record.mode == CutoverMode.HATP_MANDATORY


def test_cutover_record_is_frozen() -> None:
    record = parse_cutover_record(_record_document(repository_instance_id=_repo_id()))
    with pytest.raises(Exception):
        record.mode = CutoverMode.HATP_MANDATORY  # type: ignore[misc]


# ── Cutover Record parser: closed schema ────────────────────────────────


def test_reject_legacy_compatible_as_stored_mode() -> None:
    with pytest.raises(CutoverStateMalformedError):
        parse_cutover_record(_record_document(repository_instance_id=_repo_id(), mode="LEGACY_COMPATIBLE"))


def test_reject_unknown_mode_string() -> None:
    with pytest.raises(CutoverStateMalformedError):
        parse_cutover_record(_record_document(repository_instance_id=_repo_id(), mode="ENFORCED"))


def test_reject_unknown_field() -> None:
    document = _record_document(repository_instance_id=_repo_id())
    document["extra_field"] = "x"
    with pytest.raises(CutoverStateMalformedError):
        parse_cutover_record(document)


def test_reject_missing_field() -> None:
    document = _record_document(repository_instance_id=_repo_id())
    del document["activated_by"]
    with pytest.raises(CutoverStateMalformedError):
        parse_cutover_record(document)


def test_reject_non_dict_document() -> None:
    with pytest.raises(CutoverStateMalformedError):
        parse_cutover_record(["not", "a", "dict"])


def test_reject_duplicate_json_key_via_raw_text(tmp_path: Path) -> None:
    from pcae.core.hatp_mandatory_cutover import _load_json_no_duplicate_keys

    raw = '{"version": 1, "version": 2, "repository_instance_id": "x", "mode": "PREPARED", "activated_at": "y", "activated_by": "z"}'
    with pytest.raises(CutoverStateMalformedError):
        _load_json_no_duplicate_keys(raw)


# ── Cutover Record parser: strict version (HMRC-REQ-046) ────────────────


@pytest.mark.parametrize("bad_version", [True, False, 0, 2, None, "1", 1.0])
def test_reject_invalid_version(bad_version: object) -> None:
    document = _record_document(repository_instance_id=_repo_id(), version=bad_version)
    with pytest.raises(CutoverStateMalformedError):
        parse_cutover_record(document)


def test_accept_strict_integer_version() -> None:
    record = parse_cutover_record(_record_document(repository_instance_id=_repo_id(), version=1))
    assert record.version == 1
    assert type(record.version) is int


# ── Cutover Record parser: repository_instance_id ───────────────────────


@pytest.mark.parametrize("bad_id", ["not-a-uuid", "", None, 12345, "../../etc/passwd"])
def test_reject_invalid_repository_instance_id(bad_id: object) -> None:
    document = _record_document(repository_instance_id=_repo_id())
    document["repository_instance_id"] = bad_id
    with pytest.raises(CutoverStateMalformedError):
        parse_cutover_record(document)


# ── Cutover Record parser: strict timestamp (double-Z hardening) ────────


@pytest.mark.parametrize(
    "bad_timestamp",
    [
        "2026-08-08T12:00:00.000ZZ",
        "2026-08-08T12:00:00.000Z+00:00",
        "2026-08-08T12:00:00.000X+00:00",
        "2026-08-08T12:00:00.000Z ",
        " 2026-08-08T12:00:00.000Z",
        "2026-08-08t12:00:00.000z",
        "2026-08-08T12:00:00.000z",
        "2026-08-08T12:00:00+00:00",
        "2026-08-08T12:00:00",
        "2026-08-08",
        "not-a-timestamp",
        "",
        None,
        "2026-13-08T12:00:00.000Z",
        "2026-08-08T25:00:00.000Z",
    ],
)
def test_reject_malformed_timestamp(bad_timestamp: object) -> None:
    document = _record_document(repository_instance_id=_repo_id())
    document["activated_at"] = bad_timestamp
    with pytest.raises(CutoverStateMalformedError):
        parse_cutover_record(document)


@pytest.mark.parametrize(
    "good_timestamp",
    [
        "2026-08-08T12:00:00Z",
        "2026-08-08T12:00:00.0Z",
        "2026-08-08T12:00:00.000Z",
        "2026-08-08T12:00:00.123456Z",
    ],
)
def test_accept_strict_timestamp(good_timestamp: str) -> None:
    document = _record_document(repository_instance_id=_repo_id())
    document["activated_at"] = good_timestamp
    record = parse_cutover_record(document)
    assert record.activated_at == good_timestamp


# ── Activation marker parser ─────────────────────────────────────────────


def test_parse_valid_marker() -> None:
    repo_id = _repo_id()
    marker = parse_cutover_activation_marker(_marker_document(repository_instance_id=repo_id))
    assert marker == CutoverActivationMarker(
        version=1, repository_instance_id=repo_id, first_activated_at="2026-08-01T00:00:00.000Z"
    )


def test_marker_rejects_unknown_field() -> None:
    document = _marker_document(repository_instance_id=_repo_id())
    document["extra"] = 1
    with pytest.raises(CutoverStateMalformedError):
        parse_cutover_activation_marker(document)


@pytest.mark.parametrize("bad_version", [True, False, 2, "1", None])
def test_marker_rejects_invalid_version(bad_version: object) -> None:
    document = _marker_document(repository_instance_id=_repo_id(), version=bad_version)
    with pytest.raises(CutoverStateMalformedError):
        parse_cutover_activation_marker(document)


# ── Protected-path safety: symlinks ──────────────────────────────────────


def test_record_symlink_rejected(tmp_path: Path) -> None:
    real_target = tmp_path / "elsewhere.json"
    real_target.write_text(json.dumps(_record_document(repository_instance_id=_repo_id())), encoding="utf-8")
    root = tmp_path / "protected"
    root.mkdir()
    (root / "cutover-record.json").symlink_to(real_target)

    resolution = _resolve_cutover_mode_at_root(root, _repo_id())
    # A symlinked record is treated as CORRUPT, never trusted -- with no
    # marker present this resolves to the internal-consistency fail-closed
    # branch, never LEGACY_COMPATIBLE.
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == REASON_FAIL_CLOSED_INTERNAL_CONSISTENCY


def test_parent_symlink_rejected(tmp_path: Path) -> None:
    real_dir = tmp_path / "real-protected"
    real_dir.mkdir()
    _write_record(real_dir, _record_document(repository_instance_id=_repo_id()))
    linked_root = tmp_path / "linked-protected"
    linked_root.symlink_to(real_dir)

    resolution = _resolve_cutover_mode_at_root(linked_root, _repo_id())
    # The symlinked root also makes the marker path's parent a symlink, so
    # the marker read fails closed too (not "absent") -- either fail-closed
    # reason is acceptable; the invariant that matters is the mode.
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason in (
        REASON_FAIL_CLOSED_INTERNAL_CONSISTENCY,
        REASON_FAIL_CLOSED_RECORD_CORRUPT_AFTER_PRIOR_ACTIVATION,
    )


# ── Mode resolution: first install / no repository identity ─────────────


def test_no_repository_identity_fails_closed(tmp_path: Path) -> None:
    resolution = _resolve_cutover_mode_at_root(tmp_path, None)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == REASON_FAIL_CLOSED_NO_REPOSITORY_IDENTITY


def test_first_install_no_record_no_marker_is_legacy(tmp_path: Path) -> None:
    resolution = _resolve_cutover_mode_at_root(tmp_path, _repo_id())
    assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE
    assert resolution.reason == REASON_FIRST_INSTALL


# ── Mode resolution: valid record ────────────────────────────────────────


def test_valid_prepared_record_resolves_prepared(tmp_path: Path) -> None:
    repo_id = _repo_id()
    _write_record(tmp_path, _record_document(repository_instance_id=repo_id, mode="PREPARED"))
    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.PREPARED
    assert resolution.reason == REASON_RECORD_VALID


def test_valid_mandatory_record_resolves_mandatory(tmp_path: Path) -> None:
    repo_id = _repo_id()
    _write_record(tmp_path, _record_document(repository_instance_id=repo_id, mode="HATP_MANDATORY"))
    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == REASON_RECORD_VALID


# ── Mode resolution: wrong repository (attack #40) ───────────────────────


def test_record_for_different_repository_is_not_present_for_this_repo(tmp_path: Path) -> None:
    other_repo_id = _repo_id()
    this_repo_id = _repo_id()
    _write_record(tmp_path, _record_document(repository_instance_id=other_repo_id, mode="HATP_MANDATORY"))

    resolution = _resolve_cutover_mode_at_root(tmp_path, this_repo_id)
    assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE
    assert resolution.reason == REASON_FIRST_INSTALL


def test_record_for_different_repository_with_marker_for_this_repo_fails_closed(tmp_path: Path) -> None:
    other_repo_id = _repo_id()
    this_repo_id = _repo_id()
    _write_record(tmp_path, _record_document(repository_instance_id=other_repo_id, mode="HATP_MANDATORY"))
    _write_marker(tmp_path, _marker_document(repository_instance_id=this_repo_id))

    resolution = _resolve_cutover_mode_at_root(tmp_path, this_repo_id)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == REASON_FAIL_CLOSED_RECORD_MISSING_AFTER_PRIOR_ACTIVATION


# ── Mode resolution: deleted Cutover Record (attack #22) ────────────────


def test_deleted_record_with_marker_fails_closed_never_legacy(tmp_path: Path) -> None:
    repo_id = _repo_id()
    _write_marker(tmp_path, _marker_document(repository_instance_id=repo_id))
    # Record never existed at all in this "deletion" simulation (equivalent
    # end state to writing then deleting it).

    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == REASON_FAIL_CLOSED_RECORD_MISSING_AFTER_PRIOR_ACTIVATION
    assert resolution.mode != CutoverMode.LEGACY_COMPATIBLE


# ── Mode resolution: corrupt Cutover Record (attack #39) ────────────────


def test_corrupt_record_with_marker_fails_closed(tmp_path: Path) -> None:
    repo_id = _repo_id()
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "cutover-record.json").write_text("not json{{{", encoding="utf-8")
    _write_marker(tmp_path, _marker_document(repository_instance_id=repo_id))

    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == REASON_FAIL_CLOSED_RECORD_CORRUPT_AFTER_PRIOR_ACTIVATION


def test_corrupt_record_with_no_marker_is_internal_consistency_failure_not_legacy(tmp_path: Path) -> None:
    repo_id = _repo_id()
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "cutover-record.json").write_text("not json{{{", encoding="utf-8")

    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == REASON_FAIL_CLOSED_INTERNAL_CONSISTENCY
    assert resolution.mode != CutoverMode.LEGACY_COMPATIBLE


# ── Mode resolution: unknown version / boolean version (attacks #41/#42) ─


def test_unknown_version_record_with_marker_fails_closed(tmp_path: Path) -> None:
    repo_id = _repo_id()
    tmp_path.mkdir(parents=True, exist_ok=True)
    document = _record_document(repository_instance_id=repo_id, mode="HATP_MANDATORY", version=999)
    _write_record(tmp_path, document)
    _write_marker(tmp_path, _marker_document(repository_instance_id=repo_id))

    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == REASON_FAIL_CLOSED_RECORD_CORRUPT_AFTER_PRIOR_ACTIVATION


def test_unknown_version_record_never_assumes_legacy_even_without_marker(tmp_path: Path) -> None:
    repo_id = _repo_id()
    document = _record_document(repository_instance_id=repo_id, mode="HATP_MANDATORY", version=999)
    _write_record(tmp_path, document)

    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode != CutoverMode.LEGACY_COMPATIBLE


def test_boolean_version_record_rejected_and_fails_closed(tmp_path: Path) -> None:
    repo_id = _repo_id()
    document = _record_document(repository_instance_id=repo_id, mode="HATP_MANDATORY", version=True)
    _write_record(tmp_path, document)
    _write_marker(tmp_path, _marker_document(repository_instance_id=repo_id))

    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == REASON_FAIL_CLOSED_RECORD_CORRUPT_AFTER_PRIOR_ACTIVATION


# ── Mode resolution: corrupt marker never treated as absent ─────────────


def test_corrupt_marker_never_treated_as_absent(tmp_path: Path) -> None:
    repo_id = _repo_id()
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "cutover-activation-marker.json").write_text("not json{{{", encoding="utf-8")
    # No record at all -- if the corrupt marker were mistaken for "absent",
    # this would incorrectly resolve LEGACY_COMPATIBLE (first-install).

    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.mode != CutoverMode.LEGACY_COMPATIBLE


# ── Mode resolution: no cache (fresh read every call) ────────────────────


def test_no_cache_reflects_state_change_within_same_process(tmp_path: Path) -> None:
    repo_id = _repo_id()
    first = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert first.mode == CutoverMode.LEGACY_COMPATIBLE

    _write_record(tmp_path, _record_document(repository_instance_id=repo_id, mode="PREPARED"))
    second = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert second.mode == CutoverMode.PREPARED

    _write_record(tmp_path, _record_document(repository_instance_id=repo_id, mode="HATP_MANDATORY"))
    third = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert third.mode == CutoverMode.HATP_MANDATORY


# ── Activation marker write-once semantics ───────────────────────────────


def test_activation_marker_written_once_never_overwritten(tmp_path: Path) -> None:
    repo_id = _repo_id()
    _write_activation_marker_if_absent(tmp_path, repo_id, "2026-08-08T00:00:00.000Z")
    first_document = json.loads((tmp_path / "cutover-activation-marker.json").read_text(encoding="utf-8"))

    _write_activation_marker_if_absent(tmp_path, repo_id, "2027-01-01T00:00:00.000Z")
    second_document = json.loads((tmp_path / "cutover-activation-marker.json").read_text(encoding="utf-8"))

    assert first_document == second_document
    assert second_document["first_activated_at"] == "2026-08-08T00:00:00.000Z"


# ── Transition write: valid transitions ──────────────────────────────────


def test_write_transition_legacy_to_prepared(tmp_path: Path) -> None:
    repo_id = _repo_id()
    record = _write_cutover_transition(
        tmp_path, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="admin"
    )
    assert record.mode == CutoverMode.PREPARED
    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.PREPARED
    assert not (tmp_path / "cutover-activation-marker.json").exists()


def test_write_transition_prepared_to_mandatory_writes_marker(tmp_path: Path) -> None:
    repo_id = _repo_id()
    _write_cutover_transition(tmp_path, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="admin")
    record = _write_cutover_transition(
        tmp_path, target_mode=CutoverMode.HATP_MANDATORY, repository_instance_id=repo_id, activated_by="admin"
    )
    assert record.mode == CutoverMode.HATP_MANDATORY
    marker_path = tmp_path / "cutover-activation-marker.json"
    assert marker_path.exists()
    marker = parse_cutover_activation_marker(json.loads(marker_path.read_text(encoding="utf-8")))
    assert marker.repository_instance_id == repo_id


# ── Transition write: rejected transitions (downgrade, skip) ────────────


def test_write_transition_direct_skip_rejected(tmp_path: Path) -> None:
    repo_id = _repo_id()
    with pytest.raises(CutoverTransitionRejectedError):
        _write_cutover_transition(
            tmp_path, target_mode=CutoverMode.HATP_MANDATORY, repository_instance_id=repo_id, activated_by="admin"
        )
    assert not (tmp_path / "cutover-record.json").exists()


def test_write_transition_downgrade_from_mandatory_rejected(tmp_path: Path) -> None:
    repo_id = _repo_id()
    _write_cutover_transition(tmp_path, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="admin")
    _write_cutover_transition(tmp_path, target_mode=CutoverMode.HATP_MANDATORY, repository_instance_id=repo_id, activated_by="admin")

    with pytest.raises(CutoverTransitionRejectedError):
        _write_cutover_transition(
            tmp_path, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="admin"
        )

    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == REASON_RECORD_VALID


def test_no_disable_or_reset_api_exists() -> None:
    import pcae.core.hatp_mandatory_cutover as module

    public_names = {name for name in dir(module) if not name.startswith("_")}
    forbidden_substrings = ("disable", "reset_cutover", "set_legacy", "downgrade", "deactivate")
    for name in public_names:
        lowered = name.lower()
        assert not any(bad in lowered for bad in forbidden_substrings), f"unexpected deactivation-shaped API: {name}"


# ── Transition write: input validation ───────────────────────────────────


def test_write_transition_rejects_empty_activated_by(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        _write_cutover_transition(
            tmp_path, target_mode=CutoverMode.PREPARED, repository_instance_id=_repo_id(), activated_by=""
        )


def test_write_transition_rejects_invalid_repository_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        _write_cutover_transition(
            tmp_path, target_mode=CutoverMode.PREPARED, repository_instance_id="not-a-uuid", activated_by="admin"
        )


# ── Concurrent transition safety ─────────────────────────────────────────


def test_concurrent_identical_transitions_converge_no_corruption(tmp_path: Path) -> None:
    repo_id = _repo_id()
    results: list[object] = []
    errors: list[BaseException] = []

    def attempt() -> None:
        try:
            results.append(
                _write_cutover_transition(
                    tmp_path, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="admin"
                )
            )
        except CutoverTransitionRejectedError as exc:
            errors.append(exc)

    threads = [threading.Thread(target=attempt) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # Exactly one writer succeeds; the rest observe the already-PREPARED
    # state and are rejected (PREPARED -> PREPARED is not a valid
    # transition) -- never a corrupted/partial file, never a downgrade.
    assert len(results) == 1
    assert len(errors) == 4
    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    assert resolution.mode == CutoverMode.PREPARED
    # The on-disk record must still be strictly parseable (no torn write).
    parse_cutover_record(json.loads((tmp_path / "cutover-record.json").read_text(encoding="utf-8")))


def test_concurrent_prepared_vs_mandatory_never_regresses(tmp_path: Path) -> None:
    repo_id = _repo_id()
    _write_cutover_transition(tmp_path, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="admin")

    outcomes: list[str] = []

    def to_mandatory() -> None:
        try:
            _write_cutover_transition(
                tmp_path, target_mode=CutoverMode.HATP_MANDATORY, repository_instance_id=repo_id, activated_by="admin"
            )
            outcomes.append("mandatory_ok")
        except CutoverTransitionRejectedError:
            outcomes.append("mandatory_rejected")

    def stale_prepared_retry() -> None:
        try:
            _write_cutover_transition(
                tmp_path, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="admin"
            )
            outcomes.append("prepared_ok")
        except CutoverTransitionRejectedError:
            outcomes.append("prepared_rejected")

    threads = [threading.Thread(target=to_mandatory), threading.Thread(target=stale_prepared_retry)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    resolution = _resolve_cutover_mode_at_root(tmp_path, repo_id)
    # PREPARED -> PREPARED was never a valid transition (self-transition),
    # so the stale retry is rejected regardless of thread interleaving,
    # and the genuine PREPARED -> HATP_MANDATORY transition always
    # succeeds -- final state is never a regression from PREPARED.
    assert "prepared_ok" not in outcomes
    assert "mandatory_ok" in outcomes
    assert resolution.mode == CutoverMode.HATP_MANDATORY


# ── Repository-local spoof: creating repo/.pcae/... has no effect ───────


def test_repo_local_pcae_directory_is_never_consulted(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / ".pcae").mkdir(parents=True)
    _write_record(repo_root / ".pcae", _record_document(repository_instance_id=_repo_id(), mode="HATP_MANDATORY"))

    protected_root = tmp_path / "protected"
    resolution = _resolve_cutover_mode_at_root(protected_root, _repo_id())
    assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE
    assert resolution.reason == REASON_FIRST_INSTALL
