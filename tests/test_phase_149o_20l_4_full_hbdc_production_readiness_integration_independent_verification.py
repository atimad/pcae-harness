"""Phase 149O.20L.4 -- Full-HBDC Production Readiness Integration
Independent Verification.

Independently re-derives, from live source and fixed git history alone
(never trusting Phase 149O.20L.3's own report or test module), the facts
underlying HMRC-001 v1.1's eighth `PREPARED` readiness prerequisite
(HMRC-REQ-086-100, Section 19A) as wired into
`hatp_mandatory_cutover.py` by Phase 149O.20L.3 (production commit
e2ccb7a3, true phase-entry commit 5e9d72d3).

This module does NOT import
`tests/test_phase_149o_20l_3_full_hbdc_production_readiness_integration.py`
-- every fixture, helper, and assertion here is independently
constructed. All activation/cutover-record-write tests use isolated
`tmp_path`-rooted fixtures, never `HATPTrustStore.production().root`,
and never mutate real repository state.
"""
from __future__ import annotations

import ast
import inspect
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core import hatp_mandatory_cutover as cutover
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.hatp_class_b_topology_verifier import ClassBConformanceStatus, ClassBDeploymentVerificationResult
from pcae.core.hatp_mandatory_cutover import (
    CutoverMode,
    HATPMandatoryActivationReadinessError,
    _activate_hatp_mandatory_at_root,
    _assess_hatp_mandatory_activation_readiness_at_root,
    _resolve_cutover_mode_at_root,
    _write_cutover_transition,
    assess_hatp_mandatory_activation_readiness,
    class_b_conformance_status_satisfies_readiness,
)
from pcae.core.human_approval_trusted_provenance import (
    HATPVerificationSubstrateReadiness,
    HATPVerificationSubstrateStatus,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CUTOVER_SRC = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py"
_PHASE_ENTRY_COMMIT = "5e9d72d3"

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


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True).stdout


# ═══════════════════════════════════════════════════════════════════════════
# 1/3/4/5. Diff/vector reconstruction facts
# ═══════════════════════════════════════════════════════════════════════════


def _historical_check_names() -> "list[str]":
    source = _git("show", f"{_PHASE_ENTRY_COMMIT}:src/pcae/core/hatp_mandatory_cutover.py")
    tree = ast.parse(source)
    fn = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_assess_hatp_mandatory_activation_readiness_at_root"
    )
    names = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "HATPMandatoryActivationReadinessCheck":
            first_arg = node.args[0]
            assert isinstance(first_arg, ast.Constant)
            names.append(first_arg.value)
    return names


def _current_check_names() -> "list[str]":
    source = inspect.getsource(_assess_hatp_mandatory_activation_readiness_at_root)
    tree = ast.parse(source)
    names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "HATPMandatoryActivationReadinessCheck":
            first_arg = node.args[0]
            assert isinstance(first_arg, ast.Constant)
            names.append(first_arg.value)
    return names


class TestVectorReconstruction:
    def test_diff_scope_is_exactly_one_file(self) -> None:
        production_commit = "e2ccb7a3"
        names = _git("diff", "--name-only", _PHASE_ENTRY_COMMIT, production_commit, "--", "src/pcae").splitlines()
        assert names == ["src/pcae/core/hatp_mandatory_cutover.py"]

    def test_historical_seven_term_vector_matches_expected_order(self) -> None:
        assert tuple(_historical_check_names()) == _OLD_SEVEN_CHECK_NAMES

    def test_current_vector_is_eight_terms_eighth_is_class_b(self) -> None:
        names = _current_check_names()
        assert len(names) == 8
        assert tuple(names[:7]) == _OLD_SEVEN_CHECK_NAMES
        assert names[7] == _EIGHTH_CHECK_NAME

    def test_set_diff_is_exactly_the_eighth_term(self) -> None:
        historical = set(_historical_check_names())
        current = set(_current_check_names())
        assert current - historical == {_EIGHTH_CHECK_NAME}
        assert historical - current == set()

    def test_old_seven_checks_bodies_byte_identical_since_phase_entry(self) -> None:
        """The diff introduced only additive lines: every pre-existing
        check's construction logic is untouched. Verified by diffing the
        raw text and confirming every removed('-') line is blank/context
        only -- i.e. no '-' line carrying real code exists in the diff."""
        diff_text = _git("diff", _PHASE_ENTRY_COMMIT, "e2ccb7a3", "--", "src/pcae/core/hatp_mandatory_cutover.py")
        removed_code_lines = [
            line
            for line in diff_text.splitlines()
            if line.startswith("-") and not line.startswith("---") and line.strip() != "-"
        ]
        assert removed_code_lines == [], f"unexpected removed/modified lines: {removed_code_lines}"


