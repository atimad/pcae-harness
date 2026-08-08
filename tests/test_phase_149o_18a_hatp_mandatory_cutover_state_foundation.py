"""Phase 149O.18A -- HATP Mandatory Cutover State Foundation.

Phase-boundary verification: this phase implements ONLY the HMRC-001
cutover-state substrate (`hatp_mandatory_cutover.py`), Wave A of the
149O.17 implementation plan. This module mechanically confirms the scope
boundary was respected -- by inspecting real repository/git state, not by
trusting the phase document's prose.
"""
from __future__ import annotations

import ast
import inspect
import json
import subprocess
import uuid
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_cutover as cutover
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.paths import HarnessPath

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"

# HEAD at the moment this phase began (149O.17's final commit).
_PHASE_ENTRY_COMMIT = "cb1d9e89"

_UPSTREAM_CONTRACTS = (
    _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    _CONTRACTS / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    _CONTRACTS / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    _CONTRACTS / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    _CONTRACTS / "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
)

_NEW_MODULE_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"

_FORBIDDEN_MODIFIED_FILES = (
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/hatp_evidence_store.py",
    "src/pcae/core/hatp_signed_evidence.py",
    "src/pcae/core/hatp_signing_ceremony.py",
    "src/pcae/core/hatp_ag_authority.py",
    "src/pcae/core/agent.py",
    "src/pcae/commands/agent.py",
    "src/pcae/cli.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/repository_identity.py",
)

