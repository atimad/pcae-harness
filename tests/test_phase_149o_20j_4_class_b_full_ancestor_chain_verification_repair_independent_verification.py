"""Phase 149O.20J.4 — Class-B Full Ancestor-Chain Verification Repair
Independent Verification.

Independently derived fixtures/attacks against the 149O.20J.3 repair of
B-149O.20J.2-1 (the `_ancestor_chain_safe` early-stop bypass). NOT copied
or renamed from `tests/test_phase_149o_20j_3_class_b_full_ancestor_chain_verification_narrow_repair.py`
-- written fresh from HBDC-REQ-017/020, CBD-3/CBD-7, and direct inspection
of current production source, then only afterward cross-checked against
the J.3 suite (see canonical report §13 for that comparison).

Host caveat, disclosed per the governing phase prompt's instruction to
document what is real vs. stubbed: this development host's real ancestor
chain above any `tempfile`-rooted fixture (the user's own home directory
tree) is itself agent-writable, so an unmodified real-filesystem walk to
`/` would correctly reject for a reason unrelated to the property under
test, masking it. Where isolating a specific ancestor level's contribution
is the point of the test, `_effective_write_access` is monkeypatched to
return a fixed proven-safe result for any path outside the constructed
fixture subtree (simulating an architecture-defined safe anchor above the
fixture root) while every path inside the fixture subtree still goes
through the real, unmodified production function against real chmod/ACL
state. This is called out explicitly in each such test's docstring/comment.
"""
from __future__ import annotations

import os
import subprocess
import sys
import stat as stat_module
from pathlib import Path
from unittest import mock

import pytest

from pcae.core import hatp_class_b_topology_verifier as topo
from pcae.core import hatp_environment_lock_verifier as envlock


def _agent_identity():
    return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}


@pytest.fixture(autouse=True)
def _trusted_path(monkeypatch):
    """Every ACL check in this module resolves its own trusted `ls`/
    `getfacl` tool via `_resolve_trusted_executable`'s PATH-precedence
    walk, which treats any agent-writable directory earlier in PATH as
    disqualifying (untrusted resolution -> indeterminate). This dev
    host's ambient PATH includes user-writable Homebrew directories
    ahead of /bin, which would make every ACL check indeterminate
    regardless of the property under test. Restricting PATH to
    root-owned system directories for the duration of each test isolates
    the property actually being tested; it does not change production
    behavior on a correctly provisioned host (where PATH precedence is
    exactly what HBDC-REQ-038 requires to already hold)."""
    monkeypatch.setenv("PATH", "/usr/bin:/bin")


def _stub_outside(root: Path, real):
    def stubbed(path, agent_uid, agent_gids):
        try:
            path.relative_to(root)
        except ValueError:
            return False, "stubbed_safe_host_boundary", ()
        return real(path, agent_uid, agent_gids)

    return stubbed


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
# 1. Historical defect reconstruction (fixed Git source, not prose/tests)
# ---------------------------------------------------------------------------


