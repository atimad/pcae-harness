"""
Phase 149O.20L.7O.3J — Repository Intelligence -> Advisory Production
Consumption Integration tests.

Verifies that `pcae.core.advisory.build_advisory` (the real, default
Advisory production decision path -- `pcae advisory check`) now
automatically consumes the pre-existing, already-tested
`pcae.advisory.context.build_advisory_context` bridge, without a
manual `pcae advisory context build` CLI prerequisite, while remaining
structurally non-authoritative: Repository Intelligence context never
influences the Permission-Broker-derived verdict.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import advisory as advisory_module
from pcae.core.advisory import build_advisory
from pcae.repository_intelligence.snapshot_generator import generate_snapshot

pytestmark = pytest.mark.fast_green

REPO_ROOT = Path(__file__).resolve().parent.parent


def _repo_with_snapshot(tmp_path: Path) -> Path:
    """A bare repo_root directory carrying a real, freshly generated,
    valid Repository Knowledge Snapshot at the canonical location
    `.pcae/repository-intelligence/latest.json`."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir(parents=True)
    generate_snapshot(REPO_ROOT, output_dir=repo_root / ".pcae" / "repository-intelligence")
    return repo_root


# ── Automatic consumption / manual-choreography elimination ─────────────


def test_advisory_check_automatically_consumes_repository_intelligence_context(tmp_path):
    """The real Advisory production path acquires RI context without any
    manual `advisory context build` CLI invocation in this test."""
    repo_root = _repo_with_snapshot(tmp_path)

    data = build_advisory(
        repo_root=repo_root,
        requested_command="ls",
        requested_action="read",
    )

    ri = data["repository_intelligence_context"]
    assert ri["available"] is True
    assert "context" in ri
    assert ri["context"]["context_metadata"]["query_request"]["category"] == "boundary_lookup"


def test_advisory_check_key_present_even_without_repository_intelligence_context(tmp_path):
    """Absence of RI context is disclosed, not silently omitted."""
    repo_root = tmp_path / "no_snapshot_repo"
    repo_root.mkdir()

    data = build_advisory(
        repo_root=repo_root,
        requested_command="ls",
        requested_action="read",
    )

    assert "repository_intelligence_context" in data
    ri = data["repository_intelligence_context"]
    assert ri["available"] is False
    assert ri["unavailable_reason"] == "no_repository_intelligence_snapshot_found"


def test_entity_lookup_target_is_the_first_requested_file(tmp_path):
    repo_root = _repo_with_snapshot(tmp_path)

    data = build_advisory(
        repo_root=repo_root,
        requested_command="cat src/pcae/__init__.py",
        requested_action="read",
        requested_files=["src/pcae/__init__.py", "src/pcae/__main__.py"],
    )

    ri = data["repository_intelligence_context"]
    assert ri["available"] is True
    query_request = ri["context"]["context_metadata"]["query_request"]
    assert query_request["category"] == "entity_lookup"
    assert query_request["target"] == "src/pcae/__init__.py"


# ── Missing / invalid RI state: fail-soft, never fail-closed for Advisory ──


def test_missing_snapshot_leaves_broker_decision_unaffected(tmp_path):
    repo_root = tmp_path / "no_snapshot_repo"
    repo_root.mkdir()

    data = build_advisory(
        repo_root=repo_root,
        requested_command="ls",
        requested_action="read",
    )

    assert data["repository_intelligence_context"]["available"] is False
    assert data["broker_decision"]
    assert data["advisory_decision"]
    assert data["would_deny"] is False


def test_corrupt_snapshot_disclosed_not_raised(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    snapshot_dir = repo_root / ".pcae" / "repository-intelligence"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "latest.json").write_text("{ this is not valid json")

    data = build_advisory(
        repo_root=repo_root,
        requested_command="ls",
        requested_action="read",
    )

    ri = data["repository_intelligence_context"]
    assert ri["available"] is False
    assert ri["unavailable_reason"] == "repository_intelligence_context_build_failed"
    assert "unavailable_detail" in ri


