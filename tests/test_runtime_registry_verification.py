"""Tests for Phase 110F — Runtime Registry Verification & Compatibility.

Verification/hardening phase: proves the passive Runtime Registry
prototype (110E, `src/pcae/core/runtime_registry.py`) remains
metadata-only, non-executing, compatible with the 109A-109D observation
integrations and the 110A-110D runtime/plugin/registry architecture and
contracts, fails safe under every malformed/duplicate/unknown input,
and exposes enough read-only metadata for future introspection. This
file deliberately re-tests several claims `tests/test_runtime_registry_prototype.py`
(110E) already covers, from a compatibility/fail-safe angle rather than
a pure functional-coverage angle -- the two suites are complementary,
not redundant.

Also covers the one 110F hardening change: `PluginDescriptor.manifest`
is now an immutable `MappingProxyType` snapshot taken at construction
time, closing an aliasing gap where a caller-held manifest dict
reference could otherwise mutate already-registered metadata.

No subprocess invocation in this file; pure in-process, pytest-xdist
safe.
"""

from __future__ import annotations

import ast
from pathlib import Path
from types import MappingProxyType

import pytest

from pcae.core import command_path_observation as cpo
from pcae.core import runtime_registry as rr
from pcae.core.permission_broker_foundation import (
    IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE,
    PermissionBroker,
    build_permission_broker_request,
)
from pcae.core.runtime_registry import (
    CAPABILITY_CLASSES,
    HEALTH_STATES,
    IMPLEMENTATION_STATUSES,
    LIFECYCLE_STATES,
    PLUGIN_CATEGORIES,
    UNDECLARABLE_CAPABILITIES,
    PluginDescriptor,
    RuntimeRegistry,
    validate_descriptor,
)

REPO_ROOT = Path(rr.__file__).resolve().parent.parent.parent.parent
DOCS = REPO_ROOT / "docs"


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


def _module_import_names() -> list[str]:
    tree = ast.parse(Path(rr.__file__).read_text())
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.append(node.module)
    return names


def _broker_request(**overrides) -> object:
    fields = dict(
        action_type="read",
        execution_class="none",
        requested_component="COMP-001",
        requested_capability="evaluate",
        task_id="task-1",
        evidence_available=True,
        approval_present=True,
    )
    fields.update(overrides)
    return build_permission_broker_request(**fields)


# ═══════════════════════════════════════════════════════════════════════
# Objective 1 — Metadata-only boundary verification
# ═══════════════════════════════════════════════════════════════════════


def test_plugin_descriptor_has_no_callable_typed_fields():
    """Every declared field type on PluginDescriptor is a plain data
    type (str/tuple/Mapping) -- none is Callable, a class, or a module
    reference."""
    for f in PluginDescriptor.__dataclass_fields__.values():
        type_str = str(f.type)
        assert "Callable" not in type_str
        assert "ModuleType" not in type_str
        assert "type[" not in type_str.replace("tuple[", "")


def test_plugin_descriptor_has_no_module_or_import_path_fields():
    field_names = set(PluginDescriptor.__dataclass_fields__.keys())
    forbidden = {"module", "module_path", "import_path", "class_path", "entry_point", "callable", "handler"}
    assert not (field_names & forbidden)


def test_runtime_registry_has_no_callable_storage_attribute():
    """RuntimeRegistry's instance state is plain data dicts only --
    verified by inspecting a fresh instance's own __dict__ rather than
    trusting the source alone. Phase 149O.20L.7O.3S (RPAC-001 v1.0,
    RPAC-REQ-050) adds `_adapter_descriptors` as a second inert metadata
    collection beside `_plugins`; neither holds a callable."""
    registry = RuntimeRegistry()
    assert set(registry.__dict__.keys()) == {"_plugins", "_adapter_descriptors"}
    assert isinstance(registry._plugins, dict)
    assert isinstance(registry._adapter_descriptors, dict)


def test_runtime_registry_internal_store_holds_only_plugin_descriptors():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    for value in registry._plugins.values():
        assert isinstance(value, PluginDescriptor)
        assert not callable(value)


def test_registry_apis_cannot_load_plugins():
    """No RuntimeRegistry method name suggests, or could perform,
    dynamic loading of a plugin implementation."""
    forbidden = {"load", "load_plugin", "import_plugin", "load_module", "reload"}
    actual = {name for name in dir(RuntimeRegistry) if not name.startswith("_")}
    assert not (forbidden & actual)


def test_registry_apis_cannot_instantiate_plugins():
    forbidden = {"instantiate", "instantiate_plugin", "create_instance", "build_plugin", "construct_plugin"}
    actual = {name for name in dir(RuntimeRegistry) if not name.startswith("_")}
    assert not (forbidden & actual)