# ═══════════════════════════════════════════════════════════════════════════
# 2/7. Live HMIC frozen-scope re-read
# ═══════════════════════════════════════════════════════════════════════════


class TestFrozenScope:
    def test_exactly_28_unique_entries(self) -> None:
        frozen = hmic._FROZEN_AUTHORITY_BEARING_FILES
        assert len(frozen) == 28
        assert len(set(frozen)) == 28

    def test_all_three_class_b_verifier_modules_present(self) -> None:
        frozen = set(hmic._FROZEN_AUTHORITY_BEARING_FILES)
        assert "core/hatp_class_b_topology_verifier.py" in frozen
        assert "core/hatp_environment_lock_verifier.py" in frozen
        assert "core/hatp_class_b_conformance.py" in frozen

    def test_hbdc_contract_file_present(self) -> None:
        assert "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" in hmic._FROZEN_AUTHORITY_BEARING_FILES


# ═══════════════════════════════════════════════════════════════════════════
# 6/20. Canonical verifier consumption, single call/construction sites
# ═══════════════════════════════════════════════════════════════════════════


class TestCanonicalConsumption:
    def test_imports_canonical_verifier_and_status_enum(self) -> None:
        source = _CUTOVER_SRC.read_text()
        assert "from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance" in source
        assert "from pcae.core.hatp_class_b_topology_verifier import ClassBConformanceStatus" in source

    def test_no_duplicated_topology_or_environment_lock_logic(self) -> None:
        source = _CUTOVER_SRC.read_text()
        for forbidden in ("EnvironmentLock", "verify_class_b_topology_conformance", "verify_environment_lock_conformance"):
            assert forbidden not in source, f"unexpected reimplementation marker: {forbidden}"

    def test_single_verifier_call_site_in_cutover_module(self) -> None:
        tree = ast.parse(_CUTOVER_SRC.read_text())
        calls = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "verify_class_b_deployment_conformance"
        ]
        assert len(calls) == 1

    def test_verify_class_b_deployment_conformance_has_exactly_one_repo_wide_caller(self) -> None:
        """AST-based repo-wide scan (not a text grep, to avoid false
        positives from docstring/comment prose mentioning the function
        name): for every `.py` file under `src/pcae`, count genuine
        `ast.Call` sites whose callee resolves to the bare name
        `verify_class_b_deployment_conformance`. Excludes the function's
        own `def` (not a Call node) and any `__all__` string export (also
        not a Call node)."""
        src_root = _REPO_ROOT / "src" / "pcae"
        callers: "list[str]" = []
        for py_file in sorted(src_root.rglob("*.py")):
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "verify_class_b_deployment_conformance"
                ):
                    callers.append(str(py_file.relative_to(_REPO_ROOT)))
        assert callers == ["src/pcae/core/hatp_mandatory_cutover.py"], f"unexpected caller set: {callers}"

    def test_single_readiness_constructor_site(self) -> None:
        tree = ast.parse(_CUTOVER_SRC.read_text())
        calls = [
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "HATPMandatoryActivationReadiness"
        ]
        assert len(calls) == 1

    def test_no_alternate_seven_term_authority_path_repo_wide(self) -> None:
        result = subprocess.run(
            ["git", "grep", "-l", "HATPMandatoryActivationReadinessCheck(", "--", "src/pcae"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
        )
        files = [l for l in result.stdout.splitlines() if l.strip()]
        assert files == ["src/pcae/core/hatp_mandatory_cutover.py"]


# ═══════════════════════════════════════════════════════════════════════════
# 8/9/10. Mapping helper: identity comparison, full enum + fail-closed
# ═══════════════════════════════════════════════════════════════════════════


class TestMappingHelper:
    def test_source_uses_single_is_compare_no_equality(self) -> None:
        source = inspect.getsource(class_b_conformance_status_satisfies_readiness)
        tree = ast.parse(source)
        compares = [n for n in ast.walk(tree) if isinstance(n, ast.Compare)]
        assert len(compares) == 1
        assert [type(op).__name__ for op in compares[0].ops] == ["Is"]
        assert "==" not in source

    def test_only_compliant_satisfies(self) -> None:
        for member in ClassBConformanceStatus:
            expected = member is ClassBConformanceStatus.COMPLIANT
            assert class_b_conformance_status_satisfies_readiness(member) is expected

    def test_exactly_six_enum_members(self) -> None:
        assert len(list(ClassBConformanceStatus)) == 6

    @pytest.mark.parametrize(
        "value",
        ["COMPLIANT", None, object(), 1, ClassBConformanceStatus.NON_COMPLIANT.value],
    )
    def test_non_member_or_lookalike_fails_closed_no_raise(self, value) -> None:
        assert class_b_conformance_status_satisfies_readiness(value) is False


# ═══════════════════════════════════════════════════════════════════════════
# 11. Diagnostics: detail encodes exact status, not just boolean
# ═══════════════════════════════════════════════════════════════════════════


class TestDiagnostics:
    def test_detail_field_encodes_status_value_not_only_boolean(self, tmp_path, monkeypatch) -> None:
        for status in ClassBConformanceStatus:
            monkeypatch.setattr(
                cutover,
                "verify_class_b_deployment_conformance",
                lambda *_a, _status=status, **_kw: ClassBDeploymentVerificationResult(
                    status=_status, checks=(), reasons=(f"REASON:{_status.value}",), evidence=()
                ),
            )
            readiness = _assess_hatp_mandatory_activation_readiness_at_root(
                tmp_path / "nonexistent-protected-root", None, repository_root=None, trust_store=None
            )
            check = next(c for c in readiness.checks if c.name == _EIGHTH_CHECK_NAME)
            assert status.value in check.detail
            assert f"REASON:{status.value}" in check.detail or "reasons=" in check.detail


# ═══════════════════════════════════════════════════════════════════════════
# 12. Exception fail-closed, narrow try/except scope
# ═══════════════════════════════════════════════════════════════════════════


class TestExceptionFailClosed:
    def test_verifier_exception_yields_unsatisfied_class_b_check_ready_false(self, tmp_path, monkeypatch) -> None:
        def _raise(*_a, **_kw):
            raise RuntimeError("simulated verifier crash")

        monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _raise)
        readiness = _assess_hatp_mandatory_activation_readiness_at_root(
            tmp_path / "nonexistent-protected-root", None, repository_root=None, trust_store=None
        )
        check = next(c for c in readiness.checks if c.name == _EIGHTH_CHECK_NAME)
        assert check.satisfied is False
        assert "RuntimeError" in check.detail
        assert "simulated verifier crash" in check.detail
        assert readiness.ready is False

    def test_try_except_scope_is_narrow_other_seven_checks_still_run(self, tmp_path, monkeypatch) -> None:
        """The exception in the eighth check's verifier call must not
        propagate and abort assembly of the other seven checks."""

        def _raise(*_a, **_kw):
            raise RuntimeError("simulated verifier crash")

        monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _raise)
        readiness = _assess_hatp_mandatory_activation_readiness_at_root(
            tmp_path / "nonexistent-protected-root", None, repository_root=None, trust_store=None
        )
        names = {c.name for c in readiness.checks}
        assert set(_OLD_SEVEN_CHECK_NAMES) <= names
        assert len(readiness.checks) == 8


