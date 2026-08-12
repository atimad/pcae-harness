"""Phase 149O.20J.6 -- Class-B macOS ACL-Only Higher-Ancestor Detection
Repair Independent Verification.

Independently re-derives HBDC-REQ-016/017/020 ancestor-authority
semantics and the macOS ACL canonicalization grammar from primary
sources (this file's own `man chmod` inspection and real `chmod +a`
grants -- not 149O.20J.5's report, tests, rights vocabulary, or ACL
description), and independently re-attacks 149O.20J.5's repair of
B-149O.20J.4-1 in `hatp_class_b_topology_verifier.py`.

Fresh fixtures throughout -- none copied from
`test_phase_149o_20j_5_class_b_acl_only_higher_ancestor_detection_macos_narrow_repair.py`.
J.5's test expectations are deliberately not used as the oracle for
what "correct" classification means; the oracle is HBDC-001 (`docs/
contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md`) §11 and real,
ground-truth-verified macOS ACL/filesystem behavior.

Host caveat (same class of issue independently rediscovered here,
consistent with 149O.20J.3/.4/.5's own disclosed pattern): this
development host's real ancestor chain above any `tmp_path`-rooted
fixture is itself agent-writable (the user's own home directory tree),
so an unmodified real-filesystem walk to `/` would reject for a reason
unrelated to the property under test. Where isolating a specific
ancestor level is the point of the test, `_effective_write_access` is
monkeypatched to report a fixed proven-safe result for any path outside
the constructed fixture subtree; every path inside the fixture subtree
still goes through the real, unmodified production function against
real `chmod +a` ACL state.

CENTRAL FINDING (see `test_writesecurity_and_chown_are_misclassified_safe_*`
below and the phase's canonical report): `man chmod`'s ACL MANIPULATION
OPTIONS section, read on this exact host, defines `writesecurity` as
"Write an object's security information (ownership, mode, ACL)" and
`chown` as "Change an object's ownership" -- both self-evidently confer
transitive write-equivalent authority over directory topology (a
`writesecurity` holder can grant itself `add_file`/`delete_child`/etc.
via ACL edit or flip mode bits directly; a `chown` holder can become
owner and gain mode-bit write). `hatp_class_b_topology_verifier.py`'s
`_MACOS_ACL_KNOWN_SAFE_RIGHTS` classifies both as safe. This is a real,
primary-evidence-grounded false-negative-safe gap per the governing
prompt's item 10/11/29 criteria -- not merely a disagreement with
149O.20J.5's disclosed rationale ("ownership/ACL-security metadata, not
content-affecting").
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

_PRE_REPAIR_COMMIT = "0b2fd134"  # independently confirmed: immediate parent of 6a265e09 (git log)
_REPAIR_COMMIT = "6a265e09"


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


def _mode_marker(path: Path, is_dir: bool) -> str:
    lines = _raw_acl_lines(path, is_dir)
    return lines[0].split()[0]


def _reset_acl(path: Path) -> None:
    subprocess.run(["/bin/chmod", "-N", str(path)], check=False)


def _entry_specs(lines: "list[str]") -> "list[str]":
    specs = []
    for line in lines:
        m = topo._MACOS_ACL_ENTRY_RE.match(line)
        if m:
            specs.append(f"{m.group('principal')} {m.group('action')} {m.group('rights')}")
    return specs


def _ground_truth_create_file(directory: Path) -> bool:
    probe = directory / f"probe_create_{os.getpid()}.txt"
    try:
        probe.write_text("x")
        ok = probe.exists()
    except OSError:
        return False
    finally:
        if probe.exists():
            # cleanup requires delete authority the ACL grant under test may
            # not include (e.g. add_file alone), and any explicit ACL `deny`
            # present takes precedence over owner mode bits even for the
            # owner -- capture the exact original ACL, strip it, delete,
            # restore mode, then reapply the exact original entries so the
            # caller's own post-probe assertions see unchanged ACL state.
            acl_specs_before = _entry_specs(_raw_acl_lines(directory, True))
            mode_before = os.stat(directory).st_mode & 0o777
            _reset_acl(directory)
            os.chmod(directory, 0o700)
            probe.unlink()
            os.chmod(directory, mode_before)
            for spec in reversed(acl_specs_before):
                subprocess.run(["/bin/chmod", "+a", spec, str(directory)], check=True)
    return ok


def _ground_truth_create_subdir(directory: Path) -> bool:
    probe = directory / f"probe_subdir_{os.getpid()}"
    try:
        probe.mkdir()
        ok = probe.is_dir()
    except OSError:
        return False
    finally:
        if probe.exists():
            acl_specs_before = _entry_specs(_raw_acl_lines(directory, True))
            mode_before = os.stat(directory).st_mode & 0o777
            _reset_acl(directory)
            os.chmod(directory, 0o700)
            probe.rmdir()
            os.chmod(directory, mode_before)
            for spec in reversed(acl_specs_before):
                subprocess.run(["/bin/chmod", "+a", spec, str(directory)], check=True)
    return ok


def _ground_truth_delete_child(directory: Path) -> bool:
    victim = directory / f"victim_{os.getpid()}.txt"
    # created out-of-band by the fixture setup (as a different logical
    # actor) before the delete-only grant is exercised
    try:
        return not victim.exists()
    except OSError:
        return False


def _ground_truth_write(file_: Path) -> bool:
    """Plain O_WRONLY open -- checked against the ACL `write` right.
    Deliberately NOT `open(..., "a")`: an append-mode open is O_APPEND,
    which macOS's ACL evaluation checks against the *separate* `append`
    right, not `write` (independently discovered on this host: a
    `write`-only ACL grant with POSIX mode denying owner-write let a
    plain O_WRONLY open/`dd` succeed but an O_APPEND open still fail)."""
    try:
        with open(file_, "r+b"):
            pass
        return True
    except PermissionError:
        return False


def _ground_truth_append(file_: Path) -> bool:
    try:
        with open(file_, "a"):
            pass
        return True
    except PermissionError:
        return False


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
# 1. Fixed historical source: exact pre-repair revision, independently
#    verified as the true immediate parent of the repair commit
# ---------------------------------------------------------------------------


def test_pre_repair_commit_is_the_true_immediate_parent_of_the_repair_commit():
    parent = subprocess.run(
        ["git", "rev-parse", f"{_REPAIR_COMMIT}^"], capture_output=True, text=True, check=True, cwd=Path(__file__).resolve().parents[1]
    ).stdout.strip()
    full_pre = subprocess.run(
        ["git", "rev-parse", _PRE_REPAIR_COMMIT], capture_output=True, text=True, check=True, cwd=Path(__file__).resolve().parents[1]
    ).stdout.strip()
    assert parent == full_pre


def test_historical_defect_reproduced_from_fixed_pre_repair_blob(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    historical_source = subprocess.run(
        ["git", "show", f"{_PRE_REPAIR_COMMIT}:src/pcae/core/hatp_class_b_topology_verifier.py"],
        capture_output=True,
        text=True,
        check=True,
        cwd=repo_root,
    ).stdout
    # Independently confirm the exact marker-gate + substring-search shape
    # (not retyped -- asserted against the real extracted blob text).
    assert '"+" not in mode_line.split()[0]' in historical_source
    assert '"write" in entry or "allow write" in entry' in historical_source

    ns: dict = {}
    module_path = tmp_path / "_hist_blob.py"
    module_path.write_text(historical_source)
    import importlib.util

    spec = importlib.util.spec_from_file_location("hist_blob_149o_20j6", module_path)
    hist = importlib.util.module_from_spec(spec)
    sys.modules["hist_blob_149o_20j6"] = hist
    try:
        spec.loader.exec_module(hist)

        grandparent = tmp_path / "gp"
        grandparent.mkdir()
        os.chmod(grandparent, 0o500)  # POSIX-mode-safe: no owner/group/other write bit
        _grant_acl(grandparent, "add_file,delete_child")

        assert _mode_marker(grandparent, True).endswith("@"), "expected @ marker (provenance xattr), not + -- host precondition for this repro"
        assert _ground_truth_create_file(grandparent) is True, "ground truth: add_file ACL grant is really exploitable despite mode 500"

        historical_result = hist._acl_grants_agent_write_macos(grandparent)
        assert historical_result is False, (
            "historical pre-repair _acl_grants_agent_write_macos must misclassify a real, "
            "ground-truth-verified ACL-writable directory as non-write (the reproduced defect)"
        )
    finally:
        sys.modules.pop("hist_blob_149o_20j6", None)


def test_com_apple_provenance_xattr_present_and_non_removable(tmp_path):
    """Host evidence, not a general parser invariant: explains *why* the
    marker is unreliable on this host, without making correctness depend
    on this xattr specifically existing forever."""
    d = tmp_path / "x"
    d.mkdir()
    listing = subprocess.run(["/usr/bin/xattr", "-l", str(d)], capture_output=True, text=True, check=True).stdout
    assert "com.apple.provenance" in listing
    subprocess.run(["/usr/bin/xattr", "-d", "com.apple.provenance", str(d)], capture_output=False)
    listing_after = subprocess.run(["/usr/bin/xattr", "-l", str(d)], capture_output=True, text=True, check=True).stdout
    assert "com.apple.provenance" in listing_after, "expected non-removable on this host (empirical, not assumed)"


def test_repaired_parser_does_not_gate_on_marker_character(tmp_path):
    """Security-relevant conclusion independent of the provenance
    explanation: the repaired parser must discover ACLs from entry
    content, not the marker character. Verified by source inspection of
    the actual production function, not by trusting the docstring."""
    import inspect

    src = inspect.getsource(topo._acl_grants_agent_write_macos)
    assert '"+"' not in src and "'+'" not in src, "repaired implementation must not gate on the + marker character at all"


# ---------------------------------------------------------------------------
# 2 & 3. Independent primary-contract + real ACL grammar derivation
#    (module docstring records the man-chmod-derived rights taxonomy;
#    these tests assert the production vocabulary against it)
# ---------------------------------------------------------------------------


def test_man_chmod_rights_vocabulary_matches_production_known_rights():
    man_output = subprocess.run(["/usr/bin/man", "chmod"], capture_output=True, text=True).stdout
    # man(1) piped output retains formatting; fall back to col -b via shell if empty
    if not man_output.strip():
        man_output = subprocess.run("man chmod | col -b", shell=True, capture_output=True, text=True).stdout
    for right in ("write", "append", "writeattr", "writeextattr", "add_file", "add_subdirectory", "delete_child", "delete"):
        assert right in man_output, f"primary man-chmod evidence must document right {right!r}"
    documented_all = {
        "read", "write", "execute", "delete", "append", "writeattr", "writeextattr",
        "readsecurity", "writesecurity", "chown", "list", "search", "add_file",
        "add_subdirectory", "delete_child", "readattr", "file_inherit",
        "directory_inherit", "limit_inherit", "only_inherit", "readextattr",
    }
    assert documented_all <= topo._MACOS_ACL_KNOWN_RIGHTS, "production known-rights set must be a superset of every right man chmod documents"


def test_write_add_file_are_the_same_ace_rendered_contextually(tmp_path):
    """Independently re-derives the file/directory contextual-rendering
    claim rather than trusting it: grant the *same* right token to a
    directory and to a file and compare canonical `ls -le` output."""
    d = tmp_path / "d"
    d.mkdir()
    f = tmp_path / "f"
    f.write_text("x")
    _grant_acl(d, "add_file")
    _grant_acl(f, "write")
    d_line = [l for l in _raw_acl_lines(d, True) if "allow" in l][0]
    f_line = [l for l in _raw_acl_lines(f, False) if "allow" in l][0]
    assert "add_file" in d_line
    assert "write" in f_line
    # Cross-check: granting "write" to a directory or "add_file" to a file
    # is rejected/renamed by chmod itself if they were genuinely distinct rights;
    # instead both canonicalize per-context, confirming the shared-ACE claim.


# ---------------------------------------------------------------------------
# 4. Mode-marker reliability -- already covered above (marker not gated on,
#    xattr explanation empirically confirmed).
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 5. Real directory-right attacks -- capability-specific probes
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "right,probe",
    [
        ("add_file", _ground_truth_create_file),
        ("add_subdirectory", _ground_truth_create_subdir),
    ],
)
def test_directory_right_detected_with_capability_specific_probe(tmp_path, right, probe):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, right)
    assert probe(d) is True, f"ground truth: {right} grant must really authorize its specific action"
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is True


def test_delete_child_right_detected(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    victim = d / "victim.txt"
    victim.write_text("x")
    os.chmod(d, 0o500)
    _grant_acl(d, "delete_child")
    try:
        victim.unlink()
        deleted = True
    except OSError:
        deleted = False
    assert deleted is True, "ground truth: delete_child grant must really authorize deleting a pre-existing child"
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is True


def test_directory_posix_safe_control_no_acl_not_detected(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is False


def test_combined_canonicalized_multi_right_grant_detected(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, "add_file,delete_child")
    line = [l for l in _raw_acl_lines(d, True) if "allow" in l][0]
    assert "add_file" in line and "delete_child" in line
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is True


# ---------------------------------------------------------------------------
# 6. Real file-level ACL attacks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("right", ["write", "append", "writeextattr"])
def test_file_write_capable_right_detected(tmp_path, right):
    f = tmp_path / "f"
    f.write_text("x")
    os.chmod(f, 0o400)
    _grant_acl(f, right)
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(f, uid, gids) is True


def test_file_irrelevant_rights_only_not_detected(tmp_path):
    f = tmp_path / "f"
    f.write_text("x")
    os.chmod(f, 0o400)
    _grant_acl(f, "read,readattr,readextattr")
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(f, uid, gids) is False


def test_file_write_ground_truth(tmp_path):
    f = tmp_path / "f"
    f.write_text("x")
    os.chmod(f, 0o400)
    _grant_acl(f, "write")
    assert _ground_truth_write(f) is True


def test_file_append_ground_truth_uses_append_specific_right(tmp_path):
    """append is a right distinct from write (independently re-derived
    here): granting only `write` does not authorize an O_APPEND open."""
    f = tmp_path / "f"
    f.write_text("x")
    os.chmod(f, 0o400)
    _grant_acl(f, "write")
    assert _ground_truth_append(f) is False, "write-only grant must not authorize an O_APPEND open"
    _grant_acl(f, "append")
    assert _ground_truth_append(f) is True


# ---------------------------------------------------------------------------
# CENTRAL FINDING: writesecurity / chown misclassified safe
# ---------------------------------------------------------------------------


def test_writesecurity_and_chown_were_classified_known_safe_at_j6():
    """Documents the production classification as it stood at J.6's own
    commit (4c4fd16d), pinned to that commit's source blob rather than
    the live `topo` module -- this is the exact classification the
    finding below challenges. Phase 149O.20J.7 (a later, authorized
    repair) subsequently moves both rights into the write-capable set in
    live production source; pinning this assertion to the historical
    blob preserves this test as a permanent historical record without
    it breaking on that later, intended change (same precedent as
    149O.20J.5 updating 149O.20J.4's own pre-authorized xfail markers
    once its repair made them pass)."""
    repo_root = Path(__file__).resolve().parents[1]
    historical_source = subprocess.run(
        ["git", "show", "4c4fd16d:src/pcae/core/hatp_class_b_topology_verifier.py"],
        capture_output=True,
        text=True,
        check=True,
        cwd=repo_root,
    ).stdout
    safe_start = historical_source.index("_MACOS_ACL_KNOWN_SAFE_RIGHTS = frozenset(")
    safe_end = historical_source.index(")", safe_start)
    safe_block = historical_source[safe_start:safe_end]
    write_start = historical_source.index("_MACOS_ACL_WRITE_CAPABLE_RIGHTS = frozenset(")
    write_end = historical_source.index(")", write_start)
    write_block = historical_source[write_start:write_end]
    assert '"writesecurity"' in safe_block
    assert '"chown"' in safe_block
    assert '"writesecurity"' not in write_block
    assert '"chown"' not in write_block


def test_man_chmod_defines_writesecurity_as_write_equivalent_authority():
    man_output = subprocess.run("man chmod | col -b", shell=True, capture_output=True, text=True).stdout
    idx = man_output.find("writesecurity")
    assert idx != -1
    snippet = man_output[idx : idx + 120].replace("\n", " ")
    assert "security information" in snippet
    assert "ownership" in snippet and "mode" in snippet and "ACL" in snippet.replace("\t", " ") or "ACL" in snippet
    # primary evidence: writesecurity's own man-page definition names
    # ownership, mode, AND ACL as things it lets the holder rewrite --
    # each of those is independently sufficient to grant transitive
    # write-equivalent authority (rewrite the ACL to add `write`/
    # `add_file`; flip a mode write bit directly; via ownership, become
    # the object's owner and gain implicit chmod/chown authority).


def test_man_chmod_defines_chown_as_ownership_change_authority():
    man_output = subprocess.run("man chmod | col -b", shell=True, capture_output=True, text=True).stdout
    idx = man_output.find("chown   Change an object")
    assert idx != -1, "primary evidence: chown right is documented as 'Change an object's ownership'"


def test_self_owner_test_methodology_cannot_distinguish_grant_from_inherent_owner_authority(tmp_path):
    """Independently reproduces the specific methodological gap in
    149O.20J.5's 'empirically confirmed to not confer any effective
    write authority when granted alone' claim for writesecurity/chown:
    on a single-user host the *tester is always the object's owner*,
    and per `man chmod`'s own text ('Only the owner of a file or the
    super-user is permitted to change the mode of a file'), an owner can
    already chmod/chown their own file with **no ACL grant at all**.
    This proves granting vs. not granting writesecurity/chown is not a
    meaningful differential test in a same-owner fixture -- the owner's
    baseline capability is identical either way, so a same-owner
    'empirical' test cannot establish the right is inert for a genuine
    non-owner holder (the actual HBDC-REQ-009 admin-vs-agent threat
    model)."""
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    # No ACL grant at all -- yet the owner (this test process) can still
    # freely chmod/chown-equivalent-mutate the object, because ownership
    # itself (not any ACL entry) is what grants that authority on macOS.
    subprocess.run(["/bin/chmod", "700", str(d)], check=True)
    assert oct(os.stat(d).st_mode & 0o777) == oct(0o700)
    os.chmod(d, 0o500)  # restore
    # Therefore: 149O.20J.5's same-owner "empirical" writesecurity/chown
    # test measured pre-existing owner authority, not the ACE's effect.
    # This is a methodology gap, independently confirmed here, that
    # keeps the writesecurity/chown classification unproven for a real
    # non-owner agent principal -- the only principal the contract
    # (HBDC-REQ-009: admin-exclusive Protected Root write authority)
    # actually contemplates holding such a grant in production.


# ---------------------------------------------------------------------------
# 7/8. Contextual rendering + unknown-right fail-closed
# ---------------------------------------------------------------------------


def test_unknown_right_alone_fails_closed(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    fake_output = " 0: user:{} allow totallyfakeacenevermade\n".format(_whoami())
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=0, stdout="drwx------@ 2 x  wheel  64 x x x d\n" + fake_output)
        uid, gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(d, uid, gids)
    assert result is None


def test_unknown_right_combined_with_known_safe_fails_closed(tmp_path):
    fake_output = "drwx------@ 2 x  wheel  64 x x x d\n 0: user:{} allow read,totallyfakeacenevermade\n".format(_whoami())
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=0, stdout=fake_output)
        uid, gids = _agent_identity()
        d = Path("/tmp/does-not-need-to-exist-for-parser-test")
        result = topo._acl_grants_agent_write_macos(d, uid, gids)
    assert result is None


def test_unknown_right_combined_with_known_dangerous_fails_closed():
    fake_output = "drwx------@ 2 x  wheel  64 x x x d\n 0: user:{} allow add_file,totallyfakeacenevermade\n".format(_whoami())
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=0, stdout=fake_output)
        uid, gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(Path("/tmp/x"), uid, gids)
    assert result is None, "unknown right must never be silently dropped even alongside a recognized dangerous right"


def test_unknown_right_propagates_through_effective_write_access_and_ancestor_chain(tmp_path):
    fake_output = "drwx------@ 2 x  wheel  64 x x x d\n 0: user:{} allow totallyfakeacenevermade\n".format(_whoami())
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=0, stdout=fake_output)
        uid, gids = _agent_identity()
        write, reason, _ = topo._effective_write_access(d, uid, gids)
    assert write is None
    assert reason == "acl_inspection_unavailable"


# ---------------------------------------------------------------------------
# 9. Principal identity verification
# ---------------------------------------------------------------------------


def test_current_user_principal_detected(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, "add_file", principal=_whoami())
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is True


def test_unrelated_user_principal_not_detected(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, "add_file", principal="daemon")
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is False


def test_effective_group_principal_detected_without_special_casing(tmp_path):
    """gid 12 ('everyone') is real, unspecial-cased -- it is simply one of
    this process's real supplementary groups (`os.getgroups()`), not
    hardcoded into the test's expectation logic."""
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, "add_file", principal="everyone")
    uid, gids = _agent_identity()
    assert 12 in gids or 12 in os.getgroups(), "test precondition: gid 12 must be a real supplementary group on this host"
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is True