def test_incompatible_schema_version_disclosed_not_raised(tmp_path):
    repo_root = _repo_with_snapshot(tmp_path)
    snapshot_path = repo_root / ".pcae" / "repository-intelligence" / "latest.json"
    snapshot = json.loads(snapshot_path.read_text())
    snapshot["snapshot_identity"]["executable_schema_version"] = "future-incompatible-version"
    snapshot_path.write_text(json.dumps(snapshot))

    data = build_advisory(
        repo_root=repo_root,
        requested_command="ls",
        requested_action="read",
    )

    ri = data["repository_intelligence_context"]
    assert ri["available"] is False
    assert ri["unavailable_reason"] == "repository_intelligence_context_build_failed"


# ── Stale RI state: disclosed via existing provenance, not fabricated ────


def _make_git_repo(repo_root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_root, check=True)
    (repo_root / "README.md").write_text("placeholder\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo_root, check=True)


def test_stale_snapshot_commit_mismatch_is_disclosed_as_limitation(tmp_path):
    repo_root = _repo_with_snapshot(tmp_path)
    _make_git_repo(repo_root)
    snapshot_path = repo_root / ".pcae" / "repository-intelligence" / "latest.json"
    snapshot = json.loads(snapshot_path.read_text())
    snapshot["envelope"]["repository_context"]["repository_commit"] = "0" * 40
    snapshot_path.write_text(json.dumps(snapshot))

    data = build_advisory(
        repo_root=repo_root,
        requested_command="ls",
        requested_action="read",
    )

    ri = data["repository_intelligence_context"]
    assert ri["available"] is True
    limitation_types = {
        lim["limitation_type"] for lim in ri["context"]["limitation_bundle"]
    }
    assert "possibly_stale_snapshot" in limitation_types


def test_matching_commit_snapshot_is_not_flagged_stale(tmp_path):
    repo_root = _repo_with_snapshot(tmp_path)
    _make_git_repo(repo_root)
    snapshot_path = repo_root / ".pcae" / "repository-intelligence" / "latest.json"
    snapshot = json.loads(snapshot_path.read_text())

    from pcae.repository_intelligence.historical_memory.git_source import (
        git_head_commit_sha,
    )

    snapshot["envelope"]["repository_context"]["repository_commit"] = git_head_commit_sha(repo_root)
    snapshot_path.write_text(json.dumps(snapshot))

    data = build_advisory(
        repo_root=repo_root,
        requested_command="ls",
        requested_action="read",
    )
    ri = data["repository_intelligence_context"]
    limitation_types = {
        lim["limitation_type"] for lim in ri["context"]["limitation_bundle"]
    }
    assert "possibly_stale_snapshot" not in limitation_types


# ── Isolation: no cross-repository leakage, no "latest file" heuristic ──


def test_wrong_repo_snapshot_not_consumed(tmp_path):
    repo_a = _repo_with_snapshot(tmp_path / "a")
    repo_b = tmp_path / "b"
    repo_b.mkdir()

    data = build_advisory(
        repo_root=repo_b,
        requested_command="ls",
        requested_action="read",
    )

    assert data["repository_intelligence_context"]["available"] is False


def test_snapshot_path_is_canonical_latest_json_not_a_directory_scan(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    snapshot_dir = repo_root / ".pcae" / "repository-intelligence" / "snapshots"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "20990101T000000000000Z.json").write_text("{}")

    data = build_advisory(
        repo_root=repo_root,
        requested_command="ls",
        requested_action="read",
    )

    assert data["repository_intelligence_context"]["available"] is False
    assert data["repository_intelligence_context"]["unavailable_reason"] == (
        "no_repository_intelligence_snapshot_found"
    )


# ── Determinism ───────────────────────────────────────────────────────────


def test_repeated_consumption_is_deterministic(tmp_path):
    repo_root = _repo_with_snapshot(tmp_path)

    first = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    second = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")

    first_ri = dict(first["repository_intelligence_context"]["context"])
    second_ri = dict(second["repository_intelligence_context"]["context"])
    first_ri["context_metadata"] = {
        k: v for k, v in first_ri["context_metadata"].items() if k != "assembly_timestamp"
    }
    second_ri["context_metadata"] = {
        k: v for k, v in second_ri["context_metadata"].items() if k != "assembly_timestamp"
    }
    assert first_ri == second_ri


# ── Authority non-flow ────────────────────────────────────────────────────


def test_repository_intelligence_presence_never_changes_broker_or_advisory_decision(tmp_path):
    """A context that might read as 'informative' must never itself alter
    the broker-derived verdict -- with or without RI context present, the
    same evidence inputs must produce the identical decision."""
    repo_with_ri = _repo_with_snapshot(tmp_path / "with_ri")
    repo_without_ri = tmp_path / "without_ri"
    repo_without_ri.mkdir()

    kwargs = dict(
        requested_command="ls",
        requested_action="read",
        health_passed=True,
        check_passed=True,
    )

    with_ri = build_advisory(repo_root=repo_with_ri, **kwargs)
    without_ri = build_advisory(repo_root=repo_without_ri, **kwargs)

    assert with_ri["repository_intelligence_context"]["available"] is True
    assert without_ri["repository_intelligence_context"]["available"] is False
    for key in (
        "broker_decision",
        "advisory_decision",
        "would_block",
        "would_deny",
        "would_require_human_review",
        "hard_block_present",
        "authorization_granted",
        "execution_authorized",
    ):
        assert with_ri[key] == without_ri[key], f"{key} diverged based on RI presence"


def test_no_authority_field_synthesized_from_repository_intelligence(tmp_path):
    repo_root = _repo_with_snapshot(tmp_path)
    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")

    ri = data["repository_intelligence_context"]
    forbidden_keys = {
        "authorization",
        "permission",
        "authorized",
        "allow",
        "grant",
        "execution_capability",
    }
    serialized_keys = set()

    def _collect_keys(value):
        if isinstance(value, dict):
            for k, v in value.items():
                serialized_keys.add(k)
                _collect_keys(v)
        elif isinstance(value, (list, tuple)):
            for item in value:
                _collect_keys(item)

    _collect_keys(ri)
    assert serialized_keys.isdisjoint(forbidden_keys)
    assert data["authorization_granted"] is False
    assert data["execution_authorized"] is False


def test_no_permission_broker_coupling_in_repository_intelligence_or_advisory_context_modules():
    """Static confirmation of the pre-existing, still-intact isolation
    (149O.20L.7O.3I S20): zero references to permission_broker anywhere in
    the RI or advisory-context subsystems, unchanged by this integration."""
    ri_dir = REPO_ROOT / "src" / "pcae" / "repository_intelligence"
    ctx_dir = REPO_ROOT / "src" / "pcae" / "advisory" / "context"
    for directory in (ri_dir, ctx_dir):
        for path in directory.rglob("*.py"):
            text = path.read_text()
            assert "permission_broker" not in text, f"{path} references permission_broker"
            assert "PermissionBroker" not in text, f"{path} references PermissionBroker"


# ── No self-CLI subprocess ────────────────────────────────────────────────


def test_advisory_module_does_not_shell_out_to_pcae_cli():
    """Static AST check: `core/advisory.py` must never invoke PCAE's own
    CLI via subprocess/shell/text-parsing to acquire RI context."""
    source = Path(advisory_module.__file__).read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name != "subprocess", "core/advisory.py must not import subprocess"
        if isinstance(node, ast.ImportFrom):
            assert node.module != "subprocess"


# ── CLI regression (manual diagnostic path remains functional) ──────────


def test_cli_advisory_context_build_still_functions(tmp_path):
    repo_root = _repo_with_snapshot(tmp_path)
    snapshot_path = repo_root / ".pcae" / "repository-intelligence" / "latest.json"

    result = subprocess.run(
        [
            sys.executable, "-m", "pcae", "advisory", "context", "build",
            "--snapshot", str(snapshot_path),
            "--entity", "src/pcae/__init__.py",
            "--json",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["context_metadata"]["query_request"]["category"] == "entity_lookup"


def test_cli_advisory_check_reflects_automatic_repository_intelligence_context(tmp_path):
    repo_root = _repo_with_snapshot(tmp_path)

    result = subprocess.run(
        [sys.executable, "-m", "pcae", "advisory", "check", "--command", "ls", "--json"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "repository_intelligence_context" in payload


# ── Runtime boundary ──────────────────────────────────────────────────────


def test_advisory_check_never_activates_runtime_execution(tmp_path):
    repo_root = _repo_with_snapshot(tmp_path)
    data = build_advisory(repo_root=repo_root, requested_command="ls", requested_action="read")
    assert data["execution_authorized"] is False
    assert data["command_executed"] is False
    assert data["performed_flags"]["backend_invocation_performed"] is False
