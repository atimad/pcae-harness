from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core.paths import HarnessPath
from pcae.core.review import (
    create_lifecycle_review,
    list_lifecycle_reviews,
    show_lifecycle_review,
)
from pcae.core.session import write_session_snapshot
from pcae.core.tasks import create_task_contract


def init_git_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path, check=True, capture_output=True,
    )


def commit_all(tmp_path: Path, message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=tmp_path, check=True, capture_output=True,
    )


def test_create_lifecycle_review(tmp_path: Path, monkeypatch) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path), "Review task",
        created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
    )
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    record = create_lifecycle_review(
        HarnessPath(tmp_path),
        disposition="approved",
        notes="Looks good",
    )

    assert record.disposition == "approved"
    assert record.task_id == "20260618-1000-review-task"
    assert record.reviewer == "human"
    assert record.notes == "Looks good"
    assert (tmp_path / ".pcae" / "lifecycle-reviews" / f"{record.lrr_id}.json").is_file()


def test_show_lifecycle_review(tmp_path: Path, monkeypatch) -> None:
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path), "Show task",
        created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
    )
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    record = create_lifecycle_review(
        HarnessPath(tmp_path), disposition="informational",
    )
    found = show_lifecycle_review(HarnessPath(tmp_path), record.lrr_id)

    assert found is not None
    assert found.lrr_id == record.lrr_id
    assert found.disposition == "informational"


def test_show_lifecycle_review_not_found(tmp_path: Path) -> None:
    result = show_lifecycle_review(HarnessPath(tmp_path), "nonexistent")
    assert result is None


def test_list_lifecycle_reviews(tmp_path: Path, monkeypatch) -> None:
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path), "List task",
        created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
    )
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    create_lifecycle_review(HarnessPath(tmp_path), disposition="approved")
    create_lifecycle_review(HarnessPath(tmp_path), disposition="changes_requested")

    records = list_lifecycle_reviews(HarnessPath(tmp_path))
    assert len(records) == 2


def test_list_lifecycle_reviews_filter_by_task(tmp_path: Path, monkeypatch) -> None:
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path), "Filter task",
        created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
    )
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    create_lifecycle_review(HarnessPath(tmp_path), disposition="approved")
    create_lifecycle_review(
        HarnessPath(tmp_path), disposition="approved", task_id="other-task",
    )

    records = list_lifecycle_reviews(
        HarnessPath(tmp_path), task_id="20260618-1000-filter-task",
    )
    assert len(records) == 1


def test_list_lifecycle_reviews_open_only(tmp_path: Path, monkeypatch) -> None:
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path), "Open task",
        created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
    )
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    create_lifecycle_review(HarnessPath(tmp_path), disposition="approved")
    create_lifecycle_review(HarnessPath(tmp_path), disposition="changes_requested")

    records = list_lifecycle_reviews(HarnessPath(tmp_path), open_only=True)
    assert len(records) == 1
    assert records[0].disposition == "changes_requested"


def test_cli_lifecycle_review_create(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path), "CLI create task",
        created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
    )
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "review", "lifecycle", "create",
        "--disposition", "approved",
        "--notes", "CLI test review",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Created lifecycle review:" in output
    assert "Disposition: approved" in output


def test_cli_lifecycle_review_create_json(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    init_git_repo(tmp_path)
    init_harness(HarnessPath(tmp_path))
    create_task_contract(
        HarnessPath(tmp_path), "CLI JSON task",
        created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
    )
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "review", "lifecycle", "create",
        "--disposition", "approved",
        "--json",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert parsed["disposition"] == "approved"
    assert "lrr_id" in parsed


def test_cli_lifecycle_review_create_invalid_disposition(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main([
        "review", "lifecycle", "create",
        "--disposition", "invalid",
    ])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "Invalid disposition" in output


def test_cli_lifecycle_review_list(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path), "CLI list task",
        created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
    )
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)
    create_lifecycle_review(HarnessPath(tmp_path), disposition="approved")

    exit_code = main(["review", "lifecycle", "list"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Lifecycle reviews: 1" in output


def test_cli_lifecycle_review_list_json(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    init_git_repo(tmp_path)
    create_task_contract(
        HarnessPath(tmp_path), "CLI list JSON task",
        created_at=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
    )
    commit_all(tmp_path, "init")
    monkeypatch.chdir(tmp_path)
    create_lifecycle_review(HarnessPath(tmp_path), disposition="approved")

    exit_code = main(["review", "lifecycle", "list", "--json"])

    output = capsys.readouterr().out
    assert exit_code == 0
    parsed = json.loads(output)
    assert len(parsed["reviews"]) == 1


def test_cli_lifecycle_review_show_not_found(
    tmp_path: Path, monkeypatch, capsys,
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main(["review", "lifecycle", "show", "nonexistent"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "not found" in output
