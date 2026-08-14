"""Phase 149O.20L.3 -- Full-HBDC Production Readiness Integration.

Implements HMRC-001 v1.1's eighth `PREPARED` readiness prerequisite
(HMRC-REQ-086-100, §19A) in production: wires
`class_b_deployment_conformance_satisfies_readiness` into the single
existing `_assess_hatp_mandatory_activation_readiness_at_root` /
`assess_hatp_mandatory_activation_readiness` / `_write_cutover_transition`
readiness path. This is a production-integration phase, not a contract or
verifier change: HMRC-001, HMIC-001, HBDC-001, and all three Class-B
verifier modules are asserted byte-identical to the true phase-entry
commit throughout this module.

Every test in this module that exercises activation/cutover-record writes
uses an isolated `tmp_path`-rooted protected root via the internal test
seams -- never `HATPTrustStore.production().root` (mirrors
`test_hatp_mandatory_activation_guard.py`'s existing discipline). No test
here provisions, certifies, or activates the real deployment.

CBV-S10 is NOT closed by this phase: production integration is
implemented here, but independent verification of that integration is
deferred to Phase 149O.20L.4.
"""
from __future__ import annotations

import ast
import inspect
import re
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core import hatp_mandatory_cutover as cutover
from pcae.core.hatp_class_b_topology_verifier import ClassBConformanceStatus, ClassBDeploymentVerificationResult
from pcae.core.hatp_mandatory_cutover import (
    CutoverMode,
    HATPMandatoryActivationReadiness,
    HATPMandatoryActivationReadinessError,
    _activate_hatp_mandatory_at_root,
    _assess_hatp_mandatory_activation_readiness_at_root,
    _write_cutover_transition,
    assess_hatp_mandatory_activation_readiness,
    class_b_conformance_status_satisfies_readiness,
)
from pcae.core.paths import HarnessPath

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CUTOVER_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py"
_HMRC_RELATIVE = "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
_HMIC_RELATIVE = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_HBDC_RELATIVE = "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_CLASS_B_VERIFIER_RELATIVE_PATHS = (
    "src/pcae/core/hatp_class_b_conformance.py",
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
)

# True phase-entry commit: HEAD immediately before this phase's own first
# commit (independently confirmed by `git log --oneline -1` at phase
# bootstrap time, before any edit in this phase).
_PHASE_ENTRY_COMMIT = "5e9d72d3"

_REPO_A = "11111111-1111-4111-8111-111111111111"

_OLD_SEVEN_CHECK_NAMES = (
    "class_b_protected_storage_available",
    "repository_deployment_identity_valid",
    "hatp_substrate_operational",
    "hsce_signing_implementation_available",
    "mandatory_consumption_implementation_independently_verified",
    "production_dependency_provenance_valid",
    "protected_activation_authority_mechanism_available",
)
_EIGHTH_CHECK_NAME = "class_b_deployment_conformance_satisfies_readiness"


def _git_show_bytes(commit: str, relative_path: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative_path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        check=True,
    )
    return result.stdout


def _fake_class_b_result(status: ClassBConformanceStatus) -> ClassBDeploymentVerificationResult:
    return ClassBDeploymentVerificationResult(status=status, checks=(), reasons=(), evidence=())


def _force_seven_old_checks_satisfied(monkeypatch: pytest.MonkeyPatch, protected_root: Path) -> None:
    """Monkeypatches every dependency the seven pre-existing checks read,
    so only the eighth (Class-B) term varies across a test. Mirrors the
    existing repository convention (`test_hatp_mandatory_activation_guard.py`)
    of monkeypatching module-level names inside the `cutover` namespace
    rather than the real environment."""

    protected_root.mkdir(parents=True, exist_ok=True)
    protected_root.chmod(0o700)

    monkeypatch.setattr(
        cutover,
        "inspect_hatp_verification_substrate_readiness",
        lambda *_a, **_kw: SimpleNamespace(operational=True, status=SimpleNamespace(value="OPERATIONAL"), reasons=()),
    )
    monkeypatch.setattr(
        cutover,
        "validate_active_hatp_mandatory_independent_verification_certification",
        lambda _root: SimpleNamespace(status=SimpleNamespace(value="VALID"), reason="forced-valid-for-test"),
    )
    monkeypatch.setattr(cutover, "certification_status_satisfies_readiness", lambda _status: True)


