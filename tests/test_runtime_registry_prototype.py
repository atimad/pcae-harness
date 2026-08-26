"""Tests for Phase 110E — Runtime Registry Prototype (Observation-Only).

Verifies the first passive Runtime Registry implementation: metadata
registration, lookup, capability lookup, duplicate detection, manifest
validation, registry consistency, and read-only behavior -- plus,
critically, that the module has no dependency on shell execution,
backend invocation, plugin loading, or any other execution-adjacent
capability. No subprocess invocation in this file; pure in-process,
pytest-xdist safe.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from pcae.core import runtime_registry as rr
from pcae.core.runtime_registry import (
    CAPABILITY_CLASSES,
    HEALTH_STATES,
    IMPLEMENTATION_STATUSES,
    LIFECYCLE_STATES,
    PLUGIN_CATEGORIES,
    UNDECLARABLE_CAPABILITIES,
    PluginDescriptor,
    RegistrationResult,
    RegistrySnapshot,
    RegistryValidationReport,
    RuntimeRegistry,
    validate_descriptor,
)

MODULE_PATH = Path(rr.__file__)


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


# ═══════════════════════════════════════════════════════════════════════
# Frozen vocabularies restated correctly
# ═══════════════════════════════════════════════════════════════════════


def test_plugin_categories_match_110a_110b():
    assert PLUGIN_CATEGORIES == (
        "Intent Source",
        "Policy",
        "Decision",
        "Approval",
        "Execution Adapter",
        "Audit",
        "Notification",
        "Storage",
        "Identity",
        "Context",
    )


def test_lifecycle_states_match_110b_section_4():
    assert LIFECYCLE_STATES == (
        "defined",
        "registered",
        "configured",
        "healthy",
        "available",
        "disabled",
        "failed",
        "retired",
    )


def test_capability_classes_match_110b_section_3():
    assert CAPABILITY_CLASSES == (
        "observe",
        "advise",
        "approve",
        "deny",
        "enforce",
        "execute",
        "audit",
        "notify",
        "store",
        "rollback_prepare",
    )


def test_undeclarable_capabilities_are_enforce_and_execute():
    assert UNDECLARABLE_CAPABILITIES == frozenset({"enforce", "execute"})


def test_implementation_statuses_never_include_implemented():
    assert "implemented" not in IMPLEMENTATION_STATUSES
    assert IMPLEMENTATION_STATUSES == (
        "not_implemented",
        "foundation_implemented",
        "partially_implemented",
    )


def test_health_states_defined():
    assert HEALTH_STATES == ("healthy", "unhealthy", "unknown")


# ═══════════════════════════════════════════════════════════════════════
# PluginDescriptor is an inert data record
# ═══════════════════════════════════════════════════════════════════════


def test_plugin_descriptor_is_frozen_dataclass():
    d = _descriptor()
    with pytest.raises(Exception):
        d.plugin_id = "changed"  # type: ignore[misc]


def test_plugin_descriptor_default_manifest_is_empty_dict():
    d = _descriptor()
    assert d.manifest == {}


def test_plugin_descriptor_holds_no_callable_fields():
    d = _descriptor()
    for f in (d.plugin_id, d.plugin_type, d.version, d.lifecycle_state, d.health_state, d.implementation_status):
        assert isinstance(f, str)
    assert isinstance(d.capabilities, tuple)
    assert not callable(d.manifest)


# ═══════════════════════════════════════════════════════════════════════
# validate_descriptor()
# ═══════════════════════════════════════════════════════════════════════


def test_valid_descriptor_has_no_issues():
    assert validate_descriptor(_descriptor()) == ()


def test_empty_plugin_id_flagged():
    assert "empty_plugin_id" in validate_descriptor(_descriptor(plugin_id=""))


def test_invalid_plugin_type_flagged():
    assert "invalid_plugin_type" in validate_descriptor(_descriptor(plugin_type="Not A Category"))


@pytest.mark.parametrize("category", PLUGIN_CATEGORIES)
def test_every_frozen_plugin_category_accepted(category):
    assert validate_descriptor(_descriptor(plugin_type=category)) == ()


def test_invalid_lifecycle_state_flagged():
    assert "invalid_lifecycle_state" in validate_descriptor(_descriptor(lifecycle_state="bogus"))


@pytest.mark.parametrize("state", LIFECYCLE_STATES)
def test_every_frozen_lifecycle_state_accepted(state):
    assert validate_descriptor(_descriptor(lifecycle_state=state)) == ()


def test_invalid_health_state_flagged():
    assert "invalid_health_state" in validate_descriptor(_descriptor(health_state="bogus"))


@pytest.mark.parametrize("state", HEALTH_STATES)
def test_every_frozen_health_state_accepted(state):
    assert validate_descriptor(_descriptor(health_state=state)) == ()


def test_invalid_implementation_status_flagged():
    assert "invalid_implementation_status" in validate_descriptor(_descriptor(implementation_status="bogus"))


def test_implemented_status_is_rejected():
    """No plugin contract may claim `implemented` (110B §1 field 18)."""
    assert "invalid_implementation_status" in validate_descriptor(
        _descriptor(implementation_status="implemented")
    )


@pytest.mark.parametrize("status", IMPLEMENTATION_STATUSES)
def test_every_frozen_implementation_status_accepted(status):
    assert validate_descriptor(_descriptor(implementation_status=status)) == ()


@pytest.mark.parametrize("version", ["1.0.0", "0.1.0", "10.20.30", "0.0.1"])
def test_valid_semver_accepted(version):
    assert validate_descriptor(_descriptor(version=version)) == ()


@pytest.mark.parametrize("version", ["1.0", "v1.0.0", "1.0.0-rc1", "latest", ""])
def test_invalid_semver_flagged(version):
    assert "invalid_version_format" in validate_descriptor(_descriptor(version=version))


@pytest.mark.parametrize("capability", ["enforce", "execute"])
def test_undeclarable_capability_flagged(capability):
    issues = validate_descriptor(_descriptor(capabilities=(capability,)))
    assert "undeclarable_capability" in issues


@pytest.mark.parametrize(
    "capability",
    [c for c in CAPABILITY_CLASSES if c not in UNDECLARABLE_CAPABILITIES],
)
def test_declarable_capability_accepted(capability):
    assert validate_descriptor(_descriptor(capabilities=(capability,))) == ()


def test_unknown_capability_flagged():
    assert "invalid_capability" in validate_descriptor(_descriptor(capabilities=("not_a_real_capability",)))


def test_duplicate_capability_declaration_flagged():
    issues = validate_descriptor(_descriptor(capabilities=("observe", "observe")))
    assert "duplicate_capability_declaration" in issues


def test_manifest_plugin_id_mismatch_flagged():
    d = _descriptor(manifest={"plugin_id": "ISP-999"})
    assert "manifest_plugin_id_mismatch" in validate_descriptor(d)


def test_manifest_plugin_type_mismatch_flagged():
    d = _descriptor(manifest={"plugin_type": "Policy"})
    assert "manifest_plugin_type_mismatch" in validate_descriptor(d)


def test_manifest_version_mismatch_flagged():
    d = _descriptor(manifest={"version": "9.9.9"})
    assert "manifest_version_mismatch" in validate_descriptor(d)


def test_manifest_consistent_values_accepted():
    d = _descriptor(manifest={"plugin_id": "ISP-001", "plugin_type": "Intent Source", "version": "1.0.0"})
    assert validate_descriptor(d) == ()


def test_manifest_may_contain_unrelated_fields():
    d = _descriptor(manifest={"plugin_name": "Example Intent Source", "dependencies": ["storage.write"]})
    assert validate_descriptor(d) == ()


def test_validate_descriptor_is_pure_and_side_effect_free():
    d = _descriptor()
    before = validate_descriptor(d)
    after = validate_descriptor(d)
    assert before == after == ()


# ═══════════════════════════════════════════════════════════════════════
# RuntimeRegistry.register_metadata()
# ═══════════════════════════════════════════════════════════════════════


def test_register_valid_descriptor_is_accepted():
    registry = RuntimeRegistry()
    result = registry.register_metadata(_descriptor())
    assert isinstance(result, RegistrationResult)
    assert result.accepted is True
    assert result.issues == ()
    assert result.plugin_id == "ISP-001"


def test_register_invalid_descriptor_is_rejected_not_raised():
    registry = RuntimeRegistry()
    result = registry.register_metadata(_descriptor(plugin_type="bogus"))
    assert result.accepted is False
    assert "invalid_plugin_type" in result.issues


def test_rejected_registration_does_not_store_descriptor():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(plugin_type="bogus"))
    assert registry.list_plugins() == ()
    assert registry.get_plugin_metadata("ISP-001") is None


def test_duplicate_plugin_id_rejected():
    registry = RuntimeRegistry()
    first = registry.register_metadata(_descriptor())
    second = registry.register_metadata(_descriptor(version="2.0.0"))
    assert first.accepted is True
    assert second.accepted is False
    assert second.issues == ("duplicate_plugin_id",)


def test_duplicate_registration_does_not_overwrite_original():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(version="1.0.0"))
    registry.register_metadata(_descriptor(version="2.0.0"))
    stored = registry.get_plugin_metadata("ISP-001")
    assert stored.version == "1.0.0"


def test_register_never_raises_on_malformed_input():
    registry = RuntimeRegistry()
    for bad in [
        _descriptor(plugin_id=""),
        _descriptor(plugin_type="nope"),
        _descriptor(capabilities=("execute",)),
        _descriptor(version="not-a-version"),
    ]:
        result = registry.register_metadata(bad)
        assert result.accepted is False


# ═══════════════════════════════════════════════════════════════════════
# list_plugins() / get_plugin_metadata()
# ═══════════════════════════════════════════════════════════════════════


def test_list_plugins_empty_on_fresh_registry():
    assert RuntimeRegistry().list_plugins() == ()


def test_list_plugins_returns_all_registered():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(plugin_id="ISP-001"))
    registry.register_metadata(_descriptor(plugin_id="POL-001", plugin_type="Policy"))
    plugins = registry.list_plugins()
    assert len(plugins) == 2
    assert {p.plugin_id for p in plugins} == {"ISP-001", "POL-001"}


def test_get_plugin_metadata_returns_none_for_unknown_id():
    assert RuntimeRegistry().get_plugin_metadata("NO-SUCH-ID") is None


def test_get_plugin_metadata_returns_exact_descriptor():
    registry = RuntimeRegistry()
    d = _descriptor()
    registry.register_metadata(d)
    assert registry.get_plugin_metadata("ISP-001") == d


# ═══════════════════════════════════════════════════════════════════════
# list_capabilities() / find_capability()
# ═══════════════════════════════════════════════════════════════════════


def test_list_capabilities_empty_on_fresh_registry():
    assert RuntimeRegistry().list_capabilities() == ()


def test_list_capabilities_deduplicated_and_sorted():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(plugin_id="A-1", capabilities=("observe", "advise")))
    registry.register_metadata(_descriptor(plugin_id="A-2", plugin_type="Policy", capabilities=("advise", "deny")))
    assert registry.list_capabilities() == ("advise", "deny", "observe")


def test_find_capability_returns_matching_descriptors_only():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(plugin_id="A-1", capabilities=("observe",)))
    registry.register_metadata(_descriptor(plugin_id="A-2", plugin_type="Policy", capabilities=("deny",)))
    matches = registry.find_capability("observe")
    assert len(matches) == 1
    assert matches[0].plugin_id == "A-1"


def test_find_capability_supports_multiple_providers():
    """110D §4's MultipleCandidates outcome describes what the Runtime
    would do with more than one candidate; this registry only needs to
    surface all declared candidates, unfiltered."""
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(plugin_id="A-1", capabilities=("observe",)))
    registry.register_metadata(_descriptor(plugin_id="A-2", plugin_type="Policy", capabilities=("observe",)))
    matches = registry.find_capability("observe")
    assert {m.plugin_id for m in matches} == {"A-1", "A-2"}


def test_find_capability_empty_for_unknown_capability():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    assert registry.find_capability("nonexistent.capability") == ()


# ═══════════════════════════════════════════════════════════════════════
# registry_health()
# ═══════════════════════════════════════════════════════════════════════


def test_registry_health_empty_registry():
    snapshot = RuntimeRegistry().registry_health()
    assert isinstance(snapshot, RegistrySnapshot)
    assert snapshot.registered_plugin_count == 0
    assert snapshot.registered_capability_count == 0
    assert snapshot.registry_status == "empty"
    assert snapshot.metadata_validity == "valid"
    assert snapshot.plugin_ids == ()
    assert snapshot.capabilities == ()


def test_registry_health_populated_registry():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(plugin_id="A-1", capabilities=("observe", "advise")))
    registry.register_metadata(_descriptor(plugin_id="A-2", plugin_type="Policy", capabilities=("deny",)))
    snapshot = registry.registry_health()
    assert snapshot.registered_plugin_count == 2
    assert snapshot.registered_capability_count == 3
    assert snapshot.registry_status == "populated"
    assert snapshot.metadata_validity == "valid"
    assert set(snapshot.plugin_ids) == {"A-1", "A-2"}


def test_registry_health_carries_no_behavioral_signal():
    """The snapshot must never claim anything about whether a plugin
    actually works -- only what has been recorded about it."""
    snapshot = RuntimeRegistry().registry_health()
    field_names = set(snapshot.__dataclass_fields__.keys())
    assert "behavioral_health" not in field_names
    assert "live_status" not in field_names
    assert "execution_status" not in field_names


# ═══════════════════════════════════════════════════════════════════════
# validate_consistency()
# ═══════════════════════════════════════════════════════════════════════


def test_validate_consistency_clean_on_empty_registry():
    report = RuntimeRegistry().validate_consistency()
    assert isinstance(report, RegistryValidationReport)
    assert report.consistent is True
    assert report.duplicate_plugin_ids == ()
    assert report.plugins_with_duplicate_capability_declarations == ()
    assert report.plugins_with_manifest_inconsistencies == ()
    assert report.plugins_with_invalid_contract_fields == ()
    assert report.plugins_with_invalid_version_format == ()


def test_validate_consistency_clean_after_only_valid_registrations():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(plugin_id="A-1"))
    registry.register_metadata(_descriptor(plugin_id="A-2", plugin_type="Policy"))
    report = registry.validate_consistency()
    assert report.consistent is True


def test_validate_consistency_proves_rejected_duplicates_never_stored():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    registry.register_metadata(_descriptor(version="2.0.0"))  # duplicate id, rejected
    report = registry.validate_consistency()
    assert report.duplicate_plugin_ids == ()
    assert len(registry.list_plugins()) == 1


def test_validate_consistency_proves_rejected_invalid_descriptors_never_stored():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(capabilities=("observe", "observe")))
    registry.register_metadata(_descriptor(plugin_id="A-2", manifest={"version": "9.9.9"}))
    registry.register_metadata(_descriptor(plugin_id="A-3", plugin_type="bogus"))
    registry.register_metadata(_descriptor(plugin_id="A-4", version="bad-version"))
    report = registry.validate_consistency()
    assert report.consistent is True
    assert report.plugins_with_duplicate_capability_declarations == ()
    assert report.plugins_with_manifest_inconsistencies == ()
    assert report.plugins_with_invalid_contract_fields == ()
    assert report.plugins_with_invalid_version_format == ()
    assert registry.list_plugins() == ()


# ═══════════════════════════════════════════════════════════════════════
# Read-only behavior — repeated queries never mutate state
# ═══════════════════════════════════════════════════════════════════════


def test_repeated_reads_do_not_change_registry_state():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    before = registry.list_plugins()
    for _ in range(5):
        registry.list_plugins()
        registry.list_capabilities()
        registry.find_capability("observe")
        registry.get_plugin_metadata("ISP-001")
        registry.registry_health()
        registry.validate_consistency()
    after = registry.list_plugins()
    assert before == after


def test_list_plugins_returns_new_tuple_each_call():
    """Returned collections must not be a live, mutable view into the
    registry's internal store."""
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    result = registry.list_plugins()
    assert isinstance(result, tuple)


