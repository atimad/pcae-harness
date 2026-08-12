"""Phase 149O.20J.2 — Class-B Deployment Verifier Narrow Defect Repair
Independent Verification.

Independently verifies 149O.20J.1's three narrow defect repairs
(B-CBV-J-1 .pth executable-import, B-CBV-J-2 effective-GID, B-CBV-J-3
trusted-Git ACL) from primary source. This suite intentionally does
NOT import 149O.20J.1's own test constants/helpers/fixtures as an
oracle -- historical-defect reconstruction reads the pre-repair source
directly via `git show <parent-commit>:<path>` (never a hand-copied
inline snapshot), and live-repair assertions call the current
production functions directly.

Read-only throughout: no production source, contract, or script file
is imported for mutation; filesystem fixtures live under a scratch
tmp_path and are cleaned up by pytest.
"""
from __future__ import annotations

import ast
import inspect
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

# The exact commit whose tree is 149O.20J.1's own pre-repair baseline
# (149O.20J's own close-idle commit; independently re-confirmed equal
# to `0f2bb93c^` in this phase's own inspection, not merely trusted
# from 149O.20J.1's prose).
PRE_REPAIR_COMMIT = "dce667e73ed079051ab436179f83d8a776bcb42b"
REPAIR_COMMIT = "0f2bb93c"


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        stdin=subprocess.DEVNULL,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


@pytest.fixture(scope="module")
def historical_topology_source() -> str:
    return _git_show(PRE_REPAIR_COMMIT, "src/pcae/core/hatp_class_b_topology_verifier.py")


@pytest.fixture(scope="module")
def historical_env_lock_source() -> str:
    return _git_show(PRE_REPAIR_COMMIT, "src/pcae/core/hatp_environment_lock_verifier.py")


@pytest.fixture(scope="module")
def repaired_topology_source() -> str:
    return _git_show(REPAIR_COMMIT, "src/pcae/core/hatp_class_b_topology_verifier.py")


@pytest.fixture(scope="module")
def repaired_env_lock_source() -> str:
    return _git_show(REPAIR_COMMIT, "src/pcae/core/hatp_environment_lock_verifier.py")


# ═══════════════════════════════════════════════════════════════════════════
# §1 Commit-boundary self-check
# ═══════════════════════════════════════════════════════════════════════════


def test_pre_repair_commit_is_exact_parent_of_repair_commit():
    parent = subprocess.run(
        ["git", "rev-parse", f"{REPAIR_COMMIT}^"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
    ).stdout.strip()
    assert parent == PRE_REPAIR_COMMIT


def test_repair_commit_diff_touches_only_the_two_verifier_modules():
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{PRE_REPAIR_COMMIT}", REPAIR_COMMIT, "--", "src/pcae/"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
    )
    changed = {line for line in result.stdout.splitlines() if line}
    assert changed == {
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
    }


def test_conformance_aggregator_byte_unchanged_since_pre_repair():
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{PRE_REPAIR_COMMIT}", "HEAD", "--",
         "src/pcae/core/hatp_class_b_conformance.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
    )
    assert result.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════════
# §2 J-1: historical reproduction against pre-repair source (read via git,
# never an inlined copy)
# ═══════════════════════════════════════════════════════════════════════════


def test_historical_pth_predicate_uses_stripped_space_only_form(historical_env_lock_source):
    assert 'line.strip().startswith("import ")' in historical_env_lock_source
    assert "_pth_line_is_executable" not in historical_env_lock_source


def test_historical_pth_predicate_misses_tab_form_reconstructed():
    # Reconstructed exactly from the pre-repair source string confirmed
    # above -- not hand-invented.
    def historical_predicate(line: str) -> bool:
        return line.strip().startswith("import ")

    assert historical_predicate("import\tfoo") is False  # historical bypass
    assert historical_predicate("import foo") is True
    assert historical_predicate("  import foo") is True  # over-flags leading whitespace too


def test_cpython_site_addpackage_actually_executes_tab_form_line(tmp_path):
    import site

    (tmp_path / "probe.pth").write_text('import\tsys; sys.__pcae_j2_probe__ = True\n')
    try:
        site.addpackage(str(tmp_path), "probe.pth", set())
        assert getattr(sys, "__pcae_j2_probe__", False) is True
    finally:
        if hasattr(sys, "__pcae_j2_probe__"):
            delattr(sys, "__pcae_j2_probe__")


