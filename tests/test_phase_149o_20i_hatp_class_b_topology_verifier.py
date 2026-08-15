"""Phase 149O.20I, Wave B — tests for `hatp_class_b_topology_verifier.py`.

Covers HBDC-REQ-001..021 against isolated filesystem fixtures (never a
real Class-B host). Mirrors HBDC-001 §61's disclosed limitation: these
fixture tests prove the verifier's *logic* is correct; they are not a
substitute for real-host effective-access proof (deferred, separate
infrastructure wave, not this phase)."""
from __future__ import annotations

import inspect
import os
import stat
from pathlib import Path

import pytest

from pcae.core import hatp_class_b_topology_verifier as v
from pcae.core.hatp_class_b_topology_verifier import (
    ClassBConformanceStatus,
    ClassBDeploymentVerificationResult,
    verify_class_b_topology_conformance,
)

pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]


def _agent_uid_gids() -> "tuple[int, frozenset[int]]":
    return os.geteuid(), frozenset(os.getgroups())


def _stat_snapshot(root: Path) -> dict:
    snapshot = {}
    for path in [root, *root.rglob("*")]:
        try:
            st = path.stat()
        except OSError:
            continue
        snapshot[str(path)] = (st.st_mode, st.st_mtime_ns, st.st_size)
    return snapshot


# ═══════════════════════════════════════════════════════════════════════════
# Result model / status vocabulary
# ═══════════════════════════════════════════════════════════════════════════


def test_result_model_shape():
    result = verify_class_b_topology_conformance()
    assert isinstance(result, ClassBDeploymentVerificationResult)
    assert isinstance(result.status, ClassBConformanceStatus)
    assert isinstance(result.checks, tuple)
    assert isinstance(result.reasons, tuple)
    assert isinstance(result.evidence, tuple)


def test_status_vocabulary_is_closed():
    values = {member.value for member in ClassBConformanceStatus}
    assert values == {
        "COMPLIANT",
        "NON_COMPLIANT",
        "INDETERMINATE",
        "ACCESS_ERROR",
        "MALFORMED_STATE",
        "UNSUPPORTED_DEPLOYMENT_MODEL",
    }


def test_only_compliant_is_positive():
    assert ClassBConformanceStatus.COMPLIANT.value == "COMPLIANT"
    non_positive = set(ClassBConformanceStatus) - {ClassBConformanceStatus.COMPLIANT}
    assert len(non_positive) == 5


# ═══════════════════════════════════════════════════════════════════════════
# Public API — no caller-supplied authority
# ═══════════════════════════════════════════════════════════════════════════


def test_public_api_accepts_zero_parameters():
    sig = inspect.signature(verify_class_b_topology_conformance)
    assert len(sig.parameters) == 0


def test_no_authority_boolean_anywhere_in_public_functions():
    forbidden = {
        "is_admin",
        "permissions_ok",
        "environment_locked",
        "module_origin_ok",
        "git_trusted",
        "deployment_valid",
        "compliant",
        "expected_uid",
        "expected_root",
    }
    sig = inspect.signature(verify_class_b_topology_conformance)
    assert not (set(sig.parameters.keys()) & forbidden)


def test_real_host_result_is_not_compliant_not_provisioned():
    """§53 expectation: current dev host has no real Protected Root."""

    result = verify_class_b_topology_conformance()
    assert result.status != ClassBConformanceStatus.COMPLIANT


def test_all_hbdc_req_rows_present():
    result = verify_class_b_topology_conformance()
    ids = {c.check_id for c in result.checks}
    expected = {
        "HBDC-REQ-001",
        "HBDC-REQ-002",
        "HBDC-REQ-004",
        "HBDC-REQ-005",
        "HBDC-REQ-007",
        "HBDC-REQ-008",
        "HBDC-REQ-011",
        "HBDC-REQ-012",
        "HBDC-REQ-013",
        "HBDC-REQ-014",
        "HBDC-REQ-015",
        "HBDC-REQ-016",
        "HBDC-REQ-017",
        "HBDC-REQ-018",
        "HBDC-REQ-019",
        "HBDC-REQ-020",
        "HBDC-REQ-021",
    }
    assert expected <= ids


# ═══════════════════════════════════════════════════════════════════════════
# Effective-access primitive
# ═══════════════════════════════════════════════════════════════════════════