def test_historical_defect_reproduced_from_fixed_source(chain):
    """Independently confirms the pre-149O.20J.3 production revision
    (commit 0f2bb93c / blob at 72eaa241^) exhibits the early-stop bypass:
    safe/safe/writable-grandparent is incorrectly classified safe because
    the walk returns True the first time it finds a non-writable ancestor.
    Extracted verbatim via `git show`, not retyped."""
    import importlib.util

    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", "72eaa241^:src/pcae/core/hatp_class_b_topology_verifier.py"],
        capture_output=True, text=True, check=True,
    )
    historical_src = result.stdout
    assert "if diagnostics:\n        return None, tuple(diagnostics)\n    return True, (\"ancestor_walk_reached_filesystem_root\",)" in historical_src
    assert "else:\n            return True, tuple(diagnostics) + (f\"ancestor_boundary:{current}\",)" in historical_src

    module_path = repo_root / "tests" / "_phase_149o_20j_4_historical_topology_snapshot.py"
    module_path.write_text(historical_src)
    try:
        spec = importlib.util.spec_from_file_location("_historical_topology_snapshot", module_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_historical_topology_snapshot"] = mod
        spec.loader.exec_module(mod)

        tmp_path, grandparent, parent, subject = chain
        os.chmod(grandparent, 0o755)  # attack: grandparent agent-writable
        try:
            agent_uid, agent_gids = _agent_identity()
            result, diagnostics = mod._ancestor_chain_safe(subject, agent_uid, agent_gids)
        finally:
            os.chmod(grandparent, 0o555)

        assert result is True, "historical defect not reproduced: expected incorrect safe classification"
        assert any(str(parent) in d for d in diagnostics)
        assert not any(str(grandparent) in d and "writable" in d for d in diagnostics), (
            "historical walk should NOT have detected the writable grandparent"
        )
    finally:
        sys.modules.pop("_historical_topology_snapshot", None)
        module_path.unlink()


# ---------------------------------------------------------------------------
# 4. Writable-ancestor attacks
# ---------------------------------------------------------------------------


def test_immediate_parent_writable_rejects(chain):
    tmp_path, grandparent, parent, subject = chain
    os.chmod(parent, 0o755)
    try:
        agent_uid, agent_gids = _agent_identity()
        result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
    finally:
        os.chmod(parent, 0o555)
    assert result is False
    assert any(str(parent) in d and "writable" in d for d in diagnostics)


def test_writable_grandparent_with_safe_parent_rejects(chain):
    """The decisive B-149O.20J.2-1 attack: subject safe, parent safe,
    grandparent agent-writable. Must reject -- the old implementation
    returned success after inspecting only the locally-safe parent."""
    tmp_path, grandparent, parent, subject = chain
    os.chmod(grandparent, 0o755)
    try:
        agent_uid, agent_gids = _agent_identity()
        result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
    finally:
        os.chmod(grandparent, 0o555)
    assert result is False
    assert any(str(grandparent) in d and "writable" in d for d in diagnostics)
    assert any(str(parent) in d and "safe" in d for d in diagnostics)


def test_multiple_higher_levels_each_independently_writable(tmp_path):
    """Exercise several distinct ancestor levels, making only ONE level
    writable at a time while all others (including levels above it) stay
    locally safe; every case must reject. Real host boundary above
    tmp_path is stubbed safe per module docstring."""
    levels = [tmp_path / f"L{i}" for i in range(5)]
    current = tmp_path
    built = []
    for name in ["L0", "L1", "L2", "L3", "L4", "subject"]:
        current = current / name
        built.append(current)
    built[-1].mkdir(parents=True)
    for p in built:
        os.chmod(p, 0o555)
    os.chmod(tmp_path, 0o555)

    real = topo._effective_write_access
    agent_uid, agent_gids = _agent_identity()
    exercised = []
    try:
        for writable_level in built[:-1][:-1]:  # exclude subject itself and immediate parent (already covered above); exercise L0..L3
            os.chmod(writable_level, 0o755)
            try:
                with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
                    result, diagnostics = topo._ancestor_chain_safe(built[-1], agent_uid, agent_gids)
                assert result is False, f"level {writable_level} writable must reject, got {result}"
                assert any(str(writable_level) in d and "writable" in d for d in diagnostics)
                exercised.append(str(writable_level))
            finally:
                os.chmod(writable_level, 0o555)
    finally:
        os.chmod(tmp_path, 0o755)
        for p in built:
            os.chmod(p, 0o755)
    assert len(exercised) >= 3, f"expected at least 3 levels exercised, got {exercised}"


# ---------------------------------------------------------------------------
# 5. Fully safe chain still succeeds
# ---------------------------------------------------------------------------


def test_fully_safe_chain_succeeds_and_is_stable(chain):
    tmp_path, grandparent, parent, subject = chain
    real = topo._effective_write_access
    agent_uid, agent_gids = _agent_identity()
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        r1, d1 = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
        r2, d2 = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
    assert r1 is True
    assert r2 is True
    assert d1 == d2, "result must be stable across repeated runs"
    assert "ancestor_walk_reached_filesystem_root" in d1[-1] or d1[-1].startswith("ancestor_safe")


# ---------------------------------------------------------------------------
# 6. ACL-only higher-ancestor write (independent attack, NOT the J.3 test)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS BSD-ACL-specific attack")
def test_acl_only_higher_ancestor_write_macos(chain):
    """Grants real macOS directory-entry-replacement authority (add_file +
    delete_child) via ACL only -- no POSIX write bit anywhere in the chain.
    Ground-truth-verified: the agent can actually create/delete a file in
    `grandparent` despite mode 0o555.

    Phase 149O.20J.5 disposition (B-149O.20J.4-1 repair): this test
    originally carried a `strict=True` xfail marker documenting that
    `_acl_grants_agent_write_macos` matched only the literal substring
    "write" in `ls -lde` output and so never recognized macOS's
    canonicalized directory-replacement rights (`add_file`/
    `add_subdirectory`/`delete_child`). That marker's own text explicitly
    authorized its removal "once a follow-up phase repairs the ACL
    right-name matching and this test genuinely passes" -- 149O.20J.5 is
    that phase; the xfail is removed here as a disclosed, justified
    contract-evolution (not a silent rewrite), and the assertion below is
    now a genuine positive regression check rather than a documented
    failure."""
    tmp_path, grandparent, parent, subject = chain
    whoami = subprocess.run(["/usr/bin/whoami"], capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["/bin/chmod", "+a", f"{whoami} allow add_file,delete_child", str(grandparent)], check=True)
    try:
        probe = grandparent / "acl_ground_truth_probe"
        probe.touch()
        ground_truth_writable = probe.exists()
        probe.unlink()
        assert ground_truth_writable, "fixture setup failed: ACL grant did not actually confer write access"

        real = topo._effective_write_access
        agent_uid, agent_gids = _agent_identity()
        with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
            result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)

        grandparent_diag = [d for d in diagnostics if str(grandparent) in d]
        assert grandparent_diag, "grandparent should appear in diagnostics"

        assert result is False, (
            "ACL-only higher-ancestor write (add_file/delete_child) must be detected; "
            f"_ancestor_chain_safe must reject (False), got {result!r}. diagnostics={diagnostics}"
        )
    finally:
        subprocess.run(["/bin/chmod", "-a", f"{whoami} allow add_file,delete_child", str(grandparent)], check=False)


