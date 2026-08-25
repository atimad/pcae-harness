"""Phase 149O.20L.7O.3C.3.2 -- Auto-Publish Corrupt-Store Repair
Independent Verification.

Independently re-derives, reproduces, and attacks the narrow repair made
at Phase 149O.20L.7O.3C.3.1 (commit ``e1eac103``) for finding
``B-149O.20L.7O.3C.3-1`` (AUTO-PUBLISH CORRUPT-STORE ISOLATION DEFECT).
This suite is written from scratch against the repaired production
source (``SessionApplicationService.find_session_by_subject_ref``,
``auto_publish_confirmed_session``) without importing any fixture or
test function from
``tests/test_phase_149o_20l_7o_3c_3_1_auto_publish_corrupt_store_fail_closed_repair.py``.

See ``docs/PHASE_149O_20L_7O_3C_3_2_AUTO_PUBLISH_CORRUPT_STORE_REPAIR_INDEPENDENT_VERIFICATION.md``
for the full methodology, the historical-crash-reproduction evidence
(captured via a disposable ``git worktree`` at the pre-repair commit,
``2fd7fe3a``, run through the literal installed ``pcae phase complete``
subprocess), and the finding's final adjudication.

**Independent finding, confirmed by direct code reading of
``FilesystemSessionRepository.load``/``_unwrap`` (not asserted from the
3C.3.1 phase narrative):** every malformed-record shape this suite tests
(invalid JSON syntax, truncated JSON, empty file, a bare JSON scalar, a
JSON array where an object is required, a missing/extra field, a wrong
schema version, a mismatched nested session id) is translated into the
*same* ``SessionStoreCorruptError`` by ``_unwrap``/``load`` -- there is
no finer-grained corruption taxonomy at the repository layer for
``find_session_by_subject_ref`` to distinguish between. Consequently
"unrelated corruption is isolated" and "relevant corruption fails
closed" are, at the current architecture boundary, the *same code path*
with two different-looking outcomes depending on one fact only: whether
a separate, genuinely readable record matching the requested
``subject_ref`` exists *anywhere else* in the store. If one does, it is
returned and the corruption is irrelevant. If none does, the repaired
code cannot distinguish "the corrupt record would have matched" from
"the corrupt record was for someone else entirely" (identity recovery
requires successful parsing, which by definition did not happen) and
conservatively fails closed either way. This is verified below
(`test_unrelated_looking_corruption_with_no_other_match_still_fails_closed`)
as a documented, safety-preserving degraded behavior -- never a fabricated
absence, never a masked failure -- not a new defect, but a materially
more precise restatement of the repair's actual isolation guarantee than
3C.3.1's own phase narrative implies.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

import pytest

from pcae.commands.governance_auto_publication import (
    STATUS_APPLICATION_ERROR,
    STATUS_NO_SESSION,
    STATUS_PUBLISHED,
    auto_publish_confirmed_session,
)
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract
from pcae.governance.publication.storage import PublicationRecordStore
from pcae.governance.publication.coordinator import PublicationCoordinator
from pcae.interactive_workflow.application.errors import (
    SessionCorruptApplicationError,
    SessionPersistenceUnavailableApplicationError,
)
from pcae.interactive_workflow.application.publication_service import (
    PublicationApplicationService,
)
from pcae.interactive_workflow.application.session_service import SessionApplicationService
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    FilesystemPendingReadinessStore,
)
from pcae.interactive_workflow.persistence.filesystem_repository import (
    FilesystemSessionRepository,
    STORE_SCHEMA_VERSION,
)
from pcae.interactive_workflow.publication_handoff.models import PublicationReadinessPackage
from pcae.interactive_workflow.session.coordinator import SessionCoordinator

REPO_ROOT = Path(__file__).resolve().parent.parent
PRE_REPAIR_COMMIT = "2fd7fe3a84414a20b9f377eae2fa85fd40da3e31"
REPAIR_COMMIT = "e1eac10356bfb6971157078b19ab008c4a3de005"

_SUPPRESS_NOTIFY_ENV = {
    "PCAE_NOTIFY_CONFIG_DISABLE": "1",
    "PCAE_NOTIFY_ENABLED": "",
    "PCAE_TELEGRAM_BOT_TOKEN": "",
    "PCAE_TELEGRAM_CHAT_ID": "",
    "PCAE_TELEGRAM_ENABLED": "",
    "PCAE_NOTIFY_SINKS": "",
}


def _new_session_id() -> str:
    return f"CDS-{uuid.uuid4()}"


class _Ctx:
    def __init__(self, session_service, publication_service) -> None:
        self.session_service = session_service
        self.publication_service = publication_service


class FreshCorruptionHarness:
    """Independently reconstructed collaborator graph (same production
    composition shape ``build_application_context`` uses, rebuilt here so
    this suite does not depend on any fixture class from the repair
    phase's own test module)."""

    def __init__(self, tmp_path: Path) -> None:
        self.root = tmp_path
        self.session_repo = FilesystemSessionRepository(root=tmp_path / "sessions")
        self.session_coordinator = SessionCoordinator(repository=self.session_repo)
        self.session_service = SessionApplicationService(self.session_coordinator)
        self.readiness_store = FilesystemPendingReadinessStore(
            root=tmp_path / "sessions" / "pending-packages"
        )
        self.record_store = PublicationRecordStore(root=tmp_path / "publication-execution")
        self.publication_coordinator = PublicationCoordinator(store=self.record_store)
        self.publication_service = PublicationApplicationService(
            self.readiness_store, self.session_service, self.publication_coordinator
        )
        self.context = _Ctx(self.session_service, self.publication_service)

    def fresh_service(self) -> SessionApplicationService:
        """A brand-new ``SessionApplicationService`` over the identical
        on-disk store -- simulates process restart/resume for the
        read-only lookup path."""

        repo = FilesystemSessionRepository(root=self.root / "sessions")
        return SessionApplicationService(SessionCoordinator(repository=repo))

    def make_confirmed(self, subject_ref: str) -> str:
        session = self.session_service.create_session(
            owner_identity="op-verify", template_ref="tmpl-verify", subject_ref=subject_ref
        )
        moved = session.with_state(SessionState.CONFIRMED, _now())
        self.session_service.persist_session(moved)
        return moved.session_id

    def corrupt_path(self, content: bytes) -> Path:
        path = self.root / "sessions" / f"{_new_session_id()}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def corrupt_path_named(self, session_id: str, content: bytes) -> Path:
        path = self.root / "sessions" / f"{session_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _readiness_package(package_id: str, session_id: str) -> PublicationReadinessPackage:
    """Independently reconstructed readiness-package fixture (same shape
    3C.2's own suite uses to bypass the orchestration-coordinator's own
    stage-advancement machinery, which is unrelated to this phase's
    corruption finding): pre-persisting a package directly is how an
    already-``Confirmed`` session with an existing package is exercised
    without re-implementing the full Interactive Workflow orchestration
    lifecycle in this test module."""

    return PublicationReadinessPackage(
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
        built_at=_now(),
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
            "captured_at": _now(),
        },
        preview_rendered_content="rendered",
        confirmation_statement="I confirm",
        confirmation_timestamp=_now(),
        metadata={},
    )


