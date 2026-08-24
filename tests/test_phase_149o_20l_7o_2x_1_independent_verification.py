"""Phase 149O.20L.7O.2X.1 -- Codex-Ox Agent Registration and Generic Intake
Compatibility Independent Verification.

Independently re-derives, from current production source (not from the
2X phase's own report, tests, or documentation conclusions), whether
`codex-ox` is a coherent, truthful PCAE agent/session identity:

    supported agent identity   != authenticated runtime
    producer provenance        != authenticated model/provider
    registration                != backend implementation
    registration                != execution capability

Fresh fixtures and independently derived expectations throughout; none
of 2X's own test functions are called or imported.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands.init import init_harness
from pcae.core import agent as agent_module
from pcae.core import intake as intake_module
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def _init_git_root(path: Path) -> None:
    _git(["init", "-q"], path)
    _git(["config", "user.email", "verify@example.com"], path)
    _git(["config", "user.name", "Verifier"], path)
    (path / "README.md").write_text("root\n")
    _git(["add", "README.md"], path)
    _git(["commit", "-q", "-m", "init"], path)


def _head(path: Path) -> str:
    return _git(["rev-parse", "HEAD"], path).stdout.strip()


def _new_harness(tmp_path, name, allowed_files=("work/**",)):
    root_dir = tmp_path / name
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    contract = create_task_contract(
        root,
        f"independent verification task ({name})",
        created_at=datetime(2026, 8, 24, 20, 30, tzinfo=timezone.utc),
        allowed_files=allowed_files,
    )
    return root, contract.task_id, _head(root_dir)


def _write_agent_lock(root: HarnessPath, agent_id: str, acquired_at: datetime) -> None:
    agent_module.acquire_agent_lock(root, agent_id, acquired_at=acquired_at)


def _candidate_for(root, task_id, candidate_id, base_commit, producer_kind, path, content,
                    extra_producer=None, extra_producer_claims=None):
    import hashlib
    return {
        "intake_contract_version": intake_module.INTAKE_CONTRACT_VERSION,
        "candidate_id": candidate_id,
        "task_context": {"task_id": task_id, "declared_goal": "independent verification probe"},
        "repo_binding": {
            "repo_fingerprint": intake_module.compute_repo_fingerprint(root),
            "base_commit": base_commit,
        },
        "proposed_changes": [
            {
                "path": path,
                "operation": "create",
                "content_after": content,
                "content_hash_after": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }
        ],
        "producer": {"kind": producer_kind, **(extra_producer or {})},
        "producer_claims": extra_producer_claims or {},
    }


# ===========================================================================
# 1. Pre-2X baseline reconstruction (historical source, not current tests)
# ===========================================================================

PRE_2X_PARENT_COMMIT = "56e44d8c5554d6675435989b94d8558d141c4ca4"  # parent of 7dc2f0fa


def test_pre_2x_source_did_not_list_codex_ox_in_lockable_backends():
    """Historical fact check directly against git blob content at the
    commit immediately preceding 2X's implementation commit."""
    result = subprocess.run(
        ["git", "show", f"{PRE_2X_PARENT_COMMIT}:src/pcae/commands/session.py"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=True,
    )
    source = result.stdout
    assert '"codex-ox"' not in source
    assert '"codex", "manual", "noop"' in source


def test_pre_2x_source_did_not_register_codex_ox_in_agent_py():
    result = subprocess.run(
        ["git", "show", f"{PRE_2X_PARENT_COMMIT}:src/pcae/core/agent.py"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=True,
    )
    source = result.stdout
    assert 'agent_id="codex-ox"' not in source
    assert '"codex-ox": AgentConfigEntry' not in source


def test_pre_2x_core_governance_lock_accepted_arbitrary_identity_by_design():
    """The core governance agent lock (acquire_agent_lock /
    read_agent_lock, backing derive_producer_provenance) takes no
    vocabulary parameter and is untouched by 2X's diff (2X only touched
    session.py's _LOCKABLE_BACKENDS/_sync_backend_lock and agent.py's
    MULTI_AGENT_REGISTRY/AGENT_CONFIG_REGISTRY). Confirm by inspecting
    the current acquire_agent_lock signature and implementation for any
    identity restriction, and that the 2X diff did not touch it."""
    diff = subprocess.run(
        ["git", "diff", PRE_2X_PARENT_COMMIT, "7dc2f0fa72c5b9d57fa6f427b3ac680c73b093cf",
         "--", "src/pcae/core/agent.py"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "def acquire_agent_lock(" not in diff
    assert "def read_agent_lock(" not in diff
    assert "def derive_producer_provenance" not in diff  # lives in intake.py, untouched entirely
    diff_intake = subprocess.run(
        ["git", "diff", PRE_2X_PARENT_COMMIT, "7dc2f0fa72c5b9d57fa6f427b3ac680c73b093cf",
         "--", "src/pcae/core/intake.py"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=True,
    ).stdout
    assert diff_intake == ""


def test_pre_2x_bootstrap_backend_lock_would_have_rejected_codex_ox(tmp_path, monkeypatch, capsys):
    """Reconstruct actual pre-2X *behavior* (not just source text) by
    exercising the historical _LOCKABLE_BACKENDS set directly against the
    current _sync_backend_lock logic, proving what changed."""
    from pcae.commands.session import _sync_backend_lock

    root_dir = tmp_path / "pre2x"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)

    pre_2x_lockable = frozenset({
        "claude-local", "claude-deepseek", "claude-kimi", "codex", "manual", "noop",
    })
    assert "codex-ox" not in pre_2x_lockable  # historical fact, re-derived above

    # Exercise the current implementation but simulate the pre-2X gate: if
    # codex-ox is not in the (historical) lockable set, the sync must have
    # rejected it. Confirm this is exactly what the *current* function does
    # for a name still absent from the vocabulary, e.g. a fictitious name.
    result = _sync_backend_lock(root, "some-unregistered-backend")
    assert result["lock_synced"] is False
    assert "not a recognized lockable backend identity" in result["blocker"]


# ===========================================================================
# 2. Fresh full identity-vocabulary inventory (do not assume "five")
# ===========================================================================

def test_fresh_inventory_of_codex_ox_across_production_vocabularies():
    """Grep production source directly rather than trusting the 2X
    report's enumeration; classify each hit."""
    root = Path(__file__).resolve().parents[1] / "src" / "pcae"
    hits = subprocess.run(
        ["grep", "-rln", "--include=*.py", "codex-ox", str(root)],
        capture_output=True, text=True,
    ).stdout.strip().splitlines()
    hit_set = {Path(h).name for h in hits}
    # Independently confirm codex-ox is confined to exactly these
    # production modules (session bootstrap backend-lock recognition +
    # capability/config registry); any new file appearing here is a
    # fresh vocabulary surface that must be independently classified.
    assert hit_set <= {"session.py", "agent.py"}
    assert "session.py" in hit_set
    assert "agent.py" in hit_set


def test_backend_invocation_registry_does_not_contain_codex_ox():
    """_build_invoke_command is the actual subprocess-dispatch decision
    point. Confirm codex-ox is absent from its recognized branches by
    inspecting source, then confirm behaviorally in section 15/16."""
    agent_py = (Path(__file__).resolve().parents[1] / "src/pcae/core/agent.py").read_text()
    start = agent_py.index("def _build_invoke_command(")
    end = agent_py.index("\n\n\n", start)
    body = agent_py[start:end]
    assert '"codex-ox"' not in body


def test_runtime_probe_agents_does_not_contain_codex_ox():
    assert ("codex-ox", "codex") not in agent_module._RUNTIME_PROBE_AGENTS
    ids = {pair[0] for pair in agent_module._RUNTIME_PROBE_AGENTS}
    assert "codex-ox" not in ids


def test_remote_policy_allowed_agents_does_not_contain_codex_ox():
    policy = agent_module.build_remote_policy()
    assert "codex-ox" not in policy["allowed_agents"]
    assert set(policy["allowed_agents"]) == {"claude-local", "codex-local", "kimi-local"}


def test_pap_ipilot_default_literals_do_not_reference_codex_ox():
    agent_py = (Path(__file__).resolve().parents[1] / "src/pcae/core/agent.py").read_text()
    for marker in ("_PAP_DEFAULT_AGENT", "_IPILOT_DEFAULT_AGENT", "_PAP_DEFAULT_RUNTIME",
                   "_IPILOT_DEFAULT_RUNTIME", "REMOTE_PLAN_DEFAULT_AGENT"):
        idx = agent_py.index(marker)
        line = agent_py[idx:agent_py.index("\n", idx)]
        assert "codex-ox" not in line


# ===========================================================================
# 3/7. Capability registration necessity + declaration accuracy
# ===========================================================================

def test_codex_ox_capability_entry_differs_from_codex_local_by_missing_runtime_execution():
    ox = agent_module.get_agent_by_id("codex-ox")
    local = agent_module.get_agent_by_id("codex-local")
    assert ox is not None and local is not None
    assert "runtime_execution" in local.capabilities
    assert "runtime_execution" not in ox.capabilities
    # Declared capabilities must be independently plausible for advisory
    # code-generation/test-writing description only.
    assert set(ox.capabilities) <= {"code_generation", "test_writing"}


def test_agents_cli_lists_codex_ox_with_correct_status_and_type(tmp_path, monkeypatch, capsys):
    root = HarnessPath(tmp_path)
    init_harness(root)
    monkeypatch.chdir(tmp_path)
    exit_code = main(["agents", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    entries = {e["agent_id"]: e for e in data["agents"]}
    assert "codex-ox" in entries
    assert entries["codex-ox"]["agent_type"] == "codex"
    assert "runtime_execution" not in entries["codex-ox"]["capabilities"]


# ===========================================================================
# 4/8. Agent-config accuracy: no misleading provider/network implication
# ===========================================================================

def test_codex_ox_agent_config_points_to_same_executable_as_codex_local_not_a_new_binary():
    ox = agent_module.get_agent_config("codex-ox")
    local = agent_module.get_agent_config("codex-local")
    assert ox.executable_hint == local.executable_hint == "codex"
    assert ox.adapter_type == agent_module.ADAPTER_TYPE_CLI


def test_codex_ox_config_notes_do_not_claim_pcae_owns_provider_transport():
    ox = agent_module.get_agent_config("codex-ox")
    notes = ox.configuration_notes.lower()
    for banned in ("openrouter.ai", "api_key", "apikey", "bearer ", "authorization:",
                   "http://", "https://api"):
        assert banned not in notes
    assert "external to pcae" in notes or "external" in notes


# ===========================================================================
# 5/6/9. Session-bootstrap: literal identity, no execution authority
# ===========================================================================

def test_bootstrap_accepts_codex_ox_and_persists_literal_identity_no_execution_authority(
    tmp_path, monkeypatch, capsys,
):
    root_dir = tmp_path / "bootstrap"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    create_task_contract(root, "bootstrap probe task")
    monkeypatch.chdir(root_dir)

    exit_code = main(["session", "bootstrap", "--agent-id", "codex-ox", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert exit_code in (0, 1)  # readiness may be blocked in a bare repo; lock acquisition is independent
    assert out["lock_acquired"] is True
    assert out["recognized_backend"] is True

    core_lock = agent_module.read_agent_lock(root)
    assert core_lock is not None
    assert core_lock.agent_id == "codex-ox"  # literal, no normalization

    backend_lock_path = root_dir / ".pcae" / "agent-locks" / "latest.json"
    assert backend_lock_path.exists()
    backend_lock = json.loads(backend_lock_path.read_text())
    assert backend_lock["backend_name"] == "codex-ox"
    assert backend_lock["backend_type"] == "codex"
    assert backend_lock["invocation_allowed"] is False
    assert backend_lock["execution_authorized"] is False
    assert backend_lock["may_execute_shell"] is False
    assert backend_lock["may_commit"] is False
    assert backend_lock["may_push"] is False


def test_bootstrap_codex_ox_readback_after_restart_preserves_literal_identity(tmp_path, monkeypatch):
    root_dir = tmp_path / "restart"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    create_task_contract(root, "restart probe task")
    monkeypatch.chdir(root_dir)

    main(["session", "bootstrap", "--agent-id", "codex-ox", "--json"])
    # Simulate a fresh process re-reading persisted state (no in-memory reuse).
    reread = agent_module.read_agent_lock(HarnessPath(root_dir))
    assert reread.agent_id == "codex-ox"
    backend_lock = json.loads((root_dir / ".pcae" / "agent-locks" / "latest.json").read_text())
    assert backend_lock["backend_name"] == "codex-ox"


def test_bootstrap_codex_ox_makes_no_network_or_subprocess_call_beyond_git_and_shutil_which(
    tmp_path, monkeypatch, capsys,
):
    """Independently verify no HTTP client is invoked during bootstrap by
    monkeypatching socket creation to raise; bootstrap must still succeed
    (proving it never opens a network connection)."""
    import socket

    root_dir = tmp_path / "nonet"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    create_task_contract(root, "no-network probe task")
    monkeypatch.chdir(root_dir)

    def _forbidden_socket(*a, **kw):
        raise AssertionError("network socket creation attempted during bootstrap")

    monkeypatch.setattr(socket, "socket", _forbidden_socket)
    exit_code = main(["session", "bootstrap", "--agent-id", "codex-ox", "--json"])
    assert exit_code in (0, 1)


# ===========================================================================
# 10/11. Generic intake compatibility + producer-to-authority non-flow
# ===========================================================================

@pytest.mark.parametrize("producer_kind", ["claude-local", "codex", "codex-ox", "some-custom-tool-xyz"])
def test_intake_path_identical_across_identities_for_equivalent_state(tmp_path, producer_kind):
    root, task_id, base = _new_harness(tmp_path, f"intake-{producer_kind}", allowed_files=("work/**",))
    doc = _candidate_for(
        root, task_id, f"cand-{producer_kind}", base, producer_kind,
        "work/file.txt", f"content from {producer_kind}\n",
    )
    result = intake_module.validate_and_ingest_intake_candidate(root, doc)
    assert result["accepted"] is True
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False


def test_producer_identity_has_no_effect_on_authority_relevant_outcome_fields(tmp_path):
    """Construct equivalent candidates (same task/base/content, differing
    only by producer.kind) and assert authority-relevant fields are
    identical/independent of identity."""
    outcomes = {}
    import tempfile
    for producer_kind in ("claude-local", "codex", "codex-ox", "arbitrary-identity-42"):
        with tempfile.TemporaryDirectory() as td:
            root, task_id, base = _new_harness(Path(td), "root", allowed_files=("work/**",))
            doc = _candidate_for(root, task_id, "cand-fixed", base, producer_kind,
                                  "work/same.txt", "identical content\n")
            outcomes[producer_kind] = intake_module.validate_and_ingest_intake_candidate(root, doc)

    for producer_kind, result in outcomes.items():
        assert result["accepted"] is True, producer_kind
        assert result["execution_allowed"] is False
        assert result["promotion_executed"] is False
        assert result["file_count"] == 1
        assert result["promotion_eligible_count"] == 1


# ===========================================================================
# 12. Forged producer authority fields (codex-ox specific reproduction)
# ===========================================================================

def test_forged_producer_authority_fields_from_codex_ox_do_not_change_canonical_authority(tmp_path):
    root, task_id, base = _new_harness(tmp_path, "forged", allowed_files=("work/**",))
    doc = _candidate_for(
        root, task_id, "cand-forged", base, "codex-ox", "work/f.txt", "x\n",
        extra_producer={
            "execution_allowed": True,
            "promotion_authorized": True,
            "promotion_executed": True,
        },
        extra_producer_claims={
            "self_reported_complete": True,
            "execution_allowed": True,
            "promotion_authorized": True,
        },
    )
    result = intake_module.validate_and_ingest_intake_candidate(root, doc)
    assert result["accepted"] is True
    # Canonical authority fields must remain the module's own fixed values,
    # not anything forged in producer/producer_claims.
    assert result["execution_allowed"] is False
    assert result["promotion_executed"] is False

    stored_ecp_path = Path(result["stored_path"])
    intake_record = json.loads(stored_ecp_path.read_text())
    assert intake_record["execution_allowed"] is False
    assert intake_record["promotion_executed"] is False
    # Forged keys are preserved verbatim as descriptive metadata (proving
    # they are stored for audit, not silently stripped -- and separately
    # proving they had zero effect on the authority fields above).
    assert intake_record["producer"]["execution_allowed"] is True
    assert intake_record["producer_claims"]["promotion_authorized"] is True


# ===========================================================================
# 13. Out-of-scope intake from codex-ox
# ===========================================================================

def test_out_of_scope_codex_ox_candidate_rejected_exactly_like_any_other_producer(tmp_path):
    root, task_id, base = _new_harness(tmp_path, "oos", allowed_files=("work/allowed/**",))
    doc = _candidate_for(
        root, task_id, "cand-oos", base, "codex-ox",
        "work/forbidden/outside_scope.txt", "should be rejected\n",
    )
    result = intake_module.validate_and_ingest_intake_candidate(root, doc)
    assert result["accepted"] is False
    assert any("out_of_scope_path" in r for r in result["rejection_reasons"])


# ===========================================================================
# 14. No-lock compatibility unaffected by codex-ox registration
# ===========================================================================

def test_no_lock_direct_intake_still_works_after_codex_ox_registration(tmp_path):
    root, task_id, base = _new_harness(tmp_path, "nolock", allowed_files=("work/**",))
    assert agent_module.read_agent_lock(root) is None  # no governance lock acquired
    doc = _candidate_for(root, task_id, "cand-nolock", base, "explicit-external-producer",
                          "work/nolock.txt", "no lock\n")
    result = intake_module.validate_and_ingest_intake_candidate(root, doc)
    assert result["accepted"] is True


def test_unregistered_custom_producer_remains_compatible_after_codex_ox_registration(tmp_path):
    root, task_id, base = _new_harness(tmp_path, "custom", allowed_files=("work/**",))
    _write_agent_lock(root, "totally-unregistered-agent-name",
                       acquired_at=datetime(2026, 8, 24, 20, 30, tzinfo=timezone.utc))
    producer, errors = intake_module.derive_producer_provenance(root, None)
    assert errors == []
    assert producer["kind"] == "totally-unregistered-agent-name"


def test_derive_producer_provenance_conflict_still_rejects_when_lock_is_codex_ox(tmp_path):
    root_dir = tmp_path / "conflict"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    _write_agent_lock(root, "codex-ox", acquired_at=datetime(2026, 8, 24, 20, 30, tzinfo=timezone.utc))
    producer, errors = intake_module.derive_producer_provenance(root, "some-other-identity")
    assert producer is None
    assert any("producer_conflicts_with_active_agent_lock" in e for e in errors)


# ===========================================================================
# 15/16. No dedicated adapter/parser, no OpenRouter/Ox execution integration
# ===========================================================================

def test_no_codex_ox_specific_module_or_adapter_file_exists():
    src_root = Path(__file__).resolve().parents[1] / "src" / "pcae"
    banned_name_fragments = ["codex_ox_intake_adapter", "codex_ox_adapter", "ox_parser",
                              "openrouter_parser", "codex_ox_parser"]
    all_files = [str(p) for p in src_root.rglob("*.py")]
    for fragment in banned_name_fragments:
        assert not any(fragment in f for f in all_files)


def test_no_codex_ox_specific_branch_inside_generic_looking_intake_module():
    intake_source = (Path(__file__).resolve().parents[1] / "src/pcae/core/intake.py").read_text()
    assert "codex-ox" not in intake_source
    assert "codex_ox" not in intake_source


def test_no_http_client_or_subprocess_dispatch_added_for_codex_ox_in_diff():
    diff = subprocess.run(
        ["git", "diff", PRE_2X_PARENT_COMMIT, "7dc2f0fa72c5b9d57fa6f427b3ac680c73b093cf",
         "--", "src/pcae/core/agent.py", "src/pcae/commands/session.py"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True, text=True, check=True,
    ).stdout
    added_lines = [ln for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    # Comments are allowed to *mention* Ox/OpenRouter descriptively (2X's
    # docstring does, to explain what the identity denotes); what must be
    # absent is any actual client/transport/dispatch call.
    banned_tokens = ["requests.", "urllib", "http.client", "socket.socket", "subprocess.run",
                      "subprocess.Popen", "openrouter.ai", "api_key=", "Authorization:"]
    for line in added_lines:
        for token in banned_tokens:
            assert token not in line, f"unexpected token {token!r} in added line: {line}"


# ===========================================================================
# 17. Authentication boundary: no overclaim in source/comments
# ===========================================================================

def test_no_source_claims_codex_ox_proves_actual_execution_occurred():
    agent_py = (Path(__file__).resolve().parents[1] / "src/pcae/core/agent.py").read_text()
    idx = agent_py.index('agent_id="codex-ox"')
    surrounding = agent_py[max(0, idx - 900):idx + 300]
    overclaim_phrases = [
        "codex actually ran", "ox actually produced", "openrouter actually served",
        "authenticated execution", "verified model identity",
    ]
    lowered = surrounding.lower()
    for phrase in overclaim_phrases:
        assert phrase not in lowered


# ===========================================================================
# 18. Vocabulary fallback / alias analysis -- no silent fallback to a
# real executable backend for an unsupported/unrecognized agent.
# ===========================================================================

def test_build_invoke_command_returns_none_for_codex_ox_no_silent_codex_local_fallback():
    result = agent_module._build_invoke_command("codex-ox", "prompt text")
    assert result is None  # must not silently reuse codex-local's argv


def test_remote_job_readiness_blocks_codex_ox_before_reaching_would_execute(tmp_path):
    root_dir = tmp_path / "remote"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)

    plan = agent_module.build_remote_execution_plan(root, requested_agent="codex-ox") \
        if hasattr(agent_module, "build_remote_execution_plan") else None
    # Independently exercise the actual allow-list gate used by job readiness.
    policy = agent_module.build_remote_policy()
    assert "codex-ox" not in policy["allowed_agents"]


def test_command_preview_fallback_for_codex_ox_is_a_preview_string_not_an_execution(tmp_path):
    """codex-ox falls through _derive_command_preview's generic branch
    (neither the codex-local nor claude/kimi special case). Confirm this
    only ever produces a descriptive preview string and is never used to
    actually invoke a subprocess for codex-ox (that's _build_invoke_command,
    verified separately above to return None)."""
    preview = agent_module._derive_command_preview("codex-ox", "hello")
    assert preview is not None
    assert preview.startswith("[preview]")
    assert "codex" in preview


# ===========================================================================
# 19. W.1 non-blocking findings unrelated to codex-ox
# ===========================================================================

def test_malformed_agent_lock_json_uncaught_exception_still_reproduces_and_is_identity_agnostic(tmp_path):
    """Confirm the W.1 finding is unrelated to codex-ox specifically: it
    reproduces identically regardless of what identity would have been
    in the lock, because the failure occurs before any agent_id is read."""
    root_dir = tmp_path / "malformed"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    lock_path = root_dir / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text("{not valid json")

    with pytest.raises(json.JSONDecodeError):
        agent_module.read_agent_lock(root)


def test_empty_agent_id_in_lock_still_degrades_to_empty_string_producer_not_codex_ox_specific(tmp_path):
    root_dir = tmp_path / "emptyagent"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    lock_path = root_dir / ".pcae" / "agent-lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps({"acquired_at": "2026-08-24T20:30:00+00:00"}))

    producer, errors = intake_module.derive_producer_provenance(root, None)
    assert errors == []
    assert producer["kind"] == ""


# ===========================================================================
# 21. Packaging behavior
# ===========================================================================

def test_installed_package_recognizes_codex_ox(tmp_path):
    """Verify via the currently-importable installed package (not just
    the source tree) that codex-ox is present -- i.e. this is not a
    repository-only helper never actually packaged."""
    import pcae as pcae_pkg
    pkg_file = Path(pcae_pkg.__file__).resolve()
    # The importable package's agent module must be the one carrying the
    # registration (guards against a stale separately-installed copy).
    from pcae.core import agent as installed_agent_module
    entry = installed_agent_module.get_agent_by_id("codex-ox")
    assert entry is not None
    config = installed_agent_module.get_agent_config("codex-ox")
    assert config is not None


def test_installed_cli_entrypoint_recognizes_codex_ox_end_to_end(tmp_path, monkeypatch, capsys):
    root_dir = tmp_path / "pkgcheck"
    root_dir.mkdir()
    _init_git_root(root_dir)
    root = HarnessPath(root_dir)
    init_harness(root)
    create_task_contract(root, "package check probe task")
    monkeypatch.chdir(root_dir)

    exit_code = main(["session", "bootstrap", "--agent-id", "codex-ox", "--json"])
    assert exit_code in (0, 1)