def test_cpython_addpackage_source_matches_documented_grammar():
    import site

    src = inspect.getsource(site.addpackage)
    assert 'line.startswith("#")' in src
    assert 'line.strip() == ""' in src
    assert 'line.startswith(("import ", "import\\t"))' in src


# ═══════════════════════════════════════════════════════════════════════════
# §3 J-1: live repair verification against current production source
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.hatp_environment_lock_verifier import (  # noqa: E402
    _pth_line_is_executable,
    _check_pth_files,
    _effective_sys_path_dirs,
    _effective_write_access as _env_effective_write_access,
)


@pytest.mark.parametrize(
    "line,expected",
    [
        ("import foo", True),
        ("import\tfoo", True),
        ("import  foo", True),
        ("import\t\tfoo", True),
        (" import foo", False),
        ("\timport foo", False),
        ("import", False),
        ("importfoo", False),
        ("Import foo", False),
        ("#import foo", False),
        ("# import foo", False),
        ("", False),
        ("   ", False),
        ("/safe/path", False),
    ],
)
def test_pth_line_is_executable_matches_cpython_grammar(line, expected):
    assert _pth_line_is_executable(line) is expected


def test_check_pth_files_comment_safepath_tabimport_writable_matrix(tmp_path, monkeypatch):
    (tmp_path / "a_comment.pth").write_text("# import foo\n/safe/path\n")
    (tmp_path / "b_safe_path.pth").write_text("/some/safe/path\n")
    (tmp_path / "c_tab_import.pth").write_text("import\tfoo\n")
    (tmp_path / "d_writable.pth").write_text("/harmless/path\n")

    import pcae.core.hatp_environment_lock_verifier as m

    monkeypatch.setattr(m, "_effective_sys_path_dirs", lambda: [tmp_path])

    def fake_write_access(path, uid, gids):
        if path.name == "d_writable.pth":
            return True, "agent_is_owner_with_write_bit", (str(path),)
        return False, "no_effective_write_access", (str(path),)

    monkeypatch.setattr(m, "_effective_write_access", fake_write_access)

    result = m._check_pth_files(agent_uid=99999, agent_gids=frozenset({99999}))
    assert result.satisfied is False
    joined = " ".join(result.evidence)
    assert "c_tab_import.pth" in joined and "import_prefixed_line_present" in joined
    assert "d_writable.pth" in joined
    assert "a_comment.pth" not in joined
    assert "b_safe_path.pth" not in joined


# ═══════════════════════════════════════════════════════════════════════════
# §4 J-2: historical reproduction and live repair verification
# ═══════════════════════════════════════════════════════════════════════════


def test_historical_identity_source_omits_getegid(historical_topology_source):
    assert "os.getegid()" not in historical_topology_source
    assert "return os.geteuid(), frozenset(os.getgroups())" in historical_topology_source


def test_historical_identity_reconstruction_omits_effective_gid(monkeypatch):
    def historical_identity():
        return os.geteuid(), frozenset(os.getgroups())

    monkeypatch.setattr(os, "getgroups", lambda: [10, 20])
    monkeypatch.setattr(os, "getegid", lambda: 30)
    _, gids = historical_identity()
    assert 30 not in gids


from pcae.core.hatp_class_b_topology_verifier import (  # noqa: E402
    _current_agent_identity,
    _effective_write_access,
)


def test_repaired_identity_source_uses_getegid_not_getgid():
    src = inspect.getsource(_current_agent_identity)
    assert "os.getegid()" in src
    assert "os.getgid()" not in src


@pytest.mark.parametrize(
    "getgroups_val,getegid_val,expected",
    [
        ([10, 20], 30, {10, 20, 30}),
        ([10, 20, 30], 30, {10, 20, 30}),
        ([], 30, {30}),
    ],
)
def test_effective_group_matrix(monkeypatch, getgroups_val, getegid_val, expected):
    monkeypatch.setattr(os, "getgroups", lambda: getgroups_val)
    monkeypatch.setattr(os, "getegid", lambda: getegid_val)
    _, gids = _current_agent_identity()
    assert set(gids) == expected
    assert isinstance(gids, frozenset)


def test_effective_group_duplicate_safety(monkeypatch):
    monkeypatch.setattr(os, "getgroups", lambda: [30, 30, 10])
    monkeypatch.setattr(os, "getegid", lambda: 30)
    _, gids = _current_agent_identity()
    assert sorted(gids) == [10, 30]


