"""Phase 149O.18B -- HATP Mandatory Evidence Consumption Adapter.

Phase-boundary verification: this phase implements ONLY the HMRC-001
mandatory-consumption adapter (`hatp_rollback_consumption.py`), Wave B of
the 149O.17 implementation plan. This module mechanically confirms the
scope boundary was respected -- by inspecting real repository/git state,
not by trusting the phase document's prose.
"""
from __future__ import annotations

import ast
import inspect
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_cutover as cutover_149o_18a
from pcae.core import hatp_rollback_consumption as cons
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.paths import HarnessPath

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"

# HEAD at the moment this phase began (149O.18A's final commit).
_PHASE_ENTRY_COMMIT = "b0a71e36"

#: This phase's own exit commit -- pinned rather than diffing to live
#: "HEAD": 149O.19.5E.1/149O.19.5E.3 later and legitimately touched
#: `src/pcae/core/hatp_mandatory_certification.py`, well after this
#: phase concluded.
_PHASE_EXIT_COMMIT = "5143bb27"

_UPSTREAM_CONTRACTS = (
    _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    _CONTRACTS / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    _CONTRACTS / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    _CONTRACTS / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    _CONTRACTS / "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
)

_NEW_MODULE_PATH = _SRC / "core" / "hatp_rollback_consumption.py"
_CUTOVER_MODULE_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"

_FORBIDDEN_MODIFIED_FILES = (
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/hatp_evidence_store.py",
    "src/pcae/core/hatp_signed_evidence.py",
    "src/pcae/core/hatp_signing_ceremony.py",
    "src/pcae/core/hatp_ag_authority.py",
    "src/pcae/core/hatp_mandatory_cutover.py",
    "src/pcae/core/human_approval_trusted_provenance.py",
    "src/pcae/core/rollback_approval_evidence.py",
    "src/pcae/core/agent.py",
    "src/pcae/commands/agent.py",
    "src/pcae/cli.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/repository_identity.py",
)

_FORBIDDEN_IMPORT_MODULES = (
    "pcae.core.hatp_mandatory_cutover",
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
    def test_only_the_new_consumption_module_was_added_to_src_pcae(self) -> None:
        changed = [
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}..{_PHASE_EXIT_COMMIT}", "--", "src/pcae/").splitlines()
            if line
        ]
        assert changed == ["src/pcae/core/hatp_rollback_consumption.py"]

    def test_no_forbidden_production_file_touched(self) -> None:
        changed = set(
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}..{_PHASE_EXIT_COMMIT}", "--", "src/pcae/").splitlines()
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
        diff = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}..{_PHASE_EXIT_COMMIT}", "--", rel)
        assert diff == ""


# ── 149O.18A module byte-unchanged ────────────────────────────────────────


class TestCutoverModuleUnchanged:
    def test_cutover_module_byte_unchanged(self) -> None:
        rel = _CUTOVER_MODULE_PATH.relative_to(_REPO_ROOT).as_posix()
        diff = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}..{_PHASE_EXIT_COMMIT}", "--", rel)
        assert diff == ""

    def test_cutover_module_still_importable_and_unmodified_vocabulary(self) -> None:
        assert [m.name for m in cutover_149o_18a.CutoverMode] == [
            "LEGACY_COMPATIBLE",
            "PREPARED",
            "HATP_MANDATORY",
        ]


# ── Dependency closure: no cutover/agent/CLI imports ─────────────────────


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

    def test_no_agent_or_cli_reference(self) -> None:
        # AST-based (not substring): the module docstring's *prose*
        # legitimately names `execute_rollback`/`build_rollback_execution`
        # to explain scope boundaries -- what must never exist is an
        # actual identifier reference to either in real code.
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        assert "execute_rollback" not in identifiers
        assert "build_rollback_execution" not in identifiers
        assert "argparse" not in _NEW_MODULE_PATH.read_text(encoding="utf-8")


# ── Production dependency closure (F-2 pattern) ──────────────────────────


class TestProductionDependencyClosure:
    @pytest.mark.parametrize("fn_name", ["evaluate_for_real_effect", "evaluate_for_advisory"])
    def test_production_entrypoint_signature_is_exactly_request_root(self, fn_name: str) -> None:
        fn = getattr(cons, fn_name)
        assert list(inspect.signature(fn).parameters) == ["request", "root"]

    def test_internal_seam_is_private(self) -> None:
        assert cons._internal_consume_hatp_rollback_evidence.__name__.startswith("_")

    def test_production_entrypoints_resolve_hatp_trust_store_production_internally(self) -> None:
        source = inspect.getsource(cons._resolve_production_dependencies)
        assert "HATPTrustStore.production()" in source

    def test_hatp_trust_store_production_only_called_from_dependency_resolver(self) -> None:
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
        assert call_sites == ["_resolve_production_dependencies"]


# ── Simulation-only truthfulness (MC-14) ─────────────────────────────────


class TestSimulationOnlyTruthfulness:
    def test_real_effect_entrypoint_hardcodes_simulation_only_false(self) -> None:
        source = inspect.getsource(cons.evaluate_for_real_effect)
        assert "simulation_only=False" in source

    def test_advisory_entrypoint_hardcodes_simulation_only_true(self) -> None:
        source = inspect.getsource(cons.evaluate_for_advisory)
        assert "simulation_only=True" in source

    def test_no_public_function_exposes_simulation_only_parameter(self) -> None:
        for name, fn in vars(cons).items():
            if name.startswith("_") or not inspect.isfunction(fn):
                continue
            if fn.__module__ != cons.__name__:
                continue  # re-exported dependency, not defined by this module
            assert "simulation_only" not in inspect.signature(fn).parameters, name