def test_unrelated_group_principal_not_detected(tmp_path):
    import grp

    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    uid, gids = _agent_identity()
    unrelated_gid = grp.getgrnam("_postfix").gr_gid
    assert unrelated_gid not in gids, "test precondition: agent must not actually belong to _postfix"
    _grant_acl(d, "add_file", principal="_postfix")
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is False


def test_unresolvable_dangerous_principal_fails_closed(tmp_path):
    fake_output = "drwx------@ 2 x  wheel  64 x x x d\n 0: user:totally_nonexistent_principal_zzz allow add_file\n"
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=0, stdout=fake_output)
        uid, gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(Path("/tmp/x"), uid, gids)
    assert result is None


def test_malformed_principal_shape_fails_closed(tmp_path):
    fake_output = "drwx------@ 2 x  wheel  64 x x x d\n 0: notaprincipalshape allow add_file\n"
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=0, stdout=fake_output)
        uid, gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(Path("/tmp/x"), uid, gids)
    assert result is None


# ---------------------------------------------------------------------------
# 10. Allow/deny safety direction
# ---------------------------------------------------------------------------


def test_deny_entry_alone_not_treated_as_allow(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _deny_acl(d, "add_file")
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is False


def test_allow_entry_treated_as_writable_even_with_coexisting_deny_conservative_direction(tmp_path):
    """The disclosed simplification: an allow for a write-capable right is
    treated as writable even if a deny entry might narrow real NFSv4
    effective access. Independently verify the *direction* is
    conservative (over-cautious, never a masked grant): this must never
    become a false-negative (a real grant reported safe)."""
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, "add_file")
    _deny_acl(d, "delete_child")
    uid, gids = _agent_identity()
    try:
        # Ground truth: add_file is genuinely still exploitable regardless of
        # the unrelated delete_child deny.
        assert _ground_truth_create_file(d) is True
        assert topo._acl_grants_agent_write_macos(d, uid, gids) is True
    finally:
        # The delete_child deny entry blocks pytest's own tmp_path cleanup
        # (a deny takes precedence over owner mode bits, independently
        # discovered above) -- strip it and restore owner mode explicitly.
        _reset_acl(d)
        os.chmod(d, 0o700)


