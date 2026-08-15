"""Phase 149O.20L.7D.7 -- Class-B Verifier Narrow Source Repair for
HBDC-REQ-022/030/035.

Independently-authored companion test module (imports nothing from
7D.6's own diagnosis-phase test module as oracle -- new fixtures, new
assertions, re-derived from primary source and HBDC-001 v1.0 directly).
Proves both repairs diagnosed by 149O.20L.7D.6 and implemented by this
phase:

1. B-149O.20L.7D.6-1 -- the shared `importlib.metadata.distribution
   ("pcae")` lookup-key defect (HBDC-REQ-022/035), repaired to
   `"pcae-harness"`.
2. B-149O.20L.7D.6-3 -- the unconditional `_effective_write_access`
   symlink=True heuristic (HBDC-REQ-030 false positive), repaired to
   distinguish the symlink's own parent-chain mutability, the resolved
   target's mutability, and the target's own ancestor-chain mutability,
   while remaining fail-closed on broken links, symlink chains, and
   inspection errors.

This module does not repeat 7D.6's own test assertions; it proves the
*repair*, not the diagnosis (already independently reconfirmed against
primary source/contract text as part of this phase's own diagnosis
reconstruction, documented in the phase report).
"""
from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path

import pytest

from pcae.core import hatp_class_b_conformance as conformance
from pcae.core import hatp_class_b_topology_verifier as topo
from pcae.core import hatp_environment_lock_verifier as envlock

pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]


def _agent_uid_gids() -> "tuple[int, frozenset[int]]":
    return os.geteuid(), frozenset(os.getgroups())


# ═══════════════════════════════════════════════════════════════════════════
# Defect A: distribution-name lookup key (HBDC-REQ-022/035)
# ═══════════════════════════════════════════════════════════════════════════


def test_source_no_longer_contains_wrong_distribution_literal():
    """The exact defective literal named in the governing instruction and
    7D.6's finding B-149O.20L.7D.6-1 is gone from both call sites."""

    for module in (conformance, envlock):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert 'distribution("pcae")' not in source
        assert 'distribution("pcae-harness")' in source


def test_correct_distribution_name_resolves_on_this_host():
    """Real `importlib.metadata` lookup, not mocked -- proves the
    repaired literal is the actual PEP 621 project name, matching
    `pyproject.toml`'s `name = "pcae-harness"`."""

    dist = importlib.metadata.distribution("pcae-harness")
    assert dist is not None
    assert dist.version


def test_wrong_historical_name_does_not_silently_resolve():
    """The old, defective literal must not become an accepted fallback
    -- it should still raise `PackageNotFoundError` on this host,
    proving the repair changed the actual lookup key, not just added a
    second successful path alongside the broken one."""

    with pytest.raises(importlib.metadata.PackageNotFoundError):
        importlib.metadata.distribution("pcae")


def test_req_022_reaches_downstream_direct_url_evaluation(monkeypatch):
    """REQ-022 must not merely stop failing at the lookup step -- it
    must reach and evaluate its own downstream `direct_url.json`
    evidence. A distribution whose lookup succeeds but whose editable
    flag is `False` must still fail, on the *correct* downstream reason
    code, proving the repair didn't just swallow the exception."""

    class _FakeDist:
        _path = "/fake/pcae_harness-0.2.0.dist-info"

        def read_text(self, name):
            if name == "direct_url.json":
                return '{"dir_info": {"editable": false}, "url": "file:///opt/pcae/runtime/src"}'
            return None

    monkeypatch.setattr(
        conformance.importlib.metadata, "distribution", lambda name: _FakeDist() if name == "pcae-harness" else (_ for _ in ()).throw(conformance.importlib.metadata.PackageNotFoundError())
    )
    result = conformance._check_model_a_deployment(agent_uid=os.geteuid())
    assert result.check_id == "HBDC-REQ-024"
    assert result.satisfied is False
    assert result.status == "unsupported_deployment_model_not_editable_install"