def test_effective_write_access_owner_write_bit(tmp_path):
    target = tmp_path / "owned"
    target.mkdir()
    agent_uid, agent_gids = _agent_uid_gids()
    write, reason, _ = v._effective_write_access(target, agent_uid, agent_gids)
    assert write is True
    assert reason == "agent_is_owner_with_write_bit"


def test_effective_write_access_no_write_when_mode_locked(tmp_path, monkeypatch):
    target = tmp_path / "locked"
    target.mkdir()
    target.chmod(0o500)  # r-x for owner, nothing for group/other
    monkeypatch.setattr(v, "_acl_grants_agent_write", lambda path, uid, gids: False)
    try:
        agent_uid, agent_gids = _agent_uid_gids()
        write, _reason, _ = v._effective_write_access(target, agent_uid, agent_gids)
        assert write is False
    finally:
        target.chmod(0o700)


def test_effective_write_access_group_membership(tmp_path, monkeypatch):
    target = tmp_path / "group_writable"
    target.mkdir()
    st = target.stat()
    monkeypatch.setattr(v.os, "getgroups", lambda: [st.st_gid])
    monkeypatch.setattr(v.os, "geteuid", lambda: st.st_uid + 1)
    target.chmod(0o070)
    try:
        agent_uid = st.st_uid + 1
        agent_gids = frozenset({st.st_gid})
        write, reason, _ = v._effective_write_access(target, agent_uid, agent_gids)
        assert write is True
        assert reason == "agent_group_membership_grants_write"
    finally:
        target.chmod(0o700)


def test_effective_write_access_world_writable(tmp_path):
    target = tmp_path / "world"
    target.mkdir()
    target.chmod(0o707)
    try:
        real_owner_uid = target.stat().st_uid
        fake_agent_uid = real_owner_uid + 1  # simulate a non-owning agent principal
        write, reason, _ = v._effective_write_access(target, fake_agent_uid, frozenset())
        assert write is True
        assert reason == "world_writable"
    finally:
        target.chmod(0o700)


def test_effective_write_access_missing_path(tmp_path):
    write, reason, _ = v._effective_write_access(tmp_path / "nope", *_agent_uid_gids())
    assert write is None
    assert reason == "path_missing"


def test_effective_write_access_symlink_writable_parent_fails_closed(tmp_path):
    """149O.20L.7D.7 repair (B-149O.20L.7D.6-3): a symlink whose parent
    directory is agent-writable is still unsafe (the agent could delete
    and replace the symlink entry itself), but the reason code is now the
    specific channel found unsafe, not an unconditional literal — see the
    genuinely-safe-symlink coverage in
    tests/test_phase_149o_20l_7d_7_class_b_verifier_narrow_source_repair.py."""
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    write, reason, _ = v._effective_write_access(link, *_agent_uid_gids())
    assert write is True
    assert reason == "symlink_parent_chain_writable"


# ═══════════════════════════════════════════════════════════════════════════
# Ancestor-chain walk
# ═══════════════════════════════════════════════════════════════════════════


def test_ancestor_chain_safe_boundary(tmp_path, monkeypatch):
    """149O.20J.3: the repaired walk inspects every ancestor up to the
    real filesystem root, so a positive (fully-safe) case must prove
    every level is non-writable -- including ancestors above `tmp_path`
    itself, which real test hosts normally leave agent-owned/writable.
    Rather than depending on the real host's directory tree above
    `tmp_path` (environment-dependent, not deterministic), this test
    stubs `_effective_write_access` to apply real stat-based logic only
    within the constructed fixture and to report a deterministic safe
    result for everything above it -- simulating an admin-controlled
    boundary the same way Protected Root's real ancestors (e.g. `/etc`,
    `/Library/Application Support`) are admin-owned in production."""

    monkeypatch.setattr(v, "_acl_grants_agent_write", lambda path, uid, gids: False)
    protected_parent = tmp_path / "parent"
    protected_parent.mkdir()
    child = protected_parent / "child"
    child.mkdir()
    protected_parent.chmod(0o500)
    child.chmod(0o500)

    real_effective_write_access = v._effective_write_access

    def _stubbed_effective_write_access(path, agent_uid, agent_gids):
        if path == tmp_path or tmp_path not in path.parents:
            return False, "outside_fixture_treated_as_admin_boundary", ()
        return real_effective_write_access(path, agent_uid, agent_gids)

    monkeypatch.setattr(v, "_effective_write_access", _stubbed_effective_write_access)
    try:
        safe, diag = v._ancestor_chain_safe(child, *_agent_uid_gids())
        assert safe is True
        assert any("ancestor_safe" in d and str(protected_parent) in d for d in diag)
    finally:
        child.chmod(0o700)
        protected_parent.chmod(0o700)


