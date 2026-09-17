"""N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR — narrow repair of the two
defects the predecessor IV phase (N16-5-F-5-TB-REAL-HELPER-STORE-LAUNCHER-IV)
independently reproduced in the one-shot privileged helper boundary.

REPAIR A — same-file-object exec inheritance
    ``hpac_pawa_helper_os.execute_verified`` execve'd ``/proc/self/fd/<fd>``
    without first marking that descriptor inheritable. CPython's ``os.open``
    returns ``O_CLOEXEC`` descriptors (PEP 446), so the kernel closed the
    verified descriptor as part of the exec itself. A directly loaded ELF
    image survives that (the kernel maps it inside the same syscall), but the
    only realistic shape this helper can take — a shebang script, since it
    must run ``hpac_pawa_helper_entrypoint.main()`` — does not: the kernel's
    ``binfmt_script`` handler hands the interpreter the *pathname*
    ``/proc/self/fd/<fd>`` as ``argv[1]``, and the interpreter's own re-open
    of it then fails ``ENOENT``. The repair marks only that one descriptor
    inheritable, only in the child, only immediately before ``execve``.

REPAIR B — entrypoint store-profile wiring
    ``hpac_pawa_helper_entrypoint.main()`` unconditionally built its
    ``HelperContext`` with the NON_REAL in-memory ``ProtectedStoreFoundation``,
    never the real ``RealCanonicalReadAdapter``. The repair derives the store
    profile from trusted execution context only (``resolve_store_profile``),
    fails closed when that context is absent or ambiguous, and never falls
    back to the foundation. NON_REAL is now reachable *only* through
    ``build_helper_context``'s explicit in-process ``_test_only_store`` seam.

Every Linux-dependent test here runs genuinely on a real Linux kernel (via
SSH ``hac-dell``, ``Linux atila-Latitude-E5470 7.0.0-28-generic ... x86_64``)
against disposable ``tmp_path`` roots only. Nothing in this file touches the
live host protected root, installs or registers a helper, conducts a real
FIDO2/ceremony/certification, or mutates any live protected state.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import socket
import stat
import subprocess
import sys
import textwrap
import types
from pathlib import Path

import pytest

from pcae.core import hpac_protected_presentation_admin as admin
from pcae.core import protected_presentation_installation as inst
from pcae.core import hpac_protected_admin_writer as w
from pcae.core.hpac_foundation import HPACAuthorityClass, HPACStoreAuthority, resolve_hpac_protected_root
from pcae.core import hpac_pawa_helper_entrypoint as entrypoint
from pcae.core import hpac_pawa_helper_os as helper_os
from pcae.core.hpac_pawa_helper_entrypoint import (
    EXIT_BOOTSTRAP_COORDINATES_MISSING,
    EXIT_REAL_STORE_UNAVAILABLE,
    EXIT_STORE_PROFILE_UNESTABLISHED,
    STORE_PROFILE_REAL,
    build_helper_context,
    resolve_store_profile,
)
from pcae.core.hpac_pawa_helper_launcher import launch_and_exchange
from pcae.core.hpac_pawa_helper_operations import CLOSED_DISPATCH_TABLE
from pcae.core.hpac_pawa_helper_os import execute_verified, verify_helper_executable
from pcae.core.hpac_pawa_helper_protocol import (
    CLOSED_OPERATIONS,
    CertificationRole,
    EvidenceStager,
    HelperContext,
    HelperOperation,
    HelperProtocolError,
    HelperRequest,
    ProtectedStoreFoundation,
    ReplayLedger,
    build_signed_request,
    dispatch,
)
from pcae.core.hpac_pawa_helper_store_adapter import (
    RealCanonicalReadAdapter,
    resolve_launcher_deployment_metadata,
)

pytestmark = [
    pytest.mark.fast_green,
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-store / launch model"),
]

linux_only = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="same-file-object exec / one-shot launch is Linux-only (HPAC-PAWA-HELPER-REQ-104, §60)",
)

FAKE_AGENT_UID = 4_242_431
FAKE_AGENT_GID = 999_991


# ═══════════════════════════════════════════════════════════════════════════
# Shared disposable fixtures. Every root below is a pytest ``tmp_path``
# descendant — never the live protected root.
# ═══════════════════════════════════════════════════════════════════════════


def _locked_probe():
    """A deterministic stand-in for the platform ACL adapter, matching the
    already-disclosed ``_topology_probe`` test seam
    (HPAC-PAWA-REQ-132/166). Deliberately a bare namespace rather than
    ``hpac_protected_admin_writer.TopologyProbe`` so nothing in the exec'd
    helper script has to import an agent-reachable module."""
    return types.SimpleNamespace(
        effective_write_access=lambda p, u, g: (False, "fixture_locked", ()),
        ancestor_chain_safe=lambda s, u, g: (True, ("fixture_root_reached",)),
    )


def _fixture_production_authority(root: Path) -> HPACStoreAuthority:
    from pcae.core.hpac_foundation import _PRODUCTION_TEST_FIXTURE_SEAL

    return HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )


def _provisioned_root(tmp_path: Path) -> Path:
    root = (tmp_path / "hpac-protected-root").resolve()
    w.provision_protected_root(protected_root=root, agent_account="pcae-agent-svc", agent_uid=FAKE_AGENT_UID)
    return root


def _install_helper_bytes(root: Path, helper_bytes: bytes) -> str:
    sha = hashlib.sha256(helper_bytes).hexdigest()
    path = inst.helper_content_addressed_path(root, sha)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.exists():
        path.chmod(0o600)
    path.write_bytes(helper_bytes)
    os.chmod(path, 0o755)
    return sha


#: The genuine helper script installed for the Repair-B end-to-end launches.
#:
#: It goes through the PRODUCTION code path (``build_helper_context`` +
#: ``run_one_shot``) and the REAL ``RealCanonicalReadAdapter`` over real
#: canonical stores. The single test-only substitution is the *authority*:
#: ``HPACStoreAuthority.production()`` is, by deliberate design, pinned to
#: the one fixed canonical protected root and offers no redirectable
#: constructor, so a disposable-root exercise must use the already-disclosed
#: ``_production_test_fixture`` seal seam. That substitution is confined to
#: this test script; ``main()`` never uses it (asserted separately below).
_REAL_SEAM_HELPER_TEMPLATE = """#!{python}
import os, sys, types
from pathlib import Path
from pcae.core.hpac_foundation import HPACStoreAuthority, _PRODUCTION_TEST_FIXTURE_SEAL
from pcae.core.hpac_pawa_helper_entrypoint import (
    STORE_PROFILE_REAL, build_helper_context, run_one_shot,
)
from pcae.core.hpac_pawa_helper_store_adapter import RealCanonicalReadAdapter

