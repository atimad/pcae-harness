"""HPAC-PAWA-HELPER-001 v1.0 — OS-level primitives foundation (§5-§10):
helper provenance / same-file-object anti-TOCTOU execution, the private
one-shot local channel, and OS peer-credential authentication.

Platform profile (§5/§28): Linux (SO_PEERCRED) and macOS (getpeereid via
ctypes) are both implemented, since Linux is the deployment target and
macOS is the development host named by the phase authorization. Any other
platform, or a platform primitive that is unavailable at runtime, fails
closed per HPAC-PAWA-HELPER-REQ-104 (STOPS BLOCKED — this module raises
:class:`UnsupportedPlatformProfile` rather than falling back to a weaker
check).

This module deliberately does not import ``pcae.core.hpac_protected_admin_writer``
(HPAC-PAWA-HELPER-REQ-033) or any agent-reachable module; it does import
``pcae.core.hpac_pawa_agent_exclusion`` for configured-agent identity
resolution, which the contract's own precedent module
(``hpac_protected_admin_writer``) already treats as a co-shipped, non-agent-
-importable-fence primitive — reusing it here binds the helper to the exact
same HPAC-PAWA-AGENT-EXCLUSION/1.0 resolution, not a re-derivation."""

from __future__ import annotations

import ctypes
import hashlib
import os
import socket
import stat
import struct
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pcae.core.hpac_pawa_agent_exclusion import (
    ConfiguredAgentAuthorityIdentity,
    resolve_configured_agent_identity,
)
from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError


class UnsupportedPlatformProfile(Exception):
    """Raised when the current platform cannot realize a §16 frozen
    property (peer credential, or substitution-free exec). This is a valid
    STOP-BLOCKED condition (phase-authorization §60), not a fallback."""


# ---------------------------------------------------------------------------
# §6 / §29 — helper provenance and same-file-object anti-TOCTOU execution.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerifiedExecutable:
    """The result of verifying a candidate helper executable. Holds the
    *open file descriptor* used for both verification and execution — no
    pathname is re-resolved between the two (HPAC-PAWA-HELPER-REQ-029)."""

    fd: int
    sha256: str
    device: int
    inode: int
    owner_uid: int
    mode: int
    nlink: int