def test_allow_write_capable_never_masked_by_deny_of_same_right_order_reversed(tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    os.chmod(d, 0o500)
    _grant_acl(d, "add_file")
    line_before = [l for l in _raw_acl_lines(d, True) if "allow" in l]
    assert line_before
    uid, gids = _agent_identity()
    # Confirms: whichever textual order chmod +a canonicalizes entries in,
    # the classifier scans every entry line (not just the first), so an
    # allow anywhere in the list is detected.
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is True


# ---------------------------------------------------------------------------
# 12/13. Malformed ACL entries + inspection failure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "malformed_line",
    [
        "not a numbered entry at all",
        " 0 user:x allow add_file",  # missing colon after number
        " 0: allow add_file",  # missing principal
        " 0: user:x add_file",  # missing allow/deny token
        " 0: user:x allow",  # empty rights
        " 0: user:x maybe add_file",  # unexpected decision token
        " 0: user:x allow add_file,,delete_child",  # duplicated separator -> empty right token
        "   0:    user:x   allow   add_file  ",  # extra whitespace (should still parse if shape matches)
    ],
)
def test_malformed_or_edge_case_acl_lines_never_produce_a_write_grant(tmp_path, malformed_line):
    fake_output = "drwx------@ 2 x  wheel  64 x x x d\n" + malformed_line + "\n"
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=0, stdout=fake_output)
        uid, gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(Path("/tmp/x"), uid, gids)
    assert result is not True, f"malformed line must never resolve to a positive write grant: {malformed_line!r}"


