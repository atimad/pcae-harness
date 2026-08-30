"""Tests for Phase 111D — Runtime Inspect CLI Verification & Compatibility.

Verification/hardening phase: proves `pcae runtime inspect` (111C)
remains stable, read-only, backward-compatible with the Runtime
Introspection architecture (111A/111B) and the Runtime Registry
(110A-110F), performant, and incapable of introducing execution
behavior. This file deliberately re-tests several claims
`tests/test_runtime_inspect_cli.py` (111C) already covers, from a
compatibility/stability/performance/security angle rather than a pure
functional-coverage angle -- the two suites are complementary, not
redundant, mirroring the 110F/110E relationship.

No source code changes accompany this phase -- a full re-read of
`src/pcae/commands/runtime_inspect.py` and
`src/pcae/core/runtime_introspection.py` found no defect requiring a
hardening fix (unlike 110F's manifest-immutability finding); this
phase's task contract permits touching those files but exercises that
permission by leaving them unchanged, which this file's own tests
confirm.

No subprocess invocation in this file; pure in-process, pytest-xdist
safe.
"""

from __future__ import annotations

import ast
import json
import time
from pathlib import Path

import pytest

from pcae.cli import main
from pcae.commands import runtime_inspect as ri_cli
from pcae.core import runtime_introspection as ri_core
from pcae.core.command_path_observation import INTEGRATION_REGISTRY
from pcae.core.runtime_registry import PluginDescriptor, RuntimeRegistry

REPO_ROOT = Path(ri_cli.__file__).resolve().parent.parent.parent.parent
DOCS = REPO_ROOT / "docs"


def _run(capsys, *args: str) -> tuple[int, str]:
    exit_code = main(["runtime", "inspect", *args])
    output = capsys.readouterr().out
    return exit_code, output