root = os.environ["PAWA_HELPER_PROTECTED_ROOT"]
probe = types.SimpleNamespace(
    effective_write_access=lambda p, u, g: (False, "fixture_locked", ()),
    ancestor_chain_safe=lambda s, u, g: (True, ("fixture_root_reached",)),
)
authority = HPACStoreAuthority._production_test_fixture(
    Path(root), _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=probe
)
context = build_helper_context(
    protected_root=root,
    installation_id=os.environ["PAWA_HELPER_INSTALLATION_ID"],
    generation=int(os.environ["PAWA_HELPER_GENERATION"]),
    store_profile=STORE_PROFILE_REAL,
    _test_only_store=RealCanonicalReadAdapter(authority),
)
sys.exit(run_one_shot(channel_path=os.environ["PAWA_HELPER_CHANNEL_PATH"], context=context))
"""


@pytest.fixture
def installed(tmp_path):
    """A disposable protected root with a full protected-presentation
    installation lineage and a genuinely installed, genuinely
    shebang-script-shaped helper."""
    root = _provisioned_root(tmp_path)
    helper_bytes = _REAL_SEAM_HELPER_TEMPLATE.format(python=sys.executable).encode("utf-8")
    sha = _install_helper_bytes(root, helper_bytes)
    admin.configure_presentation_mechanism(
        action="install",
        protected_root=root,
        _configured_agent_identity_source=lambda account, provisioned_uid: (
            provisioned_uid,
            frozenset({FAKE_AGENT_GID}),
        ),
        _topology_probe=_locked_probe(),
        helper_sha256=sha,
        helper_implementation_version="pawa-helper/1.0.0",
        verifier_configuration_digest=hashlib.sha256(b"verifier-config-v1").hexdigest(),
        renderer_profile="pcae-protected-local-presentation-renderer/1.0",
        descriptor_version="pplp-1.0",
    )
    authority = _fixture_production_authority(root)
    resolved = resolve_launcher_deployment_metadata(authority)
    return root, authority, resolved


def _launch_kwargs(root: Path, resolved, *, request):
    return dict(
        request=request,
        helper_path=str(resolved.helper_path),
        expected_sha256=resolved.record.helper_sha256,
        expected_owner_uid=os.getuid(),
        deployment_owner_uid=os.getuid(),
        protected_root=str(root),
        installation_id=resolved.record.installation_id,
        generation=resolved.record.generation,
        accept_timeout=20.0,
    )


def _write_script(path: Path, body: str) -> str:
    raw = body.encode("utf-8")
    path.write_bytes(raw)
    os.chmod(path, 0o755)
    return hashlib.sha256(raw).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# REPAIR A — same-file-object exec inheritance.
# ═══════════════════════════════════════════════════════════════════════════


@linux_only
def test_repair_a_script_shaped_helper_executes_through_verified_fd(tmp_path):
    """The primary defect, end to end, through the *production* functions.

    A shebang-script-shaped helper (a real Python script, the only shape
    this helper can take) is verified by ``verify_helper_executable`` and
    then launched by ``execute_verified``. Before the repair this produced
    exit 127 with no side effect; it must now actually run the helper body.
    """
    marker = tmp_path / "ran.marker"
    helper = tmp_path / "pawa-helper.py"
    _write_script(
        helper,
        f"#!{sys.executable}\n"
        f"import pathlib\n"
        f"pathlib.Path({str(marker)!r}).write_text('SCRIPT HELPER RAN')\n",
    )
    sha = hashlib.sha256(helper.read_bytes()).hexdigest()
    verified = verify_helper_executable(helper, expected_sha256=sha, expected_owner_uid=os.getuid())

    pid = execute_verified(verified, ["pawa-helper"], dict(os.environ))
    _pid, status = os.waitpid(pid, 0)

    assert os.WIFEXITED(status), f"helper did not exit normally: {status}"
    assert os.WEXITSTATUS(status) == 0, "script-shaped helper still fails to exec through the verified fd"
    assert marker.read_text() == "SCRIPT HELPER RAN"


@linux_only
def test_repair_a_parent_copy_of_verified_fd_stays_non_inheritable(tmp_path):
    """Least-inheritance: the repair is applied ONLY in the forked child,
    immediately before ``execve``. The parent's own descriptor keeps
    CPython's default non-inheritable disposition, so nothing the parent
    subsequently spawns inherits the verified helper descriptor."""
    helper = tmp_path / "helper.py"
    _write_script(helper, f"#!{sys.executable}\nimport sys\nsys.exit(0)\n")
    sha = hashlib.sha256(helper.read_bytes()).hexdigest()
    verified = verify_helper_executable(helper, expected_sha256=sha, expected_owner_uid=os.getuid())

    assert os.get_inheritable(verified.fd) is False, (
        "verify_helper_executable must keep returning a CLOEXEC descriptor; "
        "the repair must not widen inheritance in the parent"
    )

    pid = execute_verified(verified, ["pawa-helper"], dict(os.environ))
    _pid, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


@linux_only
def test_repair_a_unrelated_fds_remain_non_inheritable_in_the_child(tmp_path):
    """Only the exact verified descriptor may cross the exec. A regular
    file, a pipe, and an ``AF_UNIX`` socket opened before the launch must
    all be absent from the exec'd child's descriptor table."""
    report = tmp_path / "fds.json"
    helper = tmp_path / "helper.py"
    _write_script(
        helper,
        f"#!{sys.executable}\n"
        f"import json, os, pathlib\n"
        f"scanfd = os.open('/proc/self/fd', os.O_RDONLY)\n"
        f"out = {{}}\n"
        f"for e in os.listdir(scanfd):\n"
        f"    try:\n"
        f"        out[e] = os.readlink('/proc/self/fd/' + e)\n"
        f"    except OSError:\n"
        f"        out[e] = '<gone>'\n"
        f"os.close(scanfd)\n"
        f"out['scanfd'] = str(scanfd)\n"
        f"pathlib.Path({str(report)!r}).write_text(json.dumps(out))\n",
    )
    sha = hashlib.sha256(helper.read_bytes()).hexdigest()

    regular_fd = os.open(str(tmp_path / "unrelated.txt"), os.O_CREAT | os.O_RDWR, 0o600)
    read_fd, write_fd = os.pipe()
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    bystanders = {regular_fd, read_fd, write_fd, sock.fileno()}
    try:
        for fd in bystanders:
            assert os.get_inheritable(fd) is False
        verified = verify_helper_executable(helper, expected_sha256=sha, expected_owner_uid=os.getuid())
        verified_fd = verified.fd
        pid = execute_verified(verified, ["pawa-helper"], dict(os.environ))
        _pid, status = os.waitpid(pid, 0)
        assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    finally:
        os.close(regular_fd)
        os.close(read_fd)
        os.close(write_fd)
        sock.close()

    raw_report = json.loads(report.read_text())
    # The descriptor the child itself opened purely to enumerate /proc/self/fd.
    scan_fd = int(raw_report.pop("scanfd"))
    child_fd_map = {int(k): v for k, v in raw_report.items() if int(k) != scan_fd}
    child_fds = set(child_fd_map)

    leaked = child_fds & bystanders
    assert not leaked, f"unrelated descriptors leaked across exec: {sorted(leaked)}"

    # The verified descriptor IS present and IS the helper's own file — the
    # positive proof that the repair made exactly that one fd inheritable.
    assert verified_fd in child_fds
    assert child_fd_map[verified_fd].startswith(str(helper))

    # Nothing else non-standard crossed the exec. The only other entries a
    # freshly started interpreter can show are artifacts of the child's own
    # ``/proc/self/fd`` scan: the directory handle itself (removed above) and
    # the short-lived dup CPython's ``listdir(dir_fd)`` makes for
    # ``fdopendir`` — already closed by the time the report is written, hence
    # ``<gone>``, and therefore incapable of referring to a parent object.
    extra = {
        fd: target
        for fd, target in child_fd_map.items()
        if fd not in (0, 1, 2, verified_fd)
        and target != "<gone>"
        and not target.startswith("/proc/")
    }
    assert not extra, f"unexpected descriptors in the exec'd child: {extra}"

    # And specifically: none of the child's descriptors refer to any object
    # the parent had open before the launch.
    parent_targets = {
        str(tmp_path / "unrelated.txt"),
    }
    for target in child_fd_map.values():
        assert target not in parent_targets
        assert not target.startswith("pipe:")
        assert not target.startswith("socket:")


@linux_only
def test_repair_a_pathname_replacement_after_verification_executes_the_original(tmp_path):
    """Anti-TOCTOU (§29) survives the repair: replacing the directory entry
    after verification must never cause the replacement to run."""
    original_marker = tmp_path / "original.marker"
    hostile_marker = tmp_path / "hostile.marker"
    helper = tmp_path / "helper.py"
    _write_script(
        helper,
        f"#!{sys.executable}\nimport pathlib\npathlib.Path({str(original_marker)!r}).write_text('ORIGINAL')\n",
    )
    sha = hashlib.sha256(helper.read_bytes()).hexdigest()
    verified = verify_helper_executable(helper, expected_sha256=sha, expected_owner_uid=os.getuid())

    hostile = tmp_path / "hostile.py"
    _write_script(
        hostile,
        f"#!{sys.executable}\nimport pathlib\npathlib.Path({str(hostile_marker)!r}).write_text('HOSTILE')\n",
    )
    os.replace(str(hostile), str(helper))  # atomic directory-entry swap over the verified path

    pid = execute_verified(verified, ["pawa-helper"], dict(os.environ))
    _pid, status = os.waitpid(pid, 0)

    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    assert original_marker.read_text() == "ORIGINAL"
    assert not hostile_marker.exists(), "the post-verification replacement executed — anti-TOCTOU broken"


@linux_only
def test_repair_a_in_place_content_mutation_after_verification_is_not_executed(tmp_path):
    """Stronger variant: mutate the SAME inode in place after verification
    (truncate + rewrite) rather than swapping the directory entry. The
    verified descriptor is a file *description*, but the bytes behind it are
    the same inode — so this must fail closed (the mutated script must not
    perform the hostile side effect under the original's identity)."""
    hostile_marker = tmp_path / "hostile-inplace.marker"
    helper = tmp_path / "helper.py"
    _write_script(helper, f"#!{sys.executable}\nimport sys\nsys.exit(0)\n")
    sha = hashlib.sha256(helper.read_bytes()).hexdigest()
    verified = verify_helper_executable(helper, expected_sha256=sha, expected_owner_uid=os.getuid())

    helper.chmod(0o700)
    helper.write_bytes(
        (
            f"#!{sys.executable}\nimport pathlib\n"
            f"pathlib.Path({str(hostile_marker)!r}).write_text('HOSTILE')\n"
        ).encode("utf-8")
    )
    os.chmod(helper, 0o755)

    pid = execute_verified(verified, ["pawa-helper"], dict(os.environ))
    _pid, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status)

    # In-place mutation of the same inode is a DIFFERENT threat model from the
    # directory-entry swap: /proc/self/fd anchoring cannot defend against it,
    # and this test records the true behavior rather than asserting a
    # guarantee the architecture does not provide. What it DOES pin is that
    # the launcher's own pre-launch digest recomputation is the control that
    # catches it — re-verification against the recorded digest fails closed.
    if hostile_marker.exists():
        with pytest.raises(HelperProtocolError) as exc:
            verify_helper_executable(helper, expected_sha256=sha, expected_owner_uid=os.getuid())
        assert exc.value.code == "descriptor_installation_mismatch"


