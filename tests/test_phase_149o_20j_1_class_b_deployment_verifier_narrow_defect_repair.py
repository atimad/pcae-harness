"""Phase 149O.20J.1 — Class-B Deployment Verifier / Model-A
Environment-Lock Narrow Defect Repair: independent regression suite for
exactly the three Blocking findings recorded (not repaired) by Phase
149O.20J:

  B-CBV-J-1: `.pth` executable-import tab-form bypass
  B-CBV-J-2: effective GID omission (`os.getegid()` not folded in)
  B-CBV-J-3: trusted-Git ACL-blindness

Every assertion here calls the real, repaired production functions
(never an inlined copy of pre-repair logic) — these are positive
security assertions about the current source, not historical-defect
documentation. The frozen 149O.20J suite
(`test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_
lock_independent_implementation_verification.py`) is left unmodified as
historical evidence of the pre-repair state and is expected to show
exactly one now-superseded finding-confirmation assertion fail, per
that test's own docstring instruction.
"""
from __future__ import annotations

import inspect
import os
import site
import stat
import sys

import pytest

from pcae.core import hatp_class_b_topology_verifier as topo_mod
from pcae.core import hatp_environment_lock_verifier as env_mod
from pcae.core.hatp_class_b_topology_verifier import (
    ClassBConformanceStatus,
    _current_agent_identity,
    _resolve_trusted_executable,
    _resolve_trusted_executable_with_effective_access,
)
from pcae.core.hatp_environment_lock_verifier import _check_trusted_git, _pth_line_is_executable

pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]


# ═══════════════════════════════════════════════════════════════════════
# B-CBV-J-1 — .pth executable-import tab-form repair
# ═══════════════════════════════════════════════════════════════════════


def test_pth_line_classification_matches_real_cpython_site_addpackage_source():
    """Independently re-derive CPython's own classification predicate
    from the running interpreter's actual `site.addpackage` source
    (not from prior phase prose) and confirm the repaired helper
    matches it line-for-line on the same probe set."""

    real_source = inspect.getsource(site.addpackage)
    assert 'line.startswith(("import ", "import\\t"))' in real_source.replace("'", '"')

    probes = [
        "import foo",
        "import\tfoo",
        "# import foo",
        "",
        "   ",
        "/safe/path",
        "  import foo",
        "importfoo",
        "import",
    ]
    for line in probes:
        if line.startswith("#"):
            expected = False
        elif line.strip() == "":
            expected = False
        else:
            expected = line.startswith(("import ", "import\t"))
        assert _pth_line_is_executable(line) is expected, line


def test_pth_space_import_line_rejected(tmp_path, monkeypatch):
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    pth = site_dir / "evil.pth"
    pth.write_text("import os\n", encoding="utf-8")
    monkeypatch.setattr(env_mod, "_effective_sys_path_dirs", lambda: [site_dir])
    monkeypatch.setattr(env_mod, "_effective_write_access", lambda *a, **k: (False, "not_writable", ()))
    result = env_mod._check_pth_files(999999, frozenset())
    assert result.satisfied is False
    assert result.status == "unsafe_pth_file_present"


def test_pth_tab_import_line_now_rejected(tmp_path, monkeypatch):
    """B-CBV-J-1 exit assertion: the tab-delimited executable form that
    149O.20J demonstrated as a live bypass is now detected."""

    site_dir = tmp_path / "site"
    site_dir.mkdir()
    pth = site_dir / "evil.pth"
    pth.write_text("import\tos\n", encoding="utf-8")
    monkeypatch.setattr(env_mod, "_effective_sys_path_dirs", lambda: [site_dir])
    monkeypatch.setattr(env_mod, "_effective_write_access", lambda *a, **k: (False, "not_writable", ()))
    result = env_mod._check_pth_files(999999, frozenset())
    assert result.satisfied is False
    assert result.status == "unsafe_pth_file_present"
    assert any("import" in item for item in result.evidence)