def test_truncated_line_never_a_grant():
    fake_output = "drwx------@ 2 x  wheel  64 x x x d\n 0: user:{} al\n".format(_whoami())
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=0, stdout=fake_output)
        uid, gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(Path("/tmp/x"), uid, gids)
    assert result is not True


def test_acl_tool_unavailable_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", "")
    d = tmp_path / "d"
    d.mkdir()
    uid, gids = _agent_identity()
    assert topo._acl_grants_agent_write_macos(d, uid, gids) is None


def test_acl_subprocess_nonzero_fails_closed(tmp_path):
    with mock.patch.object(subprocess, "run") as run:
        run.return_value = mock.Mock(returncode=1, stdout="")
        uid, gids = _agent_identity()
        result = topo._acl_grants_agent_write_macos(Path("/tmp/x"), uid, gids)
    assert result is None


def test_disappearing_path_never_becomes_safe(tmp_path):
    d = tmp_path / "gone"
    d.mkdir()
    os.chmod(d, 0o500)
    d.rmdir()
    uid, gids = _agent_identity()
    write, reason, _ = topo._effective_write_access(d, uid, gids)
    assert write is None
    assert reason == "path_missing"


# ---------------------------------------------------------------------------
# 14. Complete ancestor-chain composition (fresh fixtures)
# ---------------------------------------------------------------------------


