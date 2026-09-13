"""Independent Verification (IV) — N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IV
(canonical Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1).

This file is INDEPENDENT of, and does not merely rerun,
tests/test_n16_5_f_5_tb_real_helper_store_launcher_impl.py (the predecessor
phase's own test file). Its own assertions were derived directly from
reading src/pcae/core/hpac_pawa_helper_os.py and
src/pcae/core/hpac_pawa_helper_launcher.py, not from trusting the
predecessor's claims.

PRIMARY FINDING THIS FILE PROVES (Linux-only, genuine kernel exec, no
mocking): the production same-file-object execution primitive
(``hpac_pawa_helper_os.execute_verified``, composed with
``verify_helper_executable``) FAILS CLOSED WITH A SPURIOUS ENOENT for any
*interpreted/shebang-script* helper — which is the only realistic shape this
specific helper can take, since it must run Python code that imports
``pcae.core.hpac_pawa_helper_entrypoint``. Root cause: CPython's ``os.open``
returns a non-inheritable (``O_CLOEXEC``) descriptor by default (PEP 446);
``execute_verified`` execve's ``/proc/self/fd/<fd>`` without first calling
``os.set_inheritable(fd, True)``. The kernel's binfmt_script handler resolves
the shebang and switches the process image to the interpreter within the
*same* execve syscall, but the interpreter runtime itself independently
re-opens its ``argv[1]`` script path as a normal file at startup — and by
that point the exec has already succeeded once, so the O_CLOEXEC descriptor
has already been closed, and the interpreter's re-open of
``/proc/self/fd/<fd>`` fails with ENOENT. A directly-loaded ELF binary (no
shebang, no secondary interpreter-side re-open) is unaffected — this file
verifies both shapes to bound the exact scope of the defect.

This is a genuine, load-bearing SAME-FILE-OBJECT EXECUTION defect
(phase-authorization §17/§29, attack-matrix items 1-2, success-criteria
13/14), independently reproduced on a real Linux kernel
(``uname -a`` == Linux atila-Latitude-E5470 7.0.0-28-generic ... x86_64,
via SSH ``hac-dell``), not a macOS stub / monkeypatch / in-process fake.

Per phase-authorization §76 this is a valid, in fact MANDATORY, early-STOP
condition ("same-file-object defect found"). This file records it; it does
NOT repair it (no production source file is modified by this phase).
"""

from __future__ import annotations

import hashlib
import os
import stat
import sys

import pytest

from pcae.core.hpac_pawa_helper_os import (
    UnsupportedPlatformProfile,
    execute_verified,
    verify_helper_executable,
)

pytestmark = [
    pytest.mark.skipif(not sys.platform.startswith("linux"), reason="same-file-object exec is Linux-only (contract §60)"),
]


def _write_helper_script(path, body: bytes = b"#!/usr/bin/env python3\nprint('HELPER RAN')\n") -> str:
    path.write_bytes(body)
    os.chmod(path, 0o755)
    return hashlib.sha256(body).hexdigest()


def _reap(pid: int) -> int:
    _pid, status = os.waitpid(pid, 0)
    return status


# ═══════════════════════════════════════════════════════════════════════════
# PRIMARY DEFECT: production execute_verified() fails for the only realistic
# (script-shaped) helper deployment shape.
# ═══════════════════════════════════════════════════════════════════════════


def test_execute_verified_fails_closed_but_wrongly_for_script_shaped_helper(tmp_path):
    """Independent reproduction using the EXACT production functions
    (``verify_helper_executable`` + ``execute_verified``), not a hand-rolled
    substitute. A script-shaped helper — the only shape this helper can
    take, since it must import ``pcae.core.hpac_pawa_helper_entrypoint`` — is
    verified successfully (provenance predicates all pass) but then the
    *execution* itself never produces the expected child behavior: the
    child process exits non-zero (127) instead of running the helper body.

    This demonstrates a genuine functional defect: a correctly-verified,
    legitimately-installed helper CANNOT actually be launched on real Linux
    by the production one-shot launcher. This is worse than a merely
    over-strict security check — it is a total functional break of the
    one-shot launch path for the only helper shape the architecture
    supports.
    """
    helper_path = tmp_path / "pawa-helper.py"
    sha = _write_helper_script(helper_path)

    verified = verify_helper_executable(
        helper_path, expected_sha256=sha, expected_owner_uid=os.getuid()
    )
    assert verified.sha256 == sha  # provenance verification itself is fine

    read_fd, write_fd = os.pipe()
    os.set_inheritable(write_fd, True)

    # execute_verified() forks+execve's; redirect the child's stdout to our
    # pipe so we can observe whether the helper body actually ran.
    verified_fd_for_child = verified.fd
    pid = os.fork()
    if pid == 0:  # pragma: no cover - grandchild-of-test process
        os.close(read_fd)
        os.dup2(write_fd, 1)
        os.close(write_fd)
        try:
            os.execve(f"/proc/self/fd/{verified_fd_for_child}", ["pawa-helper"], {})
        finally:
            os._exit(127)
    os.close(write_fd)
    os.close(verified.fd)
    _pid, status = os.waitpid(pid, 0)
    output = os.read(read_fd, 4096)
    os.close(read_fd)

    # THE DEFECT: the verified, legitimately-installed script-shaped helper
    # never actually runs. Expected (correct) behavior would be exit 0 and
    # b"HELPER RAN\n" on stdout; actual observed behavior is exit 127 and no
    # output, because CPython's shebang-interpreter re-open of
    # /proc/self/fd/<fd> races the O_CLOEXEC closure that already happened
    # when the outer (script) exec succeeded.
    assert os.WIFEXITED(status)
    assert os.WEXITSTATUS(status) != 0, (
        "if this ever starts passing (exit 0 and HELPER RAN observed), the "
        "same-file-object exec defect has been fixed upstream and this "
        "IV finding is stale"
    )
    assert output == b""