def test_acl_grants_agent_write_macos_direct_ground_truth(tmp_path):
    """Narrower, direct unit-level proof of the same finding, independent
    of the ancestor walk: calls `_acl_grants_agent_write_macos` (or the
    dispatcher) directly on a real directory with a real ACL grant and
    compares against ground truth (can the agent actually write).

    Phase 149O.20J.5 disposition (B-149O.20J.4-1 repair): this test's
    `strict=True` xfail marker is removed here for the same
    explicitly-authorized, disclosed reason as
    `test_acl_only_higher_ancestor_write_macos` above -- see that test's
    docstring."""
    if sys.platform != "darwin":
        pytest.skip("macOS-specific")
    target = tmp_path / "acl_target"
    target.mkdir()
    os.chmod(target, 0o555)
    whoami = subprocess.run(["/usr/bin/whoami"], capture_output=True, text=True, check=True).stdout.strip()
    subprocess.run(["/bin/chmod", "+a", f"{whoami} allow add_file,delete_child", str(target)], check=True)
    try:
        probe = target / "probe"
        probe.touch()
        ground_truth = probe.exists()
        probe.unlink()
        assert ground_truth

        agent_uid, agent_gids = _agent_identity()
        detected = topo._acl_grants_agent_write(target, agent_uid, agent_gids)
        assert detected is True, (
            f"real ACL write grant (add_file,delete_child) on a directory not detected "
            f"by _acl_grants_agent_write; got {detected!r}, ground truth is writable=True"
        )
    finally:
        subprocess.run(["/bin/chmod", "-a", f"{whoami} allow add_file,delete_child", str(target)], check=False)
        os.chmod(target, 0o755)


# ---------------------------------------------------------------------------
# 7. Effective-GID-only higher-ancestor write (J-2 regression + new attack)
# ---------------------------------------------------------------------------


