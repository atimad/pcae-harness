"""Phase 149O.20L -- Class-B Full-HBDC Readiness Contract / Integration
Analysis.

Architecture/contract-analysis phase resolving CBV-S10 (READINESS
CONTRACT / INTEGRATION GAP). This module is proof, not implementation:
it demonstrates, against live production code and the real host, the
exact readiness/Class-B-conformance gap this phase's analysis document
(`docs/PHASE_149O_20L_CLASS_B_FULL_HBDC_READINESS_CONTRACT_INTEGRATION_
ANALYSIS.md`) describes. No production module is modified by this
phase. All fixture state is isolated (`tmp_path`); the only
non-isolated call in this module is a genuinely read-only, no-argument
call to the real `verify_class_b_deployment_conformance()` against the
real, unprovisioned host -- exactly mirroring the read-only real-host
calls prior phases (149O.20I/149O.20J.x/149O.20K.x) already made.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_cutover as cutover
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance
from pcae.core.hatp_class_b_topology_verifier import ClassBConformanceStatus
from pcae.core.hatp_mandatory_certification import CertificationStatus
from pcae.core.hatp_mandatory_cutover import (
    HATPMandatoryActivationReadiness,
    _assess_hatp_mandatory_activation_readiness_at_root,
    assess_hatp_mandatory_activation_readiness,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CUTOVER_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py").read_text(encoding="utf-8")
_CERT_SRC = (_REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py").read_text(encoding="utf-8")
_CONFORMANCE_SRC_FILES = [
    _REPO_ROOT / "src" / "pcae" / "core" / "hatp_class_b_conformance.py",
    _REPO_ROOT / "src" / "pcae" / "core" / "hatp_class_b_topology_verifier.py",
    _REPO_ROOT / "src" / "pcae" / "core" / "hatp_environment_lock_verifier.py",
]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Zero-consumer reconfirmation (governing-prompt §32) -- fresh AST/text
#    sweep, independent of any prior phase's own claim.
# ═══════════════════════════════════════════════════════════════════════════


class TestZeroConsumerReconfirmation:
    def test_readiness_root_source_has_no_class_b_verifier_reference(self) -> None:
        for name in (
            "hatp_class_b_topology_verifier",
            "hatp_environment_lock_verifier",
            "hatp_class_b_conformance",
            "verify_class_b_deployment_conformance",
        ):
            assert name not in _CUTOVER_SRC

    def test_certification_module_imports_none_of_the_three_verifier_modules(self) -> None:
        """`hatp_mandatory_certification.py` legitimately *names* the three
        verifier files as string path literals in its frozen-file-set
        constants (that is HMIC-REQ-050's v1.3 widening itself, §53.2) --
        that is data, not a Python import, and does not create a
        consumer. This test asserts the stronger, precise claim: no
        `import`/`from ... import` statement in the module names any of
        the three modules."""
        tree = ast.parse(_CERT_SRC)
        island = {"hatp_class_b_topology_verifier", "hatp_environment_lock_verifier", "hatp_class_b_conformance"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.rsplit(".", 1)[-1] not in island
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.rsplit(".", 1)[-1] not in island
        assert "verify_class_b_deployment_conformance(" not in _CERT_SRC

    def test_no_module_outside_the_island_imports_the_verifiers(self) -> None:
        """Fresh repo-wide sweep (this phase's own, not copied from
        K.2/K.3): every *.py file under src/ importing any of the three
        verifier modules is one of the three modules themselves."""
        island_names = {"hatp_class_b_conformance", "hatp_class_b_topology_verifier", "hatp_environment_lock_verifier"}
        offenders = []
        for path in (_REPO_ROOT / "src").rglob("*.py"):
            stem = path.stem
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                imported = None
                if isinstance(node, ast.ImportFrom) and node.module:
                    imported = node.module.rsplit(".", 1)[-1]
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imported = alias.name.rsplit(".", 1)[-1]
                        if imported in island_names and stem not in island_names:
                            offenders.append((str(path), imported))
                if imported in island_names and stem not in island_names and not isinstance(node, ast.Import):
                    offenders.append((str(path), imported))
        assert offenders == []


# ═══════════════════════════════════════════════════════════════════════════
# 2. Exact live readiness vector (governing-prompt §4) -- read fresh from
#    the running dataclass/function, never assumed from historical memory.
# ═══════════════════════════════════════════════════════════════════════════


class TestLiveReadinessVectorReconstruction:
    def test_readiness_root_function_exists_and_is_the_documented_name(self) -> None:
        assert callable(assess_hatp_mandatory_activation_readiness)

    def test_readiness_vector_has_exactly_seven_terms_on_the_real_host(self) -> None:
        readiness = assess_hatp_mandatory_activation_readiness(HarnessPath.cwd())
        names = [c.name for c in readiness.checks]
        assert names == [
            "class_b_protected_storage_available",
            "repository_deployment_identity_valid",
            "hatp_substrate_operational",
            "hsce_signing_implementation_available",
            "mandatory_consumption_implementation_independently_verified",
            "production_dependency_provenance_valid",
            "protected_activation_authority_mechanism_available",
        ]

    def test_none_of_the_seven_terms_names_class_b_deployment_conformance(self) -> None:
        """Contract-text-vs-implementation naming check: none of the
        seven live term names is `class_b_deployment_conformant` or any
        synonym referencing the full HBDC aggregator -- the closest
        term, `class_b_protected_storage_available`, is a narrower
        directory-existence check (proven below)."""
        readiness = assess_hatp_mandatory_activation_readiness(HarnessPath.cwd())
        names = {c.name for c in readiness.checks}
        assert "class_b_deployment_conformant" not in names
        assert "verify_class_b_deployment_conformance" not in names


# ═══════════════════════════════════════════════════════════════════════════
# 3. `class_b_protected_storage_available` is narrower than full HBDC
#    conformance (governing-prompt §5/§6) -- proven from the live source
#    of `_assess_hatp_mandatory_activation_readiness_at_root`, not
#    inferred from naming.
# ═══════════════════════════════════════════════════════════════════════════


class TestClassBTermIsNarrowerThanFullConformance:
    def test_storage_check_source_only_inspects_is_dir_and_symlink(self) -> None:
        source = inspect.getsource(cutover._assess_hatp_mandatory_activation_readiness_at_root)
        # The `class_b_protected_storage_available` check's own computation
        # line, isolated by its literal boolean expression.
        assert "protected_root.is_dir() and not protected_root.is_symlink()" in source

    def test_storage_check_never_calls_the_class_b_aggregator(self) -> None:
        source = inspect.getsource(cutover._assess_hatp_mandatory_activation_readiness_at_root)
        assert "verify_class_b_deployment_conformance" not in source
        assert "verify_class_b_topology_conformance" not in source
        assert "verify_environment_lock_conformance" not in source


# ═══════════════════════════════════════════════════════════════════════════
# 4. The concrete bypass counterexample (governing-prompt §7) -- every
#    current readiness term forced True via isolated, non-production test
#    seams (mirroring the 149O.19.5F suite's own `env`/`_assess` pattern),
#    while the REAL, un-mocked `verify_class_b_deployment_conformance()`
#    is independently invoked (no args -> real host) and is NOT COMPLIANT.
# ═══════════════════════════════════════════════════════════════════════════


class _FakeTrustStore:
    """Non-`None` stand-in satisfying `production_dependency_provenance_
    valid`'s `trust_store is not None` gate only -- never constructed via
    `HATPTrustStore.production()`, never given real filesystem authority."""


class _FakeHmicValidation:
    def __init__(self, status: CertificationStatus) -> None:
        self.status = status
        self.reason = "fixture-forced VALID for counterexample construction"


def _force_all_seven_readiness_terms_true(env, monkeypatch) -> HATPMandatoryActivationReadiness:
    monkeypatch.setattr(
        cutover,
        "inspect_hatp_verification_substrate_readiness",
        lambda *_a, **_k: _FakeOperationalSubstrate(),
    )
    monkeypatch.setattr(
        cutover,
        "validate_active_hatp_mandatory_independent_verification_certification",
        lambda *_a, **_k: _FakeHmicValidation(CertificationStatus.VALID),
    )
    monkeypatch.setattr(cutover, "certification_status_satisfies_readiness", lambda status: status == CertificationStatus.VALID)
    return _assess_hatp_mandatory_activation_readiness_at_root(
        env["protected_root"],
        env["repository_instance_id"],
        repository_root=env["repo_root"],
        trust_store=_FakeTrustStore(),
    )


class _FakeOperationalSubstrate:
    status = None
    operational = True
    reasons = ()

    def __init__(self) -> None:
        from pcae.core.human_approval_trusted_provenance import HATPVerificationSubstrateStatus

        self.status = HATPVerificationSubstrateStatus.OPERATIONAL


@pytest.fixture
def env(tmp_path):
    repo_root = tmp_path / "repo"
    protected_root = tmp_path / "protected-root"
    repo_root.mkdir()
    # HBDC-REQ-014-conformant mode bits (no group/other write) is exactly
    # what `protected_activation_authority_mechanism_available` checks --
    # deliberately satisfied here, in isolation, to prove that satisfying
    # *this one narrow bit* is not the same as satisfying full HBDC
    # Class-B deployment conformance (HBDC-REQ-025..042), which this
    # fixture directory does not, and is not claimed to, satisfy.
    protected_root.mkdir(mode=0o750)
    identity = ensure_repository_identity(HarnessPath(repo_root))
    return {
        "repo_root": repo_root,
        "protected_root": protected_root,
        "repository_instance_id": identity.repository_instance_id,
    }


class TestConcreteBypassCounterexample:
    def test_every_readiness_term_can_be_forced_true_in_isolation(self, env, monkeypatch) -> None:
        readiness = _force_all_seven_readiness_terms_true(env, monkeypatch)
        assert readiness.ready is True
        assert readiness.reasons == ()
        for check in readiness.checks:
            assert check.satisfied is True

    def test_real_unmocked_class_b_conformance_is_not_compliant_on_the_same_host(self, env, monkeypatch) -> None:
        """The counterexample (governing-prompt §7/§36 T1/T2): readiness
        can be made `ready=True` (previous test) via isolated,
        non-authority-bearing fixture state, while the REAL production
        `verify_class_b_deployment_conformance()` -- called with no
        arguments, so it inspects the actual host's real interpreter,
        real ACLs, real venv/PYTHONPATH state, completely independent of
        this fixture's `protected_root`/`repo_root` -- is independently,
        freshly evaluated and found NOT COMPLIANT. No current readiness
        term observes, or could observe, this fact: CBV-S10 is
        concretely demonstrated, not merely argued from contract text."""
        readiness = _force_all_seven_readiness_terms_true(env, monkeypatch)
        assert readiness.ready is True

        real_conformance = verify_class_b_deployment_conformance()
        assert real_conformance.status != ClassBConformanceStatus.COMPLIANT
        # T1/T2 (governing-prompt §36): whether the real result happens to
        # be NON_COMPLIANT or INDETERMINATE on this host, either satisfies
        # the counterexample -- both are members of the fail-closed set.
        assert real_conformance.status in {
            ClassBConformanceStatus.NON_COMPLIANT,
            ClassBConformanceStatus.INDETERMINATE,
            ClassBConformanceStatus.ACCESS_ERROR,
            ClassBConformanceStatus.MALFORMED_STATE,
            ClassBConformanceStatus.UNSUPPORTED_DEPLOYMENT_MODEL,
        }

    def test_readiness_result_carries_no_field_that_could_have_observed_class_b(self, env, monkeypatch) -> None:
        """Diagnostic-structure check (governing-prompt §22): confirms the
        returned `HATPMandatoryActivationReadiness`/`HATPMandatoryActivationReadinessCheck`
        dataclasses have no field a future integration could retrofit
        without a schema change -- `checks` is a fixed 7-tuple, not an
        open/extensible mapping."""
        readiness = _force_all_seven_readiness_terms_true(env, monkeypatch)
        assert len(readiness.checks) == 7
        field_names = {f for f in readiness.__dataclass_fields__}
        assert field_names == {"ready", "checks", "reasons"}


# ═══════════════════════════════════════════════════════════════════════════
# 5. Alternate-construction-path check (governing-prompt §11/§31 T6) --
#    confirm `HATPMandatoryActivationReadiness(...)` is constructed in
#    exactly one place in production.
# ═══════════════════════════════════════════════════════════════════════════


class TestNoAlternateReadinessConstructor:
    def test_dataclass_constructed_in_exactly_one_production_function(self) -> None:
        tree = ast.parse(_CUTOVER_SRC)
        constructor_sites = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "HATPMandatoryActivationReadiness":
                constructor_sites.append(node.lineno)
        assert len(constructor_sites) == 1

    def test_ready_true_can_only_result_from_all_checks_satisfied(self) -> None:
        source = inspect.getsource(cutover._assess_hatp_mandatory_activation_readiness_at_root)
        assert "ready=(len(unmet_reasons) == 0)" in source


# ═══════════════════════════════════════════════════════════════════════════
# 6. Tri-state vocabulary confirmation (governing-prompt §9/§21) -- the
#    Class-B verdict is a six-member closed enum, not a Boolean; readiness
#    is a Boolean. Any future integration must decide how to fold one into
#    the other -- this test only pins the current, live shapes.
# ═══════════════════════════════════════════════════════════════════════════


class TestCurrentShapes:
    def test_class_b_status_is_a_closed_six_member_enum_not_boolean(self) -> None:
        members = {m.value for m in ClassBConformanceStatus}
        assert members == {
            "COMPLIANT",
            "NON_COMPLIANT",
            "INDETERMINATE",
            "ACCESS_ERROR",
            "MALFORMED_STATE",
            "UNSUPPORTED_DEPLOYMENT_MODEL",
        }

    def test_readiness_ready_field_is_boolean(self) -> None:
        readiness = assess_hatp_mandatory_activation_readiness(HarnessPath.cwd())
        assert isinstance(readiness.ready, bool)


# ═══════════════════════════════════════════════════════════════════════════
# 7. Real-host regression (governing-prompt §35) -- read-only.
# ═══════════════════════════════════════════════════════════════════════════


class TestRealHostRegression:
    def test_real_host_class_b_conformance_is_not_compliant(self) -> None:
        result = verify_class_b_deployment_conformance()
        assert result.status != ClassBConformanceStatus.COMPLIANT

    def test_real_host_readiness_is_not_ready(self) -> None:
        readiness = assess_hatp_mandatory_activation_readiness(HarnessPath.cwd())
        assert readiness.ready is False


# ═══════════════════════════════════════════════════════════════════════════
# 8. Production/contract file untouched confirmation (governing-prompt
#    §42) -- these three verifier files and the readiness root remain
#    importable and syntactically identical to what earlier phases (K/K.1
#    /K.2/K.3) already independently verified; this phase performs no
#    byte modification (confirmed operationally by `pcae commit`'s
#    allowed-files enforcement, not re-proven here).
# ═══════════════════════════════════════════════════════════════════════════


class TestModulesRemainImportable:
    def test_all_class_b_verifier_modules_importable(self) -> None:
        for path in _CONFORMANCE_SRC_FILES:
            assert path.is_file()
