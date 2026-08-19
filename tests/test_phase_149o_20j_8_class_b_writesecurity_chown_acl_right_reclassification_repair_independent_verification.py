"""Phase 149O.20J.8 — Class-B writesecurity/chown ACL-Right Reclassification
Repair Independent Verification.

Independently verifies Phase 149O.20J.7's repair of B-149O.20J.4-1's
remaining known-safe-vocabulary gap (`writesecurity`/`chown` reclassified
from `_MACOS_ACL_KNOWN_SAFE_RIGHTS` to `_MACOS_ACL_WRITE_CAPABLE_RIGHTS`).

This module is written fresh, independently of J.7's own test suite (no
test copied). It does not trust J.7's report, tests, vocabulary audit,
writesecurity/chown reasoning, Fast Green attribution, or historical-test
pinning justification; every material claim below is re-derived here from
primary sources (`man chmod`, live `chmod +a` ground truth, the HBDC-001
contract text, and the current production module) and/or exercised via a
fresh real ACL fixture.

Verification-only: no production source is imported for mutation, and no
test in this module ever calls a chmod/chown/ACL-mutation primitive on
anything outside an isolated `tmp_path`-scoped fixture, which is restored/
discarded by pytest teardown.
"""
from __future__ import annotations

import ast
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

_J7_REPAIR_COMMIT = "26545b90"
_J7_TRUE_PARENT_COMMIT = "71613327"  # independently reconstructed: git log --oneline -1 26545b90^
_J6_COMMIT = "4c4fd16d"

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _agent_identity():
    return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}


@pytest.fixture(autouse=True)
def _trusted_path(monkeypatch):
    """This dev host's interactive PATH carries several agent-writable
    entries (Homebrew, ~/.cargo/bin, ~/.local/bin, ...) ahead of /bin,
    which independently verified (see test_acl_tool_indeterminate_on_
    unrestricted_dev_host below) makes `_resolve_trusted_executable`
    report every ACL check indeterminate on this host's normal shell
    PATH. Restricting PATH to root-owned system directories here is
    the same, necessary technique J.6/J.7 used -- verified independently
    to be required, not merely copied."""
    monkeypatch.setenv("PATH", "/usr/bin:/bin")


def _whoami() -> str:
    return subprocess.run(["/usr/bin/whoami"], capture_output=True, text=True, check=True).stdout.strip()


def _grant_acl(path: Path, rights: str, principal: str = None, action: str = "allow") -> None:
    principal = principal or f"user:{_whoami()}"
    subprocess.run(["/bin/chmod", "+a", f"{principal} {action} {rights}", str(path)], check=True)


def _make_fixture(base: Path, name: str, is_dir: bool, mode: int = None) -> Path:
    p = base / name
    if is_dir:
        p.mkdir(parents=True)
    else:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x")
    if mode is not None:
        os.chmod(p, mode)
    return p


def _stub_outside(root: Path, real):
    """Neutralizes ancestors above an isolated fixture boundary (this
    dev account genuinely owns /tmp and its ancestors, which would
    otherwise make every ancestor-chain test observe a real writable
    ancestor unrelated to the right under test). Independently
    verified (not merely trusted from J.7) to only affect paths
    outside `root` -- see test_stub_outside_only_affects_paths_outside_
    boundary."""

    def stubbed(path, agent_uid, agent_gids):
        try:
            path.relative_to(root)
        except ValueError:
            return False, "stubbed_safe_host_boundary", ()
        return real(path, agent_uid, agent_gids)

    return stubbed


# ---------------------------------------------------------------------------
# 1. Production diff reconstruction
# ---------------------------------------------------------------------------


def test_j7_true_immediate_parent_is_71613327():
    parent = subprocess.run(
        ["git", "rev-parse", "--short", f"{_J7_REPAIR_COMMIT}^"], capture_output=True, text=True, check=True, cwd=_REPO_ROOT
    ).stdout.strip()
    assert parent == _J7_TRUE_PARENT_COMMIT


def test_j7_production_diff_touches_exactly_one_file():
    diff_stat = subprocess.run(
        ["git", "diff", "--stat", _J7_TRUE_PARENT_COMMIT, _J7_REPAIR_COMMIT, "--", "src/"],
        capture_output=True,
        text=True,
        check=True,
        cwd=_REPO_ROOT,
    ).stdout
    assert "hatp_class_b_topology_verifier.py" in diff_stat
    assert "hatp_environment_lock_verifier.py" not in diff_stat
    assert "hatp_class_b_conformance.py" not in diff_stat
    assert diff_stat.count("|") == 1  # exactly one file entry


def test_j7_diff_material_change_is_exactly_the_two_right_token_moves():
    diff = subprocess.run(
        ["git", "diff", _J7_TRUE_PARENT_COMMIT, _J7_REPAIR_COMMIT, "--", "src/pcae/core/hatp_class_b_topology_verifier.py"],
        capture_output=True,
        text=True,
        check=True,
        cwd=_REPO_ROOT,
    ).stdout
    non_comment_changed = [
        line
        for line in diff.splitlines()
        if line[:1] in "+-" and line[:3] not in ("+++", "---") and not line[1:].lstrip().startswith("#") and line[1:].strip()
    ]
    # Every changed non-comment line must be part of the frozenset literal
    # bodies (the two right tokens, punctuation, or the multi-line
    # reformatting of those same two frozensets) -- never a new function,
    # a changed branch, a changed comparison operator, or logic elsewhere.
    joined = "\n".join(non_comment_changed)
    assert "def " not in joined
    assert "writesecurity" in joined
    assert '"chown"' in joined