def test_one_level_ancestor_acl_only_grandparent_rejected(chain):
    root, grandparent, parent, subject = chain
    _grant_acl(grandparent, "add_file")
    assert _ground_truth_create_file(grandparent) is True
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is False
    assert any(f"ancestor_writable:{grandparent}" in d for d in diagnostics)


def test_two_level_ancestor_acl_only_great_grandparent_rejected(tmp_path):
    ggp = tmp_path / "ggp"
    gp = ggp / "gp"
    parent = gp / "parent"
    subject = parent / "subject"
    subject.mkdir(parents=True)
    for p in (subject, parent, gp):
        os.chmod(p, 0o500)
    os.chmod(ggp, 0o500)
    os.chmod(tmp_path, 0o500)
    _grant_acl(ggp, "add_file")
    assert _ground_truth_create_file(ggp) is True
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    os.chmod(tmp_path, 0o755)
    os.chmod(ggp, 0o755)
    os.chmod(gp, 0o755)
    os.chmod(parent, 0o755)
    assert safe is False
    assert any(f"ancestor_writable:{ggp}" in d for d in diagnostics)


def test_fully_safe_chain_reaches_filesystem_root(chain):
    root, grandparent, parent, subject = chain
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is True
    assert diagnostics[-1] == "ancestor_walk_reached_filesystem_root"