# ── No raw-hook public inputs ──────────────────────────────────────────


class TestNoRawHookPublicInputs:
    @pytest.mark.parametrize("fn_name", ["evaluate_for_real_effect", "evaluate_for_advisory"])
    def test_no_raw_proof_or_evidence_parameter(self, fn_name: str) -> None:
        fn = getattr(cons, fn_name)
        params = set(inspect.signature(fn).parameters)
        assert params.isdisjoint({"hatp_proof", "hatp_evidence", "proof", "envelope", "raw_proof"})

    def test_request_type_carries_no_raw_hook_fields(self) -> None:
        field_names = {f.name for f in cons.HATPRollbackConsumptionRequest.__dataclass_fields__.values()}
        assert field_names.isdisjoint({"hatp_proof", "hatp_evidence", "proof", "envelope"})


# ── Fresh-per-call verification / no cache / no persistence ─────────────


class TestNoCacheNoPersistence:
    def test_no_module_level_mutable_cache_state(self) -> None:
        forbidden_module_globals = {"_CACHE", "_cache", "_MEMO", "_memo"}
        assert forbidden_module_globals.isdisjoint(vars(cons).keys())

    def test_internal_seam_takes_explicit_evaluation_time_every_call(self) -> None:
        params = inspect.signature(cons._internal_consume_hatp_rollback_evidence).parameters
        assert "evaluation_time" in params
        assert params["evaluation_time"].default is inspect.Parameter.empty

    def test_no_persistence_primitives_used_in_module(self) -> None:
        source = _NEW_MODULE_PATH.read_text(encoding="utf-8")
        for forbidden in ("write_bytes(", "write_text(", "os.replace(", "mkstemp("):
            assert forbidden not in source


# ── No effect / no cutover write / no legacy mutation ────────────────────


class TestNoEffectNoMutation:
    def test_no_git_or_filesystem_mutation_identifiers(self) -> None:
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        forbidden = {
            "_run_git_revert",
            "execute_rollback",
            "build_rollback_execution",
            "unlink",
            "write_bytes",
            "write_text",
            "subprocess",
        }
        assert identifiers.isdisjoint(forbidden)

    def test_no_cutover_record_or_marker_reference(self) -> None:
        source = _NEW_MODULE_PATH.read_text(encoding="utf-8")
        assert "cutover-record.json" not in source
        assert "cutover-activation-marker.json" not in source
        assert "activate_hatp_mandatory" not in source
        assert "_write_cutover_transition" not in source

    def test_no_rollback_approval_state_or_per_status_mutation_call(self) -> None:
        tree = ast.parse(_NEW_MODULE_PATH.read_text(encoding="utf-8"))
        identifiers = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
            node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
        }
        assert "create_rollback_approval_binding" not in identifiers
        assert "revoke_rollback_approval_binding" not in identifiers
        assert "write_binding" not in identifiers


# ── Result type shape (HMRC-REQ-075) ──────────────────────────────────────


class TestResultTypeShape:
    def test_result_has_exactly_four_fields(self) -> None:
        field_names = {f.name for f in cons.HATPRollbackConsumptionResult.__dataclass_fields__.values()}
        assert field_names == {"evidence_id", "hatp_status", "pb_decision", "reasons"}

    def test_result_has_no_executed_field(self) -> None:
        field_names = {f.name for f in cons.HATPRollbackConsumptionResult.__dataclass_fields__.values()}
        assert "executed" not in field_names
        assert "rollback_succeeded" not in field_names
        assert "capability_available" not in field_names


# ── No real production activation / no real effect on this host ────────


class TestNoRealProductionActivation:
    def test_evaluate_for_real_effect_against_real_production_dependencies_never_mutates_repo(
        self, tmp_path: Path
    ) -> None:
        # This development host has no provisioned repository identity
        # under a throwaway root -- confirms the production entrypoint
        # fails closed via dependency resolution without ever reaching
        # any mutation, and creates no file under the throwaway root.
        root = HarnessPath(tmp_path)
        before = set(tmp_path.rglob("*"))
        request = cons.HATPRollbackConsumptionRequest(
            evidence_id="a" * 64,
            operation_context=__import__(
                "pcae.core.rollback_approval_evidence", fromlist=["Ag3RollbackApprovalContext"]
            ).Ag3RollbackApprovalContext(
                job_id="job",
                original_commit_sha="b" * 40,
                task_id="task",
                repository_state=__import__(
                    "pcae.core.rollback_approval_evidence", fromlist=["RepositoryStateBinding"]
                ).RepositoryStateBinding(head_commit_sha="c" * 40, branch="main"),
            ),
        )
        result = cons.evaluate_for_real_effect(request, root=root)
        after = set(tmp_path.rglob("*"))
        assert before == after
        assert result.pb_decision == "DENY"

    def test_production_protected_root_untouched_by_this_phase(self) -> None:
        root = HATPTrustStore.production().root
        if not root.exists():
            return
        assert not (root / "cutover-record.json").exists()
        assert not (root / "cutover-activation-marker.json").exists()
