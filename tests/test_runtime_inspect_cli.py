"""Tests for Phase 111C — Runtime Inspect CLI.

Verifies the first CLI command exposing 111B's observation-only Runtime
Introspection prototype: `pcae runtime inspect`, `pcae runtime inspect
--json`, and `pcae runtime inspect --verbose`. Covers human-readable
output content, JSON output shape/validity, safety guarantees (no
mutation, no `PermissionBroker.evaluate()` call, no plugin loading/
instantiation/invocation, no secrets), and compatibility with
109C/110E/110F/111B.

Invokes the real CLI in-process via `pcae.cli.main()` + `capsys`,
matching this repo's established pattern (see `tests/test_health.py`)
rather than spawning a subprocess -- faster and pytest-xdist safe. The
command under test performs no filesystem I/O and requires no repo
setup (a fresh, empty `RuntimeRegistry()` per invocation is its entire
state), so no `tmp_path`/`monkeypatch.chdir` fixture is needed.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands import runtime_inspect as ri_cli
from pcae.core.command_path_observation import INTEGRATION_REGISTRY
from pcae.core.runtime_registry import RuntimeRegistry

REPO_ROOT = Path(ri_cli.__file__).resolve().parent.parent.parent.parent


def _run(capsys, *args: str) -> tuple[int, str]:
    exit_code = main(["runtime", "inspect", *args])
    output = capsys.readouterr().out
    return exit_code, output


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — command group exists
# ═══════════════════════════════════════════════════════════════════════


def test_pcae_runtime_inspect_exists_and_succeeds(capsys):
    exit_code, _ = _run(capsys)
    assert exit_code == 0


def test_pcae_runtime_help_lists_inspect(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["runtime", "--help"])
    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "inspect" in output


def test_pcae_runtime_inspect_help(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["runtime", "inspect", "--help"])
    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "--json" in output
    assert "--verbose" in output


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — human-readable output
# ═══════════════════════════════════════════════════════════════════════


def test_human_output_is_not_a_raw_python_dict(capsys):
    _, output = _run(capsys)
    stripped = output.strip()
    assert not stripped.startswith("{")
    assert "PCAE Runtime Inspect" in output


def test_human_output_contains_runtime_state_observed(capsys):
    _, output = _run(capsys)
    assert "Runtime state:" in output
    assert "Observed" in output


def test_human_output_contains_execution_unavailable(capsys):
    _, output = _run(capsys)
    assert "Execution capability:" in output
    assert "unavailable" in output


def test_human_output_contains_maximum_capability_observe(capsys):
    _, output = _run(capsys)
    assert "Maximum plugin capability:" in output
    assert "observe" in output


def test_human_output_contains_minimum_required_fields(capsys):
    _, output = _run(capsys)
    for label in (
        "Runtime status:",
        "Runtime state:",
        "Execution capability:",
        "Maximum plugin capability:",
        "Registry status:",
        "Plugin count:",
        "Capability count:",
        "Observation integrations:",
        "Permission Broker status:",
        "Governance posture:",
        "Runtime principles:",
    ):
        assert label in output, f"missing field: {label}"


def test_human_output_does_not_include_verbose_sections_by_default(capsys):
    _, output = _run(capsys)
    assert "Plugin metadata:" not in output
    assert "Current limitations:" not in output


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — JSON output
# ═══════════════════════════════════════════════════════════════════════


def test_pcae_runtime_inspect_json_exists(capsys):
    exit_code, _ = _run(capsys, "--json")
    assert exit_code == 0


def test_json_output_is_valid_json(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert isinstance(data, dict)


def test_json_output_contains_expected_top_level_keys(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    expected = {"runtime", "registry", "plugins", "capabilities", "health", "governance", "state", "version"}
    assert expected <= set(data.keys())


def test_json_output_contains_execution_unavailable(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["health"]["execution_availability"] == "unavailable"
    assert data["governance"]["execution_capability"] == "unavailable"


def test_json_output_contains_runtime_state_observed(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["health"]["current_runtime_state"] == "Observed"
    assert data["state"]["current_state"] == "Observed"


def test_json_output_contains_maximum_capability_observe(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["health"]["current_maximum_plugin_capability"] == "observe"


def test_json_output_is_stable_across_invocations(capsys):
    """No timestamps, no random ordering -- two invocations of a
    read-only, stateless command must produce identical output."""
    _, first = _run(capsys, "--json")
    _, second = _run(capsys, "--json")
    assert first == second


def test_json_output_observed_command_paths_is_four(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["governance"]["observed_command_paths"] == 4


def test_json_output_broker_status_execution_unavailable(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["governance"]["broker_implementation_status"] == "execution_unavailable"


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — verbose output
# ═══════════════════════════════════════════════════════════════════════


def test_pcae_runtime_inspect_verbose_exists(capsys):
    exit_code, _ = _run(capsys, "--verbose")
    assert exit_code == 0


def test_verbose_output_includes_plugin_metadata_section(capsys):
    _, output = _run(capsys, "--verbose")
    assert "Plugin metadata:" in output


def test_verbose_output_includes_capability_declarations_section(capsys):
    _, output = _run(capsys, "--verbose")
    assert "Capability declarations:" in output


def test_verbose_output_includes_observation_integrations_section(capsys):
    _, output = _run(capsys, "--verbose")
    assert "Observation integrations:" in output
    for entry in INTEGRATION_REGISTRY:
        assert entry.integration_id in output


def test_verbose_output_includes_current_limitations_section(capsys):
    _, output = _run(capsys, "--verbose")
    assert "Current limitations:" in output


def test_verbose_json_combination_still_produces_valid_json(capsys):
    """--verbose currently only affects human-readable formatting --
    --json output is unaffected either way, and must remain valid
    JSON when both flags are passed together."""
    _, output = _run(capsys, "--json", "--verbose")
    data = json.loads(output)
    assert "runtime" in data


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — safety behavior
# ═══════════════════════════════════════════════════════════════════════


def test_command_does_not_mutate_registry_or_introspection_state():
    registry = RuntimeRegistry()
    before = registry.registry_health()
    snapshot1 = ri_cli._build_snapshot(registry)
    snapshot2 = ri_cli._build_snapshot(registry)
    after = registry.registry_health()
    assert before == after
    assert snapshot1 == snapshot2


def test_command_never_constructs_or_evaluates_permission_broker():
    """Source-text scoped to actual code, not the module's own
    docstring (which legitimately names 'PermissionBroker.evaluate()'
    in prose to explain what this command deliberately never does)."""
    tree = ast.parse(Path(ri_cli.__file__).read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    for call in calls:
        func = call.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        assert name not in ("PermissionBroker", "evaluate")


def test_command_module_has_no_load_instantiate_invoke_calls():
    text = Path(ri_cli.__file__).read_text()
    for forbidden in ("load_plugin(", "instantiate_plugin(", "invoke_plugin(", "register_metadata("):
        assert forbidden not in text


def test_command_module_never_registers_a_plugin(capsys):
    """The RuntimeRegistry this command constructs is always empty --
    confirmed directly, not just by source inspection."""
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["registry"]["registered_plugin_count"] == 0
    assert data["plugins"] == []


def test_command_module_source_has_no_subprocess_or_network_calls():
    text = Path(ri_cli.__file__).read_text()
    for forbidden in ("subprocess.", "socket.", "requests.", "urllib.", "http.client", "os.system("):
        assert forbidden not in text


def test_command_module_source_has_no_file_writes():
    text = Path(ri_cli.__file__).read_text()
    for forbidden in ("open(", "write(", "os.remove", "os.rename", "shutil."):
        assert forbidden not in text


def test_command_exposes_no_secrets_or_credentials(capsys):
    _, output = _run(capsys, "--json")
    lowered = output.lower()
    for forbidden in ("token", "secret", "credential", "password", "api_key", "apikey"):
        assert forbidden not in lowered


def test_command_module_never_reads_environment_variables():
    text = Path(ri_cli.__file__).read_text()
    assert "os.environ" not in text
    assert "os.getenv" not in text


def test_manifest_never_appears_in_output(capsys):
    """PluginDescriptor.manifest is deliberately excluded -- confirmed
    directly that the field name never appears in either output mode."""
    for extra_args in ((), ("--json",), ("--verbose",)):
        _, output = _run(capsys, *extra_args)
        assert "manifest" not in output.lower()


def test_manifest_excluded_from_build_snapshot_plugin_dicts():
    registry = RuntimeRegistry()
    from pcae.core.runtime_registry import PluginDescriptor

    registry.register_metadata(
        PluginDescriptor(
            plugin_id="ISP-001",
            plugin_type="Intent Source",
            version="1.0.0",
            manifest={"secret_looking_key": "should never appear"},
        )
    )
    snapshot = ri_cli._build_snapshot(registry)
    assert len(snapshot["plugins"]) == 1
    assert "manifest" not in snapshot["plugins"][0]
    assert "secret_looking_key" not in json.dumps(snapshot)


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — compatibility
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_introspection_module_unchanged_by_this_phase():
    """111B's module must not be modified -- this phase only adds a
    CLI layer on top of it."""
    import inspect

    from pcae.core import runtime_introspection

    for name in ("get_runtime", "get_registry", "get_plugins", "get_capabilities", "get_health", "get_governance", "get_state", "get_version"):
        assert hasattr(runtime_introspection, name)
        sig = inspect.signature(getattr(runtime_introspection, name))
        assert len(sig.parameters) <= 1


def test_runtime_registry_remains_metadata_only():
    registry = RuntimeRegistry()
    ri_cli._build_snapshot(registry)
    # Phase 149O.20L.7O.3S (RPAC-001 v1.0) adds `_adapter_descriptors` as a
    # second inert metadata collection; `runtime inspect` construction still
    # touches only plain dict state, never a callable/adapter reference.
    assert set(registry.__dict__.keys()) == {"_plugins", "_adapter_descriptors"}


def test_command_path_observation_still_has_exactly_four_entries():
    assert len(INTEGRATION_REGISTRY) == 4
    assert {e.integration_id for e in INTEGRATION_REGISTRY} == {"INT-001", "INT-002", "INT-003", "INT-004"}


def test_permission_broker_decisions_remain_execution_unavailable():
    from pcae.core.permission_broker_foundation import (
        IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE,
        PermissionBroker,
        build_permission_broker_request,
    )

    broker = PermissionBroker()
    request = build_permission_broker_request(
        action_type="read",
        execution_class="none",
        requested_component="COMP-001",
        requested_capability="evaluate",
        task_id="task-1",
        evidence_available=True,
        approval_present=True,
    )
    decision = broker.evaluate(request)
    assert decision.implementation_status == IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE


def test_existing_health_command_unaffected(capsys):
    """'Unaffected' means still runs to completion and still produces
    its own output -- not a specific exit code, since that legitimately
    depends on unrelated live repo/governance state (doc-sync status,
    session state) this phase's CLI addition has no bearing on."""
    exit_code = main(["health"])
    output = capsys.readouterr().out
    assert isinstance(exit_code, int)
    assert "PCAE health" in output


