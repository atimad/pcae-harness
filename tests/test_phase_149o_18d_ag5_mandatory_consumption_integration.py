"""Phase 149O.18D -- AG5 Mandatory Consumption Integration.

Phase-boundary verification: this phase wires 149O.18A's fresh cutover-mode
resolution and 149O.18B's real-effect Consumption Attempt into AG5's real
effect boundary (`build_rollback_execution`, immediately before the
restore/remove loop), per HMRC-REQ-066, mirroring 149O.18C's AG3 wiring
exactly. It does not add `--hatp-evidence-id` CLI plumbing, does not modify
Permission Broker or POL-005, does not modify 149O.18A/18B, and does not
activate `HATP_MANDATORY` on any real deployment.

Production diff this phase: `src/pcae/core/agent.py` only -- the AG5
effect-boundary wiring, plus fixing two pre-existing, never-previously-
exercised `read_git_branch(str(root.path))` type-mismatch bugs (the same
category 149O.18C fixed for AG3's own Wave-7 block and mandatory gate) and
adding one new terminal RER status (`aborted_hatp_mandatory_denied`) to the
existing closed vocabulary so a mandatory-gate denial leaves the record in
a genuine terminal state rather than stuck `in_progress`.
"""
from __future__ import annotations

import ast
import inspect
import subprocess
from pathlib import Path

import pytest

from pcae.core import agent as agent_mod
from pcae.core import hatp_mandatory_cutover as cutover_mod
from pcae.core import hatp_rollback_consumption as cons_mod

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"

# HEAD at the moment this phase began (149O.18C's final commit).
_PHASE_ENTRY_COMMIT = "5df3d1fa"

_UPSTREAM_CONTRACTS = (
    _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    _CONTRACTS / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    _CONTRACTS / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    _CONTRACTS / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    _CONTRACTS / "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
)

_EXPECTED_CHANGED_FILES = {
    "src/pcae/core/agent.py",
}

_FORBIDDEN_MODIFIED_FILES = (
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/hatp_evidence_store.py",
    "src/pcae/core/hatp_signed_evidence.py",
    "src/pcae/core/hatp_signing_ceremony.py",
    "src/pcae/core/hatp_ag_authority.py",
    "src/pcae/core/hatp_rollback_consumption.py",
    "src/pcae/core/hatp_mandatory_cutover.py",
    "src/pcae/core/human_approval_trusted_provenance.py",
    "src/pcae/core/rollback_approval_evidence.py",
    "src/pcae/commands/agent.py",
    "src/pcae/cli.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/repository_identity.py",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


# ── Production file allowlist ─────────────────────────────────────────────


class TestProductionFileAllowlist:
    def test_exactly_agent_py_changed(self) -> None:
        changed = {
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/").splitlines()
            if line
        }
        assert changed == _EXPECTED_CHANGED_FILES

    def test_no_forbidden_production_file_touched(self) -> None:
        changed = set(
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/").splitlines()
            if line
        )
        assert changed.isdisjoint(_FORBIDDEN_MODIFIED_FILES)

    # Updated 149O.18F (149O.5-F-3 methodology): pinned to 149O.18D's own
    # completion commit (`7e4a469d`, also 149O.18E's own phase-entry
    # commit) rather than an open-ended `HEAD` -- 149O.18F additively
    # extended `hatp_mandatory_cutover.py` afterward (activation-
    # readiness/activation-guard functions), which this test was never
    # meant to forbid; it verifies only that 149O.18D itself left this
    # file untouched.
    _PHASE_149O_18D_COMPLETION_COMMIT = "7e4a469d"

    def test_18a_cutover_module_byte_unchanged(self) -> None:
        diff = _git(
            "diff", "--stat", f"{_PHASE_ENTRY_COMMIT}", self._PHASE_149O_18D_COMPLETION_COMMIT,
            "--", "src/pcae/core/hatp_mandatory_cutover.py",
        )
        assert diff.strip() == ""

    def test_18b_consumption_module_byte_unchanged(self) -> None:
        diff = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/core/hatp_rollback_consumption.py")
        assert diff.strip() == ""

    def test_ag3_execute_rollback_source_unchanged_since_entry(self) -> None:
        """149O.18C's AG3 wiring must remain behaviorally unchanged --
        confined check: no diff hunk touches `execute_rollback`'s own body."""
        diff = _git("diff", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/core/agent.py")
        assert "def execute_rollback" not in diff


# ── Contract byte-identity ────────────────────────────────────────────────


class TestContractByteIdentity:
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3) amended PBPA-001
    # v1.0 -> v1.1 (additive only: POL-013 row + PBPA-REQ-089; PBNDE-001
    # v1.0 / PBRD-001 v3.0). Sole authorized post-entry change; current
    # bytes pinned by sha256 so any further PBPA change still fails.
    # Reconciled by .1R.22R (N-23-3).
    _R122_AUTHORIZED_PBPA_SHA256 = (
        "13fc441a6e3688d1ea1b8e62a2b0ea3fafc6a293340f6907b05b7dccf8a16660"
    )

    @pytest.mark.parametrize("contract_path", _UPSTREAM_CONTRACTS, ids=lambda p: p.name)
    def test_contract_byte_unchanged(self, contract_path: Path) -> None:
        rel = contract_path.relative_to(_REPO_ROOT).as_posix()
        if rel.endswith("PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md"):
            import hashlib

            actual = hashlib.sha256(contract_path.read_bytes()).hexdigest()
            assert actual == self._R122_AUTHORIZED_PBPA_SHA256, (
                "PBPA-001 changed beyond the authorized .1R.22 v1.1 amendment"
            )
            text = contract_path.read_text()
            assert "**Version:** 1.1" in text and "POL-013" in text
            return
        diff = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}", "--", rel)
        assert diff.strip() == ""


