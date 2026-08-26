"""
Deterministic Mock/Dry Runtime Adapter — Phase 149O.20L.7O.3S.

The RPAC-001 v1.0 (RPAC-REQ-088..091) built-in, deterministic mock/dry
adapter. This is the ONLY module in the mock-v1 slice that implements the
`RuntimeAdapter` Protocol; everything upstream of it (`runtime_adapter.py`,
`runtime_invocation.py`) is trusted-kernel orchestration that owns
authority, gates, and persistence.

Static, structural, and dynamic invariants this module holds itself to:

- no `subprocess`, `os.system`, `popen`, `spawn`, `exec*`, `pty`, `shlex`,
  or shell import/call anywhere in this file (RPAC-REQ-090, 3R §27);
- no `socket`, `urllib`, `http.client`, `requests`, `httpx`, or provider
  SDK import anywhere in this file (RPAC-REQ-090, 3R §28);
- no `os.environ`, `os.getenv`, `Path.home`, keyring, token-store, or
  auth-file access anywhere in this file (RPAC-REQ-084/090, 3R §29);
- zero filesystem writes of its own -- every persisted document is
  written by the trusted `RuntimeInvocationStore`, never by this adapter
  (RPAC-REQ-061/090);
- for identical normalized semantic input and a fixed target fixture, the
  semantic output is byte-identical (RPAC-REQ-055/090/091, 3R §18/§46
  determinism unit tests use this module directly).

`MockDryRuntimeAdapter.dispatch()` is the last allowed mock-v1 operation
(3R plan §26, "Execution Attempt Boundary"). Nothing past it resolves an
executable, opens a socket, reads a credential, or mutates a worktree
file; the first such operation is explicitly reserved for a separate,
future, real-runtime-bound governed phase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .runtime_adapter import (
    AdapterPreflightResult,
    DispatchReceipt,
    RuntimeCancellationResult,
)
from .runtime_invocation import (
    ChangedFileEntry,
    FAILURE_MALFORMED_RESULT,
    FAILURE_RUNTIME_FAILURE,
    InvocationRequest,
    RuntimeInvocationResult,
    SimulationDispatchEnvelope,
    build_runtime_invocation_result,
    validate_dispatch_envelope,
)
from .runtime_registry import RuntimeDescriptor

MOCK_ADAPTER_ID = "pcae.mock-dry"
MOCK_ADAPTER_IMPLEMENTATION_VERSION = "1.0.0"
MOCK_CAPABILITY = "simulation.dry_dispatch"
MOCK_RESULT_FORMAT = "rpac.terminal-result.v1"

TARGET_NO_CHANGE = "mock-dry.no-change.v1"
TARGET_SYNTHETIC_CHANGE = "mock-dry.synthetic-change.v1"
TARGET_FAILURE = "mock-dry.failure.v1"

KNOWN_MOCK_TARGET_FIXTURES: frozenset[str] = frozenset(
    {TARGET_NO_CHANGE, TARGET_SYNTHETIC_CHANGE, TARGET_FAILURE}
)

#: A clearly non-production target/adapter identity set (RPAC-REQ-008): no
#: `codex`, `codex-ox`, `claude-local`, or provider name appears anywhere
#: in this module's identity vocabulary.
_FORBIDDEN_IDENTITY_SUBSTRINGS: tuple[str, ...] = (
    "codex",
    "claude",
    "openrouter",
    "openai",
    "anthropic",
)
for _identity in (MOCK_ADAPTER_ID, TARGET_NO_CHANGE, TARGET_SYNTHETIC_CHANGE, TARGET_FAILURE):
    _lowered = _identity.lower()
    if any(bad in _lowered for bad in _FORBIDDEN_IDENTITY_SUBSTRINGS):  # pragma: no cover
        raise RuntimeError(f"mock_target_must_not_impersonate_real_runtime:{_identity}")


def build_mock_descriptor() -> RuntimeDescriptor:
    """The one built-in `RuntimeDescriptor` for `pcae.mock-dry`
    (RPAC-REQ-011, 3R §10). Frozen, closed, canonical-JSON serializable;
    contains no status, credential, gate, or task field."""
    return RuntimeDescriptor(
        contract_version="RPAC-001/1.0",
        adapter_id=MOCK_ADAPTER_ID,
        implementation_version=MOCK_ADAPTER_IMPLEMENTATION_VERSION,
        implementation_digest="mock-dry-builtin-fixed-digest-v1",
        adapter_class="mock_dry",
        transport_kind="in_process_fixture",
        supported_capabilities=(MOCK_CAPABILITY,),
        supported_result_formats=(MOCK_RESULT_FORMAT,),
        execution_effect="none",
        locality="in_process",
        network_required=False,
        supported_platforms=("platform_independent",),
        cancellation_mode="unsupported",
        simulation_only=True,
    )


_NO_CHANGE_PAYLOAD: Mapping[str, object] = {
    "fixture": "no-change-v1",
    "message": "PCAE deterministic dry simulation completed",
    "proposed_change_count": 0,
}

_SYNTHETIC_CHANGE_CONTENT = "mock dry-run synthetic output\n"
_SYNTHETIC_CHANGE_PAYLOAD: Mapping[str, object] = {
    "fixture": "synthetic-change-v1",
    "message": "PCAE deterministic dry simulation completed with one synthetic proposed change",
    "proposed_change_count": 1,
}

_FAILURE_PAYLOAD: Mapping[str, object] = {
    "fixture": "failure-v1",
    "message": "PCAE deterministic dry simulation fixture reports a simulated runtime failure",
    "proposed_change_count": 0,
}


class MalformedMockAdapter:
    """A dedicated fake adapter used only to test `malformed_result`
    handling (3R §19: "Malformed-result behavior is tested with a
    dedicated fake adapter, not a hidden prompt-triggered mode"). It
    implements the same Protocol but `collect()` returns a value that is
    not a `RuntimeInvocationResult`."""

    def describe(self) -> RuntimeDescriptor:
        return build_mock_descriptor()

    def preflight(self, request: InvocationRequest) -> AdapterPreflightResult:
        return AdapterPreflightResult(capable=True)

    def dispatch(self, envelope: SimulationDispatchEnvelope) -> DispatchReceipt:
        return DispatchReceipt(
            invocation_id=envelope.request.invocation_id,
            attempt_id=envelope.request.attempt_id,
            accepted=True,
        )

    def collect(self, attempt_id: str) -> object:  # type: ignore[override]
        return {"not": "a RuntimeInvocationResult"}

    def cancel(self, attempt_id: str) -> RuntimeCancellationResult:
        return RuntimeCancellationResult(attempt_id=attempt_id, outcome="unsupported")


class MockDryRuntimeAdapter:
    """The built-in, deterministic, fixed-fixture RPAC-001 mock/dry
    adapter (RPAC-REQ-088). Every method is in-process, side-effect-free
    with respect to the filesystem/network/subprocess/credentials, and
    returns the same semantic output for the same normalized request and
    target fixture, every time."""

    def __init__(self) -> None:
        self._pending: dict[str, InvocationRequest] = {}
        self._completed: set[str] = set()

    def describe(self) -> RuntimeDescriptor:
        """Side-effect-free (RPAC-REQ-032)."""
        return build_mock_descriptor()

    def preflight(self, request: InvocationRequest) -> AdapterPreflightResult:
        """Fact-only capability check (RPAC-REQ-032); never dispatches."""
        fixture = _fixture_for(request.runtime_target_id)
        if fixture is None:
            return AdapterPreflightResult(
                capable=False, reasons=("unknown_mock_fixture_target",)
            )
        if request.requested_capability != MOCK_CAPABILITY:
            return AdapterPreflightResult(capable=False, reasons=("capability_mismatch",))
        return AdapterPreflightResult(capable=True)

    def dispatch(self, envelope: SimulationDispatchEnvelope) -> DispatchReceipt:
        """The last allowed mock-v1 operation (3R plan §26): validates
        the envelope, then records the request as pending in-memory
        state ready for `collect()`. Crosses no real effect boundary --
        `execution_effect` on the descriptor is `none` and stays `none`
        for the lifetime of this call."""
        request = envelope.request
        issues = validate_dispatch_envelope(envelope, expected_request=request)
        if issues:
            return DispatchReceipt(
                invocation_id=request.invocation_id,
                attempt_id=request.attempt_id,
                accepted=False,
            )
        self._pending[request.attempt_id] = request
        return DispatchReceipt(
            invocation_id=request.invocation_id,
            attempt_id=request.attempt_id,
            accepted=True,
        )

    def collect(self, attempt_id: str) -> RuntimeInvocationResult:
        """Normalize deterministic fixture data into a
        `RuntimeInvocationResult` (RPAC-REQ-035). Terminal-only: no
        streaming, no partial/pending observation type (RPAC-REQ-033)."""
        request = self._pending.pop(attempt_id, None)
        if request is None:
            raise LookupError(f"unknown_or_already_collected_attempt:{attempt_id}")
        self._completed.add(attempt_id)
        fixture = _fixture_for(request.runtime_target_id)

        if fixture == TARGET_NO_CHANGE:
            return build_runtime_invocation_result(
                request=request,
                terminal_outcome="success",
                structured_payload=_NO_CHANGE_PAYLOAD,
                changed_files=(),
                requesting_agent_id=request.requester_agent_id,
                producer_claim="pcae.mock-dry-fixture",
            )
        if fixture == TARGET_SYNTHETIC_CHANGE:
            content_hash = _content_hash(_SYNTHETIC_CHANGE_CONTENT)
            changed = (
                ChangedFileEntry(
                    path="mock-output.txt",
                    operation="create",
                    content_after=_SYNTHETIC_CHANGE_CONTENT,
                    content_hash_after=content_hash,
                ),
            )
            return build_runtime_invocation_result(
                request=request,
                terminal_outcome="success",
                structured_payload=_SYNTHETIC_CHANGE_PAYLOAD,
                changed_files=changed,
                requesting_agent_id=request.requester_agent_id,
                producer_claim="pcae.mock-dry-fixture",
            )
        if fixture == TARGET_FAILURE:
            return build_runtime_invocation_result(
                request=request,
                terminal_outcome="failure",
                structured_payload=_FAILURE_PAYLOAD,
                changed_files=(),
                error_category=FAILURE_RUNTIME_FAILURE,
                error_subcode="mock_fixed_failure",
                requesting_agent_id=request.requester_agent_id,
                producer_claim="pcae.mock-dry-fixture",
            )
        raise LookupError(f"unknown_mock_fixture_target:{request.runtime_target_id}")

    def cancel(self, attempt_id: str) -> RuntimeCancellationResult:
        """Descriptor-declared `unsupported` cancellation mode
        (RPAC-REQ-032/035, 3R §35): because the adapter completes
        synchronously, there is never a real running window to cancel."""
        if attempt_id in self._completed:
            return RuntimeCancellationResult(attempt_id=attempt_id, outcome="completed_before_cancel")
        if attempt_id in self._pending:
            return RuntimeCancellationResult(attempt_id=attempt_id, outcome="unsupported")
        return RuntimeCancellationResult(attempt_id=attempt_id, outcome="unknown_attempt")


def _fixture_for(runtime_target_id: str) -> str | None:
    return runtime_target_id if runtime_target_id in KNOWN_MOCK_TARGET_FIXTURES else None


def _content_hash(content: str) -> str:
    import hashlib

    return hashlib.sha256(content.encode("utf-8")).hexdigest()
