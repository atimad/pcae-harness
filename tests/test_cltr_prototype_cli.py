from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from pcae.cli import main

FIXTURES = Path(__file__).parent / "fixtures" / "cltr_prototype"


@pytest.fixture()
def isolated_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _copy_fixture(name: str, dest_dir: Path) -> Path:
    dest = dest_dir / name
    shutil.copy(FIXTURES / name, dest)
    return dest


def test_cli_generate_exit_code_and_json(isolated_cwd, capsys):
    fixture_path = _copy_fixture("successful_transition.json", isolated_cwd)
    exit_code = main(["cltr-prototype", "generate", "--input", str(fixture_path), "--json"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["prototype_only"] is True
    assert payload["canonical"] is False
    assert payload["authorization"] is False
    assert payload["lifecycle_state"] == "TERMINAL_SUCCESS"


def test_cli_generate_text_output_discloses_boundary(isolated_cwd, capsys):
    fixture_path = _copy_fixture("pre_certification_failure.json", isolated_cwd)
    exit_code = main(["cltr-prototype", "generate", "--input", str(fixture_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "PROTOTYPE ONLY" in captured.out
    assert "NOT a canonical" in captured.out
    assert "NOT an authorization" in captured.out


def test_cli_show_after_generate(isolated_cwd, capsys):
    fixture_path = _copy_fixture("successful_transition.json", isolated_cwd)
    main(["cltr-prototype", "generate", "--input", str(fixture_path), "--json"])
    capsys.readouterr()
    exit_code = main(["cltr-prototype", "show", "--record", "txn-fixture-successful-1", "--json"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["identity"]["transition_id"] == "txn-fixture-successful-1"


def test_cli_verify_after_generate(isolated_cwd, capsys):
    fixture_path = _copy_fixture("successful_transition.json", isolated_cwd)
    main(["cltr-prototype", "generate", "--input", str(fixture_path), "--json"])
    capsys.readouterr()
    exit_code = main(["cltr-prototype", "verify", "--record", "txn-fixture-successful-1", "--json"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["digest_valid"] is True
    assert payload["invariant_summary"]["total"] == 37


def test_cli_compare_after_generate(isolated_cwd, capsys):
    fixture_path = _copy_fixture("successful_transition.json", isolated_cwd)
    main(["cltr-prototype", "generate", "--input", str(fixture_path), "--json"])
    capsys.readouterr()

    manifest_path = isolated_cwd / "targets.json"
    manifest_path.write_text(json.dumps({"notification_result": {"transition_id": "txn-fixture-successful-1"}}))

    exit_code = main(["cltr-prototype", "compare", "--record", "txn-fixture-successful-1", "--against", str(manifest_path), "--json"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["mixed_generation_detected"] is False


def test_cli_list(isolated_cwd, capsys):
    fixture_path = _copy_fixture("successful_transition.json", isolated_cwd)
    main(["cltr-prototype", "generate", "--input", str(fixture_path), "--json"])
    capsys.readouterr()
    exit_code = main(["cltr-prototype", "list", "--json"])
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert "txn-fixture-successful-1" in payload["generations"]


def test_cli_verify_missing_record_reports_unverifiable(isolated_cwd, capsys):
    exit_code = main(["cltr-prototype", "verify", "--record", "nonexistent", "--json"])
    captured = capsys.readouterr()
    assert exit_code != 0
    payload = json.loads(captured.out)
    assert payload["conformance"] == "unverifiable"


def test_cli_generate_deterministic_exit_codes(isolated_cwd, capsys):
    fixture_path = _copy_fixture("successful_transition.json", isolated_cwd)
    exit_code_1 = main(["cltr-prototype", "generate", "--input", str(fixture_path), "--json"])
    capsys.readouterr()
    exit_code_2 = main(["cltr-prototype", "generate", "--input", str(fixture_path), "--json"])
    assert exit_code_1 == exit_code_2 == 0


def test_cli_only_writes_under_prototype_prefix(isolated_cwd):
    fixture_path = _copy_fixture("successful_transition.json", isolated_cwd)
    before = set(isolated_cwd.rglob("*"))
    main(["cltr-prototype", "generate", "--input", str(fixture_path), "--json"])
    after = set(isolated_cwd.rglob("*"))
    new_paths = after - before
    for p in new_paths:
        rel = p.relative_to(isolated_cwd)
        parts = rel.parts
        assert parts[0] == ".pcae"
        if len(parts) > 1:
            assert parts[1] == "cltr-prototypes"


def test_cli_has_no_repair_promote_complete_notify_commands():
    from pcae.cli import build_parser

    parser = build_parser()
    subparsers_action = next(a for a in parser._subparsers._group_actions if a.dest == "command")
    cltr_prototype_parser = subparsers_action.choices["cltr-prototype"]
    inner = next(a for a in cltr_prototype_parser._subparsers._group_actions if a.dest == "cltr_prototype_command")
    assert set(inner.choices.keys()) == {"generate", "show", "verify", "compare", "list"}