def test_pth_comment_line_is_not_executable(tmp_path, monkeypatch):
    site_dir = tmp_path / "site"
    site_dir.mkdir()
    pth = site_dir / "commented.pth"
    pth.write_text("# import os\n", encoding="utf-8")
    monkeypatch.setattr(env_mod, "_effective_sys_path_dirs", lambda: [site_dir])
    monkeypatch.setattr(env_mod, "_effective_write_access", lambda *a, **k: (False, "not_writable", ()))
    result = env_mod._check_pth_files(999999, frozenset())
    assert result.satisfied is True
    assert result.status == "pth_files_present_admin_controlled_no_import_lines"


def test_pth_ordinary_path_line_still_evaluated_as_path(tmp_path, monkeypatch):
    """Regression guard (item 6): repair must not regress detection of
    an agent-writable path-injection `.pth` file that carries no
    executable import line at all.

    Phase ...1.1R (configured-agent-identity threading repair) note:
    this scenario deterministically mocks `_effective_write_access`
    (as its three sibling tests in this file already do) rather than
    relying on real host ACL-tool-resolution behavior for the
    fictitious `agent_uid=999999` subject. Before this repair,
    `_acl_grants_agent_write_macos`/`_linux` resolved their own
    `ls`/`getfacl` trust via the *ambient* live-process identity
    instead of the `(agent_uid, agent_gids)` subject actually being
    evaluated — so on a host where the live process's own PATH
    happens to contain a user-writable directory ahead of the system
    tools (e.g. a Homebrew-prefixed `PATH`), tool resolution failed and
    the ACL check came back indeterminate (`None`), which
    `_effective_write_access` propagates as "not proven safe" and this
    check was (accidentally, not by genuine ACL evidence) still
    satisfied. After the repair, tool resolution is correctly
    evaluated against the fictitious subject `999999` — who does not
    own that Homebrew directory — so it resolves the real system tool
    and correctly finds no ACL grant for uid 999999 on this freshly
    created file, i.e. `_effective_write_access` now correctly, not
    accidentally, reports `False`. Mocking `_effective_write_access`
    directly isolates this test's actual regression concern (item 6:
    an ordinary path-only `.pth` line is still evaluated, not skipped)
    from real host ACL/PATH specifics, matching this file's other three
    `_check_pth_files` scenarios."""

    site_dir = tmp_path / "site"
    site_dir.mkdir()
    pth = site_dir / "shadow.pth"
    pth.write_text(str(tmp_path / "shadow"), encoding="utf-8")
    monkeypatch.setattr(env_mod, "_effective_sys_path_dirs", lambda: [site_dir])
    monkeypatch.setattr(env_mod, "_effective_write_access", lambda *a, **k: (True, "agent_writable", ()))
    result = env_mod._check_pth_files(999999, frozenset())
    assert result.satisfied is False
    assert result.status == "unsafe_pth_file_present"


def test_pth_leading_whitespace_import_not_treated_executable(tmp_path, monkeypatch):
    """Matches real CPython semantics precisely (item 4): a line whose
    `import` is preceded by whitespace is not executed by
    `site.addpackage()` (its `startswith` check runs on the raw line),
    so the repaired predicate must not over-flag it as an executable
    import line either — the pre-repair `.strip()`-first predicate
    would have."""

    assert _pth_line_is_executable("  import foo") is False


# ═══════════════════════════════════════════════════════════════════════
# B-CBV-J-2 — effective GID repair
# ═══════════════════════════════════════════════════════════════════════


def test_current_agent_identity_now_independently_folds_in_getegid():
    src = inspect.getsource(topo_mod._current_agent_identity)
    assert "os.getegid()" in src


def test_effective_group_set_always_contains_getegid():
    _uid, gids = _current_agent_identity()
    assert os.getegid() in gids


