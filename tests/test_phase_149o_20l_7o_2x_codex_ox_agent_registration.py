"""Phase 149O.20L.7O.2X -- Codex-Ox Agent Registration and Generic Intake
Compatibility.

Verifies the registration of `codex-ox` as a first-class, supported PCAE
agent identity (the multi-agent capability registry, the agent
configuration registry, and the `pcae session bootstrap` backend-lock
recognition surface), and freshly re-verifies -- for this specific
identity -- the invariants Phase 149O.20L.7O.2W already established for
the shared generic producer intake helper: `codex-ox` reuses that helper
unchanged, its literal agent_id is never normalized, and its producer
provenance never influences any allow/deny/authority decision.

This phase adds no Codex-Ox-specific intake adapter and no native
Ox/Codex output parser -- `codex-ox` differs from any other governance
agent lock identity only in being pre-declared in the advisory
capability/config registries and recognized by the session-bootstrap
backend-lock rehydration step.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core import agent as agent_module
from pcae.core import intake
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


def _init_git_root(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    (path / "README.md").write_text("hello\n")
    subprocess.run(["git", "add", "README.md"], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=path, check=True)


def _head(path: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=path, capture_output=True, text=True, check=True
    ).stdout.strip()


def _setup(tmp_path, name="root", allowed_files=("src/allowed/**",)) -> tuple[HarnessPath, str, str]:
    root_dir = tmp_path / name
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    contract = create_task_contract(
        root, "2X codex-ox registration task",
        created_at=datetime(2026, 8, 24, 12, 0, tzinfo=timezone.utc),
        allowed_files=allowed_files,
    )
    return root, contract.task_id, _head(root_dir)


def _write_content(tmp_path, name, text) -> Path:
    p = tmp_path / name
    p.write_text(text)
    return p


# ---------------------------------------------------------------------------
# Capability registry / config registry registration
# ---------------------------------------------------------------------------

def test_codex_ox_registered_in_multi_agent_registry():
    entry = agent_module.get_agent_by_id("codex-ox")
    assert entry is not None
    assert entry.agent_type == "codex"
    assert entry.status == agent_module.AGENT_STATUS_AVAILABLE
    assert entry.capabilities
    assert entry.preferred_workloads


def test_codex_ox_capabilities_do_not_claim_runtime_execution():
    """Unlike codex-local, codex-ox's advisory capability list must not
    include 'runtime_execution' -- this registration must not read as
    granting execution authority beyond the frozen runtime posture."""
    entry = agent_module.get_agent_by_id("codex-ox")
    assert "runtime_execution" not in entry.capabilities


def test_codex_ox_registered_in_agent_config_registry():
    config = agent_module.get_agent_config("codex-ox")
    assert config is not None
    assert config.adapter_type == agent_module.ADAPTER_TYPE_CLI
    assert config.executable_hint == "codex"
    assert config.configuration_status == "configured"
    # No provider credential/secret material in the advisory config notes.
    for banned in ("api_key", "apikey", "bearer", "token", "openrouter.ai/api"):
        assert banned not in config.configuration_notes.lower()


def test_codex_ox_appears_in_agents_cli_json(tmp_path, monkeypatch, capsys):
    init_harness(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    ids = {e["agent_id"] for e in data["agents"]}
    assert "codex-ox" in ids


def test_agents_validate_still_passes_with_codex_ox(tmp_path, monkeypatch, capsys):
    init_harness(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(["agents", "validate", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["valid"] is True
    assert data["errors"] == []


# ---------------------------------------------------------------------------
# Session bootstrap: literal identity, backend-lock recognition
# ---------------------------------------------------------------------------

def test_session_bootstrap_accepts_codex_ox_literally(tmp_path, monkeypatch, capsys):
    root_dir = tmp_path
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    create_task_contract(root, "2X bootstrap task")
    monkeypatch.chdir(root_dir)

    exit_code = main(["session", "bootstrap", "--agent-id", "codex-ox", "--json"])
    d = json.loads(capsys.readouterr().out)

    assert d["agent_id"] == "codex-ox"
    assert d["lock_acquired"] is True
    assert d["recognized_backend"] is True

    lock = agent_module.read_agent_lock(root)
    assert lock.agent_id == "codex-ox"
    assert lock.agent_id != "codex"
    assert lock.agent_id != "codex-local"


def test_session_bootstrap_rehydrates_codex_ox_backend_lock(tmp_path, monkeypatch, capsys):
    root_dir = tmp_path
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    create_task_contract(root, "2X backend-lock task")
    monkeypatch.chdir(root_dir)

    exit_code = main(["session", "bootstrap", "--agent-id", "codex-ox", "--json"])
    d = json.loads(capsys.readouterr().out)
    assert exit_code in (0, 1)  # readiness may be blocked in a bare fresh repo; lock sync is independent
    assert d["lock_rehydrated"] is True
    assert d["lock_backend_name"] == "codex-ox"
    assert d["lock_conflict"] is False

    backend_lock_path = root_dir / ".pcae" / "agent-locks" / "latest.json"
    assert backend_lock_path.is_file()
    backend_lock = json.loads(backend_lock_path.read_text(encoding="utf-8"))
    assert backend_lock["backend_name"] == "codex-ox"
    assert backend_lock["lock_owner"] == "codex-ox"
    assert backend_lock["backend_type"] == "codex"
    assert backend_lock["execution_authorized"] is False
    assert backend_lock["invocation_allowed"] is False
    assert backend_lock["may_execute_shell"] is False


def test_session_bootstrap_codex_ox_not_normalized_to_codex_local(tmp_path, monkeypatch, capsys):
    root_dir = tmp_path
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    create_task_contract(root, "2X no-normalization task")
    monkeypatch.chdir(root_dir)

    main(["session", "bootstrap", "--agent-id", "codex-ox", "--json"])
    capsys.readouterr()

    backend_lock = json.loads(
        (root_dir / ".pcae" / "agent-locks" / "latest.json").read_text(encoding="utf-8")
    )
    assert backend_lock["backend_name"] not in ("codex", "codex-local", "ox", "openrouter")


# ---------------------------------------------------------------------------
# Generic intake reuse: identical helper, identical provenance semantics
# ---------------------------------------------------------------------------

def test_lock_derived_producer_codex_ox_identity_no_dedicated_adapter(tmp_path):
    """codex-ox gets identical generic-helper treatment to codex-local and
    claude-local -- no Codex-Ox-specific parser or adapter, only its
    bootstrapped agent-lock identity differs."""
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "codex-ox")
    content_file = _write_content(tmp_path, "cox1.py", "x = 1\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-codex-ox",
        file_specs=[f"src/allowed/cox1.py:create:{content_file}"],
    )
    assert build_result["errors"] == []
    producer = build_result["candidate"]["producer"]
    assert producer["kind"] == "codex-ox"
    assert producer["source"] == "agent_lock"

    result = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
    assert result["accepted"] is True


def test_codex_ox_provenance_not_normalized_by_generic_helper(tmp_path):
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "codex-ox")
    content_file = _write_content(tmp_path, "cox2.py", "x = 2\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-codex-ox-norm",
        file_specs=[f"src/allowed/cox2.py:create:{content_file}"],
    )
    kind = build_result["candidate"]["producer"]["kind"]
    assert kind == "codex-ox"
    assert kind not in ("codex", "codex-local")


def test_claude_codex_codex_ox_use_identical_intake_semantics(tmp_path):
    """Same generic helper, same acceptance outcome, differing only in the
    literal producer.kind string -- for claude-local, codex-local, and the
    newly registered codex-ox."""
    for agent_id in ("claude-local", "codex-local", "codex-ox"):
        root, task_id, head = _setup(tmp_path, name=f"repo-{agent_id}")
        agent_module.acquire_agent_lock(root, agent_id)
        content_file = _write_content(tmp_path, f"eq-{agent_id}.py", "print('eq')\n")
        build_result = intake.build_intake_candidate_from_files(
            root, task_id=task_id, candidate_id=f"cand-eq-{agent_id}",
            file_specs=[f"src/allowed/eq.py:create:{content_file}"],
        )
        assert build_result["errors"] == []
        assert build_result["candidate"]["producer"]["kind"] == agent_id
        assert build_result["candidate"]["producer"]["source"] == "agent_lock"
        result = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
        assert result["accepted"] is True
        assert result["execution_allowed"] is False
        assert result["promotion_executed"] is False


def test_arbitrary_custom_identity_still_works_alongside_codex_ox_registration(tmp_path):
    """Registering codex-ox must not narrow the governance lock's
    arbitrary-caller-supplied-string acceptance (W/W.1's guarantee)."""
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "some-other-unregistered-agent")
    content_file = _write_content(tmp_path, "custom.py", "x = 3\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-custom-still-works",
        file_specs=[f"src/allowed/custom.py:create:{content_file}"],
    )
    assert build_result["errors"] == []
    assert build_result["candidate"]["producer"]["kind"] == "some-other-unregistered-agent"