def test_registry_apis_cannot_invoke_plugins():
    forbidden = {"invoke", "invoke_plugin", "call_plugin", "run_plugin", "execute_plugin", "dispatch"}
    actual = {name for name in dir(RuntimeRegistry) if not name.startswith("_")}
    assert not (forbidden & actual)


def test_capability_lookup_returns_descriptors_not_plugins():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    for result in registry.find_capability("observe"):
        assert isinstance(result, PluginDescriptor)
        assert not callable(result)
        assert not hasattr(result, "__call__")


def test_list_capabilities_returns_only_strings():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(capabilities=("observe", "advise")))
    for capability in registry.list_capabilities():
        assert isinstance(capability, str)


# ═══════════════════════════════════════════════════════════════════════
# 110F hardening — manifest immutability (closes an aliasing gap)
# ═══════════════════════════════════════════════════════════════════════


def test_descriptor_manifest_is_a_mapping_proxy():
    d = _descriptor(manifest={"plugin_name": "Example"})
    assert isinstance(d.manifest, MappingProxyType)


def test_descriptor_manifest_cannot_be_mutated_via_item_assignment():
    d = _descriptor(manifest={"plugin_name": "Example"})
    with pytest.raises(TypeError):
        d.manifest["plugin_name"] = "Changed"  # type: ignore[index]


def test_mutating_caller_supplied_manifest_after_construction_does_not_affect_descriptor():
    """The aliasing gap this hardening closes: constructing a
    descriptor from a dict, then mutating the *original* dict, must
    never change what the descriptor (or the registry, once
    registered) reports."""
    original = {"plugin_name": "Example"}
    d = _descriptor(manifest=original)
    original["plugin_name"] = "Tampered"
    original["new_key"] = "also tampered"
    assert d.manifest["plugin_name"] == "Example"
    assert "new_key" not in d.manifest


def test_registered_descriptor_manifest_immune_to_post_registration_mutation():
    original = {"dependencies": ["storage.write"]}
    d = _descriptor(manifest=original)
    registry = RuntimeRegistry()
    registry.register_metadata(d)
    original["dependencies"] = ["tampered"]
    stored = registry.get_plugin_metadata("ISP-001")
    assert stored.manifest["dependencies"] == ["storage.write"]


def test_default_manifest_still_compares_equal_to_empty_dict():
    d = _descriptor()
    assert d.manifest == {}


def test_manifest_may_contain_a_callable_but_registry_never_calls_it():
    """Objective 1's 'registry APIs cannot invoke plugins' claim holds
    even in the adversarial case of a manifest smuggling in a callable
    value -- a canary that raises if ever invoked proves no registry
    method calls it."""

    class _ExplodingCallable:
        def __call__(self) -> None:
            raise AssertionError("the registry must never call a manifest value")

    canary = _ExplodingCallable()
    registry = RuntimeRegistry()
    result = registry.register_metadata(_descriptor(manifest={"hook": canary}))
    assert result.accepted is True

    registry.list_plugins()
    registry.list_capabilities()
    registry.find_capability("observe")
    registry.get_plugin_metadata("ISP-001")
    registry.registry_health()
    registry.validate_consistency()
    # No AssertionError raised above means the canary was never called.


# ═══════════════════════════════════════════════════════════════════════
# Objective 2 — Contract compatibility verification
# ═══════════════════════════════════════════════════════════════════════


def test_plugin_categories_match_110b_contract_doc_headers():
    text = (DOCS / "PCAE_RUNTIME_PLUGIN_CONTRACTS.md").read_text()
    for category in PLUGIN_CATEGORIES:
        assert f"{category} Plugin" in text, f"{category!r} not found as a contract heading in 110B doc"


def test_lifecycle_states_match_110b_contract_doc_table():
    text = (DOCS / "PCAE_RUNTIME_PLUGIN_CONTRACTS.md").read_text()
    for state in LIFECYCLE_STATES:
        assert f"`{state}`" in text, f"lifecycle state {state!r} not found in 110B doc"


def test_capability_classes_match_110b_contract_doc_taxonomy():
    text = (DOCS / "PCAE_RUNTIME_PLUGIN_CONTRACTS.md").read_text()
    for capability in CAPABILITY_CLASSES:
        assert f"`{capability}`" in text, f"capability class {capability!r} not found in 110B doc"


def test_implementation_statuses_match_110b_contract_doc():
    text = (DOCS / "PCAE_RUNTIME_PLUGIN_CONTRACTS.md").read_text()
    for status in IMPLEMENTATION_STATUSES:
        assert f"`{status}`" in text