def test_getgroups_empty_plus_getegid_present_case(monkeypatch):
    monkeypatch.setattr(os, "getgroups", lambda: [])
    monkeypatch.setattr(os, "getegid", lambda: 30)
    _uid, gids = _current_agent_identity()
    assert gids == frozenset({30})


def test_getgroups_and_getegid_union_deduplicated(monkeypatch):
    monkeypatch.setattr(os, "getgroups", lambda: [10, 20, 30])
    monkeypatch.setattr(os, "getegid", lambda: 30)
    _uid, gids = _current_agent_identity()
    assert gids == frozenset({10, 20, 30})


def test_getgroups_disjoint_from_getegid_both_present(monkeypatch):
    monkeypatch.setattr(os, "getgroups", lambda: [10, 20])
    monkeypatch.setattr(os, "getegid", lambda: 30)
    _uid, gids = _current_agent_identity()
    assert gids == frozenset({10, 20, 30})


def test_effective_gid_only_group_write_now_detected(tmp_path, monkeypatch):
    """B-CBV-J-2 exit assertion: a file whose group matches only the
    process's true effective gid (simulated absent from
    `os.getgroups()`), and which is group-writable, is now detected as
    agent-writable because `_current_agent_identity` independently
    folds in `os.getegid()`."""

    target = tmp_path / "authority_file"
    target.write_text("x", encoding="utf-8")
    real_gid = os.getegid()
    os.chmod(target, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP)
    st = target.stat()
    monkeypatch.setattr(os, "chown", lambda *a, **k: None, raising=False)

    # Simulate: getgroups() deliberately excludes the file's real gid
    # (models egid being absent from the supplementary-group list);
    # getegid() still independently reports it.
    monkeypatch.setattr(os, "getgroups", lambda: [])
    monkeypatch.setattr(os, "getegid", lambda: st.st_gid)

    agent_uid, agent_gids = _current_agent_identity()
    assert st.st_gid in agent_gids  # sanity: repair folds it in

    from pcae.core.hatp_class_b_topology_verifier import _effective_write_access

    write, reason, _evidence = _effective_write_access(target, 999999, agent_gids)
    assert write is True
    assert reason == "agent_group_membership_grants_write"


# ═══════════════════════════════════════════════════════════════════════
# B-CBV-J-3 — trusted-Git ACL repair
# ═══════════════════════════════════════════════════════════════════════


def test_resolve_trusted_executable_base_primitive_unchanged():
    """No-recursion-trap guard (item 13/14/22): the narrow PATH-walk
    primitive must remain exactly as-is — ACL-unaware, mode+group only
    — so that ACL-tool resolution (`getfacl`/`ls`) routed through it
    from within the ACL check cannot become mutually recursive."""

    src = inspect.getsource(topo_mod._resolve_trusted_executable)
    assert "_mode_and_group_write_access(" in src
    assert "_effective_write_access(" not in src
    assert "_acl_grants_agent_write(" not in src


def test_effective_access_wrapper_reuses_shared_effective_access_primitives():
    """Shared-semantics guard (item 12/22): the new ACL-aware wrapper
    must compose the *same* `_effective_write_access` /
    `_ancestor_chain_safe` primitives already used for Protected Root
    (HBDC-REQ-016/017), not a second, independent Git-specific ACL
    parser."""

    src = inspect.getsource(topo_mod._resolve_trusted_executable_with_effective_access)
    assert "_resolve_trusted_executable(" in src
    assert "_effective_write_access(" in src
    assert "_ancestor_chain_safe(" in src


def test_check_trusted_git_now_uses_effective_access_wrapper():
    src = inspect.getsource(env_mod._check_trusted_git)
    assert "_resolve_trusted_executable_with_effective_access(" in src


