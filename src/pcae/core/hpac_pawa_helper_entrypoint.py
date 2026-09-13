"""HPAC-PAWA-HELPER-001 v1.0 — one-shot helper process entrypoint
(phase-authorization N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IMPL, §35-§39).

This is the narrow process that a Linux launcher (``hpac_pawa_helper_launcher``)
execs as the short-lived privileged child. It:

1. connects to the private one-shot channel the launcher created (§27);
2. reads **exactly one** bounded, deterministically-framed request (§36);
3. dispatches it through the existing closed §13 dispatch table — this
   module adds no new operation, no reflection, no eval/exec, no CLI
   argument selecting a module/function (§35);
4. writes **exactly one** bounded response frame (§37);
5. closes the connection and exits.

No interactive shell, no second request/response cycle, no generic
administration surface. A malformed or oversized request is a protocol
failure (fail closed), never a trust decision (§37).
"""

from __future__ import annotations

import os
import socket
import struct
import sys
from dataclasses import asdict
from typing import Mapping, Optional

from pcae.core.hpac_pawa_helper_operations import CLOSED_DISPATCH_TABLE
from pcae.core.hpac_pawa_helper_protocol import (
    HelperContext,
    HelperProtocolError,
    HelperRequest,
    HelperResponse,
    ReplayLedger,
    dispatch,
    response_leaks_authority,
)

#: §36 bounded request/response framing (HPAC-PAWA-HELPER-REQ-046/047 closed
#: schema; there is no legitimate reason for a request this large — the
#: closed operation_params never carries a path/blob/file).
MAX_FRAME_BYTES = 1 << 20  # 1 MiB
_LEN_STRUCT = struct.Struct(">I")  # 4-byte big-endian length prefix


class FramingError(Exception):
    """A transport-level framing failure — never treated as trust, never
    retried automatically by this module."""


def _recv_exact(conn: socket.socket, n: int) -> bytes:
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = conn.recv(remaining)
        if not chunk:
            raise FramingError(f"connection closed after {n - remaining} of {n} expected bytes")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_one_frame(conn: socket.socket, *, max_bytes: int = MAX_FRAME_BYTES) -> bytes:
    """§36 — exactly one bounded frame: 4-byte big-endian length prefix then
    exactly that many bytes. Oversized/truncated/zero-length-prefix-but-EOF
    all fail closed via :class:`FramingError`."""
    prefix = conn.recv(4, socket.MSG_WAITALL) if hasattr(socket, "MSG_WAITALL") else _recv_exact(conn, 4)
    if len(prefix) != 4:
        raise FramingError("truncated length prefix")
    (length,) = _LEN_STRUCT.unpack(prefix)
    if length == 0:
        raise FramingError("zero-length request frame")
    if length > max_bytes:
        raise FramingError(f"oversized frame: {length} > {max_bytes}")
    return _recv_exact(conn, length)


def write_one_frame(conn: socket.socket, payload: bytes) -> None:
    if len(payload) > MAX_FRAME_BYTES:
        raise FramingError("response frame exceeds bound — refusing to send")
    conn.sendall(_LEN_STRUCT.pack(len(payload)) + payload)


def _response_to_json_bytes(response: HelperResponse) -> bytes:
    import json

    return json.dumps(asdict(response), sort_keys=True).encode("utf-8")


def handle_one_request(
    conn: socket.socket,
    *,
    context: HelperContext,
    handlers: Mapping[str, object] = CLOSED_DISPATCH_TABLE,
) -> Optional[HelperResponse]:
    """§35-§38 — read exactly one request, dispatch, respond exactly once,
    never raise a bare framing/parse error back to the caller as a trust
    decision: any pre-dispatch failure produces no response at all (the
    launcher must treat "no response" as failure, not success) and the
    connection is closed."""
    import json

    try:
        raw = read_one_frame(conn)
    except FramingError:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("request frame is not a JSON object")
        request = HelperRequest.from_mapping(payload)
    except (ValueError, UnicodeDecodeError, HelperProtocolError):
        return None

    response = dispatch(request, context, handlers)
    if response_leaks_authority(response):
        # Defence in depth beyond dispatch()'s own assertion: never let a
        # transport bug turn an internal assertion failure into a sent
        # response.
        return None
    write_one_frame(conn, _response_to_json_bytes(response))
    return response


def run_one_shot(
    *,
    channel_path: str,
    context: HelperContext,
    handlers: Mapping[str, object] = CLOSED_DISPATCH_TABLE,
    connect_timeout: float = 5.0,
) -> int:
    """The actual child-process entrypoint body: connect to the launcher's
    rendezvous socket, process exactly one request, exit. Returns a process
    exit code (0 on any handled outcome — including a REJECTED response;
    non-zero only for a transport-level failure the launcher must not
    confuse with a protocol REJECTED)."""
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    conn.settimeout(connect_timeout)
    try:
        conn.connect(channel_path)
    except OSError:
        return 2
    try:
        response = handle_one_request(conn, context=context, handlers=handlers)
    finally:
        conn.close()
    return 0 if response is not None else 3


def main(argv=None) -> int:  # pragma: no cover - exercised via subprocess integration tests
    """Minimal process entrypoint. Reads its bootstrap coordinates from a
    closed set of environment variables the launcher sets (§31 — never from
    argv, never a caller-selected module/function). No shell, no `PATH`
    lookup, no interactive loop."""
    channel_path = os.environ.get("PAWA_HELPER_CHANNEL_PATH")
    protected_root = os.environ.get("PAWA_HELPER_PROTECTED_ROOT")
    installation_id = os.environ.get("PAWA_HELPER_INSTALLATION_ID")
    generation_raw = os.environ.get("PAWA_HELPER_GENERATION")
    if not channel_path or not protected_root or not installation_id or not generation_raw:
        return 2

    from pcae.core.hpac_pawa_helper_protocol import ProtectedStoreFoundation
    from pcae.core.hpac_pawa_helper_replay_state import open_durable_replay_ledger
    from pcae.core.hpac_pawa_helper_protocol import EvidenceStager, CLOSED_OPERATIONS

    ledger = open_durable_replay_ledger(
        protected_root=protected_root, installation_id=installation_id, generation=int(generation_raw)
    )
    context = HelperContext(
        replay_ledger=ledger,
        evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS,
        store=ProtectedStoreFoundation(),
    )
    return run_one_shot(channel_path=channel_path, context=context)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
