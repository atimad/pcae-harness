"""Phase 149O.19.5F -- HMIC Activation-Readiness Integration.

Wave F (`docs/PHASE_149O_19_4_HATP_MANDATORY_INDEPENDENT_VERIFICATION_
CERTIFICATION_IMPLEMENTATION_PLAN.md` §9/§10, gated by that plan's own
Stop Condition W-1 -- independently confirmed closed at the contract +
implementation-identity boundary by Phase 149O.19.5E.4): replaces the
previously hard-coded
`mandatory_consumption_implementation_independently_verified = False`
readiness ceiling in `hatp_mandatory_cutover.py` with fresh HMIC
active-certification validation
(`hatp_mandatory_certification.validate_active_hatp_mandatory_
independent_verification_certification`), mapped via exact
`CertificationStatus.VALID` identity
(`certification_status_satisfies_readiness`).

Scope discipline: this phase wires exactly one of HMRC-REQ-054's six
readiness terms to a new evidence source. It does not create real
certification state, does not activate `HATP_MANDATORY` on any real
host, does not change the HMIC/HMRC/HATP/HSCE/RAE/RWMPC/PBPA/PBPC
contracts, and does not modify `hatp_mandatory_certification.py` or
`scripts/hatp_certification_admin.py` (both remain byte-unchanged --
`hatp_mandatory_certification.py` is inside HMIC v1.1's independently
verified 24-file frozen scope; `hatp_mandatory_cutover.py` itself is
ALSO inside that scope, HMIC-REQ-050's very first entry, so this phase's
one production change legitimately alters the current 24-file
implementation identity -- operationally safe since no real
certification exists anywhere on this host).

`HMIC VALID` supplies exactly one readiness fact. It is never
activation, never PB `ALLOW`, never rollback approval, never execution
capability, never Class-B-deployed, never substrate-operational, and
never runtime/executed-source provenance (HMIC-REQ-063 remains
deferred) -- see `hatp_mandatory_certification.py`'s own `§5 semantic
walls` docstring, restated identically here.

All tests use isolated `tmp_path`-rooted fixtures (mirroring the
149O.19.5D suite's own `env` fixture pattern exactly) -- never
`HATPTrustStore.production().root`, and never this repository's own real
frozen files for mismatch-inducing mutation. No test in this module
activates the real development deployment or creates real certification
state.
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
from pcae.core.hatp_mandatory_cutover import (
    CutoverMode,
    HATPMandatoryActivationReadiness,
    HATPMandatoryActivationReadinessError,
    _activate_hatp_mandatory_at_root,
    _assess_hatp_mandatory_activation_readiness_at_root,
    _resolve_cutover_mode_at_root,
    assess_hatp_mandatory_activation_readiness,
)
from pcae.core.human_approval_trusted_provenance import (
    HATPVerificationSubstrateReadiness,
    HATPVerificationSubstrateStatus,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CUTOVER_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"

#: This repository's last commit before this phase -- used to prove the
#: validator/admin modules are byte-unchanged by this phase.
_PRE_WAVE_F_COMMIT = "dd6492717ea27a43e16bce3e9c2077a884ed366f"

#: This phase's (149O.19.5F's) own final commit -- used, alongside
#: `_PRE_WAVE_F_COMMIT`, to pin "changed/unchanged BY THIS PHASE"
#: assertions to a fixed historical window rather than an open-ended
#: "...HEAD forever" comparison, since Phase 149O.20F later, legitimately
#: changes `hatp_mandatory_certification.py` again (149O.20D.1's
#: HBDC-001 repair, production-aligned by 149O.20F).
_PHASE_149O_19_5F_EXIT_COMMIT = "a786f89f8abb1daba0436198b2a9be1b42a1ce19"


def _historical_frozen_canonical_paths_at(commit: str) -> "list[str]":
    """Reconstructs `_frozen_canonical_paths()`'s output at a fixed
    historical commit, mirroring production's own `src/pcae/`-prefix
    rule -- without relying on the live module, which Phase 149O.20F
    later, legitimately widens to 25 entries."""

    source = _git("show", f"{commit}:src/pcae/core/hatp_mandatory_certification.py")
    tree = ast.parse(source)
    src_relative: "tuple[str, ...]" = ()
    root_relative: "tuple[str, ...]" = ()
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "_FROZEN_SRC_PCAE_RELATIVE_FILES":
                src_relative = tuple(elt.value for elt in node.value.elts)
            elif node.target.id == "_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES":
                root_relative = tuple(elt.value for elt in node.value.elts)
    return [f"src/pcae/{entry}" for entry in src_relative] + list(root_relative)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True).stdout


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test Fixture"], cwd=root, check=True)


def _git_commit_all(root: Path, message: str) -> None:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)


# ═══════════════════════════════════════════════════════════════════════════
# Isolated fixture (mirrors the 149O.19.5D suite's `env` fixture exactly):
# a minimal, fully self-consistent git repository whose frozen-set entries
# and bound-contract files are controlled fixture files, plus a sibling
# isolated protected-root directory shared by both the Cutover Record
# (hatp_mandatory_cutover.py) and the HMIC certification store
# (hatp_mandatory_certification.py) -- exactly mirroring production, where
# both resolve `HATPTrustStore.production().root` to the same directory.
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

    _init_git_repo(repo_root)
    _git_commit_all(repo_root, "initial")

    identity = ensure_repository_identity(HarnessPath(repo_root))
    repository_instance_id = identity.repository_instance_id
    canonical_deployment_root = hmic.derive_canonical_deployment_root(HarnessPath(repo_root))

    return {
        "repo_root": repo_root,
        "protected_root": protected_root,
        "repository_instance_id": repository_instance_id,
        "canonical_deployment_root": canonical_deployment_root,
    }


def _current_hmic_fields(env, *, certified_at="2026-08-11T00:00:00Z", certified_by="protected-admin"):
    root = HarnessPath(env["repo_root"])
    return dict(
        repository_instance_id=env["repository_instance_id"],
        canonical_deployment_root=env["canonical_deployment_root"],
        implementation_commit=hmic.derive_implementation_commit(root),
        implementation_scope_digest=hmic.derive_implementation_scope_digest(root),
        contract_versions=dict(hmic.derive_contract_versions(root)),
        verification_record_digest="c" * 64,
        certified_at=certified_at,
        certified_by=certified_by,
    )


def _record_from_fields(fields: dict, *, status="active", revoked_at=None) -> hmic.CertificationRecord:
    certification_id = hmic.derive_certification_id(fields)
    return hmic.CertificationRecord(certification_id=certification_id, status=status, revoked_at=revoked_at, **fields)


def _store_and_bind(env, record: hmic.CertificationRecord) -> None:
    hmic._append_certification_record(env["protected_root"], record)
    hmic._write_active_binding(
        env["protected_root"],
        hmic.CertificationBinding(
            repository_instance_id=env["repository_instance_id"],
            canonical_deployment_root=env["canonical_deployment_root"],
            active_certification_id=record.certification_id,
        ),
    )


def _valid_certification(env) -> hmic.CertificationRecord:
    record = _record_from_fields(_current_hmic_fields(env))
    _store_and_bind(env, record)
    return record


def _fake_operational_substrate(*_args, **_kwargs) -> HATPVerificationSubstrateReadiness:
    return HATPVerificationSubstrateReadiness(
        status=HATPVerificationSubstrateStatus.OPERATIONAL,
        operational=True,
        terms=(("fixture_forced_operational", True),),
        reasons=(),
    )


class _FakeTrustStore:
    """A non-`None`, never-constructed-via-`.production()` stand-in --
    only `production_dependency_provenance_valid` (`trust_store is not
    None`) and `hatp_substrate_operational`'s own `trust_store is not
    None` gate care about its identity here; `inspect_hatp_verification_
    substrate_readiness` itself is monkeypatched below rather than made
    to genuinely inspect this fake."""


def _patch_production_trust_root(env, monkeypatch) -> None:
    """`validate_active_hatp_mandatory_independent_verification_
    certification` (HMIC-REQ-109/111) always resolves `HATPTrustStore.
    production().root` internally -- by design, it accepts no
    caller-suppliable root override (the same discipline
    `test_no_root_override_env_or_flag_accepted` in the 149O.19.5D suite
    independently proves). To exercise the REAL production validator
    end-to-end against an isolated fixture, the isolation point is
    `HATPTrustStore.production()` itself -- mirroring its own
    constructor's documented `_test_only_root` test seam -- never a
    parameter threaded through the validator."""

    monkeypatch.setattr(HATPTrustStore, "production", classmethod(lambda cls: cls(_test_only_root=env["protected_root"])))


def _assess(env, *, monkeypatch, operational_substrate: bool = True) -> HATPMandatoryActivationReadiness:
    """Full-fixture readiness assessment: real fresh HMIC validation via
    the actual validator (never mocked), plus the other five HMRC-REQ-054
    terms modeled through isolated/test seams -- `hatp_substrate_
    operational` is the only one monkeypatched (a genuine Class-B
    hardware-provider fixture is out of this phase's scope; see phase
    prompt item 65's "if it can safely be modeled" allowance)."""
    _patch_production_trust_root(env, monkeypatch)
    if operational_substrate:
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
    return _assess_hatp_mandatory_activation_readiness_at_root(
        env["protected_root"],
        env["repository_instance_id"],
        repository_root=env["repo_root"],
        trust_store=_FakeTrustStore(),
    )


def _check(readiness: HATPMandatoryActivationReadiness, name: str):
    return next(c for c in readiness.checks if c.name == name)


_HMIC_CHECK_NAME = "mandatory_consumption_implementation_independently_verified"


# ═══════════════════════════════════════════════════════════════════════════
# 1. Frozen-scope disposition (governing-prompt items 53-54)
# ═══════════════════════════════════════════════════════════════════════════


class TestFrozenScopeDisposition:
    def test_cutover_module_is_inside_the_24_file_frozen_scope(self) -> None:
        # Pinned to this phase's own exit commit: Phase 149O.20F later,
        # legitimately widens the live frozen scope to 25 entries
        # (149O.20D.1's HBDC-001 repair); this phase's own claim -- 24
        # entries as of ITS OWN conclusion -- is preserved unweakened.
        paths = _historical_frozen_canonical_paths_at(_PHASE_149O_19_5F_EXIT_COMMIT)
        assert "src/pcae/core/hatp_mandatory_cutover.py" in paths
        assert len(paths) == 24

    def test_certification_and_admin_modules_byte_unchanged_by_this_phase(self) -> None:
        # Pinned to this phase's own exit commit, not live bytes: Phase
        # 149O.20F later, legitimately changes
        # `hatp_mandatory_certification.py` again -- this assertion's
        # claim is about THIS phase's own (149O.19.5F's) diff window.
        for rel in ("src/pcae/core/hatp_mandatory_certification.py", "scripts/hatp_certification_admin.py"):
            at_exit = subprocess.run(
                ["git", "show", f"{_PHASE_149O_19_5F_EXIT_COMMIT}:{rel}"],
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.encode("utf-8")
            pre_wave_f = subprocess.run(
                ["git", "show", f"{_PRE_WAVE_F_COMMIT}:{rel}"],
                cwd=str(_REPO_ROOT),
                capture_output=True,
                text=True,
                check=True,
            ).stdout.encode("utf-8")
            assert at_exit == pre_wave_f, f"{rel} was modified by this phase but must remain byte-unchanged"

    def test_all_eight_bound_contracts_byte_unchanged_by_this_phase(self) -> None:
        contracts = (
            "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
            "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
            "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
            "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
            "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
            "docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
            "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
            "docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
        )
        diff = _git("diff", "--name-only", _PRE_WAVE_F_COMMIT, "--", *contracts)
        assert diff.strip() == ""


# ═══════════════════════════════════════════════════════════════════════════
# 2. No caller-suppliable authority input (governing-prompt items 61-62)
# ═══════════════════════════════════════════════════════════════════════════


class TestNoCallerSuppliableAuthorityInput:
    def test_public_readiness_entrypoint_signature(self) -> None:
        assert list(inspect.signature(assess_hatp_mandatory_activation_readiness).parameters) == ["root"]

    def test_internal_seam_has_no_forbidden_authority_params(self) -> None:
        forbidden = {"hmic_valid", "validation_result", "validator", "hmic_verified", "certification_valid"}
        params = set(inspect.signature(_assess_hatp_mandatory_activation_readiness_at_root).parameters)
        assert params.isdisjoint(forbidden)

    def test_no_admin_script_import(self) -> None:
        source = _CUTOVER_PATH.read_text(encoding="utf-8")
        assert "hatp_certification_admin" not in source

    def test_no_write_call_reachable_from_readiness_source(self) -> None:
        source = inspect.getsource(_assess_hatp_mandatory_activation_readiness_at_root)
        for forbidden in ("certify(", "_append_certification_record", "_write_active_binding", "_write_revocation"):
            assert forbidden not in source

    def test_import_is_narrow_not_wildcard(self) -> None:
        source = _CUTOVER_PATH.read_text(encoding="utf-8")
        assert "from pcae.core.hatp_mandatory_certification import *" not in source
        assert "certification_status_satisfies_readiness" in source
        assert "validate_active_hatp_mandatory_independent_verification_certification" in source


# ═══════════════════════════════════════════════════════════════════════════
# 3. Exact enum mapping (HMIC-REQ-107) -- VALID -> True, every other
#    member -> False. No truthiness, no string comparison.
# ═══════════════════════════════════════════════════════════════════════════


class TestExactEnumMapping:
    @pytest.mark.parametrize("status", list(hmic.CertificationStatus))
    def test_certification_status_satisfies_readiness_exact_identity(self, status) -> None:
        expected = status is hmic.CertificationStatus.VALID
        assert hmic.certification_status_satisfies_readiness(status) is expected

    def test_mapping_uses_the_shared_production_helper_not_a_local_reimplementation(self) -> None:
        source = inspect.getsource(_assess_hatp_mandatory_activation_readiness_at_root)
        assert "certification_status_satisfies_readiness" in source
        # No local truthiness/string comparison against "VALID".
        assert '== "VALID"' not in source
        assert "!= hmic.CertificationStatus.ERROR" not in source


class TestRealValidatorIntegrationEveryStatus:
    """Real Wave-D validator against isolated fixtures (never only
    mocked) -- for each production `CertificationStatus`, drives the
    validator to that exact outcome and confirms the readiness item
    follows `certification_status_satisfies_readiness` exactly."""

    def test_valid(self, env, monkeypatch) -> None:
        _valid_certification(env)
        readiness = _assess(env, monkeypatch=monkeypatch)
        assert _check(readiness, _HMIC_CHECK_NAME).satisfied is True
        assert readiness.ready is True

    def test_missing_no_binding(self, env, monkeypatch) -> None:
        readiness = _assess(env, monkeypatch=monkeypatch)
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False
        assert "MISSING" in check.detail

    def test_revoked(self, env, monkeypatch) -> None:
        record = _valid_certification(env)
        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-11T01:00:00Z")
        readiness = _assess(env, monkeypatch=monkeypatch)
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False
        assert "REVOKED" in check.detail

    def test_implementation_mismatch(self, env, monkeypatch) -> None:
        _valid_certification(env)
        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"tampered\n")
        readiness = _assess(env, monkeypatch=monkeypatch)
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False
        assert "IMPLEMENTATION_MISMATCH" in check.detail

    def test_contract_mismatch(self, env, monkeypatch) -> None:
        # A record whose stored contract_versions drifted from the live
        # contract headers, without perturbing the frozen-file digest at
        # all (mirrors the Wave D suite's own CONTRACT_MISMATCH fixture).
        fields = _current_hmic_fields(env)
        fields["contract_versions"] = {**fields["contract_versions"], "HMRC-001": "9.9"}
        record = _record_from_fields(fields)
        _store_and_bind(env, record)
        readiness = _assess(env, monkeypatch=monkeypatch)
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False
        assert "CONTRACT_MISMATCH" in check.detail

    def test_wrong_repository(self, env, monkeypatch) -> None:
        fields = _current_hmic_fields(env)
        fields["repository_instance_id"] = "22222222-2222-4222-8222-222222222222"
        record = _record_from_fields(fields)
        hmic._append_certification_record(env["protected_root"], record)
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id="22222222-2222-4222-8222-222222222222",
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id=record.certification_id,
            ),
        )
        readiness = _assess(env, monkeypatch=monkeypatch)
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False

    def test_malformed_binding_fails_closed_not_missing_or_fatal(self, env, monkeypatch) -> None:
        bindings_path = env["protected_root"] / "certification-bindings.json"
        env["protected_root"].mkdir(parents=True, exist_ok=True)
        bindings_path.write_text("{not valid json", encoding="utf-8")
        readiness = _assess(env, monkeypatch=monkeypatch)
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False
        assert readiness.ready is False


# ═══════════════════════════════════════════════════════════════════════════
# 4. Validation-exception fail-closed (governing-prompt item 12)
# ═══════════════════════════════════════════════════════════════════════════


class TestValidationExceptionFailsClosed:
    def test_validator_exception_maps_to_false_not_fatal(self, env, monkeypatch) -> None:
        def _boom(_repository_root):
            raise RuntimeError("simulated validator failure")

        monkeypatch.setattr(cutover, "validate_active_hatp_mandatory_independent_verification_certification", _boom)
        readiness = _assess(env, monkeypatch=monkeypatch)
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False
        assert "RuntimeError" in check.detail
        assert readiness.ready is False

    def test_no_repository_root_supplied_fails_closed(self, tmp_path) -> None:
        readiness = _assess_hatp_mandatory_activation_readiness_at_root(tmp_path / "root", "11111111-1111-4111-8111-111111111111")
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False


# ═══════════════════════════════════════════════════════════════════════════
# 5. Six-item conjunction preservation (governing-prompt items 15/48/49)
# ═══════════════════════════════════════════════════════════════════════════

_SIX_HMRC_REQ_054_ITEMS = frozenset(
    {
        "class_b_protected_storage_available",
        "hatp_substrate_operational",
        "hsce_signing_implementation_available",
        "mandatory_consumption_implementation_independently_verified",
        "production_dependency_provenance_valid",
        "protected_activation_authority_mechanism_available",
    }
)


class TestSixItemConjunctionPreserved:
    def test_readiness_check_names_unchanged(self, env, monkeypatch) -> None:
        readiness = _assess(env, monkeypatch=monkeypatch)
        names = {c.name for c in readiness.checks}
        assert _SIX_HMRC_REQ_054_ITEMS <= names
        assert "repository_deployment_identity_valid" in names  # module-owned, 7th check
        assert len(names) == 7

    def test_no_seventh_hmrc_054_item_introduced(self) -> None:
        source = inspect.getsource(_assess_hatp_mandatory_activation_readiness_at_root)
        tree = ast.parse(source)
        appends = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "attr", None) == "append"]
        assert len(appends) == 7

    def test_other_five_checks_ast_unchanged_since_phase_entry(self) -> None:
        """Only the mandatory_consumption_implementation_independently_
        verified check's own construction differs; every other check's
        AST is unchanged since the pre-Wave-F phase entry."""
        pre = subprocess.run(
            ["git", "show", f"{_PRE_WAVE_F_COMMIT}:src/pcae/core/hatp_mandatory_cutover.py"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        post_source = _CUTOVER_PATH.read_text(encoding="utf-8")

        def _check_blocks(source: str) -> dict:
            tree = ast.parse(source)
            fn = next(
                n
                for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == "_assess_hatp_mandatory_activation_readiness_at_root"
            )
            blocks: dict = {}
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "append":
                    dumped = ast.dump(node)
                    # crude name extraction: first string literal argument's value
                    name = None
                    for n2 in ast.walk(node):
                        if isinstance(n2, ast.Constant) and isinstance(n2.value, str) and n2.value in _SIX_HMRC_REQ_054_ITEMS | {"repository_deployment_identity_valid"}:
                            name = n2.value
                            break
                    if name:
                        blocks[name] = dumped
            return blocks

        pre_blocks = _check_blocks(pre)
        post_blocks = _check_blocks(post_source)
        assert set(pre_blocks) == set(post_blocks)
        for name in pre_blocks:
            if name == _HMIC_CHECK_NAME:
                assert pre_blocks[name] != post_blocks[name], "expected this one check's construction to change"
            else:
                assert pre_blocks[name] == post_blocks[name], f"unexpected change to unrelated check {name!r}"


class TestOverrideNeverBypassesOtherChecks:
    def test_hmic_valid_with_one_other_check_false_yields_overall_false(self, env, monkeypatch) -> None:
        _valid_certification(env)
        # Do not force substrate operational -> hatp_substrate_operational stays False.
        readiness = _assess(env, monkeypatch=monkeypatch, operational_substrate=False)
        assert _check(readiness, _HMIC_CHECK_NAME).satisfied is True
        assert _check(readiness, "hatp_substrate_operational").satisfied is False
        assert readiness.ready is False

    def test_hmic_non_valid_with_other_five_true_yields_overall_false(self, env, monkeypatch) -> None:
        # No certification stored -> HMIC MISSING -> False; force the other five true.
        readiness = _assess(env, monkeypatch=monkeypatch, operational_substrate=True)
        assert _check(readiness, _HMIC_CHECK_NAME).satisfied is False
        for name in _SIX_HMRC_REQ_054_ITEMS - {_HMIC_CHECK_NAME}:
            assert _check(readiness, name).satisfied is True, name
        assert readiness.ready is False


class TestFullPositiveFixture:
    def test_all_six_true_yields_overall_ready(self, env, monkeypatch) -> None:
        _valid_certification(env)
        readiness = _assess(env, monkeypatch=monkeypatch, operational_substrate=True)
        for name in _SIX_HMRC_REQ_054_ITEMS:
            assert _check(readiness, name).satisfied is True, name
        assert readiness.ready is True
        assert readiness.reasons == ()


# ═══════════════════════════════════════════════════════════════════════════
# 6. Freshness / no cache (HMRC-REQ-052 extended, item 74)
# ═══════════════════════════════════════════════════════════════════════════


class TestFreshnessNoCache:
    def test_repeated_calls_reflect_state_changes_no_memoization(self, env, monkeypatch) -> None:
        _patch_production_trust_root(env, monkeypatch)
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        _patch_production_trust_root(env, monkeypatch)
        first = _assess_hatp_mandatory_activation_readiness_at_root(
            env["protected_root"], env["repository_instance_id"], repository_root=env["repo_root"], trust_store=_FakeTrustStore()
        )
        assert _check(first, _HMIC_CHECK_NAME).satisfied is False

        _valid_certification(env)
        second = _assess_hatp_mandatory_activation_readiness_at_root(
            env["protected_root"], env["repository_instance_id"], repository_root=env["repo_root"], trust_store=_FakeTrustStore()
        )
        assert _check(second, _HMIC_CHECK_NAME).satisfied is True

    def test_no_cache_decorator_anywhere_in_cutover_module(self) -> None:
        source = _CUTOVER_PATH.read_text(encoding="utf-8")
        for forbidden in ("lru_cache", "functools.cache", "cached_property"):
            assert forbidden not in source


# ═══════════════════════════════════════════════════════════════════════════
# 7. Lock-held recheck / TOCTOU races (governing-prompt items 26-32,
#    69-73, 106-109)
# ═══════════════════════════════════════════════════════════════════════════


def _write_prepared(protected_root: Path, repository_instance_id: str) -> None:
    cutover._write_cutover_transition(
        protected_root,
        target_mode=CutoverMode.PREPARED,
        repository_instance_id=repository_instance_id,
        activated_by="test-operator",
    )


class TestLockHeldRecheckAndTOCTOU:
    def test_successful_activation_in_fully_positive_isolated_fixture(self, env, monkeypatch) -> None:
        """The only place this suite observes a real state transition:
        an isolated fixture with all six readiness terms genuinely
        satisfied. Never touches the real host."""
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        _patch_production_trust_root(env, monkeypatch)
        _valid_certification(env)
        _write_prepared(env["protected_root"], env["repository_instance_id"])

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

    def test_revocation_between_assessment_and_activation_blocks_activation(self, env, monkeypatch) -> None:
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        _patch_production_trust_root(env, monkeypatch)
        record = _valid_certification(env)
        _write_prepared(env["protected_root"], env["repository_instance_id"])

        pre_lock = _assess_hatp_mandatory_activation_readiness_at_root(
            env["protected_root"], env["repository_instance_id"], repository_root=env["repo_root"], trust_store=_FakeTrustStore()
        )
        assert pre_lock.ready is True  # stale, now-unused "was ready" snapshot

        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-11T02:00:00Z")

        record_path = env["protected_root"] / "cutover-record.json"
        before = record_path.read_bytes()
        with pytest.raises(HATPMandatoryActivationReadinessError):
            _activate_hatp_mandatory_at_root(
                env["protected_root"],
                env["repository_instance_id"],
                activated_by="op",
                repository_root=env["repo_root"],
                trust_store=_FakeTrustStore(),
            )
        after = record_path.read_bytes()
        assert before == after
        resolution = _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"])
        assert resolution.mode == CutoverMode.PREPARED
        assert not (env["protected_root"] / "cutover-activation-marker.json").exists()

    def test_binding_change_between_assessment_and_activation_blocks_activation(self, env, monkeypatch) -> None:
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        _patch_production_trust_root(env, monkeypatch)
        _valid_certification(env)
        _write_prepared(env["protected_root"], env["repository_instance_id"])

        pre_lock = _assess_hatp_mandatory_activation_readiness_at_root(
            env["protected_root"], env["repository_instance_id"], repository_root=env["repo_root"], trust_store=_FakeTrustStore()
        )
        assert pre_lock.ready is True

        # Re-point the active binding at a certification_id with no record.
        hmic._write_active_binding(
            env["protected_root"],
            hmic.CertificationBinding(
                repository_instance_id=env["repository_instance_id"],
                canonical_deployment_root=env["canonical_deployment_root"],
                active_certification_id="0" * 64,
            ),
        )

        with pytest.raises(HATPMandatoryActivationReadinessError):
            _activate_hatp_mandatory_at_root(
                env["protected_root"],
                env["repository_instance_id"],
                activated_by="op",
                repository_root=env["repo_root"],
                trust_store=_FakeTrustStore(),
            )
        resolution = _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"])
        assert resolution.mode == CutoverMode.PREPARED

    def test_implementation_drift_between_assessment_and_activation_blocks_activation(self, env, monkeypatch) -> None:
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        _patch_production_trust_root(env, monkeypatch)
        _valid_certification(env)
        _write_prepared(env["protected_root"], env["repository_instance_id"])

        pre_lock = _assess_hatp_mandatory_activation_readiness_at_root(
            env["protected_root"], env["repository_instance_id"], repository_root=env["repo_root"], trust_store=_FakeTrustStore()
        )
        assert pre_lock.ready is True

        (env["repo_root"] / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"drifted content\n")

        with pytest.raises(HATPMandatoryActivationReadinessError):
            _activate_hatp_mandatory_at_root(
                env["protected_root"],
                env["repository_instance_id"],
                activated_by="op",
                repository_root=env["repo_root"],
                trust_store=_FakeTrustStore(),
            )
        resolution = _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"])
        assert resolution.mode == CutoverMode.PREPARED

    def test_lock_held_recheck_calls_validator_after_lock_acquired(self, env, monkeypatch) -> None:
        """Instruments the real activation flow to prove fresh HMIC
        validation occurs while the transition lock is held, not before."""
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        _patch_production_trust_root(env, monkeypatch)
        _valid_certification(env)
        _write_prepared(env["protected_root"], env["repository_instance_id"])

        calls = []
        real_validate = hmic.validate_active_hatp_mandatory_independent_verification_certification

        def _instrumented(repository_root):
            calls.append(repository_root)
            return real_validate(repository_root)

        monkeypatch.setattr(cutover, "validate_active_hatp_mandatory_independent_verification_certification", _instrumented)

        calls_before_activation = len(calls)
        _activate_hatp_mandatory_at_root(
            env["protected_root"],
            env["repository_instance_id"],
            activated_by="op",
            repository_root=env["repo_root"],
            trust_store=_FakeTrustStore(),
        )
        assert len(calls) > calls_before_activation


# ═══════════════════════════════════════════════════════════════════════════
# 8. One-way cutover: revocation after activation never downgrades
#    HATP_MANDATORY (governing-prompt items 32-34)
# ═══════════════════════════════════════════════════════════════════════════


class TestOneWayCutoverAfterActivation:
    def test_revocation_after_activation_does_not_downgrade_mandatory(self, env, monkeypatch) -> None:
        monkeypatch.setattr(cutover, "inspect_hatp_verification_substrate_readiness", _fake_operational_substrate)
        _patch_production_trust_root(env, monkeypatch)
        record = _valid_certification(env)
        _write_prepared(env["protected_root"], env["repository_instance_id"])
        _activate_hatp_mandatory_at_root(
            env["protected_root"],
            env["repository_instance_id"],
            activated_by="op",
            repository_root=env["repo_root"],
            trust_store=_FakeTrustStore(),
        )
        resolution = _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"])
        assert resolution.mode == CutoverMode.HATP_MANDATORY

        hmic._write_revocation(env["protected_root"], certification_id=record.certification_id, revoked_at="2026-08-11T03:00:00Z")

        # Readiness may now honestly report the HMIC term unmet ...
        readiness = _assess(env, monkeypatch=monkeypatch, operational_substrate=True)
        assert _check(readiness, _HMIC_CHECK_NAME).satisfied is False
        # ... but the protected cutover state itself is one-way and unaffected.
        resolution_after = _resolve_cutover_mode_at_root(env["protected_root"], env["repository_instance_id"])
        assert resolution_after.mode == CutoverMode.HATP_MANDATORY

    def test_no_code_path_downgrades_mandatory_to_prepared_or_legacy(self) -> None:
        source = _CUTOVER_PATH.read_text(encoding="utf-8")
        # The only two writable transitions are LEGACY->PREPARED and
        # PREPARED->HATP_MANDATORY (unchanged by this phase).
        assert "(CutoverMode.HATP_MANDATORY, CutoverMode.PREPARED)" not in source
        assert "(CutoverMode.HATP_MANDATORY, CutoverMode.LEGACY_COMPATIBLE)" not in source


# ═══════════════════════════════════════════════════════════════════════════
# 9. Current real-host readiness (read-only; governing-prompt items 17/58)
# ═══════════════════════════════════════════════════════════════════════════


class TestCurrentRealHostReadiness:
    def test_real_host_readiness_is_not_ready_and_hmic_item_is_unmet(self) -> None:
        """Read-only against the real production paths. No certification
        state, protected root, or cutover record exists on this host, so
        this must honestly report not-ready -- never fabricate readiness,
        never mutate anything as a side effect."""
        certifications_marker = HATPTrustStore.production().root / "certifications.json"
        assert not certifications_marker.exists()

        readiness = assess_hatp_mandatory_activation_readiness(HarnessPath.cwd())
        assert readiness.ready is False
        check = _check(readiness, _HMIC_CHECK_NAME)
        assert check.satisfied is False

        # Still read-only afterward -- no certification state fabricated.
        assert not certifications_marker.exists()


# ═══════════════════════════════════════════════════════════════════════════
# 10. Production diff classification -- every production hunk this phase
#     introduces is directly tied to the readiness-integration wiring.
# ═══════════════════════════════════════════════════════════════════════════


class TestProductionDiffClassification:
    def test_only_cutover_module_changed_in_src_pcae(self) -> None:
        # Pinned to this phase's own exit commit, not an open-ended
        # "...HEAD forever" comparison: Phase 149O.20F later, legitimately
        # changes a second `src/pcae/**` file
        # (`hatp_mandatory_certification.py`, well after this phase
        # concluded).
        diff = _git("diff", "--name-only", _PRE_WAVE_F_COMMIT, _PHASE_149O_19_5F_EXIT_COMMIT, "--", "src/pcae/")
        changed = [ln for ln in diff.splitlines() if ln.strip()]
        assert changed == ["src/pcae/core/hatp_mandatory_cutover.py"]

    def test_no_scripts_file_changed(self) -> None:
        diff = _git("diff", "--name-only", _PRE_WAVE_F_COMMIT, "--", "scripts/")
        assert diff.strip() == ""

    def test_diff_hunks_are_import_validation_call_or_readiness_mapping_only(self) -> None:
        diff = _git("diff", "-U0", _PRE_WAVE_F_COMMIT, "--", "src/pcae/core/hatp_mandatory_cutover.py")
        added_lines = [
            line[1:]
            for line in diff.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        joined = "\n".join(added_lines)
        # Every substantive addition belongs to one of: the narrow import,
        # the HMIC validation call/mapping, diagnostics, or the
        # repository_root plumbing needed to reach the validator/lock-held
        # recheck. No unrelated addition (e.g. new CLI surface, new PB
        # call, new contract text) exists.
        assert "hatp_mandatory_certification" in joined
        assert "PermissionBroker" not in joined
        assert "evaluate_for_real_effect" not in joined
        assert "DECISION_ALLOW" not in joined


# ═══════════════════════════════════════════════════════════════════════════
# 11. No real activation / no real certification state (restated;
#     governing-prompt items 18/89/121)
# ═══════════════════════════════════════════════════════════════════════════


class TestNoRealEffects:
    def test_no_real_certification_state_exists_on_host(self) -> None:
        root = HATPTrustStore.production().root
        assert not (root / "certifications.json").exists()
        assert not (root / "certification-bindings.json").exists()

    def test_no_real_cutover_record_exists_on_host(self) -> None:
        root = HATPTrustStore.production().root
        assert not (root / "cutover-record.json").exists()
        assert not (root / "cutover-activation-marker.json").exists()

    def test_activate_hatp_mandatory_is_never_called_from_cli_or_agent(self) -> None:
        for rel in ("src/pcae/cli.py", "src/pcae/commands/agent.py", "src/pcae/core/agent.py"):
            source = (_REPO_ROOT / rel).read_text(encoding="utf-8")
            assert "activate_hatp_mandatory" not in source