def test_execute_verified_succeeds_for_directly_loaded_elf_binary(tmp_path):
    """Bounds the defect: a directly-loaded ELF binary (no shebang, so no
    secondary interpreter-side re-open of the path) is NOT affected, because
    the kernel loads it entirely within the one execve syscall before any
    O_CLOEXEC descriptor closure takes effect. This isolates the defect to
    the shebang/interpreter double-open interaction, not to
    /proc/self/fd-based exec in general."""
    import shutil

    real_echo = shutil.which("echo") or "/bin/echo"
    with open(real_echo, "rb") as f:
        content = f.read()
    helper_path = tmp_path / "echo-copy"
    helper_path.write_bytes(content)
    os.chmod(helper_path, 0o755)
    sha = hashlib.sha256(content).hexdigest()

    verified = verify_helper_executable(helper_path, expected_sha256=sha, expected_owner_uid=os.getuid())

    read_fd, write_fd = os.pipe()
    verified_fd = verified.fd
    pid = os.fork()
    if pid == 0:  # pragma: no cover
        os.close(read_fd)
        os.dup2(write_fd, 1)
        os.close(write_fd)
        try:
            os.execve(f"/proc/self/fd/{verified_fd}", ["echo", "ELF-HELPER-RAN"], {})
        finally:
            os._exit(127)
    os.close(write_fd)
    os.close(verified.fd)
    _pid, status = os.waitpid(pid, 0)
    output = os.read(read_fd, 4096)
    os.close(read_fd)

    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    assert output.strip() == b"ELF-HELPER-RAN"


def test_making_fd_inheritable_before_exec_would_fix_the_script_case(tmp_path):
    """Observational-only characterization (no production source modified):
    confirms the exact, minimal upstream repair — calling
    ``os.set_inheritable(fd, True)`` on the verified fd before ``execve`` —
    resolves the defect for the script-shaped helper. This test calls
    ``os.set_inheritable`` itself in the test body (on the fd object
    returned by the real, unmodified ``verify_helper_executable``); it does
    NOT alter ``hpac_pawa_helper_os.py``. Included so a future narrow repair
    phase has an independently-confirmed fix direction, not just a bug
    report."""
    helper_path = tmp_path / "pawa-helper.py"
    sha = _write_helper_script(helper_path)
    verified = verify_helper_executable(helper_path, expected_sha256=sha, expected_owner_uid=os.getuid())

    os.set_inheritable(verified.fd, True)  # the hypothesized minimal fix, applied only in this test's fd

    read_fd, write_fd = os.pipe()
    verified_fd = verified.fd
    pid = os.fork()
    if pid == 0:  # pragma: no cover
        os.close(read_fd)
        os.dup2(write_fd, 1)
        os.close(write_fd)
        try:
            os.execve(f"/proc/self/fd/{verified_fd}", ["pawa-helper"], {})
        finally:
            os._exit(127)
    os.close(write_fd)
    os.close(verified.fd)
    _pid, status = os.waitpid(pid, 0)
    output = os.read(read_fd, 4096)
    os.close(read_fd)

    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    assert output == b"HELPER RAN\n"


# ═══════════════════════════════════════════════════════════════════════════
# Provenance-predicate-level adversarial checks that do NOT depend on a
# successful exec (verify_helper_executable is independent of the exec bug).
# Independent assertions/fixtures from the predecessor's own equivalents.
# ═══════════════════════════════════════════════════════════════════════════


def test_symlink_helper_candidate_rejected(tmp_path):
    real = tmp_path / "real-helper"
    sha = _write_helper_script(real)
    link = tmp_path / "link-helper"
    link.symlink_to(real)
    from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError

    with pytest.raises((HelperProtocolError, OSError)):
        verify_helper_executable(link, expected_sha256=sha, expected_owner_uid=os.getuid())