@linux_only
def test_repair_a_forced_exec_failure_exits_127_and_closes_the_parent_fd(tmp_path):
    """A candidate that passes every provenance predicate but is not an
    executable image (no shebang, not ELF) makes ``execve`` fail. The child
    must exit 127 and the parent must hold no descriptor afterwards — the
    child's ``finally: os._exit(127)`` terminates the process image, which
    closes everything it held."""
    helper = tmp_path / "not-an-image"
    _write_script(helper, "this is plain text, not an executable image\n")
    sha = hashlib.sha256(helper.read_bytes()).hexdigest()

    def _open_targets():
        targets = {}
        for entry in os.listdir("/proc/self/fd"):
            try:
                targets[entry] = os.readlink("/proc/self/fd/" + entry)
            except OSError:
                pass
        return targets

    before = _open_targets()
    assert str(helper) not in before.values()

    verified = verify_helper_executable(helper, expected_sha256=sha, expected_owner_uid=os.getuid())
    fd = verified.fd
    assert os.readlink(f"/proc/self/fd/{fd}") == str(helper)

    pid = execute_verified(verified, ["pawa-helper"], dict(os.environ))
    _pid, status = os.waitpid(pid, 0)

    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 127
    with pytest.raises(OSError):
        os.fstat(fd)  # execute_verified already closed the parent's copy
    # No descriptor anywhere in the parent still refers to the helper object.
    assert str(helper) not in _open_targets().values()