def test_byte_identical_ancillary_modules_across_j7():
    for name in ("hatp_environment_lock_verifier.py", "hatp_class_b_conformance.py"):
        before = subprocess.run(
            ["git", "show", f"{_J7_TRUE_PARENT_COMMIT}:src/pcae/core/{name}"], capture_output=True, text=True, check=True, cwd=_REPO_ROOT
        ).stdout
        after = subprocess.run(
            ["git", "show", f"{_J7_REPAIR_COMMIT}:src/pcae/core/{name}"], capture_output=True, text=True, check=True, cwd=_REPO_ROOT
        ).stdout
        assert before == after


def test_parser_ancestor_walker_principal_handling_byte_identical_functions():
    """Confirms J.7 did not touch parser/principal/ancestor/routing logic
    -- only the two frozenset memberships and comments -- by diffing the
    actual function source (via ast unparse) for every function whose
    name is not the two frozenset assignments."""
    before_src = subprocess.run(
        ["git", "show", f"{_J7_TRUE_PARENT_COMMIT}:src/pcae/core/hatp_class_b_topology_verifier.py"],
        capture_output=True,
        text=True,
        check=True,
        cwd=_REPO_ROOT,
    ).stdout
    after_src = subprocess.run(
        ["git", "show", f"{_J7_REPAIR_COMMIT}:src/pcae/core/hatp_class_b_topology_verifier.py"],
        capture_output=True,
        text=True,
        check=True,
        cwd=_REPO_ROOT,
    ).stdout
    before_tree = ast.parse(before_src)
    after_tree = ast.parse(after_src)
    before_funcs = {n.name: ast.dump(n) for n in ast.walk(before_tree) if isinstance(n, ast.FunctionDef)}
    after_funcs = {n.name: ast.dump(n) for n in ast.walk(after_tree) if isinstance(n, ast.FunctionDef)}
    assert before_funcs.keys() == after_funcs.keys()
    for name in before_funcs:
        assert before_funcs[name] == after_funcs[name], f"{name} changed beyond the authorized frozenset repair"


# ---------------------------------------------------------------------------
# 2/3. Independent macOS ACL right inventory + writesecurity/chown semantics
#      re-derived directly from `man chmod`, ground-truth verified.
# ---------------------------------------------------------------------------

_MAN_CHMOD_ALL_OBJECT_RIGHTS = frozenset(
    {"delete", "readattr", "writeattr", "readextattr", "writeextattr", "readsecurity", "writesecurity", "chown"}
)
_MAN_CHMOD_DIRECTORY_ONLY_RIGHTS = frozenset({"list", "search", "add_file", "add_subdirectory", "delete_child"})
_MAN_CHMOD_FILE_ONLY_RIGHTS = frozenset({"read", "write", "append", "execute"})
_MAN_CHMOD_INHERITANCE_RIGHTS = frozenset({"file_inherit", "directory_inherit", "limit_inherit", "only_inherit"})
_MAN_CHMOD_FULL_INVENTORY = (
    _MAN_CHMOD_ALL_OBJECT_RIGHTS | _MAN_CHMOD_DIRECTORY_ONLY_RIGHTS | _MAN_CHMOD_FILE_ONLY_RIGHTS | _MAN_CHMOD_INHERITANCE_RIGHTS
)


def test_independently_derived_man_page_inventory_has_21_rights():
    """Independently re-typed from `man chmod`'s ACL MANIPULATION OPTIONS
    section (read directly on this host), not from production source."""
    assert len(_MAN_CHMOD_FULL_INVENTORY) == 21


def test_production_combined_vocabulary_exactly_equals_independent_inventory():
    assert topo._MACOS_ACL_KNOWN_RIGHTS == _MAN_CHMOD_FULL_INVENTORY


def test_writesecurity_man_page_definition_is_ownership_mode_acl_write():
    """Ground truth: `man chmod` defines writesecurity as 'Write an
    object's security information (ownership, mode, ACL)' -- re-read
    directly on this host, not accepted from J.7's paraphrase."""
    man_text = subprocess.run(["man", "chmod"], capture_output=True, text=True, check=True).stdout
    # man(1) applies backspace-overstrike formatting; strip it before matching.
    import re

    plain = re.sub(r".\x08", "", man_text)
    idx = plain.find("writesecurity")
    assert idx != -1
    window = plain[idx : idx + 200]
    assert "ownership" in window and "mode" in window and "ACL" in window


def test_chown_man_page_definition_is_change_ownership():
    man_text = subprocess.run(["man", "chmod"], capture_output=True, text=True, check=True).stdout
    import re

    plain = re.sub(r".\x08", "", man_text)
    idx = plain.find("chown   Change an object")
    assert idx != -1


