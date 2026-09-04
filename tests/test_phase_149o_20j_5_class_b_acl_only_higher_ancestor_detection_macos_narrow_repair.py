"""Phase 149O.20J.5 — Class-B macOS ACL-Only Higher-Ancestor Detection
Narrow Repair.

Repairs B-149O.20J.4-1: `_acl_grants_agent_write_macos` matched only the
literal substring "write" in `ls -lde` output. macOS canonicalizes
directory-replacement ACL rights to `add_file`/`add_subdirectory`/
`delete_child` (none of which contain "write"), and gated ACL-presence
detection on a `+` marker that a real host's near-universal
`com.apple.provenance` extended attribute silently replaces with `@`
-- so real ACL evidence was discarded before the substring search even
ran. Every fixture in this module uses real `chmod +a` ACL grants on a
real macOS host and ground-truth-verifies actual write access via a
real filesystem probe before trusting any assertion about the
repaired detector's classification of it.

Host caveat (same disclosed pattern as 149O.20J.3/149O.20J.4's own
suites): this development host's real ancestor chain above any
`tmp_path`-rooted fixture is itself agent-writable (the user's own home
tree), so an unmodified real-filesystem walk to `/` would reject for a
reason unrelated to the property under test. Where isolating a specific
ancestor level is the point of the test, `_effective_write_access` is
monkeypatched to return a fixed proven-safe result for any path outside
the constructed fixture subtree, while every path inside the fixture
subtree still goes through the real, unmodified production function
against real chmod/ACL state.
"""
from __future__ import annotations

import inspect
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from pcae.core import hatp_class_b_topology_verifier as topo

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS BSD-ACL-specific repair")

_PRE_REPAIR_COMMIT = "0b2fd134"  # HEAD immediately before this phase's repair


def _agent_identity():
    return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}


@pytest.fixture(autouse=True)
def _trusted_path(monkeypatch):
    """Restrict PATH to root-owned system directories for the duration of
    each test so `_resolve_trusted_executable("ls")` resolves for real
    instead of reporting indeterminate because of this dev host's
    user-writable Homebrew PATH entries (same pattern as 149O.20J.4)."""
    monkeypatch.setenv("PATH", "/usr/bin:/bin")


def _stub_outside(root: Path, real):
    def stubbed(path, agent_uid, agent_gids):
        try:
            path.relative_to(root)
        except ValueError:
            return False, "stubbed_safe_host_boundary", ()
        return real(path, agent_uid, agent_gids)

    return stubbed


def _whoami() -> str:
    return subprocess.run(["/usr/bin/whoami"], capture_output=True, text=True, check=True).stdout.strip()


def _grant_acl(path: Path, rights: str, principal: str = None) -> None:
    principal = principal or _whoami()
    subprocess.run(["/bin/chmod", "+a", f"{principal} allow {rights}", str(path)], check=True)


def _revoke_acl(path: Path, rights: str, principal: str = None) -> None:
    principal = principal or _whoami()
    subprocess.run(["/bin/chmod", "-a", f"{principal} allow {rights}", str(path)], check=False)


def _ground_truth_dir_writable(path: Path) -> bool:
    probe = path / f"ground_truth_probe_{os.getpid()}"
    try:
        probe.touch()
        exists = probe.exists()
    except OSError:
        return False
    finally:
        if probe.exists():
            probe.unlink()
    return exists


@pytest.fixture
def chain(tmp_path):
    grandparent = tmp_path / "grandparent"
    parent = grandparent / "parent"
    subject = parent / "subject"
    subject.mkdir(parents=True)
    os.chmod(subject, 0o555)
    os.chmod(parent, 0o555)
    os.chmod(grandparent, 0o555)
    os.chmod(tmp_path, 0o555)
    yield tmp_path, grandparent, parent, subject
    os.chmod(tmp_path, 0o755)
    os.chmod(grandparent, 0o755)
    os.chmod(parent, 0o755)


# ---------------------------------------------------------------------------
# 1. Historical (pre-repair) reproduction from fixed Git source
# ---------------------------------------------------------------------------