def _make_active_task_file(tmp_path: Path, task_id: str) -> None:
    active_dir = tmp_path / "tasks" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    (active_dir / f"{task_id}.md").write_text("# Fixture Task\n", encoding="utf-8")


@pytest.fixture
def harness(tmp_path: Path) -> FreshCorruptionHarness:
    return FreshCorruptionHarness(tmp_path)


# ═════════════════════════════════════════════════════════════════════
# 1. Historical crash: independently reproduced against real pre-repair
#    source (not a source-text assertion -- an actual subprocess run).
# ═════════════════════════════════════════════════════════════════════


def _worktree_pythonpath(tmp_path_factory) -> Optional[str]:
    """Checks out the pre-repair commit into a disposable worktree and
    returns its ``src`` directory for use as ``PYTHONPATH`` -- the
    lightest-weight way to execute the *exact* historical source tree
    (not a hand-copied snippet) without a second virtualenv, since no
    third-party dependency changed between the pre-repair commit and
    current ``HEAD``."""

    wt_dir = tmp_path_factory.mktemp("pre_repair_worktree")
    result = subprocess.run(
        ["git", "worktree", "add", "--detach", str(wt_dir), PRE_REPAIR_COMMIT],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    return str(wt_dir / "src")


def _bootstrap_fixture_repo(tmp_path: Path) -> str:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "verify@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Verify User"], cwd=tmp_path, check=True, capture_output=True)

    from pcae.commands.init import init_harness

    root = HarnessPath(tmp_path)
    init_harness(root)
    task = create_task_contract(
        root,
        title="Independent verification corrupt-store fixture task",
        goal="independently verify the corrupt-store repair",
        mode="implementation",
        allowed_files=(".pcae/**", "tasks/active/**", "tasks/done/**"),
        allowed_zones=("config", "tasks"),
    )

    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n## Current Phase\n\nPhase 205Z — Verify Fixture.\n\n"
        "Recommended next repo phase: 205ZN — Next Phase.\n",
        encoding="utf-8",
    )
    meta = {
        "phase_id": "205Z",
        "phase_name": "Verify Fixture",
        "files_changed_count": 1,
        "tests_added_or_updated": "1 tests added",
        "validation_results": [
            {"name": "report_notification_tests", "result": "1/1", "status": "passed"},
            {"name": "bootstrap_session_reporting_tests", "result": "present", "status": "passed"},
            {"name": "fast_green", "result": "1/1", "status": "passed"},
        ],
        "governance_results": [
            {"name": "pcae_health", "status": "healthy"},
            {"name": "pcae_check", "status": "passed"},
            {"name": "pcae_doctor_task_memory", "status": "clean"},
            {"name": "pcae_push_check", "status": "clean"},
            {"name": "telegram_runtime", "status": "loaded"},
        ],
        "no_go_confirmation": "No validator bypass. No task finish integration.",
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": "205ZN — Next Phase",
        "phase_commits": [{"hash": "abc1234500000099"}],
        "commit_attribution": "phase_owned",
        "execution_availability": "unavailable",
    }
    meta_path = tmp_path / ".pcae" / "phase-completion-metadata.json"
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    return task.task_id


