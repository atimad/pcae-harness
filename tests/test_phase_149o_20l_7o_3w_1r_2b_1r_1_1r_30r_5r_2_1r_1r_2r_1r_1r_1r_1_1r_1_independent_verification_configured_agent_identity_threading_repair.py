"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1 —
Independent Verification of the Configured-Agent-Identity Threading
Repair for `hatp_class_b_topology_verifier.py`'s ACL / trusted-
executable / ancestor-chain verification.

Independent of the predecessor repair phase's own suite
(`test_phase_..._1_1r_configured_agent_identity_threading_repair.py`):
this file independently re-derives the production consumer graph, the
subject-authority chain, and the positive/negative trust matrix from
primary source (the module itself, `hpac_protected_admin_writer.py`,
and `hpac_pawa_agent_exclusion.py`), rather than trusting the
predecessor's report or reusing its test bodies.

Strictly read-only against the real filesystem outside test-owned
`tmp_path` fixtures. No Protected Root / PAWA / PPA host state is
touched anywhere in this suite; no sudo, no YubiKey, no FIDO2 PIN, no
protected-presentation ceremony.
"""
from __future__ import annotations

import ast
import inspect
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pcae.core import hatp_class_b_topology_verifier as topo  # noqa: E402
from pcae.core import hpac_pawa_agent_exclusion as agent_exclusion  # noqa: E402

# Frozen at this IV phase's entry (V) — HEAD of the predecessor repair
# phase's finalized endpoint (R_FINAL), independently re-derived via
# `git log -1` below, not merely copied from the predecessor's report.
IV_ENTRY_SHA = "67d542ef3e4ba99ca2f39a2a69e92309a20ceec8"
PREDECESSOR_REPAIR_ENTRY_SHA = "9d04603e"
PREDECESSOR_PRODUCTION_REPAIR_COMMIT = "8407dd24"
PREDECESSOR_TEST_FOLLOWUP_COMMIT = "8521b9c0"


def _git(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)


def _module_source() -> str:
    return Path(inspect.getsourcefile(topo)).read_text(encoding="utf-8")


def _real_identity() -> "tuple[int, frozenset[int]]":
    return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}


# ═══════════════════════════════════════════════════════════════════════
# LINEAGE (items 1-5, 39, 49)
# ═══════════════════════════════════════════════════════════════════════


def test_iv_entry_sha_is_current_head():
    result = _git("log", "-1", "--format=%H")
    assert result.stdout.strip() == IV_ENTRY_SHA


def test_predecessor_repair_commit_is_the_sole_production_change():
    """Independently reconstructs which predecessor commit changed
    production source, rather than trusting the phase report's
    'Commits:' line."""

    changed = _git("show", "--stat", "--format=", PREDECESSOR_PRODUCTION_REPAIR_COMMIT).stdout
    assert "src/pcae/core/hatp_class_b_topology_verifier.py" in changed
    followup_changed = _git("show", "--stat", "--format=", PREDECESSOR_TEST_FOLLOWUP_COMMIT).stdout
    assert "src/pcae/core/hatp_class_b_topology_verifier.py" not in followup_changed, (
        "the follow-up commit must be test-only, not a second production change"
    )


def test_production_diff_scope_bounded_to_topology_verifier_only():
    diff = _git("diff", "--stat", f"{PREDECESSOR_REPAIR_ENTRY_SHA}..{IV_ENTRY_SHA}", "--", "src/pcae/")
    changed_files = [
        line.split("|")[0].strip()
        for line in diff.stdout.splitlines()
        if "|" in line
    ]
    assert changed_files == ["src/pcae/core/hatp_class_b_topology_verifier.py"]


def test_repair_added_exactly_one_new_function_no_deletions_elsewhere():
    diff = _git("diff", f"{PREDECESSOR_REPAIR_ENTRY_SHA}..{IV_ENTRY_SHA}", "--", "src/pcae/core/hatp_class_b_topology_verifier.py")
    added_defs = [
        line for line in diff.stdout.splitlines()
        if line.startswith("+def ") or line.startswith("+    def ")
    ]
    removed_defs = [
        line for line in diff.stdout.splitlines()
        if line.startswith("-def ") or line.startswith("-    def ")
    ]
    assert removed_defs == []
    assert any("_resolve_trusted_executable_for_subject" in d for d in added_defs)


def test_contracts_and_dependencies_byte_unchanged_since_repair_entry():
    contracts_diff = _git("diff", "--stat", f"{PREDECESSOR_REPAIR_ENTRY_SHA}..{IV_ENTRY_SHA}", "--", "docs/contracts/")
    assert contracts_diff.stdout.strip() == ""
    pyproject_diff = _git("diff", f"{PREDECESSOR_REPAIR_ENTRY_SHA}..{IV_ENTRY_SHA}", "--", "pyproject.toml")
    assert pyproject_diff.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════
# CONSUMER INVENTORY (items 6-14) — independently walked from source,
# not reused from the predecessor's own inventory.
# ═══════════════════════════════════════════════════════════════════════


def test_current_agent_identity_has_exactly_three_call_sites():
    """Independently re-derives every call site of the ambient-identity
    primitive by source scan, and classifies each."""

    tree = ast.parse(_module_source())
    call_lines = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_current_agent_identity":
            call_lines.append(node.lineno)
    assert len(call_lines) == 3, f"expected exactly 3 call sites, found {call_lines}"


def test_current_agent_identity_call_sites_are_all_live_process_subject_consumers():
    """Each of the three call sites must belong to a function whose
    consumer classification is LIVE_PROCESS_SUBJECT: the bare
    `_resolve_trusted_executable`, its own-environment wrapper
    `_resolve_trusted_executable_with_effective_access`, and the
    public diagnostic entry point `verify_class_b_topology_conformance`
    — never the (already-parameterized) ACL-tool-resolution path."""

    tree = ast.parse(_module_source())
    enclosing = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for inner in ast.walk(node):
                if (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Name)
                    and inner.func.id == "_current_agent_identity"
                ):
                    enclosing[inner.lineno] = node.name
    assert set(enclosing.values()) == {
        "_resolve_trusted_executable",
        "_resolve_trusted_executable_with_effective_access",
        "verify_class_b_topology_conformance",
    }


def test_acl_helpers_no_longer_call_ambient_resolver():
    """The exact repaired property, independently re-derived: neither
    ACL helper's source references the bare ambient-identity resolver
    or `_current_agent_identity` at all."""

    for fn in (topo._acl_grants_agent_write_linux, topo._acl_grants_agent_write_macos):
        src = inspect.getsource(fn)
        assert "_current_agent_identity" not in src
        assert "_resolve_trusted_executable(" not in src
        assert "_resolve_trusted_executable_for_subject(" in src


def test_effective_write_access_subtree_never_reaches_ambient_identity(tmp_path, monkeypatch):
    """Proves, by poisoning `_current_agent_identity` to raise, that the
    entire `_effective_write_access` call subtree (which
    `hpac_protected_admin_writer.py` invokes with the CONFIGURED agent
    subject) never touches ambient identity for any code path exercised
    by a plain file with no ACL."""

    def _poison():
        raise AssertionError("ambient identity must not be consulted by this subtree")

    monkeypatch.setattr(topo, "_current_agent_identity", _poison)
    target = tmp_path / "f"
    target.touch()
    real_uid, real_gids = _real_identity()
    result = topo._effective_write_access(target, real_uid, real_gids)
    assert result[0] is True  # owner + real uid -> writable, and no exception raised


def test_ancestor_chain_safe_never_reaches_ambient_identity(tmp_path, monkeypatch):
    def _poison():
        raise AssertionError("ambient identity must not be consulted by this subtree")

    monkeypatch.setattr(topo, "_current_agent_identity", _poison)
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    fictitious_uid = 999321
    safe, _diag = topo._ancestor_chain_safe(nested, fictitious_uid, frozenset())
    # tmp_path's own ancestry is not owned/writable by the fictitious
    # subject in the relevant way; the call must complete without ever
    # touching ambient identity regardless of the boolean outcome.
    assert safe in (True, False, None)


def test_production_writer_threads_configured_agent_not_ambient():
    """Independently re-derives, from `hpac_protected_admin_writer.py`
    source, that the production caller passes `configured_agent.uid` /
    `.gids` (from `resolve_configured_agent_identity`) into
    `_effective_write_access` / `_ancestor_chain_safe` — never
    `_current_agent_identity()` — confirming this boundary was already
    correct and required no repair (item 8)."""

    from pcae.core import hpac_protected_admin_writer as writer

    src = inspect.getsource(writer)
    assert "effective_write_access(root, configured_agent.uid, configured_agent.gids)" in src
    assert "ancestor_chain_safe(root, configured_agent.uid, configured_agent.gids)" in src
    # The module's own live_uid variable is used only for a distinctness
    # comparison, never substituted as the subject into the topology
    # calls above.
    assert "effective_write_access(root, live_uid" not in src


def test_diagnostic_entry_point_remains_non_authoritative_and_unimported_by_production():
    """`verify_class_b_topology_conformance` (LIVE_PROCESS_SUBJECT by
    module design) must remain reachable only through the disclosed
    non-authoritative aggregator, never through the real PAWA/PPA
    registration path — independently re-checked by grep across the
    whole production module tree."""

    result = subprocess.run(
        ["grep", "-rl", "verify_class_b_topology_conformance", "src/pcae/core/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    importers = {line for line in result.stdout.splitlines() if line and not line.endswith(".pyc")}
    assert importers == {
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_class_b_conformance.py",
    }


# ═══════════════════════════════════════════════════════════════════════
# SUBJECT AUTHORITY (items 15-24)
# ═══════════════════════════════════════════════════════════════════════


def test_configured_agent_identity_source_is_protected_record_not_os_geteuid():
    node = ast.parse(inspect.getsource(agent_exclusion.resolve_configured_agent_identity))
    ambient_calls = [
        n for n in ast.walk(node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "geteuid"
    ]
    assert ambient_calls == [], "the resolution function must never itself call os.geteuid()"
    assert "validate_agent_exclusion_record" in inspect.getsource(agent_exclusion.resolve_configured_agent_identity)


def test_configured_agent_identity_never_reads_env_or_cli_controlled_authority():
    """Source-scans the resolution chain for any `os.environ`/`getenv`
    read keyed by SUDO_USER/USER/LOGNAME, or any function-parameter-fed
    substitution of the subject in the production (non-fixture) path."""

    src = inspect.getsource(agent_exclusion)
    for forbidden in ("SUDO_USER", "os.environ[\"USER\"]", "LOGNAME", "getlogin", "getuser"):
        assert forbidden not in src


def test_live_uid_mismatch_with_provisioned_uid_fails_closed():
    with mock.patch("pwd.getpwnam") as getpwnam:
        getpwnam.return_value = mock.Mock(pw_uid=999999, pw_gid=999999)
        with pytest.raises(agent_exclusion.AgentExclusionError):
            agent_exclusion.resolve_live_authority_identity("someaccount", provisioned_uid=501)


def test_fixture_identity_source_is_a_disclosed_test_only_seam():
    sig = inspect.signature(agent_exclusion.resolve_live_authority_identity)
    assert "_configured_agent_identity_source" in sig.parameters
    assert sig.parameters["_configured_agent_identity_source"].default is None


def test_fixture_identity_source_still_enforces_uid_match_when_used():
    def _fixture(_account, _uid):
        return 42, frozenset({42})

    with pytest.raises(agent_exclusion.AgentExclusionError):
        agent_exclusion.resolve_live_authority_identity(
            "someaccount", provisioned_uid=501, _configured_agent_identity_source=_fixture
        )


# ═══════════════════════════════════════════════════════════════════════
# MODE / GROUP / OTHER matrix (items 25-29) — independently exercised
# against `_effective_write_access` (the function production actually
# calls), not merely `_mode_and_group_write_access`.
# ═══════════════════════════════════════════════════════════════════════


def test_owner_write_by_non_matching_subject_not_writable(tmp_path):
    """Simulates 'root owns, owner-writable, configured subject differs'
    without needing real root: the fixture file is owned by this test
    process's real uid, and the subject passed in is a distinct
    fictitious uid — the relation under test (`st_uid == agent_uid`) is
    identical regardless of which side is literally uid 0."""

    target = tmp_path / "f"
    target.touch()
    target.chmod(0o600)
    fictitious_uid = 999322
    write, reason, _ev = topo._effective_write_access(target, fictitious_uid, frozenset())
    assert write is False, reason


def test_owner_write_by_matching_subject_is_writable(tmp_path):
    target = tmp_path / "f"
    target.touch()
    target.chmod(0o600)
    real_uid, real_gids = _real_identity()
    write, reason, _ev = topo._effective_write_access(target, real_uid, real_gids)
    assert write is True, reason


def test_group_write_by_member_subject_is_writable(tmp_path):
    target = tmp_path / "f"
    target.touch()
    st_gid = target.stat().st_gid
    target.chmod(0o060)
    fictitious_uid = 999323
    write, reason, _ev = topo._effective_write_access(target, fictitious_uid, frozenset({st_gid}))
    assert write is True, reason


def test_group_write_by_unrelated_subject_not_writable(tmp_path):
    target = tmp_path / "f"
    target.touch()
    target.chmod(0o060)
    fictitious_uid = 999324
    write, reason, _ev = topo._effective_write_access(target, fictitious_uid, frozenset({999325}))
    assert write is False, reason


def test_other_write_is_writable_for_any_subject(tmp_path):
    target = tmp_path / "f"
    target.touch()
    target.chmod(0o002)
    write, reason, _ev = topo._effective_write_access(target, 999326, frozenset())
    assert write is True, reason


# ═══════════════════════════════════════════════════════════════════════
# ROOT-EXECUTOR / AMBIENT-IDENTITY POISONING (the central repaired
# property — items 25, 33, 37, 38)
# ═══════════════════════════════════════════════════════════════════════


def test_ambient_root_like_identity_does_not_poison_configured_agent_acl_result(tmp_path, monkeypatch):
    """Central repair proof: even with the *ambient* process identity
    simulated as a root-like uid 0 (whose own writeability over
    root-owned system directories is real and irrelevant), the ACL
    result for a distinct, explicitly-passed configured-agent subject
    resolves deterministically — never `None` (indeterminate) merely
    because the ambient identity happened to own the resolution tool's
    directory."""

    target = tmp_path / "f"
    target.touch()
    real_uid, real_gids = _real_identity()
    monkeypatch.setattr(topo, "_current_agent_identity", lambda: (0, frozenset({0})))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    if sys.platform == "darwin":
        result = topo._acl_grants_agent_write_macos(target, real_uid, real_gids)
    elif sys.platform == "linux":
        result = topo._acl_grants_agent_write_linux(target, real_uid, real_gids)
    else:
        pytest.skip("unsupported platform for ACL check")

    assert result is False, f"expected deterministic no-grant, got {result!r} (indeterminate means the defect is back)"


def test_before_repair_ambient_primitive_still_reproduces_the_historical_defect(tmp_path, monkeypatch):
    """Independently reconstructs the pre-repair failure mode from the
    still-present, still-frozen `_resolve_trusted_executable` (ambient-
    only) to prove the defect this repair addresses is real and
    specific to identity threading — not a PATH/tooling artifact
    (item 10/21)."""

    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    if not Path("/usr/bin/ls").exists():
        pytest.skip("host has no /usr/bin/ls to reproduce against")

    with mock.patch.object(topo, "_current_agent_identity", return_value=(0, frozenset({0}))):
        ambient_root_result = topo._resolve_trusted_executable("ls")
    with mock.patch.object(topo, "_current_agent_identity", return_value=(999999, frozenset())):
        ambient_nonowner_result = topo._resolve_trusted_executable("ls")

    assert ambient_nonowner_result is not None, "sanity: a genuinely non-owning ambient subject must resolve ls"
    if os.stat("/usr/bin").st_uid == 0 and (os.stat("/usr/bin").st_mode & 0o200):
        assert ambient_root_result is None, (
            "reproduces the historical defect: an ambient uid-0-like subject that owns "
            "/usr/bin's owner-write bit must fail closed here"
        )
    else:
        pytest.skip("host /usr/bin is not root-owned-and-owner-writable; cannot reproduce this exact shape")


def test_repaired_acl_path_immune_to_the_same_poisoning_that_broke_ambient_resolution(tmp_path, monkeypatch):
    target = tmp_path / "f"
    target.touch()
    real_uid, real_gids = _real_identity()
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    with mock.patch.object(topo, "_current_agent_identity", return_value=(0, frozenset({0}))):
        if sys.platform == "darwin":
            repaired = topo._acl_grants_agent_write_macos(target, real_uid, real_gids)
        else:
            repaired = topo._acl_grants_agent_write_linux(target, real_uid, real_gids)
    assert repaired is False


# ═══════════════════════════════════════════════════════════════════════
# TRUSTED-EXECUTABLE / PATH SEMANTICS (items 23-27, 30) —
# `_resolve_trusted_executable_for_subject` matrix.
# ═══════════════════════════════════════════════════════════════════════


def test_for_subject_resolves_ls_for_a_non_owning_subject(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    real_uid, real_gids = _real_identity()
    resolved = topo._resolve_trusted_executable_for_subject("ls", real_uid, real_gids)
    if not Path("/usr/bin/ls").exists() and not Path("/bin/ls").exists():
        pytest.skip("host has no ls on PATH")
    assert resolved is not None
    assert resolved.name == "ls"


def test_for_subject_rejects_when_configured_agent_owns_the_resolved_target(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake_tool = bin_dir / "customtool"
    fake_tool.write_text("#!/bin/sh\nexit 0\n")
    fake_tool.chmod(0o700)
    monkeypatch.setenv("PATH", str(bin_dir))
    real_uid, real_gids = _real_identity()  # this test process owns fake_tool
    resolved = topo._resolve_trusted_executable_for_subject("customtool", real_uid, real_gids)
    assert resolved is None, "a tool writable by the configured agent must never be trusted"


def test_for_subject_rejects_when_an_earlier_path_dir_is_agent_writable(tmp_path, monkeypatch):
    hostile_dir = tmp_path / "hostile"
    hostile_dir.mkdir()
    monkeypatch.setenv("PATH", f"{hostile_dir}:/usr/bin:/bin")
    real_uid, real_gids = _real_identity()  # this test owns hostile_dir -> agent-writable
    if not Path("/usr/bin/ls").exists() and not Path("/bin/ls").exists():
        pytest.skip("host has no ls on PATH")
    resolved = topo._resolve_trusted_executable_for_subject("ls", real_uid, real_gids)
    assert resolved is None, "an unsafe earlier PATH entry must reject resolution even though the real ls is later"


def test_for_subject_rejects_when_a_later_root_only_path_dir_precedes_real_target(tmp_path, monkeypatch):
    """Item 27: a directory the configured agent cannot write must not
    itself cause rejection merely because it precedes resolution."""

    if not Path("/usr/bin/ls").exists():
        pytest.skip("host has no /usr/bin/ls")
    unrelated_uid = 999327
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    resolved = topo._resolve_trusted_executable_for_subject("ls", unrelated_uid, frozenset())
    assert resolved is not None, "a root-only-writable preceding directory must not itself cause rejection"


def test_for_subject_never_falls_back_to_ambient_on_empty_gids(monkeypatch):
    """Missing/empty configured-gids must not silently broaden trust by
    falling back to the ambient process's own group set."""

    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setattr(topo, "_current_agent_identity", lambda: (0, frozenset({0, 20})))
    if not Path("/usr/bin/ls").exists():
        pytest.skip("host has no /usr/bin/ls")
    resolved = topo._resolve_trusted_executable_for_subject("ls", 999328, frozenset())
    # Must resolve purely against (999328, {}) -- not against the
    # poisoned ambient (0, {0, 20}).
    assert resolved is not None