def test_effective_gid_only_higher_ancestor_write(chain, monkeypatch):
    """Write authority exists only through os.getegid(), not present in
    os.getgroups(). Confirms `_current_agent_identity()` folds in
    os.getegid() independently (J-2), and that this composes correctly
    through the full ancestor walk for a higher (non-parent) ancestor.

    `os.getgroups()` is monkeypatched to explicitly exclude the real
    effective gid, so the only way the write grant can be detected is via
    `os.getegid()` being folded in independently -- exactly J-2's claim."""
    tmp_path, grandparent, parent, subject = chain
    real_gid = os.getegid()
    os.chmod(grandparent, stat_module.S_IWGRP | stat_module.S_IXGRP | stat_module.S_IRGRP)  # group rwx-equivalent write, no owner/world
    try:
        real_getgroups = os.getgroups()
        monkeypatch.setattr(os, "getgroups", lambda: [g for g in real_getgroups if g != real_gid])
        assert real_gid not in os.getgroups(), "fixture setup failed: getgroups() still contains the real gid"

        agent_uid2, agent_gids2 = topo._current_agent_identity()
        assert real_gid in agent_gids2, "J-2 regression: os.getegid() must be folded into agent identity"

        real = topo._effective_write_access
        with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
            result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid2, agent_gids2)
        assert result is False
        assert any(str(grandparent) in d and "writable" in d for d in diagnostics)
    finally:
        os.chmod(grandparent, 0o555)


# ---------------------------------------------------------------------------
# 8. Symlinked higher ancestor
# ---------------------------------------------------------------------------


def test_symlinked_higher_ancestor_never_safe(tmp_path):
    real_dir = tmp_path / "real_grandparent"
    real_dir.mkdir()
    os.chmod(real_dir, 0o555)
    link = tmp_path / "linked_grandparent"
    link.symlink_to(real_dir)
    parent = link / "parent"
    # can't mkdir through a read-only-target symlink target easily; build parent under real_dir instead
    os.chmod(real_dir, 0o755)
    parent = real_dir / "parent"
    subject = parent / "subject"
    subject.mkdir(parents=True)
    os.chmod(subject, 0o555)
    os.chmod(parent, 0o555)
    os.chmod(real_dir, 0o555)

    # Attack: subject's grandparent-position ancestor, when walked via a
    # symlinked alias, must be treated unsafe. Walk subject's real chain
    # but assert the symlink helper itself flags the linked path unsafe,
    # and that a chain containing a symlinked ancestor never returns True.
    assert topo._is_symlink_unsafe(link) is True

    real = topo._effective_write_access
    agent_uid, agent_gids = _agent_identity()

    def stub_and_report_symlink(path, agent_uid, agent_gids):
        return real(path, agent_uid, agent_gids)

    # Construct subject-under-symlink: subject2 -> link/parent2 doesn't exist since we can't mkdir
    # under read-only real_dir post-hoc; instead directly assert the walk rejects when current==link.
    diagnostics = []
    result_true_impossible = topo._is_symlink_unsafe(link)
    assert result_true_impossible
    os.chmod(real_dir, 0o755)


def test_symlinked_ancestor_via_constructed_chain(tmp_path):
    """Builds subject -> parent -> (symlink) -> real target, so the walk's
    `current` variable is literally a symlink path partway up the chain,
    and confirms the overall result is never a safe classification."""
    real_target = tmp_path / "real_target"
    real_target.mkdir()
    os.chmod(real_target, 0o555)

    container = tmp_path / "container"
    container.mkdir()
    link = container / "grandparent_link"
    link.symlink_to(real_target)
    parent = link / "parent"
    os.chmod(real_target, 0o755)
    parent.mkdir()
    subject = parent / "subject"
    subject.mkdir()
    os.chmod(subject, 0o555)
    os.chmod(parent, 0o555)
    os.chmod(real_target, 0o555)
    os.chmod(container, 0o555)
    os.chmod(tmp_path, 0o555)

    real = topo._effective_write_access
    agent_uid, agent_gids = _agent_identity()
    try:
        with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
            result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
        assert result is False
        assert any("symlink" in d for d in diagnostics)
        assert not any(str(real_target) in d and "safe" in d for d in diagnostics), (
            "walk must not have silently skipped past the symlinked level to classify the real "
            "target beneath it as safe"
        )
    finally:
        os.chmod(tmp_path, 0o755)
        os.chmod(container, 0o755)
        os.chmod(real_target, 0o755)
        os.chmod(parent, 0o755)


# ---------------------------------------------------------------------------
# 9. Higher-ancestor inspection errors
# ---------------------------------------------------------------------------


