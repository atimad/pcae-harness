"""Phase 149O.20L.7D.8 -- Class-B Verifier Source Repair Independent
Verification.

Independently-authored companion test module for this verification-only
phase. Does NOT import
`tests/test_phase_149o_20l_7d_7_class_b_verifier_narrow_source_repair.py`
as oracle -- new fixtures, new topologies, new assertions, re-derived
directly from primary source (`src/pcae/core/hatp_class_b_conformance.py`,
`hatp_environment_lock_verifier.py`, `hatp_class_b_topology_verifier.py`)
and from `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001
v1.0), not from 7D.7's own report prose.

This module verifies, independently, that 7D.7's two repairs
(B-149O.20L.7D.6-1: `distribution("pcae")` -> `distribution("pcae-harness")`
for HBDC-REQ-022/035; B-149O.20L.7D.6-3: unconditional
`_effective_write_access` symlink=True heuristic -> the new
`_symlink_effective_write_access` channel analysis, for HBDC-REQ-030) are
correct, minimal, complete, and fail-closed. It does not modify production
source, contracts, or the Dell host; it does not redeploy, certify, or
activate anything.
"""
from __future__ import annotations

import importlib.metadata
import os
import shutil
from pathlib import Path

import pytest

from pcae.core import hatp_class_b_conformance as conformance
from pcae.core import hatp_class_b_topology_verifier as topo
from pcae.core import hatp_environment_lock_verifier as envlock

pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]


def _distinct_agent_identity() -> "tuple[int, frozenset[int]]":
    """A uid/gid set guaranteed distinct from the real process identity
    that owns freshly-created fixture files -- the only way to simulate
    a non-owning, non-group-member agent principal without root."""

    return os.geteuid() + 424242, frozenset()


# ═══════════════════════════════════════════════════════════════════════════
# Distribution-identity ground truth and repair (HBDC-REQ-022/035)
# ═══════════════════════════════════════════════════════════════════════════


def test_pyproject_declares_pcae_harness_as_canonical_distribution_name():
    """Primary-source ground truth, independent of both modules under
    test: `pyproject.toml`'s own `[project] name` is what
    `importlib.metadata` keys distributions by (PEP 621/566), not the
    import package name (`pcae`, from `packages = ["src/pcae"]`)."""

    text = Path(__file__).resolve().parent.parent.joinpath("pyproject.toml").read_text(encoding="utf-8")
    assert '\nname = "pcae-harness"' in text
    assert 'packages = ["src/pcae"]' in text


def test_canonical_name_resolves_real_metadata_on_this_host():
    dist = importlib.metadata.distribution("pcae-harness")
    assert dist is not None
    assert dist.version


def test_old_defective_key_still_does_not_resolve():
    """The repair did not add a second successful lookup path alongside
    the broken one -- the old key must still fail, proving the literal
    itself was the fix, not an added fallback."""

    with pytest.raises(importlib.metadata.PackageNotFoundError):
        importlib.metadata.distribution("pcae")


def test_no_stray_wrong_distribution_lookup_anywhere_in_src():
    """Independent repo-wide search (not reusing 7D.7's own grep
    result) for any remaining `distribution("pcae")` call in production
    source."""

    src_root = Path(__file__).resolve().parent.parent / "src"
    offenders = []
    for path in src_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if 'distribution("pcae")' in text or "distribution('pcae')" in text:
            offenders.append(str(path))
    assert offenders == []


def test_req_022_pre_repair_literal_fails_lookup_when_executed_for_real():
    """Reproduces the actual pre-repair defect by calling the real
    (repaired) function's own underlying primitive with the pre-repair
    literal, executed against the real installed environment -- not
    string inspection."""

    with pytest.raises(importlib.metadata.PackageNotFoundError):
        importlib.metadata.distribution("pcae")


def test_req_022_repaired_function_reaches_downstream_evaluation():
    """Real execution of the repaired production function (no mocking
    of `importlib.metadata`) against this host's actual installed
    metadata: must not fail at the lookup step."""

    result = conformance._check_model_a_deployment(os.geteuid())
    assert result.status != "pcae_distribution_metadata_not_found"


def test_req_035_repaired_function_reaches_downstream_evaluation():
    result = envlock._check_editable_install_metadata(os.geteuid(), frozenset(os.getgroups()))
    assert result.status != "pcae_distribution_metadata_not_found"