def test_req_022_succeeds_when_editable_install_confirmed(monkeypatch):
    class _FakeDist:
        _path = "/fake/pcae_harness-0.2.0.dist-info"

        def read_text(self, name):
            if name == "direct_url.json":
                return '{"dir_info": {"editable": true}, "url": "file:///opt/pcae/runtime/src"}'
            return None

    monkeypatch.setattr(
        conformance.importlib.metadata, "distribution", lambda name: _FakeDist() if name == "pcae-harness" else (_ for _ in ()).throw(conformance.importlib.metadata.PackageNotFoundError())
    )
    result = conformance._check_model_a_deployment(agent_uid=os.geteuid())
    assert result.check_id == "HBDC-REQ-022"
    assert result.satisfied is True
    assert result.status == "model_a_editable_install_confirmed"


def test_req_035_reaches_downstream_metadata_writability_evaluation(monkeypatch, tmp_path):
    """REQ-035 must reach its own `dist_dir`/`direct_url.json`/`RECORD`
    writability evaluation, not merely stop raising `PackageNotFoundError`
    at the lookup step."""

    monkeypatch.setattr(topo, "_acl_grants_agent_write", lambda path, uid, gids: False)
    dist_dir = tmp_path / "pcae_harness-0.2.0.dist-info"
    dist_dir.mkdir()
    (dist_dir / "direct_url.json").write_text('{"dir_info": {"editable": true}}', encoding="utf-8")
    dist_dir.chmod(0o500)
    (dist_dir / "direct_url.json").chmod(0o400)

    class _FakeDist:
        _path = str(dist_dir)

    monkeypatch.setattr(
        envlock.importlib.metadata, "distribution", lambda name: _FakeDist() if name == "pcae-harness" else (_ for _ in ()).throw(envlock.importlib.metadata.PackageNotFoundError())
    )
    try:
        result = envlock._check_editable_install_metadata(*_agent_uid_gids())
        assert result.check_id == "HBDC-REQ-035"
        assert result.satisfied is True
        assert result.status == "editable_install_metadata_admin_controlled"
    finally:
        dist_dir.chmod(0o700)


def test_req_035_still_fails_when_metadata_agent_writable(monkeypatch, tmp_path):
    """The repair must not weaken REQ-035's actual security property --
    an agent-writable dist-info directory must still fail, proving the
    repair only fixed the lookup key, not the downstream evaluation."""

    dist_dir = tmp_path / "pcae_harness-0.2.0.dist-info"
    dist_dir.mkdir()  # left agent-owned/writable (default tmp_path mode)

    class _FakeDist:
        _path = str(dist_dir)

    monkeypatch.setattr(
        envlock.importlib.metadata, "distribution", lambda name: _FakeDist() if name == "pcae-harness" else (_ for _ in ()).throw(envlock.importlib.metadata.PackageNotFoundError())
    )
    result = envlock._check_editable_install_metadata(*_agent_uid_gids())
    assert result.check_id == "HBDC-REQ-035"
    assert result.satisfied is False
    assert result.status == "editable_install_metadata_agent_writable"


def test_req_022_fail_closed_when_metadata_genuinely_unavailable(monkeypatch):
    monkeypatch.setattr(
        conformance.importlib.metadata,
        "distribution",
        lambda name: (_ for _ in ()).throw(conformance.importlib.metadata.PackageNotFoundError()),
    )
    result = conformance._check_model_a_deployment(agent_uid=os.geteuid())
    assert result.satisfied is False
    assert result.status == "pcae_distribution_metadata_not_found"


def test_req_035_fail_closed_when_metadata_genuinely_unavailable(monkeypatch):
    monkeypatch.setattr(
        envlock.importlib.metadata,
        "distribution",
        lambda name: (_ for _ in ()).throw(envlock.importlib.metadata.PackageNotFoundError()),
    )
    result = envlock._check_editable_install_metadata(*_agent_uid_gids())
    assert result.satisfied is False
    assert result.status == "pcae_distribution_metadata_not_found"


# ═══════════════════════════════════════════════════════════════════════════
# Defect B: symlink effective-write-access (HBDC-REQ-030)
# ═══════════════════════════════════════════════════════════════════════════