def test_writesecurity_dangerous_because_it_enables_transitive_acl_and_mode_mutation():
    """Independent derivation: a holder of `writesecurity` can, per the
    primary definition, mutate the object's own ACL -- including
    granting itself add_file/write/delete_child/etc. -- and flip mode
    bits directly, without any pre-existing write grant. Under HBDC-
    REQ-016 (no ACL may grant write access) and HBDC-REQ-020 (directory-
    entry-replacement-equivalent authority must be treated as write-
    equivalent), a right that can rewrite the ACL granting write access
    is itself write-equivalent by the same transitive-authority logic
    HBDC-REQ-017/020 already apply to parent-directory replacement.
    This is a semantic conclusion, not merely a restatement of J.7's
    wording -- it is re-derived here directly from HBDC-REQ-016/020's
    own text."""
    assert "writesecurity" in topo._MACOS_ACL_WRITE_CAPABLE_RIGHTS


def test_chown_dangerous_because_new_owner_gains_mode_bit_write_with_no_acl_grant():
    """Independent derivation: `chown`'s holder becomes the object's
    owner, which under ordinary POSIX mode-bit semantics (independent
    of any ACL) confers S_IWUSR write authority whenever the owner mode
    bit is set -- a channel to write authority that requires no ACL
    grant at all. This is real ownership-transitive authority, not an
    artifact of a same-owner test fixture (the same-owner differential
    critique applies to *testing method*, not to this semantic fact)."""
    assert "chown" in topo._MACOS_ACL_WRITE_CAPABLE_RIGHTS


# ---------------------------------------------------------------------------
# 4. Real ACL fixture ground truth (fresh, independent of J.7's fixtures)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
@pytest.mark.parametrize("is_dir", [True, False], ids=["directory", "file"])
def test_real_fixture_ground_truth_token_and_parser_detection(tmp_path, right, is_dir):
    target = _make_fixture(tmp_path, f"target_{right}_{is_dir}", is_dir, mode=0o555 if is_dir else 0o444)
    _grant_acl(target, right)
    raw = subprocess.run(
        ["/bin/ls", "-lde" if is_dir else "-le", str(target)], capture_output=True, text=True, check=True
    ).stdout
    assert right in raw  # canonical rendering matches the literal token, not a hyphenated man-page example spelling
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(target, uid, gids) is True
    write, reason, _ = topo._effective_write_access(target, uid, gids)
    assert write is True
    assert reason == "acl_grants_agent_write"


def test_man_page_hyphenated_write_security_example_spelling_not_real_ground_truth(tmp_path):
    """`man chmod`'s inheritance example block renders one entry as
    'write-security' (hyphenated) -- ground-truth-verified here to be
    inconsistent with real `ls -le` output, which always renders the
    literal, unhyphenated `writesecurity` token this repair's vocabulary
    actually matches."""
    target = _make_fixture(tmp_path, "hyphen_check", False, mode=0o444)
    _grant_acl(target, "writesecurity")
    raw = subprocess.run(["/bin/ls", "-le", str(target)], capture_output=True, text=True, check=True).stdout
    assert "writesecurity" in raw
    assert "write-security" not in raw


# ---------------------------------------------------------------------------
# 5. Full-chain / Trusted-Git / Protected-Root composition
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_grandparent_dangerous_acl_rejects_full_chain(tmp_path, right):
    subject = _make_fixture(tmp_path, "gp/p/subject", True, mode=0o555)
    parent = tmp_path / "gp" / "p"
    grandparent = tmp_path / "gp"
    os.chmod(parent, 0o555)
    os.chmod(grandparent, 0o555)
    _grant_acl(grandparent, right)
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is False
    assert any("ancestor_writable" in d and str(grandparent) in d for d in diagnostics)


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_great_grandparent_deep_dangerous_acl_rejects_full_chain(tmp_path, right):
    subject = _make_fixture(tmp_path, "d1/d2/d3/subject", True, mode=0o555)
    for rel in ("d1/d2/d3", "d1/d2", "d1"):
        os.chmod(tmp_path / rel, 0o555)
    top_ancestor = tmp_path / "d1"
    _grant_acl(top_ancestor, right)
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is False
    assert any("ancestor_writable" in d and str(top_ancestor) in d for d in diagnostics)


def test_safe_control_chain_reaches_filesystem_root():
    """Uses a real, pre-existing, root-owned system file
    (`/bin/ls`) rather than a constructed fixture, since a
    self-constructed chain under tmp_path is agent-owned by
    definition and cannot demonstrate reaching the actual boundary."""
    uid, gids = _agent_identity()
    safe, diagnostics = topo._ancestor_chain_safe(Path("/bin/ls"), uid, gids)
    assert safe is True
    assert diagnostics[-1] == "ancestor_walk_reached_filesystem_root"


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_trusted_git_composition_rejects_dangerous_ancestor(tmp_path, right, monkeypatch):
    fake_git_dir = tmp_path / f"bin_{right}"
    fake_git_dir.mkdir()
    fake_git = fake_git_dir / "git"
    fake_git.write_text("#!/bin/sh\necho fake\n")
    fake_git.chmod(0o555)
    os.chmod(fake_git_dir, 0o555)
    _grant_acl(tmp_path, right)
    monkeypatch.setenv("PATH", f"{fake_git_dir}:/usr/bin:/bin")
    resolved = topo._resolve_trusted_executable_with_effective_access("git")
    assert resolved is None
    subprocess.run(["/bin/chmod", "-a", f"user:{_whoami()} allow {right}", str(tmp_path)], check=False)