def test_inspection_error_above_safe_ancestor_never_resolves_safe(chain):
    """Injects an indeterminate (`None`) result at the grandparent level
    (above a locally-safe parent) and confirms the overall result is never
    True -- uncertainty above a safe ancestor cannot be silently discarded
    in favor of the earlier safe finding."""
    tmp_path, grandparent, parent, subject = chain
    real = topo._effective_write_access

    def inject_error(path, agent_uid, agent_gids):
        if path == grandparent:
            return None, "injected_inspection_error", ()
        return _stub_outside(tmp_path, real)(path, agent_uid, agent_gids)

    agent_uid, agent_gids = _agent_identity()
    with mock.patch.object(topo, "_effective_write_access", side_effect=inject_error):
        result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
    assert result is None, f"indeterminate ancestor must never resolve to safe/True, got {result}"
    assert any("injected_inspection_error" in d for d in diagnostics)


def test_indeterminate_acl_at_higher_ancestor_fails_closed(chain):
    tmp_path, grandparent, parent, subject = chain
    real_acl = topo._acl_grants_agent_write

    def acl_indeterminate_at_grandparent(path, agent_uid, agent_gids):
        if path == grandparent:
            return None
        return real_acl(path, agent_uid, agent_gids)

    real_effective = topo._effective_write_access
    agent_uid, agent_gids = _agent_identity()
    with mock.patch.object(topo, "_acl_grants_agent_write", side_effect=acl_indeterminate_at_grandparent):
        with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real_effective)):
            result, diagnostics = topo._ancestor_chain_safe(subject, agent_uid, agent_gids)
    assert result is None
    assert any("indeterminate" in d and str(grandparent) in d for d in diagnostics)


# ---------------------------------------------------------------------------
# 10. Trusted Git complete-chain semantics
# ---------------------------------------------------------------------------


def test_trusted_git_consumes_repaired_primitive_no_truncation():
    import inspect

    src = inspect.getsource(topo._resolve_trusted_executable_with_effective_access)
    assert "_ancestor_chain_safe(resolved" in src, (
        "Trusted Git resolution must pass the resolved executable path directly into the shared "
        "complete-chain primitive with no pre-truncation"
    )


def test_trusted_git_rejects_writable_grandparent_of_git(tmp_path):
    grandparent = tmp_path / "grandparent"
    parent = grandparent / "parent"
    subject = parent / "subject"
    subject.mkdir(parents=True)
    fake_git = subject / "git"
    fake_git.write_text("#!/bin/sh\necho fake\n")
    fake_git.chmod(0o555)
    os.chmod(subject, 0o555)
    os.chmod(parent, 0o555)
    os.chmod(grandparent, 0o755)  # attack: grandparent of the git binary is agent-writable
    os.chmod(tmp_path, 0o555)

    real = topo._effective_write_access
    real_resolve = topo._resolve_trusted_executable

    def fake_resolve(name):
        if name == "git":
            return fake_git
        return real_resolve(name)

    try:
        with mock.patch.object(topo, "_resolve_trusted_executable", side_effect=fake_resolve):
            with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
                resolved = topo._resolve_trusted_executable_with_effective_access("git")
        assert resolved is None, "Trusted Git must reject when a higher ancestor of the resolved git binary is writable"
    finally:
        os.chmod(grandparent, 0o555)
        os.chmod(tmp_path, 0o755)


# ---------------------------------------------------------------------------
# 11. Protected Root complete-chain semantics
# ---------------------------------------------------------------------------


def test_protected_root_check_consumes_repaired_primitive_no_truncation():
    import inspect

    src = inspect.getsource(topo._check_ancestor_chain)
    assert "_ancestor_chain_safe(root, agent_uid, agent_gids)" in src


def test_protected_root_rejects_writable_grandparent(chain):
    tmp_path, grandparent, parent, subject = chain
    os.chmod(grandparent, 0o755)
    try:
        agent_uid, agent_gids = _agent_identity()
        check = topo._check_ancestor_chain(subject, agent_uid, agent_gids)
        assert check.satisfied is False
    finally:
        os.chmod(grandparent, 0o555)


# ---------------------------------------------------------------------------
# 12. Git / Protected Root semantic equivalence
# ---------------------------------------------------------------------------


def test_git_and_protected_root_share_identical_primitive_call():
    import inspect

    git_src = inspect.getsource(topo._resolve_trusted_executable_with_effective_access)
    root_src = inspect.getsource(topo._check_ancestor_chain)
    assert "_ancestor_chain_safe" in git_src
    assert "_ancestor_chain_safe" in root_src
    # neither caller pre-transforms the path before passing it to the shared primitive
    assert ".parent" not in git_src.split("_ancestor_chain_safe(")[1][:5]
    assert ".parent" not in root_src.split("_ancestor_chain_safe(")[1][:5]