def test_no_lock_generic_intake_still_works_with_codex_ox_registered(tmp_path):
    """No-lock/direct generic intake (W/W.1's external-producer compatibility
    path) must remain unaffected by codex-ox's registry entries."""
    root, task_id, head = _setup(tmp_path)
    content_file = _write_content(tmp_path, "nolock.py", "x = 4\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-no-lock-still-works",
        file_specs=[f"src/allowed/nolock.py:create:{content_file}"],
        explicit_producer_kind="fully-external-producer",
    )
    assert build_result["errors"] == []
    producer = build_result["candidate"]["producer"]
    assert producer["kind"] == "fully-external-producer"
    assert producer["source"] == "candidate"


# ---------------------------------------------------------------------------
# Producer-to-authority non-flow, specifically for codex-ox
# ---------------------------------------------------------------------------

def test_codex_ox_producer_cannot_influence_authority_fields(tmp_path):
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "codex-ox")
    content_file = _write_content(tmp_path, "auth.py", "print('x')\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-codex-ox-authority",
        file_specs=[f"src/allowed/auth.py:create:{content_file}"],
    )
    candidate = build_result["candidate"]
    candidate["producer"]["execution_allowed"] = True
    candidate["producer"]["promotion_authorized"] = True
    result = intake.validate_and_ingest_intake_candidate(root, candidate)
    assert result["accepted"] is True
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False
    ecp = agent_module.lookup_execution_change_package(root, result["ecp_id"])
    assert ecp["execution_allowed"] is False
    assert ecp["promotion_executed"] is False