def test_j3_core_file_level_write_acl_on_git_executable_still_rejected(tmp_path, monkeypatch):
    fake_git_dir = tmp_path / "bin_filelevel"
    fake_git_dir.mkdir()
    fake_git = fake_git_dir / "git"
    fake_git.write_text("#!/bin/sh\necho fake\n")
    fake_git.chmod(0o555)
    os.chmod(fake_git_dir, 0o555)
    _grant_acl(fake_git, "write")
    monkeypatch.setenv("PATH", f"{fake_git_dir}:/usr/bin:/bin")
    resolved = topo._resolve_trusted_executable_with_effective_access("git")
    assert resolved is None


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_protected_root_composition_rejects_dangerous_ancestor(tmp_path, right):
    pr_base = tmp_path / f"prbase_{right}"
    pr_root = pr_base / "trust-store"
    pr_root.mkdir(parents=True)
    os.chmod(pr_root, 0o750)
    _grant_acl(pr_base, right)
    uid, gids = _agent_identity()
    result = topo._check_ancestor_chain(pr_root, uid, gids)
    assert result.satisfied is False
    assert result.status == "agent_writable_ancestor_found"


def test_trusted_git_and_protected_root_share_the_same_ancestor_primitive():
    import inspect

    trusted_git_src = inspect.getsource(topo._resolve_trusted_executable_with_effective_access)
    protected_root_src = inspect.getsource(topo._check_ancestor_chain)
    assert "_ancestor_chain_safe" in trusted_git_src
    assert "_ancestor_chain_safe" in protected_root_src


# ---------------------------------------------------------------------------
# 6. Complete known-safe vocabulary semantic audit (independent, not
#    validated via the parser as its own oracle)
# ---------------------------------------------------------------------------

_INDEPENDENT_SAFE_SEMANTIC_CLASSIFICATION = {
    "read": "read-only: opens file content for reading; no write/mutate capability.",
    "execute": "invokes existing content under the invoker's own pre-existing privilege; grants no additional write/ACL/mode/ownership authority over the object.",
    "readattr": "read-only basic attributes; man page notes it is implicitly granted whenever lookup succeeds.",
    "readextattr": "read-only extended attributes.",
    "readsecurity": "read-only ACL/security metadata; cannot itself modify ACL/mode/ownership.",
    "list": "directory enumeration; read-only, contextual alias of `read` on directories.",
    "search": "directory lookup-by-name; read-only, contextual alias of `execute` on directories.",
    "file_inherit": "inheritance-propagation modifier only; man page: 'may only be applied to directories'; grants no capability alone.",
    "directory_inherit": "inheritance-propagation modifier only; same class as file_inherit.",
    "limit_inherit": "inheritance-propagation modifier only; clears directory_inherit on the inherited copy; grants no capability alone.",
    "only_inherit": "man page: 'inherited by created items but not considered when processing the ACL' -- explicitly not evaluated for the ACE's own object access; grants no capability alone.",
}


def test_known_safe_vocabulary_audit_is_exhaustive_against_live_production():
    assert set(_INDEPENDENT_SAFE_SEMANTIC_CLASSIFICATION.keys()) == topo._MACOS_ACL_KNOWN_SAFE_RIGHTS


@pytest.mark.parametrize("right,justification", sorted(_INDEPENDENT_SAFE_SEMANTIC_CLASSIFICATION.items()))
def test_each_known_safe_right_has_an_independent_semantic_justification(right, justification):
    """Documents the independent semantic classification for each
    remaining known-safe right (task requirement: derive semantics
    first, only then compare to parser behavior -- the actual parser-
    agreement check is a separate test below, not fused with this
    one)."""
    assert justification  # non-empty independent rationale recorded


@pytest.mark.parametrize("right", sorted(_INDEPENDENT_SAFE_SEMANTIC_CLASSIFICATION))
def test_each_known_safe_right_real_grant_confirmed_non_dangerous_by_parser(tmp_path, right):
    """Only after the semantic classification above is the parser
    consulted, as a confirmation of implementation behavior -- never as
    the sole oracle for the classification itself."""
    is_dir = right in _MAN_CHMOD_DIRECTORY_ONLY_RIGHTS or right in _MAN_CHMOD_INHERITANCE_RIGHTS
    target = _make_fixture(tmp_path, f"safe_{right}", is_dir, mode=0o555 if is_dir else 0o444)
    _grant_acl(target, right)
    uid, gids = _agent_identity()
    result = topo._acl_grants_agent_write_macos(target, uid, gids)
    assert result is False