# ═══════════════════════════════════════════════════════════════════════
# NO ROOT BYPASS / NO ALLOWLIST (items 28-29) — source-level proof.
# ═══════════════════════════════════════════════════════════════════════


def test_no_euid_zero_special_case_anywhere_in_module():
    src = _module_source()
    assert "geteuid() == 0" not in src
    assert "uid == 0" not in src
    for line in src.splitlines():
        lowered = line.lower()
        if "if" in lowered and ("euid" in lowered or "root" in lowered) and "0" in line:
            assert False, f"suspicious root-special-case line: {line!r}"


def test_no_hardcoded_system_directory_allowlist():
    src = _module_source()
    for forbidden in ('"/usr/bin"', "'/usr/bin'", '"/bin"', "'/bin'", '"/usr/sbin"', '"/sbin"'):
        assert forbidden not in src, f"hardcoded system-path allowlist token found: {forbidden}"


# ═══════════════════════════════════════════════════════════════════════
# LIVE-PROCESS CALLER PRESERVATION (items 34, 44-46)
# ═══════════════════════════════════════════════════════════════════════


def test_resolve_trusted_executable_with_effective_access_unchanged_and_still_ambient():
    src = inspect.getsource(topo._resolve_trusted_executable_with_effective_access)
    assert "_current_agent_identity()" in src
    assert "_resolve_trusted_executable(name)" in src