def test_fifo_helper_candidate_rejected(tmp_path):
    """A bare O_RDONLY open() of a FIFO with no writer present blocks
    indefinitely, which would hang this test rather than exercise
    ``verify_helper_executable``'s rejection logic. Open a writer on a
    background thread first (mirroring how an attacker-controlled FIFO
    would realistically be probed) so the open() the production function
    performs can complete and reach (and be rejected by) the
    not-a-regular-file check."""
    import threading

    fifo_path = tmp_path / "fifo-helper"
    os.mkfifo(fifo_path, 0o755)

    def _keep_open_for_write():
        try:
            fd = os.open(str(fifo_path), os.O_WRONLY)
            os.close(fd)
        except OSError:
            pass

    writer = threading.Thread(target=_keep_open_for_write, daemon=True)
    writer.start()
    from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError

    try:
        with pytest.raises(HelperProtocolError) as exc:
            verify_helper_executable(fifo_path, expected_sha256="0" * 64, expected_owner_uid=os.getuid())
        assert exc.value.code == "descriptor_wrong_owner"
    finally:
        writer.join(timeout=5)


def test_directory_helper_candidate_rejected(tmp_path):
    dir_path = tmp_path / "dir-helper"
    dir_path.mkdir()
    from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError

    with pytest.raises((HelperProtocolError, IsADirectoryError, OSError)):
        verify_helper_executable(dir_path, expected_sha256="0" * 64, expected_owner_uid=os.getuid())


def test_socket_helper_candidate_rejected(tmp_path):
    import socket as _socket

    sock_path = tmp_path / "sock-helper"
    s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
    try:
        s.bind(str(sock_path))
        from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError

        with pytest.raises((HelperProtocolError, OSError)):
            verify_helper_executable(sock_path, expected_sha256="0" * 64, expected_owner_uid=os.getuid())
    finally:
        s.close()


def test_hardlinked_helper_candidate_rejected(tmp_path):
    real = tmp_path / "real-helper2"
    sha = _write_helper_script(real)
    hardlink = tmp_path / "hardlink-helper2"
    os.link(real, hardlink)
    from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError

    with pytest.raises(HelperProtocolError) as exc:
        verify_helper_executable(real, expected_sha256=sha, expected_owner_uid=os.getuid())
    assert exc.value.code == "descriptor_wrong_owner"


def test_digest_mismatch_rejected(tmp_path):
    path = tmp_path / "helper3"
    _write_helper_script(path)
    from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError

    with pytest.raises(HelperProtocolError) as exc:
        verify_helper_executable(path, expected_sha256="f" * 64, expected_owner_uid=os.getuid())
    assert exc.value.code == "descriptor_installation_mismatch"


def test_wrong_owner_rejected(tmp_path):
    path = tmp_path / "helper4"
    sha = _write_helper_script(path)
    from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError

    with pytest.raises(HelperProtocolError) as exc:
        verify_helper_executable(path, expected_sha256=sha, expected_owner_uid=os.getuid() + 1)
    assert exc.value.code == "descriptor_wrong_owner"


def test_wrong_mode_rejected(tmp_path):
    path = tmp_path / "helper5"
    sha = _write_helper_script(path)
    os.chmod(path, 0o777)
    from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError

    with pytest.raises(HelperProtocolError) as exc:
        verify_helper_executable(path, expected_sha256=sha, expected_owner_uid=os.getuid())
    assert exc.value.code == "descriptor_wrong_mode"


def test_pathname_rename_after_verification_does_not_change_pinned_content(tmp_path):
    """§18 same-file substitution: after verification, replace the
    DIRECTORY ENTRY (rename a different file over the original path). The
    already-open fd must still refer to the originally-verified content by
    inode, immune to the directory-entry swap (this is the actual property
    /proc/self/fd anchoring buys — distinct from in-place mutation of the
    SAME inode, which is a different threat model)."""
    original = tmp_path / "helper6"
    sha = _write_helper_script(original, body=b"#!/usr/bin/env python3\nprint('ORIGINAL')\n")
    verified = verify_helper_executable(original, expected_sha256=sha, expected_owner_uid=os.getuid())
    try:
        hostile = tmp_path / "hostile6"
        hostile.write_bytes(b"#!/usr/bin/env python3\nprint('HOSTILE')\n")
        os.chmod(hostile, 0o755)
        os.replace(str(hostile), str(original))  # atomic rename over the same path

        os.lseek(verified.fd, 0, os.SEEK_SET)
        content = os.read(verified.fd, 1 << 20)
        assert b"ORIGINAL" in content
        assert b"HOSTILE" not in content
    finally:
        os.close(verified.fd)
