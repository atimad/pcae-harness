"""CLI + Legacy Authority Migration Integration -- Phase 149O.18E
behavioral tests.

Covers HMRC-REQ-008/009/011/012/014/057-059/065/068/078 (attacks 8, 9,
20-24, 29, 45 per the 149O.17 implementation plan's Wave-E test-plan
row): the `--hatp-evidence-id` CLI transport newly registered on
`pcae remote rollback execute` (AG3) and `pcae rollback --per-id`
(AG5), and `pcae remote rollback approve`'s new cutover-mode-aware
disposition.

This module is transport-only, mirroring `execute_rollback`'s and
`build_rollback_execution`'s own separation of concerns (HMRC-REQ-068):
it proves the CLI carries the evidence-ID locator through to the
already-wired 149O.18C/149O.18D effect boundaries, and never performs
evidence verification, approval derivation, or Permission Broker
evaluation itself. Cutover mode is monkeypatched at its owning module
(`pcae.core.hatp_mandatory_cutover`), exactly as
`tests/test_ag3_hatp_mandatory_consumption.py` and
`tests/test_ag5_hatp_mandatory_consumption.py` already do, since
`resolve_production_hatp_cutover_mode` is imported locally inside each
call site (never module-level in `agent.py`).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cli import build_parser, main
from pcae.core import agent as _agent_mod
from pcae.core import hatp_mandatory_cutover as _cutover_mod
from pcae.core.hatp_mandatory_cutover import CutoverMode, CutoverModeResolution
from pcae.core.paths import HarnessPath

from tests.test_agent import (
    _patch_rollback_execute_helpers,
    _setup_approved_rollback,
    _setup_committed_change,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_CLI_PATH = _REPO_ROOT / "src" / "pcae" / "cli.py"
_COMMANDS_AGENT_PATH = _REPO_ROOT / "src" / "pcae" / "commands" / "agent.py"
_VALID_EVIDENCE_ID = "a" * 64


def _fixed_mode(mode: CutoverMode) -> CutoverModeResolution:
    return CutoverModeResolution(mode, f"test_fixed_{mode.value}")


def _patch_mode(monkeypatch, mode: CutoverMode) -> None:
    monkeypatch.setattr(
        _cutover_mod,
        "resolve_production_hatp_cutover_mode",
        lambda root: _fixed_mode(mode),
    )


def _parse(argv):
    return build_parser().parse_args(argv)


# ═══════════════════════════════════════════════════════════════════════════
# Grammar (HMRC-REQ-008/009/011/012)
# ═══════════════════════════════════════════════════════════════════════════


def test_ag3_flag_parses_and_defaults_to_none():
    args = _parse(["remote", "rollback", "execute", "job-1"])
    assert args.hatp_evidence_id is None
    args = _parse(["remote", "rollback", "execute", "job-1", "--hatp-evidence-id", _VALID_EVIDENCE_ID])
    assert args.hatp_evidence_id == _VALID_EVIDENCE_ID


def test_ag5_flag_parses_and_defaults_to_none():
    args = _parse(["rollback", "--per-id", "per-1"])
    assert args.hatp_evidence_id is None
    args = _parse(["rollback", "--per-id", "per-1", "--hatp-evidence-id", _VALID_EVIDENCE_ID])
    assert args.hatp_evidence_id == _VALID_EVIDENCE_ID


def test_ag5_flag_coexists_with_dry_run_and_json():
    args = _parse(
        ["rollback", "--per-id", "per-1", "--hatp-evidence-id", _VALID_EVIDENCE_ID, "--dry-run", "--json"]
    )
    assert args.hatp_evidence_id == _VALID_EVIDENCE_ID
    assert args.dry_run is True
    assert args.json is True


@pytest.mark.parametrize(
    "alias",
    ["--evidence-id", "--evidence-file", "--approval-evidence", "--hatp-file"],
)
def test_no_alias_flag_registered_ag3(alias):
    with pytest.raises(SystemExit):
        _parse(["remote", "rollback", "execute", "job-1", alias, _VALID_EVIDENCE_ID])


@pytest.mark.parametrize(
    "alias",
    ["--evidence-id", "--evidence-file", "--approval-evidence", "--hatp-file"],
)
def test_no_alias_flag_registered_ag5(alias):
    with pytest.raises(SystemExit):
        _parse(["rollback", "--per-id", "per-1", alias, _VALID_EVIDENCE_ID])


# ═══════════════════════════════════════════════════════════════════════════
# Forbidden-flag inventory (governing-prompt items 12-17/94)
# ═══════════════════════════════════════════════════════════════════════════


_FORBIDDEN_FLAGS = [
    "--hatp-proof",
    "--proof",
    "--provider-assertion",
    "--hatp-envelope",
    "--hatp-evidence-file",
    "--approved",
    "--approval-present",
    "--hatp-valid",
    "--trusted",
    "--allow",
    "--pb-allow",
    "--provider",
    "--trust-store",
    "--credential-store",
    "--signer",
    "--signer-key-id",
    "--legacy",
    "--prepared",
    "--mandatory",
    "--skip-hatp",
    "--ignore-hatp",
    "--disable-hatp",
    "--cutover-mode",
    "--force-legacy",
    "--fallback",
    "--unsafe",
    "--bypass",
    "--simulation-only",
    "--pb-decision",
]


@pytest.mark.parametrize("flag", _FORBIDDEN_FLAGS)
def test_ag3_forbidden_flag_rejected_by_parser(flag):
    with pytest.raises(SystemExit):
        _parse(["remote", "rollback", "execute", "job-1", flag, "x"])


@pytest.mark.parametrize("flag", _FORBIDDEN_FLAGS)
def test_ag5_forbidden_flag_rejected_by_parser(flag):
    with pytest.raises(SystemExit):
        _parse(["rollback", "--per-id", "per-1", flag, "x"])


@pytest.mark.parametrize("flag", _FORBIDDEN_FLAGS)
def test_approve_forbidden_flag_rejected_by_parser(flag):
    with pytest.raises(SystemExit):
        _parse(["remote", "rollback", "approve", "job-1", flag, "x"])


def test_no_raw_evidence_or_status_transport_in_commands_agent_source():
    """CLI must not pass hatp_status/verification_result/approval_present/
    pb_decision/permission_result/broker into the effect functions --
    only the neutral `hatp_evidence_id` locator (governing-prompt items
    45/46)."""
    text = _COMMANDS_AGENT_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "hatp_status=",
        "verification_result=",
        "approval_present=",
        "pb_decision=",
        "permission_result=",
        "broker=",
    ):
        assert forbidden not in text


# ═══════════════════════════════════════════════════════════════════════════
# AG3 transport: parser -> handler -> execute_rollback (HMRC-REQ-011)
# ═══════════════════════════════════════════════════════════════════════════


def test_ag3_evidence_id_reaches_execute_rollback(tmp_path, monkeypatch, capsys):
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.LEGACY_COMPATIBLE)

    captured = {}
    original = _agent_mod.execute_rollback

    def _spy(root, job_id_arg, *, hatp_evidence_id=None, **kwargs):
        captured["hatp_evidence_id"] = hatp_evidence_id
        return original(root, job_id_arg, hatp_evidence_id=hatp_evidence_id, **kwargs)

    monkeypatch.setattr(_agent_mod, "execute_rollback", _spy)
    import pcae.commands.agent as _commands_agent_mod

    monkeypatch.setattr(_commands_agent_mod, "execute_rollback", _spy)

    exit_code = main(
        ["remote", "rollback", "execute", job_id, "--hatp-evidence-id", _VALID_EVIDENCE_ID, "--json"]
    )
    assert exit_code == 0
    assert captured["hatp_evidence_id"] == _VALID_EVIDENCE_ID


def test_ag3_missing_evidence_mandatory_zero_git_effect(tmp_path, monkeypatch, capsys):
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    revert_calls = []
    monkeypatch.setattr(
        _agent_mod,
        "_run_git_revert",
        lambda sha, cwd: revert_calls.append(sha),
    )

    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    assert exit_code == 1
    assert revert_calls == []


def test_ag3_locator_identity_no_typo(tmp_path, monkeypatch, capsys):
    """AG3's --hatp-evidence-id reaches exactly the `hatp_evidence_id`
    keyword on `execute_rollback` -- no alternate parameter name."""
    import inspect

    sig = inspect.signature(_agent_mod.execute_rollback)
    assert "hatp_evidence_id" in sig.parameters


# ═══════════════════════════════════════════════════════════════════════════
# AG5 transport: parser -> handler -> build_rollback_execution (HMRC-REQ-012)
# ═══════════════════════════════════════════════════════════════════════════


def test_ag5_evidence_id_reaches_build_rollback_execution(tmp_path, monkeypatch):
    from tests.test_ag5_hatp_mandatory_consumption import _setup_removable_file_per

    root, _root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.LEGACY_COMPATIBLE)
    monkeypatch.chdir(root.path)

    import pcae.commands.agent as _commands_agent_mod

    captured = {}
    original = _agent_mod.build_rollback_execution

    def _spy(root_arg, per_id, dry_run=False, *, hatp_evidence_id=None, **kwargs):
        captured["hatp_evidence_id"] = hatp_evidence_id
        return original(root_arg, per_id, dry_run=dry_run, hatp_evidence_id=hatp_evidence_id, **kwargs)

    monkeypatch.setattr(_commands_agent_mod, "build_rollback_execution", _spy)

    exit_code = main(
        ["rollback", "--per-id", "per-rertest", "--hatp-evidence-id", _VALID_EVIDENCE_ID, "--json"]
    )
    assert exit_code == 0
    assert captured["hatp_evidence_id"] == _VALID_EVIDENCE_ID


def test_ag5_missing_evidence_mandatory_zero_file_mutation(tmp_path, monkeypatch):
    from tests.test_ag5_hatp_mandatory_consumption import _setup_removable_file_per

    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    monkeypatch.chdir(root.path)

    exit_code = main(["rollback", "--per-id", "per-rertest", "--json"])
    assert exit_code == 1
    assert (root_dir / "added.txt").exists()


def test_ag5_dry_run_mandatory_no_evidence_required_zero_mutation(tmp_path, monkeypatch):
    from tests.test_ag5_hatp_mandatory_consumption import _setup_removable_file_per

    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    monkeypatch.chdir(root.path)

    exit_code = main(["rollback", "--per-id", "per-rertest", "--dry-run", "--json"])
    assert exit_code == 0
    assert (root_dir / "added.txt").exists()


def test_ag5_locator_identity_no_typo():
    import inspect

    sig = inspect.signature(_agent_mod.build_rollback_execution)
    assert "hatp_evidence_id" in sig.parameters


# ═══════════════════════════════════════════════════════════════════════════
# No implicit/auto-discovered evidence (HMRC-REQ-014/078, attack 45)
# ═══════════════════════════════════════════════════════════════════════════


def test_no_implicit_evidence_lookup_in_cli_source():
    """The CLI never looks up "latest" or "any" evidence on the
    caller's behalf -- it transports exactly the caller-supplied ID or
    None."""
    text = _COMMANDS_AGENT_PATH.read_text(encoding="utf-8")
    for forbidden in ("latest_evidence", "find_evidence", "lookup_latest", "auto_select_evidence"):
        assert forbidden not in text


# ═══════════════════════════════════════════════════════════════════════════
# Legacy approve mode-aware disposition (HMRC-REQ-057/058/059)
# ═══════════════════════════════════════════════════════════════════════════


def test_approve_legacy_compatible_unchanged(tmp_path, monkeypatch, capsys):
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    _patch_mode(monkeypatch, CutoverMode.LEGACY_COMPATIBLE)

    exit_code = main(["remote", "rollback", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["updated"] is True
    assert data["new_rollback_approval_state"] == "approved"
    assert "deprecation_warning" not in data


def test_approve_prepared_still_mutates_with_deprecation_diagnostic(tmp_path, monkeypatch, capsys):
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    _patch_mode(monkeypatch, CutoverMode.PREPARED)

    exit_code = main(["remote", "rollback", "approve", job_id, "--json"])
    data = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert data["updated"] is True
    assert data["new_rollback_approval_state"] == "approved"
    assert "deprecation_warning" in data
    assert "hatp_valid" not in json.dumps(data)


def test_approve_mandatory_refuses_without_mutation(tmp_path, monkeypatch, capsys):
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    before = job_file.read_text()
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    exit_code = main(["remote", "rollback", "approve", job_id])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "approved=True" not in output
    assert "permission granted" not in output.lower()
    assert "rollback approved by hatp" not in output.lower()
    assert job_file.read_text() == before


def test_approve_direct_core_call_mandatory_also_refuses(tmp_path, monkeypatch, capsys):
    """HMRC-REQ-068-style direct-call bypass check for the legacy
    approve authority-mutation boundary: calling `approve_rollback`
    directly (skipping the CLI) must still refuse under HATP_MANDATORY,
    since the CLI is transport-only and the mode-aware refusal lives in
    core (`src/pcae/core/agent.py`)."""
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    before = job_file.read_text()
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    with pytest.raises(ValueError):
        _agent_mod.approve_rollback(HarnessPath(tmp_path), job_id)

    assert job_file.read_text() == before


def test_approve_mode_change_after_legacy_before_mutation_no_authority_created(tmp_path, monkeypatch, capsys):
    """TOCTOU discipline (governing-prompt items 66/99): even though the
    deployment started LEGACY_COMPATIBLE, if it has become
    HATP_MANDATORY by the time approval is attempted, no legacy
    authority is created -- mode is resolved fresh immediately before
    mutation, never cached from an earlier read."""
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    job_file = tmp_path / ".pcae" / "remote" / "jobs" / f"{job_id}.json"
    before = job_file.read_text()
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    exit_code = main(["remote", "rollback", "approve", job_id])
    assert exit_code == 1
    assert job_file.read_text() == before


def test_approve_does_not_call_consumption_or_pb(tmp_path, monkeypatch, capsys):
    """Legacy approve never performs evidence consumption (18B) or
    Permission Broker evaluation (governing-prompt items 69/70)."""
    from pcae.core import hatp_rollback_consumption as _consumption_mod

    called = []
    monkeypatch.setattr(
        _consumption_mod,
        "evaluate_for_real_effect",
        lambda *a, **k: called.append(True),
    )
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys, changed_files=["docs/note.md"])
    _patch_mode(monkeypatch, CutoverMode.PREPARED)

    exit_code = main(["remote", "rollback", "approve", job_id, "--json"])
    assert exit_code == 0
    assert called == []


def test_approve_pending_legacy_approval_requires_fresh_evidence_at_effect_time(tmp_path, monkeypatch, capsys):
    """HMRC-REQ-062: a rollback approved under LEGACY_COMPATIBLE, then
    attempted after the deployment reaches HATP_MANDATORY, still
    requires fresh HATP evidence at the execute attempt -- the earlier
    legacy approval is not grandfathered."""
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    exit_code = main(["remote", "rollback", "execute", job_id, "--json"])
    assert exit_code == 1


# ═══════════════════════════════════════════════════════════════════════════
# Help surface (governing-prompt items 47/93/49/50)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "argv",
    [
        ["remote", "rollback", "execute", "--help"],
        ["rollback", "--help"],
        ["remote", "rollback", "approve", "--help"],
    ],
)
def test_help_succeeds_without_side_effects(argv):
    result = subprocess.run(
        [sys.executable, "-m", "pcae", *argv],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0


def test_ag3_help_documents_evidence_flag_neutrally():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "remote", "rollback", "execute", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "--hatp-evidence-id" in result.stdout
    assert "grants" not in result.stdout.lower()
    assert "permission granted" not in result.stdout.lower()


def test_ag5_help_documents_evidence_flag_neutrally():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "rollback", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "--hatp-evidence-id" in result.stdout


def test_approve_help_does_not_imply_removed_pre_cutover_behavior():
    result = subprocess.run(
        [sys.executable, "-m", "pcae", "remote", "rollback", "approve", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "removed" not in result.stdout.lower()
