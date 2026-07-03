"""Tests for Phase 111B — Runtime Introspection Prototype (Observation-Only).

Verifies the first observation-only Runtime Introspection
implementation (`src/pcae/core/runtime_introspection.py`): the eight
implemented introspection objects/functions, integration with the
passive Runtime Registry (110E/110F), the metadata-only health/status/
governance snapshots, read-only/immutability guarantees, absence of any
CLI wiring, and module isolation (no shell/backend/network dependency,
no plugin loading/instantiation/invocation capability). Also verifies
compatibility with 111A's frozen architecture and 110E/110F's registry.

No subprocess invocation in this file; pure in-process, pytest-xdist
safe.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from pcae.core import runtime_introspection as ri
from pcae.core.command_path_observation import INTEGRATION_REGISTRY
from pcae.core.runtime_introspection import (
    CAPABILITY_CLASSES,
    CURRENT_MAXIMUM_PLUGIN_CAPABILITY,
    CURRENT_RUNTIME_STATE,
    EXECUTION_AVAILABILITY,
    PIPELINE_STAGES,
    RUNTIME_PRINCIPLES,
    RUNTIME_SERVICES,
    RUNTIME_STATE_MODEL,
    UNDECLARABLE_CAPABILITIES,
    CapabilityInfo,
    GovernanceInfo,
    HealthInfo,
    PluginInfo,
    RegistryInfo,
    RuntimeInfo,
    RuntimeStateInfo,
    VersionInfo,
    get_capabilities,
    get_governance,
    get_health,
    get_plugins,
    get_registry,
    get_runtime,
    get_state,
    get_version,
)
from pcae.core.runtime_registry import PluginDescriptor, RegistrySnapshot, RuntimeRegistry

REPO_ROOT = Path(ri.__file__).resolve().parent.parent.parent.parent


def _descriptor(**overrides) -> PluginDescriptor:
    defaults = dict(
        plugin_id="ISP-001",
        plugin_type="Intent Source",
        version="1.0.0",
        capabilities=("observe",),
        lifecycle_state="registered",
        health_state="healthy",
        implementation_status="not_implemented",
    )
    defaults.update(overrides)
    return PluginDescriptor(**defaults)


def _populated_registry() -> RuntimeRegistry:
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    registry.register_metadata(_descriptor(plugin_id="POL-001", plugin_type="Policy", capabilities=("advise",)))
    return registry


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — Introspection model exists, eight objects implemented
# ═══════════════════════════════════════════════════════════════════════


def test_all_eight_objective_1_objects_importable():
    for name in (
        "RuntimeInfo",
        "RegistryInfo",
        "PluginInfo",
        "CapabilityInfo",
        "HealthInfo",
        "VersionInfo",
        "GovernanceInfo",
        "RuntimeStateInfo",
    ):
        assert hasattr(ri, name)


def test_registry_info_is_registry_snapshot_not_a_duplicate():
    """111A §4 named RegistryInfo as mapping directly onto
    RegistrySnapshot -- this module realizes that as a type alias, not
    a new duplicate dataclass."""
    assert RegistryInfo is RegistrySnapshot


def test_plugin_info_is_plugin_descriptor_not_a_duplicate():
    assert PluginInfo is PluginDescriptor


def test_session_task_phase_info_deliberately_not_implemented():
    """This phase's own goal statement scopes to runtime/registry/
    plugin/capability/health/state/governance -- Session/Task/Phase are
    deliberately deferred, documented in the module docstring."""
    assert not hasattr(ri, "SessionInfo")
    assert not hasattr(ri, "TaskInfo")
    assert not hasattr(ri, "PhaseInfo")
    assert "SessionInfo" in ri.__doc__
    assert "deferred" in ri.__doc__.lower()


# ═══════════════════════════════════════════════════════════════════════
# RuntimeInfo / get_runtime()
# ═══════════════════════════════════════════════════════════════════════


def test_get_runtime_returns_runtime_info():
    info = get_runtime()
    assert isinstance(info, RuntimeInfo)


def test_runtime_info_pipeline_stages_match_110a():
    info = get_runtime()
    assert info.pipeline_stages == PIPELINE_STAGES
    assert len(info.pipeline_stages) == 7
    assert "Intent Source" in info.pipeline_stages
    assert "Notification Pipeline" in info.pipeline_stages


def test_runtime_info_principles_match_110a():
    info = get_runtime()
    assert info.principles == RUNTIME_PRINCIPLES
    assert len(info.principles) == 11
    assert "Fail-closed" in info.principles


def test_runtime_info_services_match_110a():
    info = get_runtime()
    assert info.runtime_services == RUNTIME_SERVICES
    assert len(info.runtime_services) == 9
    assert "Integration Registry" in info.runtime_services


def test_get_runtime_requires_no_registry_argument():
    """RuntimeInfo is purely static architecture-level facts -- it must
    not require a live registry to compute."""
    sig = inspect.signature(get_runtime)
    assert len(sig.parameters) == 0


# ═══════════════════════════════════════════════════════════════════════
# RegistryInfo / get_registry() — integration with 110E/110F registry
# ═══════════════════════════════════════════════════════════════════════


def test_get_registry_on_empty_registry():
    info = get_registry(RuntimeRegistry())
    assert info.registered_plugin_count == 0
    assert info.registry_status == "empty"


def test_get_registry_reflects_registered_plugins():
    registry = _populated_registry()
    info = get_registry(registry)
    assert info.registered_plugin_count == 2
    assert set(info.plugin_ids) == {"ISP-001", "POL-001"}


def test_get_registry_delegates_to_registry_health():
    """No new computation -- get_registry() must produce exactly what
    RuntimeRegistry.registry_health() itself produces."""
    registry = _populated_registry()
    assert get_registry(registry) == registry.registry_health()


# ═══════════════════════════════════════════════════════════════════════
# PluginInfo / get_plugins() — metadata only, from registry
# ═══════════════════════════════════════════════════════════════════════


def test_get_plugins_empty_registry():
    assert get_plugins(RuntimeRegistry()) == ()


def test_get_plugins_returns_registered_descriptors():
    registry = _populated_registry()
    plugins = get_plugins(registry)
    assert len(plugins) == 2
    assert {p.plugin_id for p in plugins} == {"ISP-001", "POL-001"}


def test_get_plugins_delegates_to_list_plugins():
    registry = _populated_registry()
    assert get_plugins(registry) == registry.list_plugins()


def test_plugin_info_generated_from_metadata_only_no_extra_fields():
    """PluginInfo (== PluginDescriptor) carries only the eight
    metadata fields 110E froze -- no field added by this phase."""
    registry = _populated_registry()
    for plugin in get_plugins(registry):
        field_names = set(plugin.__dataclass_fields__.keys())
        assert field_names == {
            "plugin_id", "plugin_type", "version", "capabilities",
            "lifecycle_state", "health_state", "implementation_status", "manifest",
        }


# ═══════════════════════════════════════════════════════════════════════
# CapabilityInfo / get_capabilities()
# ═══════════════════════════════════════════════════════════════════════


def test_get_capabilities_covers_full_frozen_taxonomy():
    """Even on an empty registry, every one of the ten frozen
    capability classes is reported (with no declaring plugins)."""
    infos = get_capabilities(RuntimeRegistry())
    assert len(infos) == len(CAPABILITY_CLASSES) == 10
    assert {c.capability for c in infos} == set(CAPABILITY_CLASSES)


def test_get_capabilities_reports_declaring_plugins():
    registry = _populated_registry()
    infos = {c.capability: c for c in get_capabilities(registry)}
    assert infos["observe"].declaring_plugin_ids == ("ISP-001",)
    assert infos["advise"].declaring_plugin_ids == ("POL-001",)
    assert infos["deny"].declaring_plugin_ids == ()


def test_get_capabilities_marks_execute_and_enforce_undeclarable():
    infos = {c.capability: c for c in get_capabilities(RuntimeRegistry())}
    assert infos["execute"].undeclarable is True
    assert infos["enforce"].undeclarable is True
    for capability in CAPABILITY_CLASSES:
        if capability not in UNDECLARABLE_CAPABILITIES:
            assert infos[capability].undeclarable is False


def test_get_capabilities_execute_and_enforce_never_have_declaring_plugins():
    """Structurally impossible for any registered plugin to declare
    these -- registry.register_metadata() already rejects them (110E)."""
    registry = _populated_registry()
    infos = {c.capability: c for c in get_capabilities(registry)}
    assert infos["execute"].declaring_plugin_ids == ()
    assert infos["enforce"].declaring_plugin_ids == ()


def test_capability_info_generated_from_metadata_only():
    """get_capabilities() must only read registry metadata
    (find_capability()) -- confirmed by checking it never invokes or
    instantiates anything (no side effects observable via repeated
    calls returning identical results)."""
    registry = _populated_registry()
    first = get_capabilities(registry)
    second = get_capabilities(registry)
    assert first == second


# ═══════════════════════════════════════════════════════════════════════
# HealthInfo / get_health() — objective 3
# ═══════════════════════════════════════════════════════════════════════


def test_get_health_returns_health_info():
    assert isinstance(get_health(RuntimeRegistry()), HealthInfo)


def test_health_info_reflects_registry_state():
    registry = _populated_registry()
    health = get_health(registry)
    assert health.plugin_count == 2
    assert health.capability_count == 2
    assert health.registry_status == "populated"
    assert health.metadata_validity == "valid"


def test_health_info_execution_availability_is_unavailable():
    health = get_health(RuntimeRegistry())
    assert health.execution_availability == "unavailable"
    assert health.execution_availability == EXECUTION_AVAILABILITY


def test_health_info_runtime_state_is_observed():
    health = get_health(RuntimeRegistry())
    assert health.current_runtime_state == "Observed"
    assert health.current_runtime_state == CURRENT_RUNTIME_STATE


def test_health_info_maximum_plugin_capability_is_observe():
    health = get_health(RuntimeRegistry())
    assert health.current_maximum_plugin_capability == "observe"
    assert health.current_maximum_plugin_capability == CURRENT_MAXIMUM_PLUGIN_CAPABILITY


def test_health_info_runtime_status_honestly_not_implemented():
    """No live Runtime instance exists -- runtime_status must not
    fabricate a 'healthy' claim about something nonexistent."""
    health = get_health(RuntimeRegistry())
    assert health.runtime_status == "not_implemented"


def test_health_info_carries_no_behavioral_signal():
    field_names = set(HealthInfo.__dataclass_fields__.keys())
    assert "live_status" not in field_names
    assert "behavioral_health" not in field_names


# ═══════════════════════════════════════════════════════════════════════
# GovernanceInfo / get_governance() — objective 4
# ═══════════════════════════════════════════════════════════════════════


def test_get_governance_returns_governance_info():
    assert isinstance(get_governance(), GovernanceInfo)


def test_governance_info_non_executing_posture_true():
    info = get_governance()
    assert info.non_executing_posture is True


def test_governance_info_broker_status_execution_unavailable():
    info = get_governance()
    assert info.broker_implementation_status == "execution_unavailable"


def test_governance_info_observed_command_paths_matches_109c():
    info = get_governance()
    assert info.observed_command_paths == len(INTEGRATION_REGISTRY) == 4


def test_governance_info_execution_capability_unavailable():
    info = get_governance()
    assert info.execution_capability == "unavailable"


def test_get_governance_requires_no_arguments():
    sig = inspect.signature(get_governance)
    assert len(sig.parameters) == 0


def test_governance_info_never_calls_permission_broker():
    """get_governance() reads a constant; it must never construct or
    evaluate a live PermissionBroker."""
    text = Path(ri.__file__).read_text()
    assert "PermissionBroker()" not in text
    assert ".evaluate(" not in text


# ═══════════════════════════════════════════════════════════════════════
# RuntimeStateInfo / get_state()
# ═══════════════════════════════════════════════════════════════════════


def test_get_state_returns_runtime_state_info():
    assert isinstance(get_state(), RuntimeStateInfo)


def test_state_info_current_state_is_observed():
    assert get_state().current_state == "Observed"


def test_state_info_model_matches_110a_verbatim():
    info = get_state()
    assert info.state_model == RUNTIME_STATE_MODEL
    assert info.state_model == (
        "Intent", "Observed", "Advisory", "Approved",
        "Executable", "Executed", "Audited", "Rollback Ready",
    )


def test_get_state_requires_no_arguments():
    sig = inspect.signature(get_state)
    assert len(sig.parameters) == 0


# ═══════════════════════════════════════════════════════════════════════
# VersionInfo / get_version()
# ═══════════════════════════════════════════════════════════════════════


def test_get_version_returns_version_info():
    assert isinstance(get_version(RuntimeRegistry()), VersionInfo)


def test_version_info_release_version_grounded():
    from pcae import __version__

    info = get_version(RuntimeRegistry())
    assert info.release_version == __version__


def test_version_info_plugin_versions_from_registry():
    registry = _populated_registry()
    info = get_version(registry)
    assert ("ISP-001", "1.0.0") in info.plugin_versions
    assert ("POL-001", "1.0.0") in info.plugin_versions


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — registry integration must never load/instantiate/
# invoke/mutate
# ═══════════════════════════════════════════════════════════════════════


def test_introspection_never_mutates_registry():
    registry = _populated_registry()
    before = registry.list_plugins()
    get_runtime()
    get_registry(registry)
    get_plugins(registry)
    get_capabilities(registry)
    get_health(registry)
    get_governance()
    get_state()
    get_version(registry)
    after = registry.list_plugins()
    assert before == after


def test_introspection_module_has_no_load_instantiate_invoke_functions():
    forbidden = {
        "load_plugin", "instantiate_plugin", "invoke_plugin", "call_plugin",
        "run_plugin", "execute_plugin", "import_plugin", "inject_dependency",
    }
    actual = {name for name, obj in inspect.getmembers(ri) if inspect.isfunction(obj)}
    assert not (forbidden & actual)


def test_introspection_module_never_registers_metadata():
    """Introspection is read-only -- it must never call
    register_metadata() on a registry passed to it."""
    text = Path(ri.__file__).read_text()
    assert "register_metadata(" not in text


def test_manifest_may_contain_a_callable_but_introspection_never_calls_it():
    class _ExplodingCallable:
        def __call__(self) -> None:
            raise AssertionError("introspection must never call a manifest value")

    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(manifest={"hook": _ExplodingCallable()}))
    get_runtime()
    get_registry(registry)
    get_plugins(registry)
    get_capabilities(registry)
    get_health(registry)
    get_governance()
    get_state()
    get_version(registry)
    # No AssertionError raised above means the canary was never called.


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — read-only / immutability guarantees
# ═══════════════════════════════════════════════════════════════════════


def test_all_introspection_dataclasses_are_frozen():
    for cls in (RuntimeInfo, CapabilityInfo, HealthInfo, VersionInfo, GovernanceInfo, RuntimeStateInfo):
        instance_fields = cls.__dataclass_fields__
        assert instance_fields  # sanity: has fields
        assert cls.__dataclass_params__.frozen is True


def test_capability_info_cannot_be_mutated():
    info = get_capabilities(RuntimeRegistry())[0]
    with pytest.raises(Exception):
        info.undeclarable = True  # type: ignore[misc]


def test_health_info_cannot_be_mutated():
    info = get_health(RuntimeRegistry())
    with pytest.raises(Exception):
        info.registry_status = "tampered"  # type: ignore[misc]


def test_governance_info_cannot_be_mutated():
    info = get_governance()
    with pytest.raises(Exception):
        info.execution_capability = "available"  # type: ignore[misc]


def test_plugin_info_returned_is_immune_to_manifest_tampering():
    """Reuses 110F's manifest-immutability guarantee -- a caller
    receiving PluginInfo (== PluginDescriptor) from get_plugins() still
    cannot mutate its manifest."""
    registry = _populated_registry()
    plugin = get_plugins(registry)[0]
    with pytest.raises(TypeError):
        plugin.manifest["new_key"] = "tampered"  # type: ignore[index]


def test_repeated_introspection_calls_do_not_change_registry_state():
    registry = _populated_registry()
    for _ in range(5):
        get_registry(registry)
        get_plugins(registry)
        get_capabilities(registry)
        get_health(registry)
        get_version(registry)
    assert registry.registry_health().registered_plugin_count == 2


# ═══════════════════════════════════════════════════════════════════════
# Objective 6 — no CLI command exists yet
# ═══════════════════════════════════════════════════════════════════════


def test_no_argparse_in_introspection_module():
    text = Path(ri.__file__).read_text()
    assert "argparse" not in text
    assert "add_parser" not in text


def test_cli_does_not_reference_runtime_inspect_command():
    cli_text = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text()
    assert "runtime-inspect" not in cli_text
    assert "runtime_introspection" not in cli_text


def test_no_pcae_commands_runtime_introspection_module():
    assert not (REPO_ROOT / "src" / "pcae" / "commands" / "runtime_introspection.py").exists()


# ═══════════════════════════════════════════════════════════════════════
# Compatibility with 111A architecture / 110E-110F registry
# ═══════════════════════════════════════════════════════════════════════

DOCS = REPO_ROOT / "docs"


def test_api_function_names_match_111a_operations_1to1():
    """111A §7 froze GetRuntime/GetRegistry/GetPlugins/GetCapabilities/
    GetHealth/GetGovernance/GetState/GetVersion -- this module's
    snake_case names must correspond 1:1."""
    contract_text = (DOCS / "PCAE_RUNTIME_INTROSPECTION.md").read_text()
    api_pairs = (
        ("GetRuntime()", get_runtime),
        ("GetRegistry()", get_registry),
        ("GetPlugins()", get_plugins),
        ("GetCapabilities()", get_capabilities),
        ("GetHealth()", get_health),
        ("GetGovernance()", get_governance),
        ("GetState()", get_state),
        ("GetVersion()", get_version),
    )
    for operation_name, func in api_pairs:
        assert operation_name in contract_text
        assert callable(func)


def test_pipeline_stages_match_110a_doc_text():
    text = (DOCS / "PCAE_RUNTIME_ARCHITECTURE.md").read_text()
    for stage in PIPELINE_STAGES:
        assert stage in text


def test_state_model_matches_110a_doc_text():
    text = (DOCS / "PCAE_RUNTIME_ARCHITECTURE.md").read_text()
    for state in RUNTIME_STATE_MODEL:
        assert state in text


def test_compatible_with_110e_110f_plugin_descriptor_shape():
    """PluginInfo must remain assignable wherever a PluginDescriptor is
    expected -- proven directly by identity, not just structural
    similarity."""
    assert PluginInfo is PluginDescriptor
    registry = RuntimeRegistry()
    result = registry.register_metadata(_descriptor())
    assert result.accepted is True
    plugin = get_plugins(registry)[0]
    assert isinstance(plugin, PluginDescriptor)


def test_compatible_with_110f_hardened_manifest_immutability():
    """110F's manifest-immutability hardening must transparently apply
    to every PluginInfo this module returns (proven above,
    test_plugin_info_returned_is_immune_to_manifest_tampering) -- this
    test additionally confirms the underlying type identity holds."""
    from types import MappingProxyType

    registry = _populated_registry()
    for plugin in get_plugins(registry):
        assert isinstance(plugin.manifest, MappingProxyType)


# ═══════════════════════════════════════════════════════════════════════
# Module isolation — no shell / backend / telegram / plugin-loading
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def module_imports() -> list[str]:
    tree = ast.parse(Path(ri.__file__).read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def test_module_imports_are_allowlisted(module_imports):
    allowed = {
        "__future__",
        "dataclasses",
        "pcae",
        "pcae.core.command_path_observation",
        "pcae.core.permission_broker_foundation",
        "pcae.core.runtime_registry",
    }
    for name in module_imports:
        assert name in allowed, f"unexpected import: {name}"


def test_module_has_no_shell_or_subprocess_dependency(module_imports):
    forbidden = ("shell_gate", "subprocess", "os.system")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_module_has_no_backend_dependency(module_imports):
    forbidden = ("backend_invocations", "backend_cli", "agent_backends")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_module_has_no_telegram_or_notification_dependency(module_imports):
    forbidden = ("notifications", "telegram")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_module_has_no_plugin_loading_dependency(module_imports):
    forbidden = ("importlib", "pkgutil", "pluggy")
    for name in module_imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_module_source_contains_no_exec_eval_or_subprocess():
    text = Path(ri.__file__).read_text()
    for forbidden in ("subprocess.", "os.system(", "eval(", "exec(", "__import__("):
        assert forbidden not in text


def test_module_source_contains_no_file_io():
    text = Path(ri.__file__).read_text()
    for forbidden in ("open(", "Path(", "os.remove", "os.rename", "shutil."):
        assert forbidden not in text


def test_module_source_contains_no_network_calls():
    text = Path(ri.__file__).read_text()
    for forbidden in ("socket.", "requests.", "urllib.", "http.client"):
        assert forbidden not in text


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / Observed / observe reconfirmation
# ═══════════════════════════════════════════════════════════════════════


def test_module_docstring_states_execution_unavailable():
    assert "execution unavailable" in ri.__doc__.lower()


def test_module_docstring_states_observed_runtime_state():
    assert "`Observed`" in ri.__doc__


def test_module_docstring_states_observe_capability_ceiling():
    assert "`observe`" in ri.__doc__


def test_module_docstring_states_111c_cli_deferral():
    import re

    normalized = re.sub(r"\s+", " ", ri.__doc__)
    assert "111C" in normalized
    assert "pcae runtime inspect" in normalized


def test_no_introspection_or_runtime_directory_added():
    assert not (REPO_ROOT / "src" / "pcae" / "introspection").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "runtime").exists()
    assert not (REPO_ROOT / "src" / "pcae" / "plugins").exists()


def test_task_contract_excludes_forbidden_files():
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-111b*"))
    if not matches:
        pytest.skip("111B task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    for forbidden in ("cli.py", "shell_gate.py", "backend_invocations.py", "notifications.py"):
        assert forbidden not in contract_text