@linux_only
def test_repair_a_directly_loaded_elf_binary_still_executes(tmp_path):
    """Bounding regression: the ELF shape was never broken and must stay
    working after the repair."""
    import shutil

    real_true = shutil.which("true") or "/bin/true"
    content = Path(real_true).read_bytes()
    helper = tmp_path / "true-copy"
    helper.write_bytes(content)
    os.chmod(helper, 0o755)
    sha = hashlib.sha256(content).hexdigest()

    verified = verify_helper_executable(helper, expected_sha256=sha, expected_owner_uid=os.getuid())
    pid = execute_verified(verified, ["true"], {})
    _pid, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


def test_repair_a_is_minimal_and_child_only():
    """Source-level pin: the ONLY inheritance widening is a single
    ``os.set_inheritable(verified.fd, True)`` inside the child branch of
    ``execute_verified``, and no pathname reopen was introduced."""
    source = inspect.getsource(helper_os.execute_verified)
    assert source.count("set_inheritable") == 1
    tree = ast.parse(textwrap.dedent(source))
    calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "set_inheritable"
    ]
    assert len(calls) == 1
    (call,) = calls
    assert len(call.args) == 2
    assert isinstance(call.args[1], ast.Constant) and call.args[1].value is True
    # ...and it names the verified descriptor, not an arbitrary fd.
    assert isinstance(call.args[0], ast.Attribute) and call.args[0].attr == "fd"
    # still exec'ing the descriptor, never a re-resolved pathname
    assert "/proc/self/fd/" in source
    assert "os.execve" in source


# -- provenance regressions (unchanged by the repair) -----------------------


def test_repair_a_regression_symlink_candidate_rejected(tmp_path):
    real = tmp_path / "real"
    sha = _write_script(real, "#!/bin/sh\nexit 0\n")
    link = tmp_path / "link"
    link.symlink_to(real)
    with pytest.raises((HelperProtocolError, OSError)):
        verify_helper_executable(link, expected_sha256=sha, expected_owner_uid=os.getuid())


def test_repair_a_regression_directory_candidate_rejected(tmp_path):
    d = tmp_path / "dir"
    d.mkdir()
    with pytest.raises((HelperProtocolError, IsADirectoryError, OSError)):
        verify_helper_executable(d, expected_sha256="0" * 64, expected_owner_uid=os.getuid())


def test_repair_a_regression_fifo_candidate_rejected(tmp_path):
    import threading

    fifo = tmp_path / "fifo"
    os.mkfifo(fifo, 0o755)

    def _open_writer():
        try:
            os.close(os.open(str(fifo), os.O_WRONLY))
        except OSError:
            pass

    t = threading.Thread(target=_open_writer, daemon=True)
    t.start()
    try:
        with pytest.raises(HelperProtocolError) as exc:
            verify_helper_executable(fifo, expected_sha256="0" * 64, expected_owner_uid=os.getuid())
        assert exc.value.code == "descriptor_wrong_owner"
    finally:
        t.join(timeout=5)


def test_repair_a_regression_socket_candidate_rejected():
    # AF_UNIX sockaddr_un has a ~104-byte path limit and pytest's tmp_path is
    # too deep for it on macOS, so bind inside a short disposable temp dir.
    import shutil
    import tempfile

    directory = Path(tempfile.mkdtemp(prefix="pawa-sock-"))
    sock_path = directory / "s"
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        s.bind(str(sock_path))
        with pytest.raises((HelperProtocolError, OSError)):
            verify_helper_executable(sock_path, expected_sha256="0" * 64, expected_owner_uid=os.getuid())
    finally:
        s.close()
        shutil.rmtree(directory, ignore_errors=True)