def test_effective_gid_only_group_write_detected(tmp_path, monkeypatch):
    """Decisive J-2 test (governing-prompt item 15): a file whose group
    matches only the true effective GID -- excluded from
    os.getgroups() -- and is group-writable, must be detected. Isolated
    to the mode+group channel by forcing the ACL sub-check to report
    'no ACL', so the result reflects the group-membership repair alone,
    not incidental ACL-branch behavior on this host."""

    target = tmp_path / "target"
    target.write_text("x")
    os.chmod(target, 0o060)  # group rw only

    class FakeStat:
        def __init__(self, real):
            self._real = real

        def __getattr__(self, name):
            if name == "st_gid":
                return 30
            return getattr(self._real, name)

    class FakePath(type(target)):
        def stat(self, *a, **kw):
            return FakeStat(Path.stat(self, *a, **kw))

        def exists(self, *a, **kw):
            return True

        def is_symlink(self):
            return False

    fake_target = FakePath(target)

    import pcae.core.hatp_class_b_topology_verifier as m

    monkeypatch.setattr(m, "_acl_grants_agent_write", lambda path, uid, gids: False)

    agent_uid = 99999
    historical_gids = frozenset({10, 20})
    repaired_gids = frozenset({10, 20}) | {30}

    write_h, _reason_h, _ = m._effective_write_access(fake_target, agent_uid, historical_gids)
    write_r, reason_r, _ = m._effective_write_access(fake_target, agent_uid, repaired_gids)

    assert write_h is False  # historical group set misses the grant
    assert write_r is True and reason_r == "agent_group_membership_grants_write"


def test_historical_check_trusted_git_never_consults_acl(historical_env_lock_source):
    assert "_resolve_trusted_executable(" in historical_env_lock_source
    assert "_resolve_trusted_executable_with_effective_access" not in historical_env_lock_source


# ═══════════════════════════════════════════════════════════════════════════
# §5 J-3: trusted-Git ACL repair -- historical reproduction, live repair,
# non-recursion, fail-closed, fake-Git regression
# ═══════════════════════════════════════════════════════════════════════════

from pcae.core.hatp_class_b_topology_verifier import (  # noqa: E402
    _resolve_trusted_executable,
    _resolve_trusted_executable_with_effective_access,
    _acl_grants_agent_write,
)


def _make_git_fixture(tmp_path, dir_mode=0o500, file_mode=0o500):
    git_exe = tmp_path / "git"
    git_exe.write_text("#!/bin/sh\necho fake-git\n")
    os.chmod(git_exe, file_mode)
    os.chmod(tmp_path, dir_mode)
    return git_exe


def test_git_executable_acl_only_write_grant_rejected(tmp_path, monkeypatch):
    git_exe = _make_git_fixture(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))

    import pcae.core.hatp_class_b_topology_verifier as m

    resolved_git_baseline = m._resolve_trusted_executable("git")
    assert resolved_git_baseline is not None  # sane baseline before ACL simulation

    def acl_grants_on_exe(path, uid, gids):
        return path == git_exe.resolve()

    monkeypatch.setattr(m, "_acl_grants_agent_write", acl_grants_on_exe)

    # Historical behavior: the narrow primitive alone never consults ACL.
    resolved_historical = m._resolve_trusted_executable("git")
    assert resolved_historical is not None  # historical blindness reproduced

    # Repaired wrapper: rejects.
    resolved_repaired = m._resolve_trusted_executable_with_effective_access("git")
    assert resolved_repaired is None

    os.chmod(tmp_path, 0o700)


def test_git_immediate_parent_acl_only_write_grant_rejected(tmp_path, monkeypatch):
    child = tmp_path / "child"
    child.mkdir()
    git_exe = _make_git_fixture(child)
    monkeypatch.setenv("PATH", str(child))

    import pcae.core.hatp_class_b_topology_verifier as m

    def acl_grants_on_parent(path, uid, gids):
        return path == child.resolve()

    monkeypatch.setattr(m, "_acl_grants_agent_write", acl_grants_on_parent)
    resolved = m._resolve_trusted_executable_with_effective_access("git")
    assert resolved is None

    os.chmod(child, 0o700)


