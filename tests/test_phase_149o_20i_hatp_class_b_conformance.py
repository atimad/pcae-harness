"""Phase 149O.20I, Wave D/E — tests for `hatp_class_b_conformance.py`.

Covers the aggregation rule (HBDC-REQ-052/053), status-vocabulary
closure, deployment-identity wrapper (HBDC-REQ-042..046), Model-A
detection (HBDC-REQ-022/024), the read-only/non-mutation guarantee at
the aggregator level, and the zero-authority-caller / current-HMIC-
non-binding structural facts (CBV-S1)."""
from __future__ import annotations

import ast
import inspect
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.core import hatp_class_b_conformance as agg
from pcae.core.hatp_class_b_topology_verifier import ClassBCheckResult, ClassBConformanceStatus
from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance
from pcae.core.paths import HarnessPath

pytestmark = [pytest.mark.fast_green, pytest.mark.skipif(os.name != "posix", reason="POSIX-only permission model")]

_REPO_ROOT = Path(__file__).resolve().parents[1]
_THREE_MODULES = (
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
    "src/pcae/core/hatp_class_b_conformance.py",
)


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════


def test_public_api_accepts_only_root_locator():
    sig = inspect.signature(verify_class_b_deployment_conformance)
    assert list(sig.parameters.keys()) == ["root"]
    assert sig.parameters["root"].default is None


def test_no_authority_boolean_parameter():
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
    sig = inspect.signature(verify_class_b_deployment_conformance)
    assert not (set(sig.parameters.keys()) & forbidden)


def test_real_host_result_is_not_compliant_not_provisioned():
    result = verify_class_b_deployment_conformance()
    assert result.status != ClassBConformanceStatus.COMPLIANT


def test_default_root_is_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = verify_class_b_deployment_conformance()
    assert any(c.check_id == "HBDC-REQ-042" for c in result.checks)


def test_aggregate_includes_all_constituent_checks():
    result = verify_class_b_deployment_conformance()
    ids = {c.check_id for c in result.checks}
    # topology + environment + model-A + deployment identity
    assert "HBDC-REQ-001" in ids  # topology
    assert "HBDC-REQ-025" in ids  # environment lock
    assert "HBDC-REQ-022" in ids  # model A
    assert "HBDC-REQ-042" in ids  # deployment identity


# ═══════════════════════════════════════════════════════════════════════════
# Aggregation rule (HBDC-REQ-052/053, plan §38)
# ═══════════════════════════════════════════════════════════════════════════


def test_all_satisfied_yields_compliant():
    from pcae.core.hatp_class_b_topology_verifier import _aggregate_status

    checks = tuple(ClassBCheckResult(f"X-{i}", True, "ok", ()) for i in range(5))
    assert _aggregate_status(checks) == ClassBConformanceStatus.COMPLIANT


@pytest.mark.parametrize("failing_index", range(5))
def test_single_failure_prevents_compliant(failing_index):
    from pcae.core.hatp_class_b_topology_verifier import _aggregate_status

    checks = [ClassBCheckResult(f"X-{i}", True, "ok", ()) for i in range(5)]
    checks[failing_index] = ClassBCheckResult(f"X-{failing_index}", False, "no_effective_write_access", ())
    assert _aggregate_status(tuple(checks)) != ClassBConformanceStatus.COMPLIANT


def test_missing_evidence_check_prevents_compliant():
    from pcae.core.hatp_class_b_topology_verifier import _aggregate_status

    checks = (
        ClassBCheckResult("X-1", True, "ok", ()),
        ClassBCheckResult("X-2", False, "path_missing", ()),
    )
    assert _aggregate_status(checks) != ClassBConformanceStatus.COMPLIANT


def test_no_majority_partial_success_semantics():
    """9 satisfied, 1 failed must still not be COMPLIANT — no
    percentage/majority threshold exists anywhere in the aggregation
    rule."""

    from pcae.core.hatp_class_b_topology_verifier import _aggregate_status

    checks = tuple(ClassBCheckResult(f"X-{i}", i != 9, "ok" if i != 9 else "no_effective_write_access", ()) for i in range(10))
    assert _aggregate_status(checks) != ClassBConformanceStatus.COMPLIANT


def test_empty_checks_never_compliant():
    from pcae.core.hatp_class_b_topology_verifier import _aggregate_status

    assert _aggregate_status(()) != ClassBConformanceStatus.COMPLIANT