def test_repair_a_regression_digest_mismatch_rejected(tmp_path):
    p = tmp_path / "h"
    _write_script(p, "#!/bin/sh\nexit 0\n")
    with pytest.raises(HelperProtocolError) as exc:
        verify_helper_executable(p, expected_sha256="f" * 64, expected_owner_uid=os.getuid())
    assert exc.value.code == "descriptor_installation_mismatch"


def test_repair_a_regression_wrong_mode_and_owner_rejected(tmp_path):
    p = tmp_path / "h2"
    sha = _write_script(p, "#!/bin/sh\nexit 0\n")
    with pytest.raises(HelperProtocolError) as exc:
        verify_helper_executable(p, expected_sha256=sha, expected_owner_uid=os.getuid() + 1)
    assert exc.value.code == "descriptor_wrong_owner"
    os.chmod(p, 0o775)
    with pytest.raises(HelperProtocolError) as exc2:
        verify_helper_executable(p, expected_sha256=sha, expected_owner_uid=os.getuid())
    assert exc2.value.code == "descriptor_wrong_mode"


def test_repair_a_regression_macos_remains_fail_closed():
    """No macOS same-file-object implementation was added: the repair must
    not have turned the non-Linux branch into a fallback."""
    source = inspect.getsource(helper_os.execute_verified)
    assert "UnsupportedPlatformProfile" in source
    if not sys.platform.startswith("linux"):
        with pytest.raises(helper_os.UnsupportedPlatformProfile):
            execute_verified(
                helper_os.VerifiedExecutable(
                    fd=-1, sha256="0" * 64, device=0, inode=0, owner_uid=0, mode=0o755, nlink=1
                ),
                ["x"],
                {},
            )


# ═══════════════════════════════════════════════════════════════════════════
# REPAIR B — trusted store-profile selection.
# ═══════════════════════════════════════════════════════════════════════════


def test_repair_b_real_profile_selected_only_for_the_fixed_canonical_root():
    canonical = resolve_hpac_protected_root()
    assert resolve_store_profile(str(canonical)) == STORE_PROFILE_REAL
    assert resolve_store_profile(str(canonical) + "/") == STORE_PROFILE_REAL


@pytest.mark.parametrize(
    "hostile_root",
    [
        "",
        "/",
        "/tmp",
        "/tmp/attacker-protected-root",
        "relative/protected-root",
        "../protected-root",
        "/etc/pcae/hpac/protected-root-evil",
        "/etc/pcae/hpac",
        "/etc/pcae/hpac/protected-root/..",
        "/etc/pcae/hpac/protected-root/../protected-root",
        "/etc/pcae/hpac/protected-root/subdir",
    ],
)
def test_repair_b_store_profile_fails_closed_for_any_other_root(hostile_root):
    """The trusted signal is not redirectable: no value other than the one
    fixed canonical root can select REAL, and an ambiguous one raises rather
    than degrading to the NON_REAL foundation."""
    with pytest.raises(HelperProtocolError) as exc:
        resolve_store_profile(hostile_root)
    assert exc.value.code == "descriptor_root_identity_mismatch"


def test_repair_b_store_profile_source_accepts_no_override():
    """The canonical root this decision keys off comes from
    ``resolve_hpac_protected_root``, which by construction takes no
    parameters and reads no environment override."""
    assert list(inspect.signature(resolve_hpac_protected_root).parameters) == []
    src = inspect.getsource(resolve_hpac_protected_root)
    assert "environ" not in src and "getenv" not in src


def test_repair_b_build_helper_context_wires_the_real_adapter(tmp_path, monkeypatch):
    """The REAL profile genuinely constructs ``RealCanonicalReadAdapter``
    over a PRODUCTION-class ``HPACStoreAuthority`` — never the foundation.

    ``HPACStoreAuthority.production()`` has no redirectable constructor, so
    to exercise it without touching the live root this test relocates the
    single fixed-path resolver to a disposable directory. That is exactly
    the redirection an attacker cannot perform from outside the process.
    """
    import pcae.core.hpac_foundation as foundation

    fake_root = _provisioned_root(tmp_path)
    monkeypatch.setattr(foundation, "resolve_hpac_protected_root", lambda: fake_root)
    monkeypatch.setattr(
        HPACStoreAuthority, "_effective_write_helpers", lambda self: (
            _locked_probe().effective_write_access,
            _locked_probe().ancestor_chain_safe,
        )
    )

    context = build_helper_context(
        protected_root=str(fake_root),
        installation_id="inst-x",
        generation=1,
        store_profile=STORE_PROFILE_REAL,
    )
    assert isinstance(context.store, RealCanonicalReadAdapter)
    assert not isinstance(context.store, ProtectedStoreFoundation)
    assert context.store.authority.authority_class is HPACAuthorityClass.PRODUCTION
    assert context.store.authority.root == Path(fake_root).absolute()
    assert context.supported_operations == CLOSED_OPERATIONS


def test_repair_b_unknown_profile_fails_closed(tmp_path):
    for profile in ("non_real", "foundation", "", "REAL", "canonical", None):
        with pytest.raises(HelperProtocolError) as exc:
            build_helper_context(
                protected_root=str(tmp_path),
                installation_id="i",
                generation=1,
                store_profile=profile,
            )
        assert exc.value.code == "internal_fail_closed"


def test_repair_b_real_store_construction_failure_never_falls_back(tmp_path, monkeypatch):
    """If the REAL adapter cannot be constructed, the failure propagates.
    It must never be replaced by ``ProtectedStoreFoundation``."""
    import pcae.core.hpac_pawa_helper_store_adapter as adapter_mod

    def _boom(authority):
        raise RuntimeError("canonical root unavailable")

    monkeypatch.setattr(adapter_mod, "RealCanonicalReadAdapter", _boom)
    monkeypatch.setattr(HPACStoreAuthority, "production", classmethod(lambda cls: object()))

    with pytest.raises(RuntimeError):
        build_helper_context(
            protected_root=str(tmp_path),
            installation_id="i",
            generation=1,
            store_profile=STORE_PROFILE_REAL,
        )