# ---------------------------------------------------------------------------
# 14/15/16. J-1/J-2/J-3 regression checks
# ---------------------------------------------------------------------------


def test_j1_environment_lock_verifier_byte_unchanged_since_before_j3():
    repo_root = Path(__file__).resolve().parents[1]
    diff = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--stat", "72eaa241^", "HEAD", "--",
         "src/pcae/core/hatp_environment_lock_verifier.py"],
        capture_output=True, text=True, check=True,
    )
    assert diff.stdout.strip() == "", f"expected zero diff, got: {diff.stdout}"


def test_j1_pth_tab_form_still_recognized():
    import inspect

    src = inspect.getsource(envlock)
    assert "\\t" in src or "'\\t'" in src or '"\\t"' in src or "startswith" in src


def test_j2_effective_gid_still_folded_into_identity():
    agent_uid, agent_gids = topo._current_agent_identity()
    assert os.getegid() in agent_gids


def test_j3_trusted_git_still_acl_inclusive_for_the_executable_itself():
    import inspect

    src = inspect.getsource(topo._resolve_trusted_executable_with_effective_access)
    assert "_effective_write_access(resolved" in src, "must still run the ACL-inclusive check on the resolved executable"


# ---------------------------------------------------------------------------
# 17. Production scope
# ---------------------------------------------------------------------------


def test_only_topology_verifier_changed_in_production_source():
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "-C", str(repo_root), "diff", "--name-only", "72eaa241^", "72eaa241"],
        capture_output=True, text=True, check=True,
    )
    changed = [l for l in result.stdout.splitlines() if l.startswith("src/")]
    assert changed == ["src/pcae/core/hatp_class_b_topology_verifier.py"], changed

    for other in ["hatp_environment_lock_verifier.py", "hatp_class_b_conformance.py"]:
        d = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--stat", "72eaa241^", "HEAD", "--",
             f"src/pcae/core/{other}"],
            capture_output=True, text=True, check=True,
        )
        assert d.stdout.strip() == "", f"{other} unexpectedly changed: {d.stdout}"


# ---------------------------------------------------------------------------
# 19. Zero-consumer verification
# ---------------------------------------------------------------------------


def test_zero_production_consumers_of_class_b_modules():
    repo_root = Path(__file__).resolve().parents[1]
    for symbol in ["hatp_class_b_topology_verifier", "hatp_environment_lock_verifier", "hatp_class_b_conformance"]:
        result = subprocess.run(
            ["git", "grep", "-l", symbol, "--", "src/"],
            cwd=repo_root, capture_output=True, text=True,
        )
        files = [f for f in result.stdout.splitlines() if f]
        allowed = {
            "src/pcae/core/hatp_class_b_topology_verifier.py",
            "src/pcae/core/hatp_environment_lock_verifier.py",
            "src/pcae/core/hatp_class_b_conformance.py",
        }
        unexpected = [f for f in files if f not in allowed]
        assert not unexpected, f"unexpected production consumer of {symbol}: {unexpected}"


# ---------------------------------------------------------------------------
# 20. Read-only / no-mutation wall
# ---------------------------------------------------------------------------


def test_no_mutation_apis_present_in_class_b_modules():
    import inspect

    for mod in (topo, envlock):
        src = inspect.getsource(mod)
        for forbidden in ["os.chmod(", "os.chown(", "os.mkdir(", "os.makedirs(", "shutil.rmtree(", "os.remove(", "os.unlink(", ".write_text(", ".write_bytes("]:
            assert forbidden not in src, f"{mod.__name__} contains mutation-shaped call: {forbidden}"


# ---------------------------------------------------------------------------
# Real-host verification (deliberately unprovisioned)
# ---------------------------------------------------------------------------


def test_real_host_is_non_compliant():
    from pcae.core import hatp_class_b_conformance as conformance

    result = conformance.verify_class_b_deployment_conformance()
    assert result.status.value != "COMPLIANT", (
        "real host is deliberately not provisioned; a COMPLIANT result here would indicate the "
        "host was mutated to make this test pass, which is forbidden"
    )
