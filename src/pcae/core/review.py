from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

from pcae.core.paths import HarnessPath
from pcae.core.tasks import find_latest_active_task


LIFECYCLE_REVIEWS_DIR = Path(".pcae") / "lifecycle-reviews"

VALID_DISPOSITIONS = ("approved", "changes_requested", "informational")


@dataclass(frozen=True)
class LifecycleReviewRecord:
    lrr_id: str
    task_id: str
    reviewer: str
    disposition: str
    commit_range: str
    reviewed_files: tuple[str, ...]
    notes: str
    created_at: str

    def to_dict(self) -> dict:
        return {
            "commit_range": self.commit_range,
            "created_at": self.created_at,
            "disposition": self.disposition,
            "lrr_id": self.lrr_id,
            "notes": self.notes,
            "reviewed_files": list(self.reviewed_files),
            "reviewer": self.reviewer,
            "task_id": self.task_id,
        }


def create_lifecycle_review(
    root: HarnessPath,
    disposition: str,
    notes: str = "",
    reviewer: str = "human",
    task_id: str | None = None,
    commit_range: str | None = None,
    reviewed_files: tuple[str, ...] | None = None,
    created_at: datetime | None = None,
) -> LifecycleReviewRecord:
    timestamp = created_at or datetime.now(timezone.utc)

    if task_id is None:
        active_task = find_latest_active_task(root)
        task_id = active_task.task_id if active_task else "none"

    if commit_range is None:
        commit_range = _detect_commit_range(root)

    if reviewed_files is None:
        reviewed_files = _detect_changed_files(root)

    lrr_id = f"lrr-{task_id}-{timestamp:%Y%m%dT%H%M%S}-{timestamp.microsecond:06d}"

    record = LifecycleReviewRecord(
        lrr_id=lrr_id,
        task_id=task_id,
        reviewer=reviewer,
        disposition=disposition,
        commit_range=commit_range,
        reviewed_files=reviewed_files,
        notes=notes,
        created_at=timestamp.isoformat(),
    )

    target = root.join(LIFECYCLE_REVIEWS_DIR / f"{lrr_id}.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(record.to_dict(), f, indent=2, sort_keys=True)
        f.write("\n")

    return record


def show_lifecycle_review(root: HarnessPath, lrr_id: str) -> LifecycleReviewRecord | None:
    path = root.join(LIFECYCLE_REVIEWS_DIR / f"{lrr_id}.json")
    if not path.is_file():
        return None
    return _read_lrr(path)


def list_lifecycle_reviews(
    root: HarnessPath, task_id: str | None = None, open_only: bool = False,
) -> tuple[LifecycleReviewRecord, ...]:
    review_dir = root.join(LIFECYCLE_REVIEWS_DIR)
    if not review_dir.is_dir():
        return ()

    records = []
    for path in sorted(review_dir.glob("lrr-*.json")):
        record = _read_lrr(path)
        if record is None:
            continue
        if task_id and record.task_id != task_id:
            continue
        if open_only and record.disposition != "changes_requested":
            continue
        records.append(record)

    return tuple(records)


def _read_lrr(path: Path) -> LifecycleReviewRecord | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return LifecycleReviewRecord(
            lrr_id=data["lrr_id"],
            task_id=data["task_id"],
            reviewer=data["reviewer"],
            disposition=data["disposition"],
            commit_range=data.get("commit_range", "unknown"),
            reviewed_files=tuple(data.get("reviewed_files", ())),
            notes=data.get("notes", ""),
            created_at=data["created_at"],
        )
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def _detect_commit_range(root: HarnessPath) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-1", "--format=%H"],
            cwd=root.path,
            capture_output=True,
            text=True,
            check=True,
        )
        head = result.stdout.strip()[:12]
        return f"..{head}" if head else "unknown"
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def _detect_changed_files(root: HarnessPath) -> tuple[str, ...]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=root.path,
            capture_output=True,
            text=True,
            check=True,
        )
        paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return tuple(paths) if paths else ()
    except (subprocess.CalledProcessError, OSError):
        return ()