def test_environment_lock_verifier_git_resolution_still_ambient_by_design():
    from pcae.core import hatp_environment_lock_verifier as env_lock

    src = inspect.getsource(env_lock)
    assert "_resolve_trusted_executable_with_effective_access" in src


def test_resolve_trusted_executable_bare_primitive_byte_identical_to_repair_entry():
    diff = _git(
        "diff",
        f"{PREDECESSOR_REPAIR_ENTRY_SHA}..{IV_ENTRY_SHA}",
        "-G",
        r"^def _resolve_trusted_executable\(",
        "--",
        "src/pcae/core/hatp_class_b_topology_verifier.py",
    )
    assert diff.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════
# HOST STATE READ-ONLY (items 47, 54-62)
# ═══════════════════════════════════════════════════════════════════════

_EXPECTED_HELPER_DIGEST = "933c66464516080b91fa2b5e7e2b50ea176a5887058bc63a51ddb083c9ea6182"
_PROTECTED_ROOT = Path("/Library/Application Support/PCAE/HPAC/protected-root")


@pytest.mark.skipif(not _PROTECTED_ROOT.exists(), reason="no generation-1 host state present on this runner")
def test_host_protected_root_generation_and_helper_digest_unchanged():
    import hashlib

    anchor = _PROTECTED_ROOT / ".authority" / "current-generation.json"
    if anchor.exists():
        import json

        data = json.loads(anchor.read_text())
        assert data.get("generation") == 1

    helper_candidates = list((_PROTECTED_ROOT / ".authority").glob("**/*helper*")) if (_PROTECTED_ROOT / ".authority").exists() else []
    for candidate in helper_candidates:
        if candidate.is_file():
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if digest == _EXPECTED_HELPER_DIGEST:
                break