def _assess_with_class_b(
    monkeypatch: pytest.MonkeyPatch,
    protected_root: Path,
    class_b_outcome,
) -> HATPMandatoryActivationReadiness:
    """`class_b_outcome` is either a `ClassBConformanceStatus` (a
    successful verifier call is simulated) or an `Exception` instance (a
    raised verifier call is simulated)."""

    _force_seven_old_checks_satisfied(monkeypatch, protected_root)

    def _fake_verify(*_a, **_kw):
        if isinstance(class_b_outcome, Exception):
            raise class_b_outcome
        return _fake_class_b_result(class_b_outcome)

    monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _fake_verify)
    return _assess_hatp_mandatory_activation_readiness_at_root(
        protected_root,
        _REPO_A,
        repository_root=protected_root,
        trust_store=object(),
    )


# ═══════════════════════════════════════════════════════════════════════
# 1. Exact seven-term baseline reconstruction / eight-term current vector
# ═══════════════════════════════════════════════════════════════════════


class TestVectorShape:
    def test_pre_l3_seven_term_vector_reconstructed_from_phase_entry_commit(self) -> None:
        pre_l3_source = _git_show_bytes(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_cutover.py").decode(
            "utf-8"
        )
        names = re.findall(r'HATPMandatoryActivationReadinessCheck\(\s*\n?\s*"([a-z_]+)"', pre_l3_source)
        assert tuple(names) == _OLD_SEVEN_CHECK_NAMES
        assert _EIGHTH_CHECK_NAME not in pre_l3_source

    def test_current_eight_term_vector_names_in_order(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        result = _assess_with_class_b(monkeypatch, tmp_path / "root", ClassBConformanceStatus.COMPLIANT)
        assert tuple(c.name for c in result.checks) == _OLD_SEVEN_CHECK_NAMES + (_EIGHTH_CHECK_NAME,)

    def test_exact_plus_one_delta(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        result = _assess_with_class_b(monkeypatch, tmp_path / "root", ClassBConformanceStatus.COMPLIANT)
        assert len(result.checks) == len(_OLD_SEVEN_CHECK_NAMES) + 1
        assert set(c.name for c in result.checks) - set(_OLD_SEVEN_CHECK_NAMES) == {_EIGHTH_CHECK_NAME}

    def test_old_seven_checks_still_present_unrenamed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        result = _assess_with_class_b(monkeypatch, tmp_path / "root", ClassBConformanceStatus.NON_COMPLIANT)
        names = {c.name for c in result.checks}
        for old_name in _OLD_SEVEN_CHECK_NAMES:
            assert old_name in names


# ═══════════════════════════════════════════════════════════════════════
# 2. Mapping helper: closed-enum coverage + fail-closed on non-member
# ═══════════════════════════════════════════════════════════════════════


class TestMappingHelper:
    @pytest.mark.parametrize(
        "status,expected",
        [
            (ClassBConformanceStatus.COMPLIANT, True),
            (ClassBConformanceStatus.NON_COMPLIANT, False),
            (ClassBConformanceStatus.INDETERMINATE, False),
            (ClassBConformanceStatus.ACCESS_ERROR, False),
            (ClassBConformanceStatus.MALFORMED_STATE, False),
            (ClassBConformanceStatus.UNSUPPORTED_DEPLOYMENT_MODEL, False),
        ],
    )
    def test_full_closed_enum_mapping(self, status: ClassBConformanceStatus, expected: bool) -> None:
        assert class_b_conformance_status_satisfies_readiness(status) is expected

    def test_all_six_current_enum_members_covered(self) -> None:
        assert {m for m in ClassBConformanceStatus} == set(ClassBConformanceStatus)
        for member in ClassBConformanceStatus:
            result = class_b_conformance_status_satisfies_readiness(member)
            assert result is (member is ClassBConformanceStatus.COMPLIANT)

    @pytest.mark.parametrize(
        "bogus",
        ["COMPLIANT", object(), None, 1, SimpleNamespace(value="COMPLIANT")],
    )
    def test_non_member_input_fails_closed(self, bogus) -> None:
        assert class_b_conformance_status_satisfies_readiness(bogus) is False

    def test_helper_is_pure_identity_comparison_no_string_or_truthy_coercion(self) -> None:
        source = inspect.getsource(class_b_conformance_status_satisfies_readiness)
        tree = ast.parse(source)
        # Exactly one `is` comparison, no `==`, no bare boolean coercion of `status`.
        compares = [n for n in ast.walk(tree) if isinstance(n, ast.Compare)]
        assert len(compares) == 1
        assert isinstance(compares[0].ops[0], ast.Is)
        assert "==" not in source


# ═══════════════════════════════════════════════════════════════════════
# 3. Evidence/Boolean separation (HMRC-REQ-090)
# ═══════════════════════════════════════════════════════════════════════


class TestDiagnosticDetailPreservation:
    @pytest.mark.parametrize(
        "status",
        list(ClassBConformanceStatus),
    )
    def test_detail_names_exact_observed_status(
        self, status: ClassBConformanceStatus, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = _assess_with_class_b(monkeypatch, tmp_path / "root", status)
        check = next(c for c in result.checks if c.name == _EIGHTH_CHECK_NAME)
        assert status.value in check.detail
        assert check.satisfied is (status is ClassBConformanceStatus.COMPLIANT)

    def test_exception_detail_is_safe_and_identifies_failure_without_satisfying(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = _assess_with_class_b(monkeypatch, tmp_path / "root", RuntimeError("boom"))
        check = next(c for c in result.checks if c.name == _EIGHTH_CHECK_NAME)
        assert check.satisfied is False
        assert "RuntimeError" in check.detail


# ═══════════════════════════════════════════════════════════════════════
# 4. Conjunction (HMRC-REQ-096) -- no alternate "ready via Class-B alone"
# ═══════════════════════════════════════════════════════════════════════


class TestConjunction:
    def test_all_eight_satisfied_yields_ready_true(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        result = _assess_with_class_b(monkeypatch, tmp_path / "root", ClassBConformanceStatus.COMPLIANT)
        assert result.ready is True
        assert result.reasons == ()

    def test_all_seven_old_true_but_class_b_non_compliant_yields_ready_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = _assess_with_class_b(monkeypatch, tmp_path / "root", ClassBConformanceStatus.NON_COMPLIANT)
        assert result.ready is False
        assert any(_EIGHTH_CHECK_NAME == c.name for c in result.checks if not c.satisfied)

    def test_class_b_compliant_but_one_old_check_false_yields_ready_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        protected_root = tmp_path / "root"
        _force_seven_old_checks_satisfied(monkeypatch, protected_root)
        # Sabotage exactly one old check after forcing the rest true.
        monkeypatch.setattr(cutover, "certification_status_satisfies_readiness", lambda _status: False)
        monkeypatch.setattr(
            cutover, "verify_class_b_deployment_conformance", lambda *_a, **_kw: _fake_class_b_result(ClassBConformanceStatus.COMPLIANT)
        )
        result = _assess_hatp_mandatory_activation_readiness_at_root(
            protected_root, _REPO_A, repository_root=protected_root, trust_store=object()
        )
        assert result.ready is False
        class_b_check = next(c for c in result.checks if c.name == _EIGHTH_CHECK_NAME)
        assert class_b_check.satisfied is True  # Class-B alone is COMPLIANT...
        assert result.ready is False  # ...but that does not make readiness true.

    def test_class_b_indeterminate_with_all_old_true_yields_ready_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = _assess_with_class_b(monkeypatch, tmp_path / "root", ClassBConformanceStatus.INDETERMINATE)
        assert result.ready is False

    def test_only_failing_term_is_class_b_reasons_reflect_exactly_that(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result = _assess_with_class_b(monkeypatch, tmp_path / "root", ClassBConformanceStatus.NON_COMPLIANT)
        unsatisfied = [c for c in result.checks if not c.satisfied]
        assert len(unsatisfied) == 1
        assert unsatisfied[0].name == _EIGHTH_CHECK_NAME
        assert len(result.reasons) == 1
        assert len(set(result.reasons)) == 1  # no duplicate reason


# ═══════════════════════════════════════════════════════════════════════
# 5. Freshness / no cache (HMRC-REQ-092) -- verifier called each assessment
# ═══════════════════════════════════════════════════════════════════════


class TestFreshCallEachAssessment:
    def test_one_advisory_assessment_one_fresh_verifier_call(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        protected_root = tmp_path / "root"
        _force_seven_old_checks_satisfied(monkeypatch, protected_root)
        call_count = {"n": 0}

        def _counting_verify(*_a, **_kw):
            call_count["n"] += 1
            return _fake_class_b_result(ClassBConformanceStatus.COMPLIANT)

        monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _counting_verify)
        _assess_hatp_mandatory_activation_readiness_at_root(
            protected_root, _REPO_A, repository_root=protected_root, trust_store=object()
        )
        assert call_count["n"] == 1
        _assess_hatp_mandatory_activation_readiness_at_root(
            protected_root, _REPO_A, repository_root=protected_root, trust_store=object()
        )
        assert call_count["n"] == 2  # No cache: second independent call, second fresh invocation.

    def test_advisory_plus_lock_held_recheck_yields_at_least_two_independent_calls(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        protected_root = tmp_path / "root"
        _force_seven_old_checks_satisfied(monkeypatch, protected_root)
        call_count = {"n": 0}

        def _counting_verify(*_a, **_kw):
            call_count["n"] += 1
            return _fake_class_b_result(ClassBConformanceStatus.COMPLIANT)

        monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _counting_verify)

        cutover._write_cutover_transition(
            protected_root,
            target_mode=CutoverMode.PREPARED,
            repository_instance_id=_REPO_A,
            activated_by="test-operator",
        )
        # Advisory call (boundary 1).
        advisory = _assess_hatp_mandatory_activation_readiness_at_root(
            protected_root, _REPO_A, repository_root=protected_root, trust_store=object()
        )
        assert advisory.ready is True
        assert call_count["n"] == 1

        # Lock-held re-check (boundary 2) via the real activation write path.
        _activate_hatp_mandatory_at_root(
            protected_root,
            _REPO_A,
            activated_by="test-operator",
            repository_root=protected_root,
            trust_store=object(),
        )
        assert call_count["n"] >= 2


# ═══════════════════════════════════════════════════════════════════════
# 6. Advisory path integration
# ═══════════════════════════════════════════════════════════════════════


class TestAdvisoryPathIntegration:
    def test_advisory_assess_function_returns_eight_checks(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            cutover, "verify_class_b_deployment_conformance", lambda *_a, **_kw: _fake_class_b_result(ClassBConformanceStatus.NON_COMPLIANT)
        )
        result = assess_hatp_mandatory_activation_readiness(HarnessPath(tmp_path))
        assert len(result.checks) == 8
        assert any(c.name == _EIGHTH_CHECK_NAME for c in result.checks)

    def test_real_host_via_public_entrypoint_has_eight_checks_not_ready(self) -> None:
        """Real, unprovisioned host -- no monkeypatching. §21."""
        result = assess_hatp_mandatory_activation_readiness(HarnessPath.cwd())
        assert len(result.checks) == 8
        class_b_check = next(c for c in result.checks if c.name == _EIGHTH_CHECK_NAME)
        assert class_b_check.satisfied is False
        assert result.ready is False


# ═══════════════════════════════════════════════════════════════════════
# 7. Lock-held re-check integration + TOCTOU (HMRC-REQ-093/094)
# ═══════════════════════════════════════════════════════════════════════


class TestLockHeldRecheckAndToctou:
    def test_lock_held_recheck_includes_eighth_term_and_blocks_on_non_compliant(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        protected_root = tmp_path / "root"
        _force_seven_old_checks_satisfied(monkeypatch, protected_root)
        monkeypatch.setattr(
            cutover, "verify_class_b_deployment_conformance", lambda *_a, **_kw: _fake_class_b_result(ClassBConformanceStatus.NON_COMPLIANT)
        )
        cutover._write_cutover_transition(
            protected_root,
            target_mode=CutoverMode.PREPARED,
            repository_instance_id=_REPO_A,
            activated_by="test-operator",
        )
        with pytest.raises(HATPMandatoryActivationReadinessError):
            _activate_hatp_mandatory_at_root(
                protected_root,
                _REPO_A,
                activated_by="test-operator",
                repository_root=protected_root,
                trust_store=object(),
            )
        resolution = cutover._resolve_cutover_mode_at_root(protected_root, _REPO_A)
        assert resolution.mode == CutoverMode.PREPARED  # No Cutover Record write occurred.

    def test_toctou_stale_advisory_compliant_does_not_authorize_later_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        protected_root = tmp_path / "root"
        _force_seven_old_checks_satisfied(monkeypatch, protected_root)
        cutover._write_cutover_transition(
            protected_root,
            target_mode=CutoverMode.PREPARED,
            repository_instance_id=_REPO_A,
            activated_by="test-operator",
        )

        call_sequence = [ClassBConformanceStatus.COMPLIANT, ClassBConformanceStatus.NON_COMPLIANT]

        def _flip_flop_verify(*_a, **_kw):
            status = call_sequence.pop(0) if call_sequence else ClassBConformanceStatus.NON_COMPLIANT
            return _fake_class_b_result(status)

        monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _flip_flop_verify)

        # Advisory call observes COMPLIANT (stale-optimistic).
        advisory = _assess_hatp_mandatory_activation_readiness_at_root(
            protected_root, _REPO_A, repository_root=protected_root, trust_store=object()
        )
        assert advisory.ready is True

        # Real-world verifier state degraded before the authoritative,
        # lock-held re-check runs (simulated by the second queued value).
        with pytest.raises(HATPMandatoryActivationReadinessError):
            _activate_hatp_mandatory_at_root(
                protected_root,
                _REPO_A,
                activated_by="test-operator",
                repository_root=protected_root,
                trust_store=object(),
            )
        resolution = cutover._resolve_cutover_mode_at_root(protected_root, _REPO_A)
        assert resolution.mode == CutoverMode.PREPARED  # No Cutover Record produced.

    def test_lock_held_recheck_succeeds_when_all_eight_satisfied(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        protected_root = tmp_path / "root"
        _force_seven_old_checks_satisfied(monkeypatch, protected_root)
        monkeypatch.setattr(
            cutover, "verify_class_b_deployment_conformance", lambda *_a, **_kw: _fake_class_b_result(ClassBConformanceStatus.COMPLIANT)
        )
        cutover._write_cutover_transition(
            protected_root,
            target_mode=CutoverMode.PREPARED,
            repository_instance_id=_REPO_A,
            activated_by="test-operator",
        )
        record = _activate_hatp_mandatory_at_root(
            protected_root,
            _REPO_A,
            activated_by="test-operator",
            repository_root=protected_root,
            trust_store=object(),
        )
        assert record.mode == CutoverMode.HATP_MANDATORY


# ═══════════════════════════════════════════════════════════════════════
# 8. No caller override (HMRC-REQ-095)
# ═══════════════════════════════════════════════════════════════════════


class TestNoCallerOverride:
    @pytest.mark.parametrize(
        "func",
        [
            assess_hatp_mandatory_activation_readiness,
            _assess_hatp_mandatory_activation_readiness_at_root,
            cutover.activate_hatp_mandatory,
            _activate_hatp_mandatory_at_root,
        ],
    )
    def test_no_class_b_override_parameter_exists(self, func) -> None:
        params = set(inspect.signature(func).parameters)
        forbidden = {"class_b_ok", "class_b_status", "skip_class_b", "assume_compliant", "class_b_compliant"}
        assert params.isdisjoint(forbidden)

    def test_readiness_check_source_calls_canonical_verifier_directly_no_param_passthrough(self) -> None:
        source = inspect.getsource(_assess_hatp_mandatory_activation_readiness_at_root)
        assert "verify_class_b_deployment_conformance(" in source


# ═══════════════════════════════════════════════════════════════════════
# 9. Single constructor site / no alternate authority path
# ═══════════════════════════════════════════════════════════════════════


class TestNoAlternateAuthorityPath:
    def test_exactly_one_readiness_constructor_site(self) -> None:
        text = _CUTOVER_SRC.read_text(encoding="utf-8")
        assert text.count("return HATPMandatoryActivationReadiness(") == 1

    def test_exactly_one_function_builds_the_checks_tuple(self) -> None:
        tree = ast.parse(_CUTOVER_SRC.read_text(encoding="utf-8"))
        constructing_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                calls_check_ctor = any(
                    isinstance(n, ast.Call)
                    and isinstance(n.func, ast.Name)
                    and n.func.id == "HATPMandatoryActivationReadinessCheck"
                    for n in ast.walk(node)
                )
                if calls_check_ctor:
                    constructing_functions.append(node.name)
        assert constructing_functions == ["_assess_hatp_mandatory_activation_readiness_at_root"]

    def test_no_second_verify_class_b_deployment_conformance_call_site_outside_readiness_function(self) -> None:
        tree = ast.parse(_CUTOVER_SRC.read_text(encoding="utf-8"))
        calling_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                calls_verifier = any(
                    isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "verify_class_b_deployment_conformance"
                    for n in ast.walk(node)
                )
                if calls_verifier:
                    calling_functions.append(node.name)
        assert calling_functions == ["_assess_hatp_mandatory_activation_readiness_at_root"]

    def test_class_b_deployment_conformance_satisfies_readiness_appears_exactly_once_as_check_name(self) -> None:
        text = _CUTOVER_SRC.read_text(encoding="utf-8")
        assert text.count(f'"{_EIGHTH_CHECK_NAME}"') == 1


# ═══════════════════════════════════════════════════════════════════════
# 10. Read-only assessment / no side effects
# ═══════════════════════════════════════════════════════════════════════


class TestReadOnlyAssessment:
    def test_readiness_assessment_does_not_provision_or_create_protected_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        protected_root = tmp_path / "does-not-exist"
        monkeypatch.setattr(
            cutover, "verify_class_b_deployment_conformance", lambda *_a, **_kw: _fake_class_b_result(ClassBConformanceStatus.NON_COMPLIANT)
        )
        _assess_hatp_mandatory_activation_readiness_at_root(protected_root, _REPO_A)
        assert not protected_root.exists()


# ═══════════════════════════════════════════════════════════════════════
# 11. Byte-identity regressions (production integration must not touch
#     contracts or the Class-B verifier semantics)
# ═══════════════════════════════════════════════════════════════════════


class TestByteIdentityRegressions:
    @pytest.mark.parametrize("relative_path", _CLASS_B_VERIFIER_RELATIVE_PATHS)
    def test_class_b_verifier_modules_byte_identical_since_phase_entry(self, relative_path: str) -> None:
        pre = _git_show_bytes(_PHASE_ENTRY_COMMIT, relative_path)
        current = (_REPO_ROOT / relative_path).read_bytes()
        assert pre == current

    def test_hmrc_contract_byte_identical_since_phase_entry(self) -> None:
        pre = _git_show_bytes(_PHASE_ENTRY_COMMIT, _HMRC_RELATIVE)
        current = (_REPO_ROOT / _HMRC_RELATIVE).read_bytes()
        assert pre == current

    def test_hmic_contract_byte_identical_since_phase_entry(self) -> None:
        pre = _git_show_bytes(_PHASE_ENTRY_COMMIT, _HMIC_RELATIVE)
        current = (_REPO_ROOT / _HMIC_RELATIVE).read_bytes()
        assert pre == current

    def test_hbdc_contract_byte_identical_since_phase_entry(self) -> None:
        pre = _git_show_bytes(_PHASE_ENTRY_COMMIT, _HBDC_RELATIVE)
        current = (_REPO_ROOT / _HBDC_RELATIVE).read_bytes()
        assert pre == current

    def test_hmic_source_module_byte_identical_since_phase_entry(self) -> None:
        pre = _git_show_bytes(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
        current = (_REPO_ROOT / "src/pcae/core/hatp_mandatory_certification.py").read_bytes()
        assert pre == current


# ═══════════════════════════════════════════════════════════════════════
# 12. CBV-S1 regression (28 authority-bearing files / 5 contract-identity
#     members, Class-B verifier modules remain bound) -- reuses the
#     canonical production constants, never a second re-derivation.
# ═══════════════════════════════════════════════════════════════════════


class TestCbvS1Regression:
    def test_28_authority_bearing_files(self) -> None:
        assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 28

    def test_5_contract_identity_members(self) -> None:
        assert len(hmic._CONTRACT_IDENTITY_FILES) == 5

    def test_class_b_verifier_modules_not_named_in_frozen_scope(self) -> None:
        for relative_path in _CLASS_B_VERIFIER_RELATIVE_PATHS:
            assert relative_path not in hmic._FROZEN_AUTHORITY_BEARING_FILES

    def test_hmrc_still_one_of_the_28_frozen_files(self) -> None:
        assert _HMRC_RELATIVE in hmic._FROZEN_AUTHORITY_BEARING_FILES


# ═══════════════════════════════════════════════════════════════════════
# 13. B-149O.20L.1-1 regression (HMRC-001 v1.1, HMIC Depends-on line,
#     derive_contract_versions live-header read)
# ═══════════════════════════════════════════════════════════════════════


class TestB149O20L1_1Regression:
    _DEPENDS_ON_RE = re.compile(r"^\*\*Depends on.*$", re.MULTILINE)
    _VERSION_RE = re.compile(r"^\*\*Version:\*\*\s*(\S+)\s*$", re.MULTILINE)

    def test_hmrc_still_v1_1(self) -> None:
        text = (_REPO_ROOT / _HMRC_RELATIVE).read_text(encoding="utf-8")
        assert self._VERSION_RE.search(text).group(1) == "1.1"

    def test_hmic_depends_on_line_still_names_hmrc_v1_1(self) -> None:
        text = (_REPO_ROOT / _HMIC_RELATIVE).read_text(encoding="utf-8")
        depends_line = self._DEPENDS_ON_RE.search(text).group(0)
        assert "HMRC-001 v1.1" in depends_line

    def test_derive_contract_versions_reads_live_hmrc_header_as_1_1(self, tmp_path: Path) -> None:
        versions = hmic.derive_contract_versions(HarnessPath(_REPO_ROOT))
        assert versions["HMRC-001"] == "1.1"


# ═══════════════════════════════════════════════════════════════════════
# 14. CBV-S10 not closed by this phase (advisory, textual self-check)
# ═══════════════════════════════════════════════════════════════════════


class TestCbvS10NotClosed:
    def test_cutover_module_makes_no_certification_or_activation_ceremony_call(self) -> None:
        source = _CUTOVER_SRC.read_text(encoding="utf-8")
        for forbidden in ("_append_certification_record", "_write_active_binding", "_write_revocation"):
            assert forbidden not in source