def test_git_deep_ancestor_acl_only_grant_bounded_by_first_safe_boundary(tmp_path, monkeypatch):
    """Documents (does not newly regress) a pre-existing, unmodified
    characteristic of the shared `_ancestor_chain_safe` primitive
    (149O.20I, identical for Protected Root's own HBDC-REQ-017 check,
    already independently disclosed by 149O.20J's own
    `test_deep_ancestor_writable_beyond_immediate_parent_is_caught`):
    the ancestor walk stops at the first *proven-non-writable* ancestor
    and does not examine further ancestors above that boundary. J.1's
    repair reuses this primitive unmodified -- it does not introduce,
    widen, or narrow this characteristic, and it is not one of the
    three named B-CBV-J-1/2/3 defects. Recorded here as an independent,
    non-blocking observation, not a J-3 regression."""

    grandparent = tmp_path / "wa"
    grandparent.mkdir()
    parent = grandparent / "safe_parent"
    parent.mkdir()
    git_exe = _make_git_fixture(parent)
    os.chmod(grandparent, 0o700)  # agent-writable, two levels up
    # Fixture dir first (resolves our fake git), then a real system bin
    # dir so the ACL tool (getfacl/ls) itself resolves for real rather
    # than reporting indeterminate -- an indeterminate result at
    # `parent` would make `_ancestor_chain_safe` keep walking (masking
    # the very characteristic under test), rather than genuinely
    # proving `parent` a safe stop-boundary.
    monkeypatch.setenv("PATH", f"{parent}{os.pathsep}/bin")

    import pcae.core.hatp_class_b_topology_verifier as m

    resolved = m._resolve_trusted_executable_with_effective_access("git")
    # Documents current (pre-existing, disclosed) behavior: the safe
    # immediate parent forms the stop boundary, so the writable
    # grandparent is never examined.
    assert resolved is not None

    os.chmod(grandparent, 0o700)
    os.chmod(parent, 0o700)


def test_path_preceding_agent_writable_directory_rejects_resolution(tmp_path, monkeypatch):
    early = tmp_path / "early"
    late = tmp_path / "late"
    early.mkdir()
    late.mkdir()
    _make_git_fixture(late)
    os.chmod(early, 0o700)  # agent-writable, precedes `late` on PATH
    monkeypatch.setenv("PATH", f"{early}{os.pathsep}{late}")

    import pcae.core.hatp_class_b_topology_verifier as m

    resolved = m._resolve_trusted_executable_with_effective_access("git")
    assert resolved is None

    os.chmod(late, 0o700)


def test_fake_git_via_hostile_path_still_rejected(tmp_path, monkeypatch):
    early = tmp_path / "early"
    late = tmp_path / "late"
    early.mkdir()
    late.mkdir()
    _make_git_fixture(late)
    fake_git = early / "git"
    fake_git.write_text("#!/bin/sh\necho pwned\n")
    os.chmod(fake_git, 0o700)
    os.chmod(early, 0o700)
    monkeypatch.setenv("PATH", f"{early}{os.pathsep}{late}")

    import pcae.core.hatp_class_b_topology_verifier as m

    resolved_narrow = m._resolve_trusted_executable("git")
    resolved_wrapper = m._resolve_trusted_executable_with_effective_access("git")
    assert resolved_narrow is None
    assert resolved_wrapper is None

    os.chmod(late, 0o700)


def test_acl_inspection_failure_fails_closed(tmp_path, monkeypatch):
    _make_git_fixture(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))

    import pcae.core.hatp_class_b_topology_verifier as m

    monkeypatch.setattr(m, "_acl_grants_agent_write", lambda path, uid, gids: None)
    resolved = m._resolve_trusted_executable_with_effective_access("git")
    assert resolved is None  # indeterminate ACL evidence is never treated as safe

    os.chmod(tmp_path, 0o700)


def test_no_acl_tool_resolution_recursion_through_wrapper(tmp_path, monkeypatch):
    """Dynamic re-entrancy poison test: the wrapper must never be
    called from within the ACL-tool-resolution path it itself uses."""

    _make_git_fixture(tmp_path)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}/usr/bin{os.pathsep}/bin")

    import pcae.core.hatp_class_b_topology_verifier as m

    call_count = {"n": 0}
    orig = m._resolve_trusted_executable_with_effective_access

    def poisoned(name):
        call_count["n"] += 1
        if call_count["n"] > 1:
            raise RuntimeError("re-entrancy detected")
        return orig(name)

    monkeypatch.setattr(m, "_resolve_trusted_executable_with_effective_access", poisoned)

    # Exercise the real ACL branch directly; it must resolve its own
    # tool (getfacl/ls) via the narrow primitive only.
    m._acl_grants_agent_write(tmp_path / "git", os.getuid(), frozenset())
    assert call_count["n"] == 0

    os.chmod(tmp_path, 0o700)