def test_historical_defect_reproduced_from_fixed_pre_repair_source(tmp_path):
    """Extracts the exact pre-149O.20J.5 `_acl_grants_agent_write_macos`
    via `git show` (not retyped) and proves it misclassifies a real,
    ground-truth-verified ACL-only directory grant."""
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{_PRE_REPAIR_COMMIT}:src/pcae/core/hatp_class_b_topology_verifier.py"],
        capture_output=True, text=True, check=True,
    )
    historical_src = result.stdout
    assert '"+" not in mode_line.split()[0]' in historical_src
    assert '"write" in entry or "allow write" in entry' in historical_src

    # Import the historical module fresh (mirrors 149O.20J.4's own
    # approach) so the exact pre-repair function body executes unmodified.
    import importlib.util

    module_path = repo_root / "tests" / "_phase_149o_20j_5_historical_topology_snapshot.py"
    module_path.write_text(historical_src)
    try:
        spec = importlib.util.spec_from_file_location("_historical_topology_snapshot_j5", module_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_historical_topology_snapshot_j5"] = mod
        spec.loader.exec_module(mod)

        target = tmp_path / "acl_target"
        target.mkdir()
        os.chmod(target, 0o555)
        _grant_acl(target, "add_file,delete_child")
        try:
            assert _ground_truth_dir_writable(target), "fixture setup failed: ACL grant did not actually confer write access"
            detected = mod._acl_grants_agent_write_macos(target)
            assert detected is not True, (
                "historical defect not reproduced: pre-repair function unexpectedly detected the grant "
                f"(got {detected!r}) -- reproduction fixture may be invalid"
            )
        finally:
            _revoke_acl(target, "add_file,delete_child")
    finally:
        sys.modules.pop("_historical_topology_snapshot_j5", None)
        module_path.unlink()


# ---------------------------------------------------------------------------
# 2. Direct primitive: canonical directory rights
# ---------------------------------------------------------------------------


def _ground_truth_for_right(target: Path, rights: str) -> bool:
    """Each directory ACL right authorizes a narrower ground-truth-provable
    action than a generic "touch a file" probe: `add_file` only permits
    creating files, `add_subdirectory` only permits creating
    subdirectories, `delete_child` only permits deleting a pre-existing
    child (not creating one), and `delete` grants the ability to delete
    the directory itself (not its children)."""
    if rights == "add_file":
        probe = target / "probe_file"
        try:
            probe.touch()
            ok = probe.exists()
        except OSError:
            return False
        # Cleanup uses POSIX mode, not the ACL right under test:
        # add_file alone does not also grant delete_child.
        if probe.exists():
            os.chmod(target, 0o755)
            probe.unlink()
            os.chmod(target, 0o555)
        return ok
    if rights == "add_subdirectory":
        probe = target / "probe_dir"
        try:
            probe.mkdir()
            ok = probe.exists()
        except OSError:
            return False
        if probe.exists():
            os.chmod(target, 0o755)
            probe.rmdir()
            os.chmod(target, 0o555)
        return ok
    if rights == "delete_child":
        # Child must pre-exist (created before the target was locked
        # down to 0o555); deletion authority comes solely from
        # delete_child on the parent, not from any right on the child.
        child = target / "preexisting_child"
        try:
            child.unlink()
            return True
        except OSError:
            return False
    if rights == "delete":
        # `delete` grants the ability to delete the object itself.
        # Ground-truthed by renaming it out from under itself via the
        # OS-level rename primitive, which macOS treats as delete+
        # recreate of the directory entry -- verified, then the
        # directory is restored to its expected name/mode for the
        # caller's own finally-block cleanup.
        try:
            target.rename(target.with_name(target.name + "_deleted_probe"))
        except OSError:
            return False
        target.with_name(target.name + "_deleted_probe").rename(target)
        os.chmod(target, 0o555)
        return True
    raise AssertionError(f"unhandled right in ground-truth helper: {rights!r}")


@pytest.mark.parametrize("rights", ["add_file", "add_subdirectory", "delete_child", "delete"])
def test_directory_acl_right_detected(tmp_path, rights):
    target = tmp_path / "d"
    target.mkdir()
    if rights == "delete_child":
        (target / "preexisting_child").touch()
    os.chmod(target, 0o555)
    _grant_acl(target, rights)
    try:
        assert _ground_truth_for_right(target, rights), f"fixture setup failed: {rights!r} grant did not confer ground-truth authority"
        agent_uid, agent_gids = _agent_identity()
        detected = topo._acl_grants_agent_write(target, agent_uid, agent_gids)
        assert detected is True, f"right {rights!r} not detected as write-capable; got {detected!r}"
    finally:
        _revoke_acl(target, rights)


def test_directory_acl_combined_canonicalized_rights_detected(tmp_path):
    """Exercises the exact combined output macOS presents after a single
    `chmod +a` granting all three primary rights at once (not three
    separate grants), matching real canonical output grammar."""
    target = tmp_path / "d"
    target.mkdir()
    os.chmod(target, 0o555)
    _grant_acl(target, "add_file,add_subdirectory,delete_child")
    try:
        assert _ground_truth_dir_writable(target)
        agent_uid, agent_gids = _agent_identity()
        assert topo._acl_grants_agent_write(target, agent_uid, agent_gids) is True
    finally:
        _revoke_acl(target, "add_file,add_subdirectory,delete_child")


def test_directory_posix_safe_control_no_acl(tmp_path):
    target = tmp_path / "d"
    target.mkdir()
    os.chmod(target, 0o555)
    assert not _ground_truth_dir_writable(target)
    agent_uid, agent_gids = _agent_identity()
    assert topo._acl_grants_agent_write(target, agent_uid, agent_gids) is False


# ---------------------------------------------------------------------------
# 3. File-level write rights (must not regress while fixing directories)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rights", ["write", "append", "writeextattr"])
def test_file_level_acl_right_detected(tmp_path, rights):
    target = tmp_path / "f"
    target.touch()
    os.chmod(target, 0o444)
    _grant_acl(target, rights)
    try:
        agent_uid, agent_gids = _agent_identity()
        detected = topo._acl_grants_agent_write(target, agent_uid, agent_gids)
        assert detected is True, f"file-level right {rights!r} not detected; got {detected!r}"
    finally:
        _revoke_acl(target, rights)


def test_file_level_irrelevant_rights_not_detected(tmp_path):
    target = tmp_path / "f"
    target.touch()
    os.chmod(target, 0o444)
    _grant_acl(target, "readattr,readextattr,readsecurity")
    try:
        agent_uid, agent_gids = _agent_identity()
        assert topo._acl_grants_agent_write(target, agent_uid, agent_gids) is False
    finally:
        _revoke_acl(target, "readattr,readextattr,readsecurity")


# ---------------------------------------------------------------------------
# 4. Principal matching
# ---------------------------------------------------------------------------


def test_unrelated_user_principal_not_detected(tmp_path):
    target = tmp_path / "f"
    target.touch()
    os.chmod(target, 0o444)
    _grant_acl(target, "write", principal="nobody")
    try:
        agent_uid, agent_gids = _agent_identity()
        assert topo._acl_grants_agent_write(target, agent_uid, agent_gids) is False
    finally:
        _revoke_acl(target, "write", principal="nobody")


def test_effective_group_principal_detected(tmp_path):
    """`everyone` resolves to gid 12, which macOS includes in every
    process's supplementary groups -- a real effective-group match, not
    a special case in the parser."""
    target = tmp_path / "f"
    target.touch()
    os.chmod(target, 0o444)
    _grant_acl(target, "write", principal="everyone")
    try:
        agent_uid, agent_gids = _agent_identity()
        assert 12 in agent_gids, "test assumption violated: everyone (gid 12) not in this process's groups"
        assert topo._acl_grants_agent_write(target, agent_uid, agent_gids) is True
    finally:
        _revoke_acl(target, "write", principal="everyone")


def test_deny_entry_not_treated_as_allow(tmp_path):
    target = tmp_path / "f"
    target.touch()
    os.chmod(target, 0o444)
    subprocess.run(["/bin/chmod", "+a", f"{_whoami()} deny write", str(target)], check=True)
    try:
        agent_uid, agent_gids = _agent_identity()
        assert topo._acl_grants_agent_write(target, agent_uid, agent_gids) is False
    finally:
        subprocess.run(["/bin/chmod", "-a", f"{_whoami()} deny write", str(target)], check=False)


def test_irrelevant_rights_only_entry_not_detected(tmp_path):
    target = tmp_path / "f"
    target.touch()
    os.chmod(target, 0o444)
    _grant_acl(target, "readattr")
    try:
        agent_uid, agent_gids = _agent_identity()
        assert topo._acl_grants_agent_write(target, agent_uid, agent_gids) is False
    finally:
        _revoke_acl(target, "readattr")


# ---------------------------------------------------------------------------
# 5. Malformed / unexpected / unavailable ACL state -- fail closed
# ---------------------------------------------------------------------------


def test_malformed_acl_output_fails_closed(tmp_path):
    target = tmp_path / "f"
    target.touch()

    fake_stdout = f"-rw-r--r--@ 1 x  wheel  0 Jan  1 00:00 {target}\n this is not a recognized ACL entry line\n"

    class _FakeResult:
        returncode = 0
        stdout = fake_stdout

    with mock.patch("subprocess.run", return_value=_FakeResult()):
        agent_uid, agent_gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(target, agent_uid, agent_gids)
    assert result is None, f"malformed ACL output must fail closed (None), got {result!r}"


def test_unexpected_acl_right_token_fails_closed(tmp_path):
    """A right token outside the derived known-rights vocabulary must
    never be silently classified as non-write -- it must fail closed."""
    target = tmp_path / "f"
    target.touch()

    fake_stdout = f"-rw-r--r--@ 1 x  wheel  0 Jan  1 00:00 {target}\n 0: user:{_whoami()} allow some_future_unknown_right\n"

    class _FakeResult:
        returncode = 0
        stdout = fake_stdout

    with mock.patch("subprocess.run", return_value=_FakeResult()):
        agent_uid, agent_gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(target, agent_uid, agent_gids)
    assert result is None, f"unexpected ACL right token must fail closed (None), got {result!r}"


def test_acl_inspection_tool_unavailable_fails_closed(tmp_path, monkeypatch):
    target = tmp_path / "f"
    target.touch()
    # Phase ...1.1R (configured-agent-identity threading repair):
    # `_acl_grants_agent_write_macos` now resolves its ACL-inspection
    # tool via `_resolve_trusted_executable_for_subject` (evaluated
    # against the passed-in agent subject), not the ambient-identity
    # `_resolve_trusted_executable` — see that function's docstring.
    monkeypatch.setattr(topo, "_resolve_trusted_executable_for_subject", lambda name, agent_uid, agent_gids: None)
    agent_uid, agent_gids = _agent_identity()
    result = topo._acl_grants_agent_write_macos(target, agent_uid, agent_gids)
    assert result is None


def test_acl_query_subprocess_error_fails_closed(tmp_path):
    target = tmp_path / "f"
    target.touch()
    with mock.patch("subprocess.run", side_effect=OSError("boom")):
        agent_uid, agent_gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(target, agent_uid, agent_gids)
    assert result is None


def test_unresolvable_principal_name_with_write_right_fails_closed(tmp_path):
    """A well-formed ACL entry whose principal cannot be resolved (e.g. an
    orphaned identity) must not be silently treated as non-matching when
    it carries a write-capable right."""
    target = tmp_path / "f"
    target.touch()
    fake_stdout = f"-rw-r--r--@ 1 x  wheel  0 Jan  1 00:00 {target}\n 0: user:definitely_not_a_real_user_xyz allow write\n"

    class _FakeResult:
        returncode = 0
        stdout = fake_stdout

    with mock.patch("subprocess.run", return_value=_FakeResult()):
        agent_uid, agent_gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(target, agent_uid, agent_gids)
    assert result is None, f"unresolvable write-capable principal must fail closed (None), got {result!r}"


# ---------------------------------------------------------------------------
# 6. Full ancestor-chain composition
# ---------------------------------------------------------------------------


def test_ancestor_chain_rejects_acl_only_grandparent(chain):
    tmp_path, grandparent, parent, subject = chain
    _grant_acl(grandparent, "add_file,delete_child")
    try:
        assert _ground_truth_dir_writable(grandparent)
        real = topo._effective_write_access
        agent_uid, agent_gids = _agent_identity()
        with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
            result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
        assert result is False, f"ACL-only grandparent must reject; got {result!r}, diagnostics={diagnostics}"
        assert any(str(grandparent) in d and "writable" in d for d in diagnostics)
    finally:
        _revoke_acl(grandparent, "add_file,delete_child")


def test_ancestor_chain_rejects_acl_only_great_grandparent(tmp_path):
    """Multiple-depth composition: the ACL-only grant sits two levels
    above the immediate parent, both of which are POSIX-safe."""
    great_grandparent = tmp_path / "ggp"
    grandparent = great_grandparent / "gp"
    parent = grandparent / "p"
    subject = parent / "subject"
    subject.mkdir(parents=True)
    for d in (subject, parent, grandparent, great_grandparent, tmp_path):
        os.chmod(d, 0o555)
    _grant_acl(great_grandparent, "add_file,delete_child")
    try:
        assert _ground_truth_dir_writable(great_grandparent)
        real = topo._effective_write_access
        agent_uid, agent_gids = _agent_identity()
        with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
            result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
        assert result is False, f"ACL-only great-grandparent must reject; got {result!r}"
        assert any(str(great_grandparent) in d and "writable" in d for d in diagnostics)
    finally:
        _revoke_acl(great_grandparent, "add_file,delete_child")
        os.chmod(great_grandparent, 0o755)
        os.chmod(grandparent, 0o755)
        os.chmod(parent, 0o755)


def test_ancestor_chain_safe_when_no_acl_anywhere(chain):
    tmp_path, grandparent, parent, subject = chain
    real = topo._effective_write_access
    agent_uid, agent_gids = _agent_identity()
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
    assert result is True
    assert "ancestor_walk_reached_filesystem_root" in diagnostics[-1] or diagnostics[-1].startswith("ancestor_safe")


# ---------------------------------------------------------------------------
# 7. Trusted Git composition
# ---------------------------------------------------------------------------


def test_trusted_git_rejects_acl_only_higher_ancestor(tmp_path):
    grandparent = tmp_path / "grandparent"
    parent = grandparent / "parent"
    subject = parent / "subject"
    subject.mkdir(parents=True)
    fake_git = subject / "git"
    fake_git.write_text("#!/bin/sh\necho fake\n")
    fake_git.chmod(0o555)
    os.chmod(subject, 0o555)
    os.chmod(parent, 0o555)
    os.chmod(grandparent, 0o555)
    os.chmod(tmp_path, 0o555)
    _grant_acl(grandparent, "add_file,delete_child")

    real = topo._effective_write_access
    real_resolve = topo._resolve_trusted_executable

    def fake_resolve(name):
        if name == "git":
            return fake_git
        return real_resolve(name)

    try:
        assert _ground_truth_dir_writable(grandparent)
        with mock.patch.object(topo, "_resolve_trusted_executable", side_effect=fake_resolve):
            with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
                resolved = topo._resolve_trusted_executable_with_effective_access("git")
        assert resolved is None, "Trusted Git must reject when a higher ancestor is ACL-only-writable"
    finally:
        _revoke_acl(grandparent, "add_file,delete_child")
        os.chmod(grandparent, 0o755)
        os.chmod(tmp_path, 0o755)


# ---------------------------------------------------------------------------
# 8. Protected Root composition
# ---------------------------------------------------------------------------


def test_protected_root_rejects_acl_only_higher_ancestor(chain):
    tmp_path, grandparent, parent, subject = chain
    _grant_acl(grandparent, "add_file,delete_child")
    try:
        assert _ground_truth_dir_writable(grandparent)
        real = topo._effective_write_access
        agent_uid, agent_gids = _agent_identity()
        with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
            check = topo._check_ancestor_chain(subject, agent_uid, agent_gids)
        assert check.satisfied is False
    finally:
        _revoke_acl(grandparent, "add_file,delete_child")


def test_git_and_protected_root_equivalent_on_acl_only_grant(tmp_path):
    """Both call sites reject the identical ACL-only-higher-ancestor
    attack via the one shared primitive -- no divergence."""
    grandparent = tmp_path / "grandparent"
    parent = grandparent / "parent"
    subject = parent / "subject"
    subject.mkdir(parents=True)
    os.chmod(subject, 0o555)
    os.chmod(parent, 0o555)
    os.chmod(grandparent, 0o555)
    os.chmod(tmp_path, 0o555)
    _grant_acl(grandparent, "add_file,delete_child")

    real = topo._effective_write_access
    try:
        assert _ground_truth_dir_writable(grandparent)
        agent_uid, agent_gids = _agent_identity()
        with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
            root_check = topo._check_ancestor_chain(subject, agent_uid, agent_gids)
            git_safe, _ = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
        assert root_check.satisfied is False
        assert git_safe is False
    finally:
        _revoke_acl(grandparent, "add_file,delete_child")
        os.chmod(grandparent, 0o755)
        os.chmod(tmp_path, 0o755)


# ---------------------------------------------------------------------------
# 9. Early-stop repair (149O.20J.3) regression
# ---------------------------------------------------------------------------


def test_early_stop_repair_writable_grandparent_behind_safe_parent_still_rejects(chain):
    tmp_path, grandparent, parent, subject = chain
    os.chmod(grandparent, 0o755)  # mode-bit writable, not ACL
    try:
        real = topo._effective_write_access
        agent_uid, agent_gids = _agent_identity()
        with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
            result, _ = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
        assert result is False
    finally:
        os.chmod(grandparent, 0o555)


def test_early_stop_repair_full_safe_chain_reaches_root(chain):
    tmp_path, grandparent, parent, subject = chain
    real = topo._effective_write_access
    agent_uid, agent_gids = _agent_identity()
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
    assert result is True
    assert "ancestor_walk_reached_filesystem_root" in diagnostics[-1] or diagnostics[-1].startswith("ancestor_safe")


# ---------------------------------------------------------------------------
# 10. J-1 / J-2 / J-3 regressions
# ---------------------------------------------------------------------------


def test_j1_environment_lock_verifier_byte_unchanged():
    repo_root = Path(__file__).resolve().parents[1]
    diff = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--stat", _PRE_REPAIR_COMMIT, "HEAD", "--",
         "src/pcae/core/hatp_environment_lock_verifier.py"],
        capture_output=True, text=True, check=True,
    )
    assert diff.stdout.strip() == "", f"expected zero diff, got: {diff.stdout}"


