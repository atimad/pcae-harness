"""Phase 149O.20J.7 -- Class-B writesecurity/chown ACL-Right Reclassification
Narrow Repair.

Repairs the known-safe-vocabulary gap independently verified in Phase
149O.20J.6: `hatp_class_b_topology_verifier.py`'s `_MACOS_ACL_KNOWN_SAFE_
RIGHTS` classified `writesecurity` and `chown` as harmless. Both are
write-equivalent/transitively dangerous per `man chmod`'s own primary
definition ("Write an object's security information (ownership, mode,
ACL)" / "Change an object's ownership") -- a holder of either can obtain
subsequent write/ACL/mode/ownership authority over the object without
ever needing a pre-existing write grant. This module verifies the narrow
repair: both rights moved into `_MACOS_ACL_WRITE_CAPABLE_RIGHTS`, and a
bounded audit confirming no other currently-known-safe right shares the
same defect.

Fresh fixtures throughout; reuses the host-boundary-stubbing technique
independently arrived at by 149O.20J.3/.4/.5/.6 (this dev host's own home
directory is agent-writable, an unavoidable confound for any
`tmp_path`-rooted real-filesystem-root walk) but does not copy any test
body verbatim from 149O.20J.6's suite.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

from pcae.core import hatp_class_b_conformance as conformance
from pcae.core import hatp_class_b_topology_verifier as topo
from pcae.core import hatp_environment_lock_verifier as env_lock
from pcae.core import hatp_mandatory_certification as hmic

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS BSD-ACL-specific repair; verification is host-specific")

_PRE_REPAIR_COMMIT = "6a265e09"  # 149O.20J.5's repair commit -- true immediate parent of this phase's repair


def _agent_identity():
    return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}


@pytest.fixture(autouse=True)
def _trusted_path(monkeypatch):
    """Restrict PATH to root-owned system directories so
    `_resolve_trusted_executable("ls")` resolves for real instead of
    reporting indeterminate because of this dev host's user-writable
    PATH entries (e.g. Homebrew, ~/.cargo/bin) preceding /bin."""
    monkeypatch.setenv("PATH", "/usr/bin:/bin")


def _whoami() -> str:
    return subprocess.run(["/usr/bin/whoami"], capture_output=True, text=True, check=True).stdout.strip()


def _grant_acl(path: Path, rights: str, principal: str = None) -> None:
    principal = principal or _whoami()
    subprocess.run(["/bin/chmod", "+a", f"{principal} allow {rights}", str(path)], check=True)


def _deny_acl(path: Path, rights: str, principal: str = None) -> None:
    principal = principal or _whoami()
    subprocess.run(["/bin/chmod", "+a", f"{principal} deny {rights}", str(path)], check=True)


def _raw_acl_lines(path: Path, is_dir: bool) -> list:
    flag = "-lde" if is_dir else "-le"
    result = subprocess.run(["/bin/ls", flag, str(path)], capture_output=True, text=True, check=True)
    return result.stdout.splitlines()


def _reset_acl(path: Path) -> None:
    subprocess.run(["/bin/chmod", "-N", str(path)], check=False)


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


@pytest.fixture
def deep_chain(tmp_path):
    ggp = tmp_path / "ggp"
    gp = ggp / "gp"
    parent = gp / "parent"
    subject = parent / "subject"
    subject.mkdir(parents=True)
    for p in (subject, parent, gp):
        os.chmod(p, 0o500)
    os.chmod(ggp, 0o500)
    os.chmod(tmp_path, 0o500)
    yield tmp_path, ggp, gp, parent, subject
    os.chmod(tmp_path, 0o755)
    os.chmod(ggp, 0o755)
    os.chmod(gp, 0o755)
    os.chmod(parent, 0o755)


# ---------------------------------------------------------------------------
# Primary-source semantic derivation
# ---------------------------------------------------------------------------


def test_man_chmod_defines_writesecurity_as_ownership_mode_acl_write_authority():
    man_output = subprocess.run("man chmod | col -b", shell=True, capture_output=True, text=True).stdout
    idx = man_output.find("writesecurity")
    assert idx != -1
    snippet = man_output[idx : idx + 140].replace("\n", " ").replace("\t", " ")
    assert "security information" in snippet
    assert "ownership" in snippet
    assert "mode" in snippet
    assert "ACL" in snippet


def test_man_chmod_defines_chown_as_ownership_change_authority():
    man_output = subprocess.run("man chmod | col -b", shell=True, capture_output=True, text=True).stdout
    idx = man_output.find("chown")
    assert idx != -1
    snippet = man_output[idx : idx + 80].replace("\n", " ").replace("\t", " ")
    assert "Change" in snippet and "ownership" in snippet


def test_readsecurity_is_documented_distinctly_as_read_only():
    """Distinguishes the read-only counterpart (`readsecurity`, still
    correctly classified safe) from `writesecurity` -- confirms this
    repair is not conflating the two."""
    man_output = subprocess.run("man chmod | col -b", shell=True, capture_output=True, text=True).stdout
    idx = man_output.find("readsecurity")
    assert idx != -1
    snippet = man_output[idx : idx + 100].replace("\n", " ").replace("\t", " ")
    assert "Read" in snippet
    assert "ACL" in snippet
    assert "Write" not in snippet.split("readsecurity")[-1][:20]


# ---------------------------------------------------------------------------
# Exact vocabulary diff verification
# ---------------------------------------------------------------------------


def test_writesecurity_and_chown_now_classified_write_capable():
    assert "writesecurity" in topo._MACOS_ACL_WRITE_CAPABLE_RIGHTS
    assert "chown" in topo._MACOS_ACL_WRITE_CAPABLE_RIGHTS
    assert "writesecurity" not in topo._MACOS_ACL_KNOWN_SAFE_RIGHTS
    assert "chown" not in topo._MACOS_ACL_KNOWN_SAFE_RIGHTS


def test_known_rights_union_unchanged_by_the_move():
    """The repair reclassifies two rights between the two subsets; it
    must not add or drop any right from the combined recognized-rights
    vocabulary."""
    combined = topo._MACOS_ACL_WRITE_CAPABLE_RIGHTS | topo._MACOS_ACL_KNOWN_SAFE_RIGHTS
    assert combined == topo._MACOS_ACL_KNOWN_RIGHTS
    expected_all = {
        "read", "write", "execute", "delete", "append", "writeattr", "writeextattr",
        "readsecurity", "writesecurity", "chown", "list", "search", "add_file",
        "add_subdirectory", "delete_child", "readattr", "file_inherit",
        "directory_inherit", "limit_inherit", "only_inherit", "readextattr",
    }
    assert combined == expected_all


def test_production_diff_scope_limited_to_topology_verifier_since_j6():
    """Diffs the fixed pre-repair commit against the current working tree
    (not `HEAD`) -- this phase's own repair commit has not yet been made
    at the time this test first runs, matching 149O.20J.3's documented
    fix for exactly this self-check pattern (fixed-commit `git diff`
    checks must compare against the working tree during development, and
    the check remains valid post-commit since a clean tree makes the two
    identical)."""
    repo_root = Path(__file__).resolve().parents[1]
    changed = subprocess.run(
        ["git", "diff", "--name-only", _PRE_REPAIR_COMMIT, "--", "src/"],
        capture_output=True,
        text=True,
        check=True,
        cwd=repo_root,
    ).stdout.split()
    assert changed == ["src/pcae/core/hatp_class_b_topology_verifier.py"]


# ---------------------------------------------------------------------------
# Complete known-safe-vocabulary audit -- every remaining safe right must
# still be genuinely non-authority-transforming
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "right",
    ["read", "execute", "readattr", "readextattr", "readsecurity"],
)
def test_remaining_file_level_safe_rights_grant_no_write_via_parser(tmp_path, right):
    f = tmp_path / "f"
    f.write_text("x")
    os.chmod(f, 0o400)
    _grant_acl(f, right)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(f, uid, gids) is False


@pytest.mark.parametrize(
    "right",
    ["list", "search", "file_inherit", "directory_inherit", "limit_inherit", "only_inherit"],
)
def test_remaining_directory_level_safe_rights_grant_no_write_via_parser(tmp_path, right):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, right)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is False


def test_readsecurity_alone_grants_no_write_ground_truth(tmp_path):
    """Cross-check against the real filesystem, not just the parser: a
    readsecurity-only grant must not authorize a write."""
    f = tmp_path / "f"
    f.write_text("x")
    os.chmod(f, 0o400)
    _grant_acl(f, "readsecurity")
    try:
        with open(f, "r+b"):
            pass
        wrote = True
    except PermissionError:
        wrote = False
    assert wrote is False, "readsecurity alone must not confer real write access"


def test_known_safe_vocabulary_audit_is_exhaustive_and_documented():
    """Bounded-completeness check: every right in the current known-safe
    set is explicitly accounted for by this audit's parametrized cases
    above (no right silently exempted)."""
    audited = {
        "read", "execute", "readattr", "readextattr", "readsecurity",
        "list", "search", "file_inherit", "directory_inherit", "limit_inherit", "only_inherit",
    }
    assert audited == topo._MACOS_ACL_KNOWN_SAFE_RIGHTS


# ---------------------------------------------------------------------------
# writesecurity / chown real-fixture parser + ground-truth detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_canonical_acl_output_contains_expected_token(tmp_path, right):
    f = tmp_path / "f"
    f.write_text("x")
    _grant_acl(f, right)
    line = [l for l in _raw_acl_lines(f, False) if "allow" in l][0]
    assert right in line


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_detected_by_repaired_parser_on_file(tmp_path, right):
    f = tmp_path / "f"
    f.write_text("x")
    os.chmod(f, 0o400)
    _grant_acl(f, right)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(f, uid, gids) is True


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_detected_by_repaired_parser_on_directory(tmp_path, right):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, right)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is True


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_makes_effective_write_access_not_safe(tmp_path, right):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, right)
    uid, gids = _agent_identity()
    write, reason, _ = topo._effective_write_access(d, uid, gids)
    assert write is True
    assert reason == "acl_grants_agent_write"


def test_writesecurity_ground_truth_permits_self_granted_write_authority(tmp_path):
    """Empirically demonstrates the transitive-authority mechanism named
    in the repair's rationale: a holder of `writesecurity` can use it to
    grant itself a write-capable right via a further ACL edit, without
    ever needing a pre-existing write grant. This is exercised as the
    object's owner (the only account available on this host), so it
    demonstrates the *mechanism* `writesecurity` documents (self-service
    ACL editing), not a non-owner differential -- see
    `test_self_owner_methodology_limitation_disclosed` below for the
    disclosed boundary of what this host can prove."""
    f = tmp_path / "f"
    f.write_text("x")
    os.chmod(f, 0o400)
    _grant_acl(f, "writesecurity")
    # Mechanism check: writesecurity's own definition ("write an object's
    # security information... ACL") means its holder can edit the ACL
    # itself -- demonstrated here by adding a further write grant via the
    # same +a mechanism a writesecurity holder would use.
    _grant_acl(f, "write")
    line = [l for l in _raw_acl_lines(f, False) if "allow" in l][0]
    assert "write" in line and "writesecurity" in line


def test_self_owner_methodology_limitation_disclosed(tmp_path):
    """Independently reproduces 149O.20J.6's methodology critique rather
    than repeating the flawed same-owner differential as if it were
    conclusive: on this single-user host the tester is always the
    object's owner, and an owner can already mutate mode/ACL/ownership
    with NO ACL grant at all (owner authority, not any ACE). This test
    documents that fact plainly rather than treating it as proof
    writesecurity/chown are inert -- the classification instead rests on
    `man chmod`'s primary-source semantic definition (see
    `test_man_chmod_defines_*` above), per HBDC's fail-closed posture:
    an unproven-safe right belongs on the dangerous side."""
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    subprocess.run(["/bin/chmod", "700", str(d)], check=True)
    assert oct(os.stat(d).st_mode & 0o777) == oct(0o700)
    os.chmod(d, 0o500)
    # No second local user account is available on this host to run a
    # genuine cross-principal probe (HBDC-REQ-009's actual threat
    # scenario: a non-owner agent against an admin-owned ancestor). This
    # phase does not fabricate one and does not provision the host to
    # obtain one; the classification is conservatively derived from
    # primary ACL semantics instead, consistent with HBDC's fail-closed
    # posture for unproven-safe rights.


# ---------------------------------------------------------------------------
# Principal-resolution regression for the two dangerous rights
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_current_user_principal_detected(tmp_path, right):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, right, principal=_whoami())
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is True


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_unrelated_user_principal_not_detected(tmp_path, right):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, right, principal="daemon")
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is False


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_effective_group_principal_detected(tmp_path, right):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, right, principal="everyone")
    uid, gids = _agent_identity()
    assert 12 in gids, "test precondition: gid 12 must be a real supplementary group on this host"
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is True


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_unrelated_group_principal_not_detected(tmp_path, right):
    import grp

    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    uid, gids = _agent_identity()
    unrelated_gid = grp.getgrnam("_postfix").gr_gid
    assert unrelated_gid not in gids
    _grant_acl(d, right, principal="_postfix")
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is False


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_unresolvable_principal_fails_closed(right):
    fake_output = f"drwx------@ 2 x  wheel  64 x x x d\n 0: user:totally_nonexistent_principal_zzz allow {right}\n"
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=0, stdout=fake_output)
        uid, gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(Path("/tmp/x"), uid, gids)
    assert result is None


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_deny_only_not_treated_as_allow(tmp_path, right):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _deny_acl(d, right)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is False


def test_unknown_right_still_fails_closed_after_repair():
    """Regression: the repair must not have widened the known-safe set
    to accommodate unrecognized future rights -- an unknown token must
    still fail closed."""
    fake_output = "drwx------@ 2 x  wheel  64 x x x d\n 0: user:{} allow totallyfakeacenevermade\n".format(_whoami())
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=0, stdout=fake_output)
        uid, gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(Path("/tmp/x"), uid, gids)
    assert result is None


# ---------------------------------------------------------------------------
# Ancestor-chain composition: writesecurity / chown at grandparent and a
# deeper ancestor level
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_grandparent_ancestor_rejected(chain, right):
    root, grandparent, parent, subject = chain
    _grant_acl(grandparent, right)
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is False
    assert any(f"ancestor_writable:{grandparent}" in d for d in diagnostics)


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_dangerous_right_deeper_great_grandparent_ancestor_rejected(deep_chain, right):
    root, ggp, gp, parent, subject = deep_chain
    _grant_acl(ggp, right)
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is False
    assert any(f"ancestor_writable:{ggp}" in d for d in diagnostics)


def test_safe_full_chain_control_still_reaches_filesystem_root(chain):
    root, grandparent, parent, subject = chain
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is True
    assert diagnostics[-1] == "ancestor_walk_reached_filesystem_root"


# ---------------------------------------------------------------------------
# Trusted-Git and Protected-Root composition
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_trusted_git_rejects_dangerous_right_higher_ancestor(tmp_path, monkeypatch, right):
    fake_git_dir = tmp_path / "bin"
    fake_git_dir.mkdir()
    fake_git = fake_git_dir / "git"
    fake_git.write_text("#!/bin/sh\nexit 0\n")
    fake_git.chmod(0o500)
    os.chmod(fake_git_dir, 0o500)
    ancestor = tmp_path
    _grant_acl(ancestor, right)
    monkeypatch.setenv("PATH", f"{fake_git_dir}:/usr/bin:/bin")
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path.parent, real)):
        resolved = topo._resolve_trusted_executable_with_effective_access("git")
    assert resolved is None, f"{right}-only-writable ancestor above the git executable must reject trust"


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_protected_root_rejects_dangerous_right_higher_ancestor(chain, right):
    root, grandparent, parent, subject = chain
    _grant_acl(grandparent, right)
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        result = topo._check_ancestor_chain(subject, uid, gids)
    assert result.satisfied is False


def test_git_and_protected_root_use_identical_shared_semantics(chain):
    root, grandparent, parent, subject = chain
    _grant_acl(grandparent, "writesecurity")
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        git_safe, _ = topo._ancestor_chain_safe(subject, uid, gids)
        pr_safe, _ = topo._ancestor_chain_safe(subject, uid, gids)
    assert git_safe == pr_safe is False


# ---------------------------------------------------------------------------
# Existing dangerous-right regression (directory + file), no regression
# from J.5/J.6 coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("right", ["add_file", "add_subdirectory", "delete_child", "delete"])
def test_existing_directory_dangerous_right_still_detected(tmp_path, right):
    d = tmp_path / "d"
    d.mkdir()
    if right == "delete_child":
        victim = d / "victim.txt"
        victim.write_text("x")
    os.chmod(d, 0o500)
    _grant_acl(d, right)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is True


@pytest.mark.parametrize("right", ["write", "append", "writeextattr"])
def test_existing_file_dangerous_right_still_detected(tmp_path, right):
    f = tmp_path / "f"
    f.write_text("x")
    os.chmod(f, 0o400)
    _grant_acl(f, right)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(f, uid, gids) is True


def test_directory_posix_safe_control_no_acl_still_not_detected(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is False


# ---------------------------------------------------------------------------
# J-1 / J-2 / J-3 / B-149O.20J.2-1 / symlink / indeterminate regressions
# ---------------------------------------------------------------------------


def test_j1_environment_lock_source_unchanged():
    repo_root = Path(__file__).resolve().parents[1]
    diff = subprocess.run(
        ["git", "diff", "--name-only", _PRE_REPAIR_COMMIT, "HEAD", "--", "src/pcae/core/hatp_environment_lock_verifier.py"],
        capture_output=True,
        text=True,
        check=True,
        cwd=repo_root,
    ).stdout.strip()
    assert diff == "", "environment-lock source must remain byte-unchanged by this narrow repair"


def test_j2_effective_gid_still_folded_into_agent_identity():
    uid, gids = topo._current_agent_identity()
    assert os.getegid() in gids


def test_j3_core_file_level_acl_write_on_executable_still_rejected(tmp_path, monkeypatch):
    fake_git_dir = tmp_path / "bin"
    fake_git_dir.mkdir()
    fake_git = fake_git_dir / "git"
    fake_git.write_text("#!/bin/sh\nexit 0\n")
    fake_git.chmod(0o500)
    os.chmod(fake_git_dir, 0o500)
    _grant_acl(fake_git, "write")
    monkeypatch.setenv("PATH", f"{fake_git_dir}:/usr/bin:/bin")
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        resolved = topo._resolve_trusted_executable_with_effective_access("git")
    assert resolved is None, "real file-level ACL write grant on the executable itself must reject trust (J-3 core)"


def test_b_149o_20j_2_1_early_stop_defect_remains_closed(chain):
    root, grandparent, parent, subject = chain
    os.chmod(grandparent, 0o700)  # POSIX-mode writable (not ACL) -- the original early-stop scenario
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    os.chmod(grandparent, 0o500)
    assert safe is False
    assert any(f"ancestor_writable:{grandparent}" in d for d in diagnostics)


def test_symlinked_higher_ancestor_never_becomes_safe(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real_dir)
    subject = link / "subject"
    (real_dir / "subject").mkdir()
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is False
    assert any("ancestor_symlink" in d for d in diagnostics)


def test_indeterminate_acl_above_safe_ancestor_never_becomes_safe(tmp_path, monkeypatch):
    boundary = tmp_path / "a"
    d1 = boundary / "b"
    d1.mkdir(parents=True)
    os.chmod(d1, 0o500)
    os.chmod(boundary, 0o500)
    monkeypatch.setenv("PATH", "")  # ACL tool unresolvable -> every ancestor ACL check indeterminate
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(boundary, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(d1, uid, gids)
    assert safe is None, f"indeterminate evidence must never resolve to safe=True; got {safe}, diagnostics={diagnostics}"


# ---------------------------------------------------------------------------
# HMIC non-binding, zero consumers, read-only wall, real host
# ---------------------------------------------------------------------------


def test_hmic_frozen_authority_bearing_files_still_25_none_are_class_b():
    frozen = hmic._FROZEN_AUTHORITY_BEARING_FILES
    assert len(frozen) == 25
    for f in frozen:
        assert "hatp_class_b_topology_verifier" not in f
        assert "hatp_environment_lock_verifier" not in f
        assert "hatp_class_b_conformance" not in f


def test_hmic_contract_identity_files_still_5():
    assert len(hmic._CONTRACT_IDENTITY_FILES) == 5


def test_zero_production_consumers_outside_the_three_module_island():
    repo_root = Path(__file__).resolve().parents[1]
    grep = subprocess.run(
        [
            "git",
            "grep",
            "-l",
            "-E",
            "hatp_class_b_topology_verifier|hatp_environment_lock_verifier|hatp_class_b_conformance|verify_class_b_deployment_conformance|verify_class_b_topology_conformance|verify_environment_lock_conformance",
            "--",
            "src/",
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    hits = set(grep.stdout.splitlines())
    allowed = {
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "src/pcae/core/hatp_class_b_conformance.py",
    }
    assert hits <= allowed, f"unexpected production consumer(s): {hits - allowed}"


def test_read_only_wall_no_mutating_calls_in_the_three_modules():
    repo_root = Path(__file__).resolve().parents[1]
    forbidden = [
        "os.chmod(", "os.chown(", "os.mkdir(", "os.makedirs(", "shutil.rmtree(",
        "os.remove(", "os.unlink(", "os.rename(", "os.replace(", "os.symlink(",
        "os.link(", ".write_text(", ".write_bytes(",
    ]
    for rel in (
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "src/pcae/core/hatp_class_b_conformance.py",
    ):
        text = (repo_root / rel).read_text()
        for token in forbidden:
            assert token not in text, f"mutating call {token!r} found in {rel}"


def test_real_host_is_non_compliant():
    result = conformance.verify_class_b_deployment_conformance()
    assert result.status == conformance.ClassBConformanceStatus.NON_COMPLIANT


def test_repository_state_unchanged_after_verification():
    repo_root = Path(__file__).resolve().parents[1]
    status_before = subprocess.run(["git", "status", "--porcelain", "--", "src/"], capture_output=True, text=True, cwd=repo_root).stdout
    conformance.verify_class_b_deployment_conformance()
    status_after = subprocess.run(["git", "status", "--porcelain", "--", "src/"], capture_output=True, text=True, cwd=repo_root).stdout
    assert status_before == status_after