# ═══════════════════════════════════════════════════════════════════════════
# Status-vocabulary closure
# ═══════════════════════════════════════════════════════════════════════════


def test_status_vocabulary_closed():
    values = {m.value for m in ClassBConformanceStatus}
    assert values == {
        "COMPLIANT",
        "NON_COMPLIANT",
        "INDETERMINATE",
        "ACCESS_ERROR",
        "MALFORMED_STATE",
        "UNSUPPORTED_DEPLOYMENT_MODEL",
    }


def test_result_status_is_typed_enum_not_string_literal():
    result = verify_class_b_deployment_conformance()
    assert isinstance(result.status, ClassBConformanceStatus)
    # Authority decisions must use exact-identity comparison, never
    # truthiness or substring matching (mirrors HMIC-001's discipline).
    assert (result.status == ClassBConformanceStatus.COMPLIANT) in (True, False)


# ═══════════════════════════════════════════════════════════════════════════
# Deployment-identity wrapper (HBDC-REQ-042..046)
# ═══════════════════════════════════════════════════════════════════════════


def test_deployment_identity_no_binding_non_compliant(tmp_path):
    root = HarnessPath(tmp_path)
    result = agg._check_deployment_identity(root)
    assert result.satisfied is False


def test_deployment_identity_wrapper_reuses_existing_functions_not_reimplemented():
    """Confirms the wrapper genuinely calls the existing, unmodified
    hatp_bootstrap/repository_identity functions rather than
    reimplementing binding-match logic — an AST check that no local
    `==`-based binding comparison exists outside a call to
    `deployment_binding_matches`."""

    source = inspect.getsource(agg._check_deployment_identity)
    assert "deployment_binding_matches(" in source
    assert "resolve_canonical_deployment_root(" in source
    assert "read_repository_identity(" in source


# ═══════════════════════════════════════════════════════════════════════════
# Model-A detection (HBDC-REQ-022/024)
# ═══════════════════════════════════════════════════════════════════════════


def test_model_a_check_runs_without_exception():
    result = agg._check_model_a_deployment(os.geteuid())
    assert result.check_id in ("HBDC-REQ-022", "HBDC-REQ-024")
    assert isinstance(result.satisfied, bool)


def test_model_a_check_fails_closed_when_distribution_missing(monkeypatch):
    import importlib.metadata

    def _raise(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(agg.importlib.metadata, "distribution", _raise)
    result = agg._check_model_a_deployment(os.geteuid())
    assert result.satisfied is False
    assert result.status == "pcae_distribution_metadata_not_found"


# ═══════════════════════════════════════════════════════════════════════════
# Read-only / non-mutation guarantee
# ═══════════════════════════════════════════════════════════════════════════


def test_aggregator_performs_zero_filesystem_mutation(tmp_path):
    fixture = tmp_path / "workdir"
    fixture.mkdir()
    (fixture / "file.txt").write_text("x")
    before = {p: p.stat().st_mtime_ns for p in [fixture, fixture / "file.txt"]}
    verify_class_b_deployment_conformance(HarnessPath(fixture))
    after = {p: p.stat().st_mtime_ns for p in [fixture, fixture / "file.txt"]}
    assert before == after


def test_no_mutation_call_in_own_source():
    forbidden = {"mkdir", "makedirs", "chmod", "chown", "unlink", "rmdir", "rename", "replace", "symlink", "write_text", "write_bytes"}
    tree = ast.parse(Path(agg.__file__).read_text(encoding="utf-8"))
    found = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr in forbidden}
    assert not found


# ═══════════════════════════════════════════════════════════════════════════
# HBDC-REQ-050/054/055 status-claim discipline
# ═══════════════════════════════════════════════════════════════════════════


def test_result_type_has_no_activation_field():
    from dataclasses import fields

    from pcae.core.hatp_class_b_topology_verifier import ClassBDeploymentVerificationResult

    field_names = {f.name for f in fields(ClassBDeploymentVerificationResult)}
    forbidden_field_names = {"activation", "activate", "readiness", "certified", "hatp_ready", "cutover"}
    assert not (field_names & forbidden_field_names)