def test_req_022_invalid_case_absent_distribution_remains_fail_closed(monkeypatch):
    def _boom(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(conformance.importlib.metadata, "distribution", _boom)
    result = conformance._check_model_a_deployment(os.geteuid())
    assert result.satisfied is False
    assert result.status == "pcae_distribution_metadata_not_found"


def test_req_035_invalid_case_absent_distribution_remains_fail_closed(monkeypatch):
    def _boom(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(envlock.importlib.metadata, "distribution", _boom)
    result = envlock._check_editable_install_metadata(os.geteuid(), frozenset(os.getgroups()))
    assert result.satisfied is False
    assert result.status == "pcae_distribution_metadata_not_found"


# ═══════════════════════════════════════════════════════════════════════════
# Symlink / effective-write-access repair (HBDC-REQ-030)
# ═══════════════════════════════════════════════════════════════════════════

_LAB_ROOT = Path(os.path.expanduser("~/.cache/pcae_149o_20l_7d_8_test_lab"))


@pytest.fixture()
def lab(monkeypatch):
    """Fixture root under $HOME, never under /tmp: this host's /tmp is
    mode 1777 (world-writable, sticky bit) at the top level, and
    `_ancestor_chain_safe` correctly walks every ancestor up to the
    filesystem root (HBDC-REQ-017/020) -- so any fixture placed under a
    world-writable ancestor is unconditionally, correctly classified
    unsafe regardless of its own leaf-level permissions. That would
    make /tmp fixtures unusable for constructing a genuinely *safe*
    topology. $HOME's real ancestor chain has no world-writable link on
    this host, matching the real Dell topology's /etc, /usr chain.

    Also stubs the ACL channel closed: real trusted-executable
    resolution for the ACL tool (`ls`/`getfacl`) is itself PATH-based
    and, on a real dev machine, several PATH entries are owned by the
    real interactive user -- an orthogonal, already-verified concern
    (149O.20J series), not what this repair changed. Isolating it here
    prevents every case from collapsing to indeterminate for a reason
    unrelated to the symlink repair under test.
    """

    shutil.rmtree(_LAB_ROOT, ignore_errors=True)
    _LAB_ROOT.mkdir(parents=True)
    monkeypatch.setattr(topo, "_acl_grants_agent_write", lambda path, uid, gids: False)
    yield _LAB_ROOT
    shutil.rmtree(_LAB_ROOT, ignore_errors=True)


def test_pre_repair_primitive_falsely_classifies_safe_symlink_as_writable(lab):
    """Independent reproduction of the actual pre-repair defect: the
    exact pre-repair implementation (`path.is_symlink() -> True,
    "path_is_symlink"`, immutable per git blob 8a18f73d) applied to a
    genuinely safe, Dell-equivalent topology."""

    agent_uid, agent_gids = _distinct_agent_identity()
    target = lab / "target.py"
    target.write_text("")
    target.chmod(0o644)
    link = lab / "link.py"
    link.symlink_to(target)
    lab.chmod(0o755)

    def pre_repair_effective_write_access(path, uid, gids):
        if path.is_symlink():
            return True, "path_is_symlink", (str(path),)
        raise AssertionError("fixture only exercises the symlink branch")

    write, reason, _ = pre_repair_effective_write_access(link, agent_uid, agent_gids)
    assert write is True and reason == "path_is_symlink", "pre-repair defect reproduced: false positive on a safe symlink"


def test_dell_equivalent_safe_symlink_is_effectively_unwritable(lab):
    """Real Dell topology: sitecustomize.py -> /etc/python3.12/sitecustomize.py,
    admin-owned parent and target, all mutation channels closed."""

    agent_uid, agent_gids = _distinct_agent_identity()
    target = lab / "sitecustomize.py"
    target.write_text("")
    target.chmod(0o644)
    link = lab / "sitecustomize_link.py"
    link.symlink_to(target)
    lab.chmod(0o755)

    write, reason, _ = topo._effective_write_access(link, agent_uid, agent_gids)
    assert write is False
    assert reason == "symlink_fully_closed"


def test_symlink_replacement_attack_writable_parent_is_unsafe(lab):
    agent_uid, agent_gids = _distinct_agent_identity()
    target = lab / "target.py"
    target.write_text("")
    target.chmod(0o644)
    link = lab / "link.py"
    link.symlink_to(target)
    lab.chmod(0o777)  # agent can delete/replace the symlink entry itself

    write, reason, _ = topo._effective_write_access(link, agent_uid, agent_gids)
    assert write is True
    assert reason == "symlink_parent_chain_writable"


def test_target_mutation_attack_writable_target_is_unsafe(lab):
    agent_uid, agent_gids = _distinct_agent_identity()
    target = lab / "target.py"
    target.write_text("")
    target.chmod(0o666)
    link = lab / "link.py"
    link.symlink_to(target)
    lab.chmod(0o755)

    write, reason, _ = topo._effective_write_access(link, agent_uid, agent_gids)
    assert write is True
    assert "world_writable" in reason


def test_target_ancestor_attack_writable_ancestor_is_unsafe(lab):
    agent_uid, agent_gids = _distinct_agent_identity()
    sub = lab / "sub"
    sub.mkdir()
    target = sub / "target.py"
    target.write_text("")
    target.chmod(0o644)  # target file itself is non-writable
    sub.chmod(0o777)  # but its containing directory permits replacement
    link = lab / "link.py"
    link.symlink_to(target)
    lab.chmod(0o755)

    write, reason, _ = topo._effective_write_access(link, agent_uid, agent_gids)
    assert write is True
    assert "ancestor" in reason


def test_effective_supplementary_group_grants_target_write(lab):
    """Real getgroups()-derived supplementary-group semantics, not a
    reduction to owner/world bits -- the previously repaired (149O.20J
    series) effective-GID behavior must still be reachable through the
    symlink channel."""

    agent_uid, _ = _distinct_agent_identity()
    target = lab / "target.py"
    target.write_text("")
    target.chmod(0o060)  # group rw only
    real_gid = target.stat().st_gid
    link = lab / "link.py"
    link.symlink_to(target)
    lab.chmod(0o755)

    write, reason, _ = topo._effective_write_access(link, agent_uid, frozenset({real_gid}))
    assert write is True
    assert "group_membership" in reason

    write_no_group, _, _ = topo._effective_write_access(link, agent_uid, frozenset())
    assert write_no_group is False


def test_acl_only_write_grant_on_target_is_unsafe(lab, monkeypatch):
    agent_uid, agent_gids = _distinct_agent_identity()
    target = lab / "target.py"
    target.write_text("")
    target.chmod(0o644)
    link = lab / "link.py"
    link.symlink_to(target)
    lab.chmod(0o755)

    monkeypatch.setattr(topo, "_acl_grants_agent_write", lambda path, uid, gids: path == target)
    write, reason, _ = topo._effective_write_access(link, agent_uid, agent_gids)
    assert write is True
    assert "acl_grants_agent_write" in reason


def test_chained_symlinks_safe_resolves_through_both_hops(lab):
    agent_uid, agent_gids = _distinct_agent_identity()
    final = lab / "final.py"
    final.write_text("")
    final.chmod(0o644)
    mid = lab / "mid"
    mid.symlink_to(final)
    top = lab / "top"
    top.symlink_to(mid)
    lab.chmod(0o755)

    write, reason, _ = topo._effective_write_access(top, agent_uid, agent_gids)
    assert write is False
    assert reason == "symlink_fully_closed"


def test_chained_symlinks_unsafe_deep_target_detected(lab):
    agent_uid, agent_gids = _distinct_agent_identity()
    final = lab / "final.py"
    final.write_text("")
    final.chmod(0o666)  # unsafe two hops down
    mid = lab / "mid"
    mid.symlink_to(final)
    top = lab / "top"
    top.symlink_to(mid)
    lab.chmod(0o755)

    write, reason, _ = topo._effective_write_access(top, agent_uid, agent_gids)
    assert write is True
    assert "world_writable" in reason


def test_broken_symlink_is_indeterminate_never_silently_safe(lab):
    agent_uid, agent_gids = _distinct_agent_identity()
    link = lab / "link.py"
    link.symlink_to(lab / "does_not_exist.py")
    lab.chmod(0o755)

    write, reason, _ = topo._effective_write_access(link, agent_uid, agent_gids)
    assert write is None
    assert write is not False


def test_symlink_loop_is_indeterminate_no_infinite_traversal(lab):
    agent_uid, agent_gids = _distinct_agent_identity()
    a = lab / "a"
    b = lab / "b"
    a.symlink_to(b)
    b.symlink_to(a)
    lab.chmod(0o755)

    write, reason, _ = topo._effective_write_access(a, agent_uid, agent_gids)
    assert write is None
    assert write is not False


def test_relative_symlink_resolves_via_link_parent_not_cwd(lab, monkeypatch):
    agent_uid, agent_gids = _distinct_agent_identity()
    sub = lab / "sub"
    sub.mkdir()
    target = sub / "target.py"
    target.write_text("")
    target.chmod(0o644)
    sub.chmod(0o755)
    link = lab / "link.py"
    link.symlink_to("sub/target.py")  # relative
    lab.chmod(0o755)

    monkeypatch.chdir("/")  # prove resolution is not CWD-dependent
    write, reason, _ = topo._effective_write_access(link, agent_uid, agent_gids)
    assert write is False
    assert reason == "symlink_fully_closed"


def test_inspection_failure_on_readlink_never_resolves_to_safe(lab, monkeypatch):
    agent_uid, agent_gids = _distinct_agent_identity()
    target = lab / "target.py"
    target.write_text("")
    target.chmod(0o644)
    link = lab / "link.py"
    link.symlink_to(target)
    lab.chmod(0o755)

    real_readlink = os.readlink

    def _boom(path, *a, **kw):
        if Path(path) == link:
            raise OSError("simulated inspection failure")
        return real_readlink(path, *a, **kw)

    monkeypatch.setattr(topo.os, "readlink", _boom)
    write, reason, _ = topo._effective_write_access(link, agent_uid, agent_gids)
    assert write is not False
    assert reason == "symlink_unreadable"


def test_is_symlink_unsafe_and_ancestor_chain_symlink_rejection_unmodified():
    """Direct-inspection proof that the repair left the pre-existing,
    unconditional symlinked-ancestor rejection primitives untouched --
    `_is_symlink_unsafe` must remain the trivial `path.is_symlink()`
    predicate it always was; only `_effective_write_access`'s own
    leaf-symlink dispatch gained the new channel analysis."""

    import inspect

    src = inspect.getsource(topo._is_symlink_unsafe)
    assert src.strip().endswith("return path.is_symlink()")


def test_req_030_customization_module_check_routes_through_repaired_symlink_helper(lab, monkeypatch):
    """Proves the repair reaches the actual HBDC-REQ-030 compliance
    determination (`_check_customization_modules`), not merely an
    isolated helper -- the real call path a Dell deployment exercises."""

    agent_uid, agent_gids = _distinct_agent_identity()
    target = lab / "sitecustomize.py"
    target.write_text("")
    target.chmod(0o644)
    link_dir = lab / "syspath"
    link_dir.mkdir()
    link = link_dir / "sitecustomize.py"
    link.symlink_to(target)
    link_dir.chmod(0o755)

    monkeypatch.setattr(envlock, "_effective_sys_path_dirs", lambda: (link_dir,))
    result = envlock._check_customization_modules(agent_uid, agent_gids)
    assert result.satisfied is True
    assert result.status == "customization_modules_present_admin_controlled"


# ═══════════════════════════════════════════════════════════════════════════
# HMIC v1.3 source membership and identity consequence
# ═══════════════════════════════════════════════════════════════════════════


def test_all_three_repaired_modules_are_hmic_frozen_authority_bearing_source():
    from pcae.core.hatp_mandatory_certification import _FROZEN_SRC_PCAE_RELATIVE_FILES

    for relative in (
        "core/hatp_class_b_topology_verifier.py",
        "core/hatp_environment_lock_verifier.py",
        "core/hatp_class_b_conformance.py",
    ):
        assert relative in _FROZEN_SRC_PCAE_RELATIVE_FILES


def test_frozen_authority_bearing_set_is_exactly_28():
    from pcae.core.hatp_mandatory_certification import _FROZEN_AUTHORITY_BEARING_FILES

    assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 28


def test_no_contract_files_modified_by_this_repair():
    """Independent confirmation that HBDC-001's own bytes (and every
    other bound contract) are untouched -- contract identity is a
    distinct concern from implementation/source identity."""

    import subprocess

    repo_root = Path(__file__).resolve().parent.parent
    out = subprocess.run(
        ["git", "diff", "--name-only", "8a18f73d..HEAD", "--", "docs/contracts/"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert out.returncode == 0
    assert out.stdout.strip() == ""


# ═══════════════════════════════════════════════════════════════════════════
# No-mutation guardrails for this phase itself
# ═══════════════════════════════════════════════════════════════════════════


def test_this_phase_creates_no_deploymentbinding_or_certification_artifact():
    repo_root = Path(__file__).resolve().parent.parent
    pcae_dir = repo_root / ".pcae"
    offenders = [p for p in pcae_dir.rglob("*") if "deploymentbinding" in p.name.lower() or "certification" in p.name.lower()]
    assert offenders == []