# ═══════════════════════════════════════════════════════════════════════════
# 14. AND conjunction truth table
# ═══════════════════════════════════════════════════════════════════════════


class TestConjunction:
    def _readiness_with(self, tmp_path, monkeypatch, *, old_checks_true: bool, class_b_status) -> bool:
        monkeypatch.setattr(
            cutover,
            "verify_class_b_deployment_conformance",
            lambda *_a, **_kw: ClassBDeploymentVerificationResult(
                status=class_b_status, checks=(), reasons=(), evidence=()
            ),
        )
        if old_checks_true:
            monkeypatch.setattr(
                cutover,
                "inspect_hatp_verification_substrate_readiness",
                lambda *_a, **_kw: HATPVerificationSubstrateReadiness(
                    status=HATPVerificationSubstrateStatus.OPERATIONAL,
                    operational=True,
                    terms=(),
                    reasons=(),
                ),
            )
            protected_root = tmp_path / "protected"
            protected_root.mkdir(mode=0o700)
        else:
            protected_root = tmp_path / "nonexistent"
        readiness = _assess_hatp_mandatory_activation_readiness_at_root(
            protected_root, None, repository_root=None, trust_store=(object() if old_checks_true else None)
        )
        return readiness.ready

    def test_all_eight_true_is_not_reachable_without_hmic_but_class_b_alone_never_bypasses(
        self, tmp_path, monkeypatch
    ) -> None:
        # repository_instance_id is None and HMIC is unresolvable here, so
        # "all eight true" cannot be reached in this narrow fixture; this
        # test instead proves Class-B COMPLIANT alone cannot force ready.
        ready = self._readiness_with(
            tmp_path, monkeypatch, old_checks_true=True, class_b_status=ClassBConformanceStatus.COMPLIANT
        )
        assert ready is False  # repository_deployment_identity_valid still False (no identity)

    def test_class_b_non_compliant_alone_forces_not_ready(self, tmp_path, monkeypatch) -> None:
        ready = self._readiness_with(
            tmp_path, monkeypatch, old_checks_true=True, class_b_status=ClassBConformanceStatus.NON_COMPLIANT
        )
        assert ready is False

    def test_class_b_indeterminate_forces_not_ready(self, tmp_path, monkeypatch) -> None:
        ready = self._readiness_with(
            tmp_path, monkeypatch, old_checks_true=False, class_b_status=ClassBConformanceStatus.INDETERMINATE
        )
        assert ready is False

    def test_ready_field_equals_zero_unmet_reasons(self, tmp_path) -> None:
        readiness = _assess_hatp_mandatory_activation_readiness_at_root(
            tmp_path / "nonexistent", None, repository_root=None, trust_store=None
        )
        assert readiness.ready == (len(readiness.reasons) == 0)
        assert len(readiness.checks) == 8