def test_j2_effective_gid_still_folded_into_identity():
    agent_uid, agent_gids = topo._current_agent_identity()
    assert os.getegid() in agent_gids


def test_j3_trusted_git_still_acl_inclusive_for_the_executable_itself():
    src = inspect.getsource(topo._resolve_trusted_executable_with_effective_access)
    assert "_effective_write_access(resolved" in src


def test_j3_core_file_level_acl_detection_still_works(tmp_path):
    """J-3's core defect (resolve_trusted_executable's delegation never
    consulted ACL at all) remains closed: a file-level ACL write grant on
    a would-be trusted executable is still detected via the same
    delegation path."""
    fake_git = tmp_path / "git"
    fake_git.write_text("#!/bin/sh\necho fake\n")
    fake_git.chmod(0o555)
    os.chmod(tmp_path, 0o555)
    _grant_acl(fake_git, "write")
    real_resolve = topo._resolve_trusted_executable

    def fake_resolve(name):
        if name == "git":
            return fake_git
        return real_resolve(name)

    try:
        with mock.patch.object(topo, "_resolve_trusted_executable", side_effect=fake_resolve):
            resolved = topo._resolve_trusted_executable_with_effective_access("git")
        assert resolved is None, "file-level ACL write grant on the executable itself must still be detected"
    finally:
        os.chmod(tmp_path, 0o755)
        os.chmod(fake_git, 0o755)
        _revoke_acl(fake_git, "write")


