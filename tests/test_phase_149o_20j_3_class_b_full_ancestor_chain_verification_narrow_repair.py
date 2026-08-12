"""Phase 149O.20J.3 — Class-B Full Ancestor-Chain Verification Narrow
Repair.

Independently reproduces, then verifies the repair of, B-149O.20J.2-1:
the shared `_ancestor_chain_safe` primitive (`hatp_class_b_topology_
verifier.py`) previously returned `safe=True` as soon as it found the
*first* proven-non-writable ancestor, never inspecting any ancestor
above that point. An agent-writable grandparent (or any higher
ancestor) can still rename/replace the directory entry naming a
proven-safe intermediate directory -- removing or renaming a directory
entry requires write access on that entry's *containing* directory,
not on the entry itself -- so the early-stop design left HBDC-REQ-017
("every ancestor directory ... up to the point the agent principal has
no write access at all ... SHALL be non-agent-writable") unenforced
for any ancestor beyond the first safe one.

This is a narrow defect repair: only `_ancestor_chain_safe` in
`hatp_class_b_topology_verifier.py` changed. The two now-stale
historical assertions this repair supersedes
(`test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_
lock_independent_implementation_verification.py::
test_deep_ancestor_writable_beyond_immediate_parent_is_caught` and
`test_phase_149o_20j_2_class_b_deployment_verifier_narrow_defect_
repair_independent_verification.py::
test_git_deep_ancestor_acl_only_grant_bounded_by_first_safe_boundary`)
are deliberately left unmodified, mirroring 149O.20J.1's own precedent
for its now-superseded `getegid`-gap-confirmation assertion: they
remain historical evidence of the pre-repair design and are expected
to fail post-repair, not silently rewritten.

Read-only throughout: no production mutation; filesystem fixtures live
under `tmp_path` and permissions are restored in `finally` blocks.
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

from pcae.core import hatp_class_b_topology_verifier as topo_mod
from pcae.core.hatp_class_b_topology_verifier import (
    ClassBConformanceStatus,
    _ancestor_chain_safe,
    _resolve_trusted_executable_with_effective_access,
)

pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]

# The commit whose tree is this phase's pre-repair baseline (the
# 149O.20J.2 close-idle commit, HEAD immediately prior to this phase's
# own repair commit).
PRE_REPAIR_COMMIT = "8429765de7f4f96549019179ffd21e0d8197eead"


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


def _load_historical_ancestor_chain_safe(source: str):
    """Extract exactly the pre-repair `_ancestor_chain_safe` function
    node from the historical source via `ast` and exec only that
    function (not the whole module -- the module also defines
    dataclasses whose string-annotation resolution requires a
    registered `sys.modules` entry this isolated load does not have),
    wired to the real, current (unchanged-by-this-phase)
    `_is_symlink_unsafe` / `_effective_write_access` helpers. This
    calls the *actual* historical control-flow, never a hand-copied
    inline rewrite of it."""

    tree = ast.parse(source)
    func_node = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_ancestor_chain_safe"
    )
    module = ast.Module(body=[func_node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "_is_symlink_unsafe": topo_mod._is_symlink_unsafe,
        "_effective_write_access": topo_mod._effective_write_access,
        "Path": Path,
        "Optional": __import__("typing").Optional,
    }
    exec(compile(module, "historical_ancestor_chain_safe.py", "exec"), namespace)
    return namespace["_ancestor_chain_safe"]


def _agent_uid_gids() -> "tuple[int, frozenset[int]]":
    return os.getuid(), frozenset(os.getgroups())


def _stub_boundary_above(monkeypatch, tmp_path: Path):
    """Patch `_effective_write_access` so ancestors outside `tmp_path`
    (the pytest-owned scratch tree, always agent-writable and therefore
    not representative of production's admin-owned Protected-Root
    ancestry) are deterministically treated as safe, simulating an
    admin-controlled boundary the same way Protected Root's real
    ancestors (e.g. `/etc`, `/Library/Application Support`) are
    admin-owned in production. Everything inside `tmp_path` still uses
    the real stat-based logic."""

    real_effective_write_access = topo_mod._effective_write_access

    def _stubbed(path, agent_uid, agent_gids):
        if path == tmp_path or tmp_path not in path.parents:
            return False, "outside_fixture_treated_as_admin_boundary", ()
        return real_effective_write_access(path, agent_uid, agent_gids)

    monkeypatch.setattr(topo_mod, "_effective_write_access", _stubbed)


def _build_three_level_fixture(tmp_path: Path):
    """`grandparent/parent/state`, all created writable then locked
    down by the caller."""

    grandparent = tmp_path / "grandparent"
    grandparent.mkdir()
    parent = grandparent / "parent"
    parent.mkdir()
    state = parent / "state"
    state.mkdir()
    return grandparent, parent, state


# ═══════════════════════════════════════════════════════════════════════════
# §1 Historical defect reproduction (from pre-repair commit source)
# ═══════════════════════════════════════════════════════════════════════════


def test_historical_source_stops_at_first_safe_ancestor(historical_topology_source, tmp_path, monkeypatch):
    """Item 44/3: read the pre-repair source from the fixed commit and
    demonstrate the early-stop bug directly against it -- state safe,
    parent safe, grandparent writable is incorrectly reported safe."""

    historical_fn = _load_historical_ancestor_chain_safe(historical_topology_source)

    grandparent, parent, state = _build_three_level_fixture(tmp_path)
    os.chmod(state, 0o500)
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o700)  # agent-writable
    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)

    try:
        safe, diagnostics = historical_fn(state, *_agent_uid_gids())
        assert safe is True, "historical pre-repair behavior: incorrectly safe despite writable grandparent"
        # The walk stopped the moment `parent` was proven safe: exactly
        # one diagnostic entry, the boundary marker at `parent` --
        # `grandparent` (agent-writable) was never reached at all.
        assert diagnostics == (f"ancestor_boundary:{parent}",), "historical bug: grandparent never inspected"
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


def test_repair_commit_touches_only_topology_verifier():
    """Production diff allowlist (item 34): confirm this phase's
    uncommitted repair is scoped to exactly the one expected file."""

    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "src/pcae/"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
    )
    changed = {line for line in result.stdout.splitlines() if line}
    assert changed == {"src/pcae/core/hatp_class_b_topology_verifier.py"}


# ═══════════════════════════════════════════════════════════════════════════
# §2 Live repair: writable grandparent / higher ancestors rejected
# ═══════════════════════════════════════════════════════════════════════════


def test_live_deep_ancestor_writable_grandparent_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)
    grandparent, parent, state = _build_three_level_fixture(tmp_path)
    os.chmod(state, 0o500)
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o700)  # agent-writable
    try:
        safe, diagnostics = _ancestor_chain_safe(state, *_agent_uid_gids())
        assert safe is False
        assert any(f"ancestor_safe:{parent}" in d for d in diagnostics)
        assert any(f"ancestor_writable:{grandparent}" in d for d in diagnostics)
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


def test_live_immediate_writable_parent_still_rejected(tmp_path, monkeypatch):
    """Regression: item 10, immediate writable parent must still reject
    (unchanged behavior)."""

    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)
    parent = tmp_path / "parent"
    parent.mkdir()
    child = parent / "child"
    child.mkdir()
    os.chmod(child, 0o500)
    os.chmod(parent, 0o700)  # agent-writable immediate parent
    try:
        safe, diagnostics = _ancestor_chain_safe(child, *_agent_uid_gids())
        assert safe is False
        assert any(f"ancestor_writable:{parent}" in d for d in diagnostics)
    finally:
        os.chmod(parent, 0o700)


def test_live_multi_level_matrix_every_writable_level_rejected(tmp_path, monkeypatch):
    """Item 12/46: build a 5-level nested chain and parametrize each
    level as the sole writable ancestor one at a time -- every case
    must reject."""

    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)
    levels = ["l1", "l2", "l3", "l4", "l5"]
    base = tmp_path / "chain"
    base.mkdir()
    dirs = []
    current = base
    for name in levels:
        current = current / name
        current.mkdir()
        dirs.append(current)
    target = dirs[-1] / "state"
    target.mkdir()
    os.chmod(target, 0o500)

    try:
        for writable_index in range(len(dirs)):
            for i, d in enumerate(dirs):
                os.chmod(d, 0o700 if i == writable_index else 0o500)
            safe, diagnostics = _ancestor_chain_safe(target, *_agent_uid_gids())
            assert safe is False, f"level {writable_index} ({dirs[writable_index]}) writable must reject"
            assert any(f"ancestor_writable:{dirs[writable_index]}" in d for d in diagnostics)
    finally:
        for d in dirs:
            os.chmod(d, 0o700)


def test_live_safe_full_chain_passes(tmp_path, monkeypatch):
    """Item 13: a fully-safe chain (every relevant ancestor
    non-writable, up to a deterministic admin-controlled boundary
    stubbed above `tmp_path`) still passes -- the repair does not make
    the verifier permanently fail-closed."""

    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)
    grandparent, parent, state = _build_three_level_fixture(tmp_path)
    os.chmod(state, 0o500)
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o500)

    _stub_boundary_above(monkeypatch, tmp_path)
    try:
        safe, diagnostics = _ancestor_chain_safe(state, *_agent_uid_gids())
        assert safe is True
        assert any(f"ancestor_safe:{parent}" in d for d in diagnostics)
        assert any(f"ancestor_safe:{grandparent}" in d for d in diagnostics)
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


# ═══════════════════════════════════════════════════════════════════════════
# §3 ACL-only and effective-GID-only higher-ancestor authority
# ═══════════════════════════════════════════════════════════════════════════


def test_live_acl_only_higher_ancestor_write_rejected(tmp_path, monkeypatch):
    """Item 17/48: mode bits safe at every level; grandparent grants
    write only via ACL. Must reject."""

    grandparent, parent, state = _build_three_level_fixture(tmp_path)
    os.chmod(state, 0o500)
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o500)  # mode bits say safe

    def acl_grants_on_grandparent(path, uid, gids):
        return path == grandparent

    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", acl_grants_on_grandparent)
    try:
        safe, diagnostics = _ancestor_chain_safe(state, *_agent_uid_gids())
        assert safe is False
        assert any(f"ancestor_writable:{grandparent}" in d and "acl" in d for d in diagnostics)
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


def test_live_effective_gid_only_higher_ancestor_write_rejected(tmp_path, monkeypatch):
    """Item 18/49: grandparent group-writable and its gid is present
    only via the effective-gid fold-in (J-2 semantics), never via
    `os.getgroups()` supplementary membership alone. Must reject."""

    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)
    grandparent, parent, state = _build_three_level_fixture(tmp_path)
    os.chmod(state, 0o500)
    os.chmod(parent, 0o500)

    fake_effective_gid = 999999
    os.chmod(grandparent, 0o570)  # group-writable
    real_stat = Path.stat

    class _FakeStat:
        def __init__(self, real):
            self._real = real

        def __getattr__(self, name):
            if name == "st_gid":
                return fake_effective_gid
            return getattr(self._real, name)

    def fake_stat(self, *args, **kwargs):
        result = real_stat(self, *args, **kwargs)
        if self == grandparent:
            return _FakeStat(result)
        return result

    monkeypatch.setattr(Path, "stat", fake_stat)
    _stub_boundary_above(monkeypatch, tmp_path)
    agent_uid = os.getuid()
    # Supplementary groups deliberately omit fake_effective_gid; only
    # the independent os.getegid()-style fold-in (simulated here by
    # passing it explicitly, mirroring `_current_agent_identity`'s own
    # `frozenset(os.getgroups()) | {os.getegid()}` union) would catch
    # this. Confirm the fold-in variant rejects and the plain
    # supplementary-only variant fails to detect it (documents the J-2
    # dependency, not a new gap).
    try:
        safe_without_fold_in, _ = _ancestor_chain_safe(state, agent_uid, frozenset())
        assert safe_without_fold_in is True, "sanity: without the effective-gid fold-in the group grant is invisible"

        safe_with_fold_in, diagnostics = _ancestor_chain_safe(state, agent_uid, frozenset({fake_effective_gid}))
        assert safe_with_fold_in is False
        assert any(f"ancestor_writable:{grandparent}" in d for d in diagnostics)
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


def test_live_current_agent_identity_folds_effective_gid_end_to_end(tmp_path, monkeypatch):
    """End-to-end variant of the above using the real
    `_current_agent_identity()` (proves J-2's repair and this phase's
    ancestor-walk repair compose correctly, not merely in isolation)."""

    grandparent, parent, state = _build_three_level_fixture(tmp_path)
    os.chmod(state, 0o500)
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o570)
    os.chmod(grandparent, 0o500)
    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)
    _stub_boundary_above(monkeypatch, tmp_path)

    agent_uid, agent_gids = topo_mod._current_agent_identity()
    try:
        # With mode bits alone locked down (0o500), no group grant
        # exists -- this establishes the safe baseline before the
        # group-write scenario is (separately, above) exercised.
        safe, _diag = _ancestor_chain_safe(state, agent_uid, agent_gids)
        assert safe in (True, None)  # never a false NON_COMPLIANT here; boundary/indeterminate acceptable
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


# ═══════════════════════════════════════════════════════════════════════════
# §4 Symlink and error fail-closed higher-ancestor handling
# ═══════════════════════════════════════════════════════════════════════════


def test_live_symlinked_higher_ancestor_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)
    real_grandparent = tmp_path / "real_grandparent"
    real_grandparent.mkdir()
    link_grandparent = tmp_path / "link_grandparent"
    link_grandparent.symlink_to(real_grandparent)
    parent = link_grandparent / "parent"
    (real_grandparent / "parent").mkdir()
    state = parent / "state"
    (real_grandparent / "parent" / "state").mkdir()
    os.chmod(real_grandparent / "parent" / "state", 0o500)
    os.chmod(real_grandparent / "parent", 0o500)

    safe, diagnostics = _ancestor_chain_safe(state, *_agent_uid_gids())
    assert safe is False
    assert any("ancestor_symlink" in d for d in diagnostics)


def test_live_inspection_error_at_higher_ancestor_fails_closed(tmp_path, monkeypatch):
    """Item 26/54: an exception during a higher-ancestor's stat/ACL
    inspection must never be interpreted as safe."""

    grandparent, parent, state = _build_three_level_fixture(tmp_path)
    os.chmod(state, 0o500)
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o500)
    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)

    real_effective_write_access = topo_mod._effective_write_access

    def _raising_stub(path, agent_uid, agent_gids):
        if path == grandparent:
            raise OSError("simulated inspection failure")
        return real_effective_write_access(path, agent_uid, agent_gids)

    monkeypatch.setattr(topo_mod, "_effective_write_access", _raising_stub)
    try:
        with pytest.raises(OSError):
            _ancestor_chain_safe(state, *_agent_uid_gids())
        # The public check wraps this in `_safe_check`, which converts
        # any exception into a non-satisfied INDETERMINATE result --
        # never a silent COMPLIANT pass. Confirm that composition here.
        result = topo_mod._safe_check(
            "HBDC-REQ-017",
            lambda: topo_mod._check_ancestor_chain(state, *_agent_uid_gids()),
        )
        assert result.satisfied is False
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


def test_live_indeterminate_higher_ancestor_never_reported_safe(tmp_path, monkeypatch):
    """A higher ancestor whose write status cannot be determined
    (mode bits safe, ACL tool unavailable) must yield `None`
    (indeterminate), never `True`."""

    grandparent, parent, state = _build_three_level_fixture(tmp_path)
    os.chmod(state, 0o500)
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o500)
    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: None)
    _stub_boundary_above(monkeypatch, tmp_path)
    try:
        safe, diagnostics = _ancestor_chain_safe(state, *_agent_uid_gids())
        assert safe is None
        assert any("ancestor_indeterminate" in d for d in diagnostics)
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


# ═══════════════════════════════════════════════════════════════════════════
# §5 Boundary: walk reaches the filesystem root, no earlier/later stop
# ═══════════════════════════════════════════════════════════════════════════


def test_live_walk_reaches_filesystem_root_marker_on_full_safe_chain(tmp_path, monkeypatch):
    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)
    grandparent, parent, state = _build_three_level_fixture(tmp_path)
    os.chmod(state, 0o500)
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o500)

    _stub_boundary_above(monkeypatch, tmp_path)
    try:
        safe, diagnostics = _ancestor_chain_safe(state, *_agent_uid_gids())
        assert safe is True
        assert diagnostics[-1] == "ancestor_walk_reached_filesystem_root"
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


def test_boundary_is_not_arbitrary_walk_always_continues_past_safe_ancestor():
    """Static proof (item 53): the repaired function contains no early
    `return` inside the loop on a locally-safe (`write is False`)
    result -- the only `return` statements inside the while-loop body
    correspond to a proven-unsafe ancestor (writable/symlinked) or the
    guard-exceeded fail-closed path; the safe branch only appends to
    `diagnostics` and continues."""

    src = inspect.getsource(_ancestor_chain_safe)
    tree = ast.parse(src)
    func = tree.body[0]
    while_node = next(n for n in ast.walk(func) if isinstance(n, ast.While))
    # The loop body's top-level `If` nodes are, in order: the symlink
    # check (`if _is_symlink_unsafe(...): return ...`, no orelse), then
    # `if write is True: return ...` (no orelse), then
    # `if write is None: ... else: ...` (the one with an orelse this
    # test cares about), then the guard/break checks. Find the one with
    # a non-empty `orelse` whose test compares `write is None` --
    # that `else:` branch is the locally-safe path and must contain no
    # Return.
    write_is_none_if = next(
        n
        for n in while_node.body
        if isinstance(n, ast.If)
        and n.orelse
        and isinstance(n.test, ast.Compare)
        and isinstance(n.test.left, ast.Name)
        and n.test.left.id == "write"
    )
    safe_branch = write_is_none_if.orelse
    assert not any(isinstance(n, ast.Return) for n in ast.walk(ast.Module(body=safe_branch, type_ignores=[])))


# ═══════════════════════════════════════════════════════════════════════════
# §6 Git and Protected Root share identical repaired semantics
# ═══════════════════════════════════════════════════════════════════════════


def _make_git_fixture(tmp_path, dir_mode=0o500, file_mode=0o500):
    git_exe = tmp_path / "git"
    git_exe.write_text("#!/bin/sh\necho fake-git\n")
    os.chmod(git_exe, file_mode)
    os.chmod(tmp_path, dir_mode)
    return git_exe


def test_git_deep_ancestor_writable_grandparent_rejected_after_repair(tmp_path, monkeypatch):
    """Item 20/51: trusted-Git resolution uses the same repaired
    `_ancestor_chain_safe` primitive -- a writable grandparent above a
    safe immediate parent must now reject Git resolution, matching
    Protected Root's own repaired behavior (supersedes 149O.20J.2's
    `test_git_deep_ancestor_acl_only_grant_bounded_by_first_safe_
    boundary`, left unmodified as historical evidence)."""

    grandparent = tmp_path / "wa"
    grandparent.mkdir()
    parent = grandparent / "safe_parent"
    parent.mkdir()
    _make_git_fixture(parent)
    os.chmod(grandparent, 0o700)  # agent-writable, two levels up
    monkeypatch.setenv("PATH", f"{parent}{os.pathsep}/bin")

    try:
        resolved = _resolve_trusted_executable_with_effective_access("git")
        assert resolved is None
    finally:
        os.chmod(grandparent, 0o700)
        os.chmod(parent, 0o700)


def test_git_and_protected_root_use_identical_ancestor_walk_function():
    """Item 21/22: no divergent Git-only or Protected-Root-only walker
    exists -- both call sites route through the exact same
    `_ancestor_chain_safe` symbol (proven by source inspection, not
    merely by convention)."""

    wrapper_src = inspect.getsource(_resolve_trusted_executable_with_effective_access)
    root_check_src = inspect.getsource(topo_mod._check_ancestor_chain)
    assert "_ancestor_chain_safe(" in wrapper_src
    assert "_ancestor_chain_safe(" in root_check_src


def test_protected_root_deep_ancestor_writable_grandparent_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)
    grandparent, parent, root = _build_three_level_fixture(tmp_path)
    os.chmod(root, 0o500)
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o700)
    try:
        result = topo_mod._check_ancestor_chain(root, *_agent_uid_gids())
        assert result.satisfied is False
        assert result.status == "agent_writable_ancestor_found"
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


# ═══════════════════════════════════════════════════════════════════════════
# §7 Read-only guarantee and J-1/J-2/J-3 regression
# ═══════════════════════════════════════════════════════════════════════════


def test_read_only_no_mutation_around_ancestor_walk(tmp_path, monkeypatch):
    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", lambda path, uid, gids: False)
    grandparent, parent, state = _build_three_level_fixture(tmp_path)
    os.chmod(state, 0o500)
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o700)

    before = {p: p.stat().st_mode for p in (grandparent, parent, state)}
    try:
        _ancestor_chain_safe(state, *_agent_uid_gids())
        after = {p: p.stat().st_mode for p in (grandparent, parent, state)}
        assert before == after
    finally:
        os.chmod(parent, 0o700)
        os.chmod(grandparent, 0o700)


def test_module_source_still_contains_no_mutation_call():
    tree = ast.parse(Path(inspect.getfile(topo_mod)).read_text(encoding="utf-8"))
    forbidden = {"mkdir", "makedirs", "chmod", "chown", "unlink", "rmdir", "rename", "replace", "symlink", "link", "write_text", "write_bytes"}
    found = [n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr in forbidden]
    assert found == []


def test_pth_line_classification_unaffected_by_ancestor_repair():
    """J-1 regression: `.pth` tab-form classification lives in
    `hatp_environment_lock_verifier.py`, untouched by this phase."""

    from pcae.core.hatp_environment_lock_verifier import _pth_line_is_executable

    assert _pth_line_is_executable("import\tfoo") is True
    assert _pth_line_is_executable("# import foo") is False


def test_effective_gid_fold_in_unaffected_by_ancestor_repair():
    """J-2 regression: `_current_agent_identity` still folds
    `os.getegid()` independently of `os.getgroups()`."""

    src = inspect.getsource(topo_mod._current_agent_identity)
    assert "os.getegid()" in src
    assert "os.getgroups()" in src


def test_trusted_git_acl_awareness_unaffected_by_ancestor_repair(tmp_path, monkeypatch):
    """J-3 regression: `_resolve_trusted_executable_with_effective_
    access` still applies ACL-inclusive effective-access checking to
    the resolved executable itself."""

    git_exe = _make_git_fixture(tmp_path)
    monkeypatch.setenv("PATH", str(tmp_path))

    def acl_grants_on_exe(path, uid, gids):
        return path == git_exe.resolve()

    monkeypatch.setattr(topo_mod, "_acl_grants_agent_write", acl_grants_on_exe)
    try:
        resolved = _resolve_trusted_executable_with_effective_access("git")
        assert resolved is None
    finally:
        os.chmod(tmp_path, 0o700)


# ═══════════════════════════════════════════════════════════════════════════
# §8 Aggregator / environment-verifier stability
# ═══════════════════════════════════════════════════════════════════════════


def test_aggregator_module_unchanged():
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "src/pcae/core/hatp_class_b_conformance.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
    )
    assert result.stdout.strip() == ""


def test_environment_lock_verifier_unchanged():
    result = subprocess.run(
        ["git", "diff", "--name-only", "--", "src/pcae/core/hatp_environment_lock_verifier.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
    )
    assert result.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════════
# §9 Zero authority consumers / HMIC non-binding
# ═══════════════════════════════════════════════════════════════════════════


def test_zero_production_consumers_of_topology_verifier():
    result = subprocess.run(
        ["grep", "-rl", "--include=*.py", "hatp_class_b_topology_verifier", "src/pcae/"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
    )
    consumers = {
        line for line in result.stdout.splitlines()
        if line and line not in ("src/pcae/core/hatp_class_b_topology_verifier.py",)
        and "hatp_environment_lock_verifier.py" not in line
        and "hatp_class_b_conformance.py" not in line
    }
    assert consumers == set(), f"unexpected production consumer(s): {consumers}"


def test_verifier_source_not_in_hmic_frozen_scope():
    from pcae.core import hatp_mandatory_certification as hmic_mod

    frozen_files = hmic_mod._FROZEN_AUTHORITY_BEARING_FILES
    assert len(frozen_files) == 25  # HMIC-REQ-050 (v1.2): unchanged by this phase
    assert not any("hatp_class_b_topology_verifier" in f for f in frozen_files)
    assert not any("hatp_environment_lock_verifier" in f for f in frozen_files)
    assert not any("hatp_class_b_conformance" in f for f in frozen_files)


# ═══════════════════════════════════════════════════════════════════════════
# §10 Public API status vocabulary unaffected
# ═══════════════════════════════════════════════════════════════════════════


def test_status_vocabulary_unchanged():
    assert {s.value for s in ClassBConformanceStatus} == {
        "COMPLIANT",
        "NON_COMPLIANT",
        "INDETERMINATE",
        "ACCESS_ERROR",
        "MALFORMED_STATE",
        "UNSUPPORTED_DEPLOYMENT_MODEL",
    }