# ═══════════════════════════════════════════════════════════════════════════
# 15. Fresh-call-per-assessment / no caching
# ═══════════════════════════════════════════════════════════════════════════


class TestFreshCallNoCache:
    def test_no_cache_memo_or_global_markers_in_source(self) -> None:
        source = _CUTOVER_SRC.read_text()
        for marker in ("lru_cache", "functools.cache", "_CLASS_B_CACHE"):
            assert marker not in source

    def test_exactly_one_verifier_call_per_direct_assessment_call(self, tmp_path, monkeypatch) -> None:
        calls = []

        def _counting(*_a, **_kw):
            calls.append(1)
            return ClassBDeploymentVerificationResult(
                status=ClassBConformanceStatus.NON_COMPLIANT, checks=(), reasons=(), evidence=()
            )

        monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _counting)
        _assess_hatp_mandatory_activation_readiness_at_root(
            tmp_path / "nonexistent", None, repository_root=None, trust_store=None
        )
        assert len(calls) == 1
        _assess_hatp_mandatory_activation_readiness_at_root(
            tmp_path / "nonexistent", None, repository_root=None, trust_store=None
        )
        assert len(calls) == 2  # second independent call adds one more -- no memoization across calls


# ═══════════════════════════════════════════════════════════════════════════
# Isolated fixture for full end-to-end advisory + lock-held-recheck /
# TOCTOU tests (self-contained -- not imported from any other test file).
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def env(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    protected_root = tmp_path / "protected-root"
    protected_root.mkdir(mode=0o700)
    (repo_root / "src" / "pcae" / "core").mkdir(parents=True)
    (repo_root / "docs" / "contracts").mkdir(parents=True)
    (repo_root / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"alpha content v1\n")
    for name, cid, ver in (
        ("FIXTURE_HMRC.md", "HMRC-001", "1.0"),
        ("FIXTURE_HATP.md", "HATP-001", "1.0"),
        ("FIXTURE_HSCE.md", "HSCE-001", "1.1"),
        ("FIXTURE_RAE.md", "RAE-001", "1.0"),
    ):
        (repo_root / "docs" / "contracts" / name).write_bytes(f"**Contract:** {cid}\n**Version:** {ver}\n".encode())

    monkeypatch.setattr(
        hmic,
        "_FROZEN_AUTHORITY_BEARING_FILES",
        (
            "core/fixture_a.py",
            "docs/contracts/FIXTURE_HMRC.md",
            "docs/contracts/FIXTURE_HATP.md",
            "docs/contracts/FIXTURE_HSCE.md",
            "docs/contracts/FIXTURE_RAE.md",
        ),
    )
    monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 1)
    monkeypatch.setattr(
        hmic,
        "_CONTRACT_IDENTITY_FILES",
        (
            ("HMRC-001", "docs/contracts/FIXTURE_HMRC.md"),
            ("HATP-001", "docs/contracts/FIXTURE_HATP.md"),
            ("HSCE-001", "docs/contracts/FIXTURE_HSCE.md"),
            ("RAE-001", "docs/contracts/FIXTURE_RAE.md"),
        ),
    )

    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test Fixture"], cwd=repo_root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo_root, check=True)

    identity = ensure_repository_identity(HarnessPath(repo_root))
    repository_instance_id = identity.repository_instance_id
    canonical_deployment_root = hmic.derive_canonical_deployment_root(HarnessPath(repo_root))

    return {
        "repo_root": repo_root,
        "protected_root": protected_root,
        "repository_instance_id": repository_instance_id,
        "canonical_deployment_root": canonical_deployment_root,
    }