# ---------------------------------------------------------------------------
# 11. Symlink / error handling regression
# ---------------------------------------------------------------------------


def test_symlinked_higher_ancestor_still_never_safe(tmp_path):
    real_target = tmp_path / "real_target"
    parent = real_target / "parent"
    subject = parent / "subject"
    subject.mkdir(parents=True)
    symlinked_grandparent = tmp_path / "symlinked_grandparent"
    symlinked_grandparent.symlink_to(real_target)
    subject_via_symlink = symlinked_grandparent / "parent" / "subject"
    os.chmod(subject, 0o555)
    os.chmod(parent, 0o555)
    os.chmod(real_target, 0o555)
    os.chmod(tmp_path, 0o555)
    try:
        real = topo._effective_write_access
        agent_uid, agent_gids = _agent_identity()
        with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
            result, diagnostics = topo._ancestor_chain_safe(subject_via_symlink, agent_uid, agent_gids)
        assert result is False, f"symlinked ancestor must reject; got {result!r}, diagnostics={diagnostics}"
        assert any("symlink" in d for d in diagnostics)
    finally:
        os.chmod(tmp_path, 0o755)
        os.chmod(real_target, 0o755)
        os.chmod(parent, 0o755)


def test_acl_inspection_error_above_locally_safe_ancestor_fails_closed(chain):
    tmp_path, grandparent, parent, subject = chain
    real = topo._effective_write_access

    def error_at_grandparent(path, agent_uid, agent_gids):
        if path == grandparent:
            return None, "acl_inspection_unavailable", (str(path),)
        return _stub_outside(tmp_path, real)(path, agent_uid, agent_gids)

    agent_uid, agent_gids = _agent_identity()
    with mock.patch.object(topo, "_effective_write_access", side_effect=error_at_grandparent):
        result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
    assert result is None, "indeterminate ACL result above a locally-safe ancestor must never yield True"


