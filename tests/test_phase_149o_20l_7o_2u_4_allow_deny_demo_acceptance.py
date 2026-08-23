"""Phase 149O.20L.7O.2U.4 -- Deny/Allow Demo and Quick-Start Documentation.

Focused acceptance harness (not a duplicate of 2U.2's 24-case or 2U.3's
116-case adversarial suites) proving the exact user-facing claim this
phase demonstrates manually against the reference adapter and a
disposable repository:

  ALLOW: a valid, in-scope proposal is accepted, reaches the existing
  unmodified downstream review/promotion chain, and a real promotion
  writes the approved file into the repository working tree.

  DENY: a structurally identical but out-of-scope proposal is rejected
  by task-scope governance -- not malformed input -- produces no ECP,
  and cannot reach promotion.

Uses the real production `pcae.core.intake` / `pcae.core.agent`
promotion-review/promotion-execution code paths, not mocks.
"""

from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pcae.core import agent as agent_module
from pcae.core import intake
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


def _init_git_root(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / "src").mkdir()
    (path / "README.md").write_text("# demo\n")
    (path / "src" / "app.py").write_text("def greet(name):\n    return f'Hello, {name}!'\n")
    subprocess.run(["git", "add", "-A"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


def _head(path: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()


def _setup(tmp_path) -> tuple[HarnessPath, str, str]:
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    contract = create_task_contract(
        root, "2U4 allow/deny demo acceptance task",
        created_at=datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc),
        allowed_files=("src/app.py",),
    )
    return root, contract.task_id, _head(root_dir)


def _candidate(root, task_id, head, candidate_id, path, content):
    return {
        "intake_contract_version": "1.0",
        "candidate_id": candidate_id,
        "producer": {"kind": "claude-code", "adapter_version": "2U.4-demo"},
        "task_context": {"task_id": task_id, "declared_goal": "demo"},
        "repo_binding": {
            "repo_fingerprint": intake.compute_repo_fingerprint(root),
            "base_commit": head,
        },
        "proposed_changes": [
            {
                "path": path,
                "operation": "modify",
                "content_after": content,
                "content_hash_after": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }
        ],
        "producer_claims": {"summary": "demo", "self_reported_complete": True},
    }


def test_allow_reaches_real_promotion_and_writes_target_file(tmp_path):
    root, task_id, head = _setup(tmp_path)
    new_content = "def greet(name):\n    return f'Hello there, {name}!'\n"
    candidate = _candidate(root, task_id, head, "allow-1", "src/app.py", new_content)

    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False
    ecp_id = result["ecp_id"]
    assert ecp_id is not None

    review = agent_module.build_promotion_review(
        root, ecp_id, "approved", reviewed_by="demo-operator",
        approved_paths=["src/app.py"], promotion_authorized=True,
    )
    assert review["created"] is True
    assert review["promotion_authorized"] is True
    assert review["execution_allowed"] is False

    promotion = agent_module.build_promotion_execution(root, review["epr_id"])
    assert promotion["promoted"] is True
    assert promotion["execution_allowed"] is False
    assert (root.path / "src" / "app.py").read_text() == new_content


def test_deny_out_of_scope_produces_no_ecp_and_no_promotion_path(tmp_path):
    root, task_id, head = _setup(tmp_path)
    candidate = _candidate(root, task_id, head, "deny-1", "README.md", "# demo\n\nunauthorized\n")

    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is False
    assert result["ecp_id"] is None
    assert any("out_of_scope_path" in r for r in result["rejection_reasons"])

    # Proposal was otherwise valid: repo/base/hash all verify -- this is a
    # scope rejection, not a malformed-input rejection.
    assert not any(
        r.startswith(("repo_mismatch", "base_mismatch", "hash_mismatch", "malformed"))
        for r in result["rejection_reasons"]
    )

    # No ECP exists for this candidate at all, so no promotion-review or
    # promotion can be constructed from it.
    assert agent_module.lookup_execution_change_package(root, f"ecp-intake-{task_id}") is None
    assert not (root.path / "README.md").read_text().strip().endswith("unauthorized")


def test_allow_and_deny_are_independent_outcomes_from_same_task(tmp_path):
    """Side-by-side: identical task/producer, only scope differs."""
    root, task_id, head = _setup(tmp_path)
    allow_result = intake.validate_and_ingest_intake_candidate(
        root, _candidate(root, task_id, head, "allow-sbs", "src/app.py", "def greet(n):\n    return n\n")
    )
    deny_result = intake.validate_and_ingest_intake_candidate(
        root, _candidate(root, task_id, head, "deny-sbs", "config/production.yaml", "x: 1\n")
    )
    assert allow_result["accepted"] is True and allow_result["ecp_id"] is not None
    assert deny_result["accepted"] is False and deny_result["ecp_id"] is None