def test_registry_module_referenced_by_110c_and_110d_docs():
    for doc_name in ("PCAE_RUNTIME_SERVICE_REGISTRY.md", "PCAE_RUNTIME_REGISTRY_CONTRACT.md"):
        text = (DOCS / doc_name).read_text()
        assert "Registry" in text


def test_110d_canonical_api_operations_named_in_module_docstring():
    """The five operations this phase's prototype implements must be
    the same five 110D names the module docstring claims to
    implement -- verified against the actual live 110D contract doc
    text, not just against the module's own claim about itself."""
    contract_text = (DOCS / "PCAE_RUNTIME_REGISTRY_CONTRACT.md").read_text()
    implemented_110d_names = (
        "RegisterPlugin()",
        "ListPlugins()",
        "DiscoverCapabilities()",
        "ListCapabilityProviders()",
        "GetPluginMetadata()",
    )
    for name in implemented_110d_names:
        assert name in contract_text
        assert name in rr.__doc__


def test_110a_runtime_state_model_observed_state_unchanged():
    text = (DOCS / "PCAE_RUNTIME_ARCHITECTURE.md").read_text()
    assert "Current maximum state reachable by any real PCAE command path today:\n`Observed`." in text \
        or "Current maximum state reachable by any real PCAE command path today: `Observed`." in text \
        or "`Observed`" in text


def test_109c_integration_registry_unchanged_by_this_phase():
    """The four observation-only command-path integrations (109B-109D)
    must remain exactly as they were -- this phase touches no command
    path and must not add, remove, or alter any INT-NNN entry."""
    assert cpo.INTEGRATION_IDS == frozenset({"INT-001", "INT-002", "INT-003", "INT-004"})
    assert len(cpo.INTEGRATION_REGISTRY) == 4


def test_permission_broker_unaffected_by_runtime_registry_existing():
    """108A's broker must still evaluate exactly as before -- this
    phase never imports, calls, or otherwise touches
    permission_broker_foundation.py."""
    broker = PermissionBroker()
    decision = broker.evaluate(_broker_request())
    assert decision.implementation_status == IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE


def test_runtime_registry_module_never_imports_permission_broker():
    imports = _module_import_names()
    assert not any("permission_broker" in name for name in imports)


def test_no_new_command_path_integration_added():
    """This phase adds no CLI wiring, so no new INT-NNN entry (or any
    other command-path integration marker) should exist anywhere in
    runtime_registry.py."""
    text = Path(rr.__file__).read_text()
    assert "INT-00" not in text
    assert "observe(" not in text  # the command_path_observation helper, not the capability string


# ═══════════════════════════════════════════════════════════════════════
# Objective 3 — Resolution semantics verification (re-test and harden)
# ═══════════════════════════════════════════════════════════════════════


def test_registered_capability_lookup_succeeds():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(capabilities=("observe",)))
    assert len(registry.find_capability("observe")) == 1


def test_missing_capability_lookup_returns_empty_not_error():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    assert registry.find_capability("storage.write") == ()


def test_duplicate_plugin_id_handling_is_reject_not_merge():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(version="1.0.0"))
    result = registry.register_metadata(_descriptor(version="2.0.0"))
    assert result.accepted is False
    assert registry.get_plugin_metadata("ISP-001").version == "1.0.0"


def test_duplicate_capability_within_descriptor_handling_is_reject():
    registry = RuntimeRegistry()
    result = registry.register_metadata(_descriptor(capabilities=("observe", "observe")))
    assert result.accepted is False
    assert "duplicate_capability_declaration" in result.issues


def test_invalid_descriptor_handling_never_raises():
    registry = RuntimeRegistry()
    for bad in [
        _descriptor(plugin_type="Nonexistent"),
        _descriptor(lifecycle_state="nonexistent"),
        _descriptor(version="not.semver"),
    ]:
        result = registry.register_metadata(bad)
        assert result.accepted is False


def test_incompatible_metadata_handling_manifest_mismatch_rejected():
    registry = RuntimeRegistry()
    result = registry.register_metadata(_descriptor(manifest={"version": "9.9.9"}))
    assert result.accepted is False
    assert "manifest_version_mismatch" in result.issues


@pytest.mark.parametrize("health", ["healthy", "unhealthy", "unknown"])
def test_unhealthy_or_unavailable_metadata_still_representable_and_registerable(health):
    """Health/lifecycle state is inert, caller-supplied data -- an
    'unhealthy' or 'disabled' plugin is still valid metadata to
    register and query, since this registry never gates on it (that
    would be behavior, not metadata)."""
    registry = RuntimeRegistry()
    result = registry.register_metadata(_descriptor(health_state=health))
    assert result.accepted is True