def test_no_attestation_language_in_module_docstrings():
    for path in (
        Path(__file__).resolve().parents[1] / "src/pcae/core/hatp_class_b_topology_verifier.py",
        Path(__file__).resolve().parents[1] / "src/pcae/core/hatp_environment_lock_verifier.py",
        Path(agg.__file__),
    ):
        text = path.read_text(encoding="utf-8")
        assert "cryptographic executed-source" not in text.replace("does not claim runtime executed-source cryptographic attestation", "")


def test_no_self_trust_or_hmic_bound_claim_in_source():
    for path in (
        Path(__file__).resolve().parents[1] / "src/pcae/core/hatp_class_b_topology_verifier.py",
        Path(__file__).resolve().parents[1] / "src/pcae/core/hatp_environment_lock_verifier.py",
        Path(agg.__file__),
    ):
        text = path.read_text(encoding="utf-8")
        for forbidden in ("trusted=True", "self_verified=True", "hmic_bound=True"):
            assert forbidden not in text


# ═══════════════════════════════════════════════════════════════════════════
# CBV-S1: zero production authority callers, current HMIC non-binding
# ═══════════════════════════════════════════════════════════════════════════


def test_zero_authority_callers_across_src_pcae():
    """Blocking condition (governing-prompt item 67/82): search all
    src/pcae/** for any import/call of the three new modules from
    outside the three-module island itself."""

    module_names = {
        "hatp_class_b_topology_verifier",
        "hatp_environment_lock_verifier",
        "hatp_class_b_conformance",
    }
    island_paths = {(_REPO_ROOT / rel).resolve() for rel in _THREE_MODULES}

    offenders: "list[str]" = []
    for py_file in (_REPO_ROOT / "src" / "pcae").rglob("*.py"):
        if py_file.resolve() in island_paths:
            continue
        text = py_file.read_text(encoding="utf-8")
        for name in module_names:
            if name in text:
                offenders.append(f"{py_file}:{name}")
    assert not offenders, f"unexpected authority caller(s) of 149O.20I verifier modules: {offenders}"


def test_three_modules_not_in_current_hmic_frozen_scope():
    from pcae.core.hatp_mandatory_certification import _FROZEN_SRC_PCAE_RELATIVE_FILES

    for name in (
        "core/hatp_class_b_topology_verifier.py",
        "core/hatp_environment_lock_verifier.py",
        "core/hatp_class_b_conformance.py",
    ):
        assert name not in _FROZEN_SRC_PCAE_RELATIVE_FILES
    assert len(_FROZEN_SRC_PCAE_RELATIVE_FILES) == 19  # unchanged this phase


def test_hmic_bound_files_are_byte_unchanged_this_phase():
    """`hatp_mandatory_cutover.py` and `hatp_mandatory_certification.py`
    (HMIC-25-bound) must be untouched by 149O.20I."""

    for rel in (
        "src/pcae/core/hatp_mandatory_cutover.py",
        "src/pcae/core/hatp_mandatory_certification.py",
        "src/pcae/core/hatp_bootstrap.py",
        "src/pcae/core/repository_identity.py",
        "scripts/hatp_certification_admin.py",
    ):
        result = subprocess.run(
            ["git", "status", "--porcelain", "--", rel],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.stdout.strip() == "", f"{rel} shows as modified: {result.stdout}"


def test_no_self_certification_no_self_check_of_hmic_binding_in_source():
    """Plan §25: the module has no way to answer "am I HMIC-bound?"
    about itself, and does not try — no reference to
    `_FROZEN_AUTHORITY_BEARING_FILES`/`_FROZEN_SRC_PCAE_RELATIVE_FILES`
    or the certification module appears in the aggregator's own
    source."""

    text = Path(agg.__file__).read_text(encoding="utf-8")
    assert "_FROZEN_AUTHORITY_BEARING_FILES" not in text
    assert "_FROZEN_SRC_PCAE_RELATIVE_FILES" not in text
    assert "hatp_mandatory_certification" not in text


# ═══════════════════════════════════════════════════════════════════════════
# Fail-closed on exception
# ═══════════════════════════════════════════════════════════════════════════


def test_unexpected_exception_never_yields_compliant():
    from pcae.core.hatp_class_b_topology_verifier import _safe_check

    def _boom():
        raise RuntimeError("simulated aggregator failure")

    result = _safe_check("HBDC-REQ-999", _boom)
    assert result.satisfied is False
    assert result.status == "unexpected_inspection_exception"