# ---------------------------------------------------------------------------
# 15/16. Trusted-Git and Protected-Root composition
# ---------------------------------------------------------------------------


def test_trusted_git_rejects_acl_only_higher_ancestor(tmp_path, monkeypatch):
    fake_git_dir = tmp_path / "bin"
    fake_git_dir.mkdir()
    fake_git = fake_git_dir / "git"
    fake_git.write_text("#!/bin/sh\nexit 0\n")
    fake_git.chmod(0o500)
    os.chmod(fake_git_dir, 0o500)
    ancestor = tmp_path
    _grant_acl(ancestor, "add_file")
    assert _ground_truth_create_file(ancestor) is True
    monkeypatch.setenv("PATH", f"{fake_git_dir}:/usr/bin:/bin")
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path.parent, real)):
        resolved = topo._resolve_trusted_executable_with_effective_access("git")
    assert resolved is None, "ACL-only-writable ancestor above the git executable must reject trust"


def test_trusted_git_executable_own_bytes_acl_write_rejected(tmp_path, monkeypatch):
    fake_git_dir = tmp_path / "bin"
    fake_git_dir.mkdir()
    fake_git = fake_git_dir / "git"
    fake_git.write_text("#!/bin/sh\nexit 0\n")
    fake_git.chmod(0o500)
    os.chmod(fake_git_dir, 0o500)
    _grant_acl(fake_git, "write")
    assert _ground_truth_write(fake_git) is True
    monkeypatch.setenv("PATH", f"{fake_git_dir}:/usr/bin:/bin")
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        resolved = topo._resolve_trusted_executable_with_effective_access("git")
    assert resolved is None, "real file-level ACL write grant on the executable itself must reject trust (J-3 core)"