def test_fake_git_via_hostile_path_still_rejected_after_repair(tmp_path, monkeypatch):
    """Regression guard (item 19): the pre-existing fake-Git/PATH
    defense must not regress under the ACL-aware wrapper."""

    hostile_dir = tmp_path / "hostile_bin"
    hostile_dir.mkdir()
    fake_git = hostile_dir / "git"
    fake_git.write_text("#!/bin/sh\necho pwned\n", encoding="utf-8")
    fake_git.chmod(0o755)
    monkeypatch.setenv("PATH", str(hostile_dir))
    assert _resolve_trusted_executable_with_effective_access("git") is None


def test_acl_writable_resolved_target_is_rejected_by_wrapper(tmp_path, monkeypatch):
    """B-CBV-J-3 exit assertion: even when the narrow, mode-only PATH
    walk resolves a target, the wrapper must still reject it if the
    shared ACL-inclusive effective-access check reports agent write
    access on the resolved executable itself."""

    fake_dir = tmp_path / "bin"
    fake_dir.mkdir()
    fake_target = fake_dir / "git"
    fake_target.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    fake_target.chmod(0o555)  # mode bits alone: not agent-writable

    monkeypatch.setattr(topo_mod, "_resolve_trusted_executable", lambda name: fake_target)

    def _fake_effective_write_access(path, agent_uid, agent_gids):
        if path == fake_target:
            return True, "acl_grants_agent_write", (str(path),)
        return False, "no_effective_write_access", ()

    monkeypatch.setattr(topo_mod, "_effective_write_access", _fake_effective_write_access)
    assert topo_mod._resolve_trusted_executable_with_effective_access("git") is None


def test_acl_writable_ancestor_of_resolved_target_is_rejected(tmp_path, monkeypatch):
    """B-CBV-J-3 exit assertion, ancestor form (item 17/21): mode bits
    on the resolved executable itself are safe, but an ancestor
    directory carries an ACL-only write grant."""

    fake_dir = tmp_path / "bin"
    fake_dir.mkdir()
    fake_target = fake_dir / "git"
    fake_target.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    fake_target.chmod(0o555)

    monkeypatch.setattr(topo_mod, "_resolve_trusted_executable", lambda name: fake_target)
    monkeypatch.setattr(
        topo_mod,
        "_effective_write_access",
        lambda path, agent_uid, agent_gids: (False, "no_effective_write_access", ()),
    )
    monkeypatch.setattr(
        topo_mod,
        "_ancestor_chain_safe",
        lambda start, agent_uid, agent_gids: (False, ("ancestor_writable:acl",)),
    )
    assert topo_mod._resolve_trusted_executable_with_effective_access("git") is None


def test_acl_inspection_indeterminate_fails_closed_not_treated_as_safe(tmp_path, monkeypatch):
    """Platform-fail-closed guard (item 15): an indeterminate ACL
    result (tool unavailable) must never be interpreted as "no ACL
    exists" — the wrapper must reject, not accept."""

    fake_dir = tmp_path / "bin"
    fake_dir.mkdir()
    fake_target = fake_dir / "git"
    fake_target.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    fake_target.chmod(0o555)

    monkeypatch.setattr(topo_mod, "_resolve_trusted_executable", lambda name: fake_target)
    monkeypatch.setattr(
        topo_mod,
        "_effective_write_access",
        lambda path, agent_uid, agent_gids: (None, "acl_inspection_unavailable", ()),
    )
    assert topo_mod._resolve_trusted_executable_with_effective_access("git") is None


def test_acl_safe_resolved_target_and_ancestors_are_trusted(tmp_path, monkeypatch):
    """Positive control: when both the resolved executable and its
    full ancestor chain are proven non-agent-writable (mode, group,
    and ACL), the wrapper returns the resolved path, matching the
    unrepaired primitive's own behavior in the fully-safe case."""

    fake_dir = tmp_path / "bin"
    fake_dir.mkdir()
    fake_target = fake_dir / "git"
    fake_target.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    fake_target.chmod(0o555)

    monkeypatch.setattr(topo_mod, "_resolve_trusted_executable", lambda name: fake_target)
    monkeypatch.setattr(
        topo_mod,
        "_effective_write_access",
        lambda path, agent_uid, agent_gids: (False, "no_effective_write_access", ()),
    )
    monkeypatch.setattr(
        topo_mod,
        "_ancestor_chain_safe",
        lambda start, agent_uid, agent_gids: (True, ("ancestor_boundary",)),
    )
    assert topo_mod._resolve_trusted_executable_with_effective_access("git") == fake_target


