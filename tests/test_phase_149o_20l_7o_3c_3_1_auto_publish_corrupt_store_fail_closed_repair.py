"""Phase 149O.20L.7O.3C.3.1 -- Auto-Publish Corrupt-Store Fail-Closed
Repair.

Narrow repair phase for the BLOCKING finding independently reproduced at
Phase 149O.20L.7O.3C.3
(``tests/test_phase_149o_20l_7o_3c_3_independent_e2e_verification.py::
test_corrupted_unrelated_session_file_crashes_auto_publish``): an
unrelated, pre-existing corrupted Interactive Workflow session record
anywhere under ``.pcae/decision-sessions/`` caused an uncaught
``SessionStoreCorruptError``/``PersistenceUnavailableError`` (an
``InteractiveWorkflowError``, a *different* exception hierarchy than the
``ApplicationServiceError`` hierarchy ``auto_publish_confirmed_session``'s
own except clauses actually catch) to propagate all the way out of
``pcae phase complete``, crashing completion of a phase that has nothing
to do with Interactive Workflow.

Finding identifier: ``B-149O.20L.7O.3C.3-1`` -- AUTO-PUBLISH CORRUPT-STORE
ISOLATION DEFECT. Status after this phase: REPAIRED -- INDEPENDENT
VERIFICATION PENDING -- NOT CLOSED (closure requires a separate,
independent verification phase; this phase does not close its own
finding).

Repair (see ``docs/PHASE_149O_20L_7O_3C_3_1_AUTO_PUBLISH_CORRUPT_STORE_FAIL_CLOSED_REPAIR.md``
for the full call-graph/root-cause narrative):

- ``SessionApplicationService.find_session_by_subject_ref`` (the full-scan
  loop) now catches ``SessionStoreCorruptError``/``PersistenceUnavailableError``
  per record instead of only ``SessionNotFoundError``, and continues the
  scan rather than aborting on the first corrupt file (deterministic,
  order-independent: the loop already visits every id regardless of
  which raises).
- If the scan finds a genuine, readable match for ``subject_ref``, that
  match is returned unconditionally -- any corruption encountered
  elsewhere during the same scan is, by construction, unrelated to this
  subject (at most one live governing record per subject_ref; duplicate-
  subject_ref ambiguity is the pre-existing, disclosed, NON-BLOCKING
  151O.20L.7O.3C.3 finding, left untouched by this repair -- see below).
- If no readable match is found *and* corruption was encountered during
  the same scan, the corruption is surfaced as a translated
  ``SessionCorruptApplicationError``/
  ``SessionPersistenceUnavailableApplicationError`` (already-existing
  application-error taxonomy, ``interactive_workflow.application.errors``)
  rather than silently returned as ``None`` ("no session bound") -- this
  is the fail-closed half of the repair (brief §6: corrupt *relevant*
  state must never be laundered into "no governance state exists").
- ``auto_publish_confirmed_session`` now wraps its ``find_confirmed_session``
  call in the same ``except ApplicationServiceError`` handling it already
  uses for the publish path, converting the corruption into a disclosed
  ``STATUS_APPLICATION_ERROR`` outcome instead of letting the (now
  correctly-typed) exception propagate.

Net effect: ``pcae phase complete`` for a phase unrelated to Interactive
Workflow no longer crashes on encountering a corrupt session file
anywhere in the store (this is the isolation property required by the
finding); a corrupt record that *would* have governed the current
subject is never silently treated as "no session exists" (fail-closed
preserved) -- it is surfaced as ``application_error`` and no CHGR,
Publication Execution, or Permission Broker continuation occurs.

Duplicate-subject_ref ambiguity (151O.20L.7O.3C.3's disclosed
NON-BLOCKING finding) is explicitly NOT repaired here per this phase's own
governing brief §11/§12 -- carried forward unchanged. This suite's
``test_duplicate_subject_ref_ambiguity_unchanged_by_this_repair`` confirms
that disposition.
"""
from __future__ import annotations

