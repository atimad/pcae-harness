"""
Phase 149O.20L.7O.3S — RPAC-001 mock-v1 core unit tests: descriptor,
registry adapter-catalog admission, target configuration, status, the
`RuntimeAdapter` Protocol, and the explicit no-fallback resolver.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pcae.core.mock_runtime_adapter import (
    MOCK_ADAPTER_ID,
    MOCK_CAPABILITY,
    MOCK_RESULT_FORMAT,
    TARGET_NO_CHANGE,
    MockDryRuntimeAdapter,
    build_mock_descriptor,
)
from pcae.core.runtime_adapter import (
    RuntimeAdapter,
    RuntimeAdapterResolver,
    RuntimeStatus,
    RuntimeTargetConfiguration,
    ResolutionFailure,
    ResolvedTarget,
    adapter_protocol_operation_names,
    build_mock_status,
    validate_request_against_target,
)
from pcae.core.runtime_invocation import (
    AuthoritySnapshot,
    MOCK_DRY_EFFECT_PROFILE,
    build_invocation_request,
    build_prompt_artifact,
    build_simulation_approval_evidence,
)
from pcae.core.runtime_registry import (
    RuntimeDescriptor,
    RuntimeRegistry,
    validate_runtime_descriptor,
)


def fixed_clock():
    return "2026-01-01T00:00:00Z"


def _authority(task_id: str = "task-1") -> AuthoritySnapshot:
    return AuthoritySnapshot(
        repository_id="repo-1",
        repository_fingerprint="fp-1",
        base_commit="c" * 40,
        task_id=task_id,
        task_contract_digest="digest-1",
    )


def _request(runtime_target_id: str, descriptor: RuntimeDescriptor, config: RuntimeTargetConfiguration, agent_id: str = "codex-ox"):
    authority = _authority()
    prompt = build_prompt_artifact(
        content="do the thing", generation_method="test", generation_version="1.0",
        authority=authority, clock=fixed_clock,
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id=runtime_target_id,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=fixed_clock,
    )
    request, issues = build_invocation_request(
        authority=authority,
        requester_agent_id=agent_id,
        runtime_target_id=runtime_target_id,
        expected_adapter_id=descriptor.adapter_id,
        descriptor_digest=descriptor.catalog_digest(),
        target_config_digest=config.digest(),
        prompt=prompt,
        approval=approval,
        requested_capability=MOCK_CAPABILITY,
        expected_result_format=MOCK_RESULT_FORMAT,
        timeout_seconds=30,
    )
    return request, issues, prompt, approval


# ── RuntimeDescriptor (RPAC-REQ-011/012) ────────────────────────────────


def test_mock_descriptor_exact_fields():
    descriptor = build_mock_descriptor()
    assert descriptor.adapter_id == MOCK_ADAPTER_ID
    assert descriptor.adapter_class == "mock_dry"
    assert descriptor.execution_effect == "none"
    assert descriptor.simulation_only is True
    assert descriptor.supported_capabilities == (MOCK_CAPABILITY,)
    assert validate_runtime_descriptor(descriptor) == ()


def test_descriptor_contains_no_live_or_authority_fields():
    field_names = set(RuntimeDescriptor.__dataclass_fields__.keys())
    forbidden = {
        "health", "available", "authorized", "permission", "approval",
        "credential", "task_id", "dispatch", "authenticated",
    }
    assert field_names.isdisjoint(forbidden)


def test_descriptor_is_immutable():
    descriptor = build_mock_descriptor()
    try:
        descriptor.adapter_id = "changed"  # type: ignore[misc]
        raise AssertionError("descriptor must be frozen")
    except Exception:
        pass


def test_mock_descriptor_digest_immutable():
    d1 = build_mock_descriptor()
    d2 = build_mock_descriptor()
    assert d1.catalog_digest() == d2.catalog_digest()


# ── Registry adapter-catalog admission (RPAC-REQ-050/052) ───────────────


def test_one_catalog_composed_resolver():
    registry = RuntimeRegistry()
    result = registry.register_adapter_descriptor(build_mock_descriptor())
    assert result.accepted
    snapshot = registry.registry_health()
    assert snapshot.registered_plugin_count == 0  # unrelated plugin metadata untouched
    catalog = registry.adapter_catalog_snapshot()
    assert catalog.registered_adapter_count == 1
    assert catalog.real_execution_capable_count == 0


def test_adapter_registration_fail_closed_on_duplicate():
    registry = RuntimeRegistry()
    registry.register_adapter_descriptor(build_mock_descriptor())
    other = RuntimeDescriptor(
        contract_version="RPAC-001/1.0", adapter_id=MOCK_ADAPTER_ID,
        implementation_version="9.9.9", implementation_digest="different-digest",
        adapter_class="mock_dry", transport_kind="in_process_fixture",
        supported_capabilities=(MOCK_CAPABILITY,), supported_result_formats=(MOCK_RESULT_FORMAT,),
        execution_effect="none", locality="in_process", network_required=False,
        supported_platforms=("platform_independent",), cancellation_mode="unsupported",
        simulation_only=True,
    )
    result = registry.register_adapter_descriptor(other)
    assert not result.accepted
    assert "duplicate_adapter_id_digest_drift" in result.issues


def test_adapter_registration_rejects_real_effect_without_simulation_only():
    registry = RuntimeRegistry()
    bad = RuntimeDescriptor(
        contract_version="RPAC-001/1.0", adapter_id="real.adapter",
        implementation_version="1.0", implementation_digest="d",
        adapter_class="local_cli", transport_kind="process",
        supported_capabilities=("execute",), supported_result_formats=(MOCK_RESULT_FORMAT,),
        execution_effect="local_process", locality="local", network_required=False,
        supported_platforms=("linux",), cancellation_mode="unsupported",
        simulation_only=False,
    )
    result = registry.register_adapter_descriptor(bad)
    assert not result.accepted
    assert "non_simulation_real_effect_descriptor_forbidden_in_3s" in result.issues


def test_legacy_plugin_registry_unaffected():
    from pcae.core.runtime_registry import PluginDescriptor

    registry = RuntimeRegistry()
    registry.register_adapter_descriptor(build_mock_descriptor())
    plugin_result = registry.register_metadata(
        PluginDescriptor(plugin_id="p1", plugin_type="Audit", version="1.0.0")
    )
    assert plugin_result.accepted
    assert registry.registry_health().registered_plugin_count == 1
    assert registry.adapter_catalog_snapshot().registered_adapter_count == 1


# ── RuntimeTargetConfiguration / RuntimeStatus (RPAC-REQ-013/015/017) ──


def test_mock_target_configuration_digest_stable():
    config1 = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    config2 = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    assert config1.digest() == config2.digest()


def test_mock_status_separates_simulation_from_execution():
    descriptor = build_mock_descriptor()
    config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    status = build_mock_status(descriptor=descriptor, config=config, clock=fixed_clock)
    assert status.simulation_ready is True
    assert status.real_execution_available is False
    assert status.authentication == "not_required"


def test_status_cannot_report_real_execution_available():
    import pytest

    with pytest.raises(ValueError):
        RuntimeStatus(
            runtime_target_id="x", adapter_id="y", descriptor_digest="z",
            registered=True, installed=True, configured=True,
            authentication="not_required", simulation_ready=True, health="healthy",
            observed_capabilities=(), real_execution_available=True,
            source="test", observed_at=fixed_clock(),
        )


def test_status_is_fact_only():
    field_names = set(RuntimeStatus.__dataclass_fields__.keys())
    forbidden = {"approval", "permission", "authorization", "dispatch"}
    assert field_names.isdisjoint(forbidden)


def test_capability_terms_do_not_collapse():
    descriptor = build_mock_descriptor()
    config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    status = build_mock_status(descriptor=descriptor, config=config, clock=fixed_clock)
    assert status.registered and status.installed and status.configured
    assert status.authentication == "not_required"
    assert status.simulation_ready
    assert not status.real_execution_available


# ── Adapter Protocol (RPAC-REQ-001/003/031) ─────────────────────────────


def test_adapter_protocol_operation_set():
    assert adapter_protocol_operation_names() == {
        "describe", "preflight", "dispatch", "collect", "cancel"
    }


def test_adapter_surface_has_no_authority_methods():
    adapter = MockDryRuntimeAdapter()
    assert isinstance(adapter, RuntimeAdapter)
    forbidden = {"approve", "authorize", "permit", "enforce", "ingest", "promote", "commit", "push"}
    public_methods = {
        name for name in dir(adapter) if not name.startswith("_") and callable(getattr(adapter, name))
    }
    assert public_methods.isdisjoint(forbidden)


def test_mock_adapter_cannot_govern():
    import ast

    source = Path("src/pcae/core/mock_runtime_adapter.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls = {"approve", "authorize", "commit", "push", "promote"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_calls


# ── Resolver: explicit selection, no fallback (RPAC-REQ-053) ───────────


def _resolver_with_target(target: str) -> RuntimeAdapterResolver:
    registry = RuntimeRegistry()
    registry.register_adapter_descriptor(build_mock_descriptor())
    resolver = RuntimeAdapterResolver(registry)
    resolver.register_target(RuntimeTargetConfiguration(target, "1.0", MOCK_ADAPTER_ID, target))
    resolver.register_adapter_instance(MOCK_ADAPTER_ID, MockDryRuntimeAdapter())
    return resolver


def test_explicit_lookup_no_fallback():
    resolver = _resolver_with_target(TARGET_NO_CHANGE)
    resolved = resolver.resolve_exact(TARGET_NO_CHANGE)
    assert isinstance(resolved, ResolvedTarget)
    unknown = resolver.resolve_exact("does-not-exist")
    assert isinstance(unknown, ResolutionFailure)
    assert unknown.category == "no_adapter_configured"


def test_resolver_has_no_agent_id_parameter():
    import inspect

    signature = inspect.signature(RuntimeAdapterResolver.resolve_exact)
    assert "agent_id" not in signature.parameters


def test_no_agent_name_fallback_in_resolver_source():
    source = Path("src/pcae/core/runtime_adapter.py").read_text(encoding="utf-8")
    assert "agent_id ==" not in source
    assert 'if agent_id' not in source


def test_exact_mock_capability_match():
    descriptor = build_mock_descriptor()
    config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    request, issues, _, _ = _request(TARGET_NO_CHANGE, descriptor, config)
    assert issues == ()
    assert validate_request_against_target(request, descriptor, config) == ()


def test_unsupported_capability_fails_closed():
    descriptor = build_mock_descriptor()
    config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    request, issues, _, _ = _request(TARGET_NO_CHANGE, descriptor, config)
    from dataclasses import replace

    bad_request = replace(request, requested_capability="execute")
    problems = validate_request_against_target(bad_request, descriptor, config)
    assert any("capability_not_supported" in p for p in problems)


# ── Identity separation (RPAC-REQ-006/007/008) ──────────────────────────


def test_identity_layers_are_distinct():
    descriptor = build_mock_descriptor()
    config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    request, issues, _, _ = _request(TARGET_NO_CHANGE, descriptor, config, agent_id="codex-ox")
    assert issues == ()
    assert request.requester_agent_id == "codex-ox"
    assert request.runtime_target_id == TARGET_NO_CHANGE
    assert request.provider_id is None
    assert request.model_id is None


def test_codex_ox_does_not_imply_runtime():
    descriptor = build_mock_descriptor()
    config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    request, issues, _, _ = _request(TARGET_NO_CHANGE, descriptor, config, agent_id="codex-ox")
    assert issues == ()
    assert request.runtime_target_id == TARGET_NO_CHANGE
    assert "codex" not in request.runtime_target_id
    assert request.provider_id is None and request.model_id is None


def test_agent_target_provider_producer_non_equivalence():
    descriptor = build_mock_descriptor()
    config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    codex_request, _, _, _ = _request(TARGET_NO_CHANGE, descriptor, config, agent_id="codex-ox")
    custom_request, _, _, _ = _request(TARGET_NO_CHANGE, descriptor, config, agent_id="custom-review-agent-17")
    assert codex_request.runtime_target_id == custom_request.runtime_target_id
    assert codex_request.requester_agent_id != custom_request.requester_agent_id


def test_mock_provider_model_are_absent():
    descriptor = build_mock_descriptor()
    config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    request, issues, _, _ = _request(TARGET_NO_CHANGE, descriptor, config)
    assert issues == ()
    assert request.provider_id is None
    assert request.model_id is None


def test_mock_provider_or_model_supplied_is_rejected():
    descriptor = build_mock_descriptor()
    config = RuntimeTargetConfiguration(TARGET_NO_CHANGE, "1.0", MOCK_ADAPTER_ID, TARGET_NO_CHANGE)
    authority = _authority()
    prompt = build_prompt_artifact(
        content="x", generation_method="t", generation_version="1", authority=authority, clock=fixed_clock
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id=TARGET_NO_CHANGE,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=fixed_clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id="codex-ox", runtime_target_id=TARGET_NO_CHANGE,
        expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
        target_config_digest=config.digest(), prompt=prompt, approval=approval,
        requested_capability=MOCK_CAPABILITY, expected_result_format=MOCK_RESULT_FORMAT,
        timeout_seconds=30, provider_id="OpenRouter",
    )
    assert request is None
    assert any("provider" in i for i in issues)


# ── Effect defaults (RPAC-REQ-027/061/085) ──────────────────────────────


def test_mock_effects_default_deny():
    assert MOCK_DRY_EFFECT_PROFILE.is_all_denied_zero()


def test_no_command_construction_surface():
    import ast

    source = Path("src/pcae/core/runtime_adapter.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_modules = {"subprocess", "shlex", "pty", "socket"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_modules
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_modules