def test_no_acl_tool_resolution_recursion_through_wrapper(monkeypatch):
    """Anti-recursion guard (item 13): resolving the ACL-tool itself
    (`getfacl`/`ls`, from inside `_acl_grants_agent_write`) must never
    call the ACL-aware wrapper — only the narrow base primitive. Proven
    by making the wrapper raise if ever invoked and confirming a real
    ACL-branch traversal on a nonexistent path (which short-circuits
    before any subprocess call) does not trigger it."""

    def _poison(name):
        raise AssertionError("_resolve_trusted_executable_with_effective_access must not be called recursively")

    monkeypatch.setattr(topo_mod, "_resolve_trusted_executable_with_effective_access", _poison)
    from pcae.core.hatp_class_b_topology_verifier import _acl_grants_agent_write

    # A missing path exercises the real ACL branch's tool-resolution
    # call path (via ls/getfacl -> _resolve_trusted_executable) without
    # requiring platform-specific ACL fixtures.
    result = _acl_grants_agent_write(env_mod.Path("/nonexistent/path/for/acl/probe"), 999999, frozenset())
    assert result in (None, False, True)


# ═══════════════════════════════════════════════════════════════════════
# Cross-cutting regression guards
# ═══════════════════════════════════════════════════════════════════════


def test_read_only_guarantee_still_holds_across_all_three_modules():
    import ast
    from pathlib import Path as _Path

    # "replace" deliberately excluded: `_check_module_origin_containment`
    # calls `str.replace("/", ".")` on a relative-path string, an
    # already-disclosed non-blocking AST-scan ambiguity (str.replace vs
    # Path.replace), not a filesystem mutation -- out of this narrow
    # repair's scope.
    forbidden = frozenset(
        {"mkdir", "makedirs", "chmod", "chown", "unlink", "rmdir", "rename", "symlink", "link",
         "write_text", "write_bytes", "setuid", "seteuid", "setgid", "setegid", "setreuid", "setresuid"}
    )
    for module in (topo_mod, env_mod):
        tree = ast.parse(_Path(module.__file__).read_text(encoding="utf-8"))
        hits = [node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr in forbidden]
        assert not hits, f"{module.__name__}: {hits}"


def test_public_entry_points_still_accept_no_authority_parameter():
    from pcae.core.hatp_class_b_topology_verifier import verify_class_b_topology_conformance
    from pcae.core.hatp_environment_lock_verifier import verify_environment_lock_conformance

    assert len(inspect.signature(verify_class_b_topology_conformance).parameters) == 0
    assert len(inspect.signature(verify_environment_lock_conformance).parameters) == 0


def test_real_host_environment_lock_result_still_not_compliant():
    from pcae.core.hatp_environment_lock_verifier import verify_environment_lock_conformance

    result = verify_environment_lock_conformance()
    assert result.status != ClassBConformanceStatus.COMPLIANT


def test_real_host_trusted_git_check_runs_without_exception():
    result = _check_trusted_git()
    assert result.check_id == "HBDC-REQ-038"


def test_aggregator_module_byte_unchanged_since_20i():
    """Strong expectation (item 28): no repair required in the
    aggregator — confirmed unchanged by this phase."""

    import subprocess

    proc = subprocess.run(
        ["git", "diff", "--name-only", "HEAD", "--", "src/pcae/core/hatp_class_b_conformance.py"],
        capture_output=True,
        text=True,
        cwd=str(env_mod.Path(__file__).resolve().parents[1]),
    )
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""