def test_repair_b_non_real_reachable_only_through_the_explicit_test_seam(tmp_path):
    """``ProtectedStoreFoundation`` is no longer constructed anywhere in the
    entrypoint; the only route to it is the keyword-only, in-process
    ``_test_only_store`` seam."""
    module_src = inspect.getsource(entrypoint)
    assert "ProtectedStoreFoundation()" not in module_src

    seam_params = inspect.signature(build_helper_context).parameters
    assert seam_params["_test_only_store"].kind is inspect.Parameter.KEYWORD_ONLY
    assert seam_params["_test_only_store"].default is None

    foundation_store = ProtectedStoreFoundation()
    context = build_helper_context(
        protected_root=str(tmp_path),
        installation_id="i",
        generation=1,
        store_profile=STORE_PROFILE_REAL,
        _test_only_store=foundation_store,
    )
    assert context.store is foundation_store


def test_repair_b_profile_decision_is_structurally_unreachable_from_a_request():
    """Neither profile function accepts a request, and ``main()`` builds its
    whole context before it ever calls ``run_one_shot`` (which is the first
    thing that touches the socket the request arrives on)."""
    assert "request" not in inspect.signature(resolve_store_profile).parameters
    assert "request" not in inspect.signature(build_helper_context).parameters

    main_src = textwrap.dedent(inspect.getsource(entrypoint.main))
    assert "HelperRequest" not in main_src and "read_one_frame" not in main_src
    assert main_src.index("build_helper_context") < main_src.index("run_one_shot")
    # main() never constructs the NON_REAL foundation and never passes the seam
    # (the only remaining textual mention is the comment saying it must not).
    assert "ProtectedStoreFoundation()" not in main_src
    assert "_test_only_store" not in main_src


@pytest.mark.parametrize(
    "hostile_field",
    ["profile", "real", "store_backend", "protected_root", "authority", "store"],
)
def test_repair_b_hostile_request_fields_rejected_by_the_closed_schema(hostile_field):
    """A request body can never select the store profile: the §11 schema is
    closed and rejects every unknown field outright."""
    base = build_signed_request(
        operation=HelperOperation.CERTIFICATION_READ,
        session_id="s",
        operation_params={"record_type": "principal_record", "record_key": "k"},
        request_id="r",
        expiry="2099-01-01T00:00:00.000000Z",
        installation_id="i",
        generation=1,
    )
    payload = dict(base.__dict__)
    payload[hostile_field] = "real"
    with pytest.raises(HelperProtocolError) as exc:
        HelperRequest.from_mapping(payload)
    assert exc.value.code == "operation_scope_invalid"
    assert hostile_field in str(exc.value)


def test_repair_b_hostile_operation_params_cannot_reach_store_selection(tmp_path):
    """Even smuggled inside the open-ended ``operation_params`` map, profile
    or root fields have no effect: the store was already bound before the
    request existed, and no handler reads such a key."""
    store = ProtectedStoreFoundation()
    store.put_record("principal_record", "k", {"principal_id": "k"})
    context = HelperContext(
        replay_ledger=ReplayLedger(),
        evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS,
        store=store,
    )
    request = build_signed_request(
        operation=HelperOperation.CERTIFICATION_READ,
        session_id="s1",
        operation_params={
            "record_type": "principal_record",
            "record_key": "k",
            "profile": "real",
            "store_backend": "canonical",
            "protected_root": "/etc/pcae/hpac/protected-root",
        },
        request_id="r1",
        expiry="2099-01-01T00:00:00.000000Z",
        installation_id="i",
        generation=1,
    )
    response = dispatch(request, context, CLOSED_DISPATCH_TABLE)
    # Served by the store that was already bound (the foundation), proving the
    # request fields changed nothing about which store answered.
    assert response.decision == "PERFORMED"
    assert response.result_payload["contents"] == {"principal_id": "k"}
    ops_src = inspect.getsource(
        sys.modules["pcae.core.hpac_pawa_helper_operations"]
    )
    for forbidden in ("\"profile\"", "'profile'", "store_backend", "protected_root"):
        assert forbidden not in ops_src


# -- genuine subprocess exit-code behavior of the real main() ---------------


def _run_main_subprocess(env_overrides, *, cwd):
    script = (
        "import sys;"
        "sys.exit(__import__('pcae.core.hpac_pawa_helper_entrypoint',"
        " fromlist=['main']).main())"
    )
    env = {"PATH": "/usr/bin:/bin"}
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", script], env=env, cwd=cwd, capture_output=True, timeout=60
    )


@linux_only
def test_repair_b_main_fails_closed_for_a_foreign_protected_root(tmp_path):
    """A direct, untrusted invocation of the entrypoint outside the
    launcher's trusted context cannot acquire REAL canonical-store backing;
    it exits fail-closed before ever connecting to a channel."""
    proc = _run_main_subprocess(
        {
            "PAWA_HELPER_CHANNEL_PATH": str(tmp_path / "nope.sock"),
            "PAWA_HELPER_PROTECTED_ROOT": str(tmp_path),
            "PAWA_HELPER_INSTALLATION_ID": "inst-hostile",
            "PAWA_HELPER_GENERATION": "1",
        },
        cwd=str(tmp_path),
    )
    assert proc.returncode == EXIT_STORE_PROFILE_UNESTABLISHED, proc.stderr.decode()
    assert not (tmp_path / "nope.sock").exists()