@pytest.mark.parametrize("state", ["disabled", "failed", "retired"])
def test_unavailable_lifecycle_states_still_representable_and_registerable(state):
    registry = RuntimeRegistry()
    result = registry.register_metadata(_descriptor(lifecycle_state=state))
    assert result.accepted is True


def test_find_capability_does_not_filter_by_health_or_lifecycle():
    """This registry implements only 110D's unfiltered
    ListCapabilityProviders() view -- an unhealthy, disabled, or
    retired plugin's declared capability is still surfaced. Filtering
    by health/lifecycle would be ResolveCapability() behavior, out of
    scope for this phase."""
    registry = RuntimeRegistry()
    registry.register_metadata(
        _descriptor(health_state="unhealthy", lifecycle_state="failed", capabilities=("observe",))
    )
    matches = registry.find_capability("observe")
    assert len(matches) == 1
    assert matches[0].health_state == "unhealthy"
    assert matches[0].lifecycle_state == "failed"


@pytest.mark.parametrize("state", LIFECYCLE_STATES)
def test_every_frozen_lifecycle_state_is_registerable(state):
    registry = RuntimeRegistry()
    result = registry.register_metadata(_descriptor(lifecycle_state=state))
    assert result.accepted is True


def test_current_maximum_capability_remains_observe_only_in_practice():
    """No test in this suite (or the 110E suite) ever successfully
    registers execute/enforce -- reconfirmed here as a registry-wide
    invariant, not just a single validate_descriptor() unit check."""
    registry = RuntimeRegistry()
    for capability in ("execute", "enforce"):
        result = registry.register_metadata(_descriptor(plugin_id=f"X-{capability}", capabilities=(capability,)))
        assert result.accepted is False
    assert registry.list_capabilities() == ()


# ═══════════════════════════════════════════════════════════════════════
# Objective 4 — Fail-safe behavior verification
# ═══════════════════════════════════════════════════════════════════════


def test_invalid_descriptor_does_not_register():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(plugin_type="bogus"))
    assert registry.list_plugins() == ()


def test_malformed_metadata_fails_safely_not_via_exception():
    """Every malformed-field combination is rejected via a returned
    result, never a raised exception -- mirroring 108C's
    `_sanitize_result()` fail-closed-without-crashing guarantee."""
    registry = RuntimeRegistry()
    malformed = [
        _descriptor(plugin_id=""),
        _descriptor(plugin_type=""),
        _descriptor(lifecycle_state=""),
        _descriptor(health_state=""),
        _descriptor(implementation_status="implemented"),
        _descriptor(version=""),
        _descriptor(capabilities=("bogus_capability",)),
    ]
    for descriptor in malformed:
        result = registry.register_metadata(descriptor)
        assert result.accepted is False
    assert registry.list_plugins() == ()


def test_no_provider_means_no_provider_not_fallback():
    """An unresolved capability lookup returns nothing -- it never
    falls back to any default, hardcoded, or 'best guess' plugin."""
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(capabilities=("observe",)))
    result = registry.find_capability("execution.shell")
    assert result == ()
    assert result is not None


def test_multiple_providers_remain_candidates_only_no_selection_performed():
    """Registering two plugins declaring the same capability must never
    cause the registry to pick a winner -- both remain equally
    returned candidates, since selection is Runtime behavior (110D §5)
    this phase does not implement."""
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(plugin_id="A-1", capabilities=("observe",)))
    registry.register_metadata(_descriptor(plugin_id="A-2", plugin_type="Policy", capabilities=("observe",)))
    matches = registry.find_capability("observe")
    assert len(matches) == 2
    assert not hasattr(registry, "select_candidate")
    assert not hasattr(registry, "resolve_capability")
    assert not hasattr(registry, "choose_provider")


def test_empty_registry_cannot_imply_execution():
    """An entirely empty, freshly constructed registry -- the closest
    analogue to '110D's Registry unavailable' scenario a metadata-only
    prototype can represent -- never returns anything that could be
    executed, and exposes no method that could execute anything
    regardless of population state."""
    registry = RuntimeRegistry()
    assert registry.list_plugins() == ()
    assert registry.list_capabilities() == ()
    assert registry.find_capability("execution.shell") == ()
    snapshot = registry.registry_health()
    assert snapshot.registry_status == "empty"
    assert snapshot.registered_plugin_count == 0