def _stub_admin_boundary(monkeypatch, tmp_path):
    """Treat everything outside `tmp_path` as an admin-controlled,
    never-agent-writable boundary -- mirrors production Protected Root
    ancestors (`/etc`, `/usr`, `/`), which are admin-owned outside the
    test fixture. Same idiom as
    test_phase_149o_20i_hatp_class_b_topology_verifier.py's
    `test_ancestor_chain_safe_boundary`."""

    monkeypatch.setattr(topo, "_acl_grants_agent_write", lambda path, uid, gids: False)
    real_effective_write_access = topo._effective_write_access

    def _stubbed(path, agent_uid, agent_gids):
        if path == tmp_path or tmp_path not in path.parents:
            return False, "outside_fixture_treated_as_admin_boundary", ()
        return real_effective_write_access(path, agent_uid, agent_gids)

    monkeypatch.setattr(topo, "_effective_write_access", _stubbed)


def test_dell_equivalent_safe_symlink_is_effectively_unwritable(monkeypatch, tmp_path):
    """Faithful regression fixture for the real Dell case (7D.6 §13):
    `/usr/lib/python3.12/sitecustomize.py` symlinked to
    `/etc/python3.12/sitecustomize.py`, with the symlink, its parent, the
    target, and the target's parent all admin-controlled and
    agent-unwritable. The pre-repair verifier returned `True` (unsafe)
    unconditionally here -- the exact false positive this phase repairs.
    The repaired verifier must classify this as effectively unwritable."""

    _stub_admin_boundary(monkeypatch, tmp_path)
    lib_dir = tmp_path / "usr_lib_python3.12"
    etc_dir = tmp_path / "etc_python3.12"
    lib_dir.mkdir()
    etc_dir.mkdir()
    target = etc_dir / "sitecustomize.py"
    target.write_text("# admin-controlled\n", encoding="utf-8")
    link = lib_dir / "sitecustomize.py"
    link.symlink_to(target)
    lib_dir.chmod(0o500)
    etc_dir.chmod(0o500)
    target.chmod(0o444)
    try:
        write, reason, _evidence = topo._effective_write_access(link, *_agent_uid_gids())
        assert write is False
        assert reason == "symlink_fully_closed"
    finally:
        lib_dir.chmod(0o700)
        etc_dir.chmod(0o700)
        target.chmod(0o600)


def test_writable_symlink_parent_is_unsafe(monkeypatch, tmp_path):
    _stub_admin_boundary(monkeypatch, tmp_path)
    lib_dir = tmp_path / "lib"  # left agent-writable (default mode)
    etc_dir = tmp_path / "etc"
    lib_dir.mkdir()
    etc_dir.mkdir()
    target = etc_dir / "sitecustomize.py"
    target.write_text("x", encoding="utf-8")
    link = lib_dir / "sitecustomize.py"
    link.symlink_to(target)
    etc_dir.chmod(0o500)
    target.chmod(0o444)
    try:
        write, reason, _evidence = topo._effective_write_access(link, *_agent_uid_gids())
        assert write is True
        assert reason == "symlink_parent_chain_writable"
    finally:
        etc_dir.chmod(0o700)
        target.chmod(0o600)


def test_writable_resolved_target_is_unsafe(monkeypatch, tmp_path):
    _stub_admin_boundary(monkeypatch, tmp_path)
    lib_dir = tmp_path / "lib"
    etc_dir = tmp_path / "etc"
    lib_dir.mkdir()
    etc_dir.mkdir()
    target = etc_dir / "sitecustomize.py"
    target.write_text("x", encoding="utf-8")  # left agent-owner-writable (default mode)
    link = lib_dir / "sitecustomize.py"
    link.symlink_to(target)
    lib_dir.chmod(0o500)
    etc_dir.chmod(0o500)
    try:
        write, reason, _evidence = topo._effective_write_access(link, *_agent_uid_gids())
        assert write is True
        assert reason.startswith("symlink_target_writable:")
    finally:
        lib_dir.chmod(0o700)
        etc_dir.chmod(0o700)