def test_two_registries_are_fully_independent():
    a = RuntimeRegistry()
    b = RuntimeRegistry()
    a.register_metadata(_descriptor())
    assert b.list_plugins() == ()
    assert b.get_plugin_metadata("ISP-001") is None


# ═══════════════════════════════════════════════════════════════════════
# No plugin loading / instantiation / invocation — structural guarantees
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_registry_has_no_load_or_invoke_methods():
    forbidden_method_names = {
        "load_plugin",
        "instantiate_plugin",
        "invoke_plugin",
        "call_plugin",
        "execute_plugin",
        "run_plugin",
        "import_plugin",
        "inject_dependency",
    }
    actual_methods = {name for name, _ in inspect.getmembers(RuntimeRegistry, predicate=inspect.isfunction)}
    assert not (forbidden_method_names & actual_methods)


def test_plugin_descriptor_has_no_load_or_invoke_methods():
    forbidden_method_names = {"load", "instantiate", "invoke", "call", "execute", "run"}
    actual_methods = {name for name, _ in inspect.getmembers(PluginDescriptor, predicate=inspect.isfunction)}
    assert not (forbidden_method_names & actual_methods)


def test_no_unregister_method_implemented_this_phase():
    """110D §2 names UnregisterPlugin() in the canonical API, but this
    phase deliberately implements only the metadata-registration half;
    no lifecycle-driving removal behavior is added here."""
    assert not hasattr(RuntimeRegistry, "unregister_metadata")
    assert not hasattr(RuntimeRegistry, "unregister_plugin")