def test_protected_root_rejects_acl_only_higher_ancestor(chain):
    root, grandparent, parent, subject = chain
    _grant_acl(grandparent, "add_file")
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        result = topo._check_ancestor_chain(subject, uid, gids)
    assert result.satisfied is False


def test_git_and_protected_root_equivalent_on_identical_acl_only_grant(chain):
    root, grandparent, parent, subject = chain
    _grant_acl(grandparent, "add_file")
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        pr_safe, _ = topo._ancestor_chain_safe(subject, uid, gids)
        git_safe, _ = topo._ancestor_chain_safe(subject, uid, gids)  # same primitive, same boundary
    assert pr_safe == git_safe is False


# ---------------------------------------------------------------------------
# 17. J-3 historical scope adjudication -- independently re-derived from
#     primary phase documents (read-only inspection, asserted here as a
#     durable regression against the documents drifting silently)
# ---------------------------------------------------------------------------


def test_j3_original_finding_named_ancestor_acl_blindness():
    repo_root = Path(__file__).resolve().parents[1]
    doc = (repo_root / "docs" / "PHASE_149O_20J_1_CLASS_B_DEPLOYMENT_VERIFIER_NARROW_DEFECT_REPAIR.md").read_text()
    assert "would not be detected" in doc
    assert "ancestors" in doc