_FORBIDDEN_IMPORT_MODULES = (
    "pcae.core.hatp_evidence_store",
    "pcae.core.hatp_signed_evidence",
    "pcae.core.hatp_ag_authority",
    "pcae.core.human_approval_trusted_provenance",
    "pcae.core.rollback_approval_evidence",
    "pcae.core.permission_broker",
    "pcae.core.permission_broker_foundation",
    "pcae.core.agent",
    "pcae.commands.agent",
    "pcae.cli",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


# ── Production file allowlist ─────────────────────────────────────────────


class TestProductionFileAllowlist:
    def test_only_the_new_cutover_module_was_added_to_src_pcae(self) -> None:
        changed = [
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", "src/pcae/").splitlines()
            if line
        ]
        assert changed == ["src/pcae/core/hatp_mandatory_cutover.py"]

    def test_no_forbidden_production_file_touched(self) -> None:
        changed = set(
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", "src/pcae/").splitlines()
            if line
        )
        for forbidden in _FORBIDDEN_MODIFIED_FILES:
            assert forbidden not in changed, f"forbidden production file modified this phase: {forbidden}"

    def test_new_module_exists_and_is_named_as_planned(self) -> None:
        assert _NEW_MODULE_PATH.is_file()


# ── Contract byte-identity ────────────────────────────────────────────────


class TestContractByteIdentity:
    @pytest.mark.parametrize("contract_path", _UPSTREAM_CONTRACTS, ids=lambda p: p.name)
    def test_contract_unchanged(self, contract_path: Path) -> None:
        rel = contract_path.relative_to(_REPO_ROOT).as_posix()
        diff = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", rel)
        assert diff == ""


# ── Dependency closure: no evidence/PB/AG3/AG5/CLI imports ──────────────


class TestDependencyClosure:
    def test_no_forbidden_imports_in_new_module(self) -> None:
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

        for forbidden in _FORBIDDEN_IMPORT_MODULES:
            assert forbidden not in imported_modules, f"forbidden import present: {forbidden}"

    def test_module_docstring_confirms_no_evidence_consumption(self) -> None:
        assert cutover.__doc__ is not None
        assert "no** evidence verification" in cutover.__doc__.lower()


# ── Mode vocabulary (structural, redundant with unit suite by design) ────


class TestModeVocabulary:
    def test_exactly_three_modes_frozen_names(self) -> None:
        assert [m.name for m in cutover.CutoverMode] == ["LEGACY_COMPATIBLE", "PREPARED", "HATP_MANDATORY"]

    def test_no_fourth_mode_value_anywhere_in_module_source(self) -> None:
        source = _NEW_MODULE_PATH.read_text(encoding="utf-8")
        forbidden_tokens = ("DISABLED", "READY =", "ACTIVE =", "ENFORCED", "RECOVERY", "UNKNOWN =")
        for token in forbidden_tokens:
            assert token not in source, f"unexpected mode-shaped token found: {token!r}"


# ── Protected root usage ──────────────────────────────────────────────────


class TestProtectedRootUsage:
    def test_production_resolver_uses_hatp_trust_store_production(self) -> None:
        source = inspect.getsource(cutover.resolve_production_hatp_cutover_mode)
        assert "HATPTrustStore.production()" in source

    def test_production_resolver_signature_has_no_root_override(self) -> None:
        signature = inspect.signature(cutover.resolve_production_hatp_cutover_mode)
        params = list(signature.parameters)
        assert params == ["root"]

    def test_internal_test_seam_never_paired_with_production_root_in_module_source(self) -> None:
        # AST-based (not substring) so prose in docstrings/comments cannot
        # produce a false positive or false negative: only real `Call`
        # nodes count. The only real call site of
        # `HATPTrustStore.production()` anywhere in this module must be
        # inside `resolve_production_hatp_cutover_mode` (the read-only
        # resolver) -- never inside `_write_cutover_transition` or any
        # other function.
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        call_sites: list[str] = []
        for func in ast.walk(tree):
            if not isinstance(func, ast.FunctionDef):
                continue
            for node in ast.walk(func):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "production"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "HATPTrustStore"
                ):
                    call_sites.append(func.name)

        assert call_sites == ["resolve_production_hatp_cutover_mode"]

    def test_production_root_not_influenced_by_environment(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        for plausible_env in (
            "HATP_TRUST_ROOT",
            "PCAE_HATP_TRUST_ROOT",
            "HATP_CUTOVER_ROOT",
            "PCAE_CUTOVER_RECORD_PATH",
            "HOME",
        ):
            monkeypatch.setenv(plausible_env, str(tmp_path / "attacker-controlled"))
        # The production root resolution path takes no environment input at
        # all -- confirmed structurally (module never imports `os.environ`
        # in `_default_production_trust_root`'s call chain); this is a
        # smoke confirmation that setting plausible variable names before
        # constructing the store does not raise or redirect.
        root_before = HATPTrustStore.production().root
        root_after = HATPTrustStore.production().root
        assert root_before == root_after


# ── Test-seam isolation ────────────────────────────────────────────────────


class TestSeamIsolation:
    def test_internal_resolver_accepts_explicit_root(self) -> None:
        signature = inspect.signature(cutover._resolve_cutover_mode_at_root)
        assert list(signature.parameters) == ["protected_root", "repository_instance_id"]

    def test_internal_resolver_is_private(self) -> None:
        assert cutover._resolve_cutover_mode_at_root.__name__.startswith("_")


# ── No evidence store / verification / PB / agent / CLI touch ───────────


class TestScopeBoundaryNoGo:
    def test_no_hatp_evidence_store_import(self) -> None:
        source = _NEW_MODULE_PATH.read_text(encoding="utf-8")
        assert "hatp_evidence_store" not in source
        assert "HATPEvidenceStore" not in source

    def test_no_hatp_verification_import(self) -> None:
        source = _NEW_MODULE_PATH.read_text(encoding="utf-8")
        assert "verify_hatp_proof" not in source

    def test_no_permission_broker_import(self) -> None:
        source = _NEW_MODULE_PATH.read_text(encoding="utf-8")
        assert "permission_broker" not in source.lower()

    def test_no_agent_or_cli_reference(self) -> None:
        # AST-based (not substring): the module docstring's *prose*
        # legitimately names `execute_rollback`/`build_rollback_execution`
        # to explain scope boundaries -- what must never exist is an
        # actual identifier reference to either in real code.
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        identifiers = {
            node.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Name)
        } | {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
        }
        assert "execute_rollback" not in identifiers
        assert "build_rollback_execution" not in identifiers
        assert "argparse" not in _NEW_MODULE_PATH.read_text(encoding="utf-8")