def _valid_certification(env) -> hmic.CertificationRecord:
    root = HarnessPath(env["repo_root"])
    fields = dict(
        repository_instance_id=env["repository_instance_id"],
        canonical_deployment_root=env["canonical_deployment_root"],
        implementation_commit=hmic.derive_implementation_commit(root),
        implementation_scope_digest=hmic.derive_implementation_scope_digest(root),
        contract_versions=dict(hmic.derive_contract_versions(root)),
        verification_record_digest="c" * 64,
        certified_at="2026-08-14T00:00:00Z",
        certified_by="protected-admin",
    )
    certification_id = hmic.derive_certification_id(fields)
    record = hmic.CertificationRecord(certification_id=certification_id, status="active", revoked_at=None, **fields)
    hmic._append_certification_record(env["protected_root"], record)
    hmic._write_active_binding(
        env["protected_root"],
        hmic.CertificationBinding(
            repository_instance_id=env["repository_instance_id"],
            canonical_deployment_root=env["canonical_deployment_root"],
            active_certification_id=record.certification_id,
        ),
    )
    return record


def _fake_operational_substrate(*_args, **_kwargs) -> HATPVerificationSubstrateReadiness:
    return HATPVerificationSubstrateReadiness(
        status=HATPVerificationSubstrateStatus.OPERATIONAL,
        operational=True,
        terms=(("fixture_forced_operational", True),),
        reasons=(),
    )


class _FakeTrustStore:
    pass


def _patch_production_trust_root(env, monkeypatch) -> None:
    monkeypatch.setattr(
        HATPTrustStore, "production", classmethod(lambda cls: cls(_test_only_root=env["protected_root"]))
    )


def _fake_class_b_result(status: ClassBConformanceStatus) -> ClassBDeploymentVerificationResult:
    return ClassBDeploymentVerificationResult(status=status, checks=(), reasons=(), evidence=())


def _write_prepared(protected_root: Path, repository_instance_id: str) -> None:
    _write_cutover_transition(
        protected_root,
        target_mode=CutoverMode.PREPARED,
        repository_instance_id=repository_instance_id,
        activated_by="test-operator",
    )


def _fully_positive_setup(env, monkeypatch, *, class_b_status=ClassBConformanceStatus.COMPLIANT) -> None:
    monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
    monkeypatch.setattr(
        cutover, "verify_class_b_deployment_conformance", lambda *_a, **_kw: _fake_class_b_result(class_b_status)
    )
    _patch_production_trust_root(env, monkeypatch)
    _valid_certification(env)
    _write_prepared(env["protected_root"], env["repository_instance_id"])


# ═══════════════════════════════════════════════════════════════════════════
# 16. Advisory + lock-held re-check share implementation
# ═══════════════════════════════════════════════════════════════════════════


