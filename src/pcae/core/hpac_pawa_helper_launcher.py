"""HPAC-PAWA-HELPER-001 v1.0 — Linux-first one-shot privileged helper
launcher (phase-authorization N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL,
§24-§34, §63-§68).

Composes the already-verified OS-level primitives
(:mod:`pcae.core.hpac_pawa_helper_os`) and the real deployment-metadata
resolver (:mod:`pcae.core.hpac_pawa_helper_store_adapter`) into the actual
end-to-end launch: resolve the current, non-revoked helper installation,
verify its exact executable object, create a private one-shot channel, exec
the verified object as a short-lived child with a closed environment,
authenticate its kernel peer credential, exchange exactly one request/
response, reap the child, and return a bounded typed result.

**Not** a long-lived privileged daemon (§24). **Not** itself an authority —
this module never holds, mints, or forwards an ``HPACWriterCapability`` /
``HPACStoreAuthority`` (§35/§43); it only ever sees the closed
:class:`~pcae.core.hpac_pawa_helper_protocol.HelperResponse` bytes the child
already produced.

Linux-only (§59/§60): any other platform fails closed via
:class:`~pcae.core.hpac_pawa_helper_os.UnsupportedPlatformProfile` before any
protected operation, never a deterministic production downgrade.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Mapping, Optional

from pcae.core.hpac_pawa_helper_os import (
    OneShotChannel,
    PeerCredential,
    UnsupportedPlatformProfile,
    authenticate_peer,
    execute_verified,
    verify_helper_executable,
)
from pcae.core.hpac_pawa_helper_protocol import (
    HelperOperation,
    HelperProtocolError,
    HelperRequest,
    HelperResponse,
    PROTOCOL_VERSION,
)
from pcae.core.hpac_pawa_helper_entrypoint import MAX_FRAME_BYTES, FramingError

#: §31 — the closed environment passed to the exec'd helper. Nothing
#: PYTHONPATH/PYTHONHOME/user-site-related is inherited; only what the
#: entrypoint needs to bootstrap its own bounded state is set explicitly by
#: this launcher at exec time (never taken from the parent's own environ).
_CLOSED_ENV_ALLOWLIST = ("LANG", "LC_ALL")


@dataclass(frozen=True)
class LaunchOutcome:
    """§37/§38 — a bounded, typed transport result. ``response`` is present
    only on a complete request/response exchange; every other case is a
    named transport-level outcome, never a fabricated PERFORMED/REJECTED
    decision and never a signal to retry automatically (§39/§40)."""

    outcome: str  # "completed" | "no_response" | "helper_exit_nonzero" | "helper_signaled"
    response: Optional[HelperResponse]
    helper_pid: int
    helper_exit_status: Optional[int]
    peer_credential: Optional[PeerCredential]


def _child_environment(*, channel_path: str, protected_root: str, installation_id: str, generation: int) -> dict:
    env = {k: os.environ[k] for k in _CLOSED_ENV_ALLOWLIST if k in os.environ}
    env["PAWA_HELPER_CHANNEL_PATH"] = channel_path
    env["PAWA_HELPER_PROTECTED_ROOT"] = protected_root
    env["PAWA_HELPER_INSTALLATION_ID"] = installation_id
    env["PAWA_HELPER_GENERATION"] = str(generation)
    return env


def _response_from_json(raw: bytes) -> HelperResponse:
    payload = json.loads(raw.decode("utf-8"))
    if not isinstance(payload, Mapping):
        raise FramingError("response frame is not a JSON object")
    return HelperResponse(**payload)


def launch_and_exchange(
    request: HelperRequest,
    *,
    helper_path: str,
    expected_sha256: str,
    expected_owner_uid: int,
    deployment_owner_uid: int,
    protected_root: str,
    installation_id: str,
    generation: int,
    expected_root_device: Optional[int] = None,
    channel_directory: Optional[str] = None,
    accept_timeout: float = 10.0,
) -> LaunchOutcome:
    """§24 the actual one-shot launch. Every argument the entrypoint needs is
    resolved by the *caller* of this function from real canonical metadata
    (never accepted here as a bare caller-selected path — see
    :func:`pcae.core.hpac_pawa_helper_store_adapter.resolve_launcher_deployment_metadata`),
    so this function itself never re-reads request-supplied trust facts."""
    if not sys.platform.startswith("linux"):
        raise UnsupportedPlatformProfile(
            f"one-shot launcher is Linux-first; platform {sys.platform!r} is FAIL-CLOSED / NOT IMPLEMENTED"
        )
    if request.protocol_version != PROTOCOL_VERSION:
        raise HelperProtocolError("operation_scope_invalid", "request protocol_version mismatch before launch")
    if request.installation_id != installation_id or request.generation != generation:
        raise HelperProtocolError("descriptor_generation_stale", "request not bound to the resolved current generation")

    verified = verify_helper_executable(
        __import__("pathlib").Path(helper_path),
        expected_sha256=expected_sha256,
        expected_owner_uid=expected_owner_uid,
        expected_root_device=expected_root_device,
    )
    channel = OneShotChannel(directory=__import__("pathlib").Path(channel_directory) if channel_directory else None)
    try:
        env = _child_environment(
            channel_path=str(channel.path),
            protected_root=protected_root,
            installation_id=installation_id,
            generation=generation,
        )
        # §31/§34.4 — no argv-selected operation/module/function: argv[0] is
        # a conventional program-name string only (the kernel's own
        # shebang/binfmt resolution, not this launcher, decides what code
        # actually runs — that decision was already fixed by
        # `verify_helper_executable`'s same-file-object verification).
        argv = ["pawa-helper"]
        pid = execute_verified(verified, argv, env)

        conn = None
        peer_credential = None
        try:
            conn = channel.accept_one(timeout=accept_timeout)
            peer_credential = authenticate_peer(conn, deployment_owner_uid=deployment_owner_uid)

            request_bytes = json.dumps(
                {k: v for k, v in request.__dict__.items()}, sort_keys=True
            ).encode("utf-8")
            if len(request_bytes) > MAX_FRAME_BYTES:
                raise HelperProtocolError("operation_scope_invalid", "request exceeds bounded frame size")
            conn.sendall(len(request_bytes).to_bytes(4, "big") + request_bytes)

            try:
                prefix = conn.recv(4)
                if len(prefix) != 4:
                    raise FramingError("truncated response length prefix")
                length = int.from_bytes(prefix, "big")
                if length == 0 or length > MAX_FRAME_BYTES:
                    raise FramingError("invalid response frame length")
                raw = b""
                while len(raw) < length:
                    chunk = conn.recv(length - len(raw))
                    if not chunk:
                        raise FramingError("truncated response body")
                    raw += chunk
                response = _response_from_json(raw)
            except (FramingError, OSError, ValueError):
                response = None
        finally:
            if conn is not None:
                conn.close()

        # §38/§39 — reap exactly once; a lost response after this point is
        # INDETERMINATE from the launcher's perspective and MUST NOT trigger
        # an automatic retry. The durable replay ledger (consulted only
        # inside the helper) is the sole source of truth for reconciliation.
        _pid, status = os.waitpid(pid, 0)
        if response is not None:
            outcome = "completed"
        elif os.WIFSIGNALED(status):
            outcome = "helper_signaled"
        elif os.WIFEXITED(status) and os.WEXITSTATUS(status) != 0:
            outcome = "helper_exit_nonzero"
        else:
            outcome = "no_response"
        return LaunchOutcome(
            outcome=outcome,
            response=response,
            helper_pid=pid,
            helper_exit_status=status,
            peer_credential=peer_credential,
        )
    finally:
        channel.close()