# ---------------------------------------------------------------------------
# 12. Read-only wall / zero consumers / HMIC non-binding
# ---------------------------------------------------------------------------


def test_no_mutation_apis_present():
    src = inspect.getsource(topo)
    for forbidden in ["os.chmod(", "os.chown(", "os.mkdir(", "os.makedirs(", "shutil.rmtree(", "os.remove(", "os.unlink(", ".write_text(", ".write_bytes("]:
        assert forbidden not in src, f"module contains mutation-shaped call: {forbidden}"


def test_zero_production_consumers_of_class_b_modules():
    repo_root = Path(__file__).resolve().parents[1]
    for symbol in ["hatp_class_b_topology_verifier", "hatp_environment_lock_verifier", "hatp_class_b_conformance"]:
        result = subprocess.run(["git", "grep", "-l", symbol, "--", "src/"], cwd=repo_root, capture_output=True, text=True)
        files = [f for f in result.stdout.splitlines() if f]
        allowed = {
            "src/pcae/core/hatp_class_b_topology_verifier.py",
            "src/pcae/core/hatp_environment_lock_verifier.py",
            "src/pcae/core/hatp_class_b_conformance.py",
        }
        unexpected = [f for f in files if f not in allowed]
        assert not unexpected, f"unexpected production consumer of {symbol}: {unexpected}"


def test_hmic_frozen_file_set_unchanged():
    from pcae.core import hatp_mandatory_certification as cert

    assert len(cert._FROZEN_AUTHORITY_BEARING_FILES) == 25
    for mod in ("hatp_class_b_topology_verifier.py", "hatp_environment_lock_verifier.py", "hatp_class_b_conformance.py"):
        assert not any(mod in f for f in cert._FROZEN_AUTHORITY_BEARING_FILES)


def test_production_scope_limited_to_topology_verifier():
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--name-only", _PRE_REPAIR_COMMIT, "--", "src/"],
        capture_output=True, text=True, check=True,
    )
    changed = [l for l in result.stdout.splitlines() if l]
    assert changed == ["src/pcae/core/hatp_class_b_topology_verifier.py"], changed


# ---------------------------------------------------------------------------
# 13. Real-host verification (deliberately unprovisioned)
# ---------------------------------------------------------------------------


def test_real_host_is_non_compliant():
    from pcae.core import hatp_class_b_conformance as conformance

    result = conformance.verify_class_b_deployment_conformance()
    assert result.status.value != "COMPLIANT", (
        "real host is deliberately not provisioned; a COMPLIANT result here would indicate the "
        "host was mutated to make this test pass, which is forbidden"
    )