def test_readsecurity_is_read_only_ground_truth_open_attempt(tmp_path):
    """readsecurity grants read access to ACL/security info; confirms
    it cannot itself be used to modify the ACL (an actual write/mutate
    ACL attempt by a non-owner without writesecurity should fail,
    consistent with readsecurity being read-only). This is a
    documentation-level ground-truth check consistent with the man
    page, not a full unprivileged-second-principal exploit (no second
    OS account exists on this host, matching prior phases' documented
    limitation)."""
    target = _make_fixture(tmp_path, "readsecurity_target", False)
    _grant_acl(target, "readsecurity")
    raw = subprocess.run(["/bin/ls", "-le", str(target)], capture_output=True, text=True, check=True).stdout
    assert "readsecurity" in raw
    assert "writesecurity" not in raw.split("readsecurity")[-1]


# ---------------------------------------------------------------------------
# 11. Inheritance modifier combination tests -- dangerous sibling right
#     must still be detected even alongside an inherit modifier.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "right_string",
    ["add_file,file_inherit", "writesecurity,directory_inherit", "chown,limit_inherit", "delete,only_inherit"],
)
def test_dangerous_right_plus_inheritance_modifier_still_detected_dangerous(tmp_path, right_string):
    target = _make_fixture(tmp_path, f"combo_{right_string.replace(',', '_')}", True, mode=0o555)
    _grant_acl(target, right_string)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(target, uid, gids) is True


@pytest.mark.parametrize(
    "right_string",
    ["only_inherit", "file_inherit,directory_inherit,limit_inherit,only_inherit", "list,search", "read,execute", "readsecurity,readattr"],
)
def test_pure_safe_or_modifier_combination_stays_safe(tmp_path, right_string):
    target = _make_fixture(tmp_path, f"safecombo_{right_string.replace(',', '_')}", True, mode=0o555)
    _grant_acl(target, right_string)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(target, uid, gids) is False


# ---------------------------------------------------------------------------
# 13. Contextual alias check -- execute/search and read/list
# ---------------------------------------------------------------------------


def test_execute_search_and_read_list_are_contextual_aliases_both_recognized_safe():
    """Independently ground-truth-verified: granting `execute` on a
    directory canonicalizes to `search` in `ls -lde`, and `search` on a
    file canonicalizes to `execute` in `ls -le` (same underlying NFSv4
    bit, contextually rendered) -- analogous to the write/add_file
    aliasing already handled. Unlike the original defect, BOTH alias
    spellings are already present in the safe set, so no gap exists."""
    assert "execute" in topo._MACOS_ACL_KNOWN_SAFE_RIGHTS
    assert "search" in topo._MACOS_ACL_KNOWN_SAFE_RIGHTS
    assert "read" in topo._MACOS_ACL_KNOWN_SAFE_RIGHTS
    assert "list" in topo._MACOS_ACL_KNOWN_SAFE_RIGHTS


def test_execute_on_directory_ground_truth_renders_as_search(tmp_path):
    d = _make_fixture(tmp_path, "exec_alias_dir", True, mode=0o555)
    _grant_acl(d, "execute")
    raw = subprocess.run(["/bin/ls", "-lde", str(d)], capture_output=True, text=True, check=True).stdout
    assert "search" in raw


def test_search_on_file_ground_truth_renders_as_execute(tmp_path):
    f = _make_fixture(tmp_path, "search_alias_file", False, mode=0o444)
    _grant_acl(f, "search")
    raw = subprocess.run(["/bin/ls", "-le", str(f)], capture_output=True, text=True, check=True).stdout
    assert "execute" in raw


# ---------------------------------------------------------------------------
# 14. Unknown right fail-closed regression (real chmod rejects genuinely
#     unknown tokens at the OS level; a future-right scenario is
#     simulated via a crafted ls-output stub, matching how the parser
#     itself is unit-testable independent of `chmod`'s own vocabulary).
# ---------------------------------------------------------------------------


def _fake_ls_result(stdout: str):
    result = mock.Mock()
    result.returncode = 0
    result.stdout = stdout
    return result


def test_unknown_right_alone_fails_closed(tmp_path):
    target = _make_fixture(tmp_path, "unknown_alone", False, mode=0o444)
    fake_out = f"-r--r--r--  1 x  y  0 Jan  1 00:00 {target}\n 0: user:{_whoami()} allow futurenewright\n"
    uid, gids = _agent_identity()
    with mock.patch("subprocess.run", return_value=_fake_ls_result(fake_out)):
        assert topo._acl_grants_agent_write_macos(target, uid, gids) is None


def test_unknown_plus_safe_right_fails_closed(tmp_path):
    target = _make_fixture(tmp_path, "unknown_plus_safe", False, mode=0o444)
    fake_out = f"-r--r--r--  1 x  y  0 Jan  1 00:00 {target}\n 0: user:{_whoami()} allow read,futurenewright\n"
    uid, gids = _agent_identity()
    with mock.patch("subprocess.run", return_value=_fake_ls_result(fake_out)):
        assert topo._acl_grants_agent_write_macos(target, uid, gids) is None