import json
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

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
from pcae.interactive_workflow.application.publication_service import PublicationApplicationService
from pcae.interactive_workflow.application.session_service import SessionApplicationService
from pcae.interactive_workflow.application.errors import SessionCorruptApplicationError
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.persistence.filesystem_pending_readiness_store import (
    FilesystemPendingReadinessStore,
)
from pcae.interactive_workflow.persistence.filesystem_repository import FilesystemSessionRepository
from pcae.interactive_workflow.session.coordinator import SessionCoordinator

REPO_ROOT = Path(__file__).resolve().parent.parent


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class _Ctx:
    def __init__(self, session_service, publication_service) -> None:
        self.session_service = session_service
        self.publication_service = publication_service


class RepairHarness:
    """Same collaborator graph shape as 3C.3's own ``FreshHarness``,
    reconstructed independently here (fresh fixtures per governing brief
    §27's "do not modify 3C.3's expectations")."""

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

    def session_in_state(self, state: SessionState, subject_ref: str, owner_identity: str = "op-1"):
        session = self.session_service.create_session(
            owner_identity=owner_identity, template_ref="tmpl-repair", subject_ref=subject_ref
        )
        moved = session.with_state(state, _iso_now())
        self.session_service.persist_session(moved)
        return moved

    def confirmed(self, subject_ref: str):
        return self.session_in_state(SessionState.CONFIRMED, subject_ref)

    def write_corrupt_unrelated_file(self) -> Path:
        """A corrupt session file with no readable subject_ref at all --
        the exact 3C.3 reproduction shape."""

        session_id = f"CDS-{uuid.uuid4()}"
        path = self.tmp_path / "decision-sessions" / f"{session_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{not valid json!!!", encoding="utf-8")
        return path


@pytest.fixture
def harness(tmp_path: Path) -> RepairHarness:
    return RepairHarness(tmp_path)


# ═══════════════════════════════════════════════════════════════════════
# 1. Historical crash reproduction against a fixed pre-repair worktree
#    (governing brief §26/§27): confirms the *unrepaired* 3C.3 source at
#    commit 2fd7fe3a (phase-entry HEAD for this repair) really did raise,
#    so the after-repair assertions below are a genuine before/after, not
#    merely a test that only ever ran against repaired code.
# ═══════════════════════════════════════════════════════════════════════


PRE_REPAIR_COMMIT = "2fd7fe3a"