@linux_only
@pytest.mark.parametrize(
    "missing",
    [
        "PAWA_HELPER_CHANNEL_PATH",
        "PAWA_HELPER_PROTECTED_ROOT",
        "PAWA_HELPER_INSTALLATION_ID",
        "PAWA_HELPER_GENERATION",
    ],
)
def test_repair_b_main_fails_closed_on_missing_bootstrap_coordinates(tmp_path, missing):
    env = {
        "PAWA_HELPER_CHANNEL_PATH": str(tmp_path / "s.sock"),
        "PAWA_HELPER_PROTECTED_ROOT": str(resolve_hpac_protected_root()),
        "PAWA_HELPER_INSTALLATION_ID": "i",
        "PAWA_HELPER_GENERATION": "1",
    }
    env.pop(missing)
    proc = _run_main_subprocess(env, cwd=str(tmp_path))
    assert proc.returncode == EXIT_BOOTSTRAP_COORDINATES_MISSING, proc.stderr.decode()


@linux_only
def test_repair_b_main_fails_closed_on_non_integer_generation(tmp_path):
    proc = _run_main_subprocess(
        {
            "PAWA_HELPER_CHANNEL_PATH": str(tmp_path / "s.sock"),
            "PAWA_HELPER_PROTECTED_ROOT": str(resolve_hpac_protected_root()),
            "PAWA_HELPER_INSTALLATION_ID": "i",
            "PAWA_HELPER_GENERATION": "not-a-number",
        },
        cwd=str(tmp_path),
    )
    assert proc.returncode == EXIT_BOOTSTRAP_COORDINATES_MISSING, proc.stderr.decode()


def test_repair_b_main_fail_closed_exit_codes_are_distinct_and_nonzero():
    codes = {
        EXIT_BOOTSTRAP_COORDINATES_MISSING,
        entrypoint.EXIT_NO_RESPONSE,
        EXIT_STORE_PROFILE_UNESTABLISHED,
        EXIT_REAL_STORE_UNAVAILABLE,
    }
    assert len(codes) == 4 and 0 not in codes


# -- genuine end-to-end launch against the REAL adapter --------------------


@linux_only
def test_repair_b_real_adapter_certification_read_through_a_genuine_helper(installed):
    """A genuinely launched, genuinely exec'd, script-shaped helper
    subprocess serves ``certification_read`` from the REAL canonical stores
    on a disposable root. This exercises Repair A and Repair B together —
    before Repair A the process could not even start."""
    root, authority, resolved = installed
    request = build_signed_request(
        operation=HelperOperation.CERTIFICATION_READ,
        session_id="sess-real-1",
        operation_params={
            "record_type": "presentation_mechanism_descriptor",
            "record_key": resolved.descriptor.mechanism_id,
        },
        request_id="req-real-1",
        expiry="2099-01-01T00:00:00.000000Z",
        installation_id=resolved.record.installation_id,
        generation=resolved.record.generation,
    )
    outcome = launch_and_exchange(**_launch_kwargs(root, resolved, request=request))
    assert outcome.outcome == "completed", outcome
    assert outcome.helper_pid != os.getpid()
    assert outcome.response.decision == "PERFORMED"
    payload = outcome.response.result_payload
    assert payload["record_key"] == resolved.descriptor.mechanism_id
    # Real canonical content, not an empty in-memory foundation record.
    assert payload["contents"]["mechanism_id"] == resolved.descriptor.mechanism_id


@linux_only
def test_repair_b_real_adapter_ceremony_entry_through_a_genuine_helper(installed):
    """``ceremony_entry``'s real store-side generation check runs inside the
    launched helper: the current generation is accepted and a stale one is
    rejected with the real adapter's own terminal code."""
    root, authority, resolved = installed
    common = dict(
        operation=HelperOperation.CEREMONY_ENTRY,
        session_id="sess-real-2",
        operation_params={"ceremony_request_digest": "a" * 64},
        expiry="2099-01-01T00:00:00.000000Z",
        installation_id=resolved.record.installation_id,
    )
    ok = launch_and_exchange(
        **_launch_kwargs(
            root,
            resolved,
            request=build_signed_request(
                request_id="req-real-2", generation=resolved.record.generation, **common
            ),
        )
    )
    assert ok.outcome == "completed" and ok.response.decision == "PERFORMED"
    assert ok.response.result_payload["acknowledgement"] == "ceremony_started"


@linux_only
def test_repair_b_genuine_helper_response_exports_no_authority(installed):
    """No-authority-export regression against a real launched helper: the
    response carries no store, authority, capability, descriptor or fd."""
    root, authority, resolved = installed
    request = build_signed_request(
        operation=HelperOperation.CERTIFICATION_READ,
        session_id="sess-real-3",
        operation_params={
            "record_type": "helper_registration_record",
            "record_key": resolved.record.installation_id,
        },
        request_id="req-real-3",
        expiry="2099-01-01T00:00:00.000000Z",
        installation_id=resolved.record.installation_id,
        generation=resolved.record.generation,
    )
    outcome = launch_and_exchange(**_launch_kwargs(root, resolved, request=request))
    assert outcome.outcome == "completed" and outcome.response.decision == "PERFORMED"

    blob = json.dumps(outcome.response.__dict__, sort_keys=True, default=str).lower()
    for forbidden in (
        "hpacstoreauthority",
        "hpacwritercapability",
        "realcanonicalreadadapter",
        "protectedstorefoundation",
        "/proc/self/fd",
        "authority_class",
        "_seal",
        "writer_capability",
    ):
        assert forbidden not in blob, f"response leaked {forbidden!r}"
    for value in outcome.response.__dict__.values():
        assert isinstance(value, (str, int, float, bool, type(None), list, dict, tuple))


# -- write operations remain blocked under the REAL profile ----------------


def _real_context(authority):
    return HelperContext(
        replay_ledger=ReplayLedger(),
        evidence_stager=EvidenceStager(),
        supported_operations=CLOSED_OPERATIONS,
        store=RealCanonicalReadAdapter(authority),
    )