# ── CLI / PB non-change ───────────────────────────────────────────────────


class TestNoCLIOrPBChange:
    def test_no_cli_files_touched(self) -> None:
        changed = set(
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/").splitlines()
            if line
        )
        assert "src/pcae/commands/agent.py" not in changed
        assert "src/pcae/cli.py" not in changed

    def test_no_permission_broker_files_touched(self) -> None:
        changed = set(
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/").splitlines()
            if line
        )
        assert "src/pcae/core/permission_broker.py" not in changed
        assert "src/pcae/core/permission_broker_foundation.py" not in changed


# ── Effect ordering / direct-call coverage (structural, AST-based) ───────


class TestEffectOrderingAndDirectCallCoverage:
    def test_first_mutation_appears_after_mandatory_gate_in_source(self) -> None:
        source = inspect.getsource(agent_mod.build_rollback_execution)
        gate_index = source.index("Mandatory Consumption Boundary")
        first_write_index = min(
            pos for pos in (
                source.find("full_path.write_text"),
                source.find("full_path.write_bytes"),
                source.find("full_path.unlink()"),
            ) if pos != -1
        )
        assert gate_index < first_write_index

    def test_no_new_authority_override_parameters_on_build_rollback_execution(self) -> None:
        params = set(inspect.signature(agent_mod.build_rollback_execution).parameters)
        assert params == {"root", "per_id", "dry_run", "hatp_evidence_id", "hatp_proof", "hatp_evidence"}

    def test_single_production_caller_of_build_rollback_execution(self) -> None:
        """HMRC-REQ-069: inventory every production caller."""
        result = subprocess.run(
            ["grep", "-rn", "build_rollback_execution(", "--include=*.py", str(_SRC)],
            capture_output=True,
            text=True,
        )
        callers = [
            line
            for line in result.stdout.splitlines()
            if "def build_rollback_execution" not in line
        ]
        assert callers, "expected at least one production caller"
        assert all("commands/agent.py" in line for line in callers), callers

    def test_agent_module_never_calls_evaluate_for_advisory(self) -> None:
        source = inspect.getsource(agent_mod)
        tree = ast.parse(source)
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert "evaluate_for_advisory" not in names
        assert "evaluate_for_advisory" not in attrs

    def test_mandatory_gate_uses_evaluate_for_real_effect(self) -> None:
        source = inspect.getsource(agent_mod.build_rollback_execution)
        assert "evaluate_for_real_effect" in source

    def test_no_advisory_simulation_only_keyword_call_argument(self) -> None:
        """No `simulation_only=` keyword call-argument is ever passed by
        this function -- the real-effect entrypoint
        (`evaluate_for_real_effect`) structurally hardcodes it internally,
        never as a value this caller supplies. Checked at the AST call-site
        level (not raw text) so this survives free-text prose/comments
        mentioning `simulation_only=True` for documentation purposes."""
        source = inspect.getsource(agent_mod.build_rollback_execution)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    assert kw.arg != "simulation_only"


# ── No real activation ────────────────────────────────────────────────────


class TestNoRealActivation:
    def test_no_cutover_record_or_marker_writer_referenced_in_agent_py(self) -> None:
        source = inspect.getsource(agent_mod)
        assert "_write_cutover_transition" not in source
        assert "activate_hatp_mandatory" not in source

    def test_this_repository_still_resolves_legacy_compatible(self) -> None:
        """This development host has no provisioned Class-B protected root
        and no repository identity -- the real production
        `build_rollback_execution` call path resolves LEGACY_COMPATIBLE
        end-to-end, exactly as 149O.18C confirmed for AG3."""
        from pcae.core.hatp_mandatory_cutover import CutoverMode, resolve_production_hatp_cutover_mode
        from pcae.core.paths import HarnessPath

        resolution = resolve_production_hatp_cutover_mode(HarnessPath(_REPO_ROOT))
        assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE


# ── RER status vocabulary ─────────────────────────────────────────────────


class TestRERStatusVocabulary:
    def test_new_terminal_status_is_registered(self) -> None:
        assert "aborted_hatp_mandatory_denied" in agent_mod._RER_VALID_STATUSES

    def test_pre_existing_statuses_untouched(self) -> None:
        assert {"in_progress", "completed", "partial", "failed", "aborted_divergence"}.issubset(
            agent_mod._RER_VALID_STATUSES
        )


# ── Fresh git_status.read_git_branch bug fix (shared with 149O.18C) ──────


class TestReadGitBranchCallSignature:
    def test_build_rollback_execution_never_passes_a_string_to_read_git_branch(self) -> None:
        """`read_git_branch` takes a `HarnessPath`, not `str(root.path)`
        (`src/pcae/core/git_status.py`). The pre-existing Wave-7 block and
        this phase's own new gate both call it -- both must pass `root`."""
        source = inspect.getsource(agent_mod.build_rollback_execution)
        assert "read_git_branch(str(root.path))" not in source
        assert source.count("read_git_branch(root)") == 2