def test_wrapper_call_graph_never_cycles_back_to_itself():
    src = inspect.getsource(sys.modules["pcae.core.hatp_class_b_topology_verifier"])
    tree = ast.parse(src)
    relevant = {
        "_resolve_trusted_executable",
        "_resolve_trusted_executable_with_effective_access",
        "_effective_write_access",
        "_acl_grants_agent_write",
        "_acl_grants_agent_write_linux",
        "_acl_grants_agent_write_macos",
        "_ancestor_chain_safe",
        "_mode_and_group_write_access",
    }
    calls: "dict[str, set]" = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            called = set()
            for n in ast.walk(node):
                if isinstance(n, ast.Call):
                    f = n.func
                    if isinstance(f, ast.Name):
                        called.add(f.id)
                    elif isinstance(f, ast.Attribute):
                        called.add(f.attr)
            calls[node.name] = called & relevant

    def cycles_back(start, target, visited=None):
        if visited is None:
            visited = set()
        for nxt in calls.get(start, set()):
            if nxt == target:
                return True
            if nxt not in visited:
                visited.add(nxt)
                if cycles_back(nxt, target, visited):
                    return True
        return False

    assert not cycles_back(
        "_resolve_trusted_executable_with_effective_access",
        "_resolve_trusted_executable_with_effective_access",
    )