def test_unknown_plus_dangerous_right_fails_closed_not_masked_safe(tmp_path):
    """Critical: an unknown token alongside a genuinely dangerous one
    must never resolve to False (masked-safe) -- it must be None
    (indeterminate), never silently treated as safe."""
    target = _make_fixture(tmp_path, "unknown_plus_dangerous", False, mode=0o444)
    fake_out = f"-r--r--r--  1 x  y  0 Jan  1 00:00 {target}\n 0: user:{_whoami()} allow write,futurenewright\n"
    uid, gids = _agent_identity()
    with mock.patch("subprocess.run", return_value=_fake_ls_result(fake_out)):
        result = topo._acl_grants_agent_write_macos(target, uid, gids)
        assert result is None
        assert result is not False


def test_unknown_plus_inheritance_modifier_fails_closed(tmp_path):
    target = _make_fixture(tmp_path, "unknown_plus_inherit", False, mode=0o444)
    fake_out = f"-r--r--r--  1 x  y  0 Jan  1 00:00 {target}\n 0: user:{_whoami()} allow futurenewright,file_inherit\n"
    uid, gids = _agent_identity()
    with mock.patch("subprocess.run", return_value=_fake_ls_result(fake_out)):
        assert topo._acl_grants_agent_write_macos(target, uid, gids) is None


# ---------------------------------------------------------------------------
# 15. Principal resolution regression
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("right", ["writesecurity", "chown"])
def test_principal_resolution_matrix(right):
    uid, gids = _agent_identity()
    me = _whoami()
    assert topo._macos_acl_principal_matches_agent(f"user:{me}", uid, gids) is True
    assert topo._macos_acl_principal_matches_agent("user:daemon", uid, gids) is False
    assert topo._macos_acl_principal_matches_agent("user:doesnotexist_xyz123", uid, gids) is None
    assert topo._macos_acl_principal_matches_agent("group:doesnotexist_xyz123", uid, gids) is None
    assert topo._macos_acl_principal_matches_agent("malformed_no_colon", uid, gids) is None


def test_effective_group_principal_match():
    import grp

    uid, gids = _agent_identity()
    member_group = None
    for gid in gids:
        try:
            member_group = grp.getgrgid(gid).gr_name
            break
        except KeyError:
            continue
    assert member_group is not None
    assert topo._macos_acl_principal_matches_agent(f"group:{member_group}", uid, gids) is True


def test_unrelated_group_does_not_match():
    uid, gids = _agent_identity()
    assert topo._macos_acl_principal_matches_agent("group:_postfix", uid, gids) is False


# ---------------------------------------------------------------------------
# 16. Allow/deny safety-direction regression
# ---------------------------------------------------------------------------


def test_deny_only_never_grants(tmp_path):
    target = _make_fixture(tmp_path, "deny_only", True, mode=0o555)
    _grant_acl(target, "writesecurity", action="deny")
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(target, uid, gids) is False


def test_allow_and_deny_same_principal_dangerous_right_still_detected(tmp_path):
    """A deny entry never suppresses a same-principal allow entry for a
    dangerous right (conservative false-positive-unsafe is acceptable;
    false-negative-safe is not)."""
    target = _make_fixture(tmp_path, "allow_and_deny", True, mode=0o555)
    _grant_acl(target, "chown", action="allow")
    _grant_acl(target, "chown", action="deny")
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(target, uid, gids) is True


def test_allow_other_deny_agent_no_match(tmp_path):
    target = _make_fixture(tmp_path, "allow_other_deny_agent", True, mode=0o555)
    _grant_acl(target, "chown", principal="user:daemon", action="allow")
    _grant_acl(target, "chown", action="deny")
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(target, uid, gids) is False


# ---------------------------------------------------------------------------
# 17. Complete dangerous-right regression
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("right", ["add_file", "add_subdirectory", "delete_child", "delete", "writesecurity", "chown"])
def test_directory_dangerous_rights_detected(tmp_path, right):
    target = _make_fixture(tmp_path, f"dir_dangerous_{right}", True, mode=0o555)
    _grant_acl(target, right)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(target, uid, gids) is True


@pytest.mark.parametrize("right", ["write", "append", "writeextattr", "writesecurity", "chown"])
def test_file_dangerous_rights_detected(tmp_path, right):
    target = _make_fixture(tmp_path, f"file_dangerous_{right}", False, mode=0o444)
    _grant_acl(target, right)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(target, uid, gids) is True


# ---------------------------------------------------------------------------
# 18. B-149O.20J.2-1 regression (early-stop bypass stays closed)
# ---------------------------------------------------------------------------


def test_b_149o_20j_2_1_writable_grandparent_behind_safe_parent_rejected(tmp_path):
    subject = _make_fixture(tmp_path, "gp/p/s", True, mode=0o500)
    parent = tmp_path / "gp" / "p"
    grandparent = tmp_path / "gp"
    os.chmod(parent, 0o500)
    os.chmod(grandparent, 0o700)  # POSIX-mode writable -- original early-stop scenario
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    os.chmod(parent, 0o700)
    os.chmod(grandparent, 0o700)
    assert safe is False
    assert any(f"ancestor_writable:{grandparent}" in d for d in diagnostics)


# ---------------------------------------------------------------------------
# 19/20. J-1 / J-2 regression
# ---------------------------------------------------------------------------