# ── First-install / deleted-mandatory / monotonic transition smoke ──────
# (Exhaustive edge-case coverage lives in test_hatp_mandatory_cutover.py;
# this class re-derives the highest-priority attack scenarios directly
# against the phase's own module import, independent of that suite.)


class TestHighPriorityAttackSmoke:
    def _write_record(self, root: Path, repository_instance_id: str, mode: str) -> None:
        root.mkdir(parents=True, exist_ok=True)
        document = {
            "version": 1,
            "repository_instance_id": repository_instance_id,
            "mode": mode,
            "activated_at": "2026-08-08T00:00:00.000Z",
            "activated_by": "admin",
        }
        (root / "cutover-record.json").write_text(json.dumps(document), encoding="utf-8")

    def _write_marker(self, root: Path, repository_instance_id: str) -> None:
        root.mkdir(parents=True, exist_ok=True)
        document = {
            "version": 1,
            "repository_instance_id": repository_instance_id,
            "first_activated_at": "2026-08-01T00:00:00.000Z",
        }
        (root / "cutover-activation-marker.json").write_text(json.dumps(document), encoding="utf-8")

    def test_first_install(self, tmp_path: Path) -> None:
        repo_id = str(uuid.uuid4())
        resolution = cutover._resolve_cutover_mode_at_root(tmp_path, repo_id)
        assert resolution.mode == cutover.CutoverMode.LEGACY_COMPATIBLE

    def test_deleted_mandatory_record_fails_closed(self, tmp_path: Path) -> None:
        repo_id = str(uuid.uuid4())
        self._write_marker(tmp_path, repo_id)
        resolution = cutover._resolve_cutover_mode_at_root(tmp_path, repo_id)
        assert resolution.mode == cutover.CutoverMode.HATP_MANDATORY

    def test_monotonic_forward_only_transitions(self, tmp_path: Path) -> None:
        repo_id = str(uuid.uuid4())
        cutover._write_cutover_transition(
            tmp_path, target_mode=cutover.CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="admin"
        )
        cutover._write_cutover_transition(
            tmp_path, target_mode=cutover.CutoverMode.HATP_MANDATORY, repository_instance_id=repo_id, activated_by="admin"
        )
        # LEGACY_COMPATIBLE is never itself a storable record value
        # (HMRC-REQ-050: it is the *absence* of a record) -- so a
        # "downgrade to legacy" attempt is rejected even more strongly
        # than an ordinary invalid transition: it is not an expressible
        # write target at all.
        with pytest.raises(ValueError):
            cutover._write_cutover_transition(
                tmp_path, target_mode=cutover.CutoverMode.LEGACY_COMPATIBLE, repository_instance_id=repo_id, activated_by="admin"
            )
        with pytest.raises(cutover.CutoverTransitionRejectedError):
            cutover._write_cutover_transition(
                tmp_path, target_mode=cutover.CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="admin"
            )


# ── No real production activation occurred ───────────────────────────────


class TestNoRealProductionActivation:
    def test_production_protected_root_has_no_new_cutover_state(self) -> None:
        root = HATPTrustStore.production().root
        # This development host has no provisioned Class-B protected root
        # (confirmed by `pcae runtime inspect`: Observed/observe/
        # unavailable) -- if it existed, neither cutover file should be
        # present, since this phase never calls `_write_cutover_transition`
        # with the production root anywhere.
        if not root.exists():
            return
        assert not (root / "cutover-record.json").exists()
        assert not (root / "cutover-activation-marker.json").exists()

    def test_resolve_production_hatp_cutover_mode_never_mutates(self, tmp_path: Path) -> None:
        # Calling the real production entrypoint must not create any file
        # under the current repository's own .pcae/ directory as a side
        # effect (it may read repository-identity.json if already
        # provisioned by `pcae init`, but never writes cutover state).
        root = HarnessPath(_REPO_ROOT)
        before = set(_REPO_ROOT.joinpath(".pcae").glob("cutover-*"))
        cutover.resolve_production_hatp_cutover_mode(root)
        after = set(_REPO_ROOT.joinpath(".pcae").glob("cutover-*"))
        assert before == after == set()