class TestSharedImplementation:
    def test_advisory_path_includes_eighth_term(self, env, monkeypatch) -> None:
        _fully_positive_setup(env, monkeypatch)
        readiness = assess_hatp_mandatory_activation_readiness(HarnessPath(env["repo_root"]))
        assert any(c.name == _EIGHTH_CHECK_NAME for c in readiness.checks)

    def test_advisory_and_lock_held_call_same_internal_assembly_function(self, env, monkeypatch) -> None:
        calls = []
        real = _assess_hatp_mandatory_activation_readiness_at_root

        def _wrapped(*a, **kw):
            calls.append((a, kw))
            return real(*a, **kw)

        _fully_positive_setup(env, monkeypatch)
        monkeypatch.setattr(cutover, "_assess_hatp_mandatory_activation_readiness_at_root", _wrapped)
        _activate_hatp_mandatory_at_root(
            env["protected_root"],
            env["repository_instance_id"],
            activated_by="op",
            repository_root=env["repo_root"],
            trust_store=_FakeTrustStore(),
        )
        assert len(calls) == 1  # the lock-held recheck routes through the wrapped/patched internal function


# ═══════════════════════════════════════════════════════════════════════════
# 17/18. TOCTOU forward + reverse control (fresh, isolated fixtures only)
# ═══════════════════════════════════════════════════════════════════════════


class TestTOCTOU:
    def test_forward_toctou_compliant_then_non_compliant_blocks_activation(self, env, monkeypatch) -> None:
        """Advisory (pre-lock) observes COMPLIANT; authoritative lock-held
        re-check observes NON_COMPLIANT. The write must be blocked and no
        Cutover Record HATP_MANDATORY transition must be produced."""
        statuses = iter([ClassBConformanceStatus.COMPLIANT, ClassBConformanceStatus.NON_COMPLIANT])

        def _flip(*_a, **_kw):
            return _fake_class_b_result(next(statuses))

        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _flip)
        _patch_production_trust_root(env, monkeypatch)
        _valid_certification(env)
        _write_prepared(env["protected_root"], env["repository_instance_id"])

        # Advisory pre-lock read observes COMPLIANT.
        advisory = assess_hatp_mandatory_activation_readiness(HarnessPath(env["repo_root"]))
        assert advisory.ready is True

        # Authoritative lock-held re-check observes NON_COMPLIANT and blocks.
        with pytest.raises(HATPMandatoryActivationReadinessError):
            _activate_hatp_mandatory_at_root(
                env["protected_root"],
                env["repository_instance_id"],
                activated_by="op",
                repository_root=env["repo_root"],
                trust_store=_FakeTrustStore(),
            )
        resolution = _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"])
        assert resolution.mode == CutoverMode.PREPARED  # never advanced to HATP_MANDATORY

    def test_reverse_toctou_non_compliant_then_compliant_allows_activation(self, env, monkeypatch) -> None:
        """Advisory observes NON_COMPLIANT; authoritative lock-held
        re-check observes COMPLIANT with everything else satisfied --
        the fresh authoritative assessment governs, proving genuine
        re-evaluation rather than a cached boolean."""
        statuses = iter([ClassBConformanceStatus.NON_COMPLIANT, ClassBConformanceStatus.COMPLIANT])

        def _flip(*_a, **_kw):
            return _fake_class_b_result(next(statuses))

        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        monkeypatch.setattr(cutover, "verify_class_b_deployment_conformance", _flip)
        _patch_production_trust_root(env, monkeypatch)
        _valid_certification(env)
        _write_prepared(env["protected_root"], env["repository_instance_id"])

        advisory = assess_hatp_mandatory_activation_readiness(HarnessPath(env["repo_root"]))
        assert advisory.ready is False

        record = _activate_hatp_mandatory_at_root(
            env["protected_root"],
            env["repository_instance_id"],
            activated_by="op",
            repository_root=env["repo_root"],
            trust_store=_FakeTrustStore(),
        )
        assert record.mode == CutoverMode.HATP_MANDATORY
        resolution = _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"])
        assert resolution.mode == CutoverMode.HATP_MANDATORY


# ═══════════════════════════════════════════════════════════════════════════
# 19. No caller override
# ═══════════════════════════════════════════════════════════════════════════