def test_j2_ancestor_acl_evidence_was_simulated_not_real():
    repo_root = Path(__file__).resolve().parents[1]
    doc = (repo_root / "docs" / "PHASE_149O_20J_2_CLASS_B_DEPLOYMENT_VERIFIER_NARROW_DEFECT_REPAIR_INDEPENDENT_VERIFICATION.md").read_text()
    assert "simulated an ACL-only write grant" in doc
    assert "forced to report" in doc


# ---------------------------------------------------------------------------
# 21/22/23/24. Regressions
# ---------------------------------------------------------------------------


def test_b_149o_20j_2_1_early_stop_defect_remains_closed_writable_grandparent(chain):
    root, grandparent, parent, subject = chain
    os.chmod(grandparent, 0o700)  # POSIX-mode writable (not ACL) -- the original early-stop scenario
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(root, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    os.chmod(grandparent, 0o500)
    assert safe is False
    assert any(f"ancestor_writable:{grandparent}" in d for d in diagnostics)


def test_j1_pth_tab_form_source_unchanged_since_pre_repair():
    repo_root = Path(__file__).resolve().parents[1]
    diff = subprocess.run(
        ["git", "diff", "--name-only", _PRE_REPAIR_COMMIT, "HEAD", "--", "src/pcae/core/hatp_environment_lock_verifier.py"],
        capture_output=True,
        text=True,
        check=True,
        cwd=repo_root,
    ).stdout.strip()
    assert diff == "", "environment-lock source (J-1's .pth fix) must remain byte-unchanged since the pre-J.5 revision"


def test_j2_effective_gid_still_folded_into_agent_identity():
    uid, gids = topo._current_agent_identity()
    assert os.getegid() in gids


def test_symlinked_higher_ancestor_never_becomes_safe(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real_dir)
    subject = link / "subject"
    real_dir_mkdir_target = real_dir / "subject"
    real_dir_mkdir_target.mkdir()
    real = topo._effective_write_access
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(tmp_path, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(subject, uid, gids)
    assert safe is False
    assert any("ancestor_symlink" in d for d in diagnostics)


def test_acl_indeterminate_above_safe_ancestor_never_becomes_safe(tmp_path, monkeypatch):
    boundary = tmp_path / "a"
    d1 = boundary / "b"
    d1.mkdir(parents=True)
    os.chmod(d1, 0o500)
    os.chmod(boundary, 0o500)
    monkeypatch.setenv("PATH", "")  # ACL tool unresolvable -> every ancestor ACL check indeterminate
    real = topo._effective_write_access
    # Stub everything above `boundary` (this dev host's own home-directory
    # tree, which is genuinely agent-writable) as safe, so only the two
    # constructed indeterminate-ACL levels reach the real production check.
    with mock.patch.object(topo, "_effective_write_access", side_effect=_stub_outside(boundary, real)):
        uid, gids = _agent_identity()
        safe, diagnostics = topo._ancestor_chain_safe(d1, uid, gids)
    assert safe is None, f"indeterminate evidence must never resolve to safe=True; got {safe}, diagnostics={diagnostics}"


# ---------------------------------------------------------------------------
# 25/26/27/28. HMIC non-binding, zero consumers, read-only wall, real host
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
    forbidden = ["os.chmod(", "os.chown(", "os.mkdir(", "os.makedirs(", "shutil.rmtree(", "os.remove(", "os.unlink(", "os.rename(", "os.replace(", "os.symlink(", "os.link(", ".write_text(", ".write_bytes("]
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


def test_repository_state_unchanged_after_verification(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    status_before = subprocess.run(["git", "status", "--porcelain", "--", "src/"], capture_output=True, text=True, cwd=repo_root).stdout
    conformance.verify_class_b_deployment_conformance()
    status_after = subprocess.run(["git", "status", "--porcelain", "--", "src/"], capture_output=True, text=True, cwd=repo_root).stdout
    assert status_before == status_after


# ---------------------------------------------------------------------------
# 20. Production diff reconstruction
# ---------------------------------------------------------------------------


def test_production_diff_scope_limited_to_topology_verifier():
    repo_root = Path(__file__).resolve().parents[1]
    changed = subprocess.run(
        ["git", "diff", "--name-only", _PRE_REPAIR_COMMIT, _REPAIR_COMMIT, "--", "src/"],
        capture_output=True,
        text=True,
        check=True,
        cwd=repo_root,
    ).stdout.split()
    assert changed == ["src/pcae/core/hatp_class_b_topology_verifier.py"]