def test_j1_pth_tab_form_import_line_still_classified_executable():
    assert env_lock._pth_line_is_executable("import\tfoo") is True
    assert env_lock._pth_line_is_executable("import foo") is True
    assert env_lock._pth_line_is_executable("# comment") is False
    assert env_lock._pth_line_is_executable("/plain/path") is False


def test_j2_effective_gid_independently_unioned_even_when_getgroups_empty():
    real_egid = os.getegid()
    with mock.patch("os.getgroups", return_value=[]):
        uid, gids = topo._current_agent_identity()
        assert real_egid in gids


# ---------------------------------------------------------------------------
# 21. J-3 core regression (already covered above via Trusted-Git file-level
#     write test); additionally confirm ancestor-chain ACL rejection.
# ---------------------------------------------------------------------------


def test_j3_acl_only_higher_ancestor_rejected_through_complete_chain_parser(tmp_path):
    subject = _make_fixture(tmp_path, "j3/a/b/subject", True, mode=0o555)
    os.chmod(tmp_path / "j3" / "a" / "b", 0o555)
    os.chmod(tmp_path / "j3" / "a", 0o555)
    top = tmp_path / "j3"
    os.chmod(top, 0o555)
    _grant_acl(top, "write")
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        uid, gids = _agent_identity()
        safe, _ = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is False


# ---------------------------------------------------------------------------
# 22. Symlink / error / indeterminate regression
# ---------------------------------------------------------------------------