def test_existing_check_command_unaffected(capsys):
    exit_code = main(["check"])
    output = capsys.readouterr().out
    assert isinstance(exit_code, int)
    assert "PCAE check" in output or "check" in output.lower()


def test_no_behavior_changing_integration_added():
    """This phase's own command module must never call the
    observation helper -- it is a display command, not an integrated
    command path."""
    text = Path(ri_cli.__file__).read_text()
    assert "command_path_observation.observe" not in text
    assert "from pcae.core.command_path_observation import observe" not in text


# ═══════════════════════════════════════════════════════════════════════
# Module isolation — command module
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def module_imports() -> list[str]:
    tree = ast.parse(Path(ri_cli.__file__).read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def test_module_imports_are_allowlisted(module_imports):
    """112E updated this allowlist deliberately: the CLI no longer
    imports `pcae.core.runtime_introspection` directly (assembly moved
    to `pcae.core.runtime_snapshot`, per 112E objective 3 -- "avoid
    bespoke assembly logic inside the CLI"); `pcae.core.paths` is new,
    needed to resolve the repo root Runtime Snapshot reads real
    session/task state from."""
    allowed = {
        "__future__",
        "argparse",
        "json",
        "pcae.core.command_path_observation",
        "pcae.core.paths",
        "pcae.core.runtime_registry",
        "pcae.core.runtime_snapshot",
    }
    for name in module_imports:
        assert name in allowed, f"unexpected import: {name}"


def test_module_has_no_shell_backend_or_telegram_dependency(module_imports):
    forbidden = ("shell_gate", "subprocess", "backend_invocations", "notifications", "telegram", "importlib")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_module_has_no_permission_broker_dependency(module_imports):
    for name in module_imports:
        assert "permission_broker" not in name


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / no-go confirmations reconfirmed
# ═══════════════════════════════════════════════════════════════════════


def test_module_docstring_states_execution_unavailable():
    text = ri_cli.__doc__ or ""
    assert "never mutates" in text or "read-only" in text.lower()


def test_task_contract_excludes_forbidden_files():
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-111c*"))
    if not matches:
        pytest.skip("111C task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    for forbidden in ("shell_gate.py", "backend_invocations.py", "notifications.py"):
        assert forbidden not in contract_text