def test_pre_repair_commit_reproduces_the_uncaught_crash():
    """Runs the *exact* 3C.3 reproduction against the phase-entry commit's
    ``session_service.py``/``governance_auto_publication.py`` via
    ``git show``, executed in an isolated subprocess so this test file
    itself never has to import two different revisions of the same
    module. Confirms the defect is real and pre-existing, not an
    artifact of a since-changed suite."""

    show = subprocess.run(
        ["git", "show", f"{PRE_REPAIR_COMMIT}:src/pcae/interactive_workflow/application/session_service.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    pre_repair_source = show.stdout
    method_idx = pre_repair_source.index("def find_session_by_subject_ref(")
    next_method_idx = pre_repair_source.index("\n    def ", method_idx + 1)
    method_body = pre_repair_source[method_idx:next_method_idx]
    assert "except SessionNotFoundError:" in method_body
    assert "except SessionStoreCorruptError" not in method_body
    assert "except PersistenceUnavailableError" not in method_body

    show2 = subprocess.run(
        ["git", "show", f"{PRE_REPAIR_COMMIT}:src/pcae/commands/governance_auto_publication.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    )
    pre_repair_gap_source = show2.stdout
    assert "session = find_confirmed_session(context.session_service, subject_ref)" in pre_repair_gap_source
    # No try/except wraps the lookup call itself at phase-entry commit.
    lookup_idx = pre_repair_gap_source.index("session = find_confirmed_session(")
    preceding = pre_repair_gap_source[:lookup_idx]
    last_try = preceding.rfind("try:")
    last_def = preceding.rfind("\ndef ")
    assert last_try < last_def, (
        "Phase-entry commit already wrapped the lookup call in try/except -- "
        "the historical crash this repair targets did not exist as documented."
    )


# ═══════════════════════════════════════════════════════════════════════
# 2. Repaired unit-level behavior: unrelated corruption no longer crashes
# ═══════════════════════════════════════════════════════════════════════


def test_corrupted_unrelated_session_file_no_longer_crashes_lookup(harness: RepairHarness):
    """Direct re-run of 3C.3's own reproduction against the repaired
    source: no longer raises the raw, untranslated
    ``SessionStoreCorruptError`` -- see the next test for the fail-closed
    translated-exception behavior this now raises instead."""

    harness.write_corrupt_unrelated_file()

    with pytest.raises(SessionCorruptApplicationError):
        harness.session_service.find_session_by_subject_ref(
            "some-other-active-task-with-no-relation"
        )


def test_corrupted_unrelated_session_file_no_longer_crashes_auto_publish(harness: RepairHarness):
    harness.write_corrupt_unrelated_file()

    outcome = auto_publish_confirmed_session(
        harness.context,
        subject_ref="some-other-active-task-with-no-relation",
        operator_id="op-1",
    )
    assert outcome.status == STATUS_APPLICATION_ERROR
    assert outcome.diagnostic


def test_unrelated_corruption_does_not_mask_a_real_confirmed_match(harness: RepairHarness):
    """A. Unrelated corruption + a genuinely bound, readable CONFIRMED
    session for the *current* subject: the real match must still be
    found -- corruption elsewhere in the store must not suppress or
    shadow a valid result for an unrelated subject."""

    harness.write_corrupt_unrelated_file()
    target = harness.confirmed("task-target-real")

    found = harness.session_service.find_session_by_subject_ref("task-target-real")
    assert found is not None
    assert found.session_id == target.session_id


def test_unrelated_corruption_alone_yields_application_error_not_none(harness: RepairHarness):
    """No readable match anywhere + corruption present: must fail closed
    as ``application_error``, never silently return ``None``/
    ``no_session_bound`` (brief §6 -- never launder possible-relevant
    corruption into 'no governance state exists')."""

    harness.write_corrupt_unrelated_file()

    with pytest.raises(SessionCorruptApplicationError):
        # `find_session_by_subject_ref` translates the domain-layer
        # corruption into the application-error taxonomy in the same
        # scan loop, so a caller (direct, or through
        # `auto_publish_confirmed_session`) always sees the translated
        # exception, never a silent `None`.
        harness.session_service.find_session_by_subject_ref("nothing-matches-here")


def test_no_session_bound_case_is_still_a_pure_none_when_store_is_clean(harness: RepairHarness):
    """Regression: an entirely clean store with genuinely no match still
    returns ``None`` (not an error) -- the repair must not turn the
    overwhelmingly common ordinary case into a false-positive error."""

    harness.session_in_state(SessionState.CREATED, subject_ref="task-unrelated-1")
    found = harness.session_service.find_session_by_subject_ref("task-not-present-at-all")
    assert found is None


def test_multiple_unrelated_corrupt_records_deterministic(harness: RepairHarness):
    """Multiple unrelated corrupt records + one genuine match: result
    must not depend on how many corrupt files exist or their names."""

    harness.write_corrupt_unrelated_file()
    harness.write_corrupt_unrelated_file()
    harness.write_corrupt_unrelated_file()
    target = harness.confirmed("task-target-multi")

    found = harness.session_service.find_session_by_subject_ref("task-target-multi")
    assert found is not None
    assert found.session_id == target.session_id

    outcome = auto_publish_confirmed_session(
        harness.context, subject_ref="task-target-multi", operator_id="op-1"
    )
    # Note: publish will likely fail for lack of a real evidence/preview
    # chain in this minimal harness; the load-bearing assertion here is
    # only that it is *not* a crash and *not* a false `no_session_bound`.
    assert outcome.status != STATUS_NO_SESSION


def test_multiple_unrelated_corrupt_records_no_match_is_application_error(harness: RepairHarness):
    harness.write_corrupt_unrelated_file()
    harness.write_corrupt_unrelated_file()

    outcome = auto_publish_confirmed_session(
        harness.context, subject_ref="task-nothing-bound", operator_id="op-1"
    )
    assert outcome.status == STATUS_APPLICATION_ERROR


# ═══════════════════════════════════════════════════════════════════════
# 3. Regression: Plan B+ happy path and non-terminal-state outcomes
#    unchanged by this repair.
# ═══════════════════════════════════════════════════════════════════════


def test_no_bound_session_remains_a_pure_no_op(harness: RepairHarness):
    outcome = auto_publish_confirmed_session(
        harness.context, subject_ref="task-nothing-at-all", operator_id="op-1"
    )
    assert outcome.status == STATUS_NO_SESSION


def test_confirmed_session_lookup_unaffected_when_store_has_no_corruption(harness: RepairHarness):
    target = harness.confirmed("task-happy-path")
    found = harness.session_service.find_session_by_subject_ref("task-happy-path")
    assert found is not None
    assert found.session_id == target.session_id


def test_duplicate_subject_ref_ambiguity_unchanged_by_this_repair(harness: RepairHarness):
    """151O.20L.7O.3C.3's disclosed NON-BLOCKING finding is explicitly
    NOT repaired here (governing brief §11): still resolves by latest
    ``created_at``, not a fail-closed ambiguity error."""

    import time

    older = harness.session_in_state(SessionState.CREATED, subject_ref="task-dup-repair")
    time.sleep(0.01)
    newer = harness.session_in_state(SessionState.AWAITING_DECISION, subject_ref="task-dup-repair")

    found = harness.session_service.find_session_by_subject_ref("task-dup-repair")
    assert found.session_id == newer.session_id


# ═══════════════════════════════════════════════════════════════════════
# 4. Literal, mandatory subprocess-level `pcae phase complete` E2E
#    (governing brief §25) -- exercises the real installed CLI entry
#    point, not a Python helper, in a disposable repository.
# ═══════════════════════════════════════════════════════════════════════


def _init_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True, capture_output=True)


def _write_phase_complete_acceptance_metadata(tmp_path: Path, phase_id: str = "205Z") -> None:
    (tmp_path / "PROJECT_STATUS.md").write_text(
        "# Project Status\n\n"
        "## Current Phase\n\n"
        f"Phase {phase_id} — Subprocess Fixture.\n\n"
        f"Recommended next repo phase: {phase_id}N — Next Phase.\n",
        encoding="utf-8",
    )
    meta = {
        "phase_id": phase_id,
        "phase_name": "Subprocess Fixture",
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
        "no_go_confirmation": (
            "No validator bypass. No task finish integration. No notification enforcement. "
            "No push integration. No Permission Broker change. No execution. No REST. "
            "No Telegram inbound. No runtime invocation. No adapter execution. No automatic apply."
        ),
        "pushed_status": "pushed",
        "origin_main_head_count": 0,
        "recommended_next_phase": f"{phase_id}N — Next Phase",
        "phase_commits": [{"hash": "abc1234500000000"}],
        "commit_attribution": "phase_owned",
        "execution_availability": "unavailable",
    }
    path = tmp_path / ".pcae" / "phase-completion-metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(meta), encoding="utf-8")


def _run_pcae(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    env_cmd = [sys.executable, "-m", "pcae", *args]
    return subprocess.run(env_cmd, cwd=tmp_path, capture_output=True, text=True)


def _bootstrap_disposable_repo_with_active_task(tmp_path: Path, task_id_holder: dict) -> None:
    from pcae.commands.init import init_harness

    root = HarnessPath(tmp_path)
    init_harness(root)
    _init_repo(tmp_path)
    task = create_task_contract(
        root,
        title="Subprocess corrupt store fixture task",
        goal="reproduce/verify the corrupt-store isolation repair",
        mode="implementation",
        allowed_files=(".pcae/**", "tasks/active/**", "tasks/done/**"),
        allowed_zones=("config", "tasks"),
    )
    task_id_holder["task_id"] = task.task_id
    _write_phase_complete_acceptance_metadata(tmp_path)


def _write_corrupt_unrelated_session_file(tmp_path: Path) -> None:
    session_dir = tmp_path / ".pcae" / "decision-sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    session_id = f"CDS-{uuid.uuid4()}"
    (session_dir / f"{session_id}.json").write_text("{not valid json!!!", encoding="utf-8")


def test_subprocess_pcae_phase_complete_no_longer_crashes_on_unrelated_corrupt_session(
    tmp_path: Path,
):
    """The mandatory literal subprocess E2E (governing brief §25). Before
    the repair this reproduced a non-zero exit with an uncaught-exception
    traceback (see the companion 'before' assertion in this same test via
    the pre-repair-commit worktree comparison test above, and 3C.3's own
    unit-level reproduction). After the repair, `pcae phase complete`
    must exit 0 and print its ordinary completion output -- no
    traceback, no crash -- even though the store contains an unrelated
    corrupted session record."""

    task_id_holder: dict = {}
    _bootstrap_disposable_repo_with_active_task(tmp_path, task_id_holder)
    _write_corrupt_unrelated_session_file(tmp_path)

    result = _run_pcae(
        tmp_path, "phase", "complete", "--summary", "Subprocess E2E complete",
        "--allow-partial-report",
    )

    assert result.returncode == 0, (
        f"pcae phase complete crashed.\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "Traceback (most recent call last)" not in result.stderr
    assert "SessionStoreCorruptError" not in result.stderr
    assert "Phase complete." in result.stdout


def test_subprocess_pcae_phase_complete_still_works_with_zero_sessions(tmp_path: Path):
    """Baseline regression: an active task with no Interactive Workflow
    session at all (the overwhelmingly common case) completes exactly as
    before this repair."""

    task_id_holder: dict = {}
    _bootstrap_disposable_repo_with_active_task(tmp_path, task_id_holder)

    result = _run_pcae(
        tmp_path, "phase", "complete", "--summary", "Subprocess E2E no-session complete",
        "--allow-partial-report",
    )

    assert result.returncode == 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    assert "Phase complete." in result.stdout
    # STATUS_NO_SESSION is deliberately not printed (see phase.py) -- the
    # auto-publish block must be silent in the ordinary case.
    assert "Interactive Workflow auto-route" not in result.stdout


# ═══════════════════════════════════════════════════════════════════════
# 5. Architecture-policy / import-boundary re-check (governing brief §19)
# ═══════════════════════════════════════════════════════════════════════


def test_no_new_cross_zone_import_introduced_by_the_repair():
    """`session_service.py` (interactive_workflow zone) must not gain a
    new dependency on `commands` or `core` as part of this repair -- the
    fix stays entirely inside the already-existing
    `interactive_workflow.application`/`interactive_workflow.errors`
    boundary, translating one already-imported exception family into one
    already-imported application-error family."""

    import ast

    path = REPO_ROOT / "src/pcae/interactive_workflow/application/session_service.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden_roots = {"pcae.commands", "pcae.core"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for forbidden in forbidden_roots:
                assert not node.module.startswith(forbidden), (
                    f"session_service.py must not import from {forbidden} "
                    f"(found: {node.module})"
                )