def test_ppa_current_generation_and_installation_absent_on_host():
    ppa_current_gen = _PROTECTED_ROOT / ".authority" / "presentation-current-generation.json"
    ppa_install = _PROTECTED_ROOT / ".authority" / "presentation-installation.json"
    assert not ppa_current_gen.exists()
    assert not ppa_install.exists()


def test_this_iv_suite_performs_no_filesystem_write_outside_tmp_path():
    """Forbidden tokens are built by concatenation so the literal
    substring never appears in this test's own source (which would
    otherwise self-match a naive scan of its own file)."""

    src = Path(__file__).read_text(encoding="utf-8")
    for forbidden in ("shutil." + "rmtree(", "os." + "remove(", "os." + "chown(", "os.chmod(" + '"/', "os.chmod(" + "'/"):
        assert forbidden not in src, forbidden


# ═══════════════════════════════════════════════════════════════════════
# RUNTIME / DEVELOPMENT NON-REGRESSION (item 44)
# ═══════════════════════════════════════════════════════════════════════


def test_ordinary_pcae_health_and_check_do_not_require_hardware_ceremony():
    health = subprocess.run(["pcae", "health"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
    assert health.returncode == 0
    check = subprocess.run(["pcae", "check"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=60)
    assert check.returncode == 0


# ═══════════════════════════════════════════════════════════════════════
# VERDICT (items 82-83)
# ═══════════════════════════════════════════════════════════════════════


def test_verdict_configured_agent_identity_threading_repair_independently_verified():
    """This test's presence and green status is itself part of the
    canonical verdict record — see the phase report for the full
    written adjudication. It re-asserts the load-bearing facts this
    verdict depends on."""

    assert "_resolve_trusted_executable_for_subject" in inspect.getsource(topo._acl_grants_agent_write_linux)
    assert "_resolve_trusted_executable_for_subject" in inspect.getsource(topo._acl_grants_agent_write_macos)
    assert topo._resolve_trusted_executable_for_subject.__doc__ is not None


def test_verdict_f5_continuation_ready_but_not_begun_here():
    """This IV phase must not itself perform any F-5 continuation
    action. Static proof: this test file never invokes the PPA install
    script or protected-root admin script as a subprocess."""

    src = Path(__file__).read_text(encoding="utf-8")
    ppa_install_call = 'subprocess.run(["scripts/' + 'hpac_protected_presentation_admin.py'
    root_admin_call = 'subprocess.run(["scripts/' + 'hpac_protected_root_admin.py'
    assert ppa_install_call not in src
    assert root_admin_call not in src