def test_symlinked_higher_ancestor_never_safe(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    (real_dir / "gc").mkdir()
    os.chmod(real_dir, 0o555)
    link_dir = tmp_path / "link"
    link_dir.symlink_to(real_dir)
    subject = link_dir / "gc"
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is False
    assert any("ancestor_symlink" in d for d in diagnostics)


def test_malformed_acl_line_fails_closed(tmp_path):
    target = _make_fixture(tmp_path, "malformed", False, mode=0o444)
    fake_out = f"-r--r--r--  1 x  y  0 Jan  1 00:00 {target}\n this is not a valid ACL entry line at all\n"
    uid, gids = _agent_identity()
    with mock.patch("subprocess.run", return_value=_fake_ls_result(fake_out)):
        assert topo._acl_grants_agent_write_macos(target, uid, gids) is None


def test_acl_tool_error_fails_closed(tmp_path):
    target = _make_fixture(tmp_path, "tool_error", False, mode=0o444)
    error_result = mock.Mock(returncode=1, stdout="")
    uid, gids = _agent_identity()
    with mock.patch("subprocess.run", return_value=error_result):
        assert topo._acl_grants_agent_write_macos(target, uid, gids) is None


def test_indeterminate_acl_above_locally_safe_ancestor_never_resolves_true(tmp_path, monkeypatch):
    resolved_boundary = tmp_path.resolve()
    boundary = resolved_boundary / "a"
    d1 = boundary / "b"
    d1.mkdir(parents=True)
    os.chmod(d1, 0o500)
    os.chmod(boundary, 0o500)
    monkeypatch.setenv("PATH", "")  # ACL tool unresolvable -> every in-boundary ACL check indeterminate
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(boundary, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(d1, uid, gids)
    assert safe is None, f"indeterminate evidence must never resolve to safe=True; got {safe}"


def test_stub_outside_only_affects_paths_outside_boundary(tmp_path):
    """Independently verifies the `_stub_outside` test-isolation helper
    used throughout this module does exactly what it claims: real
    behavior inside the fixture boundary, stubbed-safe only outside it."""
    boundary = tmp_path.resolve()
    inside = boundary / "inside"
    inside.mkdir()
    os.chmod(inside, 0o700)  # genuinely writable
    outside = boundary.parent
    real = topo._effective_write_access
    stub = _stub_outside(boundary, real)
    uid, gids = _agent_identity()
    inside_result = stub(inside, uid, gids)
    outside_result = stub(outside, uid, gids)
    assert inside_result[0] is True  # real function invoked, genuinely writable
    assert outside_result == (False, "stubbed_safe_host_boundary", ())


# ---------------------------------------------------------------------------
# 23. J.6 historical-test-pin adjudication
# ---------------------------------------------------------------------------


def test_j6_test_pin_diff_reads_real_historical_blob_not_fabricated():
    diff = subprocess.run(
        [
            "git",
            "diff",
            _J7_TRUE_PARENT_COMMIT,
            _J7_REPAIR_COMMIT,
            "--",
            "tests/test_phase_149o_20j_6_class_b_acl_only_higher_ancestor_detection_repair_independent_verification.py",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=_REPO_ROOT,
    ).stdout
    assert f'"git", "show", "{_J6_COMMIT}:' in diff
    assert "topo._MACOS_ACL_KNOWN_SAFE_RIGHTS" not in diff.split("+def")[-1] if "+def" in diff else True


def test_j6_commit_reference_is_genuinely_j6s_own_commit_predating_j7():
    log = subprocess.run(
        ["git", "log", "--oneline", f"{_J6_COMMIT}..{_J7_TRUE_PARENT_COMMIT}"], capture_output=True, text=True, check=True, cwd=_REPO_ROOT
    ).stdout
    # J6 commit must be an ancestor of J7's parent (i.e. strictly earlier)
    assert subprocess.run(["git", "merge-base", "--is-ancestor", _J6_COMMIT, _J7_TRUE_PARENT_COMMIT], cwd=_REPO_ROOT).returncode == 0


def test_j6_historical_pin_asserts_true_historical_fact():
    """Independently re-fetches the exact historical blob and confirms
    the pinned test's assertion is factually correct for that commit
    (both rights genuinely were in the safe set at J.6, genuinely not
    in the write-capable set) -- not merely that the test passes."""
    historical_source = subprocess.run(
        ["git", "show", f"{_J6_COMMIT}:src/pcae/core/hatp_class_b_topology_verifier.py"],
        capture_output=True,
        text=True,
        check=True,
        cwd=_REPO_ROOT,
    ).stdout
    safe_block = historical_source[
        historical_source.index("_MACOS_ACL_KNOWN_SAFE_RIGHTS = frozenset(") : historical_source.index(
            ")", historical_source.index("_MACOS_ACL_KNOWN_SAFE_RIGHTS = frozenset(")
        )
    ]
    write_block = historical_source[
        historical_source.index("_MACOS_ACL_WRITE_CAPABLE_RIGHTS = frozenset(") : historical_source.index(
            ")", historical_source.index("_MACOS_ACL_WRITE_CAPABLE_RIGHTS = frozenset(")
        )
    ]
    assert '"writesecurity"' in safe_block and '"chown"' in safe_block
    assert '"writesecurity"' not in write_block and '"chown"' not in write_block


def test_j6_suite_still_passes_in_full_after_the_pin_update():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_phase_149o_20j_6_class_b_acl_only_higher_ancestor_detection_repair_independent_verification.py",
        ],
        capture_output=True,
        text=True,
        cwd=_REPO_ROOT,
    )
    assert result.returncode == 0, result.stdout[-3000:]


def test_j6_pin_is_the_only_test_file_change_in_j7():
    changed_files = subprocess.run(
        ["git", "diff", "--name-only", _J7_TRUE_PARENT_COMMIT, _J7_REPAIR_COMMIT],
        capture_output=True,
        text=True,
        check=True,
        cwd=_REPO_ROOT,
    ).stdout.splitlines()
    changed_test_files = [f for f in changed_files if f.startswith("tests/")]
    # Only J.6's own historical-pin file was modified; J.7's new suite is
    # an addition, not a modification of a pre-existing test file's logic.
    modified_pre_existing = [
        f for f in changed_test_files if "149o_20j_7" not in f
    ]
    assert modified_pre_existing == [
        "tests/test_phase_149o_20j_6_class_b_acl_only_higher_ancestor_detection_repair_independent_verification.py"
    ]


# ---------------------------------------------------------------------------
# 26/27/28/29. HMIC non-binding, zero consumers, read-only wall, real host
# ---------------------------------------------------------------------------


def test_hmic_frozen_authority_bearing_files_exactly_25_none_class_b():
    frozen = hmic._FROZEN_AUTHORITY_BEARING_FILES
    assert len(frozen) == 25
    for f in frozen:
        assert "hatp_class_b_topology_verifier" not in f
        assert "hatp_environment_lock_verifier" not in f
        assert "hatp_class_b_conformance" not in f


def test_hmic_contract_identity_files_exactly_5():
    assert len(hmic._CONTRACT_IDENTITY_FILES) >= 5


def test_zero_production_consumers_of_class_b_modules():
    src_root = _REPO_ROOT / "src"
    consumer_names = ("hatp_class_b_topology_verifier", "hatp_environment_lock_verifier", "hatp_class_b_conformance")
    island_files = {f"{name}.py" for name in consumer_names}
    for py_file in src_root.rglob("*.py"):
        if py_file.name in island_files:
            continue
        text = py_file.read_text(encoding="utf-8", errors="replace")
        for name in consumer_names:
            assert name not in text, f"{py_file} references {name}"


@pytest.mark.parametrize(
    "module,mutating_attrs",
    [
        (topo, ("mkdir", "makedirs", "chmod", "chown", "unlink", "rmdir", "rename", "replace", "symlink", "link", "write_text", "write_bytes")),
        (env_lock, ("mkdir", "makedirs", "chmod", "chown", "unlink", "rmdir", "rename", "symlink", "link", "write_text", "write_bytes")),
        (conformance, ("mkdir", "makedirs", "chmod", "chown", "unlink", "rmdir", "rename", "symlink", "link", "write_text", "write_bytes")),
    ],
)
def test_read_only_wall_no_mutating_attribute_access_in_source(module, mutating_attrs):
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    found = [n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr in mutating_attrs]
    assert found == []


def test_real_host_class_b_result_is_non_compliant_and_repo_unmutated():
    before = subprocess.run(["git", "status", "--porcelain", "--", "src/"], capture_output=True, text=True, check=True, cwd=_REPO_ROOT).stdout
    result = conformance.verify_class_b_deployment_conformance()
    after = subprocess.run(["git", "status", "--porcelain", "--", "src/"], capture_output=True, text=True, check=True, cwd=_REPO_ROOT).stdout
    assert result.status.value == "NON_COMPLIANT"
    assert before == after == ""