def test_writable_target_ancestor_is_unsafe(monkeypatch, tmp_path):
    """Target file itself is unwritable, but its containing directory is
    agent-writable -- the agent can still replace the target file
    through the writable ancestor, per governing instruction §14."""

    _stub_admin_boundary(monkeypatch, tmp_path)
    lib_dir = tmp_path / "lib"
    etc_dir = tmp_path / "etc"  # left agent-writable (default mode)
    lib_dir.mkdir()
    etc_dir.mkdir()
    target = etc_dir / "sitecustomize.py"
    target.write_text("x", encoding="utf-8")
    target.chmod(0o444)
    link = lib_dir / "sitecustomize.py"
    link.symlink_to(target)
    lib_dir.chmod(0o500)
    try:
        write, reason, _evidence = topo._effective_write_access(link, *_agent_uid_gids())
        assert write is True
        assert "symlink_target_ancestor_writable" in reason
    finally:
        lib_dir.chmod(0o700)
        target.chmod(0o600)


def test_group_writable_target_via_effective_group_is_unsafe(monkeypatch, tmp_path):
    _stub_admin_boundary(monkeypatch, tmp_path)
    lib_dir = tmp_path / "lib"
    etc_dir = tmp_path / "etc"
    lib_dir.mkdir()
    etc_dir.mkdir()
    target = etc_dir / "sitecustomize.py"
    target.write_text("x", encoding="utf-8")
    link = lib_dir / "sitecustomize.py"
    link.symlink_to(target)
    lib_dir.chmod(0o500)
    etc_dir.chmod(0o500)

    st = target.stat()
    monkeypatch.setattr(topo.os, "getgroups", lambda: [st.st_gid])
    monkeypatch.setattr(topo.os, "geteuid", lambda: st.st_uid + 1)
    target.chmod(0o070)
    try:
        write, reason, _evidence = topo._effective_write_access(link, st.st_uid + 1, frozenset({st.st_gid}))
        assert write is True
        assert "agent_group_membership_grants_write" in reason
    finally:
        lib_dir.chmod(0o700)
        etc_dir.chmod(0o700)
        target.chmod(0o600)


def test_acl_writable_target_is_unsafe(monkeypatch, tmp_path):
    _stub_admin_boundary(monkeypatch, tmp_path)
    lib_dir = tmp_path / "lib"
    etc_dir = tmp_path / "etc"
    lib_dir.mkdir()
    etc_dir.mkdir()
    target = etc_dir / "sitecustomize.py"
    target.write_text("x", encoding="utf-8")
    target.chmod(0o444)
    link = lib_dir / "sitecustomize.py"
    link.symlink_to(target)
    lib_dir.chmod(0o500)
    etc_dir.chmod(0o500)

    monkeypatch.setattr(topo, "_acl_grants_agent_write", lambda path, uid, gids: path == target)
    try:
        write, reason, _evidence = topo._effective_write_access(link, *_agent_uid_gids())
        assert write is True
        assert "acl_grants_agent_write" in reason
    finally:
        lib_dir.chmod(0o700)
        etc_dir.chmod(0o700)
        target.chmod(0o600)


def test_broken_symlink_is_indeterminate_not_silently_safe(tmp_path):
    """`Path.exists()` follows symlinks, so `_effective_write_access`'s
    own pre-existing top-level existence gate (unchanged by this repair)
    catches a broken symlink before reaching the symlink branch at all
    -- still `None`/indeterminate, still fail-closed, just via the
    pre-existing `path_missing` reason rather than a new symlink-specific
    one. This is the correct, unmodified behavior for this case; this
    test documents it rather than asserting a repair-introduced reason
    that this case never reaches."""

    link = tmp_path / "broken"
    link.symlink_to(tmp_path / "does_not_exist")
    write, reason, _evidence = topo._effective_write_access(link, *_agent_uid_gids())
    assert write is None
    assert reason == "path_missing"