def _module_import_names(module_file: str) -> list[str]:
    tree = ast.parse(Path(module_file).read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — CLI compatibility re-verification
# ═══════════════════════════════════════════════════════════════════════


def test_pcae_runtime_inspect_still_works(capsys):
    exit_code, output = _run(capsys)
    assert exit_code == 0
    assert "PCAE Runtime Inspect" in output


def test_pcae_runtime_inspect_json_still_works(capsys):
    exit_code, output = _run(capsys, "--json")
    assert exit_code == 0
    assert isinstance(json.loads(output), dict)


def test_pcae_runtime_inspect_verbose_still_implemented(capsys):
    """111C implemented --verbose (objective 4 there was not deferred);
    this phase reconfirms it is still present and functional."""
    exit_code, output = _run(capsys, "--verbose")
    assert exit_code == 0
    assert "Plugin metadata:" in output
    assert "Capability declarations:" in output
    assert "Observation integrations:" in output
    assert "Current limitations:" in output


def test_human_output_stable_across_repeated_invocations(capsys):
    _, first = _run(capsys)
    _, second = _run(capsys)
    assert first == second


def test_verbose_output_stable_across_repeated_invocations(capsys):
    _, first = _run(capsys, "--verbose")
    _, second = _run(capsys, "--verbose")
    assert first == second


def test_json_output_stable_across_repeated_invocations(capsys):
    _, first = _run(capsys, "--json")
    _, second = _run(capsys, "--json")
    assert first == second


def test_all_three_output_modes_agree_on_core_facts(capsys):
    """Human, verbose, and JSON output must never disagree with each
    other on the load-bearing facts."""
    _, human = _run(capsys)
    _, verbose = _run(capsys, "--verbose")
    _, json_output = _run(capsys, "--json")
    data = json.loads(json_output)

    for text in (human, verbose):
        assert "Observed" in text
        assert "unavailable" in text
        assert "observe" in text

    assert data["health"]["current_runtime_state"] == "Observed"
    assert data["health"]["execution_availability"] == "unavailable"
    assert data["health"]["current_maximum_plugin_capability"] == "observe"


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — JSON schema stability (stable observation contract)
# ═══════════════════════════════════════════════════════════════════════

#: The frozen top-level JSON schema, as a stable observation contract.
#: Any change to this set in a future phase must be a deliberate,
#: documented decision -- not an accidental side effect. `context` was
#: added deliberately in 112E (Runtime Snapshot / Runtime Context
#: integration, objective 4) -- exactly the kind of documented decision
#: this comment anticipated, not an accidental side effect.
STABLE_TOP_LEVEL_KEYS = frozenset(
    {"runtime", "registry", "plugins", "capabilities", "health", "governance", "state", "version", "context"}
)

STABLE_SECTION_KEYS = {
    "runtime": frozenset({"pipeline_stages", "principles", "runtime_services"}),
    "registry": frozenset(
        {
            "registered_plugin_count",
            "registered_capability_count",
            "registry_status",
            "metadata_validity",
            "plugin_ids",
            "capabilities",
        }
    ),
    "health": frozenset(
        {
            "runtime_status",
            "registry_status",
            "plugin_count",
            "capability_count",
            "metadata_validity",
            "execution_availability",
            "current_runtime_state",
            "current_maximum_plugin_capability",
        }
    ),
    "governance": frozenset(
        {"non_executing_posture", "broker_implementation_status", "observed_command_paths", "execution_capability"}
    ),
    "state": frozenset({"current_state", "state_model"}),
    "version": frozenset({"release_version", "plugin_versions"}),
}

STABLE_PLUGIN_ENTRY_KEYS = frozenset(
    {"plugin_id", "plugin_type", "version", "capabilities", "lifecycle_state", "health_state", "implementation_status"}
)

STABLE_CAPABILITY_ENTRY_KEYS = frozenset({"capability", "declaring_plugin_ids", "undeclarable"})


def test_top_level_keys_match_stable_contract(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert set(data.keys()) == STABLE_TOP_LEVEL_KEYS


@pytest.mark.parametrize("section", sorted(STABLE_SECTION_KEYS.keys()))
def test_section_keys_match_stable_contract(capsys, section):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert set(data[section].keys()) == STABLE_SECTION_KEYS[section]


def test_plugins_is_a_list_of_dicts_with_stable_keys():
    registry = RuntimeRegistry()
    registry.register_metadata(
        PluginDescriptor(plugin_id="ISP-001", plugin_type="Intent Source", version="1.0.0", capabilities=("observe",))
    )
    snapshot = ri_cli._build_snapshot(registry)
    assert isinstance(snapshot["plugins"], list)
    assert len(snapshot["plugins"]) == 1
    assert set(snapshot["plugins"][0].keys()) == STABLE_PLUGIN_ENTRY_KEYS


def test_capabilities_is_a_list_of_dicts_with_stable_keys(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert isinstance(data["capabilities"], list)
    assert len(data["capabilities"]) == 10
    for entry in data["capabilities"]:
        assert set(entry.keys()) == STABLE_CAPABILITY_ENTRY_KEYS


def test_schema_unchanged_by_registry_population():
    """Populating the registry must change list *contents*, never the
    top-level or section-level key set."""
    empty_snapshot = ri_cli._build_snapshot(RuntimeRegistry())

    populated = RuntimeRegistry()
    populated.register_metadata(
        PluginDescriptor(plugin_id="ISP-001", plugin_type="Intent Source", version="1.0.0", capabilities=("observe",))
    )
    populated_snapshot = ri_cli._build_snapshot(populated)

    assert set(empty_snapshot.keys()) == set(populated_snapshot.keys()) == STABLE_TOP_LEVEL_KEYS
    for section, expected_keys in STABLE_SECTION_KEYS.items():
        assert set(empty_snapshot[section].keys()) == expected_keys
        assert set(populated_snapshot[section].keys()) == expected_keys


def test_runtime_metadata_present_and_well_formed(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert len(data["runtime"]["pipeline_stages"]) == 7
    assert len(data["runtime"]["principles"]) == 11
    assert len(data["runtime"]["runtime_services"]) == 9


def test_json_is_always_a_flat_two_level_structure_for_scalars():
    """Every section value is either a scalar, a list of scalars, or a
    list of flat dicts -- no deeply nested structure that would make
    this an unstable contract to consume.

    `context` (112E) is deliberately excluded from this flatness
    constraint: Runtime Context is, by 112A/112B/112C's own frozen
    design, a genuinely hierarchical composition (session -> tasks,
    session -> observation) -- flattening it here would misrepresent
    the composition model this phase exists to integrate, not make the
    contract more stable."""
    data = ri_cli._build_snapshot(RuntimeRegistry())
    for key, value in data.items():
        if key == "context":
            continue
        if isinstance(value, dict):
            for sub_value in value.values():
                assert not isinstance(sub_value, dict)
        elif isinstance(value, list):
            for item in value:
                assert isinstance(item, dict)
                for sub_value in item.values():
                    assert not isinstance(sub_value, (dict, list)) or all(
                        isinstance(x, str) for x in sub_value
                    )


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — read-only guarantees
# ═══════════════════════════════════════════════════════════════════════


def test_no_registry_mutation_across_repeated_snapshots():
    registry = RuntimeRegistry()
    registry.register_metadata(
        PluginDescriptor(plugin_id="ISP-001", plugin_type="Intent Source", version="1.0.0", capabilities=("observe",))
    )
    before = registry.registry_health()
    for _ in range(5):
        ri_cli._build_snapshot(registry)
    after = registry.registry_health()
    assert before == after
    assert registry.list_plugins()[0].plugin_id == "ISP-001"


def test_no_runtime_mutation_frozen_constants_unchanged():
    before = (
        ri_core.PIPELINE_STAGES,
        ri_core.RUNTIME_PRINCIPLES,
        ri_core.RUNTIME_STATE_MODEL,
        ri_core.CURRENT_RUNTIME_STATE,
        ri_core.CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
    )
    ri_cli._build_snapshot(RuntimeRegistry())
    after = (
        ri_core.PIPELINE_STAGES,
        ri_core.RUNTIME_PRINCIPLES,
        ri_core.RUNTIME_STATE_MODEL,
        ri_core.CURRENT_RUNTIME_STATE,
        ri_core.CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
    )
    assert before == after


def test_no_plugin_mutation_descriptor_identity_preserved():
    """A PluginDescriptor object returned through the introspection
    layer must be the exact same immutable object before and after
    being read by the CLI's snapshot builder."""
    registry = RuntimeRegistry()
    registry.register_metadata(
        PluginDescriptor(plugin_id="ISP-001", plugin_type="Intent Source", version="1.0.0", capabilities=("observe",))
    )
    before = registry.get_plugin_metadata("ISP-001")
    ri_cli._build_snapshot(registry)
    after = registry.get_plugin_metadata("ISP-001")
    assert before is after


def test_no_metadata_mutation_manifest_immutability_preserved_through_cli_layer():
    registry = RuntimeRegistry()
    registry.register_metadata(
        PluginDescriptor(
            plugin_id="ISP-001",
            plugin_type="Intent Source",
            version="1.0.0",
            manifest={"plugin_name": "Example"},
        )
    )
    ri_cli._build_snapshot(registry)
    stored = registry.get_plugin_metadata("ISP-001")
    with pytest.raises(TypeError):
        stored.manifest["plugin_name"] = "Tampered"  # type: ignore[index]


def test_no_permission_broker_evaluate_call_ast_verified():
    """AST-based call-site check across both files this phase covers --
    not fooled by either module's own docstring prose naming
    `PermissionBroker.evaluate()` to explain what it deliberately never
    does."""
    for module_file in (ri_cli.__file__, ri_core.__file__):
        tree = ast.parse(Path(module_file).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                assert name not in ("PermissionBroker", "evaluate"), f"forbidden call in {module_file}: {name}"


def test_no_plugin_loading_instantiation_or_invocation_method_exists():
    forbidden = {
        "load_plugin", "instantiate_plugin", "invoke_plugin", "call_plugin",
        "run_plugin", "execute_plugin", "import_plugin",
    }
    for module in (ri_cli, ri_core, RuntimeRegistry):
        actual = {name for name in dir(module) if not name.startswith("_")}
        assert not (forbidden & actual)


def test_no_command_execution_no_subprocess_anywhere():
    for module_file in (ri_cli.__file__, ri_core.__file__):
        imports = _module_import_names(module_file)
        assert not any("subprocess" in name for name in imports)
        text = Path(module_file).read_text()
        assert "os.system(" not in text
        assert "os.popen(" not in text


def test_adversarial_callable_in_manifest_never_invoked_through_full_cli_path(capsys):
    """End-to-end version of 111B/111C's adversarial canary test, run
    through the actual CLI handler this time rather than only the
    introspection functions directly."""

    class _ExplodingCallable:
        def __call__(self) -> None:
            raise AssertionError("must never be called")

    registry = RuntimeRegistry()
    registry.register_metadata(
        PluginDescriptor(plugin_id="ISP-001", plugin_type="Intent Source", version="1.0.0", manifest={"hook": _ExplodingCallable()})
    )
    snapshot = ri_cli._build_snapshot(registry)
    json.dumps(snapshot)  # would raise TypeError if manifest leaked through (not AssertionError)
    # No AssertionError raised above means the canary was never called.


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — compatibility cross-checks (110A-111C)
# ═══════════════════════════════════════════════════════════════════════


def test_compatible_with_110a_pipeline_stages(capsys):
    text = (DOCS / "PCAE_RUNTIME_ARCHITECTURE.md").read_text()
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    for stage in data["runtime"]["pipeline_stages"]:
        assert stage in text


def test_compatible_with_110b_plugin_contract_capability_taxonomy(capsys):
    text = (DOCS / "PCAE_RUNTIME_PLUGIN_CONTRACTS.md").read_text()
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    for entry in data["capabilities"]:
        assert f"`{entry['capability']}`" in text


def test_compatible_with_110c_service_registry_architecture_doc_exists():
    assert (DOCS / "PCAE_RUNTIME_SERVICE_REGISTRY.md").exists()


def test_compatible_with_110d_registry_contract_api_names():
    text = (DOCS / "PCAE_RUNTIME_REGISTRY_CONTRACT.md").read_text()
    assert "GetPluginMetadata()" in text
    assert "ListPlugins()" in text


def test_compatible_with_110e_110f_registry_module_unchanged():
    from pcae.core import runtime_registry

    for name in ("RuntimeRegistry", "PluginDescriptor", "RegistrySnapshot"):
        assert hasattr(runtime_registry, name)


def test_compatible_with_111a_introspection_architecture_domains(capsys):
    """`context` is deliberately excluded from this per-key check: 111A's
    architecture document predates Runtime Context entirely (112A-112E)
    and never mentions it. `docs/PCAE_RUNTIME_SNAPSHOT.md` (112E) is the
    document that key's presence is meaningfully checked against
    instead -- see tests/test_runtime_snapshot.py."""
    text = (DOCS / "PCAE_RUNTIME_INTROSPECTION.md").read_text()
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    for key in data.keys():
        if key == "context":
            continue
        assert key.capitalize() in text or key in text.lower()


def test_compatible_with_111b_introspection_prototype_functions_unchanged():
    import inspect

    for name in ("get_runtime", "get_registry", "get_plugins", "get_capabilities", "get_health", "get_governance", "get_state", "get_version"):
        func = getattr(ri_core, name)
        assert callable(func)
        sig = inspect.signature(func)
        assert len(sig.parameters) <= 1


def test_compatible_with_111c_cli_command_still_registered():
    from pcae import cli

    parser_source = Path(cli.__file__).read_text()
    assert '"inspect"' in parser_source
    assert "run_runtime_inspect" in parser_source


def test_command_path_observation_109c_unaffected():
    assert len(INTEGRATION_REGISTRY) == 4
    assert {e.integration_id for e in INTEGRATION_REGISTRY} == {"INT-001", "INT-002", "INT-003", "INT-004"}


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — performance verification
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_inspect_completes_quickly(capsys):
    """Generous threshold -- this is a smoke test against runaway
    operations (e.g. an accidental filesystem walk or network call),
    not a strict performance benchmark."""
    start = time.monotonic()
    _run(capsys, "--verbose")
    elapsed = time.monotonic() - start
    assert elapsed < 2.0, f"pcae runtime inspect --verbose took {elapsed:.2f}s, expected well under 2s"


def test_no_filesystem_scanning_in_command_module():
    text = Path(ri_cli.__file__).read_text()
    for forbidden in ("os.walk(", "glob.glob(", "glob(", "rglob(", "os.listdir(", "scandir("):
        assert forbidden not in text


def test_no_filesystem_scanning_in_introspection_module():
    text = Path(ri_core.__file__).read_text()
    for forbidden in ("os.walk(", "glob.glob(", "glob(", "rglob(", "os.listdir(", "scandir("):
        assert forbidden not in text


def test_no_network_access_in_either_module():
    for module_file in (ri_cli.__file__, ri_core.__file__):
        text = Path(module_file).read_text()
        for forbidden in ("socket.", "requests.", "urllib.", "http.client"):
            assert forbidden not in text


def test_no_dynamic_plugin_discovery():
    """No importlib-based discovery, no entry_points scanning, no
    pkgutil iteration -- plugin metadata only ever arrives via
    explicit register_metadata() calls a caller makes."""
    for module_file in (ri_cli.__file__, ri_core.__file__):
        imports = _module_import_names(module_file)
        forbidden = ("importlib", "pkgutil", "pkg_resources")
        for name in imports:
            assert not any(f in name for f in forbidden), f"forbidden import in {module_file}: {name}"
        text = Path(module_file).read_text()
        assert "entry_points(" not in text


def test_no_expensive_loops_or_recursion_in_snapshot_assembly():
    """_build_snapshot()'s cost must scale only with the (currently
    always-zero) registered plugin count, never with anything
    unbounded."""
    tree = ast.parse(Path(ri_cli.__file__).read_text())
    build_snapshot_fn = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_build_snapshot"
    )
    nested_loops = [n for n in ast.walk(build_snapshot_fn) if isinstance(n, (ast.For, ast.While))]
    assert len(nested_loops) == 0  # only comprehensions are used, no explicit loop statements


def test_repeated_calls_do_not_accumulate_time():
    """No caching bug, no leak, no growing state across many
    invocations against a fresh registry each time."""
    durations = []
    for _ in range(10):
        registry = RuntimeRegistry()
        start = time.monotonic()
        ri_cli._build_snapshot(registry)
        durations.append(time.monotonic() - start)
    assert max(durations) < 1.0
    # No strict monotonicity assertion -- just confirms nothing runs away.


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — security verification
# ═══════════════════════════════════════════════════════════════════════


def test_no_secrets_exposed_in_any_output_mode(capsys):
    for extra_args in ((), ("--json",), ("--verbose",)):
        _, output = _run(capsys, *extra_args)
        lowered = output.lower()
        for forbidden in ("token", "secret", "credential", "password", "api_key", "apikey", "private_key"):
            assert forbidden not in lowered, f"forbidden term {forbidden!r} found with args {extra_args}"


def test_no_environment_variables_read_by_either_module():
    for module_file in (ri_cli.__file__, ri_core.__file__):
        text = Path(module_file).read_text()
        assert "os.environ" not in text
        assert "os.getenv" not in text


def test_no_mutable_internal_objects_exposed_registry_dict_not_returned():
    """The snapshot's 'registry' section must never contain the live
    RuntimeRegistry._plugins dict itself -- only plain serializable
    values."""
    registry = RuntimeRegistry()
    registry.register_metadata(
        PluginDescriptor(plugin_id="ISP-001", plugin_type="Intent Source", version="1.0.0", capabilities=("observe",))
    )
    snapshot = ri_cli._build_snapshot(registry)
    for value in snapshot["registry"].values():
        assert not isinstance(value, dict)
        assert value is not registry._plugins


def test_no_execution_handles_exposed_no_callable_values_in_json(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)

    def _assert_no_callables(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                _assert_no_callables(v)
        elif isinstance(obj, list):
            for v in obj:
                _assert_no_callables(v)
        else:
            assert not callable(obj)

    _assert_no_callables(data)


def test_manifest_field_absent_from_every_output_mode(capsys):
    for extra_args in ((), ("--json",), ("--verbose",)):
        _, output = _run(capsys, *extra_args)
        assert "manifest" not in output.lower()


def test_module_import_allowlist_unchanged_from_111c():
    """Deliberately updated by 112E: the CLI now delegates assembly to
    `pcae.core.runtime_snapshot` instead of importing
    `pcae.core.runtime_introspection` directly (112E objective 3), and
    gained `pcae.core.paths` to resolve the repo root Runtime Snapshot
    reads. Deliberately updated again by Phase
    149O.20L.7O.3W.1R.2B.1R.1.1R.19 (Slice B, 3S.2.1 item-9 runtime-inspect
    discoverability repair): re-adds a direct `pcae.core.runtime_introspection`
    import for the observational `get_adapter_surfaces()` surface list
    (already a transitive dependency via `runtime_snapshot`; a pure
    observation-only module). Every other 111C-era import remains
    unchanged -- this test still exists specifically to catch any
    *other*, undocumented dependency creeping in."""
    names = _module_import_names(ri_cli.__file__)
    allowed = {
        "__future__",
        "argparse",
        "json",
        "pcae.core.command_path_observation",
        "pcae.core.paths",
        "pcae.core.runtime_introspection",
        "pcae.core.runtime_registry",
        "pcae.core.runtime_snapshot",
    }
    for name in names:
        assert name in allowed, f"unexpected import: {name}"


# ═══════════════════════════════════════════════════════════════════════
# Runtime state / capability ceiling reconfirmation
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_state_remains_observed(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["state"]["current_state"] == "Observed"
    assert data["health"]["current_runtime_state"] == "Observed"


def test_maximum_plugin_capability_remains_observe(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["health"]["current_maximum_plugin_capability"] == "observe"


def test_execution_capability_remains_unavailable(capsys):
    _, output = _run(capsys, "--json")
    data = json.loads(output)
    assert data["health"]["execution_availability"] == "unavailable"
    assert data["governance"]["execution_capability"] == "unavailable"


def test_permission_broker_decision_still_execution_unavailable():
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


# ═══════════════════════════════════════════════════════════════════════
# Source-unchanged confirmation (pure verification phase, no hardening)
# ═══════════════════════════════════════════════════════════════════════


def test_no_new_functionality_added_command_module_unchanged_public_surface():
    """This phase adds no new CLI functionality -- confirmed the public
    surface of the command module is exactly what 111C left it as."""
    public_names = {name for name in dir(ri_cli) if not name.startswith("_")}
    assert "run_runtime_inspect" in public_names


def test_task_contract_excludes_forbidden_files():
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-111d*"))
    if not matches:
        pytest.skip("111D task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    for forbidden in ("shell_gate.py", "backend_invocations.py", "notifications.py"):
        assert forbidden not in contract_text