def test_ancestor_chain_writable_immediate_parent_non_compliant(tmp_path, monkeypatch):
    """Attack #4: agent-writable immediate parent lets the agent
    rename/replace the directory entry naming the protected child, even
    if the child's own mode bits look safe. The walk must not stop
    early at a proven-safe *child* mode — it inspects ancestors, and an
    agent-writable ancestor is decisive regardless of any ancestor
    further up the chain."""

    monkeypatch.setattr(v, "_acl_grants_agent_write", lambda path, uid, gids: False)
    parent = tmp_path / "parent"  # tmp_path itself is agent-owned/writable
    child = parent / "child"
    child.mkdir(parents=True)
    child.chmod(0o500)
    try:
        safe, diagnostics = v._ancestor_chain_safe(child, *_agent_uid_gids())
        assert safe is False
        assert any("ancestor_writable" in d for d in diagnostics)
    finally:
        child.chmod(0o700)


def test_ancestor_chain_symlink_ancestor_non_compliant(tmp_path):
    real_dir = tmp_path / "real_ancestor"
    real_dir.mkdir()
    link_dir = tmp_path / "link_ancestor"
    link_dir.symlink_to(real_dir)
    child = link_dir / "child"
    (real_dir / "child").mkdir()
    safe, diagnostics = v._ancestor_chain_safe(child, *_agent_uid_gids())
    assert safe is False
    assert any("ancestor_symlink" in d for d in diagnostics)


# ═══════════════════════════════════════════════════════════════════════════
# Hard-link check
# ═══════════════════════════════════════════════════════════════════════════