def test_codex_ox_scope_denial_identical_to_other_identities(tmp_path):
    root, task_id, head = _setup(tmp_path, name="repo-codex-ox-deny")
    agent_module.acquire_agent_lock(root, "codex-ox")
    content_file = _write_content(tmp_path, "bad-codex-ox.py", "print('bad')\n")
    build_result = intake.build_intake_candidate_from_files(
        root, task_id=task_id, candidate_id="cand-deny-codex-ox",
        file_specs=[f"src/forbidden/bad.py:create:{content_file}"],
    )
    result = intake.validate_and_ingest_intake_candidate(root, build_result["candidate"])
    assert result["accepted"] is False
    assert any("out_of_scope_path" in r for r in result["rejection_reasons"])


# ---------------------------------------------------------------------------
# No dedicated adapter / no native parser
# ---------------------------------------------------------------------------

def test_no_dedicated_codex_ox_intake_adapter_file_exists():
    repo_root = Path(__file__).resolve().parents[1]
    banned_names = (
        "codex_ox_intake_adapter.py",
        "codex_ox_adapter.py",
        "ox_intake_adapter.py",
        "ox_parser.py",
        "openrouter_adapter.py",
        "openrouter_parser.py",
    )
    matches = []
    for path in repo_root.rglob("*.py"):
        if "/.git/" in str(path) or "/__pycache__/" in str(path):
            continue
        if path.name in banned_names:
            matches.append(str(path))
    assert matches == []


def test_no_codex_ox_special_case_branch_in_generic_intake_module():
    """The shared generic intake helper must treat codex-ox exactly like
    any other agent_lock-derived producer -- no `if agent_id == "codex-ox"`
    (or equivalent) branch in the authority-relevant intake logic."""
    intake_source = (
        Path(__file__).resolve().parents[1] / "src" / "pcae" / "core" / "intake.py"
    ).read_text(encoding="utf-8")
    assert "codex-ox" not in intake_source
    assert "codex_ox" not in intake_source


# ---------------------------------------------------------------------------
# CLI end-to-end: pcae intake from-files with a codex-ox governance lock
# ---------------------------------------------------------------------------

def _run_cli(root_dir: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pcae", *args],
        cwd=root_dir, capture_output=True, text=True,
    )


def test_cli_from_files_end_to_end_with_codex_ox_lock(tmp_path):
    root, task_id, head = _setup(tmp_path)
    agent_module.acquire_agent_lock(root, "codex-ox")
    content_file = _write_content(tmp_path, "cli-codex-ox.py", "print('cli')\n")
    proc = _run_cli(
        root.path, "intake", "from-files",
        "--task-id", task_id, "--candidate-id", "cli-cand-codex-ox",
        "--file", f"src/allowed/cli-codex-ox.py:create:{content_file}",
        "--summary", "codex-ox cli test", "--json",
    )
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert out["accepted"] is True

    stored = intake.lookup_intake_record(root, out["intake_id"])
    assert stored["producer"]["kind"] == "codex-ox"
    assert stored["producer"]["source"] == "agent_lock"


# ---------------------------------------------------------------------------
# Runtime posture unchanged
# ---------------------------------------------------------------------------

def test_runtime_inspect_unaffected_by_codex_ox_registration(tmp_path, monkeypatch, capsys):
    init_harness(HarnessPath(tmp_path))
    monkeypatch.chdir(tmp_path)

    exit_code = main(["runtime", "inspect", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert data["state"]["current_state"] == "Observed"
    assert data["governance"]["execution_capability"] == "unavailable"
    assert data["governance"]["non_executing_posture"] is True
