"""
Phase 149O.20L.7O.3S — deterministic mock/dry adapter unit tests: fixed
fixtures, determinism, preflight/dispatch/collect/cancel semantics, and
malformed-result handling via the dedicated fake adapter.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pcae.core.mock_runtime_adapter import (
    MOCK_ADAPTER_ID,
    MOCK_CAPABILITY,
    MOCK_RESULT_FORMAT,
    TARGET_FAILURE,
    TARGET_NO_CHANGE,
    TARGET_SYNTHETIC_CHANGE,
    MalformedMockAdapter,
    MockDryRuntimeAdapter,
    build_mock_descriptor,
)
from pcae.core.runtime_adapter import validate_dispatch_envelope
from pcae.core.runtime_invocation import (
    MOCK_DRY_EFFECT_PROFILE,
    AuthoritySnapshot,
    build_dispatch_envelope,
    build_invocation_request,
    build_prompt_artifact,
    build_simulation_approval_evidence,
)


def fixed_clock():
    return "2026-01-01T00:00:00Z"


def _authority() -> AuthoritySnapshot:
    return AuthoritySnapshot(
        repository_id="repo-1", repository_fingerprint="fp-1", base_commit="c" * 40,
        task_id="task-1", task_contract_digest="digest-1",
    )


def _build_envelope(target: str):
    authority = _authority()
    descriptor = build_mock_descriptor()
    prompt = build_prompt_artifact(
        content="x", generation_method="t", generation_version="1", authority=authority, clock=fixed_clock
    )
    approval = build_simulation_approval_evidence(
        prompt=prompt, authority=authority, runtime_target_id=target,
        effect_profile_digest=MOCK_DRY_EFFECT_PROFILE.digest(), clock=fixed_clock,
    )
    request, issues = build_invocation_request(
        authority=authority, requester_agent_id="codex-ox", runtime_target_id=target,
        expected_adapter_id=MOCK_ADAPTER_ID, descriptor_digest=descriptor.catalog_digest(),
        target_config_digest="cfg-digest", prompt=prompt, approval=approval,
        requested_capability=MOCK_CAPABILITY, expected_result_format=MOCK_RESULT_FORMAT,
        timeout_seconds=30,
    )
    assert issues == ()
    envelope = build_dispatch_envelope(
        request=request, target_status_digest="status-digest", pb_decision_digest="ALLOW",
        enforcement_digest="enforcement-digest", record_reference="ref", clock=fixed_clock,
    )
    return envelope


# ── describe/preflight (RPAC-REQ-032) ───────────────────────────────────


def test_describe_is_side_effect_free_and_stable():
    adapter = MockDryRuntimeAdapter()
    d1 = adapter.describe()
    d2 = adapter.describe()
    assert d1.catalog_digest() == d2.catalog_digest()


def test_preflight_rejects_unknown_target():
    adapter = MockDryRuntimeAdapter()
    envelope = _build_envelope(TARGET_NO_CHANGE)
    bad_request = envelope.request
    from dataclasses import replace

    unknown = replace(bad_request, runtime_target_id="not-a-real-fixture")
    result = adapter.preflight(unknown)
    assert not result.capable


# ── dispatch/collect determinism (RPAC-REQ-055/090/091) ─────────────────


def test_mock_adapter_is_builtin_deterministic_no_change():
    adapter1 = MockDryRuntimeAdapter()
    adapter2 = MockDryRuntimeAdapter()
    envelope1 = _build_envelope(TARGET_NO_CHANGE)
    envelope2 = _build_envelope(TARGET_NO_CHANGE)

    receipt1 = adapter1.dispatch(envelope1)
    receipt2 = adapter2.dispatch(envelope2)
    assert receipt1.accepted and receipt2.accepted

    result1 = adapter1.collect(envelope1.request.attempt_id)
    result2 = adapter2.collect(envelope2.request.attempt_id)
    assert result1.payload_digest == result2.payload_digest
    assert result1.structured_payload == result2.structured_payload
    assert result1.terminal_outcome == result2.terminal_outcome == "success"
    assert result1.changed_files == () == result2.changed_files


def test_synthetic_change_fixture_is_deterministic_and_never_writes_disk(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    adapter = MockDryRuntimeAdapter()
    envelope = _build_envelope(TARGET_SYNTHETIC_CHANGE)
    adapter.dispatch(envelope)
    result = adapter.collect(envelope.request.attempt_id)
    assert result.terminal_outcome == "success"
    assert len(result.changed_files) == 1
    entry = result.changed_files[0]
    assert entry.path == "mock-output.txt"
    assert not (tmp_path / "mock-output.txt").exists()


def test_failure_fixture_is_deterministic():
    adapter = MockDryRuntimeAdapter()
    envelope = _build_envelope(TARGET_FAILURE)
    adapter.dispatch(envelope)
    result = adapter.collect(envelope.request.attempt_id)
    assert result.terminal_outcome == "failure"
    assert result.error_category == "runtime_failure"


def test_adapter_rejects_invalid_envelope():
    adapter = MockDryRuntimeAdapter()
    envelope = _build_envelope(TARGET_NO_CHANGE)
    from dataclasses import replace

    tampered = replace(envelope, approval_digest="tampered-digest")
    receipt = adapter.dispatch(tampered)
    assert not receipt.accepted


def test_cancel_terminal_semantics():
    adapter = MockDryRuntimeAdapter()
    envelope = _build_envelope(TARGET_NO_CHANGE)
    adapter.dispatch(envelope)
    result = adapter.cancel(envelope.request.attempt_id)
    assert result.outcome == "unsupported"
    adapter.collect(envelope.request.attempt_id)
    completed = adapter.cancel(envelope.request.attempt_id)
    assert completed.outcome == "completed_before_cancel"
    unknown = adapter.cancel("att-does-not-exist")
    assert unknown.outcome == "unknown_attempt"


def test_malformed_result_from_dedicated_fake_adapter():
    fake = MalformedMockAdapter()
    envelope = _build_envelope(TARGET_NO_CHANGE)
    receipt = fake.dispatch(envelope)
    assert receipt.accepted
    from pcae.core.runtime_invocation import RuntimeInvocationResult

    malformed = fake.collect(envelope.request.attempt_id)
    assert not isinstance(malformed, RuntimeInvocationResult)


# ── Zero-effect static/dynamic proof (RPAC-REQ-090, 3R §27/28/29) ───────


def test_mock_adapter_source_has_no_subprocess_network_or_credential_surface():
    source = Path("src/pcae/core/mock_runtime_adapter.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_modules = {"subprocess", "socket", "urllib", "http", "requests", "httpx", "pty", "shlex"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_modules
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_modules
        if isinstance(node, ast.Attribute):
            assert node.attr not in {"environ", "getenv", "system", "popen"}
        if isinstance(node, ast.Name):
            assert node.id not in {"eval", "exec"}


def test_mock_zero_effect_dynamic(tmp_path, monkeypatch):
    import socket
    import subprocess

    monkeypatch.chdir(tmp_path)

    def _boom(*args, **kwargs):
        raise AssertionError("mock adapter path must never call subprocess/socket")

    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(subprocess, "Popen", _boom)
    monkeypatch.setattr(socket, "socket", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)

    adapter = MockDryRuntimeAdapter()
    envelope = _build_envelope(TARGET_SYNTHETIC_CHANGE)
    adapter.dispatch(envelope)
    adapter.collect(envelope.request.attempt_id)

    before = sorted(p for p in tmp_path.rglob("*") if p.is_file())
    assert before == []


def test_mock_target_identities_do_not_impersonate_real_runtime():
    for identity in (MOCK_ADAPTER_ID, TARGET_NO_CHANGE, TARGET_SYNTHETIC_CHANGE, TARGET_FAILURE):
        lowered = identity.lower()
        for bad in ("codex", "claude", "openrouter", "openai", "anthropic"):
            assert bad not in lowered


def test_simulation_never_claims_real_execution():
    adapter = MockDryRuntimeAdapter()
    descriptor = adapter.describe()
    assert descriptor.execution_effect == "none"
    assert descriptor.simulation_only is True