def test_resolve_trusted_executable_base_primitive_unchanged_since_pre_repair():
    result = subprocess.run(
        ["git", "diff", f"{PRE_REPAIR_COMMIT}", "HEAD", "-G", "def _resolve_trusted_executable\\(",
         "--", "src/pcae/core/hatp_class_b_topology_verifier.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
    )
    # -G(pickaxe) reports no hunk touching the narrow primitive's def line
    assert "-def _resolve_trusted_executable(" not in result.stdout
    assert "+def _resolve_trusted_executable(" not in result.stdout


def test_topology_and_git_share_identical_effective_access_primitives():
    """Item 29: no divergent semantics -- both Protected Root
    (topology) and trusted-Git resolution route through the exact same
    `_effective_write_access` / `_ancestor_chain_safe` functions, not
    two independently-maintained policies."""

    wrapper_src = inspect.getsource(_resolve_trusted_executable_with_effective_access)
    assert "_effective_write_access" in wrapper_src
    assert "_ancestor_chain_safe" in wrapper_src


def test_git_decisions_use_repaired_effective_group_semantics():
    wrapper_src = inspect.getsource(_resolve_trusted_executable_with_effective_access)
    assert "_current_agent_identity()" in wrapper_src


# ═══════════════════════════════════════════════════════════════════════════
# §6 Cross-cutting: read-only, zero-consumer, HMIC non-binding, stability
# ═══════════════════════════════════════════════════════════════════════════

_MUTATING_ATTRS = frozenset(
    {"mkdir", "makedirs", "chmod", "chown", "unlink", "rmdir", "rename",
     "symlink", "link", "write_bytes", "setuid", "seteuid", "setgid", "setegid"}
)

_MODULE_PATHS = (
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
    "src/pcae/core/hatp_class_b_conformance.py",
)


@pytest.mark.parametrize("relpath", _MODULE_PATHS)
def test_read_only_static_scan_no_mutating_calls(relpath):
    tree = ast.parse((REPO_ROOT / relpath).read_text())
    found = [n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr in _MUTATING_ATTRS]
    # write_text is intentionally excluded from the shared set below,
    # since it also appears as a legitimate string/Path-adjacent name;
    # explicit exclusion of str.replace false-positives is not needed
    # because "replace" is not in _MUTATING_ATTRS here.
    assert found == []


def test_zero_production_consumers_of_the_three_verifier_modules():
    names = ("hatp_class_b_topology_verifier", "hatp_environment_lock_verifier", "hatp_class_b_conformance")
    consumers = []
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        if path.name in {"hatp_class_b_topology_verifier.py", "hatp_environment_lock_verifier.py", "hatp_class_b_conformance.py"}:
            continue
        text = path.read_text(errors="replace")
        if any(name in text for name in names):
            consumers.append(str(path))
    assert consumers == []


def test_readiness_certification_admin_pb_files_have_zero_references():
    targets = [
        REPO_ROOT / "src/pcae/core/hatp_mandatory_cutover.py",
        REPO_ROOT / "src/pcae/core/hatp_mandatory_certification.py",
        REPO_ROOT / "scripts/hatp_certification_admin.py",
        REPO_ROOT / "src/pcae/core/permission_broker.py",
        REPO_ROOT / "src/pcae/core/hatp_rollback_consumption.py",
    ]
    names = ("hatp_class_b_topology_verifier", "hatp_environment_lock_verifier", "hatp_class_b_conformance")
    for target in targets:
        text = target.read_text()
        assert not any(name in text for name in names), target


def test_hmic_frozen_scope_excludes_all_three_verifier_modules():
    from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES

    assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 25
    joined = " ".join(_FROZEN_AUTHORITY_BEARING_FILES)
    assert "hatp_class_b_topology_verifier" not in joined
    assert "hatp_environment_lock_verifier" not in joined
    assert "hatp_class_b_conformance" not in joined


def test_status_vocabulary_unchanged_six_member_closed_set():
    from pcae.core.hatp_class_b_topology_verifier import ClassBConformanceStatus

    assert {m.value for m in ClassBConformanceStatus} == {
        "COMPLIANT", "NON_COMPLIANT", "INDETERMINATE",
        "ACCESS_ERROR", "MALFORMED_STATE", "UNSUPPORTED_DEPLOYMENT_MODEL",
    }


def test_public_entry_points_accept_no_caller_authority_parameter():
    from pcae.core.hatp_class_b_topology_verifier import verify_class_b_topology_conformance
    from pcae.core.hatp_environment_lock_verifier import verify_environment_lock_conformance
    from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance

    assert dict(inspect.signature(verify_class_b_topology_conformance).parameters) == {}
    assert dict(inspect.signature(verify_environment_lock_conformance).parameters) == {}
    params = inspect.signature(verify_class_b_deployment_conformance).parameters
    assert list(params) == ["root"]
    assert params["root"].annotation in ("Optional[HarnessPath]",) or "HarnessPath" in str(params["root"].annotation)


def test_fail_closed_aggregation_all_satisfied_yields_compliant_single_failure_does_not():
    from pcae.core.hatp_class_b_topology_verifier import ClassBCheckResult, _build_result, ClassBConformanceStatus

    all_pass = [ClassBCheckResult(f"REQ-{i}", True, "ok", ()) for i in range(5)]
    assert _build_result(all_pass).status == ClassBConformanceStatus.COMPLIANT

    for i in range(5):
        checks = [ClassBCheckResult(f"REQ-{j}", j != i, "ok" if j != i else "fail", ()) for j in range(5)]
        assert _build_result(checks).status != ClassBConformanceStatus.COMPLIANT


def test_safe_check_wrapper_fails_closed_on_exception():
    from pcae.core.hatp_class_b_topology_verifier import _safe_check

    def boom():
        raise RuntimeError("inspection blew up")

    result = _safe_check("REQ-X", boom)
    assert result.satisfied is False


def test_meta_path_class_and_instance_finders_both_flagged(monkeypatch):
    from pcae.core.hatp_environment_lock_verifier import _check_meta_path_hooks

    class FakeClassFinder:
        pass

    class FakeInstanceFinder:
        pass

    monkeypatch.setattr(sys, "meta_path", [FakeClassFinder, FakeInstanceFinder()])
    result = _check_meta_path_hooks()
    assert result.satisfied is False
    assert any("FakeClassFinder" in e for e in result.evidence)
    assert any("FakeInstanceFinder" in e for e in result.evidence)


def test_path_env_read_for_trusted_resolution_not_flagged_as_admin_inference():
    from pcae.core.hatp_class_b_topology_verifier import _check_no_env_or_name_based_admin_inference

    result = _check_no_env_or_name_based_admin_inference()
    assert result.satisfied is True


def test_subprocess_inventory_unchanged_since_pre_repair(historical_topology_source, repaired_topology_source):
    assert historical_topology_source.count("subprocess.run(") == repaired_topology_source.count("subprocess.run(") == 2


def test_real_host_result_is_not_compliant_and_causes_zero_mutation():
    from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance
    from pcae.core.hatp_class_b_topology_verifier import ClassBConformanceStatus

    before = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True).stdout
    result = verify_class_b_deployment_conformance()
    after = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True).stdout

    assert result.status != ClassBConformanceStatus.COMPLIANT
    assert before == after