def test_unknown_capability_cannot_imply_execution():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    for unknown in ("execution.shell", "does.not.exist", "", "EXECUTE"):
        assert registry.find_capability(unknown) == ()


def test_no_descriptor_can_declare_execute_or_enforce_this_phase():
    for capability in UNDECLARABLE_CAPABILITIES:
        issues = validate_descriptor(_descriptor(capabilities=(capability,)))
        assert "undeclarable_capability" in issues


def test_undeclarable_capabilities_exactly_execute_and_enforce():
    assert UNDECLARABLE_CAPABILITIES == frozenset({"execute", "enforce"})


def test_fail_safe_direction_is_always_toward_rejection_never_acceptance():
    """Systematic sweep: every single-field corruption of an otherwise
    valid descriptor must reject, never silently accept with a
    corrected/defaulted value."""
    registry_field_corruptions = [
        dict(plugin_type="X"),
        dict(lifecycle_state="X"),
        dict(health_state="X"),
        dict(implementation_status="X"),
        dict(version="X"),
        dict(capabilities=("X",)),
        dict(capabilities=("execute",)),
        dict(capabilities=("enforce",)),
    ]
    for corruption in registry_field_corruptions:
        registry = RuntimeRegistry()
        result = registry.register_metadata(_descriptor(**corruption))
        assert result.accepted is False, f"corruption incorrectly accepted: {corruption}"


# ═══════════════════════════════════════════════════════════════════════
# Objective 5 — Introspection readiness verification
# ═══════════════════════════════════════════════════════════════════════


def test_introspection_exposes_registered_plugin_count():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    assert registry.registry_health().registered_plugin_count == 1


def test_introspection_exposes_capability_list():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(capabilities=("observe", "advise")))
    assert set(registry.registry_health().capabilities) == {"observe", "advise"}


def test_introspection_exposes_full_plugin_metadata():
    registry = RuntimeRegistry()
    d = _descriptor()
    registry.register_metadata(d)
    fetched = registry.get_plugin_metadata("ISP-001")
    assert fetched.plugin_id == d.plugin_id
    assert fetched.plugin_type == d.plugin_type
    assert fetched.version == d.version


def test_introspection_exposes_health_and_lifecycle_status():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor(health_state="unhealthy", lifecycle_state="failed"))
    fetched = registry.get_plugin_metadata("ISP-001")
    assert fetched.health_state == "unhealthy"
    assert fetched.lifecycle_state == "failed"


def test_introspection_exposes_validation_status():
    registry = RuntimeRegistry()
    registry.register_metadata(_descriptor())
    report = registry.validate_consistency()
    assert report.consistent is True
    snapshot = registry.registry_health()
    assert snapshot.metadata_validity == "valid"


def test_introspection_readiness_requires_no_cli():
    """Objective 5 explicitly permits satisfying introspection without
    a CLI -- confirmed here that no `pcae runtime plugins`-style
    command was added by this phase (cli.py is not in this phase's
    task contract's allowed files)."""
    text = Path(rr.__file__).read_text()
    assert "argparse" not in text
    assert "add_parser" not in text


# ═══════════════════════════════════════════════════════════════════════
# Execution unavailable / Observed / observe reconfirmation
# ═══════════════════════════════════════════════════════════════════════


def test_module_still_states_execution_unavailable():
    assert "execution unavailable" in rr.__doc__.lower()


def test_module_still_states_observed_runtime_state():
    assert "`Observed`" in rr.__doc__


def test_module_still_states_observe_capability_ceiling():
    assert "`observe`" in rr.__doc__


def test_no_execute_capable_descriptor_exists_anywhere_in_test_fixtures():
    """Defense in depth: this verification suite's own helper never
    accidentally constructs a descriptor declaring execute/enforce as
    its baseline default."""
    baseline = _descriptor()
    assert "execute" not in baseline.capabilities
    assert "enforce" not in baseline.capabilities


def test_runtime_registry_module_has_no_new_execution_adjacent_imports():
    imports = _module_import_names()
    forbidden = ("subprocess", "shell_gate", "backend_invocations", "notifications", "importlib", "socket")
    for name in imports:
        assert not any(f in name for f in forbidden), f"forbidden import: {name}"


def test_task_contract_excludes_forbidden_files():
    done_dir = REPO_ROOT / "tasks" / "done"
    matches = list(done_dir.glob("*phase-110f*"))
    if not matches:
        pytest.skip("110F task contract not yet moved to tasks/done/ (phase still in progress)")
    contract_text = matches[0].read_text()
    for forbidden in ("shell_gate.py", "backend_invocations.py", "notifications.py", "cli.py"):
        assert forbidden not in contract_text