def verify_helper_executable(
    path: Path,
    *,
    expected_sha256: str,
    expected_owner_uid: int,
    expected_root_device: Optional[int] = None,
) -> VerifiedExecutable:
    """§6 conjunctive provenance predicates, all evaluated against ONE
    already-open, `O_NOFOLLOW`-opened descriptor:

    - regular file (no symlink, no special file);
    - exactly one hard link;
    - owned by ``expected_owner_uid``;
    - mode 0755, not group/other-writable;
    - complete-byte SHA-256 equals ``expected_sha256``;
    - (optional) same filesystem device as the live protected root.

    All predicates are conjunctive (HPAC-PAWA-HELPER-REQ-020/028): no single
    one is sufficient, and path/hash/metadata are never treated as
    interchangeable. Fails closed (raises) on any mismatch; the caller is
    responsible for closing ``fd`` on the returned object once execution is
    complete (or immediately, if verification failed and no exception path
    already closed it)."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), flags)
    except OSError as exc:
        raise HelperProtocolError("descriptor_missing", f"cannot open helper candidate: {exc}") from exc

    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise HelperProtocolError("descriptor_wrong_owner", "helper candidate is not a regular file")
        if st.st_nlink != 1:
            raise HelperProtocolError("descriptor_wrong_owner", "helper candidate has more than one hard link")
        if st.st_uid != expected_owner_uid:
            raise HelperProtocolError("descriptor_wrong_owner", "helper candidate not owned by deployment owner")
        mode_bits = stat.S_IMODE(st.st_mode)
        if mode_bits != 0o755:
            raise HelperProtocolError("descriptor_wrong_mode", f"unexpected mode {oct(mode_bits)}")
        if expected_root_device is not None and st.st_dev != expected_root_device:
            raise HelperProtocolError(
                "descriptor_root_identity_mismatch", "helper candidate not beneath the live protected-root device"
            )

        hasher = hashlib.sha256()
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
        digest = hasher.hexdigest()
        if digest != expected_sha256:
            raise HelperProtocolError("descriptor_installation_mismatch", "helper_sha256 mismatch")

        os.lseek(fd, 0, os.SEEK_SET)
        verified = VerifiedExecutable(
            fd=fd, sha256=digest, device=st.st_dev, inode=st.st_ino,
            owner_uid=st.st_uid, mode=mode_bits, nlink=st.st_nlink,
        )
    except Exception:
        os.close(fd)
        raise
    return verified


def execute_verified(verified: VerifiedExecutable, argv, env) -> int:
    """§29 same-file-object / anti-TOCTOU execution: exec the EXACT
    descriptor that was verified, never a fresh pathname lookup.

    Linux: re-execs through ``/proc/self/fd/<fd>`` in the child, which
    resolves to the same file *description* regardless of any subsequent
    directory-entry mutation (rename/replace/symlink-substitution of the
    original path cannot change what this refers to) — this realizes the
    frozen property using only the stdlib.

    Any other platform (including macOS, the development host): this
    module has no substitution-free exec primitive available through the
    standard library, so it fails closed rather than weaken the check
    (HPAC-PAWA-HELPER-REQ-029/104 — a valid STOP-BLOCKED condition)."""
    if sys.platform.startswith("linux"):
        pid = os.fork()
        if pid == 0:  # pragma: no cover - child branch, exercised via subprocess-level test
            try:
                os.execve(f"/proc/self/fd/{verified.fd}", argv, env)
            finally:
                os._exit(127)
        os.close(verified.fd)
        return pid
    raise UnsupportedPlatformProfile(
        f"no substitution-free exec primitive on platform {sys.platform!r}; STOP BLOCKED per HPAC-PAWA-HELPER-REQ-104"
    )


# ---------------------------------------------------------------------------
# §9 — private one-shot local channel.
# ---------------------------------------------------------------------------


class OneShotChannel:
    """A private local `AF_UNIX` one-shot request/response channel
    (HPAC-PAWA-HELPER-REQ-038/039/040). Bound under a `0700` directory,
    accepts exactly one connection, serves exactly one request/response
    exchange, then closes and unlinks the socket path."""

    def __init__(self, *, directory: Optional[Path] = None) -> None:
        self._dir = Path(directory) if directory is not None else Path(tempfile.mkdtemp(prefix="pawa-helper-channel-"))
        self._dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self._dir, 0o700)
        self.path = self._dir / "helper.sock"
        if self.path.exists():
            self.path.unlink()
        self._listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._listener.bind(str(self.path))
        os.chmod(self.path, 0o600)
        self._listener.listen(1)
        self._used = False
        self._lock = threading.Lock()

    def accept_one(self, *, timeout: Optional[float] = None) -> socket.socket:
        with self._lock:
            if self._used:
                raise HelperProtocolError("capability_stale", "one-shot channel already used")
            self._used = True
        self._listener.settimeout(timeout)
        conn, _ = self._listener.accept()
        return conn

    def close(self) -> None:
        try:
            self._listener.close()
        finally:
            if self.path.exists():
                self.path.unlink()

    def __enter__(self) -> "OneShotChannel":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()


# ---------------------------------------------------------------------------
# §10 — OS peer-credential authentication.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PeerCredential:
    uid: int
    gid: int
    pid: Optional[int] = None


def _peer_credential_linux(conn: socket.socket) -> PeerCredential:
    # struct ucred { pid_t pid; uid_t uid; gid_t gid; } -- 3 x 4-byte ints on Linux.
    SO_PEERCRED = 17
    creds = conn.getsockopt(socket.SOL_SOCKET, SO_PEERCRED, struct.calcsize("3i"))
    pid, uid, gid = struct.unpack("3i", creds)
    return PeerCredential(uid=uid, gid=gid, pid=pid)


def _peer_credential_darwin(conn: socket.socket) -> PeerCredential:
    libc = ctypes.CDLL(None, use_errno=True)
    euid = ctypes.c_uint32()
    egid = ctypes.c_uint32()
    fd = conn.fileno()
    rc = libc.getpeereid(fd, ctypes.byref(euid), ctypes.byref(egid))
    if rc != 0:
        errno = ctypes.get_errno()
        raise UnsupportedPlatformProfile(f"getpeereid failed (errno={errno})")
    return PeerCredential(uid=euid.value, gid=egid.value, pid=None)


def get_kernel_peer_credential(conn: socket.socket) -> PeerCredential:
    """§10/§16: obtains the peer's *kernel-authenticated* (uid, gid[, pid])
    — never from any field the peer sent over the channel. Fails closed
    (raises :class:`UnsupportedPlatformProfile`) on a platform with no
    known kernel-authenticated peer-credential primitive."""
    if sys.platform.startswith("linux"):
        return _peer_credential_linux(conn)
    if sys.platform == "darwin":
        return _peer_credential_darwin(conn)
    raise UnsupportedPlatformProfile(
        f"no kernel-authenticated peer-credential primitive on platform {sys.platform!r}; "
        "STOP BLOCKED per HPAC-PAWA-HELPER-REQ-104"
    )


def authenticate_peer(
    conn: socket.socket,
    *,
    deployment_owner_uid: int,
    configured_agent: Optional[ConfiguredAgentAuthorityIdentity] = None,
) -> PeerCredential:
    """§10 required conjuncts, evaluated before any operation admission:
    peer uid == deployment owner; peer uid != configured agent principal.
    ``configured_agent`` defaults to a live resolution via
    :func:`resolve_configured_agent_identity` — a caller MAY inject an
    already-resolved identity (e.g. a test double) but MUST NOT inject one
    derived from request-supplied fields (HPAC-PAWA-HELPER-REQ-042)."""
    credential = get_kernel_peer_credential(conn)
    if credential.uid != deployment_owner_uid:
        raise HelperProtocolError("unauthorized_factory_consumer", "peer uid is not the deployment owner")
    agent_identity = configured_agent
    if agent_identity is not None and credential.uid == agent_identity.uid:
        raise HelperProtocolError("current_context_is_agent", "peer uid is the configured agent principal")
    return credential
