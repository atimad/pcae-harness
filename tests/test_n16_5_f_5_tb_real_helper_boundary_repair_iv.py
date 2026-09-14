"""N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR-IV — independent, adversarial
Linux verification of the repaired one-shot privileged helper boundary
(N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR, commit 43813b16).

This file is authored by a BOUNDED DELEGATED WORKER with no finalization
authority; it does not modify anything under ``src/pcae/**`` and is a
NEW file (the predecessor test files are re-run read-only as regression,
never edited).

Scope: two gaps the predecessor repair phase's own 40-test suite
(``test_n16_5_f_5_tb_real_helper_boundary_repair.py``) did not close:

1. **Finding C** (in-place same-inode content mutation after verification,
   disclosed but not repaired by the predecessor phase) is empirically
   classified here using a *second, genuinely distinct, unprivileged OS
   principal* (``nobody``, uid 65534) rather than only self-mutation as the
   file's own owner. The predecessor's own
   ``test_repair_a_in_place_content_mutation_after_verification_is_not_executed``
   already proved that the OWNER can mutate the inode and have the hostile
   bytes execute; what it did not test is whether a non-owner (the actual
   adversary class this boundary defends against — see
   ``hpac_pawa_helper_os.authenticate_peer``'s "peer uid is the configured
   agent principal" check) can reach that same write.

2. **Transitive import attack**: a hostile ``PYTHONPATH`` / cwd-shadow
   module is never tested against the *real* end-to-end
   ``launch_and_exchange`` path anywhere in the existing suite (grepped).

Every Linux-dependent test here runs genuinely on a real Linux kernel via
SSH ``hac-dell`` (``Linux atila-Latitude-E5470 7.0.0-28-generic`` x86_64),
against disposable ``tmp_path`` roots only. Nothing here touches the live
host protected root or performs a real ceremony/FIDO2/certification.
"""

from __future__ import annotations

import hashlib
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
from pcae.core.hpac_foundation import HPACStoreAuthority
from pcae.core.hpac_pawa_helper_os import (
    OneShotChannel,
    execute_verified,
    verify_helper_executable,
)
from pcae.core.hpac_pawa_helper_protocol import HelperProtocolError
from pcae.core.hpac_pawa_helper_launcher import launch_and_exchange
from pcae.core.hpac_pawa_helper_protocol import HelperOperation, build_signed_request
from pcae.core.hpac_pawa_helper_store_adapter import resolve_launcher_deployment_metadata

pytestmark = [
    pytest.mark.skipif(os.name != "posix", reason="POSIX-only protected-store / launch model"),
]

linux_only = pytest.mark.skipif(
    not sys.platform.startswith("linux"),
    reason="same-file-object exec / one-shot launch is Linux-only (HPAC-PAWA-HELPER-REQ-104, §60)",
)

FAKE_AGENT_UID = 4_242_431
FAKE_AGENT_GID = 999_991