def test_hard_link_single_link_safe(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("x")
    safe, reason = v._hard_link_safe(target)
    assert safe is True
    assert reason == "single_link"


def test_hard_link_multiple_links_non_compliant(tmp_path):
    target = tmp_path / "file.txt"
    target.write_text("x")
    alias = tmp_path / "alias.txt"
    os.link(target, alias)
    safe, reason = v._hard_link_safe(target)
    assert safe is False
    assert reason == "multiple_hard_links"


def test_hard_link_missing_path(tmp_path):
    safe, reason = v._hard_link_safe(tmp_path / "nope.txt")
    assert safe is None
    assert reason == "path_missing_or_symlink"


# ═══════════════════════════════════════════════════════════════════════════
# Protected Root scenario checks (via internal helpers directly, since
# the public API is fixed to the real production root)
# ═══════════════════════════════════════════════════════════════════════════


def test_missing_root_fails_closed_never_auto_provisions(tmp_path):
    """Attack #7: root absent; verifier never auto-provisions it."""

    fake_root = tmp_path / "trust-store"
    assert not fake_root.exists()
    result = v._check_two_principal_topology(fake_root)
    assert result.satisfied is False
    assert not fake_root.exists()  # verifier performed zero mutation


def test_principal_distinctness_same_uid_non_compliant(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    agent_uid = os.geteuid()
    result = v._check_principal_distinctness(root, agent_uid)
    assert result.satisfied is False
    assert result.status == "agent_and_admin_share_os_principal"


def test_root_mode_group_writable_non_compliant(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    root.chmod(0o770)
    try:
        result = v._check_root_mode(root)
        assert result.satisfied is False
    finally:
        root.chmod(0o700)


def test_root_mode_locked_down_compliant(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    root.chmod(0o700)
    result = v._check_root_mode(root)
    assert result.satisfied is True


def test_root_symlink_non_compliant(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    result = v._check_symlink_safety(link)
    assert result.satisfied is False
    assert result.status == "protected_root_is_symlink"


def test_registry_hard_linked_non_compliant(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    registry = root / "registry.json"
    registry.write_text("{}")
    alias = tmp_path / "alias.json"
    os.link(registry, alias)
    result = v._check_hard_link_safety(root)
    assert result.satisfied is False


def test_registry_absent_hard_link_check_vacuously_true(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    result = v._check_hard_link_safety(root)
    assert result.satisfied is True


# ═══════════════════════════════════════════════════════════════════════════
# Read-only-mutation guard (§18)
# ═══════════════════════════════════════════════════════════════════════════


def test_verifier_performs_zero_filesystem_mutation(tmp_path):
    fixture_root = tmp_path / "fixture-tree"
    fixture_root.mkdir()
    (fixture_root / "sub").mkdir()
    (fixture_root / "sub" / "file.txt").write_text("data")

    before = _stat_snapshot(fixture_root)
    v._check_two_principal_topology(fixture_root / "not-real-root")
    v._effective_write_access(fixture_root, *_agent_uid_gids())
    v._ancestor_chain_safe(fixture_root / "sub", *_agent_uid_gids())
    v._hard_link_safe(fixture_root / "sub" / "file.txt")
    after = _stat_snapshot(fixture_root)
    assert before == after


def test_full_verifier_run_performs_zero_source_mutation(tmp_path):
    """Runs the full public API and confirms this module's own source
    file is untouched — the strongest available proxy for "the verifier
    never writes" without a real Protected Root fixture."""

    source = Path(v.__file__)
    before_stat = source.stat()
    verify_class_b_topology_conformance()
    after_stat = source.stat()
    assert before_stat.st_mtime_ns == after_stat.st_mtime_ns
    assert before_stat.st_size == after_stat.st_size


# ═══════════════════════════════════════════════════════════════════════════
# Fail-closed on exception
# ═══════════════════════════════════════════════════════════════════════════


def test_safe_check_catches_exception_never_compliant():
    def _boom():
        raise RuntimeError("simulated inspection failure")

    result = v._safe_check("HBDC-REQ-999", _boom)
    assert result.satisfied is False
    assert result.status == "unexpected_inspection_exception"


# ═══════════════════════════════════════════════════════════════════════════
# Static self-checks (HBDC-REQ-004/005/012)
# ═══════════════════════════════════════════════════════════════════════════


def test_no_self_trust_claim_in_source():
    source_text = Path(v.__file__).read_text(encoding="utf-8")
    for forbidden in ("trusted=True", "self_verified=True", "hmic_bound=True"):
        assert forbidden not in source_text


def test_no_mutation_call_in_own_source():
    result = v._check_read_only_guarantee()
    assert result.satisfied is True


def test_no_admin_inference_call_in_own_source():
    result = v._check_no_env_or_name_based_admin_inference()
    assert result.satisfied is True


def test_no_self_elevation_call_in_own_source():
    result = v._check_no_self_elevation_path()
    assert result.satisfied is True


def test_current_module_not_in_hmic_frozen_scope():
    """HBDC-REQ scope-boundary check (CBV-S1): this module's own path
    must not currently appear in HMIC-001's frozen 25-file set."""

    from pcae.core.hatp_mandatory_certification import _FROZEN_SRC_PCAE_RELATIVE_FILES

    assert "core/hatp_class_b_topology_verifier.py" not in _FROZEN_SRC_PCAE_RELATIVE_FILES


# ═══════════════════════════════════════════════════════════════════════════
# Aggregation rule (module-local: exercised again at the aggregator
# level in test_phase_149o_20i_hatp_class_b_conformance.py)
# ═══════════════════════════════════════════════════════════════════════════


def test_aggregation_all_satisfied_yields_compliant():
    checks = (v.ClassBCheckResult("X-1", True, "ok", ()), v.ClassBCheckResult("X-2", True, "ok", ()))
    assert v._aggregate_status(checks) == ClassBConformanceStatus.COMPLIANT


def test_aggregation_single_failure_prevents_compliant():
    checks = (v.ClassBCheckResult("X-1", True, "ok", ()), v.ClassBCheckResult("X-2", False, "no_effective_write_access", ()))
    assert v._aggregate_status(checks) != ClassBConformanceStatus.COMPLIANT


def test_aggregation_indeterminate_check_prevents_compliant():
    checks = (v.ClassBCheckResult("X-1", True, "ok", ()), v.ClassBCheckResult("X-2", False, "indeterminate:acl_unavailable", ()))
    status = v._aggregate_status(checks)
    assert status != ClassBConformanceStatus.COMPLIANT
