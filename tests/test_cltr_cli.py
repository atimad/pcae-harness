"""Phase 135K — read-only `pcae cltr shadow ...` CLI tests."""

from __future__ import annotations

import json

import pytest

from pcae.cli import build_parser
from pcae.cltr.enums import CertificationState, LifecycleState, NotificationState, TransitionType
from pcae.cltr.models import CommitOwnershipEntry, EvidenceReference, ShadowTransitionInput
from pcae.cltr.shadow import observe_finalized_transition


@pytest.fixture()
def isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _publish_one():
    inp = ShadowTransitionInput(
        entry_point="phase_complete",
        phase_id="135K-CLI",
        transition_type=TransitionType.CLOSE_SUCCESS,
        intended_lifecycle_state=LifecycleState.TERMINAL_SUCCESS,
        source_revision="abc123",
        repository_identity="repo",
        branch_identity="main",
        report_id="r1", report_digest="a" * 64,
        metadata_id="m1", metadata_digest="b" * 64,
        snapshot_id="s1", snapshot_digest="c" * 64,
        promotion_id="p1",
        notification_ids=("n1",),
        notification_state=NotificationState.CONFIRMED,
        receipt_id="rcpt1",
        phase_commit_ownership=(
            CommitOwnershipEntry(commit_hash="deadbeef", repository_identity="repo", branch_identity="main", certification_state=CertificationState.UNVERIFIABLE),
        ),
        evidence_refs=(EvidenceReference(evidence_id="e1", evidence_kind="test_suite", reference="pytest::fast_green"),),
    )
    # Uses the default shadow root (".pcae/cltr-shadow", relative to cwd) so
    # the CLI handlers under test (which also use the default) see it.
    return observe_finalized_transition(inp)


def test_parser_registers_cltr_shadow_commands():
    parser = build_parser()
    args = parser.parse_args(["cltr", "shadow", "status"])
    assert args.command == "cltr"
    assert args.cltr_command == "shadow"
    assert args.cltr_shadow_command == "status"


def test_status_json(capsys, monkeypatch, isolated_cwd):
    from pcae.commands.cltr_shadow import run_cltr_shadow_status

    monkeypatch.delenv("PCAE_CLTR_SHADOW_ENABLED", raising=False)
    args = type("Args", (), {"json": True})()
    rc = run_cltr_shadow_status(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["enabled"] is False
    assert payload["shadow_mode"] is True
    assert payload["authoritative"] is False
    assert payload["mutation"] == "none"


def test_show_latest_and_list_and_verify(isolated_cwd, capsys):
    from pcae.commands import cltr_shadow

    result = _publish_one()
    assert result.status == "published"

    args = type("Args", (), {"latest": True, "phase_id": None, "json": True})()
    rc = cltr_shadow.run_cltr_shadow_show(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["found"] is True
    assert payload["record"]["phase_id"] == "135K-CLI"
    assert payload["shadow_mode"] is True
    assert payload["authoritative"] is False

    verify_args = type("Args", (), {"latest": True, "json": True})()
    rc = cltr_shadow.run_cltr_shadow_verify(verify_args)
    assert rc == 0
    verify_payload = json.loads(capsys.readouterr().out)
    assert verify_payload["verified"] is True

    list_args = type("Args", (), {"limit": None, "json": True})()
    rc = cltr_shadow.run_cltr_shadow_list(list_args)
    assert rc == 0
    list_payload = json.loads(capsys.readouterr().out)
    assert "135K-CLI" in list_payload["generations"]


def test_reconcile_is_read_only_and_never_mutates(isolated_cwd, capsys):
    from pcae.commands import cltr_shadow

    _publish_one()
    shadow_root = isolated_cwd / ".pcae" / "cltr-shadow"
    before = sorted(p.name for p in shadow_root.rglob("*") if p.is_file())

    args = type("Args", (), {"phase_id": "135K-CLI", "json": True})()
    rc = cltr_shadow.run_cltr_shadow_reconcile(args)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["mutation"] == "none"
    assert payload["blockers"] == []

    after = sorted(p.name for p in shadow_root.rglob("*") if p.is_file())
    assert before == after


def test_reconcile_missing_phase_reports_blocker_not_crash(isolated_cwd, capsys):
    from pcae.commands import cltr_shadow

    args = type("Args", (), {"phase_id": "NO-SUCH-PHASE", "json": True})()
    rc = cltr_shadow.run_cltr_shadow_reconcile(args)
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["generation_found"] is False
    assert payload["blockers"]


def test_no_subprocess_no_network_in_cltr_package():
    import ast
    from pathlib import Path

    package_root = Path(__file__).resolve().parent.parent / "src" / "pcae" / "cltr"
    forbidden_modules = {"subprocess", "socket", "urllib", "http", "requests"}
    for py_file in package_root.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = {node.module.split(".")[0]}
            else:
                continue
            assert not (names & forbidden_modules), f"{py_file} imports forbidden module(s): {names & forbidden_modules}"