def _nobody_available() -> bool:
    """True iff this host can genuinely exercise a second, unprivileged OS
    principal via passwordless ``sudo -u nobody`` — never faked/assumed."""
    if os.geteuid() != 0:
        try:
            probe = subprocess.run(
                ["sudo", "-n", "-u", "nobody", "id", "-u"], capture_output=True, timeout=5, text=True
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return probe.returncode == 0 and probe.stdout.strip() == "65534"
    return False


NOBODY_AVAILABLE = sys.platform.startswith("linux") and _nobody_available()
needs_nobody = pytest.mark.skipif(
    not NOBODY_AVAILABLE, reason="requires passwordless `sudo -u nobody` on a genuine second uid"
)


def _write_script(path: Path, body: str) -> str:
    raw = body.encode("utf-8")
    path.write_bytes(raw)
    os.chmod(path, 0o755)
    return hashlib.sha256(raw).hexdigest()


def _locked_probe():
    return types.SimpleNamespace(
        effective_write_access=lambda p, u, g: (False, "fixture_locked", ()),
        ancestor_chain_safe=lambda s, u, g: (True, ("fixture_root_reached",)),
    )


def _provisioned_root(tmp_path: Path) -> Path:
    root = (tmp_path / "hpac-protected-root").resolve()
    w.provision_protected_root(protected_root=root, agent_account="pcae-agent-svc", agent_uid=FAKE_AGENT_UID)
    return root


def _fixture_production_authority(root: Path) -> HPACStoreAuthority:
    from pcae.core.hpac_foundation import _PRODUCTION_TEST_FIXTURE_SEAL

    return HPACStoreAuthority._production_test_fixture(
        root, _seal=_PRODUCTION_TEST_FIXTURE_SEAL, _topology_probe=_locked_probe()
    )


def _install_helper_bytes(root: Path, helper_bytes: bytes) -> str:
    sha = hashlib.sha256(helper_bytes).hexdigest()
    path = inst.helper_content_addressed_path(root, sha)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.exists():
        path.chmod(0o600)
    path.write_bytes(helper_bytes)
    os.chmod(path, 0o755)
    return sha


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


# ═══════════════════════════════════════════════════════════════════════════
# Finding C — in-place same-inode mutation, classified against a genuine
# second, unprivileged OS principal (not just the owning test process).
# ═══════════════════════════════════════════════════════════════════════════


@linux_only
@needs_nobody
def test_finding_c_non_owner_cannot_open_verified_inode_for_writing(tmp_path):
    """The predecessor phase's disclosed Finding C ("in-place same-inode
    content mutation after verify is undefended") only demonstrated the
    mutation as the file's OWNER. This test asks the actual adversary-model
    question: can a *different*, unprivileged OS principal (``nobody``) open
    the SAME already-verified inode for writing at all?

    ``verify_helper_executable``'s conjunctive predicates require mode 0755
    (§6: "not group/other-writable") and ``st_uid == expected_owner_uid``
    before a file is ever accepted as a launch candidate. Under ordinary
    POSIX permission semantics this makes the write itself — not just the
    directory-entry swap — unavailable to any principal other than the
    owning uid (or root). This is checked here empirically, not merely
    read off the mode bits: ``nobody`` genuinely attempts the open."""
    helper = tmp_path / "helper.py"
    _write_script(helper, f"#!{sys.executable}\nimport sys\nsys.exit(0)\n")
    os.chmod(tmp_path, 0o755)  # parent directory traversable by "nobody" too
    sha = hashlib.sha256(helper.read_bytes()).hexdigest()
    verified = verify_helper_executable(helper, expected_sha256=sha, expected_owner_uid=os.getuid())
    try:
        assert verified.mode == 0o755
        assert verified.owner_uid == os.getuid()

        probe = subprocess.run(
            [
                "sudo", "-n", "-u", "nobody", sys.executable, "-c",
                textwrap.dedent(
                    f"""
                    import os, sys
                    try:
                        fd = os.open({str(helper)!r}, os.O_WRONLY)
                    except OSError as exc:
                        print("DENIED", exc.errno)
                        sys.exit(0)
                    os.write(fd, b"HOSTILE-FROM-NOBODY")
                    os.close(fd)
                    print("WROTE")
                    sys.exit(0)
                    """
                ),
            ],
            capture_output=True, text=True, timeout=15,
        )
        assert probe.returncode == 0, probe.stderr
        assert "DENIED" in probe.stdout, (
            f"a non-owner principal was able to write into the verified inode: {probe.stdout!r}/{probe.stderr!r}"
        )
        assert helper.read_bytes() != b"HOSTILE-FROM-NOBODY", "in-place write by a non-owner succeeded"
    finally:
        os.close(verified.fd)


@linux_only
@needs_nobody
def test_finding_c_owner_can_mutate_but_owner_is_the_maximal_trust_principal(tmp_path):
    """Companion positive control: the OWNER (this test process's own uid,
    which stands in for the deployment owner in these disposable fixtures)
    CAN mutate the inode in place and have the mutated bytes execute — this
    reproduces the predecessor's own disclosed finding — but the owner is
    already the single most-trusted principal in this project's model
    (``hpac_pawa_helper_os.authenticate_peer`` requires the *peer* uid to
    equal ``deployment_owner_uid`` and explicitly rejects the configured
    *agent* principal — the agent is a strictly lower-trust principal than
    the deployment owner). Reaching Finding C therefore requires an actor
    who already holds the maximal trust level this boundary exists to
    protect, which is not a privilege escalation."""
    hostile_marker = tmp_path / "hostile.marker"
    helper = tmp_path / "helper.py"
    _write_script(helper, f"#!{sys.executable}\nimport sys\nsys.exit(0)\n")
    sha = hashlib.sha256(helper.read_bytes()).hexdigest()
    verified = verify_helper_executable(helper, expected_sha256=sha, expected_owner_uid=os.getuid())
    try:
        helper.chmod(0o700)
        helper.write_bytes(
            f"#!{sys.executable}\nimport pathlib\npathlib.Path({str(hostile_marker)!r}).write_text('X')\n".encode()
        )
        os.chmod(helper, 0o755)
        pid = execute_verified(verified, ["pawa-helper"], dict(os.environ))
        _pid, status = os.waitpid(pid, 0)
        assert os.WIFEXITED(status)
        assert hostile_marker.exists(), "owner-authored in-place mutation should execute (documents the known gap)"
    finally:
        pass  # execute_verified always closes/consumes the parent's fd copy


@linux_only
@needs_nobody
def test_finding_c_channel_socket_directory_denies_a_different_uid(tmp_path):
    """A second control for the same disposition: even if Finding C were
    reachable, the private one-shot channel itself (§9, 0700 directory /
    0600 socket) independently denies any non-owner peer a connection at
    all — defence in depth beyond the exec-time provenance check."""
    channel = OneShotChannel(directory=tmp_path / "chan")
    try:
        assert stat.S_IMODE(os.stat(channel._dir).st_mode) == 0o700
        assert stat.S_IMODE(os.stat(channel.path).st_mode) == 0o600
        probe = subprocess.run(
            [
                "sudo", "-n", "-u", "nobody", sys.executable, "-c",
                textwrap.dedent(
                    f"""
                    import socket, sys
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    try:
                        s.connect({str(channel.path)!r})
                    except OSError as exc:
                        print("DENIED", exc.errno)
                        sys.exit(0)
                    print("CONNECTED")
                    sys.exit(0)
                    """
                ),
            ],
            capture_output=True, text=True, timeout=15,
        )
        assert probe.returncode == 0, probe.stderr
        assert "DENIED" in probe.stdout, probe.stdout
    finally:
        channel.close()


# ═══════════════════════════════════════════════════════════════════════════
# Transitive import attack — hostile PYTHONPATH / cwd-shadow module, tested
# against the genuine end-to-end launch_and_exchange path.
# ═══════════════════════════════════════════════════════════════════════════


@linux_only
def test_transitive_import_hostile_pythonpath_not_inherited_end_to_end(installed, tmp_path, monkeypatch):
    """Plant a hostile ``pcae`` shadow package on ``PYTHONPATH`` in THIS
    (launcher) process's own environment — simulating a compromised or
    misconfigured invoking agent/CI environment — then run the real,
    unmodified ``launch_and_exchange`` for a genuine ``certification_read``.
    The shadow package writes a marker file the instant it is imported by
    ANY process. If the closed child-environment allowlist
    (``hpac_pawa_helper_launcher._CLOSED_ENV_ALLOWLIST = ("LANG", "LC_ALL")``)
    is respected, the marker must never appear and the read must still
    succeed against the genuine production ``pcae.core`` package."""
    root, authority, resolved = installed
    shadow_dir = tmp_path / "hostile-site"
    shadow_pkg = shadow_dir / "pcae"
    shadow_pkg.mkdir(parents=True)
    marker = tmp_path / "shadow-imported.marker"
    (shadow_pkg / "__init__.py").write_text(
        f"import pathlib\npathlib.Path({str(marker)!r}).write_text('IMPORTED')\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(shadow_dir))

    request = build_signed_request(
        operation=HelperOperation.CERTIFICATION_READ,
        session_id="s-transitive-import-1",
        operation_params={
            "record_type": "presentation_mechanism_descriptor",
            "record_key": resolved.descriptor.mechanism_id,
        },
        request_id="req-transitive-import-1",
        expiry="2099-01-01T00:00:00.000000Z",
        installation_id=resolved.record.installation_id,
        generation=resolved.record.generation,
    )
    outcome = launch_and_exchange(**_launch_kwargs(root, resolved, request=request))

    assert not marker.exists(), "the hostile PYTHONPATH shadow package was imported by the exec'd helper"
    assert outcome.outcome == "completed", outcome
    assert outcome.response is not None and outcome.response.decision == "PERFORMED", outcome.response
    assert outcome.response.result_payload["contents"]["mechanism_id"] == resolved.descriptor.mechanism_id


@linux_only
def test_transitive_import_cwd_shadow_module_not_reachable(installed, tmp_path, monkeypatch):
    """Same attack shape, but via a cwd-relative shadow module rather than
    ``PYTHONPATH``: place a single-file ``pcae.py`` (not a package) in the
    directory that becomes this launcher process's cwd, then launch for
    real. A cwd-relative shadow only matters if something puts cwd on
    ``sys.path`` for the child — this test empirically confirms nothing in
    the production launch path does."""
    root, authority, resolved = installed
    shadow_cwd = tmp_path / "hostile-cwd"
    shadow_cwd.mkdir()
    marker = tmp_path / "cwd-shadow-imported.marker"
    (shadow_cwd / "pcae.py").write_text(
        f"import pathlib\npathlib.Path({str(marker)!r}).write_text('IMPORTED')\nraise SystemExit(1)\n"
    )
    old_cwd = os.getcwd()
    os.chdir(shadow_cwd)
    try:
        request = build_signed_request(
            operation=HelperOperation.CERTIFICATION_READ,
            session_id="s-transitive-import-2",
            operation_params={
                "record_type": "presentation_mechanism_descriptor",
                "record_key": resolved.descriptor.mechanism_id,
            },
            request_id="req-transitive-import-2",
            expiry="2099-01-01T00:00:00.000000Z",
            installation_id=resolved.record.installation_id,
            generation=resolved.record.generation,
        )
        outcome = launch_and_exchange(**_launch_kwargs(root, resolved, request=request))
    finally:
        os.chdir(old_cwd)

    assert not marker.exists(), "the cwd-shadow module was imported by the exec'd helper"
    assert outcome.outcome == "completed", outcome
    assert outcome.response is not None and outcome.response.decision == "PERFORMED", outcome.response
    assert outcome.response.result_payload["contents"]["mechanism_id"] == resolved.descriptor.mechanism_id