def test_no_resolve_capability_method_implemented_this_phase():
    """ResolveCapability() (110D §4) requires Runtime-side selection
    behavior among candidates -- explicitly out of scope for a
    metadata-only registry."""
    assert not hasattr(RuntimeRegistry, "resolve_capability")


# ═══════════════════════════════════════════════════════════════════════
# Module isolation — no shell / backend / telegram / execution dependency
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def module_imports() -> list[str]:
    tree = ast.parse(MODULE_PATH.read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def test_module_imports_only_stdlib(module_imports):
    # Phase 149O.20L.7O.3S (RPAC-001 v1.0, RPAC-REQ-050) adds `hashlib`/`json`
    # for RuntimeDescriptor.catalog_digest() -- both standard library, no
    # dependency added.
    stdlib_allowed = {"__future__", "re", "dataclasses", "typing", "types", "hashlib", "json"}
    for name in module_imports:
        top = name.split(".")[0]
        assert top in stdlib_allowed, f"non-stdlib import: {name}"


def test_module_has_no_shell_dependency(module_imports):
    forbidden = ("shell_gate", "subprocess", "os.system", "os")
    for name in module_imports:
        assert not any(name == f or name.startswith(f + ".") for f in forbidden), f"forbidden import: {name}"


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


def test_module_has_no_permission_broker_dependency(module_imports):
    """This registry is purely metadata -- it does not consult the
    Permission Broker, since it grants no capability the broker would
    need to gate."""
    for name in module_imports:
        assert "permission_broker" not in name


def test_module_source_contains_no_exec_eval_compile_or_subprocess():
    text = MODULE_PATH.read_text()
    for forbidden in ("subprocess.", "os.system(", "eval(", "exec(", "__import__("):
        assert forbidden not in text, f"forbidden call present: {forbidden}"
    # Only the builtin `compile(` is forbidden -- `re.compile(` (used for
    # semver validation) is a legitimate, unrelated stdlib call.
    assert "\ncompile(" not in text and " compile(" not in text.replace("re.compile(", "")


def test_module_source_contains_no_file_io():
    text = MODULE_PATH.read_text()
    for forbidden in ("open(", "Path(", "os.remove", "os.rename", "shutil."):
        assert forbidden not in text, f"forbidden filesystem call present: {forbidden}"


def test_module_source_contains_no_network_calls():
    text = MODULE_PATH.read_text()
    for forbidden in ("socket.", "requests.", "urllib.", "http.client"):
        assert forbidden not in text, f"forbidden network call present: {forbidden}"


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / current runtime state remains Observed
# ═══════════════════════════════════════════════════════════════════════


def test_module_docstring_states_execution_unavailable():
    assert "execution unavailable" in rr.__doc__.lower()


def test_module_docstring_states_observed_runtime_state():
    assert "Observed" in rr.__doc__


def test_module_docstring_states_observe_plugin_capability_ceiling():
    assert "`observe`" in rr.__doc__


def test_registering_a_plugin_does_not_grant_any_capability():
    """Registering metadata declaring `execute` capability is
    impossible -- proving registration alone can never grant execution
    capability, only *record a claim*, and even undeclarable claims are
    rejected outright."""
    registry = RuntimeRegistry()
    result = registry.register_metadata(_descriptor(capabilities=("execute",)))
    assert result.accepted is False
    assert registry.find_capability("execute") == ()


def test_no_plugin_directory_or_runtime_directory_added():
    repo_root = MODULE_PATH.resolve().parent.parent.parent.parent
    assert not (repo_root / "src" / "pcae" / "plugins").exists()
    assert not (repo_root / "src" / "pcae" / "runtime").exists()


def test_task_contract_excludes_forbidden_files():
    """This phase's task contract must not list any CLI wiring, shell,
    backend, or Telegram file as allowed -- confirming the
    observation-only boundary was respected at the governance layer."""
    repo_root = MODULE_PATH.resolve().parent.parent.parent.parent
    done_dir = repo_root / "tasks" / "done"
    matches = list(done_dir.glob("*phase-110e*"))
    if not matches:
        pytest.skip("110E task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    for forbidden in ("shell_gate.py", "backend_invocations.py", "notifications.py", "cli.py"):
        assert forbidden not in contract_text