class TestNoCallerOverride:
    _FORBIDDEN_NAMES = {"class_b_ok", "class_b_status", "class_b_compliant", "skip_class_b", "assume_compliant"}

    @pytest.mark.parametrize(
        "fn",
        [
            assess_hatp_mandatory_activation_readiness,
            _assess_hatp_mandatory_activation_readiness_at_root,
            cutover.activate_hatp_mandatory,
            _activate_hatp_mandatory_at_root,
        ],
    )
    def test_no_class_b_override_parameter(self, fn) -> None:
        params = set(inspect.signature(fn).parameters)
        assert not (params & self._FORBIDDEN_NAMES), f"{fn.__name__} has forbidden param(s): {params & self._FORBIDDEN_NAMES}"


# ═══════════════════════════════════════════════════════════════════════════
# 22/23. Lock-held non-bypassability + read-only assessment
# ═══════════════════════════════════════════════════════════════════════════


class TestNonBypassAndReadOnly:
    def test_write_blocked_when_readiness_check_raises_no_record_created(self, env, monkeypatch) -> None:
        _patch_production_trust_root(env, monkeypatch)
        _write_prepared(env["protected_root"], env["repository_instance_id"])

        def _refuse():
            raise cutover.HATPMandatoryActivationReadinessError("refused for test")

        with pytest.raises(cutover.HATPMandatoryActivationReadinessError):
            _write_cutover_transition(
                env["protected_root"],
                target_mode=CutoverMode.HATP_MANDATORY,
                repository_instance_id=env["repository_instance_id"],
                activated_by="op",
                readiness_check=_refuse,
            )
        record_path = env["protected_root"] / "cutover-record.json"
        # No HATP_MANDATORY transition -- either absent entirely or still PREPARED, never mandatory.
        if record_path.exists():
            assert "HATP_MANDATORY" not in record_path.read_text()

    def test_readiness_assessment_against_nonexistent_root_does_not_create_it(self, tmp_path) -> None:
        target = tmp_path / "never-created"
        assert not target.exists()
        _assess_hatp_mandatory_activation_readiness_at_root(target, None, repository_root=None, trust_store=None)
        assert not target.exists()


# ═══════════════════════════════════════════════════════════════════════════
# 24. Real host test (unmocked) + no side effects
# ═══════════════════════════════════════════════════════════════════════════


class TestRealHost:
    def test_real_unmocked_verifier_is_non_compliant_on_this_host(self) -> None:
        from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance

        result = verify_class_b_deployment_conformance()
        assert result.status is not ClassBConformanceStatus.COMPLIANT

    def test_real_unmocked_assessment_has_eight_checks_class_b_unsatisfied_not_ready(self) -> None:
        readiness = assess_hatp_mandatory_activation_readiness(HarnessPath(_REPO_ROOT))
        assert len(readiness.checks) == 8
        eighth = next(c for c in readiness.checks if c.name == _EIGHTH_CHECK_NAME)
        assert eighth.satisfied is False
        assert readiness.ready is False

    def test_git_status_clean_immediately_after_real_call(self) -> None:
        before = subprocess.run(
            ["git", "status", "--short"], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True
        ).stdout
        assess_hatp_mandatory_activation_readiness(HarnessPath(_REPO_ROOT))
        after = subprocess.run(
            ["git", "status", "--short"], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True
        ).stdout
        # Compares before/after rather than asserting a globally-clean tree,
        # since this verification module's own file may itself be untracked
        # at the time this test runs -- the assertion under test is that the
        # readiness assessment call itself has no side effect.
        assert after == before


# ═══════════════════════════════════════════════════════════════════════════
# 25. Byte identity across the whole L.3 phase window
# ═══════════════════════════════════════════════════════════════════════════


class TestByteIdentity:
    _PATHS = (
        "src/pcae/core/hatp_class_b_conformance.py",
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "src/pcae/core/hatp_mandatory_certification.py",
        "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
        "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
        "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
    )

    @pytest.mark.parametrize("path", _PATHS)
    def test_byte_identical_since_phase_entry_to_head(self, path) -> None:
        diff = _git("diff", _PHASE_ENTRY_COMMIT, "HEAD", "--", path)
        assert diff == "", f"{path} is NOT byte-identical since {_PHASE_ENTRY_COMMIT}:\n{diff}"