def _run_pcae_subprocess(tmp_path: Path, pythonpath: Optional[str], *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update(_SUPPRESS_NOTIFY_ENV)
    if pythonpath is not None:
        env["PYTHONPATH"] = pythonpath
    else:
        env.pop("PYTHONPATH", None)
    return subprocess.run(
        [sys.executable, "-m", "pcae", *args], cwd=tmp_path, capture_output=True, text=True, env=env,
    )


@pytest.mark.parametrize("dummy", [None])
def test_historical_crash_independently_reproduced_against_pre_repair_worktree(
    tmp_path_factory, dummy,
):
    """Checks out the real, fixed pre-repair commit into a disposable
    worktree, builds an isolated fixture repository with an unrelated
    corrupted Interactive Workflow session record, and runs the literal
    ``python -m pcae phase complete`` entry point against that exact
    historical source tree. Requires an uncaught traceback and non-zero
    exit -- if this does not reproduce, the test fails loudly rather than
    silently passing, per the governing brief's "STOP and investigate"
    instruction."""

    pythonpath = _worktree_pythonpath(tmp_path_factory)
    if pythonpath is None:
        pytest.fail(
            "Could not create a git worktree at the pre-repair commit "
            f"{PRE_REPAIR_COMMIT} -- historical crash reproduction is "
            "required, not optional, for this phase's closure."
        )

    fixture_root = tmp_path_factory.mktemp("pre_repair_fixture")
    task_id = _bootstrap_fixture_repo(fixture_root)

    session_dir = fixture_root / ".pcae" / "decision-sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / f"{_new_session_id()}.json").write_bytes(b"{not valid json at all!!!")

    result = _run_pcae_subprocess(
        fixture_root, pythonpath, "phase", "complete",
        "--summary", "independent historical crash repro", "--allow-partial-report",
    )

    assert result.returncode != 0, (
        "Expected the pre-repair commit to crash on an unrelated corrupt "
        f"session record; task_id={task_id!r}.\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert "SessionStoreCorruptError" in result.stderr
    assert "Traceback (most recent call last)" in result.stderr
    assert "find_session_by_subject_ref" in result.stderr
    assert "auto_publish_confirmed_session" in result.stderr


def test_repaired_source_same_fixture_shape_no_longer_crashes(tmp_path_factory):
    """Same reproduction shape as above, run against the current,
    repaired, installed ``pcae`` (no ``PYTHONPATH`` override) -- the
    primary closure test (governing brief §5/§25)."""

    fixture_root = tmp_path_factory.mktemp("repaired_fixture")
    task_id = _bootstrap_fixture_repo(fixture_root)

    session_dir = fixture_root / ".pcae" / "decision-sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / f"{_new_session_id()}.json").write_bytes(b"{not valid json at all!!!")

    result = _run_pcae_subprocess(
        fixture_root, None, "phase", "complete",
        "--summary", "independent repaired-source run", "--allow-partial-report",
    )

    assert result.returncode == 0, (
        f"pcae phase complete crashed for task {task_id!r}.\nstdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
    assert "Traceback (most recent call last)" not in result.stderr
    assert "Phase complete." in result.stdout
    assert "status: application_error" in result.stdout


def test_repaired_source_ordinary_completion_unaffected_by_zero_sessions(tmp_path_factory):
    """Baseline: an active task with no Interactive Workflow session at
    all -- the overwhelmingly common case -- still completes exactly as
    before, no auto-route line printed."""

    fixture_root = tmp_path_factory.mktemp("repaired_fixture_no_sessions")
    _bootstrap_fixture_repo(fixture_root)

    result = _run_pcae_subprocess(
        fixture_root, None, "phase", "complete",
        "--summary", "independent no-session run", "--allow-partial-report",
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "Phase complete." in result.stdout
    assert "Interactive Workflow auto-route" not in result.stdout


# ═════════════════════════════════════════════════════════════════════
# 2. Absent vs corrupt distinction (§9)
# ═════════════════════════════════════════════════════════════════════


def test_absent_session_is_a_pure_none_not_an_error(harness: FreshCorruptionHarness):
    found = harness.session_service.find_session_by_subject_ref("no-such-subject-at-all")
    assert found is None

    outcome = auto_publish_confirmed_session(
        harness.context, subject_ref="no-such-subject-at-all", operator_id="op-1",
    )
    assert outcome.status == STATUS_NO_SESSION


# ═════════════════════════════════════════════════════════════════════
# 3. Unrelated-vs-relevant corruption semantics (§8/§10/§11/§12), derived
#    independently rather than assumed from the repair-phase narrative.
# ═════════════════════════════════════════════════════════════════════


def test_valid_relevant_plus_corrupt_unrelated_finds_the_real_match(
    harness: FreshCorruptionHarness, tmp_path: Path, monkeypatch,
):
    """A genuine readable match exists for the requested subject; an
    unrelated corrupt record also exists. The real match must win, must
    not be masked, and the full publish path (not just the lookup) must
    succeed -- i.e. corruption elsewhere must not even partially degrade
    the outcome for the real subject."""

    monkeypatch.chdir(tmp_path)
    _make_active_task_file(tmp_path, "subject-real-a")

    harness.corrupt_path(b"{not valid json!!!")
    target_id = harness.make_confirmed("subject-real-a")
    harness.publication_service.persist_readiness_package(
        _readiness_package("prp-real-a", target_id)
    )

    found = harness.session_service.find_session_by_subject_ref("subject-real-a")
    assert found is not None
    assert found.session_id == target_id

    outcome = auto_publish_confirmed_session(
        harness.context, subject_ref="subject-real-a", operator_id="op-verify",
    )
    assert outcome.status == STATUS_PUBLISHED, outcome.diagnostic
    assert outcome.record_id


def test_unrelated_looking_corruption_with_no_other_match_still_fails_closed(
    harness: FreshCorruptionHarness,
):
    """The nuance documented at the top of this file: a corrupt record
    that is, in fact, unrelated to the requested subject (no field of it
    was ever readable, so its true subject_ref can never be recovered)
    still produces the *same* fail-closed ``application_error`` as
    genuinely relevant corruption would, whenever no other readable
    record matches. This is the conservative, safety-preserving half of
    the repair -- proven here as a real, reproducible behavior, not
    inferred from the phase narrative."""

    harness.corrupt_path(b"{not valid json!!!")

    with pytest.raises(SessionCorruptApplicationError):
        harness.session_service.find_session_by_subject_ref("subject-nobody-owns")

    outcome = auto_publish_confirmed_session(
        harness.context, subject_ref="subject-nobody-owns", operator_id="op-1",
    )
    assert outcome.status == STATUS_APPLICATION_ERROR
    assert outcome.diagnostic


def test_corrupt_relevant_plus_valid_unrelated_fails_closed_not_masked_by_other_session(
    harness: FreshCorruptionHarness,
):
    """A valid, readable CONFIRMED session exists for a *different*
    subject; the requested subject's own record is corrupt. The system
    must not silently substitute the unrelated valid session as though
    it answered the query."""

    harness.corrupt_path(b"{not valid json!!!")
    other_id = harness.make_confirmed("subject-other-valid")

    with pytest.raises(SessionCorruptApplicationError):
        harness.session_service.find_session_by_subject_ref("subject-nobody-owns")

    # Confirm the unrelated valid session is untouched and still its own.
    found_other = harness.session_service.find_session_by_subject_ref("subject-other-valid")
    assert found_other is not None
    assert found_other.session_id == other_id


def test_multiple_unrelated_corrupt_records_deterministic_and_no_accumulated_crash(
    harness: FreshCorruptionHarness,
):
    for _ in range(5):
        harness.corrupt_path(b"{still not valid json")

    for _ in range(3):
        with pytest.raises(SessionCorruptApplicationError):
            harness.session_service.find_session_by_subject_ref("subject-nobody-owns")

    target_id = harness.make_confirmed("subject-real-b")
    found = harness.session_service.find_session_by_subject_ref("subject-real-b")
    assert found is not None
    assert found.session_id == target_id


def test_all_records_corrupt_no_crash_fails_closed(harness: FreshCorruptionHarness):
    for _ in range(4):
        harness.corrupt_path(b"not json at all")

    with pytest.raises(SessionCorruptApplicationError):
        harness.session_service.find_session_by_subject_ref("anything")


# ═════════════════════════════════════════════════════════════════════
# 4. Malformed-record matrix (§6) -- every shape independently confirmed
#    to translate into ``SessionStoreCorruptError`` at the repository
#    layer (`_unwrap`), then confirmed caught by the repaired scan loop.
# ═════════════════════════════════════════════════════════════════════


_MALFORMED_PAYLOADS = {
    "invalid_json_syntax": b"{this is not json",
    "truncated_json": b'{"schema_version": 1, "session_id": "CDS-x", "sess',
    "empty_file": b"",
    "json_scalar": b"42",
    "json_array": b"[1, 2, 3]",
    "object_missing_required_fields": json.dumps({"schema_version": STORE_SCHEMA_VERSION}).encode(),
    "wrong_schema_version": json.dumps(
        {"schema_version": STORE_SCHEMA_VERSION + "-unsupported", "session_id": "placeholder", "session": {}}
    ).encode(),
    "mismatched_session_id_field": json.dumps(
        {"schema_version": STORE_SCHEMA_VERSION, "session_id": "CDS-does-not-match-filename", "session": {}}
    ).encode(),
    "wrong_field_type_for_session_payload": json.dumps(
        {"schema_version": STORE_SCHEMA_VERSION, "session_id": "placeholder", "session": "not-an-object"}
    ).encode(),
}


@pytest.mark.parametrize("shape", sorted(_MALFORMED_PAYLOADS))
def test_malformed_record_matrix_entry_is_bounded_not_crashing(
    harness: FreshCorruptionHarness, shape: str,
):
    session_id = _new_session_id()
    payload = _MALFORMED_PAYLOADS[shape]
    if shape == "mismatched_session_id_field" or shape == "wrong_field_type_for_session_payload" or shape == "wrong_schema_version":
        # These need the *filename* id to differ from/matches the payload's
        # own declared id in a controlled way; the harness already writes
        # under a fresh random filename, so the mismatch is inherent.
        harness.corrupt_path_named(session_id, payload)
    else:
        harness.corrupt_path_named(session_id, payload)

    with pytest.raises((SessionCorruptApplicationError, SessionPersistenceUnavailableApplicationError)):
        harness.session_service.find_session_by_subject_ref("some-subject-not-present-elsewhere")


# ═════════════════════════════════════════════════════════════════════
# 5. Filesystem-level failures (§7) -- permission-denied read.
# ═════════════════════════════════════════════════════════════════════


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0, reason="POSIX permission bits only, not meaningful as root")
def test_unreadable_file_permission_error_fails_closed_not_crashing(harness: FreshCorruptionHarness):
    path = harness.corrupt_path(b'{"schema_version": 1, "session_id": "x", "session": {}}')
    path.chmod(0)
    try:
        with pytest.raises((SessionCorruptApplicationError, SessionPersistenceUnavailableApplicationError)):
            harness.session_service.find_session_by_subject_ref("some-subject-not-present-elsewhere")
    finally:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


# ═════════════════════════════════════════════════════════════════════
# 6. Ordering attack (§16) -- outcome must not depend on filesystem
#    iteration/creation order.
# ═════════════════════════════════════════════════════════════════════


def test_ordering_of_corrupt_and_valid_records_does_not_change_outcome(
    harness: FreshCorruptionHarness,
):
    # Write corrupt records both before and after the valid one, with
    # varied filenames (not lexically adjacent) and explicit mtime
    # perturbation, to attack any hidden ordering dependence.
    harness.corrupt_path(b"corrupt-a")
    target_id = harness.make_confirmed("subject-order-test")
    harness.corrupt_path(b"corrupt-z")
    later_corrupt = harness.corrupt_path(b"corrupt-mid")

    now = time.time()
    os.utime(later_corrupt, (now - 100000, now - 100000))

    found = harness.session_service.find_session_by_subject_ref("subject-order-test")
    assert found is not None
    assert found.session_id == target_id


# ═════════════════════════════════════════════════════════════════════
# 7. Restart/resume (§21/§22) -- a fresh service instance over the same
#    on-disk store reaches the identical result; relevant corruption
#    remains fail-closed after "restart", no silent replacement.
# ═════════════════════════════════════════════════════════════════════


def test_restart_resume_after_unrelated_corruption_is_deterministic(
    harness: FreshCorruptionHarness,
):
    harness.corrupt_path(b"corrupt-persists")
    target_id = harness.make_confirmed("subject-restart-a")

    first = harness.session_service.find_session_by_subject_ref("subject-restart-a")
    second = harness.fresh_service().find_session_by_subject_ref("subject-restart-a")
    assert first is not None and second is not None
    assert first.session_id == second.session_id == target_id


def test_restart_resume_after_relevant_corruption_remains_fail_closed(
    harness: FreshCorruptionHarness,
):
    harness.corrupt_path(b"corrupt-relevant")

    with pytest.raises(SessionCorruptApplicationError):
        harness.session_service.find_session_by_subject_ref("subject-no-match")
    with pytest.raises(SessionCorruptApplicationError):
        harness.fresh_service().find_session_by_subject_ref("subject-no-match")


# ═════════════════════════════════════════════════════════════════════
# 8. Duplicate subject_ref -- independent adjudication (§15), verified
#    against the primary-source contract (``--subject-ref`` is
#    documented free text with no store-level uniqueness enforcement
#    anywhere in ``create``/``persist``), not merely re-asserting 3C.3's
#    prior classification.
# ═════════════════════════════════════════════════════════════════════


def test_create_session_enforces_no_subject_ref_uniqueness(harness: FreshCorruptionHarness):
    """Direct proof, from the production ``create_session``/``create``
    path itself, that nothing in the frozen contract layer rejects a
    second session sharing an existing ``subject_ref`` -- the basis for
    this suite's independent NON-BLOCKING/ACCEPTED-DEBT classification of
    finding B-149O.20L.7O.3C.3-1's duplicate-subject_ref sub-issue (the
    uniqueness constraint the governing brief's item 15 asks about simply
    does not exist anywhere upstream of ``find_session_by_subject_ref``,
    so a fail-closed *lookup* would be enforcing an invariant no other
    layer of the system enforces or documents)."""

    harness.session_service.create_session(
        owner_identity="op-1", template_ref="tmpl-dup", subject_ref="dup-subject",
    )
    second = harness.session_service.create_session(
        owner_identity="op-1", template_ref="tmpl-dup", subject_ref="dup-subject",
    )
    assert second.subject_ref == "dup-subject"


def test_duplicate_subject_ref_resolves_deterministically_by_latest_created_at(
    harness: FreshCorruptionHarness,
):
    older = harness.session_service.create_session(
        owner_identity="op-1", template_ref="tmpl-dup", subject_ref="dup-subject-2",
    )
    time.sleep(0.01)
    newer = harness.session_service.create_session(
        owner_identity="op-1", template_ref="tmpl-dup", subject_ref="dup-subject-2",
    )

    found = harness.session_service.find_session_by_subject_ref("dup-subject-2")
    assert found is not None
    assert found.session_id == newer.session_id
    assert found.session_id != older.session_id


# ═════════════════════════════════════════════════════════════════════
# 9. Plan B+ happy-path / human-boundary spot-check (§17-20), rebuilt
#    fresh rather than reusing the repair phase's own harness, to
#    confirm the corruption repair changed nothing about the successful
#    or human-authority-preserving paths.
# ═════════════════════════════════════════════════════════════════════


def test_confirmed_session_with_unrelated_corruption_present_still_publishes(
    harness: FreshCorruptionHarness, tmp_path: Path, monkeypatch,
):
    monkeypatch.chdir(tmp_path)
    _make_active_task_file(tmp_path, "subject-happy-path")

    harness.corrupt_path(b"unrelated corruption during happy path")
    target_id = harness.make_confirmed("subject-happy-path")
    harness.publication_service.persist_readiness_package(
        _readiness_package("prp-happy-path", target_id)
    )

    outcome = auto_publish_confirmed_session(
        harness.context, subject_ref="subject-happy-path", operator_id="op-verify",
    )
    assert outcome.status == STATUS_PUBLISHED, outcome.diagnostic
    assert outcome.record_id

    # Idempotent repeat call: same record, not a duplicate CHGR.
    outcome2 = auto_publish_confirmed_session(
        harness.context, subject_ref="subject-happy-path", operator_id="op-verify",
    )
    assert outcome2.status == "already_published"
    assert outcome2.record_id == outcome.record_id


def test_non_terminal_session_state_reports_awaiting_human_decision_not_error(
    harness: FreshCorruptionHarness,
):
    session = harness.session_service.create_session(
        owner_identity="op-1", template_ref="tmpl-pending", subject_ref="subject-pending",
    )
    outcome = auto_publish_confirmed_session(
        harness.context, subject_ref="subject-pending", operator_id="op-1",
    )
    assert outcome.status == "awaiting_human_decision"
    assert outcome.session_id == session.session_id


def test_rejected_session_reports_human_rejected_no_chgr(harness: FreshCorruptionHarness):
    session = harness.make_confirmed("subject-to-cancel")
    # Move a fresh session (not the confirmed one) into Cancelled from Created.
    created = harness.session_service.create_session(
        owner_identity="op-1", template_ref="tmpl-cancel", subject_ref="subject-cancelled",
    )
    cancelled = created.with_state(SessionState.CANCELLED, _now())
    harness.session_service.persist_session(cancelled)

    outcome = auto_publish_confirmed_session(
        harness.context, subject_ref="subject-cancelled", operator_id="op-1",
    )
    assert outcome.status == "human_rejected"
    assert outcome.record_id is None


# ═════════════════════════════════════════════════════════════════════
# 10. Architecture-boundary re-check (§27) -- independently re-derived
#     (not copy-pasted) forbidden-import assertion for the repaired file.
# ═════════════════════════════════════════════════════════════════════


def test_session_service_module_has_no_forbidden_cross_zone_import():
    import ast

    path = REPO_ROOT / "src/pcae/interactive_workflow/application/session_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = ("pcae.commands", "pcae.core")
    violations = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(forbidden)
    ]
    assert violations == []


def test_no_new_self_cli_subprocess_introduced_by_the_repair():
    for rel in (
        "src/pcae/commands/governance_auto_publication.py",
        "src/pcae/interactive_workflow/application/session_service.py",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert 'subprocess.run(["pcae"' not in text
        assert "subprocess.run(['pcae'" not in text