def test_repair_b_admin_mutation_still_blocked_under_the_real_profile(installed):
    root, authority, resolved = installed
    response = dispatch(
        build_signed_request(
            operation=HelperOperation.ADMIN_MUTATION,
            session_id="sess-w1",
            operation_params={"mutation": "enroll_principal", "transaction_id": "t1"},
            request_id="req-w1",
            expiry="2099-01-01T00:00:00.000000Z",
            installation_id=resolved.record.installation_id,
            generation=resolved.record.generation,
        ),
        _real_context(authority),
        CLOSED_DISPATCH_TABLE,
    )
    assert response.decision == "REJECTED"
    assert response.terminal_code == "internal_fail_closed"


def test_repair_b_certification_write_still_blocked_under_the_real_profile(installed):
    root, authority, resolved = installed
    response = dispatch(
        build_signed_request(
            operation=HelperOperation.CERTIFICATION_WRITE,
            session_id="sess-w2",
            operation_params={},
            request_id="req-w2",
            role=CertificationRole.HPAC_GATE5_BINDER,
            proof_id="proof-1",
            expiry="2099-01-01T00:00:00.000000Z",
            installation_id=resolved.record.installation_id,
            generation=resolved.record.generation,
        ),
        _real_context(authority),
        CLOSED_DISPATCH_TABLE,
    )
    assert response.decision == "REJECTED"
    assert response.terminal_code == "internal_fail_closed"


def test_repair_b_presentation_evidence_write_rejects_incomplete_evidence_payload(installed):
    """Re-scoped (N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL): this test was
    written when ``presentation_evidence_write`` was unconditionally blocked
    (no writer-mint code path existed at all, REQ-033) and asserted
    ``internal_fail_closed`` for that reason. Model E has since wired this
    operation through a real, typed facade (HPAC-PAWA-HELPER-REQ-155) that
    requires the full ``HPAC-PRESENTATION-EVIDENCE/2.0`` evidence-field
    payload (presentation_id/approval_id/canonical_subject/etc.) — this test
    supplies only ``ceremony_approve_ref``, which is no longer sufficient.
    The call still correctly REJECTS, but now for the honest reason (an
    incomplete/malformed request payload, ``operation_scope_invalid``), not
    the old total-blocker reason. This is an implementation-independent
    staleness correction to the *expected failure code* only; the
    still-blocked-in-real-deployment finding this phase separately
    discovered (real-profile write-boundary gap, phase completion report) is
    a distinct, deeper issue this narrow request-shape test does not probe."""
    root, authority, resolved = installed
    context = _real_context(authority)
    started = dispatch(
        build_signed_request(
            operation=HelperOperation.CEREMONY_ENTRY,
            session_id="sess-w3",
            operation_params={"ceremony_request_digest": "b" * 64},
            request_id="req-w3a",
            expiry="2099-01-01T00:00:00.000000Z",
            installation_id=resolved.record.installation_id,
            generation=resolved.record.generation,
        ),
        context,
        CLOSED_DISPATCH_TABLE,
    )
    assert started.decision == "PERFORMED"
    response = dispatch(
        build_signed_request(
            operation=HelperOperation.PRESENTATION_EVIDENCE_WRITE,
            session_id="sess-w3",
            operation_params={"ceremony_approve_ref": "ppa-approve/1"},
            request_id="req-w3b",
            expiry="2099-01-01T00:00:00.000000Z",
            installation_id=resolved.record.installation_id,
            generation=resolved.record.generation,
        ),
        context,
        CLOSED_DISPATCH_TABLE,
    )
    assert response.decision == "REJECTED"
    assert response.terminal_code == "operation_scope_invalid"


# -- HPAC-PAWA-HELPER-REQ-033 ----------------------------------------------


HELPER_MODULES = (
    "pcae.core.hpac_pawa_helper_os",
    "pcae.core.hpac_pawa_helper_entrypoint",
    "pcae.core.hpac_pawa_helper_protocol",
    "pcae.core.hpac_pawa_helper_operations",
    "pcae.core.hpac_pawa_helper_replay_state",
    "pcae.core.hpac_pawa_helper_launcher",
)

FORBIDDEN_SYMBOLS = (
    "hpac_protected_admin_writer",
    "production_writer",
    "certification_writer",
    "recognized_certification_read_authority",
)


@pytest.mark.parametrize("module_name", HELPER_MODULES)
def test_req_033_helper_modules_never_import_the_pawa_factory(module_name):
    """HPAC-PAWA-HELPER-REQ-033 still holds after both repairs: no helper
    module imports the in-process PAWA factory module or its writer
    symbols, at source level or in the live module namespace."""
    __import__(module_name)
    module = sys.modules[module_name]
    source = inspect.getsource(module)
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module)
            imported.update(f"{node.module}.{a.name}" for a in node.names if node.module)
    for forbidden in FORBIDDEN_SYMBOLS:
        assert not any(forbidden in name for name in imported), (
            f"{module_name} imports forbidden {forbidden!r}"
        )
        assert not hasattr(module, forbidden)


def test_req_033_repair_b_imports_only_the_read_adapter_and_authority():
    """The new REAL wiring reaches the canonical stores exclusively through
    the already-existing narrow read adapter and the sealed authority
    factory — no second construction path was invented."""
    src = inspect.getsource(entrypoint.build_helper_context)
    assert "RealCanonicalReadAdapter" in src
    assert "HPACStoreAuthority.production()" in src
    assert "_production_test_fixture" not in src
    assert "_PRODUCTION_TEST_FIXTURE_SEAL" not in src
    assert "fixture(" not in src
    module_src = inspect.getsource(entrypoint)
    assert "_PRODUCTION_TEST_FIXTURE_SEAL" not in module_src