def test_symlink_loop_is_indeterminate_not_silently_safe(tmp_path):
    """Same top-level-gate interaction as the broken-symlink case above:
    `Path.exists()` on a true two-hop symlink cycle cannot resolve the
    loop (CPython's `Path.exists()` treats an `OSError`/`ELOOP` failure
    to stat as non-existence, verified empirically on this platform)
    and the pre-existing top-level gate returns `path_missing` before
    the symlink branch is ever reached -- still `None`, still
    fail-closed."""

    a = tmp_path / "a"
    b = tmp_path / "b"
    a.symlink_to(b)
    b.symlink_to(a)
    write, reason, _evidence = topo._effective_write_access(a, *_agent_uid_gids())
    assert write is None
    assert reason == "path_missing"


def test_symlink_unreadable_is_indeterminate(monkeypatch, tmp_path):
    _stub_admin_boundary(monkeypatch, tmp_path)
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    link.parent.chmod(0o500)  # tmp_path itself: make the immediate parent chain safe first

    def _boom(path):
        raise OSError("simulated readlink failure")

    monkeypatch.setattr(topo.os, "readlink", _boom)
    try:
        write, reason, _evidence = topo._effective_write_access(link, *_agent_uid_gids())
        assert write is None
        assert reason == "symlink_unreadable"
    finally:
        link.parent.chmod(0o700)


def test_relative_symlink_resolves_correctly(monkeypatch, tmp_path):
    """A relative symlink target must be resolved against the symlink's
    own parent directory, matching real OS/`readlink` semantics -- not
    against the process CWD or the repository root."""

    _stub_admin_boundary(monkeypatch, tmp_path)
    etc_dir = tmp_path / "etc"
    etc_dir.mkdir()
    target = etc_dir / "sitecustomize.py"
    target.write_text("x", encoding="utf-8")
    target.chmod(0o444)
    link = etc_dir / "link_to_sitecustomize.py"
    link.symlink_to("sitecustomize.py")  # relative target, same directory
    etc_dir.chmod(0o500)
    try:
        write, reason, _evidence = topo._effective_write_access(link, *_agent_uid_gids())
        assert write is False
        assert reason == "symlink_fully_closed"
    finally:
        etc_dir.chmod(0o700)
        target.chmod(0o600)


def test_chained_symlink_safe_case_resolves_through_both_hops(monkeypatch, tmp_path):
    _stub_admin_boundary(monkeypatch, tmp_path)
    etc_dir = tmp_path / "etc"
    etc_dir.mkdir()
    real_target = etc_dir / "real.py"
    real_target.write_text("x", encoding="utf-8")
    real_target.chmod(0o444)
    middle_link = etc_dir / "middle.py"
    middle_link.symlink_to(real_target)
    outer_link = etc_dir / "outer.py"
    outer_link.symlink_to(middle_link)
    etc_dir.chmod(0o500)
    try:
        write, reason, _evidence = topo._effective_write_access(outer_link, *_agent_uid_gids())
        assert write is False
        assert reason == "symlink_fully_closed"
    finally:
        etc_dir.chmod(0o700)
        real_target.chmod(0o600)


def test_chained_symlink_unsafe_case_detects_deep_writable_target(monkeypatch, tmp_path):
    _stub_admin_boundary(monkeypatch, tmp_path)
    etc_dir = tmp_path / "etc"
    etc_dir.mkdir()
    real_target = etc_dir / "real.py"
    real_target.write_text("x", encoding="utf-8")  # agent-writable (default mode)
    middle_link = etc_dir / "middle.py"
    middle_link.symlink_to(real_target)
    outer_link = etc_dir / "outer.py"
    outer_link.symlink_to(middle_link)
    etc_dir.chmod(0o500)
    try:
        write, reason, _evidence = topo._effective_write_access(outer_link, *_agent_uid_gids())
        assert write is True
        assert "symlink_target_writable" in reason
    finally:
        etc_dir.chmod(0o700)


def test_symlink_chain_guard_exceeded_is_indeterminate(tmp_path):
    """Direct white-box test of the recursion guard -- calling the
    repaired helper at a depth already past `_SYMLINK_CHAIN_GUARD`
    deterministically exercises the guard clause without needing an
    OS-level symlink chain long enough to also trip the kernel's own
    independent `ELOOP` protection."""

    link = tmp_path / "link"
    link.symlink_to(tmp_path / "target")
    write, reason, _evidence = topo._symlink_effective_write_access(
        link, *_agent_uid_gids(), _depth=topo._SYMLINK_CHAIN_GUARD + 1
    )
    assert write is None
    assert reason == "symlink_chain_guard_exceeded"


def test_symlink_target_inspection_error_is_indeterminate(monkeypatch, tmp_path):
    _stub_admin_boundary(monkeypatch, tmp_path)
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)

    real_exists = Path.exists

    def _boom_exists(self):
        if self == real:
            raise OSError("simulated stat failure")
        return real_exists(self)

    monkeypatch.setattr(Path, "exists", _boom_exists)
    write, reason, _evidence = topo._effective_write_access(link, *_agent_uid_gids())
    assert write is None
    assert reason == "symlink_target_inspection_error"


# ═══════════════════════════════════════════════════════════════════════════
# Before/after: prove the old literal defect and confirm the repair fixes it
# ═══════════════════════════════════════════════════════════════════════════


def test_before_after_distribution_defect_reproduction(monkeypatch):
    """Reproduces the exact pre-repair call (`distribution("pcae")`) to
    prove it genuinely raised on this host, then proves the repaired
    call path (the real, unmocked production function) succeeds."""

    with pytest.raises(importlib.metadata.PackageNotFoundError):
        importlib.metadata.distribution("pcae")  # the old, defective literal

    real = importlib.metadata.distribution
    monkeypatch.setattr(
        conformance.importlib.metadata,
        "distribution",
        lambda name: real("pcae-harness") if name == "pcae-harness" else (_ for _ in ()).throw(importlib.metadata.PackageNotFoundError()),
    )
    result = conformance._check_model_a_deployment(agent_uid=os.geteuid())
    assert result.status != "pcae_distribution_metadata_not_found"


def test_before_after_symlink_defect_reproduction(tmp_path, monkeypatch):
    """Reproduces the exact pre-repair unconditional-True symlink branch
    inline (the literal old code), proving it would have misclassified
    the Dell-equivalent safe fixture, then proves the repaired
    production function correctly classifies the identical fixture."""

    _stub_admin_boundary(monkeypatch, tmp_path)
    etc_dir = tmp_path / "etc"
    etc_dir.mkdir()
    target = etc_dir / "sitecustomize.py"
    target.write_text("x", encoding="utf-8")
    target.chmod(0o444)
    link = tmp_path / "link" / "sitecustomize.py"
    link.parent.mkdir()
    link.symlink_to(target)
    link.parent.chmod(0o500)
    etc_dir.chmod(0o500)
    try:
        def _old_defective_branch(path):
            return path.is_symlink()  # pre-repair: True (writable) for any symlink, unconditionally

        assert _old_defective_branch(link) is True  # old code would have called this unsafe

        write, reason, _evidence = topo._effective_write_access(link, *_agent_uid_gids())
        assert write is False  # repaired code correctly finds it safe
        assert reason == "symlink_fully_closed"
    finally:
        link.parent.chmod(0o700)
        etc_dir.chmod(0o700)
        target.chmod(0o600)


# ═══════════════════════════════════════════════════════════════════════════
# Unsafe topology remains rejected -- adversarial baseline sanity
# ═══════════════════════════════════════════════════════════════════════════


def test_non_symlink_paths_completely_unaffected_by_this_repair(tmp_path):
    """Regression guard: this phase's repair only touches the
    `path.is_symlink()` branch of `_effective_write_access` -- ordinary
    file/directory mode-bit evaluation must be byte-for-byte unchanged."""

    target = tmp_path / "plain"
    target.mkdir()
    write, reason, _evidence = topo._effective_write_access(target, *_agent_uid_gids())
    assert write is True
    assert reason == "agent_is_owner_with_write_bit"
